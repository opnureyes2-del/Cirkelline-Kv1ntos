# Streaming Agent Responses

**Source:** https://docs.agno.com/basics/agents/usage/streaming

Streaming allows you to process agent responses in real-time as they're generated, rather than waiting for the complete response. This is essential for building responsive user interfaces and handling long-running operations.

---

## Table of Contents

1. [Why Stream?](#why-stream)
2. [Basic Streaming](#basic-streaming)
3. [Async Streaming](#async-streaming)
4. [Stream Events](#stream-events)
5. [Team Streaming](#team-streaming)
6. [Event Types Reference](#event-types-reference)
7. [Best Practices](#best-practices)
8. [Common Patterns](#common-patterns)

---

## Why Stream?

**Streaming provides several benefits:**

### 1. Improved User Experience
```python
# Without streaming - user waits 30 seconds
response = agent.run("Write a long article")
print(response.content)  # Shows nothing until complete

# With streaming - user sees progress immediately
for chunk in agent.run("Write a long article", stream=True):
    if chunk.event == RunEvent.run_content:
        print(chunk.content, end="", flush=True)  # Shows text as it's generated
```

### 2. Real-Time Feedback
- Show progress indicators
- Display partial results
- Provide status updates
- Allow early cancellation

### 3. Memory Efficiency
- Process chunks incrementally
- Don't need to hold full response in memory
- Better for large outputs

### 4. Debugging & Monitoring
- See tool calls as they happen
- Monitor reasoning steps
- Track delegation events
- Catch errors earlier

---

## Basic Streaming

### Synchronous Streaming

**Simple streaming pattern:**

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.run.agent import RunEvent

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful assistant.",
)

# Stream the response
stream = agent.run("Trending products", stream=True)

# Process each chunk
for chunk in stream:
    if chunk.event == RunEvent.run_content:
        print(chunk.content, end="", flush=True)
```

**Key points:**
- Set `stream=True` in the `run()` method
- Returns an iterator instead of a single response
- Filter by `RunEvent.run_content` to get text chunks
- Use `end=""` and `flush=True` for real-time display

### Using with Gemini

```python
from agno.agent import Agent
from agno.models.google import Gemini
from agno.run.agent import RunEvent

agent = Agent(
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Be concise and helpful.",
)

# Stream response
for chunk in agent.run("Explain Python in 3 sentences", stream=True):
    if chunk.event == RunEvent.run_content:
        print(chunk.content, end="", flush=True)

print()  # New line after streaming completes
```

---

## Async Streaming

### Basic Async Streaming

**Using `arun()` for async streaming:**

```python
import asyncio
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.run.agent import RunEvent

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful assistant.",
)

async def stream_response():
    # Use async for with arun()
    async for chunk in agent.arun("Tell me a story", stream=True):
        if chunk.event == RunEvent.run_content:
            print(chunk.content, end="", flush=True)

    print()  # New line

# Run async function
asyncio.run(stream_response())
```

**Key differences from sync:**
- Use `arun()` instead of `run()`
- Use `async for` instead of `for`
- Wrap in `async def` function
- Run with `asyncio.run()`

### Using `aprint_response()`

**Convenience method for printing streamed responses:**

```python
import asyncio
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="Be helpful and concise.",
)

# Automatically prints streamed response
asyncio.run(
    agent.aprint_response(
        "Share a 2 sentence horror story",
        stream=True
    )
)
```

**What `aprint_response()` does:**
- Automatically filters `run_content` events
- Prints with proper formatting
- Handles async iteration
- Perfect for CLI applications

### Multiple Concurrent Streams

```python
import asyncio
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful assistant.",
)

async def process_query(query: str, label: str):
    """Process a single query with streaming"""
    print(f"\n{label}:")
    await agent.aprint_response(query, stream=True)

async def main():
    # Run multiple queries concurrently
    await asyncio.gather(
        process_query("What is Python?", "Query 1"),
        process_query("What is JavaScript?", "Query 2"),
        process_query("What is Rust?", "Query 3"),
    )

asyncio.run(main())
```

---

## Stream Events

### Event Types

**By default, only content is streamed. Enable all events with `stream_events=True`:**

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.run.agent import RunEvent

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful assistant.",
    tools=[...],  # Some tools
)

# Stream ALL events
for event in agent.run(
    "Search for Python tutorials",
    stream=True,
    stream_events=True  # ← Enable all event types
):
    # Handle different event types
    if event.event == RunEvent.run_content:
        print(f"Content: {event.content}")

    elif event.event == RunEvent.tool_call_started:
        print(f"Tool call started: {event.tool_name}")

    elif event.event == RunEvent.tool_call_completed:
        print(f"Tool call completed: {event.tool_name}")

    elif event.event == RunEvent.reasoning_step:
        print(f"Reasoning: {event.content}")
```

### Available Events

**Common `RunEvent` types:**

1. **`run_content`** - Generated text content
2. **`tool_call_started`** - Tool execution beginning
3. **`tool_call_completed`** - Tool execution finished
4. **`reasoning_step`** - Agent thinking process
5. **`run_started`** - Agent run beginning
6. **`run_completed`** - Agent run finished

### Event Filtering Example

```python
def process_stream(agent, query):
    """Process streaming events with custom handling"""

    content_buffer = []
    tool_calls = []

    for event in agent.run(query, stream=True, stream_events=True):

        # Collect content
        if event.event == RunEvent.run_content:
            content_buffer.append(event.content)
            print(event.content, end="", flush=True)

        # Track tool usage
        elif event.event == RunEvent.tool_call_started:
            tool_calls.append(event.tool_name)
            print(f"\n[Using tool: {event.tool_name}]")

        # Show completion
        elif event.event == RunEvent.run_completed:
            print("\n✓ Complete")

    # Return collected data
    return {
        "content": "".join(content_buffer),
        "tools_used": tool_calls
    }
```

---

## Team Streaming

### Basic Team Streaming

**Teams stream their leader's responses by default:**

```python
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.run.team import TeamRunEvent

# Create team members
researcher = Agent(
    name="Researcher",
    model=OpenAIChat(id="gpt-4o"),
    role="Research topics",
)

writer = Agent(
    name="Writer",
    model=OpenAIChat(id="gpt-4o"),
    role="Write content",
)

# Create team
team = Team(
    name="Content Team",
    members=[researcher, writer],
    model=OpenAIChat(id="gpt-4o"),
)

# Stream team response
for event in team.run("Write about AI", stream=True):
    if event.event == TeamRunEvent.team_run_content:
        print(event.content, end="", flush=True)
```

### Streaming Member Events

**See what team members are doing with `stream_member_events=True`:**

```python
from agno.team import Team
from agno.run.team import TeamRunEvent

team = Team(
    name="Research Team",
    members=[researcher, analyst],
    model=OpenAIChat(id="gpt-4o"),
    stream_member_events=True  # ← Enable member event streaming
)

for event in team.run(
    "Research Python frameworks",
    stream=True,
    stream_events=True
):
    # Team leader content
    if event.event == TeamRunEvent.team_run_content:
        print(f"[Team]: {event.content}")

    # Member delegation
    elif event.event == TeamRunEvent.team_tool_call_started:
        print(f"[Delegating to]: {event.tool_name}")

    # Member responses (only if stream_member_events=True)
    elif event.event == TeamRunEvent.run_content:
        # This is content from a team member
        print(f"[Member]: {event.content}")
```

### Disabling Member Events

**For cleaner output, disable member streaming:**

```python
team = Team(
    name="News Team",
    members=[news_agent, weather_agent],
    model=OpenAIChat(id="gpt-4o"),
    stream_member_events=False  # ← Only stream team leader
)

response_stream = team.run(
    "What's the weather in Tokyo?",
    stream=True,
    stream_events=True
)

for event in response_stream:
    # Only team leader events will appear
    if event.event == TeamRunEvent.team_run_content:
        print(event.content, end="", flush=True)
```

### Async Team Streaming

```python
import asyncio
from agno.team import Team
from agno.run.team import TeamRunEvent

team = Team(
    name="Research Team",
    members=[researcher, analyst],
    model=OpenAIChat(id="gpt-4o"),
)

async def stream_team_response():
    async for event in team.arun(
        "Research AI trends",
        stream=True,
        stream_events=True,
        stream_member_events=True
    ):
        if event.event == TeamRunEvent.team_run_content:
            print(event.content, end="", flush=True)
        elif event.event == TeamRunEvent.team_tool_call_started:
            print(f"\n[Delegating]: {event.tool_name}")

asyncio.run(stream_team_response())
```

**Important:** When using `arun()`, multiple members can run concurrently. Member events may arrive out of order.

---

## Event Types Reference

### Agent Events (`RunEvent`)

| Event | Description | When it fires |
|-------|-------------|---------------|
| `run_content` | Generated text content | As agent generates response |
| `tool_call_started` | Tool execution beginning | When agent starts using a tool |
| `tool_call_completed` | Tool execution finished | When tool returns result |
| `reasoning_step` | Agent thinking process | During reasoning (if enabled) |
| `run_started` | Agent run beginning | At start of agent.run() |
| `run_completed` | Agent run finished | After agent finishes |

### Team Events (`TeamRunEvent`)

| Event | Description | When it fires |
|-------|-------------|---------------|
| `team_run_content` | Team leader's content | As team leader generates response |
| `team_tool_call_started` | Member delegation start | When delegating to a member |
| `team_tool_call_completed` | Member delegation complete | When member finishes task |
| `team_reasoning_step` | Team leader thinking | During team leader reasoning |
| `run_content` | Member content | When member generates content (if `stream_member_events=True`) |

### Event Attributes

**Common attributes on event objects:**

```python
event.event          # Event type (string)
event.content        # Text content (if applicable)
event.tool_name      # Tool/member name (for tool_call events)
event.timestamp      # When event occurred
```

---

## Best Practices

### 1. Always Filter by Event Type

```python
# ❌ BAD - assumes all events have content
for chunk in agent.run("query", stream=True):
    print(chunk.content)  # Might crash on non-content events

# ✓ GOOD - filter for content events
for chunk in agent.run("query", stream=True):
    if chunk.event == RunEvent.run_content:
        print(chunk.content, end="", flush=True)
```

### 2. Use `stream_events=True` for Debugging

```python
# During development - see everything
for event in agent.run(
    "query",
    stream=True,
    stream_events=True  # See all events for debugging
):
    print(f"{event.event}: {getattr(event, 'content', 'N/A')}")

# In production - only stream content
for event in agent.run("query", stream=True):
    if event.event == RunEvent.run_content:
        print(event.content, end="", flush=True)
```

### 3. Handle Errors Gracefully

```python
try:
    for event in agent.run("query", stream=True, stream_events=True):
        if event.event == RunEvent.run_content:
            print(event.content, end="", flush=True)
        elif event.event == RunEvent.tool_call_started:
            print(f"\n[Using: {event.tool_name}]")
except Exception as e:
    print(f"\nError during streaming: {e}")
    # Handle error appropriately
```

### 4. Flush Output for Real-Time Display

```python
# ✓ GOOD - flush for immediate display
for event in agent.run("query", stream=True):
    if event.event == RunEvent.run_content:
        print(event.content, end="", flush=True)  # flush=True is key

# ❌ BAD - buffered output, not truly real-time
for event in agent.run("query", stream=True):
    if event.event == RunEvent.run_content:
        print(event.content, end="")  # No flush - buffered
```

### 5. Use Async for Concurrent Operations

```python
import asyncio

# ✓ GOOD - concurrent streaming with async
async def process_multiple():
    tasks = [
        agent.aprint_response("Query 1", stream=True),
        agent.aprint_response("Query 2", stream=True),
        agent.aprint_response("Query 3", stream=True),
    ]
    await asyncio.gather(*tasks)

asyncio.run(process_multiple())

# ❌ BAD - sequential processing
for query in ["Query 1", "Query 2", "Query 3"]:
    for event in agent.run(query, stream=True):
        if event.event == RunEvent.run_content:
            print(event.content, end="", flush=True)
```

### 6. Disable Member Events for Production

```python
# For production UIs - only show final results
team = Team(
    name="Team",
    members=[agent1, agent2],
    model=OpenAIChat(id="gpt-4o"),
    stream_member_events=False  # Hide internal work
)

# For debugging - show everything
team = Team(
    name="Team",
    members=[agent1, agent2],
    model=OpenAIChat(id="gpt-4o"),
    stream_member_events=True  # Show all member activity
)
```

---

## Common Patterns

### Pattern 1: Web API Streaming (FastAPI)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.run.agent import RunEvent

app = FastAPI()
agent = Agent(model=OpenAIChat(id="gpt-4o"))

@app.post("/chat/stream")
async def chat_stream(message: str):
    async def event_generator():
        async for event in agent.arun(message, stream=True):
            if event.event == RunEvent.run_content:
                yield f"data: {event.content}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

### Pattern 2: Progress Indicator

```python
from agno.run.agent import RunEvent

def run_with_progress(agent, query):
    """Show progress while streaming"""
    print("Processing", end="", flush=True)

    content_chunks = []
    tool_count = 0

    for event in agent.run(query, stream=True, stream_events=True):
        if event.event == RunEvent.run_content:
            content_chunks.append(event.content)
            print(".", end="", flush=True)  # Progress dots

        elif event.event == RunEvent.tool_call_started:
            tool_count += 1
            print(f"\n[Tool {tool_count}]", end="", flush=True)

    print("\n\nComplete!")
    return "".join(content_chunks)
```

### Pattern 3: Collect Full Response

```python
def stream_and_collect(agent, query):
    """Stream for UX but also collect full response"""
    full_content = []

    for event in agent.run(query, stream=True):
        if event.event == RunEvent.run_content:
            chunk = event.content
            full_content.append(chunk)
            print(chunk, end="", flush=True)  # Show to user

    print()  # New line

    # Return complete response
    return "".join(full_content)

# Usage
complete_response = stream_and_collect(agent, "Write an essay")
# complete_response now has full text for storage/processing
```

### Pattern 4: Event Logging

```python
import logging
from agno.run.agent import RunEvent

logger = logging.getLogger(__name__)

def run_with_logging(agent, query):
    """Log all events while streaming"""

    for event in agent.run(query, stream=True, stream_events=True):
        # Log the event
        logger.info(f"Event: {event.event}")

        # Display content
        if event.event == RunEvent.run_content:
            print(event.content, end="", flush=True)

        # Log tool usage
        elif event.event == RunEvent.tool_call_started:
            logger.info(f"Tool called: {event.tool_name}")
```

### Pattern 5: Markdown Streaming

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.run.agent import RunEvent

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    markdown=True  # Enable markdown output
)

def stream_markdown(query):
    """Stream markdown content"""
    for event in agent.run(query, stream=True):
        if event.event == RunEvent.run_content:
            # Markdown-formatted chunks
            print(event.content, end="", flush=True)

stream_markdown("Create a markdown table of Python frameworks")
```

---

## Summary

**Key Takeaways:**

1. **Enable streaming** with `stream=True`
2. **Use async** with `arun()` for better concurrency
3. **Filter events** by type (e.g., `RunEvent.run_content`)
4. **Enable all events** with `stream_events=True` for debugging
5. **Control team events** with `stream_member_events` parameter
6. **Always flush output** for real-time display
7. **Handle errors** gracefully with try/except
8. **Use async patterns** for concurrent streams

**Next Steps:**
- Explore [Async Usage](./05-async-usage.md) for advanced async patterns
- Learn about [Teams](../../teams/) for multi-agent streaming
- Check [Debugging](./03-debugging-agents.md) for troubleshooting streams
