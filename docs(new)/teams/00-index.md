# AGNO Teams Documentation Index

**AGNO Version:** 2.3.4
**Total Files:** 6

---

## Quick Reference

| When you need to... | Read this |
|---------------------|-----------|
| Create a team of agents | `01-building-teams.md` |
| Run teams and get responses | `02-running-teams.md` |
| Understand delegation | `03-delegation.md` |
| See basic team patterns | `04-basic-flows.md` |
| Use async patterns | `05-async-flows.md` |
| Run team as CLI app | `06-run-as-cli.md` |

---

## Documentation Structure

### Fundamentals (01-03)

| File | Description |
|------|-------------|
| `01-building-teams.md` | Creating teams, adding members, configuration |
| `02-running-teams.md` | run(), print_response(), response handling |
| `03-delegation.md` | How leader delegates to members, routing |

### Patterns (04-06)

| File | Description |
|------|-------------|
| `04-basic-flows.md` | Common team patterns, examples |
| `05-async-flows.md` | arun(), async team execution |
| `06-run-as-cli.md` | cli_app() for interactive testing |

---

## Key Concepts Quick Reference

### Creating a Team

```python
from agno.agent import Agent
from agno.team import Team
from agno.model.google import Gemini

# Create specialist agents
researcher = Agent(
    name="Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Research topics thoroughly.",
)

writer = Agent(
    name="Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write clear content.",
)

# Create team
team = Team(
    name="Research Team",
    members=[researcher, writer],
    instructions="Coordinate research and writing.",
)
```

### Running a Team

```python
# Synchronous
response = team.run("Research AI trends")
team.print_response("Research AI trends", stream=True)

# Asynchronous
response = await team.arun("Research AI trends")
await team.aprint_response("Research AI trends", stream=True)

# CLI app
team.cli_app(stream=True)
```

### Key Parameters

| Parameter | Purpose |
|-----------|---------|
| `name` | Team identifier |
| `members` | List of Agent members |
| `instructions` | Team-level coordination instructions |
| `db` | Database for persistence |
| `mode` | Execution mode (coordinate, collaborate) |

---

## Teams vs Workflows

| Aspect | Teams | Workflows |
|--------|-------|-----------|
| **Execution** | Dynamic delegation | Deterministic steps |
| **Control** | Leader decides routing | Pre-defined flow |
| **Use Case** | Flexible collaboration | Predictable pipelines |
| **Complexity** | Simpler setup | More control |

**When to use Teams:**
- Dynamic task routing needed
- Leader should decide which agent handles what
- Flexible collaboration patterns

**When to use Workflows:**
- Predictable, repeatable processes
- Need explicit step control
- Complex conditional/parallel logic

---

## Learning Path

**Beginner:**
1. `01-building-teams.md` - Create first team
2. `02-running-teams.md` - Run and get responses
3. `03-delegation.md` - Understand how delegation works

**Intermediate:**
4. `04-basic-flows.md` - Common patterns
5. `05-async-flows.md` - Async execution
6. `06-run-as-cli.md` - Interactive testing

---

*Last Updated: December 2025 | AGNO 2.3.4*
