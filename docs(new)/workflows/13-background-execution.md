# Background Execution

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/background-execution

---

## Introduction

Background execution allows workflows to run asynchronously without blocking your application. This is useful for:

- Long-running workflows (research, data processing)
- Batch operations
- Non-blocking user experiences
- Queue-based processing

---

## Core Concept

```python
import asyncio
from agno.workflow import Workflow

async def main():
    # Start workflow in background
    response = await workflow.arun(
        input="Long running task",
        background=True,  # Non-blocking
    )

    print(f"Started! Run ID: {response.run_id}")

    # Poll for completion
    while True:
        result = workflow.get_run(response.run_id)
        if result and result.has_completed():
            print(result.content)
            break
        await asyncio.sleep(5)

asyncio.run(main())
```

---

## How It Works

1. Call `arun()` with `background=True`
2. Workflow starts in background, returns immediately
3. Get `run_id` from initial response
4. Poll using `get_run(run_id)` to check status
5. When complete, get final result

```
arun(background=True)
        ↓
Immediate return with run_id
        ↓
Workflow runs in background
        ↓
Poll with get_run(run_id)
        ↓
Completed → get result
```

---

## Basic Example

```python
import asyncio
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.db.sqlite import SqliteDb

# Define agents for long-running workflow
researcher = Agent(
    name="Deep Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Conduct thorough, comprehensive research.",
)

analyst = Agent(
    name="Analyst",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze findings and create detailed reports.",
)

# Long-running workflow
deep_research_workflow = Workflow(
    name="Deep Research Pipeline",
    description="Comprehensive research and analysis",
    db=SqliteDb(db_file="tmp/workflow.db"),
    steps=[
        Step(name="Research Phase 1", agent=researcher),
        Step(name="Research Phase 2", agent=researcher),
        Step(name="Analysis", agent=analyst),
    ],
)


async def main():
    print("Starting background workflow...")

    # Start in background
    bg_response = await deep_research_workflow.arun(
        input="Comprehensive analysis of renewable energy market trends",
        background=True,
    )

    print(f"Workflow started!")
    print(f"Run ID: {bg_response.run_id}")
    print(f"Status: {bg_response.status}")

    # Poll for completion
    poll_count = 0
    while True:
        poll_count += 1
        result = deep_research_workflow.get_run(bg_response.run_id)

        if result is None:
            print(f"[{poll_count}] Still initializing...")
            await asyncio.sleep(5)
            continue

        if result.has_completed():
            print(f"\n[{poll_count}] Workflow completed!")
            print(f"\nFinal Result:\n{result.content}")
            break

        print(f"[{poll_count}] Status: {result.status} - Still running...")
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Key Requirements

| Requirement | Description |
|-------------|-------------|
| **Async Only** | Must use `.arun()` not `.run()` |
| **Database Required** | Workflow needs `db` for state persistence |
| **Polling** | Use `get_run(run_id)` to check status |
| **Completion Check** | Use `result.has_completed()` |

---

## Response Object

Initial background response:

```python
bg_response = await workflow.arun(input="Task", background=True)

# Available immediately
print(bg_response.run_id)       # Unique run identifier
print(bg_response.workflow_id)  # Workflow identifier
print(bg_response.status)       # Current status
print(bg_response.created_at)   # Start timestamp
```

### Run Status Values

| Status | Description |
|--------|-------------|
| `pending` | Workflow queued |
| `running` | Workflow executing |
| `completed` | Successfully finished |
| `failed` | Error occurred |
| `cancelled` | Manually cancelled |

---

## Polling Patterns

### Simple Polling

```python
async def simple_poll(workflow, run_id, interval=5, timeout=300):
    """Poll until complete or timeout"""
    start_time = asyncio.get_event_loop().time()

    while True:
        elapsed = asyncio.get_event_loop().time() - start_time

        if elapsed > timeout:
            raise TimeoutError(f"Workflow did not complete in {timeout}s")

        result = workflow.get_run(run_id)

        if result and result.has_completed():
            return result

        await asyncio.sleep(interval)
```

### Exponential Backoff

```python
async def poll_with_backoff(workflow, run_id, max_wait=60):
    """Poll with exponential backoff"""
    wait_time = 1  # Start with 1 second

    while True:
        result = workflow.get_run(run_id)

        if result and result.has_completed():
            return result

        # Exponential backoff with cap
        wait_time = min(wait_time * 2, max_wait)
        print(f"Waiting {wait_time}s before next check...")
        await asyncio.sleep(wait_time)
