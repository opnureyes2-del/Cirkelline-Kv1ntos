# Running Agents

**AGNO Version:** 2.2.13
**Source:** https://docs.agno.com/basics/agents/running-agents

---

## How Agents Run

**Execution loop:**
1. Build context (system message, user message, history, memories, session state)
2. Send to model
3. Model responds (message OR tool call)
4. If tool call → execute tool → back to step 2
5. Return final response (when no more tool calls)

---

## Basic Execution

### run() Method

```python
from agno.agent import Agent, RunOutput
from agno.models.anthropic import Claude
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[HackerNewsTools()],
    instructions="Write a report on the topic.",
    markdown=True,
)

# Run and get response
response: RunOutput = agent.run("Trending startups")
print(response.content)
```

**Returns:** `RunOutput` object with full response and metadata.

---

### Simple Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=["You are a helpful assistant."],
    markdown=True,
)

response = agent.run("Tell me a joke")
print(response.content)
```

---

## Development vs Production

### Development: print_response()

**Quick testing - prints to terminal:**

```python
# Development only
agent.print_response("Trending startups")
```

**Not recommended for production.**

---

### Production: run() or arun()

```python
# Synchronous
response: RunOutput = agent.run("Input")

# Asynchronous
response: RunOutput = await agent.arun("Input")
```

**Why production needs run():**
- Returns structured `RunOutput`
- Includes metadata/metrics
- Better error handling
- Can log/store results

---

## RunOutput Object

### Core Attributes

```python
response = agent.run("Tell me about AI")

response.run_id          # Unique run ID
response.agent_id        # Agent ID
response.session_id      # Session ID
response.user_id         # User ID
response.content         # Response content
response.content_type    # Type (str or class name)
response.messages        # Messages sent to model
response.metrics         # Tokens, cost, time
response.tools           # Tool executions
response.status          # completed, error, etc.
```

### Using RunOutput

```python
from agno.utils.pprint import pprint_run_response

response = agent.run("Trending startups")

# Pretty print
pprint_run_response(response, markdown=True)

# Access data
print(f"Run ID: {response.run_id}")
print(f"Tokens: {response.metrics.total_tokens}")
```

**Full reference:** [RunOutput API](https://docs.agno.com/reference/agents/run-response)

---

## Streaming

Stream responses in real-time as they're generated.

### Basic Streaming

```python
from typing import Iterator
from agno.agent import Agent, RunOutputEvent, RunEvent

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You are a helpful assistant.",
)

# Stream response
stream: Iterator[RunOutputEvent] = agent.run(
    "Trending products",
    stream=True
)

# Consume stream
for chunk in stream:
    if chunk.event == RunEvent.run_content:
        print(chunk.content, end="", flush=True)
```

**Returns:** `Iterator[RunOutputEvent]` instead of `RunOutput`.

---

### Stream and Pretty Print

```python
from agno.utils.pprint import pprint_run_response

stream = agent.run("Trending products", stream=True)
pprint_run_response(stream, markdown=True)
```

---

### Handle Different Events

```python
from agno.agent import (
    RunContentEvent,
    ToolCallStartedEvent,
    ToolCallCompletedEvent,
)

stream = agent.run("What's happening in USA?", stream=True)

for chunk in stream:
    if isinstance(chunk, RunContentEvent):
        print(f"Content: {chunk.content}")

    elif isinstance(chunk, ToolCallStartedEvent):
        print(f"Tool: {chunk.tool.tool_name}")
        print(f"Args: {chunk.tool.tool_args}")

    elif isinstance(chunk, ToolCallCompletedEvent):
        print(f"Result: {chunk.tool.result}")
```

---

### Stream Events

Enable intermediate events:

```python
stream = agent.run(
    "Query",
    stream=True,
    stream_events=True  # Tool calls, reasoning, etc.
)
```

---

## Async Execution

### Basic Async

```python
import asyncio

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    markdown=True,
)

async def main():
    response: RunOutput = await agent.arun("Tell me a story")
    print(response.content)

asyncio.run(main())
```

---

### Async with Streaming

```python
import asyncio
from typing import AsyncIterator

async def main():
    stream: AsyncIterator[RunOutputEvent] = await agent.arun(
        "Tell me a story",
        stream=True
    )

    async for chunk in stream:
        if chunk.event == RunEvent.run_content:
            print(chunk.content, end="")

asyncio.run(main())
```

**Returns:** `AsyncIterator[RunOutputEvent]`

---

### Development: aprint_response()

```python
import asyncio

asyncio.run(
    agent.aprint_response("Tell me a story", stream=True)
)
```

---

## Specifying User and Session

Associate runs with specific users and sessions.

### Basic Usage

```python
agent.run(
    "Tell me a story",
    user_id="john@example.com",
    session_id="session_123"
)
```

**Why specify:**
- **user_id:** User-specific memories, permissions, tracking
- **session_id:** Conversation continuity, history, grouped runs

---

### Example

```python
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    db=db,
    add_history_to_context=True,
)

# First message
agent.run(
    "My name is John",
    user_id="user_123",
    session_id="session_abc"
)

# Second message - remembers context
agent.run(
    "What's my name?",
    user_id="user_123",
    session_id="session_abc"
)
# Response: "Your name is John"
```

---

## Run Parameters

### Input Types

```python
# String
agent.run(input="Tell me a joke")

# List
agent.run(input=["Instruction 1", "Instruction 2"])

