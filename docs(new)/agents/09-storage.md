# AGNO Storage Documentation

> **Source:** https://docs.agno.com/basics/agents/usage/agent-with-storage
> **Last Updated:** 2025-11-29

---

## What Is Storage?

Storage provides persistent data storage for agents and teams, enabling them to:
- Maintain sessions across conversations
- Store chat history
- Preserve memories between runs
- Enable multi-user, multi-session applications

---

## Database Configuration

### PostgresDb (Recommended for Production)

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
db = PostgresDb(db_url=db_url)

agent = Agent(
    db=db,
    # ... other config
)
```

### AsyncPostgresDb (For Async Applications)

```python
from agno.db.postgres import AsyncPostgresDb

db_url = "postgresql+psycopg_async://ai:ai@localhost:5532/ai"
db = AsyncPostgresDb(db_url=db_url)
```

### Other Supported Databases

| Class | Use Case |
|-------|----------|
| `SqliteDb` | Development/testing |
| `PostgresDb` | Production |
| `AsyncPostgresDb` | Async production |
| `MongoDb` | Document storage |
| `RedisDb` | Fast caching |

---

## V2 Changes (IMPORTANT)

AGNO V2 unified storage:

| Old (V1) | New (V2) |
|----------|----------|
| `PostgresStorage` | `PostgresDb` |
| `storage` parameter | `db` parameter |
| `memory` parameter | Removed (use `enable_user_memories`) |
| `AgentMemory` class | Removed |

**Key change:** Single `db` parameter handles sessions, memories, and metrics.

---

## Session Management

### Basic Session

```python
agent = Agent(
    db=db,
    user_id="user@example.com",
    session_id="unique-session-id",
)
```

### Session Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `db` | PostgresDb | Database instance (required for persistence) |
| `user_id` | str | User identifier for organizing sessions |
| `session_id` | str | Unique session identifier |

---

## History Management

### Add History to Context

```python
agent = Agent(
    db=db,
    add_history_to_context=True,    # Enable history in context
    num_history_runs=3,              # Last 3 conversation turns (default)
)
```

### History Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `add_history_to_context` | False | Add previous messages to context |
| `num_history_runs` | 3 | Number of previous runs to include |
| `num_history_messages` | None | More granular message count |
| `max_tool_calls_from_history` | None | Limit tool calls in history |
| `read_chat_history` | False | Provide `get_chat_history()` tool |
| `read_tool_call_history` | False | Provide `get_tool_call_history()` tool |

### Cross-Session History

```python
agent = Agent(
    db=db,
    search_session_history=True,     # Search across sessions
    num_history_sessions=3,          # Last 3 sessions
)
```

**Warning:** Keep `num_history_sessions` low (2-3) to avoid context overflow.

---

## Session Summaries

Automatically condense long conversations:

```python
agent = Agent(
    db=db,
    enable_session_summaries=True,        # Generate summaries
    add_session_summary_to_context=True,  # Include in context (default if summaries enabled)
)
```

### Combining History + Summaries

```python
agent = Agent(
    db=db,
    add_session_summary_to_context=True,  # Long-term memory
    add_history_to_context=True,
    num_history_runs=2,                   # Recent detail
)
```

---

## Memory Management

### Enable User Memories

```python
agent = Agent(
    db=db,
    enable_user_memories=True,  # Create/update memories after each run
)
```

### Agentic Memory (Active Management)

```python
agent = Agent(
    db=db,
    enable_agentic_memory=True,  # Agent can create/update/delete memories
)
```

### Custom Memory Manager

```python
from agno.memory import MemoryManager

class MyMemoryManager(MemoryManager):
    # Custom logic
    pass

agent = Agent(
    db=db,
    memory_manager=MyMemoryManager(),
)
```

### Memory Methods

```python
# Get user memories
memories = agent.get_user_memories(user_id="user@example.com")

# Clear memories
agent.db.clear_memories()
```

---

## Team Storage

Teams use the same storage pattern:

```python
from agno.team import Team

team = Team(
    db=db,
    members=[agent1, agent2],
    add_history_to_context=True,
    num_history_runs=3,
    enable_user_memories=True,
    enable_session_summaries=True,
)
```

### Team-Specific History Options

| Parameter | Description |
|-----------|-------------|
| `add_team_history_to_members` | Share team history with members |
| `num_team_history_runs` | How many team runs to share |
| `share_member_interactions` | Members see each other's outputs |

---

## Retrieving Sessions

```python
from agno.db.base import SessionType

# Get session
session = agent.get_session(session_id="123")

# Get session with type
session = db.get_session(
    session_id="123",
    session_type=SessionType.AGENT  # or SessionType.TEAM
)

# Get all sessions for user
sessions = db.get_sessions(user_id="user@example.com")

# Get session summary
summary = session.summary
```

---

## Best Practices

### 1. Pattern Selection

| Scenario | Configuration |
|----------|---------------|
| Short chats | Defaults (history off) or `num_history_runs=3` |
| Long conversations | `num_history_runs=2` + session summaries |
| Tool-heavy agents | Use `max_tool_calls_from_history` |
| Cross-session recall | `search_session_history=True`, `num_history_sessions=2` |

### 2. Performance Tips

- **Start small:** Begin with `num_history_runs=3`, increase if needed
- **More history = larger context = slower/costlier requests**
- **Keep `num_history_sessions` low (2-3)** to avoid context overflow
- **Use summaries** for long conversations instead of full history

### 3. Required for Persistence

**All storage features require `db` parameter:**
- Sessions
- Memories
- History
- Summaries
- Metrics

---

## Complete Example

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
db = PostgresDb(db_url=db_url)

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    db=db,
    user_id="user@example.com",
    session_id="unique-session-123",

    # History
    add_history_to_context=True,
    num_history_runs=5,

    # Cross-session
    search_session_history=True,
    num_history_sessions=3,

    # Memories
    enable_user_memories=True,

    # Summaries
    enable_session_summaries=True,

    debug_mode=True,
)

agent.print_response("My name is John", stream=True)
agent.print_response("What's my name?", stream=True)

# Access memories
memories = agent.get_user_memories(user_id="user@example.com")
```

---

## Summary

| Feature | Parameter | Requires `db` |
|---------|-----------|---------------|
| Session persistence | `db=PostgresDb(...)` | Yes |
| History in context | `add_history_to_context=True` | Yes |
| Cross-session search | `search_session_history=True` | Yes |
| User memories | `enable_user_memories=True` | Yes |
| Session summaries | `enable_session_summaries=True` | Yes |
| Agentic memory | `enable_agentic_memory=True` | Yes |

**Key Insight:** The `db` parameter is the foundation for ALL persistence features in AGNO.
