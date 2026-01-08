# Cirkelline Memory System

**Version:** v1.3.3 | **Last Updated:** 2025-12-14

---

## Overview

Cirkelline uses AGNO's memory system to store and retrieve user-specific information across conversations. The memory system has two main functions:

1. **Memory CREATION**: Automatically extract and save memorable information from conversations
2. **Memory RETRIEVAL**: Intelligently search and retrieve relevant memories using topic-based filtering

**Key Design Principle:** Memories are filtered at the SQL level - we do NOT load all memories into context. Only memories matching the requested topics are retrieved.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY SYSTEM FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER MESSAGE                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ CIRKELLINE ORCHESTRATOR                                 │   │
│  │ • Receives message                                       │   │
│  │ • May call search_memories() tool if topic relevant      │   │
│  │ • Generates response                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│       │                                                         │
│       ▼ (after run completes)                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ MEMORY MANAGER (automatic)                               │   │
│  │ • Extracts memorable info from conversation              │   │
│  │ • Creates new memories with topic tags                   │   │
│  │ • Stores in PostgreSQL (ai.agno_memories)               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

**Table:** `ai.agno_memories`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `memory_id` | VARCHAR | AGNO-generated memory ID |
| `user_id` | VARCHAR | User who owns this memory |
| `memory` | TEXT | The memory content |
| `topics` | JSONB | Array of topic tags (e.g., `["family", "relationships"]`) |
| `created_at` | BIGINT | Unix timestamp in **SECONDS** (10 digits like `1733414400`) |
| `updated_at` | BIGINT | Unix timestamp in **SECONDS** (10 digits like `1733414400`) |

**IMPORTANT - Timestamp Format (v1.3.3):**
- AGNO expects timestamps in Unix **SECONDS** (10 digits)
- Do NOT use MILLISECONDS (13 digits) - causes "year 57898 is out of range" error
- Threshold check: if `timestamp > 4102444800` (year 2100), it's MILLISECONDS

**Indexes:**
- `idx_agno_memories_user_id` - Fast user filtering
- `idx_agno_memories_updated_at` - Recent memories ordering

---

## Configuration

### Team Configuration (`cirkelline_team.py`)

```python
from agno.memory import MemoryManager
from agno.models.google import Gemini

# v1.2.34.6: Explicit MemoryManager with aggressive capture instructions
memory_manager = MemoryManager(
    model=Gemini(id="gemini-2.5-flash"),
    db=db,
    additional_instructions="""
IMPORTANT: Be AGGRESSIVE about capturing memories. Extract and store ANY of the following:

1. PERSONAL FACTS: Names, birthdays, anniversaries, locations, age, occupation
2. RELATIONSHIPS: Family members, friends, pets (including names), colleagues
3. PREFERENCES: Favorite things (movies, food, colors, music), likes/dislikes
4. EVENTS & MILESTONES: Recent events, upcoming plans, achievements, life changes
5. WORK/PROJECTS: Current projects, job details, professional interests
6. INTERESTS & HOBBIES: Activities, sports, creative pursuits

RULES:
- If the user mentions a pet, family member, or friend BY NAME → create a memory
- If the user shares a personal fact (birthday, location, etc.) → create a memory
- If the user expresses a strong preference or opinion → create a memory
- If the user mentions an event or milestone → create a memory
- Do NOT require explicit "remember this" - extract automatically from natural conversation
- Assign relevant topic tags to each memory for easy retrieval
"""
)

cirkelline = Team(
    ...
    db=db,
    memory_manager=memory_manager,  # Required for memory creation

    # Memory configuration
    add_memories_to_context=False,    # DON'T auto-load all memories
    enable_user_memories=True,        # CREATE memories automatically after each run
    # NOTE: Do NOT use enable_agentic_memory=True with enable_user_memories=True
    # They are MUTUALLY EXCLUSIVE - agentic_memory disables automatic memory creation
    ...
)
```

### Key Settings Explained

| Setting | Value | Purpose |
|---------|-------|---------|
| `memory_manager` | Explicit instance | Required for Teams to create memories |
| `add_memories_to_context` | `False` | Don't load all memories - use search tool instead |
| `enable_user_memories` | `True` | Auto-extract memories after each conversation |

**IMPORTANT:** `enable_user_memories` and `enable_agentic_memory` are **MUTUALLY EXCLUSIVE**.
If both are set, `enable_agentic_memory` wins and automatic memory creation is DISABLED.
Use ONE or the OTHER, not both.

