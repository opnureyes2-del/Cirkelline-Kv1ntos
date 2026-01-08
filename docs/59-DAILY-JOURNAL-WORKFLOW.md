# Daily Journal Workflow

**Version:** v1.3.2 | **Type:** AGNO Workflow | **Status:** Production

---

## Overview

The Daily Journal Workflow automatically generates diary-style journal entries summarizing a user's daily interactions with Cirkelline. It transforms raw session data into warm, reflective narrative prose written from Cirkelline's perspective.

**Key Features:**
- **Narrative prose** - Diary-style entries (not bullet points)
- **Time-based grouping** - Activities grouped by morning/afternoon/evening
- **Topic extraction** - Identifies 3-7 key topics per day
- **Sequential day numbering** - "Day 1", "Day 2" based on journal count, not calendar days
- **Automated scheduling** - Daily job at 1 AM + background worker
- **Gap filling** - Backfill journals for days with activity but no journal

---

## Why This Workflow Exists

### The User Story Problem

Users interacting with Cirkelline daily accumulate hundreds of sessions over time. Without a summary mechanism:
- Hard to remember what was accomplished each day
- No way to track patterns or progress over time
- Valuable context scattered across many sessions

### The Solution

Daily journals provide:
1. **Quick daily recap** - See what happened at a glance
2. **Searchable history** - Find past conversations by topic
3. **Personal connection** - Cirkelline "remembers" the user's journey
4. **Sidebar integration** - Easy access to recent journals

---

## Architecture

### 5-Step AGNO Workflow Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DAILY JOURNAL WORKFLOW (v1.1.0)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 1: FETCH SESSIONS                                             │
│  ├── Query ai.agno_sessions for target date                         │
│  ├── Extract user_id, session_name, runs (messages)                 │
│  └── Output: Sessions with messages, timestamps, message count      │
│                     ↓                                               │
│  Step 2: SUMMARIZE INTERACTIONS                                     │
│  ├── Journal Summarizer Agent (Gemini 2.5 Flash)                    │
│  ├── Group activities by time: morning/afternoon/evening            │
│  └── Output: Structured summary (activities, outcomes, topics)      │
│                     ↓                                               │
│  Step 3: WRITE NARRATIVE                                            │
│  ├── Journal Writer Agent (Gemini 2.5 Flash)                        │
│  ├── Transform bullets into diary-style prose                       │
│  └── Output: Narrative text + topics + achievements                 │
│                     ↓                                               │
│  Step 4: SAVE JOURNAL                                               │
│  ├── Calculate "Day X" number (sequential count)                    │
│  ├── UPSERT to ai.user_journals                                     │
│  └── Output: journal_id, target_date, stats                         │
│                     ↓                                               │
│  Step 5: GENERATE REPORT                                            │
│  └── Output: Summary report with stats and status                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Queue-Based Processing

```
┌─────────────────────────────────────────────────────────────────────┐
│                    JOURNAL AUTOMATION SYSTEM                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  SCHEDULER (APScheduler)                                            │
│  ├── Runs daily at 1:00 AM                                          │
│  ├── Finds users with activity yesterday but no journal             │
│  └── Adds jobs to queue with priority=10                            │
│                     ↓                                               │
│  QUEUE (ai.journal_queue)                                           │
│  ├── Stores pending/processing/completed/failed jobs                │
│  ├── Priority-based ordering (higher = first)                       │
│  └── Unique constraint: (user_id, target_date)                      │
│                     ↓                                               │
│  WORKER (Background async task)                                     │
│  ├── Polls queue every 30s when processing                          │
│  ├── Waits 60s when queue empty                                     │
│  ├── Processes one job at a time (rate limiting)                    │
│  └── Updates job status: pending → processing → completed/failed    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Two-agent pipeline** | Separates structure extraction from prose writing for better quality |
| **Narrative from Cirkelline's POV** | Creates personal connection ("I helped...", "I noticed...") |
| **Sequential day numbering** | "Day 40" means 40th journal, not 40 days since registration |
| **Queue-based processing** | Handles backfill gracefully, prevents API rate limits |
| **UPSERT on save** | Safe to re-run for same date (idempotent) |
| **Priority system** | Daily jobs (priority=10) run before backfill (priority=0) |

---

## Day Number Calculation

**Important:** The "Day X" number is the **sequential journal entry number**, NOT calendar days.

```python
# In journal_steps.py:_get_user_journal_count()
def _get_user_journal_count(user_id: str, before_date: str) -> int:
    """Count journals created BEFORE target date."""
    # Day 1 = first journal ever (count=0 + 1)
    # Day 2 = second journal ever (count=1 + 1)
    # etc.
