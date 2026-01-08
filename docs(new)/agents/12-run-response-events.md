# AGNO Run Response Events Documentation

> **Source:** https://docs.agno.com/basics/agents/usage/run-response-events
> **Last Updated:** 2025-11-29

---

## What Are Run Response Events?

Run Response Events allow you to monitor and react to different stages of an agent's execution in real-time. Instead of waiting for a complete response, you can observe each step: when tools start, when they complete, when text is generated, etc.

**Use Cases:**
- Show "Searching..." indicators when tools are running
- Stream text to users word-by-word
- Log tool calls for debugging
- Build activity feeds showing agent work
- Track progress in long-running operations

---

## Event Types - Agents

### Core Events

| Event | Description |
|-------|-------------|
| `RunStartedEvent` | Indicates the start of a run |
| `RunContentEvent` | Contains model's response text as individual chunks |
| `RunContentCompletedEvent` | Signals completion of content streaming |
| `RunIntermediateContentEvent` | Intermediate response text (when `output_model` is set) |
| `RunCompletedEvent` | Signals successful completion of the run |
| `RunErrorEvent` | Indicates an error occurred during the run |
| `RunCancelledEvent` | Signals that the run was cancelled |

### Tool Events

| Event | Description |
|-------|-------------|
| `ToolCallStartedEvent` | Indicates the start of a tool call |
| `ToolCallCompletedEvent` | Signals completion of a tool call, including results |

---

## Event Types - Teams

Teams use the same pattern but with `Team` prefix:

| Event | Description |
|-------|-------------|
| `TeamRunStartedEvent` | Start of team run |
| `TeamRunContentEvent` | Content chunks from team |
| `TeamRunContentCompletedEvent` | Content streaming complete |
| `TeamRunCompletedEvent` | Team run complete |
| `TeamRunErrorEvent` | Error during team run |
| `TeamRunCancelledEvent` | Team run cancelled |
| `TeamToolCallStartedEvent` | Tool call started |
| `TeamToolCallCompletedEvent` | Tool call completed |

---

## Streaming Modes

### Default Streaming (Content Only)

```python
# Only RunContentEvent is emitted
response = agent.run("Your prompt", stream=True)

for chunk in response:
    print(chunk.content, end="")
```

### Full Event Streaming

```python
# ALL events are emitted (tools, content, etc.)
response = agent.run(
    "Your prompt",
    stream=True,
    stream_events=True  # Enable full event streaming
)

for event in response:
    if isinstance(event, ToolCallStartedEvent):
        print(f"Tool started: {event.tool.tool_name}")
    elif isinstance(event, RunContentEvent):
        print(event.content, end="")
```

---

## Event Attributes

### RunContentEvent

| Attribute | Type | Description |
|-----------|------|-------------|
| `event` | str | "RunContent" |
| `content` | Optional[Any] | The content of the response |
| `content_type` | str | Type of content (default: "str") |
| `reasoning_content` | Optional[str] | Reasoning content produced |
| `citations` | Optional[Citations] | Citations used in response |
| `model_provider_data` | Optional[Any] | Model-specific metadata |
| `response_audio` | Optional[Audio] | Audio response |
| `image` | Optional[Image] | Image attached to response |
| `references` | Optional[List] | References used |
| `reasoning_steps` | Optional[List] | Reasoning steps |

### ToolCallStartedEvent

| Attribute | Type | Description |
|-----------|------|-------------|
| `event` | str | "ToolCallStarted" |
| `tool` | Optional[ToolExecution] | The tool being called |
| `tool.tool_name` | str | Name of the tool |
| `tool.tool_args` | dict | Arguments passed to tool |

### ToolCallCompletedEvent

| Attribute | Type | Description |
|-----------|------|-------------|
| `event` | str | "ToolCallCompleted" |
| `tool` | Optional[ToolExecution] | The completed tool |
| `tool.tool_name` | str | Name of the tool |
| `tool.tool_args` | dict | Arguments used |
| `tool.result` | Any | Result returned by tool |

---

## Basic Usage