# Dictionary
agent.run(input={"task": "summarize", "text": "..."})

# Pydantic Model
from pydantic import BaseModel

class Query(BaseModel):
    question: str

agent.run(input=Query(question="What is AI?"))
```

---

### Media Parameters

```python
from agno.media import Image, Audio, Video, File

# Images
agent.run(
    "Describe this",
    images=[Image(url="https://example.com/img.jpg")]
)

# Audio
agent.run(
    "Transcribe this",
    audio=[Audio(content=audio_bytes, format="wav")]
)

# Video
agent.run(
    "Analyze this",
    videos=[Video(url="https://example.com/vid.mp4")]
)

# Files
agent.run(
    "Summarize this",
    files=[File(content=file_bytes, name="doc.pdf")]
)
```

---

### Session Parameters

```python
agent.run(
    "Input",
    session_id="session_123",
    user_id="user_456",
    session_state={"key": "value"},
)
```

---

### Context Parameters

```python
agent.run(
    "Input",
    add_history_to_context=True,
    add_dependencies_to_context=True,
    add_session_state_to_context=True,
)
```

---

### Advanced Parameters

```python
agent.run(
    "Input",
    stream=True,
    stream_events=True,
    retries=3,
    knowledge_filters={"tag": "docs"},
    dependencies={"var": value},
    metadata={"source": "api"},
    output_schema=MyModel,
    debug_mode=True,
)
```

**Full reference:** [Agent.run() API](https://docs.agno.com/reference/agents/agent)

---

## Helper Methods

### print_response()

Development only - prints to terminal:

```python
agent.print_response("Tell me a joke")
agent.print_response("Story", stream=True)
```

---

### aprint_response()

Async version:

```python
import asyncio

asyncio.run(agent.aprint_response("Joke", stream=True))
```

---

### get_last_run_output()

Get last run's output:

```python
agent.run("First query")
agent.run("Second query")

last = agent.get_last_run_output()
print(last.content)
```

---

### continue_run()

Continue paused/errored run:

```python
response = agent.run("Complex task")

if response.status == RunStatus.paused:
    continued = agent.continue_run(run_response=response)
```

---

## Best Practices

### 1. Use run() in Production

**Development:**
```python
agent.print_response("Query")
```

**Production:**
```python
response = agent.run("Query")
# Log response.run_id
# Store response.metrics
```

---

### 2. Always Specify user_id and session_id

**❌ Bad:**
```python
agent.run("Query")
```

**✅ Good:**
```python
agent.run(
    "Query",
    user_id=current_user,
    session_id=current_session
)
```

Enables memories, history, tracking.

---

### 3. Handle Errors

```python
try:
    response = agent.run("Query")

    if response.status == RunStatus.error:
        print(f"Failed: {response.content}")
    elif response.status == RunStatus.completed:
        print(f"Success: {response.content}")

except Exception as e:
    print(f"Error: {e}")
```

---

### 4. Stream Long Responses

```python
stream = agent.run("Write long article", stream=True)

for chunk in stream:
    if chunk.event == RunEvent.run_content:
        print(chunk.content, end="", flush=True)
```

Better UX - show progress, lower perceived latency.

---

### 5. Log Run Metadata

```python
response = agent.run("Query")

logger.info(f"Run: {response.run_id}")
logger.info(f"Session: {response.session_id}")
logger.info(f"Tokens: {response.metrics.total_tokens}")
logger.info(f"Time: {response.metrics.time_to_first_token}s")
```

---

### 6. Use Async for Concurrent Runs

```python
import asyncio

async def run_multiple():
    results = await asyncio.gather(
        agent1.arun("Query 1"),
        agent2.arun("Query 2"),
        agent3.arun("Query 3"),
    )
    return results

asyncio.run(run_multiple())
```

Much faster than sequential!

---

### 7. Test Both Streaming and Non-Streaming

```python
# Non-streaming (simpler debugging)
response = agent.run("Test")
assert "expected" in response.content

# Streaming (production behavior)
stream = agent.run("Test", stream=True)
content = ""
for chunk in stream:
    if chunk.event == RunEvent.run_content:
        content += chunk.content
assert "expected" in content
```

---

## Summary

### Methods

**Development:**
- `print_response()` - Print to terminal
- `aprint_response()` - Async print

**Production:**
- `run()` - Returns RunOutput
- `arun()` - Async returns RunOutput

### Features

**Streaming:**
```python
stream = agent.run(input, stream=True)
```

**Session:**
```python
agent.run(input, user_id="...", session_id="...")
```

**Media:**
```python
agent.run(input, images=[...], audio=[...])
```

### Execution Loop

1. Build context
2. Send to model
3. Model responds
4. Tool call? → Execute → Repeat
5. Return final response

### Best Practices

1. Use `run()` in production
2. Specify `user_id` and `session_id`
3. Handle errors gracefully
4. Stream long responses
5. Log run metadata
6. Use async for concurrency
7. Test both modes

---

## Related Documentation

**AGNO Official:**
- [Running Agents](https://docs.agno.com/basics/agents/running-agents)
- [RunOutput API](https://docs.agno.com/reference/agents/run-response)
- [Agent API](https://docs.agno.com/reference/agents/agent)
- [Streaming](https://docs.agno.com/basics/agents/usage/streaming)

**Next Topics:**
- 03-debugging-agents.md
- 06-streaming.md
- 09-storage.md

---

**AGNO Documentation:** https://docs.agno.com
**Version:** 1.0