```

**Example:**
- User registers December 1st
- First activity: December 1st → Journal created = "Day 1"
- Next activity: December 5th → Journal created = "Day 2" (NOT Day 5)
- Next activity: December 10th → Journal created = "Day 3" (NOT Day 10)

---

## Triggering

### 1. Automatic (Daily Scheduler)

**When:** 1:00 AM daily

**Logic:**
1. Find all users with sessions yesterday (`created_at` in yesterday's range)
2. Exclude users who already have a journal for yesterday
3. Add each user to queue with `priority=10`

**Code:** `cirkelline/workflows/journal_scheduler.py`

### 2. Manual (Admin Dashboard)

**Endpoint:** `POST /api/admin/workflows/daily-journal/run?target_user_id=<uuid>&target_date=<YYYY-MM-DD>`

**Frontend:** `/admin/workflows/journals` → Select user → Click "Generate"

### 3. Backfill (Gap Filling)

**Single User:** `POST /api/admin/workflows/journals/backfill/{user_id}`
- Finds all days with activity but no journal
- Adds to queue with `priority=0` (lower than daily)

**All Users:** `POST /api/admin/workflows/journals/backfill-all`
- Runs single-user backfill for all users with gaps

---

## Files

### Workflow Core

| File | Purpose | Lines |
|------|---------|-------|
| `cirkelline/workflows/daily_journal.py` | Main workflow, agents, schemas, run function | ~275 |
| `cirkelline/workflows/journal_steps.py` | Step executors (fetch, summarize, narrative, save, report) | ~760 |
| `cirkelline/workflows/journal_queue.py` | Queue management (add, get, mark status) | ~460 |
| `cirkelline/workflows/journal_worker.py` | Background worker (polling, processing) | ~160 |
| `cirkelline/workflows/journal_scheduler.py` | APScheduler config (daily job at 1 AM) | ~110 |

### Endpoints

| File | Purpose |
|------|---------|
| `cirkelline/endpoints/journals.py` | User-facing journal API (GET /api/journals) |
| `cirkelline/admin/workflows.py` | Admin journal endpoints (lines 1326-2660) |

### Tools

| File | Purpose |
|------|---------|
| `cirkelline/tools/journal_search_tool.py` | AGNO tool for searching journals in conversations |

### Integration

| File | Line | Purpose |
|------|------|---------|
| `my_os.py` | 464-498 | Worker/scheduler startup/shutdown hooks |
| `my_os.py` | 177 | Router registration |

---

## Agents

### Journal Summarizer

**Model:** Gemini 2.5 Flash

**Purpose:** Extract structured data from raw session messages

**Instructions Summary:**
- Group activities by time of day (morning: 00:00-12:00, afternoon: 12:00-18:00, evening: 18:00-24:00)
- Be concise - bullet points, not paragraphs
- Focus on WHAT WAS DONE, not conversation details
- Extract key outcomes and 3-7 topic keywords

**Output Schema:**
```python
class JournalSummary(BaseModel):
    morning: List[str]      # Morning activities
    afternoon: List[str]    # Afternoon activities
    evening: List[str]      # Evening activities
    outcomes: List[str]     # Key accomplishments
    topics: List[str]       # 3-7 topic keywords
```

### Journal Writer (Narrative)

**Model:** Gemini 2.5 Flash

**Purpose:** Transform structured summary into diary-style prose

**Instructions Summary:**
- Write from Cirkelline's perspective ("I helped...", "I noticed...")
- Refer to user in third person ("Ivo worked on...", "She focused on...")
- Tone: Thoughtful, reflective, warm but not overly enthusiastic
- NO greetings (never "Hello!", "Hey there!")
- 2-3 paragraphs, 100-200 words

**Output Schema:**
```python
class JournalNarrative(BaseModel):
    narrative: str           # Full diary-style text
    topics: List[str]        # 3-7 topic keywords
    key_achievements: List[str]  # 2-5 key outcomes
```

---

## Database

### Tables

| Table | Schema | Purpose |
|-------|--------|---------|
| `ai.user_journals` | ai | Stored journal entries |
| `ai.journal_queue` | ai | Processing queue |
| `ai.workflow_runs` | ai | Workflow run tracking |

### user_journals Schema

```sql
CREATE TABLE ai.user_journals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    journal_date DATE NOT NULL,
    summary TEXT NOT NULL,               -- The narrative prose
    topics JSONB,                        -- ["topic1", "topic2", ...]
    outcomes JSONB,                      -- ["outcome1", "outcome2", ...]
    sessions_processed JSONB,            -- ["session_id_1", "session_id_2", ...]
    message_count INTEGER,
    created_at BIGINT NOT NULL,          -- Unix timestamp
    UNIQUE(user_id, journal_date)
);