---

## Memory Search Tool

### File: `cirkelline/tools/memory_search_tool.py`

The `IntelligentMemoryTool` provides topic-based memory retrieval:

```python
class IntelligentMemoryTool(Toolkit):
    """Tool for intelligent memory search using database-level topic filtering."""

    def __init__(self, database):
        super().__init__(name="memory_tools")
        self.database = database
        self.register(self.search_memories)
        self.register(self.get_recent_memories)

    def search_memories(self, topics: List[str], user_id: str, limit: int = 10) -> str:
        """
        Search for memories by topic keywords using SQL-level filtering.
        Only memories matching the topics are returned - NOT all memories.

        Args:
            topics: Topic keywords to filter by (e.g., ["travel", "Japan"])
            user_id: The user's ID
            limit: Maximum memories to return (default 10)
        """
        memories = self.database.get_user_memories(
            user_id=user_id,
            topics=topics,  # SQL-level filtering
            limit=limit
        )
        ...

    def get_recent_memories(self, user_id: str, limit: int = 5) -> str:
        """Get the most recent memories (no topic filtering)."""
        ...
```

### How SQL Filtering Works

When `topics=["family", "travel"]` is passed:

```sql
SELECT * FROM ai.agno_memories
WHERE user_id = 'xxx'
  AND topics LIKE '%"family"%'
  AND topics LIKE '%"travel"%'
LIMIT 10
```

This returns ONLY memories tagged with both "family" AND "travel" - not all 100+ memories.

---

## Instructions for Agent

### File: `cirkelline/orchestrator/instructions.py` (MEMORY ACCESS section)

```python
# ✅ v1.2.34.5: Memory search with topic-based filtering (SQL-level, not loading all)
base_instructions.extend([
    "",
    "═══════════════════════════════════════",
    "MEMORY ACCESS (Topic-Based Filtering)",
    "═══════════════════════════════════════",
    "",
    "You have memory tools that filter at the database level - NEVER loading all memories:",
    "",
    "• search_memories(topics, user_id, limit): Search by topic keywords",
    "  - topics: List of keywords extracted from the conversation",
    "  - Database returns ONLY memories matching those topics",
    "",
    "• get_recent_memories(user_id, limit): Get most recent memories (no filtering)",
    "",
    "HOW TO USE:",
    "1. Extract relevant topic keywords from the user's message/question",
    "2. Call search_memories with those topics",
    "",
    "EXAMPLES:",
    "• User asks: 'Tell me about my trip to Japan'",
    "  → topics=['travel', 'Japan']",
    "",
    "• User asks: 'What do I like about AI?'",
    "  → topics=['AI', 'interests', 'preferences']",
    "",
    "• User asks: 'What's my favorite programming language?'",
    "  → topics=['programming', 'preferences', 'technical']",
    "",
    "IMPORTANT:",
    "• Memories are NOT automatically loaded - you must search when needed",
    "• Always extract 2-4 relevant topic keywords from the conversation",
    "• Topics are dynamically generated per memory (e.g., 'AI agents', 'travel', 'work')",
    "• Only matching memories are returned - efficient and context-aware",
    ""
])
```

---

## Memory Creation Flow

### What Gets Saved

The MemoryManager automatically extracts and saves:

1. **Personal Facts**
   - "User's favorite movie is The Matrix" → topics: `["favorite movie", "preferences"]`
   - "User lives in Copenhagen" → topics: `["location", "personal"]`

2. **Relationships**
   - "User's sister is named Emma" → topics: `["family", "relationships"]`
   - "User has a cat named Whiskers" → topics: `["pets", "animals"]`

3. **Events**
   - "User's sister Emma got engaged to Marcus" → topics: `["family", "relationships", "events"]`
   - "User started a new job at Google" → topics: `["work", "career", "events"]`

4. **Preferences**
   - "User prefers Python over JavaScript" → topics: `["programming", "preferences", "technical"]`
   - "User enjoys hiking on weekends" → topics: `["hobbies", "activities", "outdoors"]`

### Topic Generation

Topics are **dynamically generated** by the MemoryManager based on the memory content. They are NOT predefined categories. Common topics include:

- `family`, `relationships`, `friends`, `pets`
- `work`, `career`, `projects`, `professional`
- `preferences`, `favorites`, `likes`, `dislikes`
- `travel`, `locations`, `places`
- `hobbies`, `interests`, `activities`
- `events`, `milestones`, `achievements`
- `technical`, `programming`, `AI`

