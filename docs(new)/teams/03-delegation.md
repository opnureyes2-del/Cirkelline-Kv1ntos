# Team Delegation

**AGNO Version:** 2.2.13
**Source:** https://docs.agno.com/basics/teams/delegation

---

## How Delegation Works

A Team has an internal **team leader** that delegates tasks to members. The team leader uses a model to analyze input and decide which member(s) should handle the task.

### Basic Flow

```
1. Team receives user input
2. Team leader analyzes input and breaks it into subtasks
3. Team leader delegates specific tasks to appropriate members
   └── Uses `delegate_task_to_member` tool internally
4. Members complete tasks and return results
5. Team leader either:
   └── Delegates to more members, OR
   └── Synthesizes outputs into final response
```

### Concurrent Execution

When using `arun()` and the team leader delegates to **multiple members at once**, those members run **concurrently**:

```python
# Sequential (run)
response = team.run("Query")  # Members execute one at a time

# Concurrent (arun)
response = await team.arun("Query")  # Multiple members execute in parallel
```

---

## Key Delegation Parameters

### Overview

| Parameter | Default | Description |
|-----------|---------|-------------|
| `respond_directly` | `False` | Return member responses without synthesis |
| `determine_input_for_members` | `True` | Team leader crafts custom input for members |
| `delegate_to_all_members` | `False` | Delegate to ALL members simultaneously |

---

## respond_directly

**Default:** `False` - Team leader synthesizes member responses into cohesive output.

**Set to `True`:** Return member responses directly without team leader processing.

```python
# Default behavior (respond_directly=False)
team = Team(
    members=[english_agent, spanish_agent],
)
# User asks in Spanish → Spanish agent responds → Team leader synthesizes → User

# With respond_directly=True
team = Team(
    members=[english_agent, spanish_agent],
    respond_directly=True,  # Bypass team leader synthesis
)
# User asks in Spanish → Spanish agent responds → User (directly)
```

### Use Cases

- Language routing (no need to process translations)
- Specialized agents that should speak directly to user
- Reducing latency by skipping synthesis step

### Important Notes

- **NOT compatible** with `delegate_to_all_members`
- If team leader delegates to multiple members, responses are **concatenated**

---

## determine_input_for_members

**Default:** `True` - Team leader crafts a custom task description for each member.

**Set to `False`:** Send original user input directly to members unchanged.

```python
# Default behavior (determine_input_for_members=True)
team = Team(
    members=[researcher, analyst],
)
# User: "Tell me about AI"
# → Researcher gets: "Research the latest developments in AI"
# → Analyst gets: "Analyze the implications of AI trends"

# With determine_input_for_members=False
team = Team(
    members=[researcher, analyst],
    determine_input_for_members=False,  # Pass input unchanged
)
# User: "Tell me about AI"
# → Researcher gets: "Tell me about AI" (unchanged)
# → Analyst gets: "Tell me about AI" (unchanged)
```

### Use Cases

- Structured inputs (Pydantic models) that members should receive as-is
- When you want consistent input across all members
- Router teams where input shouldn't be modified

---

## delegate_to_all_members

**Default:** `False` - Team leader selectively chooses which member(s) to delegate to.

**Set to `True`:** Delegate to ALL members simultaneously.

```python
# Default behavior (delegate_to_all_members=False)
team = Team(
    members=[reddit_researcher, hackernews_researcher, twitter_researcher],
)
# Team leader decides: "This question is best for Reddit researcher"
# → Only Reddit researcher runs

# With delegate_to_all_members=True
team = Team(
    members=[reddit_researcher, hackernews_researcher, twitter_researcher],
    delegate_to_all_members=True,  # All members work on it
)
# → ALL three researchers run simultaneously
# → Team leader synthesizes all their findings
```

### Use Cases

- Research teams gathering multiple perspectives
- Review teams where all reviewers should evaluate
- Consensus-building across specialists

### Important Notes

- **NOT compatible** with `respond_directly`
- With `arun()`, all members execute **concurrently** (maximum parallelism)

---

## Team Patterns

### 1. Coordinator (Default)

Team leader analyzes, delegates selectively, and synthesizes responses.

```python
team = Team(
    name="Research Team",
    members=[researcher, analyst],
    model=OpenAIChat(id="gpt-4o"),
    # All defaults
)
```

**Flow:** User → Leader analyzes → Selective delegation → Leader synthesizes → User

---

### 2. Router / Passthrough

Team leader routes to appropriate member without modifying input or output.

```python
team = Team(
    name="Language Router",
    members=[
        Agent(name="English Agent", role="Answer in English"),
        Agent(name="Spanish Agent", role="Answer in Spanish"),
        Agent(name="German Agent", role="Answer in German"),
    ],
    model=OpenAIChat(id="gpt-4o-mini"),  # Lightweight model for routing
    respond_directly=True,              # Don't process member output
    determine_input_for_members=False,  # Don't modify input
)
```

