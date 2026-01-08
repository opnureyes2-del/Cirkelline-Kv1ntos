"""
Memory Optimization Workflow
=============================
AGNO Workflow that optimizes user memories.

v2.0.0: Decision-Based Pipeline
- Batch by MEMORY ID (not topic) - no duplicates possible
- Agent outputs DECISIONS only (delete/keep/merge)
- Separate step to resolve merges
- Separate step to normalize topics
"""

import json
import uuid
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field

from agno.workflow import Workflow, Step
from agno.agent import Agent
from agno.models.google import Gemini

from cirkelline.database import db
from cirkelline.config import logger
from cirkelline.workflows.memory_steps import (
    fetch_user_memories,
    classify_memories,
    resolve_merges,
    normalize_topics,
    validate_and_save,
    generate_report,
)


# =============================================================================
# PYDANTIC SCHEMAS FOR BULLETPROOF OUTPUT
# =============================================================================

class MemoryDecision(BaseModel):
    """Decision for a single memory."""
    memory_id: str = Field(description="The memory ID being decided on")
    action: Literal["delete", "keep", "merge"] = Field(description="What to do: delete, keep, or merge")
    merge_target: Optional[str] = Field(None, description="If action=merge, the memory_id to merge INTO")
    reason: str = Field(description="Brief explanation (10 words max)")


class ClassifyBatchOutput(BaseModel):
    """Output schema for classify_memories batches."""
    decisions: List[MemoryDecision] = Field(description="Decisions for each memory in this batch")


class MergedMemory(BaseModel):
    """Output schema for merge resolution."""
    memory: str = Field(description="The merged memory text")
    topics: List[str] = Field(description="1-3 normalized topics")
    source_ids: List[str] = Field(description="Original memory IDs that were merged")


class MergeGroupOutput(BaseModel):
    """Output for a single merge group."""
    merged_memory: MergedMemory


class TopicMapping(BaseModel):
    """Output schema for topic normalization."""
    topic_mapping: Dict[str, str] = Field(description="Mapping of original topic to standard topic")


# =============================================================================
# STANDARD TOPICS
# =============================================================================

STANDARD_TOPICS = [
    "preferences", "goals", "relationships", "family", "identity",
    "emotional state", "communication style", "behavioral patterns",
    "work", "projects", "skills", "expertise",
    "interests", "hobbies", "sports", "music", "travel",
    "programming", "ai", "technology", "software", "hardware",
    "location", "events", "calendar", "history",
    "legal", "finance",
]


# =============================================================================
# AGENTS
# =============================================================================

