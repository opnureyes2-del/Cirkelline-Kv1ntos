# Debugging Agents

**AGNO Version:** 2.2.13
**Source:** https://docs.agno.com/basics/agents/debugging-agents

---

## What is Debug Mode?

AGNO provides an exceptional debug mode that takes your development experience to the next level.

**Debug mode helps you:**
- Inspect messages sent to the model and responses
- Trace intermediate steps and monitor metrics
- Inspect tool calls, errors, and results
- Identify issues with tools and improve reliability
- Track token usage and execution time

---

## Enabling Debug Mode

### On Agent (All Runs)

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[HackerNewsTools()],
    debug_mode=True,  # Enable for all runs
    # debug_level=2,  # Optional: more detailed logs
)

agent.print_response("Trending startups and products.")
```

**Applies to:** All runs of this agent

---

### On Run (Single Run)

```python
agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[HackerNewsTools()],
)

# Enable debug for this run only
agent.run("Trending startups", debug_mode=True)
```

**Applies to:** Only this specific run

---

### Environment Variable (Global)

```bash
# Linux/Mac
export AGNO_DEBUG=True
python my_agent.py

# Windows
set AGNO_DEBUG=True
python my_agent.py
```

**Applies to:** All agents in this process

---

## Debug Levels

Control the amount of debug information displayed.

### Level 1: Basic Debug Information

```python
agent = Agent(
    model=Claude(id="claude-3-5-sonnet-20240620"),
    tools=[DuckDuckGoTools()],
    debug_mode=True,
    debug_level=1,  # Basic (default)
)

agent.print_response("What is the current price of Tesla?")
```

**Shows:**
- Messages sent to model
- Model responses
- Basic tool calls
- Token counts

---

### Level 2: Detailed Debug Information

```python
agent = Agent(
    model=Claude(id="claude-3-5-sonnet-20240620"),
    tools=[DuckDuckGoTools()],
    debug_mode=True,
    debug_level=2,  # Verbose
)

agent.print_response("What is the current price of Apple?")
```

**Shows:**
- Everything from Level 1
- Detailed tool arguments
- Full message contents
- Execution timestamps
- Additional metadata

---

## Interactive CLI for Testing

Test agents with back-and-forth conversations in the terminal.

### Basic CLI App

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[HackerNewsTools()],
    db=SqliteDb(db_file="tmp/data.db"),
    add_history_to_context=True,
    num_history_runs=3,
    markdown=True,
)

# Run agent as interactive CLI app
agent.cli_app(stream=True)
```

**How it works:**
- Type messages → Get responses
- Conversation history maintained
- Type `exit`, `quit`, or `bye` to quit

---

### Async CLI App

```python
import asyncio

async def main():
    await agent.acli_app(stream=True)

asyncio.run(main())
```

---

### Custom CLI Configuration

```python
agent.cli_app(
    input="Hello! How can I help you today?",  # Initial message
    user="Developer",                           # User name
    emoji="🚀",                                 # User emoji
    stream=True,                                # Stream responses
    markdown=True,                              # Markdown formatting
    exit_on=["exit", "quit", "bye"]            # Exit commands
)
```

---

## Inspecting Messages

Debug mode shows all messages sent to/from the model.

### Example Output

```
DEBUG | Sending messages to model:
  [SystemMessage] You are a helpful assistant.
  [UserMessage] What is the weather in Tokyo?

DEBUG | Model response received (12 tokens):
  [AssistantMessage] I'll check the weather for you.
  [ToolCall] get_weather(location="Tokyo")

DEBUG | Tool execution:
  Tool: get_weather
  Args: {"location": "Tokyo"}
  Result: 22°C, Sunny

DEBUG | Final response sent to user (45 tokens):
  The weather in Tokyo is currently 22°C and sunny.
```

---

## Streaming Intermediate Steps

See tool calls and execution events as they happen.

### Basic Streaming

```python
from typing import Iterator
from agno.agent import Agent, RunOutputEvent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools(stock_price=True)],
    markdown=True,
)

# Enable intermediate step streaming
stream: Iterator[RunOutputEvent] = agent.run(
    "What is the stock price of NVDA",
    stream=True,
    stream_events=True  # Key parameter
)

for chunk in stream:
    print(chunk.to_dict())
    print("---" * 20)
```

**Returns:** All events including tool calls, intermediate results

---

### Event Types

```python
from agno.agent import (
    RunStartedEvent,
    RunContentEvent,
    ToolCallStartedEvent,
    ToolCallCompletedEvent,
    RunCompletedEvent,
)

stream = agent.run("Query", stream=True, stream_events=True)

for event in stream:
    if isinstance(event, RunStartedEvent):
        print(f"Run started: {event.run_id}")

    elif isinstance(event, ToolCallStartedEvent):
        print(f"Tool: {event.tool.tool_name}")
        print(f"Args: {event.tool.tool_args}")

    elif isinstance(event, ToolCallCompletedEvent):
        print(f"Result: {event.tool.result}")

    elif isinstance(event, RunContentEvent):
        print(f"Content: {event.content}")

    elif isinstance(event, RunCompletedEvent):
        print(f"Run completed")
```

