# AGNO Intermediate Steps Documentation

> **Source:** https://docs.agno.com/basics/agents/usage/intermediate-steps
> **Last Updated:** 2025-11-29

---

## What Are Intermediate Steps?

Intermediate steps provide visibility into what happens BETWEEN a user's question and the agent's final answer. Instead of treating the agent as a black box, you can observe every action: tool calls, reasoning processes, and execution flow.

**Analogy:** Like watching a cooking show instead of just receiving your meal at a restaurant.

**Use Cases:**
- Debug agent behavior when things go wrong
- Build transparent UIs showing agent activity
- Monitor reasoning for complex problem-solving
- Log all actions for audit/compliance
- Improve user trust through visibility

---

## Relationship to Run Response Events

**They're the same mechanism!**

| Term | Meaning |
|------|---------|
| **Intermediate Steps** | The CONCEPT - seeing the in-between work |
| **Run Response Events** | The MECHANISM - the actual events you stream |

The documentation uses "intermediate steps" to explain WHY you'd want visibility, and "run response events" for HOW to access it technically.

**See also:** [12-run-response-events.md](./12-run-response-events.md)

---

## Basic Usage

### Without Intermediate Steps (Black Box)

```python
# Just get the final answer
response = agent.run("What's NVDA stock price?")
print(response.content)  # "NVIDIA is trading at $142.50"
```

### With Intermediate Steps (Full Visibility)

```python
from typing import Iterator
from agno.agent import Agent, RunOutputEvent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from rich.pretty import pprint

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[DuckDuckGoTools()],
)

# Stream with events to see intermediate steps
run_stream: Iterator[RunOutputEvent] = agent.run(
    "What is the stock price of NVDA",
    stream=True,
    stream_events=True
)

for chunk in run_stream:
    pprint(chunk.to_dict())
```

**Output shows every step:**
```python
{"event": "RunStarted", "run_id": "abc123", ...}
{"event": "ToolCallStarted", "tool_name": "get_stock_price", "args": {"symbol": "NVDA"}}
{"event": "ToolCallCompleted", "tool_name": "get_stock_price", "result": "$142.50"}
{"event": "RunContent", "content": "NVIDIA (NVDA) is currently..."}
{"event": "RunCompleted", ...}
```

---

## Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `stream=True` | bool | Enable streaming (don't wait for complete response) |
| `stream_events=True` | bool | Include ALL events (tools, reasoning), not just content |
| `debug_mode=True` | bool | Extra detailed logging for development |
| `show_full_reasoning=True` | bool | Display reasoning steps in terminal output |
| `stream_intermediate_steps=True` | bool | Stream reasoning steps in real-time (with Reasoning Agents) |

---

## What You Can See

### 1. Tool Execution

```python
for event in agent.run(message, stream=True, stream_events=True):
    if event.event == "ToolCallStarted":
        print(f"Starting: {event.tool.tool_name}")
        print(f"Args: {event.tool.tool_args}")
    elif event.event == "ToolCallCompleted":
        print(f"Result: {event.tool.result}")
```

### 2. Reasoning Steps (with Reasoning Tools/Agents)

```python
from agno.tools.reasoning import ReasoningTools

agent = Agent(
    model=model,
    tools=[ReasoningTools()],
    show_full_reasoning=True,  # Display in terminal
)
```

Shows:
- Each reasoning step with title and action
- Why the agent chose each approach
- Tool calls made during reasoning
- Validation checks performed
- Confidence scores (0.0-1.0)
- Self-corrections if errors detected

### 3. Metrics and Performance

```python
for event in agent.run(message, stream=True, stream_events=True):
    if event.event == "RunCompleted":
        metrics = event.metrics
        print(f"Tokens used: {metrics.get('total_tokens')}")
        print(f"Time: {metrics.get('time_to_first_token')}")
```

---

## Debug Mode

For development, enable comprehensive debugging:

