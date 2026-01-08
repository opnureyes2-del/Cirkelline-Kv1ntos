# Run As CLI

**AGNO Version:** 2.2.13
**Source:** https://docs.agno.com/basics/teams/usage/other/run-as-cli

---

## Overview

AGNO provides a **built-in interactive CLI** that runs your Team (or Agent) as a command-line application. This allows you to test back-and-forth conversations directly in your terminal without needing a web interface.

---

## The `cli_app()` Method

### For Teams

```python
team.cli_app(
    input="Initial greeting message",      # Optional first message from team
    user="User",                            # Display name for user
    emoji=":sunglasses:",                   # Emoji for user
    stream=True,                            # Stream responses in real-time
    markdown=True,                          # Format output as markdown
    exit_on=["exit", "quit", "bye"],        # Commands to exit CLI
    session_id="my-session",                # Optional session ID
    user_id="user-123",                     # Optional user ID
)
```

### For Agents

```python
agent.cli_app(
    input="Hello! How can I help?",
    user="User",
    emoji=":sunglasses:",
    stream=True,
    markdown=True,
    exit_on=["exit", "quit", "bye"],
    session_id="my-session",
    user_id="user-123",
)
```

### Async Version

```python
import asyncio

# For teams
asyncio.run(team.acli_app(stream=True))

# For agents
asyncio.run(agent.acli_app(stream=True))
```

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input` | `Optional[str]` | `None` | Initial message from team/agent |
| `user` | `str` | `"User"` | Display name for the user |
| `emoji` | `str` | `":sunglasses:"` | Emoji displayed next to user |
| `stream` | `bool` | `False` | Stream responses in real-time |
| `markdown` | `bool` | `False` | Format output as markdown |
| `exit_on` | `Optional[List[str]]` | `None` | Commands to exit (default: exit, quit, bye) |
| `session_id` | `Optional[str]` | `None` | Session ID for history persistence |
| `user_id` | `Optional[str]` | `None` | User ID for personalization |

---

## Basic Example: Team CLI

```python
from agno.team import Team
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat

news_agent = Agent(
    name="News Agent",
    role="Get the latest news"
)

weather_agent = Agent(
    name="Weather Agent",
    role="Get the weather for the next 7 days"
)

team = Team(
    name="News and Weather Team",
    members=[news_agent, weather_agent],
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file="tmp/data.db"),
    add_history_to_context=True,
    num_history_runs=3,
)

# Run team as interactive CLI
team.cli_app(stream=True)
```

---

## Advanced Example: Writing Team

```python
from agno.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

# Research Specialist
research_agent = Agent(
    name="Research Specialist",
    role="Conduct information research and fact verification",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[DuckDuckGoTools()],
    instructions=[
        "Provide multiple reliable sources",
        "Include statistics when available",
        "Cross-reference claims",
    ],
)

# Creative Brainstormer
brainstormer = Agent(
    name="Creative Brainstormer",
    role="Generate unique content concepts and creative angles",
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions=[
        "Develop compelling headlines",
        "Create story structures",
        "Target audience-specific ideas",
    ],
)

# Content Writer
writer = Agent(
    name="Content Writer",
    role="Create structured, engaging content",
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions=[
        "Write with clear logical flow",
        "Adapt tone for target readers",
        "Apply SEO best practices",
    ],
)

# Editor
editor = Agent(
    name="Editor",
    role="Quality assurance and final polish",
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions=[
        "Check grammar and clarity",
        "Ensure consistency",
        "Prepare for publication",
    ],
)

# Create the team
writing_team = Team(
    name="Writing Team",
    model=OpenAIChat(id="gpt-4o"),
    members=[research_agent, brainstormer, writer, editor],
    show_members_responses=True,
    markdown=True,
    instructions=[
        "Coordinate writing tasks among team members",
        "Research first, then brainstorm, write, and edit",
    ],
)

if __name__ == "__main__":
    print("Welcome to the Writing Team CLI!")
    print("Type 'exit' to quit.\n")

    writing_team.cli_app(
        input="Hello! I'm your writing team. What would you like us to write today?",
        user="Writer",
        emoji="✍️",
        stream=True,
    )
```

---

## Agent CLI Example

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[HackerNewsTools()],
    db=SqliteDb(db_file="tmp/data.db"),
    add_history_to_context=True,
    num_history_runs=3,
    markdown=True,
)

# Run agent as interactive CLI
agent.cli_app(stream=True)
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Interactive Loop** | Continuous back-and-forth conversation |
| **History Persistence** | With `db` configured, history is saved across sessions |
| **Streaming** | Real-time response delivery with `stream=True` |
| **Member Visibility** | With `show_members_responses=True`, see all agent contributions |
| **Custom Exit Commands** | Define your own exit commands |
| **Session Management** | Specify `session_id` to resume conversations |

---

## Use Cases

### 1. Local Development & Testing

Test your team/agent without spinning up a web server:

```python
# Quick test during development
team.cli_app(stream=True, markdown=True)
```

### 2. Debugging Conversations

See exactly what's happening:

```python
team = Team(
    ...,
    debug_mode=True,
    show_members_responses=True,
)
team.cli_app(stream=True)
```

### 3. Demo & Prototyping

Quickly demonstrate team capabilities:

```python
team.cli_app(
    input="Welcome! I'm your AI assistant team. How can I help?",
    user="Demo User",
    emoji="🎯",
    stream=True,
)
```

### 4. Internal Tools

Create command-line tools for internal use:

```bash
python my_team.py  # Runs as interactive CLI
```

---

## Comparison: CLI vs Web API

| Aspect | `cli_app()` | FastAPI/Web |
|--------|-------------|-------------|
| Setup | Zero - just call method | Need server, routes |
| Use case | Dev, testing, demos | Production |
| Multi-user | Single user | Multiple concurrent |
| Deployment | Local only | Can deploy anywhere |
| History | File-based (SQLite) | Database (PostgreSQL) |

---

## Tips

### Persist History

```python
from agno.db.sqlite import SqliteDb

team = Team(
    ...,
    db=SqliteDb(db_file="conversations.db"),
    add_history_to_context=True,
    num_history_runs=5,
)
```

### Resume Session

```python
team.cli_app(
    session_id="my-previous-session",
    stream=True,
)
```

### Custom User Display

```python
team.cli_app(
    user="Ivo",
    emoji="👨‍💻",
    stream=True,
)
```

---

## Summary

| Method | Description |
|--------|-------------|
| `team.cli_app()` | Sync interactive CLI for teams |
| `team.acli_app()` | Async interactive CLI for teams |
| `agent.cli_app()` | Sync interactive CLI for agents |
| `agent.acli_app()` | Async interactive CLI for agents |

**Key:** `cli_app()` is perfect for development, testing, and demos. For production multi-user applications, use FastAPI/AgentOS.