```

### With Progress Callback

```python
async def poll_with_callback(workflow, run_id, on_progress):
    """Poll with progress callback"""
    poll_count = 0

    while True:
        poll_count += 1
        result = workflow.get_run(run_id)

        # Call progress callback
        on_progress(poll_count, result)

        if result and result.has_completed():
            return result

        await asyncio.sleep(5)


# Usage
def progress_handler(count, result):
    status = result.status if result else "initializing"
    print(f"Poll #{count}: {status}")

result = await poll_with_callback(
    workflow,
    run_id,
    on_progress=progress_handler,
)
```

---

## Multiple Background Workflows

Run multiple workflows concurrently:

```python
import asyncio
from agno.workflow import Workflow

async def run_multiple_workflows():
    # Start multiple workflows in background
    responses = await asyncio.gather(
        workflow1.arun(input="Task 1", background=True),
        workflow2.arun(input="Task 2", background=True),
        workflow3.arun(input="Task 3", background=True),
    )

    # Collect run IDs
    run_ids = [(r.run_id, workflow) for r, workflow in zip(
        responses,
        [workflow1, workflow2, workflow3]
    )]

    print(f"Started {len(run_ids)} workflows")

    # Poll all until complete
    results = {}
    pending = set(r[0] for r in run_ids)

    while pending:
        for run_id, workflow in run_ids:
            if run_id not in pending:
                continue

            result = workflow.get_run(run_id)

            if result and result.has_completed():
                results[run_id] = result
                pending.remove(run_id)
                print(f"Workflow {run_id} completed!")

        if pending:
            await asyncio.sleep(5)

    return results


asyncio.run(run_multiple_workflows())
```

---

## Error Handling

Handle failures in background workflows:

```python
async def safe_background_run(workflow, input_text):
    """Run with error handling"""
    try:
        bg_response = await workflow.arun(
            input=input_text,
            background=True,
        )

        # Poll for result
        while True:
            result = workflow.get_run(bg_response.run_id)

            if result is None:
                await asyncio.sleep(5)
                continue

            if result.has_completed():
                # Check for failure
                if result.status == "failed":
                    print(f"Workflow failed: {result.error}")
                    return None
                return result

            if result.status == "cancelled":
                print("Workflow was cancelled")
                return None

            await asyncio.sleep(5)

    except Exception as e:
        print(f"Error: {e}")
        return None
```

---

## Database Requirement

Background execution requires a database:

```python
from agno.db.sqlite import SqliteDb
from agno.db.postgres import PostgresDb

# SQLite for development
workflow = Workflow(
    name="Background Workflow",
    db=SqliteDb(db_file="tmp/workflow.db"),
    steps=[...],
)

# PostgreSQL for production
workflow = Workflow(
    name="Background Workflow",
    db=PostgresDb("postgresql+psycopg://user:pass@localhost/db"),
    steps=[...],
)
```

Without a database, background execution will fail because there's no way to persist the run state.

---

## FastAPI Integration

Use in a web API:

```python
from fastapi import FastAPI, BackgroundTasks
from agno.workflow import Workflow
from agno.db.postgres import PostgresDb
import asyncio

app = FastAPI()

# Workflow with database
workflow = Workflow(
    name="Processing Pipeline",
    db=PostgresDb("postgresql+psycopg://user:pass@localhost/db"),
    steps=[...],
)


@app.post("/process")
async def start_processing(input_text: str):
    """Start a background workflow"""
    response = await workflow.arun(
        input=input_text,
        background=True,
    )

    return {
        "run_id": response.run_id,
        "status": response.status,
        "message": "Processing started",
    }


@app.get("/status/{run_id}")
async def check_status(run_id: str):
    """Check workflow status"""
    result = workflow.get_run(run_id)

    if result is None:
        return {"status": "not_found"}

    return {
        "run_id": run_id,
        "status": result.status,
        "completed": result.has_completed(),
        "content": result.content if result.has_completed() else None,
    }


@app.get("/result/{run_id}")
async def get_result(run_id: str):
    """Get completed workflow result"""
    result = workflow.get_run(run_id)

    if result is None:
        return {"error": "Run not found"}

    if not result.has_completed():
        return {"error": "Still processing", "status": result.status}

    return {
        "run_id": run_id,
        "status": result.status,
        "content": result.content,
        "created_at": result.created_at,
    }
```

---

## Webhook Pattern

Notify when complete instead of polling:

```python
import httpx
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput

# Define a notification step
async def notify_completion(step_input: StepInput) -> StepOutput:
    """Send webhook when workflow completes"""
    content = step_input.previous_step_content or ""
    additional = step_input.additional_data or {}

    webhook_url = additional.get("webhook_url")
    run_id = additional.get("run_id")

    if webhook_url:
        async with httpx.AsyncClient() as client:
            await client.post(
                webhook_url,
                json={
                    "run_id": run_id,
                    "status": "completed",
                    "content": content[:1000],  # Truncate for webhook
                },
            )

    return StepOutput(content=content)


# Workflow with notification
workflow = Workflow(
    name="Notifying Workflow",
    db=db,
    steps=[
        Step(name="Research", agent=researcher),
        Step(name="Analysis", agent=analyst),
        Step(name="Notify", executor=notify_completion),
    ],
)


async def start_with_webhook(input_text: str, webhook_url: str):
    """Start workflow with webhook notification"""
    response = await workflow.arun(
        input=input_text,
        background=True,
        additional_data={
            "webhook_url": webhook_url,
            "run_id": "will-be-replaced",  # Gets actual run_id
        },
    )

    return response.run_id
```

---

## Complete Example

```python
import asyncio
from agno.agent import Agent
from agno.workflow import Workflow, Step, Parallel
from agno.model.google import Gemini
from agno.db.sqlite import SqliteDb
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.exa import ExaTools

# Database
db = SqliteDb(db_file="tmp/background_demo.db")

# Define agents
web_researcher = Agent(
    name="Web Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Research current events and news.",
)

deep_researcher = Agent(
    name="Deep Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[ExaTools()],
    instructions="Find authoritative, in-depth sources.",
)

analyst = Agent(
    name="Analyst",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze and synthesize research findings.",
)

reporter = Agent(
    name="Reporter",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write comprehensive, well-structured reports.",
)

# Complex workflow for background execution
comprehensive_research = Workflow(
    name="Comprehensive Research",
    description="Multi-source research with analysis and reporting",
    db=db,
    steps=[
        Parallel(
            Step(name="Web Research", agent=web_researcher),
            Step(name="Deep Research", agent=deep_researcher),
            name="Research Phase",
        ),
        Step(name="Analysis", agent=analyst),
        Step(name="Report", agent=reporter),
    ],
)


async def main():
    print("=" * 50)
    print("Background Execution Demo")
    print("=" * 50)

    # Start background workflow
    print("\n1. Starting background workflow...")
    bg_response = await comprehensive_research.arun(
        input="Analyze the current state and future of quantum computing",
        background=True,
    )

    run_id = bg_response.run_id
    print(f"   Run ID: {run_id}")
    print(f"   Status: {bg_response.status}")

    # Do other work while waiting
    print("\n2. Doing other work while workflow runs...")
    for i in range(3):
        print(f"   Working on other task {i + 1}...")
        await asyncio.sleep(2)

    # Poll for completion
    print("\n3. Polling for completion...")
    poll_count = 0
    max_polls = 60  # 5 minutes max

    while poll_count < max_polls:
        poll_count += 1
        result = comprehensive_research.get_run(run_id)

        if result is None:
            print(f"   [{poll_count}] Initializing...")
            await asyncio.sleep(5)
            continue

        status = result.status
        print(f"   [{poll_count}] Status: {status}")

        if result.has_completed():
            print("\n4. Workflow completed!")
            print("=" * 50)
            print("RESULT:")
            print("=" * 50)
            print(result.content)
            break

        if status == "failed":
            print(f"\n4. Workflow failed!")
            print(f"   Error: {result.error}")
            break

        await asyncio.sleep(5)
    else:
        print("\n4. Timeout - workflow took too long")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Best Practices

### Do's

1. **Always use database** - Required for state persistence
2. **Handle timeouts** - Don't poll forever
3. **Use exponential backoff** - Reduce server load
4. **Store run_id** - Needed to retrieve results later
5. **Handle failures** - Check for failed status

### Don'ts

1. **Don't use `run()`** - Only `arun()` supports background
2. **Don't forget polling** - Results don't appear automatically
3. **Don't poll too frequently** - Use reasonable intervals
4. **Don't ignore errors** - Check status for failures

---

## Summary

| Concept | Description |
|---------|-------------|
| `background=True` | Start workflow in background |
| `get_run(run_id)` | Retrieve run status/result |
| `has_completed()` | Check if workflow finished |
| **Database Required** | Needed for state persistence |
| **Polling** | Check status until complete |

---

## Related Documentation

- **Running Workflows:** `docs(new)/workflows/03-running-workflows.md`
- **Workflow Sessions:** `docs(new)/workflows/01-overview.md#workflow-sessions`

---

*Last Updated: December 2025 | AGNO 2.3.4*
