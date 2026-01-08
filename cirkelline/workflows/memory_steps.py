"""
Memory Optimization Workflow - Function Steps
==============================================
v2.0.0: Decision-Based Pipeline

Steps:
1. fetch_user_memories - Get all memories for user
2. classify_memories - Batch by MEMORY ID, output DECISIONS only
3. resolve_merges - Create merged memories for merge groups
4. normalize_topics - Normalize topics for survivors
5. validate_and_save - Validate and save optimized memories
6. generate_report - Summary
"""

import json
import uuid
import time
from datetime import datetime
from typing import Set, Dict, List, Optional
from collections import defaultdict

from sqlalchemy import text
from agno.workflow.types import StepInput, StepOutput

from cirkelline.database import _shared_engine
from cirkelline.config import logger


def _track_step(run_id: str, step_name: str, step_number: int, stats: dict = None):
    """Track step progress in database."""
    try:
        from cirkelline.admin.workflows import update_workflow_step
        update_workflow_step(run_id, step_name, step_number, 6, stats)
    except Exception as e:
        logger.warning(f"[Step Tracking] Failed to track step {step_name}: {e}")


# =============================================================================
# STEP 1: FETCH USER MEMORIES
# =============================================================================

async def fetch_user_memories(step_input: StepInput) -> StepOutput:
    """Step 1: Fetch all memories for the user."""
    additional_data = step_input.additional_data or {}
    user_id = additional_data.get("user_id")

    if not user_id:
        return StepOutput(content="ERROR: No user_id provided", success=False, stop=True)

    logger.info(f"[Workflow v2.0] Step 1: Fetching memories for user: {user_id}")

    try:
        with _shared_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT memory_id, memory, topics, updated_at, created_at
                    FROM ai.agno_memories
                    WHERE user_id = :user_id
                    ORDER BY updated_at DESC
                """),
                {"user_id": user_id}
            )
            rows = result.fetchall()

        all_topics: Set[str] = set()
        memories = []

        for row in rows:
            memory_id = str(row[0])
            memory_content = row[1] if isinstance(row[1], str) else str(row[1])
            topics = row[2] if row[2] else []
            updated_ts = row[3]
            created_ts = row[4]

            all_topics.update(topics)

            # v1.3.3: Handle both SECONDS and MILLISECONDS formats
            # Timestamps > 4102444800 (year 2100) are in milliseconds, need to divide
            if updated_ts and updated_ts > 4102444800:
                updated_ts = updated_ts / 1000
            if created_ts and created_ts > 4102444800:
                created_ts = created_ts / 1000

            memories.append({
                "memory_id": memory_id,
                "memory": memory_content,
                "topics": topics,
                "updated_at": datetime.fromtimestamp(updated_ts).isoformat() if updated_ts else None,
                "created_at": datetime.fromtimestamp(created_ts).isoformat() if created_ts else None,
            })

        logger.info(f"[Workflow v2.0] Fetched {len(memories)} memories with {len(all_topics)} unique topics")

        output_data = {
            "memories": memories,
            "unique_topics": list(all_topics),
            "stats": {
                "count": len(memories),
                "unique_topics": len(all_topics),
                "user_id": user_id
            }
        }

        # Track step progress
        run_id = additional_data.get("run_id")
        if run_id:
            _track_step(run_id, "Fetch Memories", 1, {"memories_fetched": len(memories)})

        return StepOutput(content=json.dumps(output_data, ensure_ascii=False))

    except Exception as e:
        logger.error(f"[Workflow v2.0] Error fetching memories: {e}")
        return StepOutput(content=f"ERROR: Failed to fetch memories: {str(e)}", success=False, stop=True)


# =============================================================================
# STEP 2: CLASSIFY MEMORIES (Decision-Based)
# =============================================================================

async def classify_memories(step_input: StepInput) -> StepOutput:
    """
    Step 2: Classify each memory with DECISIONS only.

    Key v2.0 changes:
    - Batch by MEMORY ID (not topic) - each ID appears in exactly ONE batch
    - Agent outputs DECISIONS only (delete/keep/merge with merge_target)
    - Small output = reliable JSON
    """
    additional_data = step_input.additional_data or {}
    memory_classifier = additional_data.get("memory_classifier")
    classify_schema = additional_data.get("classify_schema")

    if not memory_classifier:
        return StepOutput(content="ERROR: memory_classifier agent not provided", success=False, stop=True)

    logger.info("[Workflow v2.0] Step 2: Classifying memories (decision-based)...")

    try:
        # Get fetch output
        fetch_output = step_input.previous_step_outputs.get("Fetch Memories")
        if not fetch_output:
            return StepOutput(content="ERROR: Cannot find Fetch Memories output", success=False, stop=True)

        fetch_data = json.loads(fetch_output.content)
        memories = fetch_data.get("memories", [])

        if not memories:
            logger.info("[Workflow v2.0] No memories to classify")
            return StepOutput(content=json.dumps({
                "decisions": [],
                "stats": {"total": 0, "delete": 0, "keep": 0, "merge": 0}
            }))

        # Build FULL context (agent sees everything for intelligent decisions)
        all_memories_context = []
        for mem in memories:
            all_memories_context.append({
                "id": mem["memory_id"],
                "text": mem["memory"],
                "topics": mem.get("topics", [])
            })

        full_context = json.dumps(all_memories_context, ensure_ascii=False)

        # Batch by MEMORY ID (20 per batch)
        BATCH_SIZE = 20
        memory_ids = [m["memory_id"] for m in memories]
        batches = [memory_ids[i:i + BATCH_SIZE] for i in range(0, len(memory_ids), BATCH_SIZE)]

        all_decisions = []
        stats = {"delete": 0, "keep": 0, "merge": 0}

        for batch_idx, batch_ids in enumerate(batches):
            logger.info(f"[Workflow v2.0]   Batch {batch_idx + 1}/{len(batches)}: {len(batch_ids)} memories")

            # Determine data state for intelligent classification
            data_state = "RAW" if len(memories) > 100 else "CURATED"
            data_guidance = (
                "This appears to be RAW data with many memories. Look for duplicates, ephemeral queries, and junk to clean up."
                if data_state == "RAW" else
                "This appears to be CURATED data with fewer memories. These likely already survived optimization - be conservative, when in doubt KEEP."
            )

            prompt = f"""DATA STATE: {data_state} ({len(memories)} total memories)
{data_guidance}

