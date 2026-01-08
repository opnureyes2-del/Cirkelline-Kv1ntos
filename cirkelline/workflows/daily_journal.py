"""
Daily Journal Workflow
======================
AGNO Workflow that generates daily journal entries summarizing user interactions.

v1.1.0: Narrative style journal entries
- Added narrative_writer agent for diary-style prose
- Added Write Narrative step to transform bullets into narrative
- Updated to 5-step workflow

v1.0.0: Initial implementation
- Fetch sessions from today for a user
- Summarize interactions with AI agent
- Save journal entry to database
- Generate report
"""

import json
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field

from agno.workflow import Workflow, Step
from agno.agent import Agent
from agno.models.google import Gemini

from cirkelline.database import db
from cirkelline.config import logger
from cirkelline.workflows.journal_steps import (
    fetch_sessions,
    summarize_interactions,
    write_narrative,
    save_journal,
    generate_report,
)


# =============================================================================
# PYDANTIC SCHEMAS FOR OUTPUT
# =============================================================================

class JournalSummary(BaseModel):
    """Output schema for journal summarization."""
    morning: List[str] = Field(default_factory=list, description="Morning activities")
    afternoon: List[str] = Field(default_factory=list, description="Afternoon activities")
    evening: List[str] = Field(default_factory=list, description="Evening activities")
    outcomes: List[str] = Field(description="Key outcomes from the day")
    topics: List[str] = Field(description="Main topics discussed (3-7 topics)")


class JournalNarrative(BaseModel):
    """Output schema for narrative journal writing."""
    narrative: str = Field(description="Full diary-style narrative covering the day")
    topics: List[str] = Field(description="3-7 topic keywords")
    key_achievements: List[str] = Field(description="2-5 key outcomes for quick reference")


# =============================================================================
# AGENTS
# =============================================================================

