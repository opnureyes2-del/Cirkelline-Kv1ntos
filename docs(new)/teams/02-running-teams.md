# Running Teams

**AGNO Version:** 2.2.13
**Source:** https://docs.agno.com/basics/teams/running-teams

---

## Execution Flow

When you call `Team.run()` or `Team.arun()`, AGNO executes a series of steps:

```
1. Pre-hooks execute (validation/setup)
2. Reasoning agent runs (if enabled)
3. Context builds (system message, user input, history, memories, session state)
4. Model processes the context
5. Model decides: respond directly, call tools, or delegate to members
6. If delegating → members run concurrently (async mode) → return results
7. Team leader processes results (may delegate further or respond)
8. Response parsed into output_schema (if provided)
9. Post-hooks execute (final validation)
10. Session and metrics stored in database (if configured)
11. TeamRunOutput returned to caller
```

---

## Basic Execution Methods

### run() - Synchronous

```python
from agno.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

news_agent = Agent(
    name="News Agent",
    model=OpenAIChat(id="gpt-4o"),
    role="Get the latest news",
    tools=[DuckDuckGoTools()]
)

team = Team(
    name="News Team",
    members=[news_agent],
    model=OpenAIChat(id="gpt-4o")
)

# Run and get response
response = team.run("What's the latest news?")
print(response.content)
```

### arun() - Asynchronous

Members run **concurrently** when the team leader delegates to multiple members:

```python
import asyncio

async def main():
    response = await team.arun("What's the latest news?")
    print(response.content)

asyncio.run(main())
```

### print_response() - Development

Prints formatted output directly to terminal:

```python
# Basic usage
team.print_response("What's the weather?", stream=True)

# Show member responses too
team.print_response("...", stream=True, show_members_responses=True)

# With markdown formatting
team.print_response("...", stream=True, markdown=True)
```

---

## Run Parameters

Both `run()` and `arun()` accept these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `input` | `str`, `List`, `Dict`, `Message`, `BaseModel` | The input to send |
| `stream` | `bool` | Enable streaming response |
| `stream_events` | `bool` | Stream intermediate steps |
| `session_id` | `str` | Session ID for continuity |
| `session_state` | `Dict[str, Any]` | Session state (merged with DB) |
| `user_id` | `str` | User ID for isolation |
| `retries` | `int` | Number of retry attempts |
| `audio` | `Sequence[Audio]` | Audio files to include |
| `images` | `Sequence[Image]` | Image files to include |
| `videos` | `Sequence[Video]` | Video files to include |
| `files` | `Sequence[File]` | Files to include |
| `knowledge_filters` | `Dict[str, Any]` | Knowledge base filters |
| `add_history_to_context` | `bool` | Include chat history |
| `add_dependencies_to_context` | `bool` | Include dependencies |
| `add_session_state_to_context` | `bool` | Include session state |
| `dependencies` | `Dict[str, Any]` | Dependencies for this run |
| `metadata` | `Dict[str, Any]` | Metadata for this run |
| `output_schema` | `Type[BaseModel]` | Structured output schema |
| `debug_mode` | `bool` | Enable debug logging |
| `yield_run_response` | `bool` | Yield run response (streaming only) |

---

## TeamRunOutput

When not streaming, `run()` returns a `TeamRunOutput` object:

```python
response = team.run("Query")

# Access content
print(response.content)

# Access messages sent to model
for message in response.messages:
    print(message.role, message.content)

# Access metrics
print(response.metrics)

# Access member responses (if store_member_responses=True)
if response.member_responses:
    for member_response in response.member_responses:
        print(member_response.content)
```

### Key Properties

| Property | Description |
|----------|-------------|
| `content` | The final response content |
| `messages` | List of messages sent to model |
| `metrics` | Token usage, timing, costs |
| `member_responses` | List of member `RunOutput` objects |
| `run_id` | Unique identifier for this run |
| `session_id` | Session identifier |

---

## Streaming

### Basic Streaming

Enable with `stream=True` to receive chunks as they're generated:

```python
# Returns iterator of TeamRunOutputEvent objects
stream = team.run("Your query", stream=True)

for chunk in stream:
    print(chunk.content, end="", flush=True)
```

### Async Streaming

```python
async def main():
    stream = await team.arun("Your query", stream=True)
    async for chunk in stream:
        print(chunk.content, end="", flush=True)

asyncio.run(main())
```

### Event Streaming

Get real-time updates about internal processes with `stream_events=True`:

```python
from agno.run.team import TeamRunEvent

stream = team.run(
    "Your query",
    stream=True,
    stream_events=True
)

for event in stream:
    if event.event == TeamRunEvent.run_started:
        print("Team run started")
    elif event.event == TeamRunEvent.run_content:
        print(event.content, end="", flush=True)
    elif event.event == TeamRunEvent.tool_call_started:
        print(f"Tool call: {event.tool_name}")
    elif event.event == TeamRunEvent.run_completed:
        print("\nTeam run completed")
```

### Member Event Streaming

By default, team leader streams member events to caller. Members run concurrently in async mode.

```python
team = Team(
    members=[agent1, agent2],
    stream_member_events=True,  # Default: True
)
```

Disable with `stream_member_events=False` if you only want team leader events.

---

## Event Types

### Core Events

| Event | Description |
|-------|-------------|
| `TeamRunStarted` | Team run has started |
| `TeamRunContent` | Content chunk received |
| `TeamRunContentCompleted` | Content generation completed |
| `TeamRunIntermediateContent` | Intermediate content (before final) |
| `TeamRunCompleted` | Team run completed successfully |
| `TeamRunError` | Error occurred during run |
| `TeamRunCancelled` | Run was cancelled |

