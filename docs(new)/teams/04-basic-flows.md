# Basic Flows

**AGNO Version:** 2.2.13
**Source:** https://docs.agno.com/basics/teams/usage/basic-flows/

---

## Overview

Basic flows cover the fundamental patterns for running teams and handling their responses. This document bundles:
- Basic Team
- Basic Streaming
- Stream Events
- Response as Variable
- Respond Directly
- Delegate to All Members

---

## 1. Basic Team

A team coordinates specialized agents to accomplish complex tasks.

### Minimal Example

```python
from agno.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.hackernews import HackerNewsTools
from agno.tools.newspaper4k import Newspaper4kTools

# Specialized agents
hn_researcher = Agent(
    name="HackerNews Researcher",
    model=OpenAIChat("gpt-4o-mini"),
    role="Gets top stories from hackernews.",
    tools=[HackerNewsTools()],
)

article_reader = Agent(
    name="Article Reader",
    model=OpenAIChat("gpt-4o-mini"),
    role="Reads articles from URLs.",
    tools=[Newspaper4kTools()],
)

# Team with leader
research_team = Team(
    name="Research Team",
    model=OpenAIChat("gpt-4o-mini"),
    members=[hn_researcher, article_reader],
    instructions=[
        "Search HackerNews for relevant stories",
        "Direct article reader to fetch content",
        "Compile findings into summaries",
    ],
    markdown=True,
)

research_team.print_response("Find the top AI stories on HackerNews")
```

### Structured Output

```python
from pydantic import BaseModel
from typing import List

class ArticleSummary(BaseModel):
    title: str
    summary: str
    reference_links: List[str]

team = Team(
    name="Research Team",
    model=OpenAIChat("gpt-4o-mini"),
    members=[hn_researcher, article_reader],
    response_model=ArticleSummary,  # Enforce output structure
    markdown=True,
)
```

---

## 2. Basic Streaming

Enable real-time response delivery with `stream=True`.

### Example

```python
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.tools.exa import ExaTools

stock_searcher = Agent(
    name="Stock Searcher",
    model=OpenAIChat(id="gpt-4o-mini"),
    role="Searches for stock information",
    tools=[ExaTools(
        include_domains=["cnbc.com", "reuters.com", "bloomberg.com"]
    )],
)

company_info_agent = Agent(
    name="Company Info Searcher",
    model=OpenAIChat(id="gpt-4o-mini"),
    role="Retrieves company background",
    tools=[ExaTools(
        include_domains=["cnbc.com", "reuters.com", "bloomberg.com"]
    )],
)

team = Team(
    name="Stock Research Team",
    model=OpenAIChat(id="gpt-4o-mini"),
    members=[stock_searcher, company_info_agent],
    markdown=True,
    show_members_responses=True,
)

# Stream the response
team.print_response(
    "What is the current stock price of NVDA?",
    stream=True,
)
```

### Key Parameters

| Parameter | Description |
|-----------|-------------|
| `stream=True` | Enable real-time response delivery |
| `markdown=True` | Format output with markdown |
| `show_members_responses=True` | Display each agent's contribution |

### Async Streaming

```python
async def stream_response():
    async for chunk in team.arun("Your question", stream=True):
        print(chunk.content, end="", flush=True)
```

---

## 3. Stream Events

Monitor detailed execution events during team operation.

### Event Types

| Event | Description |
|-------|-------------|
| `run_started` | Team/agent execution begins |
| `run_completed` | Team/agent execution finishes |
| `tool_call_started` | Tool execution begins |
| `tool_call_completed` | Tool execution finishes |
| `run_content` | Content being generated |

### Example

```python
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

# Stream with events
async def monitor_events():
    async for event in company_info_team.arun(
        "Tell me about OpenAI",
        stream=True,
        stream_events=True,
    ):
        if event.event == "run_started":
            print(">>> Team started")
        elif event.event == "run_completed":
            print(">>> Team completed")
        elif event.event == "tool_call_started":
            print(f">>> Tool starting: {event.tool_name}")
            print(f"    Args: {event.tool_args}")
        elif event.event == "tool_call_completed":
            print(f">>> Tool finished: {event.tool_name}")
        elif event.event == "run_content":
            print(event.content, end="", flush=True)
```

### Use Cases

- **Debugging** - Track exactly what agents are doing
- **Monitoring** - Observe tool usage patterns
- **Logging** - Create detailed execution logs
- **UI Updates** - Show progress in real-time

---

## 4. Response as Variable

Capture structured responses using Pydantic models.

### Define Models

```python
from pydantic import BaseModel

class StockAnalysis(BaseModel):
    symbol: str
    company_name: str
    analysis: str

class CompanyAnalysis(BaseModel):
    company_name: str
    analysis: str
```

### Agent with Output Schema

```python
stock_searcher = Agent(
    name="Stock Searcher",
    model=OpenAIChat(id="gpt-4o-mini"),
    role="Search for stock information",
    tools=[ExaTools(
        include_domains=["cnbc.com", "reuters.com", "bloomberg.com"]
    )],
    output_schema=StockAnalysis,  # Enforce structure
)

company_info_agent = Agent(
    name="Company Info Agent",
    model=OpenAIChat(id="gpt-4o-mini"),
    role="Search for company news",
    tools=[ExaTools(
        include_domains=["cnbc.com", "reuters.com", "bloomberg.com"]
    )],
    output_schema=CompanyAnalysis,
)
```

