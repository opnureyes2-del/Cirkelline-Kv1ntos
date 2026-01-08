# Workflows Overview

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/overview

---

## What Are Workflows?

AGNO Workflows enable you to build **deterministic, controlled agentic flows** by orchestrating agents, teams, and functions through a series of defined steps. Unlike free-form agent interactions, workflows provide structured automation with predictable execution patterns.

Each step in a workflow handles a specific part of a larger task, with output automatically flowing from one step to the next, creating a smooth pipeline from start to finish.

**Think of it like an assembly line:** each step specializes in one thing, and together they accomplish complex tasks that would be hard for a single agent or team to handle.

### Key Characteristics

| Characteristic | Description |
|----------------|-------------|
| **Deterministic** | Predictable step-by-step processing with defined inputs/outputs |
| **Controlled** | You define the exact execution flow |
| **Orchestrated** | Combines agents, teams, and custom functions |
| **Reliable** | Consistent results across multiple runs |
| **Auditable** | Clear execution history and metrics |

---

## Workflows vs Teams vs Agents

Understanding when to use each construct is critical:

| Construct | Purpose | Execution Style | Best For |
|-----------|---------|-----------------|----------|
| **Agent** | Single AI assistant with specific role | Free-form conversation | Single tasks, Q&A |
| **Team** | Coordinated group of agents | Dynamic, collaborative | Complex problems requiring discussion |
| **Workflow** | Orchestrated pipeline of steps | Deterministic, sequential | Production pipelines, repeatable processes |

### Decision Guide

**Use Workflows when you need:**
- Predictable, repeatable processes
- Clear audit trails
- Controlled handoffs between steps
- Production reliability with consistent results

**Use Teams when you need:**
- Flexible, collaborative problem-solving
- Dynamic agent coordination
- Emergent solutions from discussion

---

## Building Blocks

Workflows are composed of these core components:

| Component | Purpose | Import |
|-----------|---------|--------|
| **Workflow** | Top-level orchestrator | `from agno.workflow import Workflow` |
| **Step** | Basic execution unit | `from agno.workflow import Step` |
| **Parallel** | Concurrent execution | `from agno.workflow import Parallel` |
| **Condition** | Conditional branching | `from agno.workflow.condition import Condition` |
| **Loop** | Iterative execution | `from agno.workflow.loop import Loop` |
| **Router** | Dynamic path selection | `from agno.workflow.router import Router` |
| **Steps** | Reusable step sequences | `from agno.workflow.steps import Steps` |

### Step Executors

Each Step can have ONE executor type:

```python
from agno.workflow import Step

# Agent as executor
research_step = Step(name="Research", agent=research_agent)

# Team as executor
analysis_step = Step(name="Analysis", team=analysis_team)

# Function as executor
process_step = Step(name="Process", executor=custom_function)
```

---

## Execution Patterns

AGNO Workflows support six execution patterns that can be combined:

### 1. Sequential Workflows

Linear execution where each step depends on the output of the previous step.

```python
from agno.workflow import Workflow

workflow = Workflow(
    name="Content Pipeline",
    steps=[
        research_agent,      # Step 1: Research
        analysis_team,       # Step 2: Analyze
        writer_agent,        # Step 3: Write
    ]
)

workflow.print_response("Write about AI trends")
```

**Use when:** Processes must execute in order (Research → Analyze → Write).

### 2. Parallel Workflows

Concurrent execution for independent tasks that can run simultaneously.

```python
from agno.workflow import Workflow, Step, Parallel

workflow = Workflow(
    name="Research Pipeline",
    steps=[
        Parallel(
            Step(name="HN Research", agent=hackernews_agent),
            Step(name="Web Research", agent=web_agent),
            name="Research Phase"
        ),
        writer_agent,  # Receives combined output
    ]
)
```

**Use when:** Tasks don't depend on each other but contribute to the same goal.

### 3. Conditional Workflows

Branching logic based on conditions.

