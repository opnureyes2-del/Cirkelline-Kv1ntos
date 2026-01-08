# Memory Optimization Workflow

**Version:** v1.3.3 | **Type:** AGNO Workflow | **Status:** Production

---

## Overview

The Memory Optimization Workflow is Cirkelline's first automated workflow. It optimizes user memories by:
- **Deleting** one-time actions, research queries, technical documentation, and test data

> **v1.3.3 Note:** Timestamps are now stored in Unix **SECONDS** (10 digits like `1733414400`), not MILLISECONDS. This matches AGNO's expected format. See `docs/10-CHANGELOG.md` for details.
- **Merging** duplicate/related memories into comprehensive single entries
- **Normalizing** topics to a standard set for consistent categorization

**Results:**
- Ivo: 807 → 90 memories (88.9% reduction)
- Rasmus: 670 → 291 memories (56.6% reduction - more personal facts preserved)

---

## Why This Workflow Exists

### The Topic Problem (Dec 3, 2025)

After implementing topic filtering on the memories page, we discovered **155+ unique topics** for ~800 memories - far too many due to inconsistency.

**Issues Found:**

| Problem | Example |
|---------|---------|
| Case sensitivity | `preferences` (18) vs `PREFERENCES` (4) |
| Wording variations | `goals`, `goals & objectives`, `short-term goals` |
| Over-granular | `Apollo 11`, `Benfica`, `favorite movie` instead of `history`, `sports`, `preferences` |

**Solution:** Two-part fix:
1. **MemoryManager Instructions** - Updated to use STANDARD_TOPICS (prevents future chaos)
2. **This Workflow** - Cleans up existing mess (normalize, merge, delete junk)

### v1.6 → v2.0 Evolution (Dec 4, 2025)

**v1.6.0 Problem:** Batched by TOPIC → same memory in multiple batches → **8 duplicate pairs**

```
Memory "User likes music on Linux" has topics ["music", "hobbies"]
→ Processed in BOTH "music" batch AND "hobbies" batch
→ Creates 2 duplicate outputs
```

**v2.0 Fix:** Batch by MEMORY ID → each ID in exactly ONE batch → **duplicates impossible**

| Aspect | v1.6.0 (Topic Batching) | v2.0 (Memory ID Batching) |
|--------|-------------------------|---------------------------|
| Batching | By TOPIC (60 groups) | By MEMORY ID (6 batches) |
| Output | Full memory TEXT | Decision only (tiny) |
| Duplicates | 8 pairs found | **Impossible** |
| Each ID | May appear in multiple batches | Exactly ONE batch |

---

## Architecture

### Decision-Based Pipeline (v2.0)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MEMORY OPTIMIZATION WORKFLOW                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 1: FETCH MEMORIES                                             │
│  ├── Query ai.agno_memories for user                                │
│  └── Output: All memories with topics                               │
│                     ↓                                               │
│  Step 2: CLASSIFY (Decision-Based)                                  │
│  ├── Memory Classifier Agent (Gemini 2.5 Flash)                     │
│  ├── Batch by MEMORY ID (20 per batch)                              │
│  └── Output: DECISIONS only (delete/keep/merge)                     │
│                     ↓                                               │
│  Step 3: RESOLVE MERGES                                             │
│  ├── Memory Merger Agent (Gemini 2.5 Flash)                         │
│  ├── Group merges by target_id                                      │
│  └── Output: Merged memories + survivors                            │
│                     ↓                                               │
│  Step 4: NORMALIZE TOPICS                                           │
│  ├── Topic Normalizer Agent (Gemini 2.5 Flash)                      │
│  └── Output: Memories with standard topics                          │
│                     ↓                                               │
│  Step 5: VALIDATE AND SAVE                                          │
│  ├── Archive old memories (recoverable)                             │
│  ├── Insert optimized memories                                      │
│  └── Output: Counts and run_id                                      │
│                     ↓                                               │
│  Step 6: GENERATE REPORT                                            │
│  └── Output: Summary with stats                                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Batch by Memory ID** | Prevents duplicates - each ID in exactly one batch |
| **Decisions only output** | Small JSON = reliable parsing |
| **Full context for classifier** | Agent sees ALL memories but only decides on batch |
| **Archive before delete** | Original memories always recoverable |
| **Standard topics** | Consistent categorization across all users |

