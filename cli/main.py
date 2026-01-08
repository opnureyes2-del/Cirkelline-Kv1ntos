#!/usr/bin/env python3
"""
Cirkelline Terminal CLI
=======================
Main entry point for Kommandant terminal interface.

Usage:
    cirkelline login                    # Authenticate
    cirkelline status                   # System status
    cirkelline ping                     # Test connection
    cirkelline ask "What is..."         # Ask Kommandanten
    cirkelline context                  # Show current context
    cirkelline chat                     # Interactive chat mode
"""

import os
import sys
import asyncio
import logging
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.config import load_config, save_config, CLIConfig
from cli.auth import get_auth_manager, AuthManager
from cli.git_context import get_git_context, GitContext
from cli.client import KommandantClient

console = Console()
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CLICK CLI GROUP
# ═══════════════════════════════════════════════════════════════════════════════

@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--no-color", is_flag=True, help="Disable color output")
@click.pass_context
def cli(ctx, verbose: bool, no_color: bool):
    """
    Cirkelline Terminal CLI - Kommandant Interface

    Connect to Cirkelline from your terminal with full Git context awareness.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["no_color"] = no_color

    # Configure logging
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(message)s")


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option("--email", "-e", prompt=True, help="Email address")
@click.option("--password", "-p", prompt=True, hide_input=True, help="Password")
def login(email: str, password: str):
    """Authenticate with Cirkelline."""

    async def do_login():
        auth = get_auth_manager()

        with console.status("[bold cyan]Authenticating..."):
            success = await auth.login(email, password)

        if success:
            console.print(Panel(
                f"[bold green]Login successful![/bold green]\n\n"
                f"User: {auth.token.user_email}\n"
                f"Tier: {auth.token.tier}",
                title="Authenticated",
                border_style="green"
            ))
        else:
            console.print("[bold red]Login failed.[/bold red] Check credentials.")
            sys.exit(1)

    asyncio.run(do_login())


@cli.command()
def logout():
    """Clear authentication."""
    auth = get_auth_manager()
    auth.logout()
    console.print("[yellow]Logged out.[/yellow]")


@cli.command()
def whoami():
    """Show current authentication status."""
    auth = get_auth_manager()

    if auth.is_authenticated:
        table = Table(title="Authentication Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Status", "Authenticated")
        table.add_row("Email", auth.token.user_email or "N/A")
        table.add_row("User ID", auth.token.user_id[:20] + "..." if auth.token.user_id else "N/A")
        table.add_row("Tier", auth.token.tier or "N/A")

        console.print(table)
    else:
        console.print("[yellow]Not authenticated.[/yellow] Run 'cirkelline login' first.")


# ═══════════════════════════════════════════════════════════════════════════════
# STATUS & CONNECTIVITY COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
def ping():
    """Test connection to Kommandanten."""

    async def do_ping():
        client = KommandantClient()

        with console.status("[bold cyan]Pinging Kommandanten..."):
            result = await client.ping()

        if result.get("success"):
            latency = result.get("latency_ms", "N/A")
            console.print(f"[bold green]PONG![/bold green] Latency: {latency}ms")
        else:
            console.print(f"[bold red]Connection failed:[/bold red] {result.get('error', 'Unknown error')}")
            sys.exit(1)

    asyncio.run(do_ping())


@cli.command()
def status():
    """Show system status and health."""

    async def get_status():
        client = KommandantClient()
        auth = get_auth_manager()

        # Collect status
        with console.status("[bold cyan]Checking system status..."):
            health = await client.get_health()
            git = get_git_context()

        # Build status table
        table = Table(title="System Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Details")

        # API Connection
        if health.get("api_status") == "healthy":
            table.add_row("API", "[green]Healthy[/green]", health.get("api_version", ""))
        else:
            table.add_row("API", "[red]Offline[/red]", health.get("error", ""))

        # Authentication
        if auth.is_authenticated:
            table.add_row("Auth", "[green]Authenticated[/green]", auth.token.user_email or "")
        else:
            table.add_row("Auth", "[yellow]Not logged in[/yellow]", "")

        # Git Context
        if git.is_git_repo:
            changes = f"+{len(git.staged_files)} staged, ~{len(git.modified_files)} modified"
            table.add_row("Git", "[green]Repository[/green]", f"{git.repo_name} @ {git.current_branch}")
            if git.has_changes:
                table.add_row("", "", changes)
        else:
            table.add_row("Git", "[yellow]Not a repo[/yellow]", os.getcwd())

        console.print(table)

    asyncio.run(get_status())


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def context(as_json: bool):
    """Show current Git and terminal context."""
    git = get_git_context()

    if as_json:
        import json
        console.print(json.dumps(git.to_dict(), indent=2))
        return

    if not git.is_git_repo:
        console.print("[yellow]Not in a Git repository.[/yellow]")
        console.print(f"Current directory: {os.getcwd()}")
        return

    # Git Context Panel
    table = Table(title=f"Git Context: {git.repo_name}")
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("Branch", git.current_branch or "N/A")
    table.add_row("Commit", f"{git.commit_short} - {git.commit_message[:50]}..." if git.commit_message else "N/A")
    table.add_row("Author", git.commit_author or "N/A")
    table.add_row("Date", git.commit_date or "N/A")

    if git.remote_url:
        table.add_row("Remote", git.remote_url)
        if git.ahead_count or git.behind_count:
            table.add_row("Sync", f"+{git.ahead_count}/-{git.behind_count}")

    if git.has_changes:
        table.add_row("Staged", f"{len(git.staged_files)} files")
        table.add_row("Modified", f"{len(git.modified_files)} files")
        table.add_row("Untracked", f"{len(git.untracked_files)} files")

    console.print(table)


# ═══════════════════════════════════════════════════════════════════════════════
# INTERACTION COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
@click.argument("question", nargs=-1, required=True)
@click.option("--no-context", is_flag=True, help="Don't include Git context")
def ask(question: tuple, no_context: bool):
    """Ask Kommandanten a question."""
    question_text = " ".join(question)

    async def do_ask():
        auth = get_auth_manager()
        if not auth.is_authenticated:
            console.print("[yellow]Not authenticated.[/yellow] Run 'cirkelline login' first.")
            sys.exit(1)

        client = KommandantClient()

        # Collect context
        git_context = None if no_context else get_git_context().to_dict()

        console.print(f"\n[bold cyan]You:[/bold cyan] {question_text}\n")

        with console.status("[bold cyan]Thinking..."):
            response = await client.ask(question_text, context=git_context)

        if response.get("success"):
            answer = response.get("answer", "No response")
            console.print(f"[bold green]Kommandanten:[/bold green]")
            console.print(Markdown(answer))
        else:
            console.print(f"[bold red]Error:[/bold red] {response.get('error', 'Unknown error')}")
            sys.exit(1)

    asyncio.run(do_ask())


@cli.command()
def chat():
    """Start interactive chat with Kommandanten."""
    auth = get_auth_manager()
    if not auth.is_authenticated:
        console.print("[yellow]Not authenticated.[/yellow] Run 'cirkelline login' first.")
        sys.exit(1)

    console.print(Panel(
        "[bold cyan]Cirkelline Chat[/bold cyan]\n\n"
        "Type your message and press Enter.\n"
        "Commands: /exit, /clear, /context, /help",
        title="Interactive Mode",
        border_style="cyan"
    ))

    async def chat_loop():
        client = KommandantClient()
        git = get_git_context()

        while True:
            try:
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ")

                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    cmd = user_input.lower().strip()
                    if cmd == "/exit" or cmd == "/quit":
                        console.print("[yellow]Goodbye![/yellow]")
                        break
                    elif cmd == "/clear":
                        console.clear()
                        continue
                    elif cmd == "/context":
                        if git.is_git_repo:
                            console.print(f"[dim]Context: {git.repo_name} @ {git.current_branch}[/dim]")
                        else:
                            console.print("[dim]No Git context[/dim]")
                        continue
                    elif cmd == "/help":
                        console.print("[dim]/exit - Exit chat[/dim]")
                        console.print("[dim]/clear - Clear screen[/dim]")
                        console.print("[dim]/context - Show current context[/dim]")
                        continue

                # Send message
                with console.status("[dim]...[/dim]"):
                    response = await client.ask(user_input, context=git.to_dict())

                if response.get("success"):
                    answer = response.get("answer", "")
                    console.print(f"\n[bold green]Kommandanten:[/bold green]")
                    console.print(Markdown(answer))
                else:
                    console.print(f"[red]Error: {response.get('error', 'Unknown')}[/red]")

            except KeyboardInterrupt:
                console.print("\n[yellow]Use /exit to quit[/yellow]")
            except EOFError:
                break

    asyncio.run(chat_loop())


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group()
def config():
    """Configuration management."""
    pass


@config.command("show")
def config_show():
    """Show current configuration."""
    cfg = load_config()

    table = Table(title="CLI Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    table.add_row("API URL", cfg.api_base_url)
    table.add_row("WebSocket URL", cfg.ws_url)
    table.add_row("Auto-detect Git", str(cfg.auto_detect_git))
    table.add_row("Include Git diff", str(cfg.include_git_diff))
    table.add_row("Request timeout", f"{cfg.request_timeout}s")
    table.add_row("Log level", cfg.log_level)

    console.print(table)


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value."""
    cfg = load_config()

    if hasattr(cfg, key):
        # Type conversion
        current = getattr(cfg, key)
        if isinstance(current, bool):
            value = value.lower() in ("true", "1", "yes")
        elif isinstance(current, int):
            value = int(value)

        setattr(cfg, key, value)
        save_config(cfg)
        console.print(f"[green]Set {key} = {value}[/green]")
    else:
        console.print(f"[red]Unknown config key: {key}[/red]")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# VERSION & INFO
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command()
def version():
    """Show CLI version information."""
    from cli import __version__

    console.print(Panel(
        f"[bold cyan]Cirkelline Terminal CLI[/bold cyan]\n\n"
        f"Version: {__version__}\n"
        f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        title="Version Info",
        border_style="cyan"
    ))


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