```python
from agno.workflow import Workflow, Step
from agno.workflow.condition import Condition
from agno.workflow.types import StepInput

def needs_fact_checking(step_input: StepInput) -> bool:
    """Determine if content needs fact-checking"""
    content = step_input.previous_step_content or ""
    keywords = ["study shows", "statistics", "percent", "%"]
    return any(kw in content.lower() for kw in keywords)

workflow = Workflow(
    name="Article Pipeline",
    steps=[
        research_step,
        Condition(
            name="fact_check_condition",
            evaluator=needs_fact_checking,
            steps=[fact_check_step],
        ),
        write_step,
    ]
)
```

**Use when:** Different paths based on content analysis or business logic.

### 4. Iterative Workflows (Loops)

Loop-based execution with exit conditions.

```python
from agno.workflow import Workflow, Step, Loop
from agno.workflow.types import StepOutput
from typing import List

def quality_check(outputs: List[StepOutput]) -> bool:
    """Return True to exit loop, False to continue"""
    if not outputs:
        return False
    total_length = sum(len(o.content or "") for o in outputs)
    return total_length > 500  # Exit when content is substantial

workflow = Workflow(
    name="Research Loop",
    steps=[
        Loop(
            name="Research Loop",
            steps=[research_step, analysis_step],
            end_condition=quality_check,
            max_iterations=3,
        ),
        final_step,
    ]
)
```

**Use when:** Quality must meet a threshold before proceeding.

### 5. Branching Workflows (Router)

Dynamic routing based on input analysis.

```python
from agno.workflow import Workflow, Step
from agno.workflow.router import Router
from agno.workflow.types import StepInput
from typing import List

def route_by_topic(step_input: StepInput) -> List[Step]:
    """Select steps based on topic"""
    topic = (step_input.input or "").lower()

    if "tech" in topic or "ai" in topic:
        return [tech_research_step]
    else:
        return [general_research_step]

workflow = Workflow(
    name="Adaptive Research",
    steps=[
        Router(
            name="topic_router",
            selector=route_by_topic,
            choices=[tech_research_step, general_research_step],
        ),
        write_step,
    ]
)
```

**Use when:** Different topics/inputs require fundamentally different processing.

### 6. Grouped Steps

Reusable step sequences for modular design.

```python
from agno.workflow import Workflow, Step
from agno.workflow.steps import Steps

# Define reusable sequence
article_sequence = Steps(
    name="article_creation",
    steps=[research_step, write_step, edit_step],
)

# Use in workflow
workflow = Workflow(
    name="Article Workflow",
    steps=[article_sequence],
)
```

**Use when:** Step sequences are reused across multiple workflows.

---

## StepInput and StepOutput

Custom functions must use standardized interfaces for data flow:

### StepInput (What Your Function Receives)

```python
from agno.workflow.types import StepInput

def my_function(step_input: StepInput) -> StepOutput:
    # Access available data
    message = step_input.input                    # Original workflow input
    previous = step_input.previous_step_content   # Last step's output
    all_outputs = step_input.previous_step_outputs  # Dict of all step outputs
    images = step_input.images                    # Any images passed through
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `input` | `Optional[str]` | Original workflow input message |
| `previous_step_content` | `Optional[Any]` | Content from the last step |
| `previous_step_outputs` | `Optional[Dict[str, StepOutput]]` | All previous outputs by step name |
| `images` | `Optional[List[Image]]` | Images accumulated from previous steps |
| `videos` | `Optional[List[Video]]` | Videos accumulated from previous steps |
| `audio` | `Optional[List[Audio]]` | Audio accumulated from previous steps |

### StepOutput (What Your Function Returns)

```python
from agno.workflow.types import StepOutput

def my_function(step_input: StepInput) -> StepOutput:
    result = process(step_input.input)

    return StepOutput(
        content=result,       # Main output (required)
        success=True,         # Success status
        stop=False,           # Set True to terminate workflow early
    )