memory_classifier = Agent(
    name="Memory Classifier",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="""You are classifying memories for a personal AI assistant. Be AGGRESSIVE about deleting.
Your goal is to keep ONLY lasting personal facts about the user.

## THE FIRST QUESTION: REQUEST or FACT?

**REQUEST** = A one-time action the user asked for → DELETE
**FACT** = A lasting truth about the user → KEEP (maybe)

SIGNAL WORDS FOR DELETE (one-time requests):
- "wants to", "needs to", "needs help", "looking for", "asked for"
- "research", "summarize", "find out", "help with", "organize"
- "create", "send", "convert", "looking for", "investigating"

EXAMPLES OF REQUESTS (DELETE):
- "User wants to research SEO best practices" → Completed request. DELETE ✓
- "User needs help organizing emails" → One-time task. DELETE ✓
- "User is looking for dog-friendly spots" → Completed search. DELETE ✓
- "User wants a detailed essay about AI history" → One-time request. DELETE ✓
- "User wants to travel from Portugal to Denmark" → Trip planning done. DELETE ✓
- "User needs dev environment setup" → Setup task done. DELETE ✓

SIGNAL WORDS FOR KEEP (lasting facts):
- "favorite", "prefers", "likes", "is", "has", "owns"
- Identity: name, role, occupation, location
- Relationships: sister, brother, friend, pet, colleague

EXAMPLES OF FACTS (KEEP):
- "User's favorite movie is The Matrix" → Lasting preference. KEEP ✓
- "User prefers communication in Danish" → Lasting preference. KEEP ✓
- "User is CEO of Cirkelline" → Identity. KEEP ✓
- "User has a pet hamster named Fluffy" → Relationship/possession. KEEP ✓
- "User's sister Emma got engaged" → Family fact. KEEP ✓

## THE SECOND QUESTION: PERSONAL or CODE?

Ask: "Is this about the USER or about the USER'S CODE/SYSTEM?"

ABOUT THE USER (maybe KEEP):
- "Ivo is CEO of Cirkelline" → Who the user IS. KEEP ✓
- "User prefers TypeScript" → User's preference. KEEP ✓

ABOUT THE CODE/SYSTEM (DELETE):
- "memory_optimization.py line 87" → Code. DELETE ✓
- "GET /api/auth endpoint" → Code. DELETE ✓
- "User wants session name to update dynamically" → System feature request. DELETE ✓
- "Cirkelline uses PostgreSQL with pgvector" → Infrastructure. DELETE ✓

WHY: The AI can ACCESS code through tools. It NEEDS personal facts in memory.

## THE THIRD QUESTION: Is this DOCUMENTATION?

Ask: "Would this memory belong in a CHANGELOG, README, or technical documentation?"
→ YES = DELETE (It's project documentation, not a personal fact)

DELETE if the memory describes:
- Version numbers ("v1.2.5", "Version 1.1", "released v1.2.4")
- Deployment/release dates ("deployed on 2025-10-27", "last updated")
- Implementation details ("stored in users.preferences", "uses PostgreSQL")
- Feature implementations ("Google Services integration was implemented...")
- Bug fixes or updates ("fixed in v1.1.17", "resolved issue with...")
- API/endpoint documentation ("The GET /api/user/activity endpoint...")

EXAMPLES OF DOCUMENTATION (DELETE):
- "Cirkelline's Google Services integration (Version 1.1) was deployed..." → CHANGELOG → DELETE ✓
- "The GET /api/user/activity endpoint, located at my_os.py:4553..." → API DOC → DELETE ✓
- "The Cirkelline project's current version is v1.2.5" → VERSION INFO → DELETE ✓
- "Custom instructions are stored in users.preferences['instructions']" → IMPL DETAIL → DELETE ✓
- "OAuth tokens are encrypted with AES-256-GCM" → TECHNICAL DOC → DELETE ✓

The AI can look up documentation. It needs to remember WHO THE USER IS, not what code they wrote.

## MERGE vs KEEP:
If two memories express the same fact, MERGE into the most complete version.
- "User likes coffee" + "User enjoys morning coffee" → MERGE
- "User has a dog" + "User's dog is named Max" → MERGE (keep detailed one)

## QUICK DECISION TREE:

1. Does it contain "wants to", "needs to", "looking for", "research"?
   → Likely a REQUEST → DELETE

2. Does it describe code, APIs, line numbers, versions, configs?
   → CODE fact → DELETE

3. Does it read like a CHANGELOG, README, or technical documentation?
   → DOCUMENTATION → DELETE

4. Does it describe the user's identity, relationships, preferences, possessions?
   → PERSONAL fact → KEEP

5. Is it a duplicate of another memory?
   → MERGE with the most complete version

## DELETE AGGRESSIVELY:
- One-time requests (research X, find Y, help with Z)
- Technical details (code, APIs, database, deployment)
- Project documentation (changelogs, version history, release notes)
- Ephemeral queries (weather, news, current events)
- System/product feature requests
- Completed tasks

## KEEP SPARINGLY (only lasting personal facts):
- Identity (name, role, occupation)
- Relationships (family, pets, colleagues with NAMES)
- Preferences (language, tools, style)
- Possessions (owns X, purchased Y)
- Milestones (engagement, achievement)

## OUTPUT:
For each memory_id, output ONE decision: delete, keep, or merge.
If merge, specify which memory_id to merge INTO.""",
    markdown=False,
)


