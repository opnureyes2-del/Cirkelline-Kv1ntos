# Structured I/O, Events, and Cancellation

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/usage

---

## Introduction

This documentation covers advanced workflow features:

- **Structured I/O** - Type-safe data flow with Pydantic models
- **Input Schema Validation** - Validate workflow inputs before execution
- **Event Storage** - Store and filter workflow events
- **Workflow Cancellation** - Gracefully cancel running workflows

---

## Structured I/O at Step Level

Use Pydantic models to enforce type-safe data flow between steps:

```python
from typing import List
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from pydantic import BaseModel, Field


# Define structured models for each step
class ResearchFindings(BaseModel):
    """Structured research output"""
    topic: str = Field(description="The research topic")
    key_insights: List[str] = Field(
        description="Main insights discovered",
        min_items=3,
    )
    trending_technologies: List[str] = Field(
        description="Technologies that are trending",
        min_items=2,
    )
    market_impact: str = Field(description="Market impact analysis")
    confidence_score: float = Field(
        description="Confidence in findings (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )


class ContentStrategy(BaseModel):
    """Structured content strategy"""
    target_audience: str = Field(description="Primary target audience")
    content_pillars: List[str] = Field(
        description="Main content themes",
        min_items=3,
    )
    key_messages: List[str] = Field(
        description="Core messages to communicate",
        min_items=3,
    )
    hashtags: List[str] = Field(
        description="Recommended hashtags",
        min_items=5,
    )


class FinalContentPlan(BaseModel):
    """Final content plan output"""
    campaign_name: str = Field(description="Campaign name")
    content_calendar: List[str] = Field(
        description="Specific content pieces",
        min_items=6,
    )
    success_metrics: List[str] = Field(
        description="Success measurement",
        min_items=3,
    )
    timeline: str = Field(description="Implementation timeline")


# Agents with output_schema
research_agent = Agent(
    name="Research Specialist",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    output_schema=ResearchFindings,  # Structured output
    instructions=[
        "Research the topic thoroughly.",
        "Structure response according to ResearchFindings model.",
    ],
)

strategy_agent = Agent(
    name="Strategy Expert",
    model=Gemini(id="gemini-2.5-flash"),
    output_schema=ContentStrategy,  # Structured output
    instructions=[
        "Create content strategy from research findings.",
        "Structure response according to ContentStrategy model.",
    ],
)

planning_agent = Agent(
    name="Planning Specialist",
    model=Gemini(id="gemini-2.5-flash"),
    output_schema=FinalContentPlan,  # Structured output
    instructions=[
        "Create detailed implementation plan.",
        "Structure response according to FinalContentPlan model.",
    ],
)

# Workflow with structured steps
structured_workflow = Workflow(
    name="Structured Content Pipeline",
    description="Type-safe content creation workflow",
    steps=[
        Step(name="Research", agent=research_agent),
        Step(name="Strategy", agent=strategy_agent),
        Step(name="Planning", agent=planning_agent),
    ],
)

if __name__ == "__main__":
    structured_workflow.print_response(
        input="AI developments in healthcare",
    )
```

---

## Structured I/O Flow

```
User Input (string)
    ↓
Research Agent
    ↓
ResearchFindings (Pydantic model)
    ↓
Strategy Agent
    ↓
ContentStrategy (Pydantic model)
    ↓
Planning Agent
    ↓
FinalContentPlan (Pydantic model)
```

**Benefits:**
- Type safety between steps
- Automatic validation
- Clear data contracts
- IDE autocomplete support

---

## Workflow Input Schema

Validate workflow inputs before execution:

```python
from typing import List
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.team import Team
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.db.sqlite import SqliteDb
from pydantic import BaseModel, Field


class ResearchTopic(BaseModel):
    """Workflow input schema"""
    topic: str = Field(description="Research topic")
    focus_areas: List[str] = Field(description="Specific focus areas")
    target_audience: str = Field(description="Target audience")
    sources_required: int = Field(
        description="Number of sources needed",
        default=5,
    )


# Agents
web_researcher = Agent(
    name="Web Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Research topics from the web.",
)

content_planner = Agent(
    name="Content Planner",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Plan content schedule for 4 weeks, 3 posts per week.",
)

# Workflow with input validation
content_workflow = Workflow(
    name="Content Creation Workflow",
    description="Validates input before processing",
    db=SqliteDb(db_file="tmp/workflow.db"),
    input_schema=ResearchTopic,  # Input validation!
    steps=[
        Step(name="Research", agent=web_researcher),
        Step(name="Planning", agent=content_planner),
    ],
)

if __name__ == "__main__":
    # Method 1: Pydantic model input
    research_topic = ResearchTopic(
        topic="AI trends in 2025",
        focus_areas=["Machine Learning", "NLP", "Computer Vision"],
        target_audience="Tech professionals",
        sources_required=8,
    )

    content_workflow.print_response(
        input=research_topic,
        markdown=True,
    )

    # Method 2: Dictionary input (auto-validated)
    content_workflow.print_response(
        input={
            "topic": "Quantum Computing",
            "focus_areas": ["Hardware", "Algorithms"],
            "target_audience": "Researchers",
            "sources_required": 10,
        },
        markdown=True,
    )
```

---

## Input Validation Behavior

```python
# Valid inputs
workflow.run(input=ResearchTopic(...))  # ✓ Pydantic model
workflow.run(input={"topic": "...", ...})  # ✓ Dict matching schema

# Invalid inputs (will raise ValidationError)
workflow.run(input="Just a string")  # ✗ Wrong type
workflow.run(input={"topic": "..."})  # ✗ Missing required fields
workflow.run(input={"topic": 123, ...})  # ✗ Wrong field type
```

| Input Type | Behavior |
|------------|----------|
| Matching Pydantic model | Accepted directly |
| Dict matching schema | Validated and converted |
| Wrong model type | ValidationError |
| Missing required fields | ValidationError |
| Wrong field types | ValidationError |

---

## Event Storage

Store workflow events for auditing and debugging:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.parallel import Parallel
from agno.run.workflow import WorkflowRunEvent
from agno.run.agent import RunEvent
from agno.model.google import Gemini
from agno.tools.hackernews import HackerNewsTools
from agno.db.sqlite import SqliteDb

news_agent = Agent(
    name="News Agent",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[HackerNewsTools()],
    instructions="Research tech news and summarize.",
)

analysis_agent = Agent(
    name="Analysis Agent",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze and summarize findings.",
)

# Workflow with event storage
workflow = Workflow(
    name="Event Storage Workflow",
    description="Stores events for auditing",
    db=SqliteDb(
        db_file="tmp/workflow.db",
        session_table="workflow_sessions",
    ),
    steps=[
        Parallel(
            Step(name="News Research", agent=news_agent),
            Step(name="Analysis", agent=analysis_agent),
            name="Research Phase",
        ),
    ],
    store_events=True,  # Enable event storage
    events_to_skip=[
        # Skip verbose events
        WorkflowRunEvent.step_started,
        WorkflowRunEvent.workflow_completed,
        RunEvent.run_content,
        RunEvent.run_started,
        RunEvent.run_completed,
    ],
)

if __name__ == "__main__":
    # Run workflow
    workflow.print_response("Research AI trends")

    # Access stored events
    run_output = workflow.get_last_run_output()

    if run_output and run_output.events:
        print("\n=== Stored Events ===")
        for event in run_output.events:
            print(f"Event: {event.event}")
            if hasattr(event, 'step_id'):
                print(f"  Step: {event.step_id}")
```

---

## Event Types

### WorkflowRunEvent Types

| Event | Description |
|-------|-------------|
| `workflow_started` | Workflow execution began |
| `workflow_completed` | Workflow finished successfully |
| `workflow_cancelled` | Workflow was cancelled |
| `step_started` | A step began execution |
| `step_completed` | A step finished |
| `step_output` | Step produced output |

### RunEvent Types (Agent-level)

| Event | Description |
|-------|-------------|
| `run_started` | Agent run began |
| `run_completed` | Agent run finished |
| `run_content` | Agent produced content |
| `run_cancelled` | Agent run cancelled |
| `tool_call_started` | Tool call began |
| `tool_call_completed` | Tool call finished |

---

## Selective Event Storage

```python
# Store all events (verbose)
workflow = Workflow(
    store_events=True,
    # events_to_skip not specified = store everything
)

