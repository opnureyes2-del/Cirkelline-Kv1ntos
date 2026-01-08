# AGNO Agents Documentation Index

**AGNO Version:** 2.3.4
**Total Files:** 15

---

## Quick Reference

| When you need to... | Read this |
|---------------------|-----------|
| Create your first agent | `01-building-agents.md` |
| Run agents and get responses | `02-running-agents.md` |
| Debug agent issues | `03-debugging-agents.md` |
| Use async/await patterns | `05-async-usage.md` |
| Stream responses | `06-streaming.md` |
| Add tools to agents | `08-tools.md` |
| Add memory to agents | `10-memory.md` |
| Add knowledge base | `11-knowledge.md` |

---

## Documentation Structure

### Fundamentals (01-04)

| File | Description |
|------|-------------|
| `01-building-agents.md` | Creating agents, configuration, models |
| `02-running-agents.md` | run(), print_response(), response handling |
| `03-debugging-agents.md` | Debug mode, logging, troubleshooting |
| `04-basic-usage.md` | Common patterns, basic examples |

### Execution Patterns (05-06)

| File | Description |
|------|-------------|
| `05-async-usage.md` | arun(), aprint_response(), async patterns |
| `06-streaming.md` | Stream responses, chunk handling |

### Configuration (07-08)

| File | Description |
|------|-------------|
| `07-instructions.md` | Agent instructions, callable instructions |
| `08-tools.md` | Adding tools, custom tools, tool configuration |

### Data & Memory (09-11)

| File | Description |
|------|-------------|
| `09-storage.md` | Database storage, session persistence |
| `10-memory.md` | Agent memory, remembering context |
| `11-knowledge.md` | Knowledge base, RAG, document retrieval |

### Advanced (12-15)

| File | Description |
|------|-------------|
| `12-run-response-events.md` | RunEvent types, event handling |
| `13-intermediate-steps.md` | Tool calls, reasoning steps |
| `14-run-metadata-metrics.md` | Token usage, timing, metrics |
| `15-cancel-run.md` | Cancelling agent runs |

---

## Key Concepts Quick Reference

### Creating an Agent

```python
from agno.agent import Agent
from agno.model.google import Gemini

agent = Agent(
    name="My Agent",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="You are a helpful assistant.",
    tools=[...],
    markdown=True,
)
```

### Running an Agent

```python
# Synchronous
response = agent.run("Hello")
agent.print_response("Hello", stream=True)

# Asynchronous
response = await agent.arun("Hello")
await agent.aprint_response("Hello", stream=True)
```

### Key Parameters

| Parameter | Purpose |
|-----------|---------|
| `name` | Agent identifier |
| `model` | LLM model to use |
| `instructions` | System prompt / behavior |
| `tools` | Available tools |
| `db` | Database for persistence |
| `memory` | Memory configuration |
| `knowledge` | Knowledge base |
| `markdown` | Format output as markdown |
| `output_schema` | Pydantic model for structured output |

---

## Learning Path

**Beginner:**
1. `01-building-agents.md` - Create first agent
2. `02-running-agents.md` - Run and get responses
3. `04-basic-usage.md` - Common patterns

**Intermediate:**
4. `07-instructions.md` - Write good instructions
5. `08-tools.md` - Add capabilities with tools
6. `06-streaming.md` - Stream responses
7. `05-async-usage.md` - Async patterns

**Advanced:**
8. `09-storage.md` - Persist sessions
9. `10-memory.md` - Add memory
10. `11-knowledge.md` - Add knowledge base
11. `12-run-response-events.md` - Handle events
12. `03-debugging-agents.md` - Debug issues

---

*Last Updated: December 2025 | AGNO 2.3.4*
