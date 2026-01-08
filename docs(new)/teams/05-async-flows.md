# Async Flows

**AGNO Version:** 2.2.13
**Source:** https://docs.agno.com/basics/teams/usage/async-flows/

---

## Overview

Async flows enable non-blocking team execution for production applications. This document bundles:
- Basic Team (Async)
- Basic Streaming (Async)
- Stream Events (Async)
- Respond Directly (Async)
- Delegate to All Members (Async)

**Key difference from basic flows:** All methods use `await` and async patterns.

---

## 1. Basic Team (Async)

Asynchronous team coordination for non-blocking research tasks.

### Example

```python
import asyncio
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.tools.hackernews import HackerNewsTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.newspaper4k import Newspaper4kTools
from pydantic import BaseModel
from typing import List

class Article(BaseModel):
    title: str
    summary: str
    reference_links: List[str]

# Specialized agents
hn_researcher = Agent(
    name="HackerNews Researcher",
    model=OpenAIChat("gpt-4o-mini"),
    role="Find and analyze HackerNews posts",
    tools=[HackerNewsTools()],
)

web_searcher = Agent(
    name="Web Searcher",
    model=OpenAIChat("gpt-4o-mini"),
    role="Search web for topic information",
    tools=[DuckDuckGoTools()],
)

article_reader = Agent(
    name="Article Reader",
    model=OpenAIChat("gpt-4o-mini"),
    role="Read and extract content from URLs",
    tools=[Newspaper4kTools()],
)

# Team configuration
hn_team = Team(
    name="Research Team",
    model=OpenAIChat("gpt-4o"),
    members=[hn_researcher, web_searcher, article_reader],
    response_model=Article,
    show_members_responses=True,
    instructions=[
        "Search HackerNews for user-requested topics",
        "Have article reader extract content from links",
        "Use web searcher for supplementary information",
        "Provide comprehensive summary with citations",
    ],
)

# Async execution
async def main():
    await hn_team.aprint_response(
        "Write an article about the top 2 stories on hackernews"
    )

asyncio.run(main())
```

### Key Methods

| Sync Method | Async Equivalent |
|-------------|------------------|
| `team.run()` | `await team.arun()` |
| `team.print_response()` | `await team.aprint_response()` |

---

## 2. Basic Streaming (Async)

Real-time streaming with async/await patterns.

### Example

```python
import asyncio
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.tools.exa import ExaTools

stock_searcher = Agent(
    name="Stock Searcher",
    model=OpenAIChat(id="gpt-4o-mini"),
    role="Search for stock information",
    tools=[ExaTools(
        include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"]
    )],
)

company_info_agent = Agent(
    name="Company Info Searcher",
    model=OpenAIChat(id="gpt-4o-mini"),
    role="Gather company-specific information",
    tools=[ExaTools(
        include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"]
    )],
)

team = Team(
    name="Stock Research Team",
    model=OpenAIChat(id="gpt-4o-mini"),
    members=[stock_searcher, company_info_agent],
    markdown=True,
    show_members_responses=True,
)

# Method 1: Using arun() with streaming
async def streaming_with_arun():
    async for chunk in team.arun(
        "What is the current stock price of NVDA?",
        stream=True,
    ):
        print(chunk.content, end="", flush=True)

# Method 2: Using aprint_response()
async def streaming_with_aprint_response():
    await team.aprint_response(
        "What is the current stock price of NVDA?",
        stream=True,
    )

asyncio.run(streaming_with_arun())
```

### Streaming Patterns

| Pattern | Use Case |
|---------|----------|
| `async for chunk in team.arun(..., stream=True)` | Custom chunk processing |
| `await team.aprint_response(..., stream=True)` | Direct terminal output |

---

## 3. Stream Events (Async)

Monitor detailed execution events asynchronously.

### Event Types

| Event | Description |
|-------|-------------|
| `TeamRunEvent.run_started` | Team execution begins |
| `TeamRunEvent.run_completed` | Team execution finishes |
| `TeamRunEvent.tool_call_started` | Team-level tool starts |
| `TeamRunEvent.tool_call_completed` | Team-level tool finishes |
| `RunEvent.tool_call_started` | Member tool starts |
| `RunEvent.tool_call_completed` | Member tool finishes |
| `TeamRunEvent.run_content` | Content being generated |