---

## Triggering

### Manual Trigger (Admin Dashboard)

**Endpoint:** `POST /api/admin/workflows/memory-optimization/run?target_user_id=<uuid>`

**Access:** Admin only (requires `admin_profiles` entry)

**Frontend:** `/admin/workflows` dashboard → User Stats Table → "Optimize" button

### Auto-Trigger (Growth-Based) - v1.3.1

**When:** After every chat message (non-blocking background task)

**Criteria (v2.0 - Growth-Based):**
1. Auto-trigger is enabled (`WORKFLOW_CONFIG["memory_optimization"]["enabled"] = True`)
2. **Growth-based threshold:**
   - **Existing users:** Trigger when `growth >= 100` (new memories since last optimization)
   - **First-time users:** Trigger when total memories >= 100
3. Cooldown has expired (default: 24 hours since last run)

**Why Growth-Based?**
The old threshold-based trigger would re-optimize users like Rasmus (291 memories) every time they exceeded 100 memories - even though those 291 memories were already optimized and valid. Growth-based triggering only runs when 100+ NEW memories are added.

**Example:**
```
Rasmus has 291 memories after last optimization
→ post_optimization_count = 291

If Rasmus adds 50 new memories:
→ current = 341, growth = 50
→ NO TRIGGER (growth < 100)

If Rasmus adds 100 new memories:
→ current = 391, growth = 100
→ TRIGGER! (growth >= 100)
```

**Configuration:**
```python
WORKFLOW_CONFIG = {
    "memory_optimization": {
        "enabled": True,
        "threshold": 100,        # Trigger when GROWTH >= threshold
        "cooldown_hours": 24,    # Don't re-trigger within this period
    }
}
```

**Endpoints:**
- `GET /api/admin/workflows/config` - Get current config
- `PUT /api/admin/workflows/config` - Update config

---

## Files

### Workflow Definition

| File | Purpose |
|------|---------|
| `cirkelline/workflows/memory_optimization.py` | Main workflow, agents, schemas |
| `cirkelline/workflows/memory_steps.py` | Step executors (fetch, classify, merge, normalize, save, report) |
| `cirkelline/workflows/triggers.py` | Auto-trigger logic and cooldown checking |

### Admin Endpoints

| File | Purpose |
|------|---------|
| `cirkelline/admin/workflows.py` | All admin endpoints, config, active run tracking |

### Integration Point

| File | Line | Purpose |
|------|------|---------|
| `cirkelline/endpoints/custom_cirkelline.py` | ~970, ~1080 | Background task hook after chat |

---

## Agents

### Memory Classifier

**Model:** Gemini 2.5 Flash

**Purpose:** Classify each memory as delete/keep/merge

**Instructions:**
```
DELETE (be AGGRESSIVE):
1. ONE-TIME ACTIONS - "User wants to send an email to X"
2. RESEARCH QUERIES - "User wants to know the latest news about X"
3. TEST DATA - "User's name is TestUser123"

MERGE (provide merge_target ID):
- Same fact, different wording
- Related preferences to combine

KEEP:
- IDENTITY: Name, role, location, pets, family
- PREFERENCES: Favorite things, communication style
- RELATIONSHIPS: People the user knows
- SKILLS/EXPERTISE: What the user is good at
- ONGOING PROJECTS: Active work (not one-time tasks)
```

**Output Schema:**
```python
class MemoryDecision(BaseModel):
    memory_id: str
    action: Literal["delete", "keep", "merge"]
    merge_target: Optional[str]
    reason: str
```