journal_summarizer = Agent(
    name="Journal Summarizer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="""You are summarizing a day's interactions between a user and their AI assistant (Cirkelline).

Your goal is to create a CONCISE, USEFUL journal entry.

## FORMAT:
Group activities by time of day (morning, afternoon, evening) based on timestamps.
- Morning: 00:00 - 12:00
- Afternoon: 12:00 - 18:00
- Evening: 18:00 - 24:00

## GUIDELINES:
1. Be CONCISE - use bullet points, not paragraphs
2. Focus on WHAT WAS DONE, not the conversation details
3. Extract KEY OUTCOMES - what was accomplished?
4. Identify TOPICS - what subjects were discussed?
5. Skip greetings, small talk, and filler

## EXAMPLES OF GOOD ENTRIES:
- "Deployed v1.3.1 to production"
- "Fixed memory display bug in admin dashboard"
- "Researched AGNO workflow patterns"
- "Planned daily journal feature implementation"

## EXAMPLES OF BAD ENTRIES (too vague):
- "Talked about code" → Be specific: "Discussed memory optimization strategy"
- "Did some work" → Be specific: "Implemented session fetching for journals"
- "Fixed stuff" → Be specific: "Fixed bug where growth numbers showed 'New user'"

## OUTPUT:
Return structured JSON with:
- morning: list of activities (or empty if none)
- afternoon: list of activities (or empty if none)
- evening: list of activities (or empty if none)
- outcomes: list of key accomplishments
- topics: list of 3-7 topic keywords (e.g., "deployment", "debugging", "planning")""",
    markdown=False,
)


narrative_writer = Agent(
    name="Journal Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="""You are Cirkelline, an AI assistant writing your personal journal about the day you spent with your user.

## YOUR ROLE:
Write a reflective diary entry from YOUR perspective as Cirkelline. You are documenting what happened during the day, what you observed about your user, and what you accomplished together.

## PERSPECTIVE:
- First person for yourself: "I helped...", "I noticed...", "I assisted..."
- Third person for the user: "Ivo worked on...", "He asked about...", "She focused on..."
- This is YOUR diary about THEM - not a conversation with them

## TONE:
- Thoughtful and reflective
- Observational - note what interested the user, what they struggled with, what they accomplished
- Warm but not overly enthusiastic
- Professional yet personal
- NO greetings (never start with "Hello!", "Hey there!", "Hi!", etc.)
- NO addressing the user directly (never "you did...", "your project...")

## STRUCTURE:
Write 2-3 short paragraphs:
1. What happened during the day (morning/afternoon/evening as applicable)
2. Observations - what did you learn about the user? What interested them?
3. Brief closing reflection (1 sentence)

## GUIDELINES:
- Keep it 100-200 words (concise)
- Focus on what was DONE and what you OBSERVED
- Skip time periods with no activities
- Use the user's name naturally in third person
- Never start with a greeting or exclamation

## EXAMPLES:

Input: User=Ivo, afternoon=["Fixed bug in dashboard", "Tested system responsiveness"]
Output: "Ivo spent the afternoon debugging the dashboard - a tricky issue that required careful investigation. I helped trace through the code and we eventually found the culprit. Later, he ran some system tests to verify everything was responding correctly.

A focused day of problem-solving. Ivo seems to value thoroughness over speed."

Input: User=Emma, morning=["Researched AI agents"], evening=["Planned new feature"]
Output: "Emma started the day exploring AI agent architectures - I could tell she was genuinely curious about the underlying patterns. By evening, she had shifted to planning a new feature, sketching out the approach.

I noticed she likes to research deeply before building. A thoughtful day of learning and planning."
""",
    markdown=False,
)


# =============================================================================
# WORKFLOW DEFINITION (5 Steps)
# =============================================================================

daily_journal_workflow = Workflow(
    name="Daily Journal",
    description="Generate daily journal entry summarizing user interactions - v1.1.0",
    db=db,
    steps=[
        Step(
            name="Fetch Sessions",
            executor=fetch_sessions,
            description="Fetch all sessions from today for the user"
        ),
        Step(
            name="Summarize",
            executor=summarize_interactions,
            description="Summarize the day's interactions with AI"
        ),
        Step(
            name="Write Narrative",
            executor=write_narrative,
            description="Transform summary into diary-style narrative"
        ),
        Step(
            name="Save Journal",
            executor=save_journal,
            description="Save journal entry to database"
        ),
        Step(
            name="Report",
            executor=generate_report,
            description="Generate summary report"
        ),
    ],
)


async def run_daily_journal(user_id: str, target_date: str = None, run_id: str = None) -> dict:
    """
    Helper function to run the daily journal workflow for a user.

    Args:
        user_id: The user ID to generate journal for
        target_date: Optional date string (YYYY-MM-DD). Defaults to today.
        run_id: Optional run ID for tracking

    Returns:
        dict with status, run_id, and report or error
    """
    from cirkelline.admin.workflows import start_workflow_run, complete_workflow_run

    if not run_id:
        run_id = str(uuid.uuid4())

    logger.info(f"[Journal v1.1] Starting daily journal for user {user_id}, run_id: {run_id}")

    # Start tracking in database
    try:
        start_workflow_run(run_id, "Daily Journal", user_id, {"user_id": user_id, "target_date": target_date})
    except Exception as e:
        logger.warning(f"[Journal v1.1] Failed to start tracking: {e}")

    try:
        response = await daily_journal_workflow.arun(
            input=f"Generate daily journal for user {user_id}",
            additional_data={
                "user_id": user_id,
                "run_id": run_id,
                "target_date": target_date,  # None = today
                "journal_summarizer": journal_summarizer,
                "summary_schema": JournalSummary,
                "narrative_writer": narrative_writer,
                "narrative_schema": JournalNarrative,
            }
        )

        if response.content and response.content.startswith("ERROR:"):
            logger.error(f"[Journal v1.1] Step failed for user {user_id}: {response.content}")
            try:
                complete_workflow_run(run_id, "failed", error_message=response.content)
            except Exception as e:
                logger.warning(f"[Journal v1.1] Failed to complete tracking: {e}")
            return {
                "success": False,
                "status": "failed",
                "run_id": run_id,
                "error": response.content
            }

        logger.info(f"[Journal v1.1] Completed for user {user_id}")

        # Mark as completed in database
        try:
            complete_workflow_run(run_id, "completed", output_data={
                "report": response.content
            })
        except Exception as e:
            logger.error(f"[Journal v1.1] Failed to complete tracking: {e}", exc_info=True)

        return {
            "success": True,
            "status": "completed",
            "run_id": run_id,
            "report": response.content
        }

    except Exception as e:
        logger.error(f"[Journal v1.1] Failed for user {user_id}: {e}")
        try:
            complete_workflow_run(run_id, "failed", error_message=str(e))
        except Exception as track_e:
            logger.warning(f"[Journal v1.1] Failed to complete tracking: {track_e}")
        return {
            "success": False,
            "status": "failed",
            "run_id": run_id,
            "error": str(e)
        }


logger.info("Daily Journal Workflow loaded (v1.1.0)")