### Tool Events

| Event | Description |
|-------|-------------|
| `TeamToolCallStarted` | Tool call initiated |
| `TeamToolCallCompleted` | Tool call finished |

### Reasoning Events

| Event | Description |
|-------|-------------|
| `TeamReasoningStarted` | Reasoning phase started |
| `TeamReasoningStep` | Individual reasoning step |
| `TeamReasoningCompleted` | Reasoning phase completed |

### Memory Events

| Event | Description |
|-------|-------------|
| `TeamMemoryUpdateStarted` | Memory update started |
| `TeamMemoryUpdateCompleted` | Memory update completed |

### Hook Events

| Event | Description |
|-------|-------------|
| `TeamPreHookStarted` | Pre-hook execution started |
| `TeamPreHookCompleted` | Pre-hook execution completed |
| `TeamPostHookStarted` | Post-hook execution started |
| `TeamPostHookCompleted` | Post-hook execution completed |

### Model Events

| Event | Description |
|-------|-------------|
| `TeamParserModelResponseStarted` | Parser model started |
| `TeamParserModelResponseCompleted` | Parser model completed |
| `TeamOutputModelResponseStarted` | Output model started |
| `TeamOutputModelResponseCompleted` | Output model completed |

---

## Event Storage

Store all run events on the `TeamRunOutput`:

```python
team = Team(
    name="My Team",
    members=[...],
    store_events=True,  # Store events for later access
)

response = team.run("Query")

# Access stored events
for event in response.events:
    print(event.event, event.content)
```

### Skip Specific Events

Control which events are stored:

```python
team = Team(
    store_events=True,
    events_to_skip=["TeamRunContent"],  # Don't store content chunks
)
```

---

## Custom Events

Create custom events for your tools:

```python
from dataclasses import dataclass
from typing import Optional
from agno.run.team import CustomEvent

@dataclass
class CustomerProfileEvent(CustomEvent):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None

# Yield from a tool
def get_customer_profile(customer_id: str):
    # ... fetch customer ...
    yield CustomerProfileEvent(
        customer_name="John Doe",
        customer_email="john@example.com"
    )
    return customer_data
```

Custom events integrate with standard AGNO events and appear in the stream.

---

## User & Session Management

### Per-Run User/Session

```python
response = team.run(
    "Query",
    user_id="user_123",
    session_id="session_456"
)
```

### Session State

Pass custom state that's available throughout the run:

```python
response = team.run(
    "Query",
    session_state={
        "user_timezone": "Europe/London",
        "user_preferences": {"language": "en"}
    }
)
```

---

## Multimodal Input

### Images

```python
from agno.models.content import Image

response = team.run(
    "Analyze this image",
    images=[Image(url="https://example.com/image.jpg")]
)
```

### Audio

```python
from agno.models.content import Audio

response = team.run(
    "Transcribe this audio",
    audio=[Audio(filepath="/path/to/audio.mp3")]
)
```

### Videos

```python
from agno.models.content import Video

response = team.run(
    "Describe this video",
    videos=[Video(url="https://example.com/video.mp4")]
)
```

---

## Structured Output

Use Pydantic models for typed responses:

```python
from pydantic import BaseModel

class ResearchReport(BaseModel):
    title: str
    summary: str
    findings: list[str]
    confidence: float

response = team.run(
    "Research AI trends",
    output_schema=ResearchReport
)

# response.content is now a ResearchReport instance
report = response.content
print(report.title)
print(report.findings)
```

---

## Metrics

Access detailed metrics about the run:

```python
team = Team(
    members=[...],
    store_member_responses=True,  # Include member metrics
)

response = team.run("Query")

# Team-level metrics
print(response.metrics)
# {
#   "input_tokens": 150,
#   "output_tokens": 200,
#   "total_tokens": 350,
#   "time_to_first_token": 0.5,
#   "response_time": 2.3,
#   ...
# }

# Session metrics (aggregated across all runs)
session_metrics = team.get_session_metrics()
print(session_metrics.to_dict())

# Per-message metrics
for message in response.messages:
    if message.role == "assistant":
        print(message.metrics)
```

---

## Run Cancellation

Cancel a running team:

```python
# Get the run_id from the stream or store it
run_id = None

# In one thread/task
stream = team.run("Long query", stream=True)
for event in stream:
    if event.run_id:
        run_id = event.run_id
    # ... process events

# In another thread/task
team.cancel_run(run_id)
```

---

## Error Handling

```python
from agno.exceptions import ModelProviderError

try:
    response = team.run("Query", retries=3)
except ModelProviderError as e:
    print(f"Model error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Summary

| Method | Returns | Use Case |
|--------|---------|----------|
| `run()` | `TeamRunOutput` or `Iterator` | Synchronous execution |
| `arun()` | `TeamRunOutput` or `AsyncIterator` | Async with concurrent members |
| `print_response()` | None | Development/debugging |

| Parameter | Purpose |
|-----------|---------|
| `stream=True` | Get response chunks as they generate |
| `stream_events=True` | Get internal process updates |
| `store_events=True` | Store events on response object |
| `store_member_responses=True` | Include member responses in output |
| `output_schema=Model` | Get structured typed response |

**Key Points:**
1. Use `arun()` for concurrent member execution
2. `stream=True` returns iterator instead of complete response
3. `stream_events=True` shows internal delegation/tool activity
4. Access metrics at message, run, and session levels
5. Custom events integrate with standard event stream