### Example

```python
import asyncio
from agno.agent import Agent
from agno.team import Team
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.tools.hackernews import HackerNewsTools
from agno.tools.duckduckgo import DuckDuckGoTools

hn_agent = Agent(
    name="Hacker News Agent",
    model=OpenAIChat("gpt-4o-mini"),
    tools=[HackerNewsTools()],
)

web_agent = Agent(
    name="Website Agent",
    model=OpenAIChat("gpt-4o-mini"),
    tools=[DuckDuckGoTools()],
)

company_info_team = Team(
    name="Company Info Team",
    model=Claude("claude-sonnet-4-20250514"),
    members=[hn_agent, web_agent],
)

async def monitor_events():
    prompt = "Tell me about OpenAI"

    async for event in company_info_team.arun(
        prompt,
        stream=True,
        stream_events=True,
    ):
        # Team-level events
        if event.event == "run_started":
            print("\n>>> Team execution started")

        elif event.event == "run_completed":
            print("\n>>> Team execution completed")

        elif event.event == "tool_call_started":
            print(f"\n>>> Tool starting: {event.tool_name}")
            print(f"    Arguments: {event.tool_args}")

        elif event.event == "tool_call_completed":
            print(f"\n>>> Tool completed: {event.tool_name}")
            if hasattr(event, 'tool_result'):
                result_preview = str(event.tool_result)[:100]
                print(f"    Result preview: {result_preview}...")

        elif event.event == "run_content":
            print(event.content, end="", flush=True)

        # Member-level events (nested)
        elif hasattr(event, 'member_name'):
            print(f"\n  [Member: {event.member_name}] {event.event}")

asyncio.run(monitor_events())
```

### Use Cases

- **Debugging**: Track exactly what agents are doing
- **Monitoring**: Observe tool usage patterns in production
- **Logging**: Create detailed execution logs
- **UI Updates**: Show real-time progress to users
- **Performance**: Measure tool execution times

---

## 4. Respond Directly (Async)

Async routing where selected member responds without leader synthesis.

### Example: Multi-Language Router

```python
import asyncio
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat

# Language-specific agents
english_agent = Agent(
    name="English Agent",
    role="You only answer in English",
    model=OpenAIChat(id="gpt-4o-mini"),
)

japanese_agent = Agent(
    name="Japanese Agent",
    role="You only answer in Japanese",
    model=OpenAIChat(id="gpt-4o-mini"),
)

chinese_agent = Agent(
    name="Chinese Agent",
    role="You only answer in Chinese",
    model=OpenAIChat(id="gpt-4o-mini"),
)

spanish_agent = Agent(
    name="Spanish Agent",
    role="You only answer in Spanish",
    model=OpenAIChat(id="gpt-4o-mini"),
)

french_agent = Agent(
    name="French Agent",
    role="You only answer in French",
    model=OpenAIChat(id="gpt-4o-mini"),
)

german_agent = Agent(
    name="German Agent",
    role="You only answer in German",
    model=OpenAIChat(id="gpt-4o-mini"),
)

# Router team
multi_language_team = Team(
    name="Multi Language Team",
    model=OpenAIChat("gpt-4o-mini"),
    respond_directly=True,  # Member responds directly!
    members=[
        english_agent,
        japanese_agent,
        chinese_agent,
        spanish_agent,
        french_agent,
        german_agent,
    ],
    markdown=True,
    instructions=[
        "Route questions to appropriate language agent",
        "For unsupported languages, respond in English",
        "Check input language before routing",
    ],
    show_members_responses=True,
)

async def main():
    # French input -> Routes to French Agent
    await multi_language_team.aprint_response(
        "Bonjour, comment ça va?",
        stream=True,
    )

    # German input -> Routes to German Agent
    await multi_language_team.aprint_response(
        "Wie geht es dir?",
        stream=True,
    )

    # Unsupported (Italian) -> Responds with supported languages
    await multi_language_team.aprint_response(
        "Ciao, come stai?",
        stream=True,
    )

asyncio.run(main())
```

### Flow Comparison

```
Without respond_directly:
User → Leader → Member → Leader → User
       (routes)  (works)  (synthesizes)

With respond_directly=True:
User → Leader → Member → User
       (routes)  (responds directly)
```