FULL CONTEXT (all {len(memories)} memories):
{full_context}

YOUR TASK: Decide on ONLY these {len(batch_ids)} memory IDs:
{json.dumps(batch_ids)}

For each ID, output ONE decision: delete, keep, or merge.
If merge, specify which memory_id to merge INTO (the best/most complete one).

Remember: Ask yourself "Would the user want their AI to remember this?" - if yes or uncertain, KEEP."""

            try:
                response = await memory_classifier.arun(
                    input=prompt,
                    output_schema=classify_schema
                )

                # Parse response
                batch_decisions = []

                if hasattr(response.content, 'decisions'):
                    # Pydantic object
                    for d in response.content.decisions:
                        batch_decisions.append({
                            "memory_id": d.memory_id,
                            "action": d.action,
                            "merge_target": d.merge_target,
                            "reason": d.reason
                        })
                elif isinstance(response.content, dict):
                    batch_decisions = response.content.get("decisions", [])
                elif isinstance(response.content, str):
                    try:
                        result = json.loads(response.content)
                        batch_decisions = result.get("decisions", [])
                    except:
                        logger.warning(f"[Workflow v2.0] Could not parse batch {batch_idx + 1} response")

                # Count stats
                for d in batch_decisions:
                    action = d.get("action", "keep")
                    stats[action] = stats.get(action, 0) + 1

                all_decisions.extend(batch_decisions)

            except Exception as e:
                logger.error(f"[Workflow v2.0] Error in batch {batch_idx + 1}: {e}")
                # Fallback: keep all in batch
                for mid in batch_ids:
                    all_decisions.append({
                        "memory_id": mid,
                        "action": "keep",
                        "merge_target": None,
                        "reason": "Fallback due to error"
                    })
                    stats["keep"] += 1

        logger.info(f"[Workflow v2.0] Classification complete: delete={stats['delete']}, keep={stats['keep']}, merge={stats['merge']}")

        output_data = {
            "decisions": all_decisions,
            "memories": memories,  # Pass through for next steps
            "stats": {
                "total": len(memories),
                **stats
            }
        }

        # Track step progress
        run_id = additional_data.get("run_id")
        if run_id:
            _track_step(run_id, "Classify", 2, {"deleted": stats['delete'], "kept": stats['keep'], "merged": stats['merge']})

        return StepOutput(content=json.dumps(output_data, ensure_ascii=False))

    except Exception as e:
        logger.error(f"[Workflow v2.0] Error in classify_memories: {e}")
        return StepOutput(content=f"ERROR: Classification failed: {str(e)}", success=False, stop=True)


# =============================================================================
# STEP 3: RESOLVE MERGES
# =============================================================================

async def resolve_merges(step_input: StepInput) -> StepOutput:
    """
    Step 3: Create merged memories for merge groups.

    Input: decisions with action=merge + merge_target
    Output: merged_memories list + surviving_memories list
    """
    additional_data = step_input.additional_data or {}
    memory_merger = additional_data.get("memory_merger")
    merge_schema = additional_data.get("merge_schema")

    logger.info("[Workflow v2.0] Step 3: Resolving merges...")

    try:
        # Get classify output
        classify_output = step_input.previous_step_outputs.get("Classify")
        if not classify_output:
            return StepOutput(content="ERROR: Cannot find Classify output", success=False, stop=True)

        classify_data = json.loads(classify_output.content)
        decisions = classify_data.get("decisions", [])
        memories = classify_data.get("memories", [])

        # Build memory lookup
        memory_lookup = {m["memory_id"]: m for m in memories}

        # Build decision lookup
        decision_lookup = {d["memory_id"]: d for d in decisions}

        # Group merges by target
        merge_groups: Dict[str, List[str]] = defaultdict(list)

        for d in decisions:
            if d.get("action") == "merge" and d.get("merge_target"):
                target = d["merge_target"]
                source = d["memory_id"]
                # Both target and source go into the merge group
                if target not in merge_groups[target]:
                    merge_groups[target].append(target)
                if source not in merge_groups[target]:
                    merge_groups[target].append(source)

        logger.info(f"[Workflow v2.0] Found {len(merge_groups)} merge groups")

        # Track which IDs are consumed by merges
        merged_source_ids = set()
        for target, sources in merge_groups.items():
            merged_source_ids.update(sources)

        # Process merge groups
        merged_memories = []

        if memory_merger and merge_groups:
            for target_id, source_ids in merge_groups.items():
                # Get all source memories
                source_memories = []
                for sid in source_ids:
                    if sid in memory_lookup:
                        source_memories.append(memory_lookup[sid])

                if len(source_memories) < 2:
                    # Not enough to merge, keep the target as-is
                    if target_id in memory_lookup:
                        mem = memory_lookup[target_id]
                        merged_memories.append({
                            "memory": mem["memory"],
                            "topics": mem.get("topics", []),
                            "source_ids": [target_id],
                            "is_merged": False
                        })
                    continue

                # Build merge prompt
                merge_prompt = f"""MERGE THESE {len(source_memories)} MEMORIES INTO ONE:

{json.dumps([{"id": m["memory_id"], "text": m["memory"], "topics": m.get("topics", [])} for m in source_memories], ensure_ascii=False)}

Combine ALL facts, remove redundancy, create ONE comprehensive memory."""

                try:
                    response = await memory_merger.arun(
                        input=merge_prompt,
                        output_schema=merge_schema
                    )

                    # Parse response
                    merged = None

                    if hasattr(response.content, 'merged_memory'):
                        m = response.content.merged_memory
                        merged = {
                            "memory": m.memory,
                            "topics": m.topics,
                            "source_ids": m.source_ids if hasattr(m, 'source_ids') else source_ids,
                            "is_merged": True
                        }
                    elif isinstance(response.content, dict):
                        m = response.content.get("merged_memory", response.content)
                        merged = {
                            "memory": m.get("memory", ""),
                            "topics": m.get("topics", []),
                            "source_ids": m.get("source_ids", source_ids),
                            "is_merged": True
                        }
                    elif isinstance(response.content, str):
                        try:
                            result = json.loads(response.content)
                            m = result.get("merged_memory", result)
                            merged = {
                                "memory": m.get("memory", ""),
                                "topics": m.get("topics", []),
                                "source_ids": m.get("source_ids", source_ids),
                                "is_merged": True
                            }
                        except:
                            logger.warning(f"[Workflow v2.0] Could not parse merge response for {target_id}")

                    if merged and merged.get("memory"):
                        merged_memories.append(merged)
                        logger.info(f"[Workflow v2.0]   Merged {len(source_ids)} memories -> 1")
                    else:
                        # Fallback: keep target memory
                        if target_id in memory_lookup:
                            mem = memory_lookup[target_id]
                            merged_memories.append({
                                "memory": mem["memory"],
                                "topics": mem.get("topics", []),
                                "source_ids": [target_id],
                                "is_merged": False
                            })

                except Exception as e:
                    logger.error(f"[Workflow v2.0] Error merging group {target_id}: {e}")
                    # Fallback: keep target memory
                    if target_id in memory_lookup:
                        mem = memory_lookup[target_id]
                        merged_memories.append({
                            "memory": mem["memory"],
                            "topics": mem.get("topics", []),
                            "source_ids": [target_id],
                            "is_merged": False
                        })
        else:
            logger.info("[Workflow v2.0] No merges to process or no merger agent")

        # Build surviving memories (keep decisions not consumed by merges)
        surviving_memories = []

        for d in decisions:
            mid = d["memory_id"]
            action = d.get("action", "keep")

            if action == "keep" and mid not in merged_source_ids:
                if mid in memory_lookup:
                    mem = memory_lookup[mid]
                    surviving_memories.append({
                        "memory": mem["memory"],
                        "topics": mem.get("topics", []),
                        "source_ids": [mid],
                        "is_merged": False
                    })

        logger.info(f"[Workflow v2.0] Merge resolution: {len(merged_memories)} merged + {len(surviving_memories)} kept = {len(merged_memories) + len(surviving_memories)} total")

        output_data = {
            "merged_memories": merged_memories,
            "surviving_memories": surviving_memories,
            "all_memories": merged_memories + surviving_memories,
            "stats": {
                "merge_groups": len(merge_groups),
                "merged_count": len(merged_memories),
                "kept_count": len(surviving_memories),
                "total_output": len(merged_memories) + len(surviving_memories)
            }
        }

        # Track step progress
        run_id = additional_data.get("run_id")
        if run_id:
            _track_step(run_id, "Resolve Merges", 3, {"merge_groups": len(merge_groups), "total_output": len(merged_memories) + len(surviving_memories)})

        return StepOutput(content=json.dumps(output_data, ensure_ascii=False))

    except Exception as e:
        logger.error(f"[Workflow v2.0] Error in resolve_merges: {e}")
        return StepOutput(content=f"ERROR: Merge resolution failed: {str(e)}", success=False, stop=True)


# =============================================================================
# STEP 4: NORMALIZE TOPICS
# =============================================================================

async def normalize_topics(step_input: StepInput) -> StepOutput:
    """
    Step 4: Normalize topics for all surviving memories.

    Uses topic_normalizer agent to map arbitrary topics to standard set.
    """
    additional_data = step_input.additional_data or {}
    topic_normalizer = additional_data.get("topic_normalizer")
    topic_schema = additional_data.get("topic_schema")
    standard_topics = additional_data.get("standard_topics", [])

    logger.info("[Workflow v2.0] Step 4: Normalizing topics...")

    try:
        # Get merge output
        merge_output = step_input.previous_step_outputs.get("Resolve Merges")
        if not merge_output:
            return StepOutput(content="ERROR: Cannot find Resolve Merges output", success=False, stop=True)

        merge_data = json.loads(merge_output.content)
        all_memories = merge_data.get("all_memories", [])

        if not all_memories:
            logger.info("[Workflow v2.0] No memories to normalize topics for")
            return StepOutput(content=json.dumps({
                "normalized_memories": [],
                "topic_mapping": {},
                "stats": {"original_topics": 0, "normalized_topics": 0}
            }))

        # Collect all unique topics
        all_topics: Set[str] = set()
        for mem in all_memories:
            all_topics.update(mem.get("topics", []))

        logger.info(f"[Workflow v2.0] Found {len(all_topics)} unique topics to normalize")

        # Normalize topics
        topic_mapping = {}

        if topic_normalizer and all_topics:
            prompt = f"""STANDARD TOPICS (use ONLY these, lowercase):
{', '.join(standard_topics)}