```python
from typing import Iterator, List
from agno.agent import (
    Agent,
    RunContentEvent,
    RunOutputEvent,
    ToolCallCompletedEvent,
    ToolCallStartedEvent,
)
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    markdown=True,
)

# Stream with events
run_response: Iterator[RunOutputEvent] = agent.run(
    "What's happening in the news?",
    stream=True
)

response: List[str] = []
for chunk in run_response:
    if isinstance(chunk, RunContentEvent):
        response.append(chunk.content)
    elif isinstance(chunk, ToolCallStartedEvent):
        response.append(
            f"Tool started: {chunk.tool.tool_name} "
            f"with args: {chunk.tool.tool_args}"
        )
    elif isinstance(chunk, ToolCallCompletedEvent):
        response.append(
            f"Tool completed: {chunk.tool.tool_name} "
            f"with result: {chunk.tool.result}"
        )

print("\n".join(response))
```

---

## Team Event Handling

```python
from agno.team import Team
from agno.run.team import (
    TeamRunContentEvent,
    TeamToolCallStartedEvent,
    TeamToolCallCompletedEvent,
)

team = Team(
    members=[agent1, agent2],
    model=Gemini(id="gemini-2.5-flash"),
)

for event in team.run("Research this topic", stream=True, stream_events=True):
    if isinstance(event, TeamToolCallStartedEvent):
        print(f"Team tool started: {event.tool.tool_name}")
    elif isinstance(event, TeamToolCallCompletedEvent):
        print(f"Team tool completed: {event.tool.tool_name}")
    elif isinstance(event, TeamRunContentEvent):
        print(event.content, end="")
```

---

## Async Event Handling

```python
async for event in agent.arun("Your prompt", stream=True):
    if isinstance(event, RunContentEvent):
        print(event.content, end="")
    elif isinstance(event, ToolCallStartedEvent):
        print(f"\nTool: {event.tool.tool_name}")
```

---

## SSE (Server-Sent Events) Pattern

For web applications, convert AGNO events to SSE:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

async def stream_response(message: str):
    async for event in agent.arun(message, stream=True, stream_events=True):
        if isinstance(event, ToolCallStartedEvent):
            yield f"data: {json.dumps({'type': 'tool_start', 'tool': event.tool.tool_name})}\n\n"
        elif isinstance(event, ToolCallCompletedEvent):
            yield f"data: {json.dumps({'type': 'tool_complete', 'tool': event.tool.tool_name})}\n\n"
        elif isinstance(event, RunContentEvent):
            yield f"data: {json.dumps({'type': 'content', 'text': event.content})}\n\n"

@app.post("/chat")
async def chat(message: str):
    return StreamingResponse(
        stream_response(message),
        media_type="text/event-stream"
    )
```

---

## V2 Changes (IMPORTANT)

Event names were renamed in AGNO v2:

| Old (V1) | New (V2) |
|----------|----------|
| `RunResponseStartedEvent` | `RunStartedEvent` |
| `RunResponseContentEvent` | `RunContentEvent` |
| `RunResponseCompletedEvent` | `RunCompletedEvent` |
| `RunResponseErrorEvent` | `RunErrorEvent` |
| `RunResponseCancelledEvent` | `RunCancelledEvent` |
| `RunResponse` | `RunOutput` |

Import location changed to `agno.run.agent` for `RunOutput`.

---

## Best Practices

### 1. Use `stream_events=True` for Activity Indicators

```python
# Show users what the agent is doing
response = agent.run(message, stream=True, stream_events=True)

for event in response:
    if isinstance(event, ToolCallStartedEvent):
        show_activity_indicator(f"Using {event.tool.tool_name}...")
    elif isinstance(event, ToolCallCompletedEvent):
        hide_activity_indicator()
```

### 2. Handle Errors Gracefully

```python
for event in agent.run(message, stream=True, stream_events=True):
    if isinstance(event, RunErrorEvent):
        log_error(event.error)
        notify_user("Something went wrong")
        break
```

### 3. Store Events for Debugging

```python
events_log = []
for event in agent.run(message, stream=True, stream_events=True):
    events_log.append({
        "type": type(event).__name__,
        "timestamp": datetime.now().isoformat(),
        "data": str(event)
    })
```

### 4. Use `store_events=True` on Agent/Team

```python
agent = Agent(
    model=...,
    store_events=True,  # Retain all run events in database
)
```

---

## Summary

| Feature | Parameter | Notes |
|---------|-----------|-------|
| Basic streaming | `stream=True` | Only content events |
| Full events | `stream=True, stream_events=True` | All event types |
| Store events | `store_events=True` | Persist to database |
| Async streaming | `arun(..., stream=True)` | Returns AsyncIterator |

**Key Insight:** Use `stream_events=True` when you need to show users what the agent is doing (tool calls, progress), not just the final text output.
