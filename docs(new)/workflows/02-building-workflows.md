# Building Workflows

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/building-workflows

---

## Introduction

Workflows are a powerful way to orchestrate your agents and teams. They are a series of steps that are executed in a flow that you control.

You can combine agents, teams, and custom Python functions to build sophisticated automation pipelines with predictable execution patterns.

---

## Building Blocks

The core components for building workflows:

| Component | Purpose | Description |
|-----------|---------|-------------|
| **Workflow** | Top-level orchestrator | Manages the entire execution process |
| **Step** | Basic execution unit | Encapsulates exactly ONE executor (agent, team, or function) |
| **Parallel** | Concurrent execution | Execute steps simultaneously, outputs joined together |
| **Condition** | Conditional logic | Make steps conditional based on criteria you specify |
| **Loop** | Iterative execution | Repeat steps until a condition is met |
| **Router** | Dynamic routing | Specify which step(s) to execute next (branching logic) |
| **Steps** | Reusable sequences | Group multiple steps into reusable modules |

---

## Your First Workflow

The simplest workflow combines agents, teams, and functions:

```python
from agno.workflow import Workflow, StepOutput

# Custom function for preprocessing
def data_preprocessor(step_input):
    # Custom preprocessing logic
    # Or run any agent/team here
    return StepOutput(content=f"Processed: {step_input.input}")

# Build the workflow
workflow = Workflow(
    name="Mixed Execution Pipeline",
    steps=[
        research_team,      # Team as step
        data_preprocessor,  # Function as step
        content_agent,      # Agent as step
    ]
)

# Run it
workflow.print_response(
    "Analyze the competitive landscape for fintech startups",
    markdown=True
)
```

---

## Step Types

Each step can have exactly ONE executor:

### 1. Agent as Step

```python
from agno.agent import Agent
from agno.workflow import Workflow

research_agent = Agent(
    name="Researcher",
    instructions="Research the given topic thoroughly.",
)

workflow = Workflow(
    name="Research Workflow",
    steps=[research_agent],  # Agent directly as step
)
```

### 2. Team as Step

```python
from agno.team import Team
from agno.workflow import Workflow

research_team = Team(
    name="Research Team",
    members=[agent1, agent2],
    instructions="Collaborate on research tasks.",
)

workflow = Workflow(
    name="Team Research Workflow",
    steps=[research_team],  # Team directly as step
)
```

### 3. Function as Step

```python
from agno.workflow import Workflow
from agno.workflow.types import StepInput, StepOutput

def custom_processor(step_input: StepInput) -> StepOutput:
    """Custom processing function"""
    data = step_input.input
    processed = f"Processed: {data}"
    return StepOutput(content=processed)

workflow = Workflow(
    name="Function Workflow",
    steps=[custom_processor],  # Function directly as step
)
```

---

## Named Steps

For better logging and tracking, use the `Step` class to name your steps:

```python
from agno.workflow import Workflow, Step

# Define named steps
research_step = Step(
    name="Research Phase",
    agent=research_agent,
    description="Research the topic thoroughly",
)

analysis_step = Step(
    name="Analysis Phase",
    team=analysis_team,
    description="Analyze the research findings",
)

writing_step = Step(
    name="Writing Phase",
    executor=custom_writer_function,
    description="Write the final content",
)

# Build workflow with named steps
workflow = Workflow(
    name="Content Pipeline",
    steps=[research_step, analysis_step, writing_step],
)
```

### Benefits of Named Steps

1. **Better Logging:** Clear identification in logs
2. **Easier Debugging:** Know which step failed
3. **Platform Support:** Enhanced visibility in AgentOS
4. **Output Access:** Access step outputs by name

---

## Step Parameters

The `Step` class accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Step identifier (required) |
| `agent` | `Agent` | Agent executor |
| `team` | `Team` | Team executor |
| `executor` | `Callable` | Custom function executor |
| `description` | `str` | Step description for logging |

**Note:** You must provide exactly ONE of `agent`, `team`, or `executor`.

---

## StepInput: What Steps Receive

