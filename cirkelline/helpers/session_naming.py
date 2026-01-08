"""
Cirkelline Session Naming Helpers
==================================
Intelligent session name generation using AI.

NOTE: This module has a forward reference to 'cirkelline' team which will be
imported from cirkelline.orchestrator.cirkelline_team in Phase 5.
"""

import asyncio
from agno.models.google import Gemini
from agno.models.message import Message
from cirkelline.config import logger

# Forward reference - will be set by main module
cirkelline = None

def set_cirkelline_team(team):
    """Set cirkelline team reference after it's created"""
    global cirkelline
    cirkelline = team

def is_session_named(session_id: str) -> bool:
    """Check if session already has an auto-generated name"""
    try:
        session = cirkelline.get_session(session_id=session_id)
        if session and session.session_data:
            session_name = session.session_data.get("session_name")
            # Check if it has a name that's not generic
            if session_name:
                logger.debug(f"Session {session_id[:8]}... has name: '{session_name}'")
                return True
        logger.debug(f"Session {session_id[:8]}... has NO name yet")
        return False
    except Exception as e:
        logger.warning(f"Error checking if session is named: {e}")
        return False

def get_message_count(session_id: str) -> int:
    """Get number of messages in session"""
    try:
        messages = cirkelline.get_session_messages(session_id=session_id)
        count = len(messages) if messages else 0
        logger.debug(f"Session {session_id[:8]}... has {count} messages")
        return count
    except Exception as e:
        logger.warning(f"Error getting message count: {e}")
        return 0

def generate_custom_session_name(session_id: str, max_words: int = 10) -> str:
    """Generate session name with custom word limit (max 10 words per user requirement)"""
    try:
        messages = cirkelline.get_session_messages(session_id=session_id)

        if not messages or len(messages) < 2:
            logger.warning(f"Not enough messages to generate name (count: {len(messages) if messages else 0})")
            return None

        # Build conversation context (limit to first 3 exchanges for efficiency)
        conversation = "Conversation:\n"
        for msg in messages[:6]:  # First 3 exchanges (user + assistant)
            role = msg.role.upper() if hasattr(msg, 'role') else 'USER'
            # Ensure content is always a string, explicitly check for None
            if hasattr(msg, 'content') and msg.content is not None:
                content = str(msg.content)  # Convert to string for safety
            else:
                content = str(msg) if msg else ""
            # Truncate very long messages (content is guaranteed to be a string)
            if len(content) > 500:
                content = content[:500] + "..."
            conversation += f"{role}: {content}\n"

        logger.info(f"🏷️  Generating session name for {session_id[:8]}...")
        logger.debug(f"Conversation context ({len(conversation)} chars):\n{conversation[:200]}...")

        # Custom prompt with 10-word limit and anti-generic instructions
        system_msg = Message(
            role="system",
            content=(
                f"Generate a descriptive name for this conversation in maximum {max_words} words. "
                f"Be specific and capture the main topic or task. "
                f"NEVER use generic words like 'test', 'hey', 'hello', 'hi', or 'greeting'. "
                f"Focus on the actual content and purpose of the conversation. "
                f"Examples: 'Image Analysis Request', 'Python Data Analysis Help', 'Calendar Event Creation', 'Email Search Assistance'"
            )
        )
        user_msg = Message(role="user", content=conversation + "\n\nSession Name:")

        # Generate using Gemini (same model as cirkelline team)
        response = Gemini(id="gemini-2.5-flash").response(messages=[system_msg, user_msg])

        if not response or not response.content:
            logger.error("No response from Gemini for session name generation")
            return None

        name = response.content.replace('"', '').replace("'", '').strip()

        # Validate length
        word_count = len(name.split())
        if word_count > 15:  # Hard limit with buffer
            logger.warning(f"Generated name too long ({word_count} words), retrying...")
            # Retry with stricter prompt
            return generate_custom_session_name(session_id, max_words=max_words)

        logger.info(f"✅ Generated name ({word_count} words): '{name}'")
        return name

    except Exception as e:
        logger.error(f"Failed to generate session name: {e}")
        return None

async def attempt_session_naming(session_id: str, attempt_number: int = None):
    """Attempt to name a session, with logging"""
    try:
        # Check if already named
        if is_session_named(session_id):
            logger.debug(f"Session {session_id[:8]}... already named, skipping")
            return True

        # Check message count
        message_count = get_message_count(session_id)
        if message_count < 2:
            logger.debug(f"Session {session_id[:8]}... needs more messages (has {message_count})")
            return False

        # Calculate attempt number from message count if not provided
        if attempt_number is None:
            attempt_number = message_count // 2  # Each exchange is 2 messages

        logger.info(f"🎯 Attempt #{attempt_number} to name session {session_id[:8]}... ({message_count} messages)")

        # Generate name (runs in thread pool to avoid blocking)
        generated_name = await asyncio.to_thread(
            generate_custom_session_name,
            session_id=session_id,
            max_words=10
        )

        if not generated_name:
            logger.warning(f"⚠️  Attempt #{attempt_number} failed: No name generated")
            return False

        # Save to database
        await asyncio.to_thread(
            cirkelline.set_session_name,
            session_id=session_id,
            session_name=generated_name
        )

        logger.info(f"✅ SUCCESS! Session {session_id[:8]}... named: '{generated_name}'")
        return True

    except Exception as e:
        logger.error(f"❌ Attempt #{attempt_number} failed with error: {e}")
        return False

logger.info("✅ Session naming helpers loaded")