TOPICS TO NORMALIZE:
{json.dumps(list(all_topics), ensure_ascii=False)}

Map each original topic to the most appropriate standard topic.
Similar concepts should map to the same standard topic."""

            try:
                response = await topic_normalizer.arun(
                    input=prompt,
                    output_schema=topic_schema
                )

                # Parse response
                if hasattr(response.content, 'topic_mapping'):
                    topic_mapping = response.content.topic_mapping
                elif isinstance(response.content, dict):
                    topic_mapping = response.content.get("topic_mapping", {})
                elif isinstance(response.content, str):
                    try:
                        result = json.loads(response.content)
                        topic_mapping = result.get("topic_mapping", {})
                    except:
                        logger.warning("[Workflow v2.0] Could not parse topic mapping response")

            except Exception as e:
                logger.error(f"[Workflow v2.0] Topic normalization error: {e}")

        # Ensure all topics are mapped (fallback: lowercase)
        for topic in all_topics:
            if topic not in topic_mapping:
                topic_mapping[topic] = topic.lower()

        # Apply topic mapping to memories
        normalized_memories = []
        final_topics: Set[str] = set()

        for mem in all_memories:
            old_topics = mem.get("topics", [])
            new_topics = []

            for t in old_topics:
                normalized = topic_mapping.get(t, t.lower())
                new_topics.append(normalized)

            # Dedupe and limit to 3
            new_topics = list(set(new_topics))[:3]
            final_topics.update(new_topics)

            normalized_memories.append({
                "memory": mem["memory"],
                "topics": new_topics,
                "source_ids": mem.get("source_ids", []),
                "is_merged": mem.get("is_merged", False)
            })

        logger.info(f"[Workflow v2.0] Topic normalization: {len(all_topics)} -> {len(final_topics)} unique topics")

        output_data = {
            "normalized_memories": normalized_memories,
            "topic_mapping": topic_mapping,
            "stats": {
                "original_topics": len(all_topics),
                "normalized_topics": len(final_topics),
                "memory_count": len(normalized_memories)
            }
        }

        # Track step progress
        run_id = additional_data.get("run_id")
        if run_id:
            _track_step(run_id, "Normalize Topics", 4, {"topics_normalized": len(final_topics)})

        return StepOutput(content=json.dumps(output_data, ensure_ascii=False))

    except Exception as e:
        logger.error(f"[Workflow v2.0] Error in normalize_topics: {e}")
        return StepOutput(content=f"ERROR: Topic normalization failed: {str(e)}", success=False, stop=True)


# =============================================================================
# STEP 5: VALIDATE AND SAVE
# =============================================================================

async def validate_and_save(step_input: StepInput) -> StepOutput:
    """
    Step 5: Validate and save optimized memories.

    - Archives old memories (recoverable)
    - Inserts new optimized memories
    """
    additional_data = step_input.additional_data or {}
    user_id = additional_data.get("user_id")
    run_id = additional_data.get("run_id", str(uuid.uuid4()))

    logger.info(f"[Workflow v2.0] Step 5: Validating and saving for user: {user_id}")

    try:
        # Get normalize output
        normalize_output = step_input.previous_step_outputs.get("Normalize Topics")
        if not normalize_output:
            return StepOutput(content="ERROR: Cannot find Normalize Topics output", success=False, stop=True)

        normalize_data = json.loads(normalize_output.content)
        normalized_memories = normalize_data.get("normalized_memories", [])

        # Get original stats from fetch
        fetch_output = step_input.previous_step_outputs.get("Fetch Memories")
        original_count = 0
        if fetch_output:
            try:
                fetch_data = json.loads(fetch_output.content)
                original_count = fetch_data.get("stats", {}).get("count", 0)
            except:
                pass

        # Get classify stats
        classify_output = step_input.previous_step_outputs.get("Classify")
        deleted_count = 0
        if classify_output:
            try:
                classify_data = json.loads(classify_output.content)
                deleted_count = classify_data.get("stats", {}).get("delete", 0)
            except:
                pass

        # Validation
        if len(normalized_memories) == 0 and original_count > 0:
            logger.warning("[Workflow v2.0] Validation: All memories would be deleted - keeping originals")
            return StepOutput(
                content="ERROR: Validation failed - would delete all memories",
                success=False,
                stop=True
            )

        # v1.3.3: Use SECONDS (not milliseconds) to match AGNO's expected format
        current_time_s = int(time.time())

        with _shared_engine.begin() as conn:
            # Archive old memories
            # v1.3.3: Handle both SECONDS and MILLISECONDS formats
            # Timestamps > 4102444800 (year 2100) are in milliseconds
            conn.execute(
                text("""
                    INSERT INTO ai.agno_memories_archive
                    (original_memory_id, user_id, memory, topics, input, created_at, optimization_run_id)
                    SELECT memory_id, user_id, memory, topics, input,
                           TO_TIMESTAMP(CASE WHEN created_at > 4102444800 THEN created_at / 1000.0 ELSE created_at END) as created_at, :run_id
                    FROM ai.agno_memories
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id, "run_id": run_id}
            )

            result = conn.execute(
                text("SELECT COUNT(*) FROM ai.agno_memories WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            archived_count = result.scalar()

            # Delete old memories
            conn.execute(
                text("DELETE FROM ai.agno_memories WHERE user_id = :user_id"),
                {"user_id": user_id}
            )

            # Insert optimized memories
            inserted = 0
            for mem in normalized_memories:
                new_memory_id = str(uuid.uuid4())

                memory_text = mem["memory"]
                if not isinstance(memory_text, str):
                    memory_text = str(memory_text)
                memory_text = memory_text.strip()

                # Handle double-encoding
                if memory_text.startswith('"') and memory_text.endswith('"') and len(memory_text) > 2:
                    try:
                        decoded = json.loads(memory_text)
                        if isinstance(decoded, str):
                            memory_text = decoded
                    except:
                        pass

                topics = mem.get("topics", [])
                if not isinstance(topics, list):
                    topics = []
                topics = [t.lower().strip() for t in topics if isinstance(t, str)][:3]

                conn.execute(
                    text("""
                        INSERT INTO ai.agno_memories
                        (memory_id, user_id, memory, topics, created_at, updated_at)
                        VALUES (:memory_id, :user_id, CAST(:memory AS jsonb), CAST(:topics AS jsonb), :created_at, :updated_at)
                    """),
                    {
                        "memory_id": new_memory_id,
                        "user_id": user_id,
                        "memory": json.dumps(memory_text),
                        "topics": json.dumps(topics),
                        "created_at": current_time_s,
                        "updated_at": current_time_s
                    }
                )
                inserted += 1

        logger.info(f"[Workflow v2.0] Archived {archived_count}, inserted {inserted} memories")

        output_data = {
            "status": "completed",
            "archived_count": archived_count,
            "inserted_count": inserted,
            "deleted_count": deleted_count,
            "run_id": run_id
        }

        # Track step progress
        if run_id:
            _track_step(run_id, "Save", 5, {"archived": archived_count, "inserted": inserted})

        return StepOutput(content=json.dumps(output_data))

    except Exception as e:
        logger.error(f"[Workflow v2.0] Save/archive error: {e}")
        return StepOutput(content=f"ERROR: Failed to save/archive: {str(e)}", success=False, stop=True)


# =============================================================================
# STEP 6: GENERATE REPORT
# =============================================================================

def generate_report(step_input: StepInput) -> StepOutput:
    """Step 6: Generate summary report."""
    logger.info("[Workflow v2.0] Step 6: Generating report...")

    try:
        # Fetch stats
        fetch_output = step_input.previous_step_outputs.get("Fetch Memories")
        original_count = 0
        original_topics = 0
        if fetch_output:
            try:
                data = json.loads(fetch_output.content)
                original_count = data.get("stats", {}).get("count", 0)
                original_topics = data.get("stats", {}).get("unique_topics", 0)
            except:
                pass

        # Classify stats
        classify_output = step_input.previous_step_outputs.get("Classify")
        deleted_count = 0
        merge_decisions = 0
        keep_decisions = 0
        if classify_output:
            try:
                data = json.loads(classify_output.content)
                stats = data.get("stats", {})
                deleted_count = stats.get("delete", 0)
                merge_decisions = stats.get("merge", 0)
                keep_decisions = stats.get("keep", 0)
            except:
                pass

        # Merge stats
        merge_output = step_input.previous_step_outputs.get("Resolve Merges")
        merge_groups = 0
        merged_count = 0
        if merge_output:
            try:
                data = json.loads(merge_output.content)
                stats = data.get("stats", {})
                merge_groups = stats.get("merge_groups", 0)
                merged_count = stats.get("merged_count", 0)
            except:
                pass

        # Normalize stats
        normalize_output = step_input.previous_step_outputs.get("Normalize Topics")
        final_topics = 0
        if normalize_output:
            try:
                data = json.loads(normalize_output.content)
                final_topics = data.get("stats", {}).get("normalized_topics", 0)
            except:
                pass

        # Save stats
        save_output = step_input.previous_step_outputs.get("Save")
        inserted_count = 0
        archived_count = 0
        run_id = "N/A"
        if save_output:
            try:
                data = json.loads(save_output.content)
                inserted_count = data.get("inserted_count", 0)
                archived_count = data.get("archived_count", 0)
                run_id = data.get("run_id", "N/A")
            except:
                pass

        # Calculate reduction
        reduction = 0
        if original_count > 0:
            reduction = 100 - (inserted_count / original_count * 100)

        report = f"""## Memory Optimization Complete (v2.0)

**Summary:**
- Memories: {original_count} → {inserted_count} ({reduction:.1f}% reduction)
- Topics: {original_topics} → {final_topics} unique topics

**Decisions:**
- Deleted: {deleted_count} (one-time actions, queries, test data)
- Merged: {merge_groups} groups → {merged_count} memories
- Kept: {keep_decisions} (valuable long-term facts)

**Actions:**
- {archived_count} original memories archived (recoverable)
- {inserted_count} optimized memories saved

**Run ID:** {run_id}
"""

        logger.info(f"[Workflow v2.0] Report: {original_count} → {inserted_count} memories ({reduction:.1f}% reduction)")

        # Track step progress (final step)
        if run_id != "N/A":
            _track_step(run_id, "Report", 6, {"before": original_count, "after": inserted_count, "reduction": round(reduction, 1)})

        return StepOutput(content=report)

    except Exception as e:
        logger.error(f"[Workflow v2.0] Report error: {e}")
        return StepOutput(content=f"Report generation failed: {str(e)}", success=True)
