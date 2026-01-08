# AGNO Run Cancellation Documentation

> **Source:** https://docs.agno.com/basics/agents/usage/cancel-a-run
> **Related:** https://docs.agno.com/execution-control/run-cancellation/overview
> **Last Updated:** 2025-11-29

---

## Overview

Run cancellation allows you to stop agent, team, or workflow executions mid-run. This is essential for:
- User-initiated stops ("Cancel" button)
- Timeout enforcement
- Cost control
- Error recovery
- Resource management

---

## How It Works

### Cancellation Flow

```
1. Start run → Get run_id from first event
2. Store run_id → Track active runs per user/session
3. Cancel request → Call cancel_run(run_id)
4. Graceful stop → Current step finishes, then stops
5. Event emitted → RunCancelledEvent sent to stream
6. Cleanup → Handle partial content, update UI
```

### Key Behavior

| Aspect | Description |
|--------|-------------|
| **Graceful** | Finishes current step before stopping |
| **Not instant** | May take a moment to fully stop |
| **Partial content preserved** | Content generated before cancel is kept |
| **Event-based** | Cancellation emits an event you can handle |
| **Thread-safe** | Can be called from another thread/process |

---

## Basic Usage

### Agent Cancellation

```python
from agno.agent import Agent
from agno.run.agent import RunEvent
from agno.run.base import RunStatus

agent = Agent(
    model=model,
    name="MyAgent"
)

# Track run_id
run_id = None

for chunk in agent.run("Write a long story...", stream=True):
    # Capture run_id from first event
    if chunk.run_id and not run_id:
        run_id = chunk.run_id

    # Handle cancellation event
    if chunk.event == RunEvent.run_cancelled:
        print(f"Run {chunk.run_id} was cancelled")
        break

    # Normal content
    if chunk.event == RunEvent.run_content:
        print(chunk.content, end="")

# To cancel from elsewhere:
success = agent.cancel_run(run_id)
```

### Team Cancellation

```python
from agno.team import Team
from agno.run.team import TeamRunEvent

team = Team(
    members=[agent1, agent2],
    model=model
)

for chunk in team.run("Research this topic...", stream=True):
    if chunk.run_id and not run_id:
        run_id = chunk.run_id

    # Team-specific cancellation event
    if chunk.event == TeamRunEvent.run_cancelled:
        print("Team run cancelled")
        break

# Cancel
success = team.cancel_run(run_id)
```

### Workflow Cancellation

```python
from agno.workflow.workflow import Workflow
from agno.run.workflow import WorkflowRunEvent

workflow = Workflow(
    steps=[step1, step2, step3]
)

for chunk in workflow.run("Process this...", stream=True):
    if chunk.run_id and not run_id:
        run_id = chunk.run_id

    if chunk.event == WorkflowRunEvent.workflow_cancelled:
        print("Workflow cancelled")
        break

# Cancel
success = workflow.cancel_run(run_id)
```

---

## Events Reference

| Type | Event | Description |
|------|-------|-------------|
| Agent | `RunEvent.run_cancelled` | Agent run was cancelled |
| Team | `TeamRunEvent.run_cancelled` | Team run was cancelled |
| Workflow | `WorkflowRunEvent.workflow_cancelled` | Workflow was cancelled |

### Non-Streaming Response

For non-streaming runs, check the status:

```python
response = agent.run("Do something", stream=False)

if response.status == RunStatus.cancelled:
    print("Run was cancelled")
```

---

## Threading Pattern

The standard pattern uses threads to run the agent and cancel separately:

```python
import threading
import time

def run_agent(agent, run_id_container, message):
    """Run agent in a thread, store run_id for cancellation."""
    content_pieces = []

    for chunk in agent.run(message, stream=True):
        # Store run_id for cancellation thread
        if chunk.run_id and "run_id" not in run_id_container:
            run_id_container["run_id"] = chunk.run_id

        if chunk.event == RunEvent.run_cancelled:
            run_id_container["result"] = {
                "status": "cancelled",
                "content": "".join(content_pieces)
            }
            return

        if chunk.event == RunEvent.run_content:
            content_pieces.append(chunk.content)

    run_id_container["result"] = {
        "status": "completed",
        "content": "".join(content_pieces)
    }

def cancel_after_delay(agent, run_id_container, delay_seconds):
    """Cancel the run after a delay."""
    time.sleep(delay_seconds)

    run_id = run_id_container.get("run_id")
    if run_id:
        success = agent.cancel_run(run_id)
        print(f"Cancellation {'succeeded' if success else 'failed'}")

# Usage
run_id_container = {}

agent_thread = threading.Thread(
    target=run_agent,
    args=(agent, run_id_container, "Write a very long story...")
)

cancel_thread = threading.Thread(
    target=cancel_after_delay,
    args=(agent, run_id_container, 5)  # Cancel after 5 seconds
)

agent_thread.start()
cancel_thread.start()

agent_thread.join()
cancel_thread.join()

print(run_id_container["result"])
```