### Memory Merger

**Model:** Gemini 2.5 Flash

**Purpose:** Combine related memories into one comprehensive memory

**Output Schema:**
```python
class MergedMemory(BaseModel):
    memory: str           # The merged text
    topics: List[str]     # 1-3 normalized topics
    source_ids: List[str] # Original memory IDs
```

### Topic Normalizer

**Model:** Gemini 2.5 Flash

**Purpose:** Map arbitrary topics to standard set

**Standard Topics:**
```python
STANDARD_TOPICS = [
    "preferences", "goals", "relationships", "family", "identity",
    "emotional state", "communication style", "behavioral patterns",
    "work", "projects", "skills", "expertise",
    "interests", "hobbies", "sports", "music", "travel",
    "programming", "ai", "technology", "software", "hardware",
    "location", "events", "calendar", "history",
    "legal", "finance",
]
```

---

## Database

### Tables

| Table | Purpose |
|-------|---------|
| `ai.agno_memories` | Active memories |
| `ai.agno_memories_archive` | Archived memories (recovery) |
| `ai.workflow_runs` | Workflow run history and metrics |

### Archive Schema

```sql
CREATE TABLE ai.agno_memories_archive (
    id SERIAL PRIMARY KEY,
    original_memory_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    memory JSONB NOT NULL,
    topics JSONB,
    input VARCHAR,
    created_at TIMESTAMP,
    archived_at TIMESTAMP DEFAULT NOW(),
    optimization_run_id VARCHAR  -- Links all memories from same run
);
```

### Workflow Runs Schema

```sql
CREATE TABLE ai.workflow_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR UNIQUE NOT NULL,
    workflow_name VARCHAR NOT NULL,
    user_id VARCHAR,                    -- NULL for system-wide runs
    status VARCHAR NOT NULL,            -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    current_step VARCHAR,               -- Which step is running
    steps_completed JSONB DEFAULT '[]', -- [{name, started, completed, duration_ms}]
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    metrics JSONB                       -- {total_tokens, cost, duration_ms}
);

CREATE INDEX idx_workflow_runs_status ON ai.workflow_runs(status);
CREATE INDEX idx_workflow_runs_workflow ON ai.workflow_runs(workflow_name);
CREATE INDEX idx_workflow_runs_user ON ai.workflow_runs(user_id);
```

### Queries

```sql
-- Count memories for user
SELECT COUNT(*) FROM ai.agno_memories WHERE user_id = :user_id;

-- Check last optimization (for cooldown)
SELECT MAX(archived_at) FROM ai.agno_memories_archive
WHERE user_id = :user_id AND optimization_run_id IS NOT NULL;

-- Get run history
SELECT DISTINCT optimization_run_id, MIN(archived_at), MAX(archived_at)
FROM ai.agno_memories_archive
WHERE optimization_run_id IS NOT NULL
GROUP BY optimization_run_id;
```

---

## Admin Dashboard

### URL

`/admin/workflows`

### Sections

1. **Active Runs** - Live progress with polling (2s interval)
2. **Pending Triggers** - Users ready to trigger (growth >= threshold) + approaching threshold
3. **User Stats Table** - Enhanced with:
   - Email, Memory Count, **Growth** (+X new), **Runs**, Last Opt, Action
   - Expandable row with run history per user
   - Sortable by all columns
   - Users with `should_trigger=true` highlighted in amber
