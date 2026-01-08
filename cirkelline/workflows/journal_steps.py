"""
Daily Journal Workflow - Function Steps
========================================
v1.1.0: Narrative style journal entries
- Added write_narrative step for diary-style prose
- Updated to 5-step workflow

v1.0.0: Initial implementation

Steps:
1. fetch_sessions - Get all sessions from today for user
2. summarize_interactions - AI summarizes the day's conversations
3. write_narrative - Transform summary into diary-style prose
4. save_journal - Save journal entry to database
5. generate_report - Generate summary
"""

import json
import time
from datetime import datetime, date
from typing import Dict, List

from sqlalchemy import text
from agno.workflow.types import StepInput, StepOutput

from cirkelline.database import _shared_engine
from cirkelline.config import logger


def _track_step(run_id: str, step_name: str, step_number: int, stats: dict = None):
    """Track step progress in database."""
    try:
        from cirkelline.admin.workflows import update_workflow_step
        update_workflow_step(run_id, step_name, step_number, 5, stats)  # 5 steps in v1.1
    except Exception as e:
        logger.warning(f"[Journal Step Tracking] Failed to track step {step_name}: {e}")


def _get_target_date(target_date_str: str = None) -> date:
    """Get the target date for journal generation."""
    if target_date_str:
        return datetime.strptime(target_date_str, "%Y-%m-%d").date()
    return date.today()