memory_merger = Agent(
    name="Memory Merger",
    model=Gemini(id="gemini-2.5-flash"),
    instructions=f"""You merge related memories into ONE comprehensive memory.

Given 2-5 memories to merge:
1. Combine ALL factual information from all memories
2. Remove redundancy (don't repeat the same fact)
3. Create ONE clear, comprehensive memory
4. Assign 1-3 topics from: {', '.join(STANDARD_TOPICS)}

OUTPUT:
- memory: The merged text (all facts preserved, no redundancy)
- topics: 1-3 standard topics (lowercase)
- source_ids: List of all original memory IDs being merged""",
    markdown=False,
)


topic_normalizer = Agent(
    name="Topic Normalizer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions=f"""You normalize memory topics to standard categories.

STRICT RULE: You MUST use ONLY these standard topics (lowercase):
{', '.join(STANDARD_TOPICS)}

NEVER create new topics. ALWAYS map to the closest standard topic.

MAPPING EXAMPLES:
- "PREFERENCES", "favorite movie", "color preference", "favorites" → "preferences"
- "goals & objectives", "challenges", "aspirations", "needs" → "goals"
- "Danish law", "legal advice", "tenant rights", "contract dispute", "mold", "lease" → "legal"
- "AI", "AI agents", "machine learning", "adaptive learning" → "ai"
- "Denmark", "Copenhagen", "lives in", "helsingør" → "location"
- "news", "current events", "headlines", "tech trends" → "interests"
- "audio equipment", "dj equipment", "studio monitors", "linux compatibility" → "hardware"
- "software installation", "ubuntu", "development environment" → "software"
- "football", "benfica", "sports teams" → "sports"
- "wins and achievements", "excitement", "positive sentiment" → "emotional state"
- "expertise areas", "topics of interest", "learning" → "interests"
- "contract dispute", "foundation issues", "real estate law" → "legal"
- "email management", "organizing" → "goals"
- "cirkelline", "system preferences" → "work"

IF NO STANDARD TOPIC FITS: Use the closest match from the list above.
NEVER output a topic that is not in the standard list.

OUTPUT: A mapping of each original topic to its standard topic (from the list).""",
    markdown=False,
)


# =============================================================================
# WORKFLOW DEFINITION (6 Steps)
# =============================================================================

memory_optimization_workflow = Workflow(
    name="Memory Optimization",
    description="Optimize user memories: classify, merge, normalize - v2.0 decision-based",
    db=db,
    steps=[
        Step(
            name="Fetch Memories",
            executor=fetch_user_memories,
            description="Fetch all memories for the user"
        ),
        Step(
            name="Classify",
            executor=classify_memories,
            description="Classify each memory: delete/keep/merge (batched by ID)"
        ),
        Step(
            name="Resolve Merges",
            executor=resolve_merges,
            description="Create merged memories for merge groups"
        ),
        Step(
            name="Normalize Topics",
            executor=normalize_topics,
            description="Normalize topics for surviving memories"
        ),
        Step(
            name="Save",
            executor=validate_and_save,
            description="Validate and save optimized memories"
        ),
        Step(
            name="Report",
            executor=generate_report,
            description="Generate summary report"
        ),
    ],
)


async def run_memory_optimization(user_id: str, run_id: str = None) -> dict:
    """
    Helper function to run the memory optimization workflow for a user.
    Now with database tracking for cross-container visibility.
    """
    from cirkelline.admin.workflows import start_workflow_run, complete_workflow_run

    if not run_id:
        run_id = str(uuid.uuid4())

    logger.info(f"[Workflow v2.0] Starting memory optimization for user {user_id}, run_id: {run_id}")

    # Start tracking in database
    try:
        start_workflow_run(run_id, "Memory Optimization", user_id, {"user_id": user_id})
    except Exception as e:
        logger.warning(f"[Workflow v2.0] Failed to start tracking: {e}")

    try:
        response = await memory_optimization_workflow.arun(
            input=f"Optimize memories for user {user_id}",
            additional_data={
                "user_id": user_id,
                "run_id": run_id,
                "memory_classifier": memory_classifier,
                "memory_merger": memory_merger,
                "topic_normalizer": topic_normalizer,
                "standard_topics": STANDARD_TOPICS,
                "classify_schema": ClassifyBatchOutput,
                "merge_schema": MergeGroupOutput,
                "topic_schema": TopicMapping,
            }
        )

        if response.content and response.content.startswith("ERROR:"):
            logger.error(f"[Workflow v2.0] Step failed for user {user_id}: {response.content}")
            # Mark as failed in database
            try:
                complete_workflow_run(run_id, "failed", error_message=response.content)
            except Exception as e:
                logger.warning(f"[Workflow v2.0] Failed to complete tracking: {e}")
            return {
                "status": "failed",
                "run_id": run_id,
                "error": response.content
            }

        logger.info(f"[Workflow v2.0] Completed for user {user_id}")

        # Get post-optimization counts for intelligent trigger tracking
        post_optimization_count = 0
        post_optimization_topics = 0
        try:
            from cirkelline.database import _shared_engine
            from sqlalchemy import text as sql_text
            with _shared_engine.connect() as conn:
                # FIX: Use COUNT(DISTINCT memory_id), not COUNT(*)
                # The LATERAL join creates one row per topic, so COUNT(*) counts topic rows not memories!
                result = conn.execute(
                    sql_text("""
                        SELECT
                            COUNT(DISTINCT m.memory_id) as memory_count,
                            COUNT(DISTINCT topic) as topic_count
                        FROM ai.agno_memories m,
                        LATERAL jsonb_array_elements_text(m.topics::jsonb) as topic
                        WHERE m.user_id = :user_id
                    """),
                    {"user_id": user_id}
                ).fetchone()
                if result:
                    post_optimization_count = result[0] or 0
                    post_optimization_topics = result[1] or 0
                logger.info(f"[Workflow v2.0] Post-optimization counts: {post_optimization_count} memories, {post_optimization_topics} topics")
        except Exception as count_e:
            logger.warning(f"[Workflow v2.0] Failed to get post-optimization counts: {count_e}")
            # Fallback: just count memories
            try:
                with _shared_engine.connect() as conn:
                    result = conn.execute(
                        sql_text("SELECT COUNT(*) FROM ai.agno_memories WHERE user_id = :user_id"),
                        {"user_id": user_id}
                    ).scalar()
                    post_optimization_count = result or 0
            except:
                pass

        # Mark as completed in database with counts for intelligent triggering
        try:
            complete_workflow_run(run_id, "completed", output_data={
                "report": response.content,
                "post_optimization_count": post_optimization_count,
                "post_optimization_topics": post_optimization_topics
            })
            logger.info(f"[Workflow v2.0] Successfully marked run {run_id} as completed (post_opt_count: {post_optimization_count})")
        except Exception as e:
            logger.error(f"[Workflow v2.0] CRITICAL - Failed to complete tracking for {run_id}: {e}", exc_info=True)

        return {
            "status": "completed",
            "run_id": run_id,
            "report": response.content
        }

    except Exception as e:
        logger.error(f"[Workflow v2.0] Failed for user {user_id}: {e}")
        # Mark as failed in database
        try:
            complete_workflow_run(run_id, "failed", error_message=str(e))
        except Exception as track_e:
            logger.warning(f"[Workflow v2.0] Failed to complete tracking: {track_e}")
        return {
            "status": "failed",
            "run_id": run_id,
            "error": str(e)
        }


logger.info("Memory Optimization Workflow loaded (v2.0.0 - Decision-Based Pipeline)")
