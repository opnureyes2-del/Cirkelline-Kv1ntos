# AGNO Memory Documentation

> **Source:** https://docs.agno.com/basics/agents/usage/agent-with-memory
> **Last Updated:** 2025-11-29

---

## What Is Memory?

Memory enables agents to recall information about users across sessions. It provides personalized experiences by remembering user preferences, context, and history.

---

## Memory Modes

### 1. Automatic Memory (Recommended)

```python
agent = Agent(
    db=db,
    enable_user_memories=True,  # Automatic memory management
)
```

**How it works:**
- Memories are automatically created/updated after each run
- AGNO handles extraction, storage, and retrieval
- Reliable and predictable

**Best for:** Customer support, personal assistants, conversational apps

### 2. Agentic Memory

```python
agent = Agent(
    db=db,
    enable_agentic_memory=True,  # Agent controls memory via tools
)
```

**How it works:**
- Agent gets tools to create, update, and delete memories
- Agent decides when to remember based on context
- More flexible but requires intelligent decisions

**Best for:** Complex workflows, multi-turn interactions

### IMPORTANT: Mutual Exclusivity

```python
# DON'T do this - they're mutually exclusive!
agent = Agent(
    enable_user_memories=True,      # This will be IGNORED
    enable_agentic_memory=True,     # This takes precedence
)
```

**Rule:** If both are set, `enable_agentic_memory` wins and `enable_user_memories` is ignored.

---

## Memory Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enable_user_memories` | False | Auto-create memories after each run |
| `enable_agentic_memory` | False | Agent manages memories via tools |
| `add_memories_to_context` | True | Include user memories in context |
| `memory_manager` | None | Custom MemoryManager instance |

---

## Context Control

### Default Behavior (memories in context)

```python
agent = Agent(
    db=db,
    enable_user_memories=True,
    # add_memories_to_context=True  # Default
)
```

Memories are automatically added to agent's context on each request.

### Background Collection (lean context)

```python
agent = Agent(
    db=db,
    enable_user_memories=True,
    add_memories_to_context=False,  # Collect but don't include
)
```

**Use case:** Analytics on memories, or when agent should explicitly search for memories using tools.

---

## Custom Memory Manager

### Basic Customization

```python
from agno.memory import MemoryManager

memory_manager = MemoryManager(
    db=db,
    model=OpenAIChat(id="gpt-5-mini"),  # Model for memory creation
    additional_instructions="Don't store the user's real name",
)

agent = Agent(
    db=db,
    memory_manager=memory_manager,
    enable_user_memories=True,
)
```

### Memory Capture Instructions

```python
memory_manager = MemoryManager(
    model=OpenAIChat(id="gpt-5-mini"),
    memory_capture_instructions="""\
        Memories should only include details about the user's academic interests.
        Only include which subjects they are interested in.
        Ignore names, hobbies, and personal interests.
    """,
    db=db,
)
```

### MemoryManager Parameters

| Parameter | Description |
|-----------|-------------|
| `model` | LLM for memory creation (defaults to agent's model) |
| `db` | Database for memory storage |
| `additional_instructions` | Extra rules added to default prompt |
| `memory_capture_instructions` | Full override of capture instructions |

---

## Memory Retrieval

### From Agent

```python
# Get all memories for a user
memories = agent.get_user_memories(user_id="john@example.com")
```

### From MemoryManager

```python
memory_manager = MemoryManager(db=db, model=model)
memories = memory_manager.get_user_memories(user_id="john@example.com")
```

### Creating Memories Directly

```python
from agno.models.message import Message

# From text
memory_manager.create_user_memories(
    input="I enjoy hiking and reading science fiction.",
    user_id="john@example.com",
)

# From message history
memory_manager.create_user_memories(
    messages=[
        Message(role="user", content="My name is Jane"),
        Message(role="user", content="I like chess"),
    ],
    user_id="jane@example.com",
)
```

---

## Team Memory

Teams use the same memory parameters:

```python
from agno.team import Team

team = Team(
    db=db,
    members=[agent1, agent2],
    enable_user_memories=True,      # OR
    # enable_agentic_memory=True,   # (not both!)
)
```

---

## Best Practices

### 1. Choose the Right Mode

| Scenario | Mode |
|----------|------|
| Simple chat apps | `enable_user_memories=True` |
| Complex multi-turn | `enable_agentic_memory=True` |
| Analytics/search | `add_memories_to_context=False` |

### 2. Custom Instructions

```python
# Privacy-focused
additional_instructions="Never store PII like phone numbers, addresses, or SSN"

# Domain-focused
memory_capture_instructions="Only capture professional skills and work preferences"
```

### 3. Memory Hygiene

```python
# Clear all memories (use with caution!)
db.clear_memories()

# With agentic memory, user can request deletion
agent.print_response("Remove all existing memories of me.", user_id=user_id)
```

### 4. Database Required

**All memory features require `db` parameter:**
```python
agent = Agent(
    db=PostgresDb(db_url="..."),  # Required!
    enable_user_memories=True,
)
```

---

## Complete Example

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.memory import MemoryManager
from agno.models.openai import OpenAIChat

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

# Custom memory manager with privacy rules
memory_manager = MemoryManager(
    db=db,
    model=OpenAIChat(id="gpt-5-mini"),
    additional_instructions="""\
        Focus on capturing:
        - User preferences and interests
        - Communication style preferences
        - Important context about their situation

        Do NOT capture:
        - Exact addresses or phone numbers
        - Financial information
        - Medical details
    """,
)

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    db=db,
    memory_manager=memory_manager,
    enable_user_memories=True,
    user_id="user@example.com",
)

# Conversation with automatic memory
agent.print_response("I prefer email communication and work in tech.")
agent.print_response("What's the best way to reach me?")

# Retrieve memories
memories = agent.get_user_memories(user_id="user@example.com")
```

---

## Summary

| Feature | Parameter | Notes |
|---------|-----------|-------|
| Auto memory | `enable_user_memories=True` | Recommended for most cases |
| Agent-controlled | `enable_agentic_memory=True` | More flexible, agent decides |
| Context control | `add_memories_to_context=False` | For analytics/lean context |
| Custom rules | `memory_manager=MemoryManager(...)` | Privacy, domain focus |
| Retrieval | `agent.get_user_memories(user_id)` | Get stored memories |

**Key Insight:** Memory modes are mutually exclusive - use one or the other, not both.
