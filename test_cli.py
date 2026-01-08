#!/usr/bin/env python3
"""
Cirkelline CLI Testing Tool
===========================

Test Cirkelline directly from your terminal without starting the web server.

Usage:
    python test_cli.py                    # Quick Search mode (default)
    python test_cli.py --deep-research    # Deep Research mode
    python test_cli.py --debug            # Enable debug output

Requirements:
    - PostgreSQL database running: docker start cirkelline-postgres
    - Virtual environment activated: source .venv/bin/activate
    - Environment variables loaded (automatic via .venv/bin/activate)

What works in CLI mode:
    - Streaming responses
    - Tool calls (search, reasoning, etc.)
    - Session persistence (stored in database)
    - User memories
    - Knowledge base search

What does NOT work:
    - File uploads
    - Google integration (requires OAuth flow)
    - Web UI sidebar
"""

import argparse
import sys
from datetime import datetime

# Parse arguments FIRST before any imports (avoids loading everything for --help)
parser = argparse.ArgumentParser(description="Cirkelline CLI Testing Tool")
parser.add_argument("--deep-research", action="store_true", help="Enable Deep Research mode")
parser.add_argument("--debug", action="store_true", help="Enable debug output")
parser.add_argument("--user-id", type=str, default="ee461076-8cbb-4626-947b-956f293cf7bf",
                    help="User ID for knowledge filtering (default: Ivo's ID)")
parser.add_argument("--session-id", type=str, default=None,
                    help="Session ID to continue a previous conversation")
args = parser.parse_args()

# Now import Cirkelline (this loads all the heavy stuff)
print("Loading Cirkelline...")
from cirkelline.orchestrator.cirkelline_team import cirkelline
from cirkelline.config import logger
from cirkelline.middleware.middleware import _shared_engine
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy import text


def get_user_info(user_id: str) -> dict:
    """Load real user info from database."""
    try:
        with SQLAlchemySession(_shared_engine) as session:
            # Query users table for basic info
            result = session.execute(
                text("""
                    SELECT u.display_name, u.email,
                           ap.name as admin_name, ap.role as admin_role
                    FROM users u
                    LEFT JOIN admin_profiles ap ON u.id = ap.user_id
                    WHERE u.id = :user_id
                """),
                {"user_id": user_id}
            ).fetchone()

            if result:
                # Prefer admin_name if exists, otherwise display_name
                name = result[2] if result[2] else (result[0] if result[0] else "User")
                role = result[3] if result[3] else "User"
                email = result[1] if result[1] else ""

                return {
                    "name": name,
                    "role": role,
                    "email": email,
                    "is_admin": result[2] is not None
                }
    except Exception as e:
        logger.warning(f"Failed to load user info: {e}")

    return {"name": "User", "role": "User", "email": "", "is_admin": False}


def main():
    # Load real user info from database
    user_info = get_user_info(args.user_id)

    print("=" * 60)
    print("CIRKELLINE CLI TEST MODE")
    print("=" * 60)
    print()
    print(f"User: {user_info['name']} ({user_info['role']})")
    print(f"Mode: {'Deep Research' if args.deep_research else 'Quick Search'}")
    print(f"Debug: {'Enabled' if args.debug else 'Disabled'}")
    if args.session_id:
        print(f"Session: {args.session_id[:20]}...")
    print()
    print("Type your messages and press Enter.")
    print("Type 'exit', 'quit', or 'bye' to stop.")
    print()
    print("=" * 60)
    print()

    # Build session_state (same structure as custom_cirkelline.py endpoint)
    # This is CRITICAL for:
    # - Knowledge base filtering (uses current_user_id)
    # - Deep Research mode (uses deep_research flag)
    # - Callable instructions (reads from agent.session_state)
    session_state = {
        "current_user_id": args.user_id,
        "current_user_type": "Admin" if user_info['is_admin'] else "Regular",
        "current_user_name": user_info['name'],
        "current_tier_slug": "elite" if user_info['is_admin'] else "member",
        "current_tier_level": 5 if user_info['is_admin'] else 1,
        "deep_research": args.deep_research,
        "current_user_timezone": "UTC",
        "current_user_datetime": datetime.now().strftime('%A, %B %d, %Y at %H:%M'),
    }

    # CRITICAL WORKAROUND: Manually set session_state on the team
    # AGNO doesn't automatically set agent.session_state during run()
    # Callable instructions access it via agent.session_state
    # Without this, deep_research mode won't work!
    cirkelline.session_state = session_state

    # Configure debug mode
    if args.debug:
        cirkelline.debug_mode = True
        cirkelline.show_members_responses = True
        logger.info("Debug mode enabled")

    # If deep_research mode, remove direct search tools
    # (same logic as custom_cirkelline.py endpoint)
    if args.deep_research:
        original_tools = cirkelline.tools.copy() if cirkelline.tools else []
        cirkelline.tools = [
            tool for tool in cirkelline.tools
            if not (tool.__class__.__name__ in ['ExaTools', 'TavilyTools'])
        ]
        print(f"Deep Research Mode: Removed ExaTools and TavilyTools")
        print(f"Remaining tools: {[tool.__class__.__name__ for tool in cirkelline.tools]}")
        print()

    # Build cli_app kwargs
    cli_kwargs = {
        "stream": True,
        "markdown": True,
        "user": user_info['name'],
        "emoji": "👨‍💻" if user_info['is_admin'] else "👤",
        "exit_on": ["exit", "quit", "bye", "q"],
    }

    # Add session_id if provided (for continuing conversations)
    if args.session_id:
        cli_kwargs["session_id"] = args.session_id

    # Add user_id for database persistence
    cli_kwargs["user_id"] = args.user_id

    try:
        # Run interactive CLI
        cirkelline.cli_app(**cli_kwargs)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
    finally:
        # Restore tools if we modified them
        if args.deep_research:
            cirkelline.tools = original_tools
            print("\nRestored original tools.")


if __name__ == "__main__":
    main()