Every step receives a `StepInput` object with:

```python
from agno.workflow.types import StepInput

def my_step(step_input: StepInput) -> StepOutput:
    # Original workflow input
    original_message = step_input.input

    # Output from previous step
    previous_output = step_input.previous_step_content

    # All previous step outputs (by name)
    all_outputs = step_input.previous_step_outputs

    # Access specific step output
    if all_outputs:
        research_result = all_outputs.get("Research Phase")

    # Media from previous steps
    images = step_input.images
    videos = step_input.videos
    audio = step_input.audio
```

### StepInput Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `input` | `Optional[str]` | Original workflow input message |
| `previous_step_content` | `Optional[Any]` | Content from the last step |
| `previous_step_outputs` | `Dict[str, StepOutput]` | All outputs by step name |
| `images` | `List[Image]` | Accumulated images |
| `videos` | `List[Video]` | Accumulated videos |
| `audio` | `List[Audio]` | Accumulated audio |
| `files` | `List[File]` | Accumulated files |

---

## StepOutput: What Steps Return

Custom functions must return a `StepOutput` object:

```python
from agno.workflow.types import StepOutput

def my_step(step_input: StepInput) -> StepOutput:
    try:
        result = process(step_input.input)
        return StepOutput(
            content=result,      # Main output
            success=True,        # Execution succeeded
        )
    except Exception as e:
        return StepOutput(
            content="Processing failed",
            success=False,
            error=str(e),
        )
```

### StepOutput Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `Any` | `None` | Primary output content |
| `success` | `bool` | `True` | Execution success status |
| `error` | `str` | `None` | Error message if failed |
| `stop` | `bool` | `False` | Stop entire workflow early |
| `images` | `List[Image]` | `None` | Output images |
| `videos` | `List[Video]` | `None` | Output videos |
| `audio` | `List[Audio]` | `None` | Output audio |

---

## Early Workflow Termination

Use `stop=True` to terminate the workflow early:

```python
def validation_step(step_input: StepInput) -> StepOutput:
    data = step_input.previous_step_content

    if not is_valid(data):
        return StepOutput(
            content="Validation failed - stopping workflow",
            stop=True,  # Terminate workflow here
        )

    return StepOutput(content="Validation passed")
```

---

## Calling Agents/Teams Inside Functions

Custom functions can orchestrate agents and teams:

```python
def custom_orchestration(step_input: StepInput) -> StepOutput:
    """Custom function that calls agents internally"""
    message = step_input.input
    previous = step_input.previous_step_content

    # Build a prompt using previous step data
    prompt = f"""
    Topic: {message}
    Research: {previous[:500] if previous else "None"}

    Create a content plan based on this research.
    """

    # Call an agent inside the function
    response = content_planner.run(prompt)

    # Enhance and return
    enhanced = f"""
    ## Content Plan

    **Topic:** {message}
    **Research Used:** {"Yes" if previous else "No"}

    {response.content}
    """

    return StepOutput(content=enhanced)
```

---

## Class-Based Executors

For complex logic, use class-based executors:

```python
from agno.workflow.types import StepInput, StepOutput

class ContentPlanningExecutor:
    """Class-based executor with configuration"""

    def __init__(self, max_weeks: int = 4, posts_per_week: int = 3):
        self.max_weeks = max_weeks
        self.posts_per_week = posts_per_week
        self.planner_agent = Agent(
            name="Planner",
            instructions=f"Plan content for {max_weeks} weeks, {posts_per_week} posts/week"
        )

    def __call__(self, step_input: StepInput) -> StepOutput:
        """Execute the planning logic"""
        response = self.planner_agent.run(step_input.input)
        return StepOutput(content=response.content)

# Use in workflow
planning_step = Step(
    name="Content Planning",
    executor=ContentPlanningExecutor(max_weeks=4, posts_per_week=3),
)
```

### When to Use Class-Based Executors

1. **Configuration at initialization:** Pass settings, API keys, or behavior flags
2. **Stateful execution:** Maintain counters, caches, or track information
3. **Reusable components:** Create configured instances shared across workflows