### Team with Routing

```python
team = Team(
    name="Financial Research Team",
    model=OpenAIChat(id="gpt-4o-mini"),
    members=[stock_searcher, company_info_agent],
    respond_directly=True,
    instructions=[
        "Route stock price questions to Stock Searcher",
        "Route company news to Company Info Agent",
    ],
)
```

### Capture Response

```python
# Single query
response = team.run("What is the current stock price of NVDA?")

# Access structured data
print(f"Symbol: {response.content.symbol}")
print(f"Company: {response.content.company_name}")
print(f"Analysis: {response.content.analysis}")

# Batch processing
companies = ["AAPL", "GOOGL", "MSFT"]
responses = []
for company in companies:
    resp = team.run(f"Analyze {company} stock")
    responses.append(resp)
```

### Benefits

| Benefit | Description |
|---------|-------------|
| Type Safety | Pydantic validates response structure |
| IDE Support | Autocomplete for response fields |
| Reliability | Guaranteed response format |
| Integration | Easy to store in databases, APIs |

---

## 5. Respond Directly

With `respond_directly=True`, selected member responds without team leader synthesis.

### Use Case: Multi-Language Router

```python
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
        english_agent, japanese_agent, chinese_agent,
        spanish_agent, french_agent, german_agent,
    ],
    markdown=True,
    instructions=[
        "Route questions to appropriate language agent",
        "For unsupported languages, respond in English",
        "Check input language before routing",
    ],
    show_members_responses=True,
)

await multi_language_team.aprint_response(
    "Bonjour, comment ça va?",
    stream=True,
)
# Routes to French Agent, responds directly in French
```

### How It Works

```
Without respond_directly:
User → Leader → Member → Leader → User
       (routes)  (works)  (synthesizes)

With respond_directly=True:
User → Leader → Member → User
       (routes)  (responds directly)
```

### When to Use

| Scenario | Use respond_directly? |
|----------|----------------------|
| Routing to specialized agents | Yes |
| Language-specific responses | Yes |
| Need team leader synthesis | No |
| Multiple agents collaborate | No |
| Single agent handles entire task | Yes |

---

## 6. Delegate to All Members

With `delegate_to_all_members=True`, all members get the same task simultaneously.

### Use Case: Cooperative Research

```python
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
        "Search for Reddit discussions",
        "Analyze sentiment and opinions",
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

# Discussion team
agent_team = Team(
    name="Discussion Team",
    model=OpenAIChat("gpt-4o-mini"),
    members=[reddit_researcher, hackernews_researcher],
    delegate_to_all_members=True,  # All get same task!
    show_members_responses=True,
    markdown=True,
    instructions=[
        "Assign research task to all members",
        "Let members discuss findings",
        "Stop when consensus is reached",
        "Synthesize final answer",
    ],
)

agent_team.print_response(
    "What do developers think about AI code assistants?"
)
```

### Execution Flow

```
1. User submits query
2. Leader assigns SAME task to ALL members
3. All members work in parallel
4. Members share findings
5. Discussion until consensus
6. Leader synthesizes final response
```

### When to Use

| Scenario | Use delegate_to_all? |
|----------|---------------------|
| Multiple perspectives needed | Yes |
| Cross-platform research | Yes |
| Consensus building | Yes |
| Single specialized task | No |
| Routing to one agent | No |

---

## Quick Reference

### Execution Methods

```python
# Synchronous
team.print_response("Query", stream=False)
response = team.run("Query")

# Asynchronous
await team.aprint_response("Query", stream=True)
response = await team.arun("Query")

# Event streaming
async for event in team.arun("Query", stream=True, stream_events=True):
    process_event(event)
```

### Parameter Comparison

| Parameter | Default | Behavior |
|-----------|---------|----------|
| `stream` | `False` | Real-time output delivery |
| `stream_events` | `False` | Detailed execution events |
| `respond_directly` | `False` | Member bypasses leader synthesis |
| `delegate_to_all_members` | `False` | All members get same task |
| `show_members_responses` | `False` | Display individual agent responses |

### Common Patterns

| Pattern | Configuration |
|---------|---------------|
| Simple coordination | Default settings |
| Real-time output | `stream=True` |
| Event monitoring | `stream=True, stream_events=True` |
| Routing | `respond_directly=True` |
| Collaboration | `delegate_to_all_members=True` |
| Structured output | `response_model=PydanticModel` |

---

## Summary

| Flow | Purpose | Key Parameter |
|------|---------|---------------|
| Basic Team | Coordinate agents | `members=[...]` |
| Streaming | Real-time output | `stream=True` |
| Stream Events | Monitor execution | `stream_events=True` |
| Response Variable | Structured output | `output_schema=Model` |
| Respond Directly | Skip synthesis | `respond_directly=True` |
| Delegate All | Parallel work | `delegate_to_all_members=True` |