```python
agent = Agent(
    model=model,
    tools=[...],
    debug_mode=True,      # Enable debug output
    debug_level=2,        # More detailed logs (optional)
)

# Or per-run
agent.run(message, debug_mode=True)

# Or via environment
# AGNO_DEBUG=true python my_agent.py
```

**Debug mode shows:**
- Messages sent to the model
- Model responses
- Token usage and timing
- Tool calls, errors, and results
- Intermediate execution steps

---

## Practical Examples

### Example 1: Progress Indicator for UI

```python
async def stream_with_progress(message: str):
    async for event in agent.arun(message, stream=True, stream_events=True):
        if event.event == "ToolCallStarted":
            yield {"type": "progress", "message": f"Using {event.tool.tool_name}..."}
        elif event.event == "RunContent":
            yield {"type": "content", "text": event.content}
        elif event.event == "RunCompleted":
            yield {"type": "done"}
```

### Example 2: Logging for Debugging

```python
import logging

logger = logging.getLogger("agent")

for event in agent.run(message, stream=True, stream_events=True):
    logger.debug(f"Event: {event.event}")

    if event.event == "ToolCallStarted":
        logger.info(f"Tool: {event.tool.tool_name}({event.tool.tool_args})")
    elif event.event == "ToolCallCompleted":
        logger.info(f"Result: {event.tool.result[:100]}...")  # First 100 chars
    elif event.event == "RunError":
        logger.error(f"Error: {event.error}")
```

### Example 3: Audit Trail

```python
audit_log = []

for event in agent.run(message, stream=True, stream_events=True):
    audit_log.append({
        "timestamp": datetime.now().isoformat(),
        "event_type": event.event,
        "data": event.to_dict()
    })

# Save to database for compliance
save_audit_log(audit_log)
```

---

## Image Generation Example

Intermediate steps are especially useful for long-running operations like image generation:

```python
from agno.tools.dalle import DalleTools

image_agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[DalleTools()],
    markdown=True,
)

for event in image_agent.run(
    "Create an image of a sunset over mountains",
    stream=True,
    stream_events=True
):
    if event.event == "ToolCallStarted":
        print("Generating image...")  # Show user something is happening
    elif event.event == "ToolCallCompleted":
        print(f"Image ready: {event.tool.result}")
    elif event.event == "RunContent":
        print(event.content)
```

---

## Teams Intermediate Steps

For teams, use `stream_member_events=True` to see what each member does:

```python
for event in team.run(
    message,
    stream=True,
    stream_events=True,
    stream_member_events=True  # See individual agent activity
):
    agent_id = getattr(event, 'agent_id', None)
    if agent_id:
        print(f"[{agent_id}] {event.event}")
```

---

## Best Practices

### 1. Use for Development, Consider for Production

```python
# Development: full visibility
agent.run(message, stream=True, stream_events=True, debug_mode=True)

# Production: stream content only (less overhead)
agent.run(message, stream=True)

# Production with UI indicators: stream events without debug
agent.run(message, stream=True, stream_events=True)
```

### 2. Handle Events Gracefully

```python
for event in agent.run(message, stream=True, stream_events=True):
    try:
        process_event(event)
    except Exception as e:
        logger.warning(f"Failed to process event {event.event}: {e}")
        # Continue processing other events
```

### 3. Don't Block on Every Event

```python
# Good: Batch or filter events
important_events = ["ToolCallStarted", "ToolCallCompleted", "RunError"]

for event in agent.run(message, stream=True, stream_events=True):
    if event.event in important_events:
        process_important_event(event)
```

---

## Summary

| Feature | How to Enable | What You See |
|---------|--------------|--------------|
| Basic streaming | `stream=True` | Content chunks only |
| Full events | `stream=True, stream_events=True` | All events (tools, content, etc.) |
| Team member events | `+ stream_member_events=True` | Events from each team member |
| Debug logging | `debug_mode=True` | Detailed console output |
| Reasoning visibility | `show_full_reasoning=True` | Reasoning steps in terminal |

**Key Insight:** Intermediate steps let you see the agent's "thinking" process. Essential for debugging, great for UX, and required for compliance/audit scenarios.