---

## Adding Database Storage

Persist workflow sessions and state:

```python
from agno.workflow import Workflow
from agno.db.postgres import PostgresDb
from agno.db.sqlite import SqliteDb

# PostgreSQL
workflow = Workflow(
    name="Production Workflow",
    steps=[...],
    db=PostgresDb(db_url="postgresql+psycopg://user:pass@localhost/db"),
)

# SQLite (for development)
workflow = Workflow(
    name="Dev Workflow",
    steps=[...],
    db=SqliteDb(
        db_file="tmp/workflow.db",
        session_table="workflow_session",
    ),
)
```

---

## Workflow Parameters

The `Workflow` class accepts:

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Workflow name (required) |
| `description` | `str` | Workflow description |
| `steps` | `List` | List of steps or single function |
| `db` | `Db` | Database for persistence |
| `session_state` | `Dict` | Initial session state |
| `agent` | `WorkflowAgent` | For conversational workflows |

---

## Complete Example

```python
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput
from agno.db.postgres import PostgresDb
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

# Define agents
hackernews_agent = Agent(
    name="HackerNews Agent",
    tools=[HackerNewsTools()],
    instructions="Extract insights from HackerNews",
)

web_agent = Agent(
    name="Web Agent",
    tools=[DuckDuckGoTools()],
    instructions="Search the web for trends",
)

content_planner = Agent(
    name="Content Planner",
    instructions="Create a 4-week content plan with 3 posts/week",
)

# Define team
research_team = Team(
    name="Research Team",
    members=[hackernews_agent, web_agent],
    instructions="Research topics from multiple sources",
)

# Define custom function
def enhance_plan(step_input: StepInput) -> StepOutput:
    """Enhance the content plan with metadata"""
    plan = step_input.previous_step_content

    enhanced = f"""
    ## Enhanced Content Plan

    **Generated:** {datetime.now().isoformat()}
    **Topic:** {step_input.input}

    {plan}

    ---
    *Auto-generated by Content Pipeline*
    """
    return StepOutput(content=enhanced)

# Define named steps
research_step = Step(
    name="Research",
    team=research_team,
    description="Multi-source research",
)

planning_step = Step(
    name="Planning",
    agent=content_planner,
    description="Create content plan",
)

enhance_step = Step(
    name="Enhancement",
    executor=enhance_plan,
    description="Add metadata and formatting",
)

# Build workflow
workflow = Workflow(
    name="Content Creation Pipeline",
    description="Research, plan, and enhance content",
    steps=[research_step, planning_step, enhance_step],
    db=PostgresDb("postgresql+psycopg://user:pass@localhost/db"),
)

# Run
if __name__ == "__main__":
    workflow.print_response(
        input="AI trends in 2025",
        markdown=True,
    )
```

---

## Best Practices

### Do's

1. **Name your steps** for better debugging and logging
2. **Use StepInput/StepOutput** consistently for custom functions
3. **Add database persistence** for production workflows
4. **Handle errors gracefully** with `success=False` and `error` messages
5. **Use class-based executors** for complex, configurable logic

### Don'ts

1. **Don't mix executor types** in one Step (choose ONE: agent, team, or executor)
2. **Don't forget to return StepOutput** from custom functions
3. **Don't ignore previous step output** - use `step_input.previous_step_content`
4. **Don't skip validation** - use Conditions for quality gates

---

## Summary

| Concept | Purpose |
|---------|---------|
| `Workflow` | Top-level orchestrator |
| `Step` | Named execution unit with one executor |
| `StepInput` | Data received by each step |
| `StepOutput` | Data returned by each step |
| `db` | Database for persistence |

---

## Related Documentation

- **Running Workflows:** `docs(new)/workflows/03-running-workflows.md`
- **Workflow Patterns:** `docs(new)/workflows/04-basic-patterns.md`
- **Sessions & State:** https://docs.agno.com/basics/sessions/workflow-sessions

---

*Last Updated: December 2025 | AGNO 2.3.4*
