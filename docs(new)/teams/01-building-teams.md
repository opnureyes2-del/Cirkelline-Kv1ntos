# Building Teams

**AGNO Version:** 2.2.13
**Source:** https://docs.agno.com/basics/teams/building-teams

---

## What is a Team?

A Team is a collection of Agents (or other sub-teams) that work together to accomplish tasks.

**Core concept:**
- A Team has a **team leader** (the top level) that coordinates work
- Team leader delegates tasks to **members** based on their roles
- Members can be `Agent` or `Team` instances (nested teams)

**Think of it as a tree structure:**
```
Team Leader
├── Agent A (specialist)
├── Agent B (specialist)
└── Sub-Team
    ├── Agent C
    └── Agent D
```

---

## When to Use Teams?

Use Teams when:
- Task requires **variety of tools** or **long list of steps**
- Single agent's **context limit gets exceeded**
- Complex task needs **multiple specialists**

**Guideline:** Keep Agents narrow in scope. When complexity grows, use a Team of single-purpose agents.

---

## Your First Team

### Minimal Example

```python
from agno.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

# Create specialized agents
news_agent = Agent(
    id="news-agent",
    name="News Agent",
    role="Get the latest news and provide summaries",
    tools=[DuckDuckGoTools()]
)

weather_agent = Agent(
    id="weather-agent",
    name="Weather Agent",
    role="Get weather information and forecasts",
    tools=[DuckDuckGoTools()]
)

# Create the team
team = Team(
    name="News and Weather Team",
    members=[news_agent, weather_agent],
    model=OpenAIChat(id="gpt-4o"),
    instructions="Coordinate with team members to provide comprehensive information."
)

team.print_response("What's the latest news and weather in Tokyo?", stream=True)
```

**Key elements:** Model + Members + Instructions

---

## Member Configuration

### Required Fields (Recommended)

Specify these for better team leader identification:

| Field | Purpose |
|-------|---------|
| `id` | Identifies member in team context |
| `name` | Display name for member |
| `role` | Describes what the member does (team leader uses this to decide delegation) |

```python
agent = Agent(
    id="research-agent",      # Required for delegation
    name="Research Agent",    # Human-readable name
    role="Research and analyze information from the web",  # Critical for routing
    tools=[...]
)
```

---

## Model Inheritance

Members inherit the model from their parent Team if not explicitly specified.

| Scenario | Behavior |
|----------|----------|
| Member has no model | Inherits from parent Team |
| Member has explicit model | Uses its own model |
| Team has no model | Defaults to OpenAI `gpt-4o` |
| Nested teams | Inherits from direct parent |

**Important:** `reasoning_model`, `parser_model`, and `output_model` must be explicitly defined (no inheritance).

```python
# Example: Member inherits team's model
team = Team(
    model=OpenAIChat(id="gpt-4o"),  # Team's model
    members=[
        Agent(name="Agent A"),       # Inherits gpt-4o
        Agent(
            name="Agent B",
            model=Claude(id="claude-3-5-sonnet"),  # Uses its own
        ),
    ],
)
```

---

## Team Features

Teams support the same features as Agents:

| Feature | Description |
|---------|-------------|
| **Model** | Used by team leader to delegate tasks |
| **Instructions** | Guide how team leader solves problems |
| **Database** | Store session history and state |
| **Reasoning** | Team leader can "think" before delegating |
| **Knowledge** | Knowledge base accessible to team leader |
| **Memory** | Store/recall information from previous interactions |
| **Tools** | Team leader can use tools directly |

---

## Delegation Behavior

### Default Behavior (Coordinate Mode)

By default, the team leader:
1. Receives user request
2. Analyzes and determines which member(s) to delegate to
3. Synthesizes a custom input for each member
4. Collects responses from members
5. Synthesizes final response for user

### Key Delegation Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `respond_directly` | `False` | If `True`, return member responses directly (no synthesis) |
| `determine_input_for_members` | `True` | If `False`, send user input directly to members |
| `delegate_to_all_members` | `False` | If `True`, delegate to ALL members simultaneously |

