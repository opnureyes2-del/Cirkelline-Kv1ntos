# Running Workflows

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/running-workflows

---

## Introduction

The `Workflow.run()` function executes the workflow and generates a response, either as a `WorkflowRunOutput` object or a stream of `WorkflowRunOutputEvent` objects.

Many examples use `workflow.print_response()` which is a helper utility to print the response in the terminal. This uses `workflow.run()` under the hood.

---

## Execution Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `run()` | Synchronous execution | `WorkflowRunOutput` or `Iterator[WorkflowRunOutputEvent]` |
| `arun()` | Asynchronous execution | `WorkflowRunOutput` or `AsyncIterator[WorkflowRunOutputEvent]` |
| `print_response()` | Helper that prints to terminal | None |
| `aprint_response()` | Async helper that prints to terminal | None |

---

## Basic Execution

### Non-Streaming (Returns Complete Response)

```python
from agno.workflow import Workflow

workflow = Workflow(
    name="My Workflow",
    steps=[research_agent, writer_agent],
)

# Run and get complete response
response = workflow.run(input="Write about AI trends")

# Access the output
print(response.content)
print(f"Run ID: {response.run_id}")
print(f"Status: {response.status}")
```

### Using print_response() Helper

```python
# Prints formatted output to terminal
workflow.print_response(
    input="Write about AI trends",
    markdown=True,
)
```

---

## Streaming Execution

For real-time output as the workflow executes:

### Synchronous Streaming

```python
from agno.workflow import Workflow

# Enable streaming
response_stream = workflow.run(
    input="Write about AI trends",
    stream=True,
)

# Process events as they arrive
for event in response_stream:
    if event.content:
        print(event.content, end="", flush=True)
```

### With Event Filtering

```python
from agno.run.workflow import WorkflowRunEvent

response_stream = workflow.run(
    input="Write about AI trends",
    stream=True,
    stream_events=True,  # Include detailed events
)

for event in response_stream:
    if event.event == WorkflowRunEvent.workflow_started.value:
        print("Workflow started!")
    elif event.event == WorkflowRunEvent.step_started.value:
        print(f"Step started: {event.step_id}")
    elif event.event == WorkflowRunEvent.step_completed.value:
        print(f"Step completed: {event.step_id}")
    elif event.event == WorkflowRunEvent.workflow_completed.value:
        print("Workflow completed!")
    elif event.content:
        print(event.content, end="")
```

---

## Async Execution

For non-blocking execution in async applications:

### Async Non-Streaming

```python
import asyncio
from agno.workflow import Workflow

async def main():
    response = await workflow.arun(input="Write about AI trends")
    print(response.content)

asyncio.run(main())
```

### Async Streaming

```python
import asyncio
from agno.run.workflow import WorkflowRunEvent

async def main():
    response_stream = workflow.arun(
        input="Write about AI trends",
        stream=True,
        stream_events=True,
    )

    async for event in response_stream:
        if event.event == WorkflowRunEvent.step_started.value:
            print(f"\nStep: {event.step_id}")
        elif event.event == WorkflowRunEvent.step_completed.value:
            print(f" [Done]")
        elif event.content:
            print(event.content, end="")

asyncio.run(main())
```

### Async print_response

```python
import asyncio

async def main():
    await workflow.aprint_response(
        input="Write about AI trends",
        stream=True,
        markdown=True,
    )

asyncio.run(main())
```

---

## Background Execution

For long-running workflows that shouldn't block your main thread:

```python
import asyncio
from agno.workflow import Workflow

async def main():
    # Start workflow in background
    bg_response = await workflow.arun(
        input="Complex research task",
        background=True,  # Non-blocking
    )

    print(f"Started! Run ID: {bg_response.run_id}")
    print(f"Status: {bg_response.status}")

    # Poll for completion
    while True:
        result = workflow.get_run(bg_response.run_id)

        if result is None:
            print("Still waiting...")
            await asyncio.sleep(5)
            continue

        if result.has_completed():
            print("Completed!")
            print(result.content)
            break

        await asyncio.sleep(5)

asyncio.run(main())
```