4. **Settings** - Growth trigger (+100 new), cooldown, enable/disable
5. **Recent Runs** - History with before/after comparisons

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/workflows` | GET | List workflows |
| `/api/admin/workflows/runs` | GET | List all runs |
| `/api/admin/workflows/runs/{run_id}` | GET | Run details |
| `/api/admin/workflows/{name}/run` | POST | Trigger workflow |
| `/api/admin/workflows/stats` | GET | Statistics |
| `/api/admin/workflows/users-stats` | GET | Enhanced user stats (see below) |
| `/api/admin/workflows/active` | GET | Currently running workflows |
| `/api/admin/workflows/config` | GET/PUT | Auto-trigger configuration |

### Enhanced `/api/admin/workflows/users-stats` Response (v1.3.1)

```json
{
  "success": true,
  "users": [
    {
      "user_id": "uuid",
      "email": "user@example.com",
      "memory_count": 391,
      "topic_count": 25,
      "last_optimization": "2024-12-05T10:00:00",
      "total_runs": 3,
      "post_optimization_count": 291,
      "growth": 100,
      "should_trigger": true,
      "run_history": [
        {
          "run_id": "uuid",
          "status": "completed",
          "started_at": "2024-12-05T10:00:00",
          "completed_at": "2024-12-05T10:02:00",
          "before_count": 670,
          "after_count": 291,
          "reduction_percent": 56.6
        }
      ]
    }
  ],
  "total": 2,
  "growth_threshold": 100
}
```

| Field | Description |
|-------|-------------|
| `total_runs` | Number of workflow runs for this user |
| `post_optimization_count` | Memory count immediately after last successful run |
| `growth` | New memories since last optimization (`memory_count - post_optimization_count`) |
| `should_trigger` | Boolean - true if growth >= threshold |
| `run_history` | Array of last 5 runs with before/after stats |

---

## Active Run Tracking

### In-Memory Storage

```python
ACTIVE_WORKFLOW_RUNS = {
    "<user_id>": {
        "run_id": "uuid",
        "user_id": "uuid",
        "step": 3,
        "step_name": "Resolve Merges",
        "total_steps": 6,
        "progress": 50,  # percentage
        "started_at": "2024-12-04T12:00:00",
        "stats": {}
    }
}
```

### Functions

```python
update_active_run(user_id, run_id, step, step_name, total_steps=6, stats=None)
clear_active_run(user_id)
get_active_run(user_id=None)
```

---

## Execution Flow

### 1. Check Trigger Criteria (Growth-Based v2.0)

```python
async def check_and_trigger_optimization(user_id: str):
    config = WORKFLOW_CONFIG.get("memory_optimization", {})

    if not config.get("enabled", True):
        return  # Auto-trigger disabled

    threshold = config.get("threshold", 100)
    memory_count = await get_user_memory_count(user_id)

    if memory_count == 0:
        return  # No memories

    # Get post_optimization_count from last successful run
    post_opt_count = await get_post_optimization_count(user_id)

    if post_opt_count is not None:
        # Existing user - check GROWTH
        growth = memory_count - post_opt_count
        if growth < threshold:
            return  # Not enough new memories
    else:
        # First-time user - check total count
        if memory_count < threshold:
            return  # Below first-time threshold

    if not await check_cooldown(user_id, config.get("cooldown_hours", 24)):
        return  # Within cooldown period

    # All checks passed - fire and forget
    asyncio.create_task(run_optimization_background(user_id))
```

### 2. Run Workflow

```python
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
```

### 3. Step Communication

Each step receives `StepInput` with:
- `previous_step_outputs`: Dict of step name → StepOutput
- `additional_data`: Shared data (user_id, agents, schemas)

Each step returns `StepOutput` with:
- `content`: JSON string with results
- `success`: Boolean (default True)
- `stop`: Boolean to halt workflow (default False)

---

## Error Handling

### Step Failures

```python
if response.content.startswith("ERROR:"):
    return {
        "status": "failed",
        "run_id": run_id,
        "error": response.content
    }
```

### Batch Failures

If a classify batch fails, fallback to "keep" for all memories in batch:
```python
except Exception as e:
    for mid in batch_ids:
        all_decisions.append({
            "memory_id": mid,
            "action": "keep",
            "merge_target": None,
            "reason": "Fallback due to error"
        })
