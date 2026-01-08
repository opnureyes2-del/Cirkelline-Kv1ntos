"""
Cirkelline Memory Manager
=========================
Custom memory manager for enhanced user understanding.
Captures identity, emotional state, preferences, goals, and patterns organically.
"""

from agno.memory import MemoryManager
from cirkelline.database import db
from cirkelline.config import logger

# Enhanced Memory Manager (v1.1.19+)
# ✅ v1.2.33: Added db parameter explicitly (AGNO best practice)
custom_memory_manager = MemoryManager(
    db=db,  # ✅ v1.2.33: Explicit database connection
    memory_capture_instructions="""
    Capture the following about the user organically through conversation:

    IDENTITY:
    • Name, role, company, location, background
    • Professional context and career stage
    • Technical expertise and specializations
    • Interests and hobbies

    EMOTIONAL STATE:
    • Current mood and tone
    • Urgency level and stress indicators
    • Confidence level in different areas
    • Excitement or concern about topics

    PREFERENCES:
    • Communication style (detailed vs concise, formal vs casual)
    • Learning preferences (examples, theory, hands-on)
    • Decision-making approach (data-driven, intuitive, collaborative)
    • Response formatting preferences

    GOALS:
    • Short-term needs and immediate objectives
    • Long-term aspirations and plans
    • Current projects and initiatives
    • Challenges and blockers

    PATTERNS:
    • Recurring topics and questions
    • Time patterns (when they work, urgency patterns)
    • Successful approaches that worked well
    • Areas where they need more support
    • Tools and platforms they use

    CONTEXT:
    • Current life situation and changes
    • Team dynamics and relationships
    • External factors affecting decisions
    • Previous solutions that helped
    """,

    additional_instructions="""
    MEMORY CAPTURE PRINCIPLES:

    1. NEVER ASSUME - Always verify before storing important facts
    2. VERIFY CONFIDENCE - Tag each memory with certainty level
    3. UPDATE DON'T DUPLICATE - Refresh existing memories with new info
    4. PRIORITIZE EMOTION - Emotional context shapes how to help
    5. CAPTURE IMPLICIT PREFERENCES - Notice patterns in what they respond to
    6. CONTEXT IS KEY - Store the "why" behind facts, not just facts
    7. RESPECT PRIVACY - Don't store overly personal details unless clearly shared
    8. ORGANIC CAPTURE - Extract naturally, don't interrogate
    """
)

logger.info("✅ Memory manager module loaded")