**Flow:** User → Leader routes → Member responds → User (leader bypassed)

**Best for:**
- Language routing
- Specialized agent selection
- Minimizing latency

---

### 3. Collaboration / Fan-out

All members work on the same task simultaneously.

```python
team = Team(
    name="Review Team",
    members=[
        Agent(name="Security Reviewer", role="Review for security issues"),
        Agent(name="Performance Reviewer", role="Review for performance"),
        Agent(name="UX Reviewer", role="Review for user experience"),
    ],
    model=OpenAIChat(id="gpt-4o"),
    delegate_to_all_members=True,  # All reviewers work simultaneously
)
```

**Flow:** User → Leader → ALL members work → Leader synthesizes → User

**Best for:**
- Multi-perspective analysis
- Parallel research
- Comprehensive reviews

---

## Migration from v1.x.x

The `mode` parameter is **deprecated**. Use these parameters instead:

| Old Mode | New Parameters |
|----------|----------------|
| `mode="coordinate"` | Default (no changes needed) |
| `mode="route"` | `respond_directly=True, determine_input_for_members=False` |
| `mode="collaborate"` | `delegate_to_all_members=True` |

---

## System Message Context

The team leader automatically receives information about members in its system message:

```
You are the leader of a team of AI Agents.
Your task is to coordinate the team to complete the user's request.

Here are the members in your team:
<team_members>
- Agent 1:
    - ID: web-researcher
    - Name: Web Researcher
    - Role: You are a web researcher that can find information on the web.
    - Member tools:
        - duckduckgo_search
        - duckduckgo_news
- Agent 2:
    - ID: legal-analyst
    - Name: Legal Analyst
    - Role: You analyze legal documents and provide insights.
</team_members>

<how_to_respond>
- Forward tasks to members with highest likelihood of completing the request.
- Analyze tools available to members and their roles before delegating.
- You cannot use member tools directly. You can only delegate tasks.
- When delegating include: member_id, task_description, expected_output.
- You can delegate to multiple members at once.
- Always analyze responses from members before responding to user.
</how_to_respond>
```

### Control Member Information

```python
team = Team(
    members=[...],
    add_member_tools_to_context=False,  # Don't show member tools in system message
)
```

---

## Sharing Context Between Members

### Share Member Interactions (Within Same Run)

Allow members to see what other members have done during the current run:

```python
team = Team(
    members=[researcher, analyst],
    share_member_interactions=True,  # Members see each other's work
)
```

When enabled, subsequent members receive:

```
<member_interaction_context>
- Member: Web Researcher
- Task: Find information about AI trends
- Response: I found the following trends...
</member_interaction_context>
```

### Share Team History (Across Runs)

Allow members to see previous team interactions:

```python
team = Team(
    members=[...],
    add_team_history_to_members=True,  # Members see team history
    num_team_history_runs=3,           # Number of previous runs to include
)
```

---

## Complete Example: Multi-Lingual Router

```python
from uuid import uuid4
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team import Team

german_agent = Agent(
    name="German Agent",
    role="You answer German questions.",
    model=OpenAIChat(id="gpt-4o-mini"),
    add_history_to_context=True,  # Member has its own history
)

spanish_agent = Agent(
    name="Spanish Agent",
    role="You answer Spanish questions.",
    model=OpenAIChat(id="gpt-4o-mini"),
    add_history_to_context=True,
)

router_team = Team(
    name="Multi-Lingual Router",
    model=OpenAIChat(id="gpt-4o-mini"),
    members=[german_agent, spanish_agent],
    instructions=[
        "Route questions to the appropriate language agent.",
        "German questions → German Agent",
        "Spanish questions → Spanish Agent",
    ],
    db=SqliteDb(db_file="router.db"),
    respond_directly=True,              # Return member response directly
    determine_input_for_members=False,  # Pass input unchanged
)

session_id = f"conversation_{uuid4()}"

# German question
router_team.print_response(
    "Hallo, wie heißt du?",
    stream=True,
    session_id=session_id
)

# Spanish question
router_team.print_response(
    "Hola, ¿cómo estás?",
    stream=True,
    session_id=session_id
)
```

---

## Summary

| Pattern | Parameters | Use Case |
|---------|------------|----------|
| **Coordinator** | Defaults | Complex tasks needing synthesis |
| **Router** | `respond_directly=True, determine_input_for_members=False` | Language routing, specialist selection |
| **Collaboration** | `delegate_to_all_members=True` | Multi-perspective, parallel research |

| Parameter | Effect |
|-----------|--------|
| `respond_directly=True` | Skip team leader synthesis |
| `determine_input_for_members=False` | Pass user input unchanged |
| `delegate_to_all_members=True` | All members work simultaneously |
| `share_member_interactions=True` | Members see each other's work (same run) |
| `add_team_history_to_members=True` | Members see team history (across runs) |