CREATE INDEX idx_user_journals_user_id ON ai.user_journals(user_id);
CREATE INDEX idx_user_journals_date ON ai.user_journals(journal_date);
CREATE INDEX idx_user_journals_topics ON ai.user_journals USING gin(topics);
```

### journal_queue Schema

```sql
CREATE TABLE ai.journal_queue (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    target_date DATE NOT NULL,
    status VARCHAR DEFAULT 'pending',     -- pending, processing, completed, failed
    priority INTEGER DEFAULT 0,           -- Higher = processed first
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    UNIQUE(user_id, target_date)
);

CREATE INDEX idx_journal_queue_status ON ai.journal_queue(status);
CREATE INDEX idx_journal_queue_priority ON ai.journal_queue(priority DESC, created_at);
```

### Sample Queries

```sql
-- Get user's journals
SELECT * FROM ai.user_journals
WHERE user_id = :user_id
ORDER BY journal_date DESC;

-- Find gap days (activity but no journal)
SELECT DISTINCT DATE(to_timestamp(created_at)) as activity_date
FROM ai.agno_sessions
WHERE user_id = :user_id
EXCEPT
SELECT journal_date FROM ai.user_journals WHERE user_id = :user_id;

-- Queue stats
SELECT status, COUNT(*) FROM ai.journal_queue GROUP BY status;

-- Get journal count for day number calculation
SELECT COUNT(*) FROM ai.user_journals
WHERE user_id = :user_id AND journal_date < :target_date;
```

---

## Admin Dashboard

### URL

`/admin/workflows/journals`

### Features

1. **Statistics Panel** - Total journals, today's runs, success rate
2. **User Stats Table** - Journals per user, expected vs actual, gaps
3. **Active Runs** - Live progress with polling
4. **Calendar View** - Per-user timeline showing activity/journal status per day
5. **Queue Management** - View/cancel pending jobs, retry failed, backfill

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/workflows/journals/stats` | GET | Overall statistics |
| `/api/admin/workflows/journals/users` | GET | All users with journal stats |
| `/api/admin/workflows/journals/entries` | GET | Paginated journal entries |
| `/api/admin/workflows/journals/runs` | GET | Workflow run history |
| `/api/admin/workflows/journals/runs/{run_id}` | GET | Single run details |
| `/api/admin/workflows/journals/active` | GET | Currently running workflows |
| `/api/admin/workflows/journals/queue` | GET | Queue stats and items |
| `/api/admin/workflows/journals/backfill/{user_id}` | POST | Backfill single user |
| `/api/admin/workflows/journals/backfill-all` | POST | Backfill all users |
| `/api/admin/workflows/journals/queue/retry-failed` | POST | Retry failed jobs |
| `/api/admin/workflows/journals/queue/cancel-pending` | POST | Cancel all pending |
| `/api/admin/workflows/journals/scheduler/trigger` | POST | Run daily job now |
| `/api/admin/workflows/journals/user/{id}/calendar` | GET | User's day-by-day timeline |
| `/api/admin/workflows/journals/user/{id}/day/{date}` | GET | Specific day details |

---

## User-Facing Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/journals` | GET | Get user's journals (paginated) |
| `/api/journals/{id}` | GET | Get single journal detail |

### Response Format

```json
{
  "success": true,
  "journals": [
    {
      "id": 42,
      "journal_date": "2025-12-10",
      "summary": "Day 40 - December 10, 2025\n\nIvo spent the afternoon...",
      "topics": ["deployment", "debugging", "planning"],
      "outcomes": ["Fixed production bug", "Deployed v1.3.1"],
      "message_count": 15,
      "created_at": 1733840000
    }
  ],
  "total": 40,
  "page": 1,
  "limit": 7,
  "has_more": true
}
```

---

## Sidebar Integration

Journals appear in the chat sidebar below conversations:

**Format:** `Day 40  Wednesday December 10`
- Day number: Bold, primary color
- Date: Secondary color, same line

**Click behavior:** Opens journal detail in profile page (`/profile/journals`)

**Files:**
- `cirkelline-ui/src/components/chat/Sidebar/Journals/Journals.tsx`
- `cirkelline-ui/src/components/chat/Sidebar/Journals/JournalItem.tsx`

---

## Error Handling

### Step Failures

Each step returns `StepOutput` with error prefix:
```python
if error_condition:
    return StepOutput(
        content=f"ERROR: {error_message}",
        success=False,
        stop=True  # Halts workflow
    )
```