```

### Validation

Before saving, validate that not all memories would be deleted:
```python
if len(normalized_memories) == 0 and original_count > 0:
    return StepOutput(
        content="ERROR: Validation failed - would delete all memories",
        success=False,
        stop=True
    )
```

---

## Sample Output

### Report

```markdown
## Memory Optimization Complete (v2.0)

**Summary:**
- Memories: 113 → 33 (70.8% reduction)
- Topics: 45 → 18 unique topics

**Decisions:**
- Deleted: 62 (one-time actions, queries, test data)
- Merged: 8 groups → 8 memories
- Kept: 25 (valuable long-term facts)

**Actions:**
- 113 original memories archived (recoverable)
- 33 optimized memories saved

**Run ID:** a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

## Recovery

### Restore Archived Memories

All original memories are preserved in `ai.agno_memories_archive` with:
- `original_memory_id`: Original UUID
- `optimization_run_id`: Links all memories from same run
- `archived_at`: Timestamp

```sql
-- Restore all memories from a specific run
INSERT INTO ai.agno_memories (memory_id, user_id, memory, topics, created_at, updated_at)
SELECT original_memory_id, user_id, memory, topics,
       EXTRACT(EPOCH FROM created_at) * 1000,
       EXTRACT(EPOCH FROM NOW()) * 1000
FROM ai.agno_memories_archive
WHERE optimization_run_id = :run_id;

-- Then delete current memories for that user and re-run above
```

---

## Testing

### Manual Test via curl

```bash
# 1. Get admin token
TOKEN=$(curl -s -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"xxx"}' | jq -r '.token')

# 2. Check user stats
curl -s http://localhost:7777/api/admin/workflows/users-stats \
  -H "Authorization: Bearer $TOKEN" | jq

# 3. Trigger optimization for a user
curl -s -X POST "http://localhost:7777/api/admin/workflows/memory-optimization/run?target_user_id=<uuid>" \
  -H "Authorization: Bearer $TOKEN" | jq

# 4. Check run details
curl -s "http://localhost:7777/api/admin/workflows/runs/<run_id>" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Verify Results

```sql
-- Before/after comparison
SELECT
    (SELECT COUNT(*) FROM ai.agno_memories_archive WHERE optimization_run_id = :run_id) as before,
    (SELECT COUNT(*) FROM ai.agno_memories WHERE user_id = :user_id) as after;

-- Check topic normalization
SELECT DISTINCT jsonb_array_elements_text(topics) as topic
FROM ai.agno_memories WHERE user_id = :user_id
ORDER BY topic;
```

---

## Configuration Reference

### WORKFLOW_CONFIG

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | `True` | Enable/disable auto-trigger |
| `threshold` | int | `100` | Growth threshold - NEW memories since last optimization to trigger (first-time users: total memories) |
| `cooldown_hours` | int | `24` | Hours between auto-triggers per user |

### Environment Variables

None required - uses existing database connection.

---

## Known Issues

### Timestamp Format

AGNO's memory manager saves timestamps in milliseconds, but some code expects seconds. Fixed in `cirkelline/endpoints/user.py`:

```python
# Handle both seconds (10 digits) and milliseconds (13 digits)
if ts > 4102444800:  # 2100-01-01 as Unix timestamp
    ts = ts / 1000
timestamp = datetime.fromtimestamp(ts).isoformat()
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.3.1 | 2025-12-05 | Growth-based triggering, enhanced dashboard with run history, post_optimization_count tracking, DOCUMENTATION delete rule |
| v1.3.0 | 2025-12-05 | Initial Memory Workflow release, production results (Ivo: 88.9%, Rasmus: 56.6%) |
| v2.0.0 | 2024-12-04 | Decision-based pipeline, auto-trigger, admin dashboard |
| v1.0.0 | 2024-12-02 | Initial implementation with topic-based batching |

---

## Related Documentation

- `docs/57-MEMORY.md` - Memory system overview
- `docs(new)/workflows/` - AGNO workflow documentation