# Store only important events
workflow = Workflow(
    store_events=True,
    events_to_skip=[
        WorkflowRunEvent.step_started,  # Skip step start
        RunEvent.run_content,           # Skip content chunks
        RunEvent.run_started,           # Skip run start
        RunEvent.run_completed,         # Skip run complete
    ],
)

# Result: Only stores step_completed, tool events, etc.
```

---

## Workflow Cancellation

Cancel running workflows gracefully:

```python
import asyncio
import threading
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.run.workflow import WorkflowRunEvent
from agno.run.agent import RunEvent
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.db.sqlite import SqliteDb

researcher = Agent(
    name="Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Research topics thoroughly with multiple sources.",
)

writer = Agent(
    name="Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write comprehensive reports.",
)

workflow = Workflow(
    name="Cancellable Workflow",
    description="Demonstrates graceful cancellation",
    db=SqliteDb(db_file="tmp/workflow.db"),
    steps=[
        Step(name="Research", agent=researcher),
        Step(name="Write", agent=writer),
    ],
)


def run_workflow():
    """Run workflow with cancellation detection"""
    run_id_container = {}
    partial_content = []

    for chunk in workflow.run(
        input="Research comprehensive AI developments",
        stream=True,
    ):
        # Capture run_id when available
        if "run_id" not in run_id_container and chunk.run_id:
            run_id_container["run_id"] = chunk.run_id
            print(f"Started run: {chunk.run_id}")

        # Detect cancellation
        if chunk.event == RunEvent.run_cancelled:
            print("\n⚠️ Run cancelled!")
            break

        if chunk.event == WorkflowRunEvent.workflow_cancelled:
            print("\n⚠️ Workflow cancelled!")
            break

        # Collect content
        if hasattr(chunk, 'content') and chunk.content:
            partial_content.append(chunk.content)
            print(chunk.content, end="", flush=True)

    return {
        "run_id": run_id_container.get("run_id"),
        "partial_content": "".join(partial_content),
    }


def cancel_after_delay(delay_seconds: int):
    """Cancel workflow after delay"""
    import time
    time.sleep(delay_seconds)

    # Get current run_id and cancel
    run_output = workflow.get_last_run_output()
    if run_output and run_output.run_id:
        print(f"\n🛑 Cancelling run: {run_output.run_id}")
        workflow.cancel_run(run_output.run_id)


if __name__ == "__main__":
    # Run workflow in one thread
    workflow_thread = threading.Thread(target=run_workflow)

    # Cancel after 8 seconds in another thread
    cancel_thread = threading.Thread(
        target=cancel_after_delay,
        args=(8,),
    )

    workflow_thread.start()
    cancel_thread.start()

    workflow_thread.join()
    cancel_thread.join()

    print("\n=== Execution Complete ===")
```

---

## Async Cancellation

```python
import asyncio
from agno.workflow import Workflow

async def run_with_timeout(workflow: Workflow, input_text: str, timeout: int):
    """Run workflow with timeout-based cancellation"""
    run_id = None

    async def execute():
        nonlocal run_id
        async for chunk in workflow.arun(input=input_text, stream=True):
            if run_id is None and chunk.run_id:
                run_id = chunk.run_id

            if hasattr(chunk, 'content') and chunk.content:
                print(chunk.content, end="", flush=True)

    try:
        await asyncio.wait_for(execute(), timeout=timeout)
    except asyncio.TimeoutError:
        if run_id:
            print(f"\n⏰ Timeout! Cancelling {run_id}")
            workflow.cancel_run(run_id)


async def main():
    await run_with_timeout(
        workflow,
        "Comprehensive research on quantum computing",
        timeout=30,  # 30 second timeout
    )


asyncio.run(main())
```

---

## Cancellation Flow

```
Workflow Running
    ↓
cancel_run(run_id) called
    ↓
Current step completes (graceful)
    ↓
WorkflowRunEvent.workflow_cancelled emitted
    ↓
Remaining steps skipped
    ↓
