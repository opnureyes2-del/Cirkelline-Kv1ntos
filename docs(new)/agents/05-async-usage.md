# Async Usage in AGNO

**Last Updated**: 2025-11-26
**AGNO Version**: 2.1.1+

## Overview

AGNO provides full async/await support for building non-blocking AI agent systems. Async operations enable concurrent execution, improved performance, and better resource utilization when running multiple agents or handling I/O-bound operations.

**Key Benefits**:
- Non-blocking agent execution
- Concurrent multi-agent workflows
- Better performance for I/O-bound operations
- Seamless integration with async frameworks (FastAPI, aiohttp, etc.)
- Real-time streaming with async iterators

---

## Table of Contents

1. [Basic Async Patterns](#basic-async-patterns)
2. [Async Methods](#async-methods)
3. [Async Streaming](#async-streaming)
4. [Concurrent Agent Execution](#concurrent-agent-execution)
5. [Async Teams](#async-teams)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)
8. [Real-World Examples](#real-world-examples)

---

## Basic Async Patterns

### Simple Async Agent

```python
import asyncio
from agno import Agent
from agno.models.openai import OpenAIChat

agent = Agent(model=OpenAIChat(id="gpt-4o-mini"))

async def main():
    response = await agent.arun(input="Tell me a joke.")
    print(response.content)

asyncio.run(main())
```

**How It Works**:
1. Define agent with standard configuration
2. Create async function with `async def`
3. Use `await` with `agent.arun()` for non-blocking execution
4. Run with `asyncio.run()` entry point

### Quick Response with aprint_response

```python
import asyncio
from agno import Agent
from agno.models.openai import OpenAIChat

agent = Agent(model=OpenAIChat(id="gpt-4o-mini"), markdown=True)

async def main():
    # Directly prints response without manual handling
    await agent.aprint_response("What is quantum computing?")

asyncio.run(main())
```

**When to Use**:
- `arun()`: When you need the response object for processing
- `aprint_response()`: When you just want to display output immediately

---

## Async Methods

### Core Async Methods

| Method | Returns | Use Case |
|--------|---------|----------|
| `arun(input, stream=False)` | `RunResponse` | Get response object for processing |
| `aprint_response(input, stream=False)` | `None` | Direct output display |
| `arun(input, stream=True)` | `AsyncIterator[RunResponse]` | Stream response chunks |
| `aprint_response(input, stream=True)` | `None` | Stream and print chunks |

### Method Comparison

```python
import asyncio
from agno import Agent
from agno.models.openai import OpenAIChat

agent = Agent(model=OpenAIChat(id="gpt-4o-mini"))

async def compare_methods():
    # Method 1: arun() - Get response object
    response = await agent.arun(input="Explain AI in one sentence.")
    print(f"Content: {response.content}")
    print(f"Model: {response.model}")
    print(f"Metrics: {response.metrics}")

    # Method 2: aprint_response() - Direct display
    await agent.aprint_response("Explain AI in one sentence.")

asyncio.run(compare_methods())
```

### Accessing Response Data

```python
async def process_response():
    response = await agent.arun(input="List 3 programming languages.")

    # Access content
    print(response.content)

    # Access metadata
    if response.metrics:
        print(f"Time: {response.metrics.get('time_to_first_token')}s")
        print(f"Tokens: {response.metrics.get('output_tokens')}")

    # Access messages
    for message in response.messages:
        print(f"{message.role}: {message.content}")

asyncio.run(process_response())
```

---

## Async Streaming

### Basic Async Streaming

```python
import asyncio
from agno import Agent
from agno.models.openai import OpenAIChat

agent = Agent(model=OpenAIChat(id="gpt-4o-mini"), markdown=True)

async def stream_response():
    # Method 1: Using aprint_response (simplest)
    await agent.aprint_response(
        "Write a short story about AI.",
        stream=True
    )

asyncio.run(stream_response())
```

### Manual Stream Processing

```python
import asyncio
from agno import Agent
from agno.models.openai import OpenAIChat

agent = Agent(model=OpenAIChat(id="gpt-4o-mini"))

async def process_stream():
    # Get async iterator
    stream = await agent.arun(
        input="Explain machine learning step by step.",
        stream=True
    )

    # Process chunks as they arrive
    async for chunk in stream:
        if chunk.content:
            print(chunk.content, end="", flush=True)

    print()  # Newline after stream completes

asyncio.run(process_stream())
```

### Stream with Pretty Printing Utility

```python
import asyncio
from agno import Agent
from agno.models.openai import OpenAIChat
from agno.utils.pprint import apprint_run_response

agent = Agent(model=OpenAIChat(id="gpt-4o-mini"), markdown=True)

async def pretty_stream():
    # apprint_run_response handles formatting and display
    await apprint_run_response(
        agent.arun(input="Describe neural networks.", stream=True)
    )

asyncio.run(pretty_stream())
```

### Collecting Stream Data

```python
async def collect_stream():
    stream = await agent.arun(
        input="List 5 AI applications.",
        stream=True
    )

    full_content = ""
    chunk_count = 0

    async for chunk in stream:
        if chunk.content:
            full_content += chunk.content
            chunk_count += 1

            # Optional: Process each chunk
            if chunk_count % 10 == 0:
                print(f"Received {chunk_count} chunks...")

    print(f"\nTotal chunks: {chunk_count}")
    print(f"Full content length: {len(full_content)} chars")

asyncio.run(collect_stream())
```

---

## Concurrent Agent Execution

### Running Multiple Agents Concurrently

```python
import asyncio
from agno import Agent
from agno.models.openai import OpenAIChat

# Create specialized agents
researcher = Agent(
    name="Researcher",
    model=OpenAIChat(id="gpt-4o"),
    role="Research and find information"
)

writer = Agent(
    name="Writer",
    model=OpenAIChat(id="gpt-4o"),
    role="Write clear, engaging content"
)

analyst = Agent(
    name="Analyst",
    model=OpenAIChat(id="gpt-4o"),
    role="Analyze data and provide insights"
)

async def concurrent_execution():
    # Run all agents concurrently
    results = await asyncio.gather(
        researcher.arun(input="Find latest AI trends"),
        writer.arun(input="Write about quantum computing"),
        analyst.arun(input="Analyze tech stock performance")
    )

    # Process results
    for i, response in enumerate(results):
        print(f"\nAgent {i+1} Response:")
        print(response.content[:200] + "...")

asyncio.run(concurrent_execution())
```

### Concurrent Execution with Individual Error Handling

```python
async def safe_concurrent_execution():
    # Create tasks with error handling
    tasks = [
        researcher.arun(input="Research topic A"),
        writer.arun(input="Write about topic B"),
        analyst.arun(input="Analyze data C")
    ]

    # Use return_exceptions=True to handle errors gracefully
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results and handle errors
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Agent {i+1} failed: {result}")
        else:
            print(f"Agent {i+1} succeeded: {result.content[:100]}...")

asyncio.run(safe_concurrent_execution())
```

### Sequential vs Concurrent Performance

```python
import asyncio
import time

async def sequential_execution():
    """Execute agents one after another."""
    start = time.time()

    r1 = await agent.arun(input="Task 1")
    r2 = await agent.arun(input="Task 2")
    r3 = await agent.arun(input="Task 3")

    elapsed = time.time() - start
    print(f"Sequential: {elapsed:.2f}s")

async def concurrent_execution():
    """Execute agents simultaneously."""
    start = time.time()

    results = await asyncio.gather(
        agent.arun(input="Task 1"),
        agent.arun(input="Task 2"),
        agent.arun(input="Task 3")
    )

    elapsed = time.time() - start
    print(f"Concurrent: {elapsed:.2f}s")

# Compare performance
asyncio.run(sequential_execution())   # ~30 seconds (3 x 10s each)
asyncio.run(concurrent_execution())   # ~10 seconds (all parallel)
```

---

## Async Teams

### Basic Async Team

```python
import asyncio
from agno import Agent, Team
from agno.models.openai import OpenAIChat
from agno.tools.exa import ExaTools

# Create team members
searcher = Agent(
    name="Web Searcher",
    model=OpenAIChat(id="gpt-4o-mini"),
    role="Search the web for information",
    tools=[ExaTools()]
)

analyst = Agent(
    name="Analyst",
    model=OpenAIChat(id="gpt-4o-mini"),
    role="Analyze and synthesize information"
)

# Create team
research_team = Team(
    name="Research Team",
    model=OpenAIChat(id="gpt-4o"),
    members=[searcher, analyst],
    markdown=True,
    show_members_responses=True
)

async def run_team():
    response = await research_team.arun(
        input="What are the latest developments in quantum computing?"
    )
    print(response.content)

asyncio.run(run_team())
```

### Async Team with Streaming

```python
import asyncio
from agno.utils.pprint import apprint_run_response

async def stream_team_response():
    # Stream team coordination and member responses
    await apprint_run_response(
        research_team.arun(
            input="Analyze NVIDIA's stock performance this year.",
            stream=True
        )
    )

asyncio.run(stream_team_response())
```

### Concurrent Team Execution

```python
async def multiple_teams():
    # Create multiple specialized teams
    research_team = Team(name="Research Team", members=[...])
    analysis_team = Team(name="Analysis Team", members=[...])
    writing_team = Team(name="Writing Team", members=[...])

    # Run teams concurrently
    results = await asyncio.gather(
        research_team.arun(input="Research AI trends"),
        analysis_team.arun(input="Analyze market data"),
        writing_team.arun(input="Write summary report")
    )

    # Combine results
    final_report = "\n\n".join([r.content for r in results])
    print(final_report)

asyncio.run(multiple_teams())
```

---

## Error Handling

### Basic Try-Except

```python
async def handle_errors():
    try:
        response = await agent.arun(input="Complex query...")
        print(response.content)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(handle_errors())
```

### Retry Logic with Exponential Backoff

```python
import asyncio

async def retry_with_backoff(agent, input_text, max_retries=3):
    """Retry agent execution with exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = await agent.arun(input=input_text)
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            wait_time = 2 ** attempt  # 1s, 2s, 4s
            print(f"Attempt {attempt + 1} failed: {e}")
            print(f"Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)

async def main():
    response = await retry_with_backoff(
        agent,
        "Explain quantum entanglement"
    )
    print(response.content)

asyncio.run(main())
```

### Timeout Handling

```python
async def with_timeout():
    try:
        # Set 30-second timeout
        response = await asyncio.wait_for(
            agent.arun(input="Long-running query..."),
            timeout=30.0
        )
        print(response.content)
    except asyncio.TimeoutError:
        print("Request timed out after 30 seconds")

asyncio.run(with_timeout())
```

### Graceful Degradation

```python
async def graceful_degradation():
    """Try primary agent, fallback to backup if it fails."""
    primary_agent = Agent(model=OpenAIChat(id="gpt-4o"))
    backup_agent = Agent(model=OpenAIChat(id="gpt-4o-mini"))

    try:
        response = await primary_agent.arun(input="Complex query")
    except Exception as e:
        print(f"Primary failed ({e}), using backup...")
        response = await backup_agent.arun(input="Complex query")

    return response

asyncio.run(graceful_degradation())
```

---

## Best Practices

### 1. Use asyncio.gather for Concurrent Execution

```python
# ✅ GOOD: Run independent tasks concurrently
async def good_concurrent():
    results = await asyncio.gather(
        agent1.arun(input="Task 1"),
        agent2.arun(input="Task 2"),
        agent3.arun(input="Task 3")
    )

# ❌ BAD: Sequential execution when tasks are independent
async def bad_sequential():
    r1 = await agent1.arun(input="Task 1")
    r2 = await agent2.arun(input="Task 2")
    r3 = await agent3.arun(input="Task 3")
```

### 2. Always Handle Exceptions

```python
# ✅ GOOD: Proper error handling
async def good_error_handling():
    try:
        response = await agent.arun(input="Query")
        return response.content
    except Exception as e:
        logger.error(f"Agent failed: {e}")
        return "Error occurred"

# ❌ BAD: No error handling
async def bad_no_error_handling():
    response = await agent.arun(input="Query")
    return response.content  # Will crash on error
```

### 3. Use Streaming for Long Responses

```python
# ✅ GOOD: Stream long responses for better UX
async def good_streaming():
    await agent.aprint_response(
        "Write a detailed essay on AI ethics.",
        stream=True
    )

# ❌ BAD: Wait for entire response
async def bad_no_streaming():
    response = await agent.arun(
        input="Write a detailed essay on AI ethics."
    )
    print(response.content)  # User waits with no feedback
```

### 4. Set Timeouts for Critical Operations

```python
# ✅ GOOD: Timeout prevents hanging
async def good_with_timeout():
    try:
        response = await asyncio.wait_for(
            agent.arun(input="Query"),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        return "Request timed out"

# ❌ BAD: No timeout, could hang indefinitely
async def bad_no_timeout():
    response = await agent.arun(input="Query")
```

### 5. Clean Up Resources

```python
# ✅ GOOD: Proper cleanup
async def good_cleanup():
    try:
        response = await agent.arun(input="Query")
        return response
    finally:
        # Clean up resources
        await agent.cleanup()  # If available

# ❌ BAD: No cleanup
async def bad_no_cleanup():
    response = await agent.arun(input="Query")
    return response
```

---

## Real-World Examples

### FastAPI Integration

```python
from fastapi import FastAPI, BackgroundTasks
from agno import Agent
from agno.models.openai import OpenAIChat

app = FastAPI()
agent = Agent(model=OpenAIChat(id="gpt-4o-mini"))

@app.post("/ask")
async def ask_agent(question: str):
    """Async endpoint for agent queries."""
    response = await agent.arun(input=question)
    return {"answer": response.content}

@app.post("/ask/stream")
async def ask_agent_stream(question: str):
    """Streaming endpoint."""
    from fastapi.responses import StreamingResponse

    async def generate():
        stream = await agent.arun(input=question, stream=True)
        async for chunk in stream:
            if chunk.content:
                yield chunk.content

    return StreamingResponse(generate(), media_type="text/plain")
```

### Background Task Processing

```python
import asyncio
from typing import List

async def process_batch(inputs: List[str]):
    """Process multiple queries in background."""
    tasks = [agent.arun(input=query) for query in inputs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]

    return {
        "successful": len(successful),
        "failed": len(failed),
        "results": [r.content for r in successful]
    }

# Usage in FastAPI
@app.post("/batch")
async def batch_process(background_tasks: BackgroundTasks, queries: List[str]):
    background_tasks.add_task(process_batch, queries)
    return {"status": "processing", "count": len(queries)}
```

### Multi-Agent Workflow

```python
async def research_workflow(topic: str):
    """Complex multi-agent research workflow."""

    # Step 1: Research (concurrent)
    research_results = await asyncio.gather(
        web_searcher.arun(input=f"Find latest info on {topic}"),
        academic_searcher.arun(input=f"Find papers on {topic}"),
        news_searcher.arun(input=f"Find recent news on {topic}")
    )

    # Step 2: Analyze combined results
    analysis = await analyst.arun(
        input=f"Analyze this research: {research_results}"
    )

    # Step 3: Generate report
    report = await writer.arun(
        input=f"Write comprehensive report: {analysis.content}"
    )

    return report.content

# Execute workflow
result = asyncio.run(research_workflow("quantum computing"))
```

---

## Summary

**Async AGNO enables**:
- ✅ Non-blocking agent execution
- ✅ Concurrent multi-agent workflows
- ✅ Real-time streaming responses
- ✅ Integration with async frameworks (FastAPI, etc.)
- ✅ Better resource utilization

**Key Methods**:
- `arun()` - Get response object
- `aprint_response()` - Direct output
- Both support `stream=True` for streaming

**Best Practices**:
1. Use `asyncio.gather()` for concurrent execution
2. Always handle exceptions with try-except
3. Set timeouts for critical operations
4. Stream long responses for better UX
5. Use `return_exceptions=True` in gather for graceful degradation

**Next Steps**:
- Read [06-streaming.md](./06-streaming.md) for advanced streaming patterns
- Read [07-teams.md](./07-teams.md) for team coordination patterns
- Check [Real-World Examples](../examples/) for production patterns