```

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `Any` | `None` | Primary output content |
| `success` | `bool` | `True` | Execution success status |
| `stop` | `bool` | `False` | Early workflow termination |
| `error` | `Optional[str]` | `None` | Error message if failed |

---

## Running Workflows

### Basic Execution

```python
# Non-streaming (returns WorkflowRunOutput)
response = workflow.run(input="Your message", user_id="user123")
print(response.content)

# Streaming (returns iterator)
for event in workflow.run(input="Your message", stream=True):
    print(event.content, end="")

# Helper utility (prints to terminal)
workflow.print_response("Your message", markdown=True)
```

### Async Execution

```python
# Async non-streaming
response = await workflow.arun(input="Your message")

# Async streaming
async for event in await workflow.arun(input="Your message", stream=True):
    print(event.content, end="")
```

### WorkflowRunOutput

The response object contains:

| Attribute | Type | Description |
|-----------|------|-------------|
| `content` | `Any` | Final workflow output |
| `workflow_id` | `str` | Workflow identifier |
| `workflow_name` | `str` | Workflow name |
| `run_id` | `str` | Unique run identifier |
| `session_id` | `str` | Session UUID |
| `step_results` | `List[StepOutput]` | All step outputs |
| `metrics` | `WorkflowMetrics` | Execution metrics |
| `status` | `RunStatus` | Current run status |

---

## Workflow Sessions

Workflow sessions track **execution history** (not conversation messages like Agent/Team sessions).

```
Agent/Team sessions = conversation history (messages back and forth)
Workflow sessions   = execution history (complete pipeline runs with results)
```

### Enabling Sessions

```python
from agno.workflow import Workflow
from agno.db.postgres import PostgresDb

workflow = Workflow(
    name="My Workflow",
    steps=[...],
    db=PostgresDb(db_url="postgresql+psycopg://user:pass@localhost/db"),
)
```

### WorkflowSession Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `session_id` | `str` | Session UUID |
| `user_id` | `Optional[str]` | User identifier |
| `workflow_id` | `Optional[str]` | Workflow identifier |
| `workflow_name` | `Optional[str]` | Workflow name |
| `runs` | `List[WorkflowRunOutput]` | All runs in session |
| `session_data` | `Dict` | Session name, state, media |
| `created_at` | `int` | Creation timestamp |
| `updated_at` | `int` | Last update timestamp |

### Retrieving History

```python
# Get chat history for the workflow
history = workflow.get_chat_history(last_n_runs=5)
```

---

## Workflow State

Session state enables sharing and updating data across ALL workflow components.

### Initializing State

```python
workflow = Workflow(
    name="Shopping Workflow",
    steps=[...],
    session_state={"cart": [], "preferences": {}},
    db=PostgresDb(db_url),
)
```

### Accessing State in Tools

```python
from agno.run.context import RunContext

def add_to_cart(item: str, run_context: RunContext) -> str:
    """Tool that accesses session state"""
    run_context.session_state["cart"].append(item)
    return f"Added {item} to cart"
```

### State Persistence

- State is **automatically persisted** if database is configured
- State is **loaded** in subsequent workflow runs
- All components (agents, teams, functions) can access and modify state

---

## Conversational Workflows

When users interact directly with a workflow, make it conversational using `WorkflowAgent`.

### How It Works

The `WorkflowAgent` intelligently decides whether to:
1. **Answer directly** from past workflow results
2. **Run the workflow** when new processing is needed

```python
from agno.workflow import Workflow, WorkflowAgent
from agno.db.postgres import PostgresDb

workflow_agent = WorkflowAgent(
    model=OpenAIChat(id="gpt-4o-mini"),
    num_history_runs=4,  # How many past runs to consider
)

workflow = Workflow(
    name="Story Generator",
    agent=workflow_agent,
    steps=[story_writer, story_formatter],
    db=PostgresDb(db_url),
)

# First call - runs workflow
workflow.print_response("Tell me a story about a dog named Rocky")

# Second call - answers from history (no workflow run)
workflow.print_response("What was Rocky's personality?")