---

## Monitoring Metrics

Access detailed metrics about agent execution.

### Run Metrics

```python
from agno.agent import Agent, RunOutput
from agno.models.openai import OpenAIChat
from rich.pretty import pprint

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    markdown=True,
)

response: RunOutput = agent.run("Tell me a joke")

# Access metrics
if response.metrics:
    print(f"Input tokens: {response.metrics.input_tokens}")
    print(f"Output tokens: {response.metrics.output_tokens}")
    print(f"Total tokens: {response.metrics.total_tokens}")
    print(f"Duration: {response.metrics.duration:.2f}s")
    print(f"Time to first token: {response.metrics.time_to_first_token:.2f}s")

    # Pretty print all metrics
    pprint(response.metrics.to_dict())
```

---

### Available Metrics

**Token metrics:**
- `input_tokens` - Tokens sent to model
- `output_tokens` - Tokens received from model
- `total_tokens` - Sum of input and output
- `cache_read_tokens` - Tokens read from cache
- `cache_write_tokens` - Tokens written to cache
- `reasoning_tokens` - Tokens used for reasoning (if applicable)

**Audio metrics (multimodal):**
- `audio_input_tokens` - Audio tokens sent
- `audio_output_tokens` - Audio tokens received
- `audio_total_tokens` - Sum of audio tokens

**Performance metrics:**
- `duration` - Total execution time (seconds)
- `time_to_first_token` - Latency to first token (seconds)

**Provider metrics:**
- `provider_metrics` - Model provider-specific data

---

### Session Metrics

Aggregated metrics across all runs in a session.

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    db=SqliteDb(db_file="tmp/agent.db"),
)

# Run multiple times
agent.run("First query", session_id="session_123")
agent.run("Second query", session_id="session_123")
agent.run("Third query", session_id="session_123")

# Get aggregated session metrics
session_metrics = agent.get_session_metrics(session_id="session_123")

print(f"Total tokens used: {session_metrics.total_tokens}")
print(f"Total duration: {session_metrics.duration:.2f}s")
```

---

## Inspecting Tool Calls

Debug mode shows all tool executions.

### Tool Call Information

```python
response: RunOutput = agent.run("What is the weather?", debug_mode=True)

# Access tool calls from response
if response.tools:
    for tool_call in response.tools:
        print(f"Tool: {tool_call.tool_name}")
        print(f"Arguments: {tool_call.tool_args}")
        print(f"Result: {tool_call.result}")
        print(f"Success: {tool_call.success}")
        if tool_call.error:
            print(f"Error: {tool_call.error}")
```

---

### Debug Output Example

```
DEBUG | Tool Call Started:
  tool_name: duckduckgo_search
  tool_args: {"query": "weather Tokyo", "max_results": 5}

DEBUG | Tool Execution:
  Status: Running
  Duration: 1.2s

DEBUG | Tool Call Completed:
  Status: Success
  Result: [5 search results returned]

DEBUG | Tool Error (if failed):
  Error: Connection timeout
  Traceback: ...
```

---

## Troubleshooting Common Issues

### Agent Not Responding

**Check:**
```python
# 1. Verify agent configuration
print(f"Model: {agent.model}")
print(f"Tools: {agent.tools}")

# 2. Enable debug mode
response = agent.run("Test", debug_mode=True)

# 3. Check for errors
print(f"Status: {response.status}")
if response.status == "error":
    print(f"Error: {response.content}")
```

---

### Tool Not Being Called

**Debug:**
```python
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[MyTool()],
    debug_mode=True,  # See if model tries to call tool
)

response = agent.run("Query that should use tool")

# Check if tool was registered
print(f"Available tools: {[t.name for t in agent.tools]}")

# Check tool call attempts
if response.tools:
    print(f"Tools called: {len(response.tools)}")
else:
    print("No tools were called - check instructions")
```

**Common causes:**
- Instructions don't mention tool usage
- Tool description unclear
- Tool name not intuitive
- Model doesn't think tool is needed

---

### High Token Usage

**Monitor:**
```python
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    debug_mode=True,
)

response = agent.run("Query")

print(f"Input tokens: {response.metrics.input_tokens}")
print(f"Output tokens: {response.metrics.output_tokens}")

# Check message sizes
for msg in response.messages:
    if hasattr(msg, 'content'):
        print(f"{msg.role}: {len(str(msg.content))} chars")