---

## Web Application Pattern

For web apps, track active runs per user:

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

# Track active runs: {user_id: run_id}
active_runs = {}

@app.post("/api/chat")
async def chat(request: Request):
    user_id = request.state.user_id
    body = await request.json()
    message = body["message"]

    async def generate():
        async for event in agent.arun(message, stream=True):
            # Track run_id
            if event.run_id and user_id not in active_runs:
                active_runs[user_id] = event.run_id

            # Handle cancellation
            if event.event == RunEvent.run_cancelled:
                active_runs.pop(user_id, None)
                yield f"event: cancelled\ndata: {{}}\n\n"
                return

            # Stream content
            if event.event == RunEvent.run_content:
                yield f"event: content\ndata: {event.content}\n\n"

        # Cleanup on completion
        active_runs.pop(user_id, None)

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/api/chat/cancel")
async def cancel_chat(request: Request):
    user_id = request.state.user_id

    run_id = active_runs.get(user_id)
    if not run_id:
        return {"success": False, "error": "No active run"}

    success = agent.cancel_run(run_id)
    if success:
        active_runs.pop(user_id, None)

    return {"success": success}
```

---

## Async Cancellation

For async code, use the same pattern:

```python
import asyncio

async def run_with_timeout(agent, message, timeout_seconds=30):
    """Run agent with automatic timeout cancellation."""
    run_id = None
    content = []

    async def stream():
        nonlocal run_id
        async for event in agent.arun(message, stream=True):
            if event.run_id and not run_id:
                run_id = event.run_id

            if event.event == RunEvent.run_cancelled:
                return {"status": "cancelled", "content": "".join(content)}

            if event.event == RunEvent.run_content:
                content.append(event.content)
                yield event.content

        return {"status": "completed", "content": "".join(content)}

    try:
        async with asyncio.timeout(timeout_seconds):
            async for chunk in stream():
                print(chunk, end="")
    except asyncio.TimeoutError:
        if run_id:
            agent.cancel_run(run_id)
        return {"status": "timeout", "content": "".join(content)}
```

---

## REST API (AgentOS)

If using AgentOS, cancel via REST API:

```bash
# Cancel agent run
POST /agents/{agent_id}/runs/{run_id}/cancel

# Cancel team run
POST /teams/{team_id}/runs/{run_id}/cancel

# Cancel workflow run
POST /workflows/{workflow_id}/runs/{run_id}/cancel
```

---

## Use Cases

### 1. User Stop Button

```python
# Frontend sends cancel request
# POST /api/chat/cancel

# Backend handles
@app.post("/api/chat/cancel")
async def cancel(request: Request):
    user_id = request.state.user_id
    run_id = active_runs.get(user_id)
    if run_id:
        team.cancel_run(run_id)
        return {"cancelled": True}
    return {"cancelled": False}
```

### 2. Timeout Enforcement

```python
# Already have timeout via asyncio.timeout()
async with asyncio.timeout(120):  # 2 minutes
    async for event in agent.arun(...):
        ...

# On timeout, cancel the run
except asyncio.TimeoutError:
    if run_id:
        agent.cancel_run(run_id)
```

### 3. Cost Control

```python
token_count = 0
MAX_TOKENS = 10000

for chunk in agent.run(message, stream=True):
    if chunk.metrics:
        token_count += chunk.metrics.total_tokens

    if token_count > MAX_TOKENS:
        agent.cancel_run(chunk.run_id)
        break
```

### 4. User Navigation Away

```javascript
// Frontend: Cancel when user leaves page
window.addEventListener('beforeunload', () => {
    if (activeRunId) {
        navigator.sendBeacon('/api/chat/cancel', JSON.stringify({
            run_id: activeRunId
        }));
    }
});
```

---

## Best Practices

### 1. Always Track run_id

```python
# Store run_id as soon as available
active_runs[user_id] = event.run_id
```

### 2. Handle Cancellation Events

```python
if event.event == RunEvent.run_cancelled:
    # Save partial content
    # Update UI
    # Cleanup resources
    pass
```

### 3. Cleanup on Cancel

```python
finally:
    active_runs.pop(user_id, None)
```

### 4. Don't Assume Instant

```python
# Cancellation is graceful, not instant
# The current step will finish first
```

### 5. Handle Already-Completed Runs

```python
success = agent.cancel_run(run_id)
if not success:
    # Run already completed or doesn't exist
    pass
```

---

## Summary

| Method | Works On | Event |
|--------|----------|-------|
| `agent.cancel_run(run_id)` | Agent | `RunEvent.run_cancelled` |
| `team.cancel_run(run_id)` | Team | `TeamRunEvent.run_cancelled` |
| `workflow.cancel_run(run_id)` | Workflow | `WorkflowRunEvent.workflow_cancelled` |

**Key Insight:** Run cancellation enables user control, timeout enforcement, and cost management. Essential for production applications where users need a "Stop" button.