# Third call - runs workflow (new topic)
workflow.print_response("Now tell me about a cat")
```

### WorkflowAgent Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `Model` | Required | LLM for decision-making |
| `num_history_runs` | `int` | `4` | Past runs visible to agent |

---

## Metrics & Monitoring

Workflows provide detailed metrics at multiple levels:

### Per Workflow

```python
response = workflow.run("Your input")
print(f"Duration: {response.metrics.duration}s")
```

### Per Step

Each step includes:
- `duration`: Execution time in seconds
- Token usage (input/output)
- Model information
- Executor type (agent/team/function)

### Accessing Step Metrics

```python
response = workflow.run("Your input")

for step_result in response.step_results:
    print(f"Step: {step_result.step_name}")
    print(f"Duration: {step_result.metrics.duration}s")
    print(f"Executor: {step_result.executor_type}")
```

---

## Complete Example

Here's a full workflow combining multiple patterns:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step, Parallel
from agno.workflow.condition import Condition
from agno.workflow.types import StepInput, StepOutput
from agno.db.postgres import PostgresDb
from agno.tools.duckduckgo import DuckDuckGoTools

# Define agents
researcher = Agent(
    name="Researcher",
    tools=[DuckDuckGoTools()],
    instructions="Research the topic thoroughly.",
)

fact_checker = Agent(
    name="Fact Checker",
    tools=[DuckDuckGoTools()],
    instructions="Verify facts and claims.",
)

writer = Agent(
    name="Writer",
    instructions="Write engaging content based on research.",
)

# Define condition
def needs_verification(step_input: StepInput) -> bool:
    content = step_input.previous_step_content or ""
    indicators = ["study", "statistics", "percent", "million"]
    return any(word in content.lower() for word in indicators)

# Define custom function
def format_output(step_input: StepInput) -> StepOutput:
    content = step_input.previous_step_content
    formatted = f"## Final Article\n\n{content}\n\n---\nGenerated by Workflow"
    return StepOutput(content=formatted)

# Build workflow
workflow = Workflow(
    name="Content Creation Pipeline",
    description="Research, verify, and write content",
    steps=[
        Step(name="Research", agent=researcher),
        Condition(
            name="verify_condition",
            evaluator=needs_verification,
            steps=[Step(name="Fact Check", agent=fact_checker)],
        ),
        Step(name="Write", agent=writer),
        Step(name="Format", executor=format_output),
    ],
    db=PostgresDb("postgresql+psycopg://user:pass@localhost/db"),
)

# Run
workflow.print_response(
    "Write about recent AI developments",
    markdown=True,
)
```

---

## Best Practices

### Do's

1. **Use StepInput/StepOutput consistently** for custom functions
2. **Add database persistence** for production workflows
3. **Name your steps** for better logging and debugging
4. **Use Parallel** for independent tasks to improve performance
5. **Set `max_iterations`** on Loops to prevent infinite execution
6. **Use `stop=True`** in StepOutput for early termination when needed

### Don'ts

1. **Don't mix execution styles** - use Workflows for deterministic processes, Teams for dynamic collaboration
2. **Don't skip validation** - use Conditions for quality gates
3. **Don't ignore metrics** - monitor duration and token usage
4. **Don't hardcode paths** - use Router for adaptive workflows

---

## Summary

| Concept | Purpose |
|---------|---------|
| **Workflow** | Deterministic orchestration of steps |
| **Step** | Basic execution unit (agent, team, or function) |
| **Parallel** | Run independent steps concurrently |
| **Condition** | Conditional step execution |
| **Loop** | Iterative execution with exit conditions |
| **Router** | Dynamic path selection |
| **Session** | Execution history tracking |
| **State** | Shared data across all components |
| **WorkflowAgent** | Conversational workflow interface |

---

## Related Documentation

- **Agents:** `docs(new)/agents/01-building-agents.md`
- **Teams:** `docs(new)/teams/01-building-teams.md`
- **Sessions:** `docs(new)/agents/09-storage.md`
- **State Management:** https://docs.agno.com/basics/state/overview

---

*Last Updated: December 2025 | AGNO 2.3.4*