### Queue Job Failures

Jobs marked as `failed` with error message stored:
```python
mark_failed(job_id, str(e))
```

**Retry:** Admin can use "Retry Failed" button or API endpoint.

### No Sessions Case

If no sessions found for target date:
- Step 2 returns empty summary with "No activity recorded"
- Step 3 writes minimal narrative
- Journal still saved (documents the "no activity" day)

---

## Sample Output

### Journal Entry

```
Day 40 - December 10, 2025

Ivo spent most of the afternoon focused on the daily journal workflow
implementation. I helped structure the database schema and worked through
the queue-based processing logic together. There was a tricky moment with
the day number calculation - originally counting calendar days, but we
switched to counting journal entries sequentially which makes more sense.

Later in the evening, he tested the backfill feature to generate journals
for missed days. I noticed he's meticulous about testing edge cases.

A productive day building features that help track these very interactions.
```

### Workflow Report

```
==================================================
DAILY JOURNAL WORKFLOW REPORT
==================================================

Date: 2025-12-10
Journal ID: 42

STATS:
- Sessions processed: 3
- Messages summarized: 47
- Topics identified: 5
- Key outcomes: 3

TOPICS:
  - deployment
  - debugging
  - journal-workflow
  - agno
  - database

OUTCOMES:
  - Implemented daily journal workflow
  - Fixed day number calculation
  - Added queue-based processing

==================================================
Journal entry saved successfully!
==================================================
```

---

## Configuration

### Worker Settings

```python
# In journal_worker.py
WORKER_INTERVAL_SECONDS = 30  # Time between processing jobs
WORKER_IDLE_INTERVAL = 60     # Time to wait when queue empty
WORKER_ENABLED = True         # Global enable/disable
```

### Scheduler Settings

```python
# In journal_scheduler.py
SCHEDULER_HOUR = 1           # Run at 1 AM
SCHEDULER_MINUTE = 0
DAILY_JOB_PRIORITY = 10      # Higher than backfill jobs (0)
```

---

## Testing

### Manual Test via curl

```bash
# 1. Get admin token
TOKEN=$(curl -s -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"opnureyes2@gmail.com","password":"xxx"}' | jq -r '.token')

# 2. Check user journal stats
curl -s http://localhost:7777/api/admin/workflows/journals/users \
  -H "Authorization: Bearer $TOKEN" | jq

# 3. Trigger journal for specific user and date
curl -s -X POST "http://localhost:7777/api/admin/workflows/daily-journal/run?target_user_id=<uuid>&target_date=2025-12-10" \
  -H "Authorization: Bearer $TOKEN" | jq

# 4. Check active runs
curl -s http://localhost:7777/api/admin/workflows/journals/active \
  -H "Authorization: Bearer $TOKEN" | jq

# 5. Get user's journals (as that user)
curl -s http://localhost:7777/api/journals \
  -H "Authorization: Bearer $USER_TOKEN" | jq

# 6. Check queue status
curl -s http://localhost:7777/api/admin/workflows/journals/queue \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Verify Results

```sql
-- Check journal was created
SELECT id, journal_date, summary, topics
FROM ai.user_journals
WHERE user_id = :user_id
ORDER BY journal_date DESC
LIMIT 1;

-- Check queue status
SELECT * FROM ai.journal_queue
WHERE user_id = :user_id
ORDER BY created_at DESC;

-- Check workflow run
SELECT * FROM ai.workflow_runs
WHERE workflow_name = 'Daily Journal'
AND user_id = :user_id
ORDER BY started_at DESC;
```

---

## Known Issues

### 1. Timestamp Handling

Sessions use Unix timestamps (seconds), created_at may be in different formats. The code handles both:
```python
created_ts = row[2]  # Unix timestamp from sessions
# Handle both seconds and milliseconds
if created_ts > 4102444800:
    created_ts = created_ts / 1000
```

### 2. Empty Sessions

Some sessions may have no messages (opened but unused). The workflow handles this gracefully by skipping them.

### 3. Long Messages

AI responses are truncated to 500 chars when building context for summarizer to prevent token overflow.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.3.2 | 2025-12-12 | Documentation, sidebar UI improvements, day number fix |
| v1.1.0 | 2025-12-11 | Narrative style (2-agent pipeline), queue system, scheduler |
| v1.0.0 | 2025-12-10 | Initial implementation (bullet-point summaries) |

---

## Related Documentation

- `docs/57-MEMORY.md` - Memory system overview
- `docs/58-MEMORY-WORKFLOW.md` - Memory Optimization Workflow (similar pattern)
- `docs(new)/workflows/` - AGNO workflow documentation