### When to Use

| Scenario | respond_directly? |
|----------|-------------------|
| Language routing | Yes |
| Specialized handlers | Yes |
| Need synthesis | No |
| Multiple perspectives | No |

---

## 5. Delegate to All Members (Async)

Async parallel execution where all members get the same task.

### Example: Cross-Platform Research

```python
import asyncio
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

reddit_researcher = Agent(
    name="Reddit Researcher",
    model=OpenAIChat("gpt-4o-mini"),
    role="Find and analyze Reddit posts",
    tools=[DuckDuckGoTools()],
    instructions=[
        "Search for Reddit discussions on the topic",
        "Analyze sentiment and key opinions",
        "Provide summary of Reddit perspective",
    ],
)

hackernews_researcher = Agent(
    name="HackerNews Researcher",
    model=OpenAIChat("gpt-4o-mini"),
    role="Find and analyze HackerNews posts",
    tools=[HackerNewsTools()],
    instructions=[
        "Search HackerNews for relevant posts",
        "Analyze technical discussions",
        "Provide summary of HN perspective",
    ],
)

# Collaborative team
discussion_team = Team(
    name="Discussion Team",
    model=OpenAIChat("gpt-4o-mini"),
    members=[reddit_researcher, hackernews_researcher],
    delegate_to_all_members=True,  # All get same task!
    show_members_responses=True,
    markdown=True,
    instructions=[
        "Assign research task to all members",
        "Let members discuss their findings",
        "Stop discussion when consensus is reached",
        "Synthesize final answer from all perspectives",
    ],
)

async def main():
    await discussion_team.aprint_response(
        "What do developers think about AI code assistants?",
        stream=True,
    )

asyncio.run(main())
```

### Execution Flow

```
1. User submits query
2. Leader assigns SAME task to ALL members (parallel)
3. All members work simultaneously
4. Members share findings
5. Discussion until consensus
6. Leader synthesizes final response
```

### Use Cases

| Use Case | Why Delegate to All? |
|----------|---------------------|
| Cross-platform research | Different sources, same question |
| Multiple perspectives | Diverse viewpoints needed |
| Consensus building | Agreement from multiple agents |
| Validation | Cross-check information |

---

## Quick Reference

### Async Methods

| Method | Description |
|--------|-------------|
| `await team.arun(prompt)` | Async run, returns response |
| `await team.arun(prompt, stream=True)` | Async streaming generator |
| `await team.arun(prompt, stream=True, stream_events=True)` | Async with events |
| `await team.aprint_response(prompt)` | Async print to terminal |
| `await team.aprint_response(prompt, stream=True)` | Async streaming print |

### Async Patterns

```python
import asyncio

# Pattern 1: Simple async call
async def simple():
    response = await team.arun("Query")
    print(response.content)

# Pattern 2: Streaming chunks
async def streaming():
    async for chunk in team.arun("Query", stream=True):
        print(chunk.content, end="", flush=True)

# Pattern 3: Event monitoring
async def events():
    async for event in team.arun("Query", stream=True, stream_events=True):
        if event.event == "run_content":
            print(event.content, end="", flush=True)

# Pattern 4: Direct print
async def direct_print():
    await team.aprint_response("Query", stream=True)

# Run any pattern
asyncio.run(simple())
```

### Parameter Summary

| Parameter | Default | Description |
|-----------|---------|-------------|
| `stream` | `False` | Enable streaming output |
| `stream_events` | `False` | Enable event monitoring |
| `respond_directly` | `False` | Skip leader synthesis |
| `delegate_to_all_members` | `False` | All members get same task |
| `show_members_responses` | `False` | Display member outputs |

---

## Summary

| Flow | Async Method | Key Feature |
|------|--------------|-------------|
| Basic Team | `await team.arun()` | Non-blocking execution |
| Streaming | `async for chunk in team.arun(..., stream=True)` | Real-time output |
| Events | `async for event in team.arun(..., stream_events=True)` | Execution monitoring |
| Respond Direct | `respond_directly=True` | Skip synthesis |
| Delegate All | `delegate_to_all_members=True` | Parallel work |

**Key:** All async methods require `await` and must run inside `async def` functions.