---

## Common Team Patterns

### 1. Coordinator Team (Default)

Team leader synthesizes input for members and synthesizes their responses.

```python
team = Team(
    name="Research Team",
    model=OpenAIChat(id="gpt-4o"),
    members=[researcher, analyst],
    instructions="Coordinate research and analysis tasks.",
)
```

**Flow:** User → Leader synthesizes → Members work → Leader synthesizes → User

---

### 2. Router/Passthrough Team

Team leader routes to appropriate member without modifying input/output.

```python
team = Team(
    name="Language Router",
    model=OpenAIChat(id="gpt-4o-mini"),
    members=[
        Agent(name="English Agent", role="Answer in English"),
        Agent(name="Spanish Agent", role="Answer in Spanish"),
    ],
    respond_directly=True,              # Don't process member responses
    determine_input_for_members=False,  # Send input directly to member
)
```

**Flow:** User → Leader routes → Member responds → User (leader bypassed)

---

### 3. Collaboration Team

All members work on the same task simultaneously.

```python
team = Team(
    name="Review Team",
    model=OpenAIChat(id="gpt-4o"),
    members=[reviewer_1, reviewer_2, reviewer_3],
    delegate_to_all_members=True,  # All members get the task
)
```

**Flow:** User → Leader → ALL members work → Leader synthesizes → User

**Note:** `respond_directly` is NOT compatible with `delegate_to_all_members`.

---

## Nested Teams

Teams can contain other teams as members:

```python
team = Team(
    name="Main Team",
    members=[
        Agent(name="English Agent", role="Answer in English"),
        Agent(name="Chinese Agent", role="Answer in Chinese"),
        Team(
            name="Germanic Team",
            role="Answer questions in German and Dutch",
            members=[
                Agent(name="German Agent", role="Answer in German"),
                Agent(name="Dutch Agent", role="Answer in Dutch"),
            ],
        ),
    ],
)
```

---

## Running Teams

### Development

```python
# Print response to terminal
team.print_response("What's the weather?", stream=True)

# Show member responses too
team.print_response("...", stream=True, show_members_responses=True)
```

### Production

```python
# Synchronous
response = team.run("What's the weather?")
print(response.content)

# Asynchronous
response = await team.arun("What's the weather?")

# Streaming
stream = team.run("...", stream=True)
for chunk in stream:
    print(chunk.content, end="", flush=True)
```

---

## Team History

### Team Leader History

```python
team = Team(
    db=SqliteDb(db_file="team.db"),
    add_history_to_context=True,  # Leader sees previous requests
)
```

### Share History with Members

```python
team = Team(
    db=SqliteDb(db_file="team.db"),
    add_team_history_to_members=True,  # Members see team's history
)
```

This allows members to recall context from previous interactions with other members.

---

## Migration from v1.x.x

The `mode` parameter is deprecated. Use these instead:

| Old Mode | New Parameters |
|----------|----------------|
| `mode="coordinate"` | Default behavior (no changes needed) |
| `mode="route"` | `respond_directly=True, determine_input_for_members=False` |
| `mode="collaborate"` | `delegate_to_all_members=True` |

---

## Summary

| Concept | Description |
|---------|-------------|
| **Team** | Collection of Agents/Teams working together |
| **Team Leader** | Top-level coordinator that delegates tasks |
| **Members** | Agents or sub-Teams that do the work |
| **Model Inheritance** | Members inherit team's model if not specified |
| **respond_directly** | Return member responses without synthesis |
| **determine_input_for_members** | Whether leader synthesizes input for members |
| **delegate_to_all_members** | Send task to all members simultaneously |

**Key Best Practices:**
1. Always specify `id`, `name`, `role` for members
2. Keep agents narrow in scope
3. Use Teams when single agent context is exceeded
4. Choose the right pattern: Coordinator, Router, or Collaboration
5. Use `show_members_responses=True` during development