### Background Execution Key Points

| Requirement | Description |
|-------------|-------------|
| **Async Only** | Use `.arun()` not `.run()` |
| **Polling** | Use `workflow.get_run(run_id)` to check status |
| **Completion Check** | Use `result.has_completed()` |
| **Use Cases** | Large data processing, multi-step research, batch operations |

---

## Run Parameters

Parameters accepted by `run()` and `arun()`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input` | `str` | Required | Input message for the workflow |
| `stream` | `bool` | `False` | Enable streaming output |
| `stream_events` | `bool` | `False` | Include detailed workflow events |
| `user_id` | `str` | `None` | User identifier |
| `session_id` | `str` | `None` | Session identifier |
| `background` | `bool` | `False` | Run as background task (async only) |
| `debug_mode` | `bool` | `False` | Enable debug logging |

---

## WorkflowRunOutput

The response object returned by non-streaming execution:

```python
response = workflow.run(input="Your message")

# Access response data
print(response.content)           # Final output content
print(response.workflow_id)       # Workflow identifier
print(response.workflow_name)     # Workflow name
print(response.run_id)            # Unique run identifier
print(response.session_id)        # Session UUID
print(response.status)            # Run status
print(response.created_at)        # Timestamp
```

### WorkflowRunOutput Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `content` | `Any` | Main output from workflow execution |
| `content_type` | `str` | Type of content (e.g., "str", "json") |
| `workflow_id` | `str` | Unique workflow identifier |
| `workflow_name` | `str` | Name of the workflow |
| `run_id` | `str` | Unique identifier for this run |
| `session_id` | `str` | Session UUID |
| `step_results` | `List[StepOutput]` | All step execution results |
| `step_executor_runs` | `List` | Agent/team responses |
| `events` | `List[WorkflowRunOutputEvent]` | Captured events |
| `metrics` | `WorkflowMetrics` | Execution metrics |
| `metadata` | `Dict` | Additional metadata |
| `created_at` | `int` | Unix timestamp |
| `status` | `RunStatus` | Current run status |
| `images` | `List[Image]` | Generated images |
| `videos` | `List[Video]` | Generated videos |
| `audio` | `List[Audio]` | Generated audio |

---

## Workflow Events

Events emitted during streaming execution:

| Event | Description |
|-------|-------------|
| `workflow_started` | Workflow execution began |
| `workflow_completed` | Workflow execution finished |
| `step_started` | A step began execution |
| `step_completed` | A step finished execution |
| `condition_execution_started` | Condition evaluation began |
| `condition_execution_completed` | Condition evaluation finished |
| `loop_iteration_started` | Loop iteration began |
| `loop_iteration_completed` | Loop iteration finished |
| `parallel_execution_started` | Parallel execution began |
| `parallel_execution_completed` | Parallel execution finished |

### Processing Events

```python
from agno.run.workflow import WorkflowRunEvent

async def process_workflow():
    response_stream = workflow.arun(
        input="Your message",
        stream=True,
        stream_events=True,
    )

    async for event in response_stream:
        match event.event:
            case WorkflowRunEvent.workflow_started.value:
                print(f"Started workflow: {event.workflow_name}")

            case WorkflowRunEvent.step_started.value:
                print(f"  Step: {event.step_id}")

            case WorkflowRunEvent.step_completed.value:
                print(f"  Completed: {event.step_id}")

            case WorkflowRunEvent.workflow_completed.value:
                print(f"Workflow finished!")

            case _:
                if event.content:
                    print(event.content, end="")
```

---

## Session Management

### Using Sessions

```python
# First run - creates new session
response1 = workflow.run(
    input="Research AI trends",
    session_id="my-session-123",
    user_id="user-456",
)