---

## Memory Retrieval Flow

### Example: "What do you remember about my family?"

```
1. User sends: "What do you remember about my family?"

2. Cirkelline extracts topic keywords: ["family"]

3. Cirkelline calls tool:
   search_memories(topics=["family"], user_id="xxx")

4. Database executes SQL:
   SELECT * FROM ai.agno_memories
   WHERE user_id = 'xxx'
   AND topics LIKE '%"family"%'
   LIMIT 10

5. Returns ONLY family memories:
   - "User's sister is named Emma" (topics: family, relationships)
   - "User's sister Emma got engaged to Marcus" (topics: family, relationships, events)

6. Cirkelline responds:
   "I remember your sister Emma got engaged to Marcus recently!"
```

### Token Efficiency

| Approach | Tokens Used | Issue |
|----------|-------------|-------|
| Load ALL memories | ~5,000+ | Bloats context, expensive |
| Topic-based filtering | ~200-500 | Only relevant memories loaded |

---

## Code Files

| File | Purpose |
|------|---------|
| `cirkelline/orchestrator/cirkelline_team.py` | Team config with MemoryManager |
| `cirkelline/tools/memory_search_tool.py` | IntelligentMemoryTool implementation |
| `cirkelline/orchestrator/instructions.py` | Agent instructions for memory usage |
| `cirkelline/database.py` | PostgresDb with memory table config |

---

## API Endpoints

### Get User Memories

```
GET /api/user/memories
Authorization: Bearer <token>
```

**Response:**
```json
{
  "memories": [
    {
      "memory_id": "uuid",
      "memory": "User's favorite movie is The Matrix",
      "topics": ["favorite movie", "preferences"],
      "created_at": "2025-12-02T12:00:00Z"
    }
  ],
  "total": 111
}
```

---

## Troubleshooting

### Memories Not Being Created

1. **Check MemoryManager exists:**
   ```python
   # cirkelline_team.py must have:
   memory_manager = MemoryManager(model=..., db=db)
   cirkelline = Team(..., memory_manager=memory_manager, ...)
   ```

2. **Check enable_user_memories:**
   ```python
   enable_user_memories=True  # Must be True
   ```

3. **Check database connection:**
   ```bash
   docker exec cirkelline-postgres psql -U cirkelline -d cirkelline \
     -c "SELECT COUNT(*) FROM ai.agno_memories;"
   ```

### Memories Not Being Retrieved

1. **Check topic extraction:**
   - Look for `search_memories` tool call in logs
   - Verify topics match what's stored in database

2. **Check SQL filtering:**
   ```sql
   SELECT memory, topics FROM ai.agno_memories
   WHERE user_id = 'xxx'
   AND topics LIKE '%"family"%';
   ```

3. **Verify tool is registered:**
   - Check `memory_search_tool` is in Team's tools list

### All Memories Loading (Token Bloat)

If all memories are loading into context:

1. **Check add_memories_to_context:**
   ```python
   add_memories_to_context=False  # Must be False
   ```

2. **Verify using custom tool:**
   - Agent should call `search_memories()` tool
   - NOT rely on automatic memory context loading

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.3.0 | 2025-12-04 | Added Memory Optimization Workflow (see `58-MEMORY-WORKFLOW.md`) |
| v1.2.34.6 | 2025-12-02 | Added aggressive memory capture instructions |
| v1.2.34.5 | 2025-12-02 | Added explicit MemoryManager to Team |
| v1.2.34.4 | 2025-12-02 | Implemented topic-based SQL filtering |
| v1.2.34 | 2025-12-01 | Initial memory system redesign |

---

## Quick Reference

### Memory Creation
- **Automatic**: `enable_user_memories=True`
- **Model**: Gemini 2.5 Flash
- **Trigger**: After each conversation run
- **Stored in**: `ai.agno_memories` table

### Memory Retrieval
- **Tool**: `search_memories(topics, user_id, limit)`
- **Filtering**: SQL-level (NOT loading all)
- **Agent extracts**: Topic keywords from user message
- **Returns**: Only matching memories

### Key Files
- Team config: `cirkelline/orchestrator/cirkelline_team.py`
- Search tool: `cirkelline/tools/memory_search_tool.py`
- Instructions: `cirkelline/orchestrator/instructions.py`

---

## Related Documentation

- **`58-MEMORY-WORKFLOW.md`** - Memory Optimization Workflow (auto-trigger, admin dashboard, merging, topic normalization)