def _get_user_registration_date(user_id: str) -> date:
    """Get the user's registration date from the database."""
    try:
        with _shared_engine.connect() as conn:
            result = conn.execute(
                text("SELECT created_at FROM users WHERE id = CAST(:user_id AS uuid)"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            if row and row[0]:
                # created_at is a timestamp
                return row[0].date() if hasattr(row[0], 'date') else datetime.fromisoformat(str(row[0])).date()
    except Exception as e:
        logger.warning(f"[Journal] Could not fetch user registration date: {e}")
    return None


def _get_user_journal_count(user_id: str, before_date: str) -> int:
    """Get the count of journals for a user created before a given date.

    This is used to calculate the journal "Day X" number - each journal entry
    is numbered sequentially (Day 1, Day 2, etc.) regardless of gaps in dates.
    """
    logger.info(f"[Journal] Getting journal count for user_id={user_id}, before_date={before_date}")
    try:
        with _shared_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT COUNT(*)
                    FROM ai.user_journals
                    WHERE user_id = :user_id
                    AND journal_date < :before_date
                """),
                {"user_id": user_id, "before_date": before_date}
            )
            row = result.fetchone()
            count = row[0] if row else 0
            logger.info(f"[Journal] Journal count result: {count}")
            return count
    except Exception as e:
        logger.error(f"[Journal] Could not fetch user journal count: {e}", exc_info=True)
    return 0


def _get_user_name(user_id: str) -> str:
    """Get the user's name from admin_profiles if available."""
    try:
        with _shared_engine.connect() as conn:
            result = conn.execute(
                text("SELECT name FROM admin_profiles WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            if row and row[0]:
                return row[0]
    except Exception as e:
        logger.warning(f"[Journal] Could not fetch user name: {e}")
    return None


def _parse_agent_response(response) -> dict:
    """Parse AGNO agent response to extract structured data."""
    result = None

    # Method 1: Check for parsed_content (AGNO's structured output)
    if hasattr(response, 'parsed_content') and response.parsed_content:
        data = response.parsed_content
        if hasattr(data, 'model_dump'):
            result = data.model_dump()
        elif hasattr(data, 'dict'):
            result = data.dict()
        elif isinstance(data, dict):
            result = data

    # Method 2: Check content directly
    if not result and hasattr(response, 'content') and response.content:
        data = response.content
        if hasattr(data, 'model_dump'):
            result = data.model_dump()
        elif hasattr(data, 'dict'):
            result = data.dict()
        elif isinstance(data, dict):
            result = data
        elif isinstance(data, str):
            try:
                clean_content = data.strip()
                if clean_content.startswith("```json"):
                    clean_content = clean_content[7:]
                if clean_content.startswith("```"):
                    clean_content = clean_content[3:]
                if clean_content.endswith("```"):
                    clean_content = clean_content[:-3]
                result = json.loads(clean_content.strip())
            except json.JSONDecodeError:
                pass

    # Method 3: Fallback to entire response
    if not result:
        if hasattr(response, 'model_dump'):
            result = response.model_dump()
        elif isinstance(response, dict):
            result = response

    return result or {}


# =============================================================================
# STEP 1: FETCH SESSIONS
# =============================================================================

async def fetch_sessions(step_input: StepInput) -> StepOutput:
    """Step 1: Fetch all sessions from today for the user."""
    additional_data = step_input.additional_data or {}
    user_id = additional_data.get("user_id")
    target_date_str = additional_data.get("target_date")

    if not user_id:
        return StepOutput(content="ERROR: No user_id provided", success=False, stop=True)

    target_date = _get_target_date(target_date_str)
    logger.info(f"[Journal v1.1] Step 1: Fetching sessions for user {user_id} on {target_date}")

    try:
        # Calculate start and end timestamps for the target date
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        start_ts = int(start_of_day.timestamp())
        end_ts = int(end_of_day.timestamp())

        with _shared_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT session_id, runs, created_at, session_data->>'session_name' as session_name
                    FROM ai.agno_sessions
                    WHERE user_id = :user_id
                    AND created_at >= :start_ts
                    AND created_at <= :end_ts
                    ORDER BY created_at ASC
                """),
                {"user_id": user_id, "start_ts": start_ts, "end_ts": end_ts}
            )
            rows = result.fetchall()

        sessions = []
        total_messages = 0

        for row in rows:
            session_id = row[0]
            runs_data = row[1] or []
            created_ts = row[2]
            session_name = row[3] or "Untitled"

            # Extract messages from runs
            # AGNO stores data as:
            #   input = {'input_content': 'user message'}  (dict)
            #   content = 'AI response text'  (string, NOT 'response')
            messages = []
            if isinstance(runs_data, list):
                for run in runs_data:
                    if isinstance(run, dict):
                        msg_created = run.get("created_at", created_ts)

                        # Extract user input - handle dict structure
                        raw_input = run.get("input", "")
                        if isinstance(raw_input, dict):
                            user_input = raw_input.get("input_content", "")
                        else:
                            user_input = str(raw_input) if raw_input else ""

                        # Response is stored as 'content', not 'response'
                        ai_response = run.get("content", "") or ""

                        messages.append({
                            "input": user_input,
                            "response": ai_response,
                            "created_at": msg_created,
                            "time": datetime.fromtimestamp(msg_created).strftime("%H:%M") if msg_created else "00:00"
                        })

            total_messages += len(messages)

            sessions.append({
                "session_id": session_id,
                "name": session_name,
                "messages": messages,
                "message_count": len(messages),
                "created_at": created_ts,
                "time": datetime.fromtimestamp(created_ts).strftime("%H:%M") if created_ts else "00:00"
            })

        logger.info(f"[Journal v1.1] Fetched {len(sessions)} sessions with {total_messages} messages")

        output_data = {
            "sessions": sessions,
            "target_date": target_date.isoformat(),
            "stats": {
                "session_count": len(sessions),
                "message_count": total_messages,
                "user_id": user_id
            }
        }

        # Track step progress
        run_id = additional_data.get("run_id")
        if run_id:
            _track_step(run_id, "Fetch Sessions", 1, {"sessions_fetched": len(sessions), "messages": total_messages})

        return StepOutput(content=json.dumps(output_data, ensure_ascii=False))

    except Exception as e:
        logger.error(f"[Journal v1.1] Error fetching sessions: {e}")
        return StepOutput(content=f"ERROR: Failed to fetch sessions: {str(e)}", success=False, stop=True)


# =============================================================================
# STEP 2: SUMMARIZE INTERACTIONS
# =============================================================================

async def summarize_interactions(step_input: StepInput) -> StepOutput:
    """Step 2: Summarize the day's interactions using AI."""
    additional_data = step_input.additional_data or {}
    journal_summarizer = additional_data.get("journal_summarizer")
    summary_schema = additional_data.get("summary_schema")

    if not journal_summarizer:
        return StepOutput(content="ERROR: journal_summarizer agent not provided", success=False, stop=True)

    logger.info("[Journal v1.1] Step 2: Summarizing interactions...")

    try:
        # Get fetch output
        fetch_output = step_input.previous_step_outputs.get("Fetch Sessions")
        if not fetch_output:
            return StepOutput(content="ERROR: Cannot find Fetch Sessions output", success=False, stop=True)

        fetch_data = json.loads(fetch_output.content)
        sessions = fetch_data.get("sessions", [])
        target_date = fetch_data.get("target_date")

        if not sessions:
            logger.info("[Journal v1.1] No sessions to summarize")
            return StepOutput(content=json.dumps({
                "summary": {
                    "morning": [],
                    "afternoon": [],
                    "evening": [],
                    "outcomes": ["No activity recorded"],
                    "topics": []
                },
                "target_date": target_date,
                "message_count": 0
            }))

        # Build conversation context for the summarizer
        conversation_text = f"Date: {target_date}\n\n"
        total_messages = 0

        for session in sessions:
            session_time = session.get("time", "00:00")
            session_name = session.get("name", "Untitled")
            messages = session.get("messages", [])

            if messages:
                conversation_text += f"--- Session: {session_name} (started {session_time}) ---\n"
                for msg in messages:
                    msg_time = msg.get("time", "00:00")

                    # Safely extract string values (defensive - handle non-strings)
                    raw_input = msg.get("input", "")
                    raw_response = msg.get("response", "")
                    user_input = str(raw_input).strip() if raw_input else ""
                    ai_response = str(raw_response).strip() if raw_response else ""

                    # Truncate long responses
                    if len(ai_response) > 500:
                        ai_response = ai_response[:500] + "..."

                    if user_input:
                        conversation_text += f"[{msg_time}] User: {user_input}\n"
                    if ai_response:
                        conversation_text += f"[{msg_time}] Cirkelline: {ai_response}\n"
                    conversation_text += "\n"
                    total_messages += 1

        # Truncate if too long
        if len(conversation_text) > 15000:
            conversation_text = conversation_text[:15000] + "\n\n[... truncated for length ...]"

        logger.info(f"[Journal v1.1] Sending {total_messages} messages to summarizer")

        # Call the summarizer agent
        response = await journal_summarizer.arun(
            conversation_text,
            response_model=summary_schema
        )

        # Debug: Log response structure
        logger.info(f"[Journal v1.1] Response type: {type(response)}")
        logger.info(f"[Journal v1.1] Response attrs: {[a for a in dir(response) if not a.startswith('_')][:15]}")

        # Parse structured output - AGNO response_model handling
        summary_dict = None

        # Method 1: Check for parsed_content (AGNO's structured output)
        if hasattr(response, 'parsed_content') and response.parsed_content:
            summary_data = response.parsed_content
            logger.info(f"[Journal v1.1] Using parsed_content, type: {type(summary_data)}")
            if hasattr(summary_data, 'model_dump'):
                summary_dict = summary_data.model_dump()
            elif hasattr(summary_data, 'dict'):
                summary_dict = summary_data.dict()
            elif isinstance(summary_data, dict):
                summary_dict = summary_data

        # Method 2: Check content directly
        if not summary_dict and hasattr(response, 'content') and response.content:
            summary_data = response.content
            logger.info(f"[Journal v1.1] Using content, type: {type(summary_data)}")
            if hasattr(summary_data, 'model_dump'):
                summary_dict = summary_data.model_dump()
            elif hasattr(summary_data, 'dict'):
                summary_dict = summary_data.dict()
            elif isinstance(summary_data, dict):
                summary_dict = summary_data
            elif isinstance(summary_data, str):
                # Try to parse as JSON from the string content
                try:
                    # Remove markdown code blocks if present
                    clean_content = summary_data.strip()
                    if clean_content.startswith("```json"):
                        clean_content = clean_content[7:]
                    if clean_content.startswith("```"):
                        clean_content = clean_content[3:]
                    if clean_content.endswith("```"):
                        clean_content = clean_content[:-3]
                    summary_dict = json.loads(clean_content.strip())
                    logger.info(f"[Journal v1.1] Parsed JSON from string content")
                except json.JSONDecodeError as e:
                    logger.warning(f"[Journal v1.1] Failed to parse content as JSON: {e}")
                    logger.info(f"[Journal v1.1] Content preview: {str(summary_data)[:500]}")

        # Method 3: Fallback to entire response
        if not summary_dict:
            if hasattr(response, 'model_dump'):
                summary_dict = response.model_dump()
            elif isinstance(response, dict):
                summary_dict = response

        # Final fallback
        if not summary_dict:
            logger.warning(f"[Journal v1.1] Could not parse response, using fallback")
            summary_dict = {
                "morning": [],
                "afternoon": [],
                "evening": [],
                "outcomes": ["Failed to parse summary"],
                "topics": []
            }

        output_data = {
            "summary": summary_dict,
            "target_date": target_date,
            "message_count": total_messages,
            "session_count": len(sessions)
        }

        # Track step progress
        run_id = additional_data.get("run_id")
        if run_id:
            _track_step(run_id, "Summarize", 2, {"messages_summarized": total_messages})

        logger.info(f"[Journal v1.1] Summarization complete: {len(summary_dict.get('outcomes', []))} outcomes, {len(summary_dict.get('topics', []))} topics")

        return StepOutput(content=json.dumps(output_data, ensure_ascii=False))

    except Exception as e:
        logger.error(f"[Journal v1.1] Error summarizing: {e}", exc_info=True)
        return StepOutput(content=f"ERROR: Failed to summarize: {str(e)}", success=False, stop=True)


# =============================================================================
# STEP 3: WRITE NARRATIVE
# =============================================================================

async def write_narrative(step_input: StepInput) -> StepOutput:
    """Step 3: Transform structured summary into narrative prose."""
    additional_data = step_input.additional_data or {}
    narrative_writer = additional_data.get("narrative_writer")
    narrative_schema = additional_data.get("narrative_schema")
    user_id = additional_data.get("user_id")

    if not narrative_writer:
        return StepOutput(content="ERROR: narrative_writer agent not provided", success=False, stop=True)

    logger.info("[Journal v1.1] Step 3: Writing narrative...")

    try:
        # Get summarize output
        summarize_output = step_input.previous_step_outputs.get("Summarize")
        if not summarize_output:
            return StepOutput(content="ERROR: Cannot find Summarize output", success=False, stop=True)

        summarize_data = json.loads(summarize_output.content)
        summary = summarize_data.get("summary", {})
        target_date = summarize_data.get("target_date")
        message_count = summarize_data.get("message_count", 0)
        session_count = summarize_data.get("session_count", 0)

        # Handle no activity case
        if message_count == 0:
            logger.info("[Journal v1.1] No activity to write narrative for")
            return StepOutput(content=json.dumps({
                "narrative": "No activity recorded for this day.",
                "topics": [],
                "key_achievements": [],
                "target_date": target_date,
                "message_count": 0,
                "session_count": 0
            }))

        # Get user name from admin profile if available
        user_name = _get_user_name(user_id)

        # Build prompt for narrative writer
        morning_activities = summary.get("morning", [])
        afternoon_activities = summary.get("afternoon", [])
        evening_activities = summary.get("evening", [])
        outcomes = summary.get("outcomes", [])
        topics = summary.get("topics", [])

        prompt = f"""Date: {target_date}
User Name: {user_name or "the user"}

Activities by time of day:

MORNING:
{chr(10).join(f"- {a}" for a in morning_activities) if morning_activities else "(No morning activities)"}

AFTERNOON:
{chr(10).join(f"- {a}" for a in afternoon_activities) if afternoon_activities else "(No afternoon activities)"}

EVENING:
{chr(10).join(f"- {a}" for a in evening_activities) if evening_activities else "(No evening activities)"}

KEY OUTCOMES:
{chr(10).join(f"- {o}" for o in outcomes) if outcomes else "(No specific outcomes noted)"}

TOPICS DISCUSSED:
{', '.join(topics) if topics else "general conversation"}

Transform this into a warm, diary-style narrative entry. Remember to skip time periods with no activities."""

        logger.info(f"[Journal v1.1] Sending to narrative writer (user: {user_name or 'unknown'})")

        # Call narrative writer agent with schema for structured output
        response = await narrative_writer.arun(prompt, response_model=narrative_schema)

        # Parse response - handle both structured and plain text responses
        narrative_dict = _parse_agent_response(response)

        logger.info(f"[Journal v1.1] Narrative response parsed: topics={narrative_dict.get('topics')}, achievements={narrative_dict.get('key_achievements')}")

        # Extract narrative with fallback
        narrative = narrative_dict.get("narrative", "")

        # If parsing failed but we have plain text content, use that as the narrative
        if not narrative and hasattr(response, 'content') and isinstance(response.content, str):
            # The agent returned plain text narrative - use it directly
            narrative = response.content.strip()
            logger.info(f"[Journal v1.1] Using plain text narrative from content ({len(narrative)} chars)")

        if not narrative:
            # Final fallback if nothing worked
            narrative = "A day of activities with Cirkelline."

        # Always use topics/outcomes from summarizer - more reliable than narrative writer
        # The narrative writer's job is just to write prose, not extract data
        final_topics = topics if topics else narrative_dict.get("topics", [])
        final_achievements = outcomes if outcomes else narrative_dict.get("key_achievements", [])

        logger.info(f"[Journal v1.1] Final output: topics={final_topics}, achievements={final_achievements}")

        output_data = {
            "narrative": narrative,
            "topics": final_topics,
            "key_achievements": final_achievements,
            "target_date": target_date,
            "message_count": message_count,
            "session_count": session_count
        }

        # Track step progress
        run_id = additional_data.get("run_id")
        if run_id:
            _track_step(run_id, "Write Narrative", 3, {"narrative_length": len(narrative)})

        logger.info(f"[Journal v1.1] Narrative written: {len(narrative)} chars")

        return StepOutput(content=json.dumps(output_data, ensure_ascii=False))

    except Exception as e:
        logger.error(f"[Journal v1.1] Error writing narrative: {e}", exc_info=True)
        return StepOutput(content=f"ERROR: Failed to write narrative: {str(e)}", success=False, stop=True)


# =============================================================================
# STEP 4: SAVE JOURNAL
# =============================================================================

async def save_journal(step_input: StepInput) -> StepOutput:
    """Step 4: Save journal entry to database."""
    additional_data = step_input.additional_data or {}
    user_id = additional_data.get("user_id")

    logger.info("[Journal v1.1] Step 4: Saving journal entry...")

    try:
        # Get narrative output (from Write Narrative step)
        narrative_output = step_input.previous_step_outputs.get("Write Narrative")
        if not narrative_output:
            return StepOutput(content="ERROR: Cannot find Write Narrative output", success=False, stop=True)

        narrative_data = json.loads(narrative_output.content)
        narrative = narrative_data.get("narrative", "")
        target_date = narrative_data.get("target_date")
        message_count = narrative_data.get("message_count", 0)
        session_count = narrative_data.get("session_count", 0)
        topics = narrative_data.get("topics", [])
        achievements = narrative_data.get("key_achievements", [])

        logger.info(f"[Journal v1.1] Save step received: topics={topics}, achievements={achievements}")

        # Get fetch output for session IDs
        fetch_output = step_input.previous_step_outputs.get("Fetch Sessions")
        fetch_data = json.loads(fetch_output.content) if fetch_output else {}
        sessions = fetch_data.get("sessions", [])
        session_ids = [s.get("session_id") for s in sessions if s.get("session_id")]

        # Format journal with narrative prose
        summary_text = _format_journal_with_narrative(target_date, narrative, topics, achievements, user_id)

        # Prepare data for database
        topics_json = json.dumps(topics)
        outcomes_json = json.dumps(achievements)
        sessions_json = json.dumps(session_ids)
        created_at = int(time.time())

        with _shared_engine.connect() as conn:
            # Use UPSERT to handle unique constraint
            # Note: Using CAST() instead of :: for JSONB to avoid SQLAlchemy parameter binding conflict
            result = conn.execute(
                text("""
                    INSERT INTO ai.user_journals
                        (user_id, journal_date, summary, topics, outcomes, sessions_processed, message_count, created_at)
                    VALUES
                        (:user_id, :journal_date, :summary, CAST(:topics AS jsonb), CAST(:outcomes AS jsonb), CAST(:sessions AS jsonb), :message_count, :created_at)
                    ON CONFLICT (user_id, journal_date)
                    DO UPDATE SET
                        summary = EXCLUDED.summary,
                        topics = EXCLUDED.topics,
                        outcomes = EXCLUDED.outcomes,
                        sessions_processed = EXCLUDED.sessions_processed,
                        message_count = EXCLUDED.message_count,
                        created_at = EXCLUDED.created_at
                    RETURNING id
                """),
                {
                    "user_id": user_id,
                    "journal_date": target_date,
                    "summary": summary_text,
                    "topics": topics_json,
                    "outcomes": outcomes_json,
                    "sessions": sessions_json,
                    "message_count": message_count,
                    "created_at": created_at
                }
            )
            journal_id = result.scalar()
            conn.commit()

        logger.info(f"[Journal v1.1] Saved journal entry {journal_id} for {target_date}")

        output_data = {
            "journal_id": journal_id,
            "target_date": target_date,
            "message_count": message_count,
            "session_count": session_count,
            "topics": topics,
            "outcomes": achievements
        }

        # Track step progress
        run_id = additional_data.get("run_id")
        if run_id:
            _track_step(run_id, "Save Journal", 4, {"journal_id": journal_id})

        return StepOutput(content=json.dumps(output_data, ensure_ascii=False))

    except Exception as e:
        logger.error(f"[Journal v1.1] Error saving journal: {e}", exc_info=True)
        return StepOutput(content=f"ERROR: Failed to save journal: {str(e)}", success=False, stop=True)


def _format_journal_with_narrative(target_date: str, narrative: str, topics: list, achievements: list, user_id: str = None) -> str:
    """Format journal entry with narrative prose (v1.1.0)."""
    lines = []

    # Header with day number (sequential journal entry number)
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")

        # Get journal count to calculate "Day X" (sequential journal entry number)
        # Day 1 = first journal, Day 2 = second journal, etc.
        day_num = None
        logger.info(f"[Journal] Formatting journal - user_id={user_id}, target_date={target_date}")
        if user_id:
            journal_count = _get_user_journal_count(user_id, target_date)
            day_num = journal_count + 1  # This journal will be Day (count + 1)
            logger.info(f"[Journal] Calculated day_num={day_num} (count={journal_count})")

        if day_num and day_num > 0:
            lines.append(f"Day {day_num} - {dt.strftime('%B %d, %Y')}")
        else:
            lines.append(f"{dt.strftime('%A, %B %d, %Y')}")  # Fallback: just the date
    except:
        lines.append(f"Journal - {target_date}")

    lines.append("")

    # Narrative body
    if narrative:
        lines.append(narrative)
    else:
        lines.append("No activity recorded for this day.")

    # NOTE: Topics and achievements are stored separately in the database
    # and displayed in the UI from there - no need to duplicate in the text

    return "\n".join(lines)


# =============================================================================
# STEP 5: GENERATE REPORT
# =============================================================================

async def generate_report(step_input: StepInput) -> StepOutput:
    """Step 5: Generate final summary report."""
    additional_data = step_input.additional_data or {}

    logger.info("[Journal v1.1] Step 5: Generating report...")

    try:
        # Get save output
        save_output = step_input.previous_step_outputs.get("Save Journal")
        if not save_output:
            return StepOutput(content="ERROR: Cannot find Save Journal output", success=False, stop=True)

        save_data = json.loads(save_output.content)

        journal_id = save_data.get("journal_id")
        target_date = save_data.get("target_date")
        message_count = save_data.get("message_count", 0)
        session_count = save_data.get("session_count", 0)
        topics = save_data.get("topics", [])
        outcomes = save_data.get("outcomes", [])

        # Build report
        report_lines = [
            "=" * 50,
            "DAILY JOURNAL WORKFLOW REPORT",
            "=" * 50,
            "",
            f"Date: {target_date}",
            f"Journal ID: {journal_id}",
            "",
            "STATS:",
            f"- Sessions processed: {session_count}",
            f"- Messages summarized: {message_count}",
            f"- Topics identified: {len(topics)}",
            f"- Key outcomes: {len(outcomes)}",
            "",
            "TOPICS:",
        ]

        for topic in topics[:10]:
            report_lines.append(f"  - {topic}")

        report_lines.append("")
        report_lines.append("OUTCOMES:")

        for outcome in outcomes[:10]:
            report_lines.append(f"  - {outcome}")

        report_lines.append("")
        report_lines.append("=" * 50)
        report_lines.append("Journal entry saved successfully!")
        report_lines.append("=" * 50)

        report = "\n".join(report_lines)

        # Track step progress
        run_id = additional_data.get("run_id")
        if run_id:
            _track_step(run_id, "Report", 5, {"success": True})

        logger.info(f"[Journal v1.1] Report generated for {target_date}")

        return StepOutput(content=report)

    except Exception as e:
        logger.error(f"[Journal v1.1] Error generating report: {e}")
        return StepOutput(content=f"ERROR: Failed to generate report: {str(e)}", success=False, stop=True)