# Second run - continues same session
response2 = workflow.run(
    input="Now write about the findings",
    session_id="my-session-123",
    user_id="user-456",
)
```

### Retrieving Session Data

```python
# Get session by ID
session = workflow.get_session(session_id="my-session-123")

# Get session state
state = workflow.get_session_state(session_id="my-session-123")

# Get session metrics
metrics = workflow.get_session_metrics(session_id="my-session-123")
```

---

## Retrieving Run Output

Access run results after execution:

```python
# Get specific run by ID
run_output = workflow.get_run(run_id="run-xyz-123")

# Get the last run output
last_output = workflow.get_last_run_output()
```

---

## Debug Mode

Enable detailed logging for troubleshooting:

```python
# Enable for a specific run
response = workflow.run(
    input="Your message",
    debug_mode=True,
)

# See detailed execution logs
```

---

## CLI Application

Run workflows interactively from the command line:

```python
# Start CLI mode
workflow.cli_app(
    session_id="cli-session",
    user="User",
    emoji="🤖",
    stream=True,
    show_step_details=True,
)
```

This starts an interactive session where you can:
- Type messages and see workflow responses
- Maintain conversation history
- See step-by-step execution details

---

## Complete Example

```python
import asyncio
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.db.postgres import PostgresDb
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.run.workflow import WorkflowRunEvent

# Define agents
researcher = Agent(
    name="Researcher",
    tools=[DuckDuckGoTools()],
    instructions="Research thoroughly.",
)

writer = Agent(
    name="Writer",
    instructions="Write engaging content.",
)

# Build workflow
workflow = Workflow(
    name="Content Pipeline",
    steps=[
        Step(name="Research", agent=researcher),
        Step(name="Write", agent=writer),
    ],
    db=PostgresDb("postgresql+psycopg://user:pass@localhost/db"),
)

async def main():
    print("=== Async Streaming Example ===\n")

    response_stream = workflow.arun(
        input="Latest developments in quantum computing",
        stream=True,
        stream_events=True,
        session_id="demo-session",
        user_id="user-123",
    )

    async for event in response_stream:
        if event.event == WorkflowRunEvent.step_started.value:
            print(f"\n[{event.step_id}] Starting...")
        elif event.event == WorkflowRunEvent.step_completed.value:
            print(f"\n[{event.step_id}] Done!")
        elif event.content:
            print(event.content, end="", flush=True)

    print("\n\n=== Execution Complete ===")

    # Get session metrics
    metrics = workflow.get_session_metrics(session_id="demo-session")
    print(f"Total duration: {metrics.duration}s")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Best Practices

### Do's

1. **Use async for production:** Better performance and non-blocking
2. **Enable streaming for UX:** Users see progress in real-time
3. **Use session IDs:** Maintain context across runs
4. **Check run status:** For background execution, poll until complete
5. **Enable debug_mode:** When troubleshooting issues

### Don'ts

1. **Don't block on long workflows:** Use `background=True` for heavy tasks
2. **Don't ignore errors:** Check `response.status` and handle failures
3. **Don't forget user_id:** Required for user-specific sessions
4. **Don't mix sync/async:** Stick to one pattern per application

---

## Summary

| Method | Use Case |
|--------|----------|
| `run()` | Simple synchronous execution |
| `run(stream=True)` | Real-time output |
| `arun()` | Non-blocking async execution |
| `arun(background=True)` | Long-running background tasks |
| `print_response()` | Quick terminal output |
| `cli_app()` | Interactive CLI mode |

---

## Related Documentation

- **Building Workflows:** `docs(new)/workflows/02-building-workflows.md`
- **Workflow Patterns:** `docs(new)/workflows/04-basic-patterns.md`
- **Background Execution:** https://docs.agno.com/basics/workflows/background-execution

---

*Last Updated: December 2025 | AGNO 2.3.4*