```

**Reduce tokens:**
- Shorter instructions
- Limit history runs: `num_history_runs=3`
- Fewer tools registered
- More focused knowledge base

---

### Slow Response Times

**Measure:**
```python
response = agent.run("Query", debug_mode=True)

print(f"Total duration: {response.metrics.duration:.2f}s")
print(f"Time to first token: {response.metrics.time_to_first_token:.2f}s")

# Check tool execution time
if response.tools:
    for tool in response.tools:
        print(f"{tool.tool_name}: {tool.duration:.2f}s")
```

**Optimize:**
- Use faster models (gpt-5-mini vs gpt-4o)
- Reduce context size
- Optimize slow tools
- Enable streaming for better UX

---

## Best Practices

### 1. Use Debug Mode in Development

**Development:**
```python
agent = Agent(
    model=model,
    debug_mode=True,  # Always on in dev
    debug_level=2,    # Verbose
)
```

**Production:**
```python
agent = Agent(
    model=model,
    debug_mode=False,  # Off in production
)
```

---

### 2. Test with CLI App

```python
# Quick testing during development
agent.cli_app(stream=True)

# Interactive conversations
# See how agent handles multi-turn dialogue
# Test edge cases interactively
```

---

### 3. Monitor Metrics

```python
# Always capture metrics in production
response = agent.run("Query")

# Log important metrics
logger.info(f"Run {response.run_id}")
logger.info(f"Tokens: {response.metrics.total_tokens}")
logger.info(f"Duration: {response.metrics.duration}s")
logger.info(f"Status: {response.status}")
```

---

### 4. Stream Intermediate Steps for Complex Tasks

```python
# When debugging complex agent behavior
stream = agent.run(
    "Complex task",
    stream=True,
    stream_events=True,  # See all steps
    debug_mode=True,     # Full details
)

for event in stream:
    # Monitor agent's decision-making process
    pprint(event.to_dict())
```

---

### 5. Test Error Handling

```python
# Simulate tool failures
def failing_tool():
    raise Exception("Tool error")

agent = Agent(
    model=model,
    tools=[FailingTool()],
    debug_mode=True,  # See error details
)

response = agent.run("Use failing tool")

# Verify error handling
assert response.status == "error"
assert "Tool error" in response.content
```

---

### 6. Debug Tool Issues

```python
from agno.tools import Toolkit

class MyTool(Toolkit):
    def my_function(self, param: str) -> str:
        """Clear description of what this tool does"""
        # Add logging inside tools
        print(f"Tool called with: {param}")
        result = process(param)
        print(f"Tool returning: {result}")
        return result

agent = Agent(
    model=model,
    tools=[MyTool()],
    debug_mode=True,
)

# See tool execution in detail
agent.run("Use my tool")
```

---

### 7. Compare Runs

```python
# Run without debug
response1 = agent.run("Query", debug_mode=False)
print(f"Without debug: {response1.metrics.duration}s")

# Run with debug
response2 = agent.run("Query", debug_mode=True)
print(f"With debug: {response2.metrics.duration}s")

# Debug adds minimal overhead (~5-10%)
```

---

## Summary

### Debug Mode Methods

**Agent-level:**
```python
Agent(debug_mode=True, debug_level=2)
```

**Run-level:**
```python
agent.run("Query", debug_mode=True)
```

**Environment:**
```bash
export AGNO_DEBUG=True
```

---

### Interactive Testing

```python
# Terminal CLI app
agent.cli_app(stream=True)

# Custom configuration
agent.cli_app(
    user="Dev",
    emoji="🔧",
    stream=True,
)
```

---

### Metrics & Monitoring

```python
response = agent.run("Query")

# Run metrics
print(response.metrics.total_tokens)
print(response.metrics.duration)

# Session metrics
session_metrics = agent.get_session_metrics()
```

---

### Streaming Events

```python
stream = agent.run(
    "Query",
    stream=True,
    stream_events=True,
)

for event in stream:
    # Process events
    handle_event(event)
```

---

### Key Features

**Inspect:**
- Messages sent to model
- Model responses
- Tool calls and results
- Errors and exceptions

**Monitor:**
- Token usage
- Execution time
- Tool performance
- Session metrics

**Test:**
- Interactive CLI
- Multi-turn conversations
- Edge cases
- Error scenarios

---

## Related Documentation

**AGNO Official:**
- [Debugging Agents](https://docs.agno.com/basics/agents/debugging-agents)
- [Agent Metrics](https://docs.agno.com/basics/sessions/metrics/agent)
- [Debug Level](https://docs.agno.com/basics/agents/usage/debug-level)
- [Intermediate Steps](https://docs.agno.com/basics/agents/usage/intermediate-steps)

**Next Topics:**
- 04-basic-usage.md
- 05-async-usage.md
- 06-streaming.md

---

**AGNO Documentation:** https://docs.agno.com
**Version:** 1.0