Partial results available
```

**Key Points:**
- Cancellation is graceful - current step completes
- Partial results are preserved
- Events indicate cancellation occurred
- Database stores incomplete run state

---

## Combined Example

Complete example with all features:

```python
import asyncio
from typing import List
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.run.workflow import WorkflowRunEvent
from agno.run.agent import RunEvent
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.db.postgres import PostgresDb
from pydantic import BaseModel, Field


# Input schema
class ResearchRequest(BaseModel):
    """Validated workflow input"""
    topic: str = Field(description="Research topic")
    depth: str = Field(description="quick or deep")
    max_sources: int = Field(default=5)


# Output schemas
class ResearchOutput(BaseModel):
    """Structured research output"""
    findings: List[str] = Field(min_items=3)
    sources: List[str]
    confidence: float = Field(ge=0.0, le=1.0)


class ReportOutput(BaseModel):
    """Structured report output"""
    title: str
    summary: str
    sections: List[str]
    recommendations: List[str]


# Agents with structured output
researcher = Agent(
    name="Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    output_schema=ResearchOutput,
    instructions="Research with structured output.",
)

reporter = Agent(
    name="Reporter",
    model=Gemini(id="gemini-2.5-flash"),
    output_schema=ReportOutput,
    instructions="Create structured reports.",
)

# Database
db = PostgresDb("postgresql+psycopg://user:pass@localhost/db")

# Full-featured workflow
advanced_workflow = Workflow(
    name="Advanced Research Workflow",
    description="Demonstrates all advanced features",
    db=db,
    input_schema=ResearchRequest,  # Input validation
    store_events=True,             # Event storage
    events_to_skip=[               # Selective storage
        RunEvent.run_content,
        RunEvent.run_started,
    ],
    steps=[
        Step(name="Research", agent=researcher),
        Step(name="Report", agent=reporter),
    ],
)


async def main():
    # Valid structured input
    request = ResearchRequest(
        topic="AI in Healthcare",
        depth="deep",
        max_sources=10,
    )

    run_id = None

    # Streaming with cancellation support
    async for chunk in advanced_workflow.arun(
        input=request,
        stream=True,
    ):
        if run_id is None and chunk.run_id:
            run_id = chunk.run_id

        # Check for cancellation
        if chunk.event == WorkflowRunEvent.workflow_cancelled:
            print("\n⚠️ Cancelled!")
            break

        if hasattr(chunk, 'content') and chunk.content:
            print(chunk.content, end="", flush=True)

    # Access stored events
    run_output = advanced_workflow.get_last_run_output()
    if run_output and run_output.events:
        print(f"\n\n=== Stored {len(run_output.events)} events ===")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Summary

| Feature | Parameter/Method | Purpose |
|---------|------------------|---------|
| **Step Output Schema** | `agent.output_schema` | Type-safe step output |
| **Input Validation** | `workflow.input_schema` | Validate workflow input |
| **Event Storage** | `store_events=True` | Persist events to DB |
| **Event Filtering** | `events_to_skip=[...]` | Skip verbose events |
| **Cancellation** | `workflow.cancel_run(id)` | Gracefully stop workflow |
| **Get Last Run** | `workflow.get_last_run_output()` | Access run results |

---

## Best Practices

### Do's

1. **Define clear schemas** - Use descriptive Field descriptions
2. **Validate at boundaries** - Use input_schema for external input
3. **Filter events wisely** - Skip only truly unnecessary events
4. **Handle cancellation** - Check for cancellation events in streaming
5. **Store important events** - Keep step_completed, tool events

### Don'ts

1. **Don't over-constrain** - Allow reasonable flexibility in schemas
2. **Don't skip all events** - Keep enough for debugging
3. **Don't ignore cancellation** - Always check for cancellation events
4. **Don't forget cleanup** - Handle partial results properly

---

## Related Documentation

- **Additional Data:** `docs(new)/workflows/08-additional-data.md`
- **Previous Steps Access:** `docs(new)/workflows/10-access-previous-steps.md`
- **Early Stop:** `docs(new)/workflows/11-early-stop.md`
- **Background Execution:** `docs(new)/workflows/13-background-execution.md`

---

*Last Updated: December 2025 | AGNO 2.3.4*
