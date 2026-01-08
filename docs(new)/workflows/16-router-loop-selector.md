# Router, Loop, and Selector Patterns

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/usage

---

## Introduction

This documentation covers advanced combination patterns involving Router and Loop constructs, including:

- Router routing to Loop steps
- Selector pattern for media pipelines
- Conversational workflows with conditions
- Complex multi-pattern combinations

---

## Router to Loop Routing

A Router can route to a Loop, enabling dynamic selection between simple execution and iterative processing:

```python
from typing import List
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.router import Router
from agno.workflow.loop import Loop
from agno.workflow.types import StepInput, StepOutput
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

# Research agents
hackernews_agent = Agent(
    name="HackerNews Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[HackerNewsTools()],
    instructions="Research tech trends from Hacker News.",
)

web_agent = Agent(
    name="Web Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Comprehensive web research.",
)

content_agent = Agent(
    name="Content Publisher",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Create engaging, well-structured articles.",
)

# Steps
research_hackernews = Step(
    name="Research HackerNews",
    agent=hackernews_agent,
)

research_web = Step(
    name="Research Web",
    agent=web_agent,
)

publish_content = Step(
    name="Publish",
    agent=content_agent,
)


def research_quality_check(outputs: List[StepOutput]) -> bool:
    """Check if research meets quality threshold"""
    if not outputs:
        return False
    for output in outputs:
        if output.content and len(output.content) > 300:
            print("✅ Quality check passed")
            return True
    print("❌ Need more research")
    return False


# Create iterative research loop
deep_research_loop = Loop(
    name="Deep Research Loop",
    steps=[research_hackernews],
    end_condition=research_quality_check,
    max_iterations=3,
)


def research_strategy_router(step_input: StepInput) -> str:
    """Route to simple or deep research based on complexity"""
    topic = (step_input.user_input or "").lower()

    deep_keywords = [
        "startup", "ai developments", "machine learning",
        "programming", "blockchain", "tech industry",
    ]

    if any(kw in topic for kw in deep_keywords):
        print("🔬 Deep topic: Using iterative loop")
        return "deep_research"
    else:
        print("🌐 Simple topic: Using web search")
        return "simple_research"


# Workflow with Router to Loop
workflow = Workflow(
    name="Adaptive Research",
    description="Routes to simple or iterative research based on topic",
    steps=[
        Router(
            name="Research Router",
            router=research_strategy_router,
            routes={
                "simple_research": research_web,
                "deep_research": deep_research_loop,  # Route to Loop!
            },
        ),
        publish_content,
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        "Latest developments in artificial intelligence",
    )
```

---

## Router to Loop Flow

```
User Input
    ↓
Router evaluates topic
    ↓
    ├── Simple topic → Single Step → Publish
    │
    └── Complex topic → Loop (iterates until quality) → Publish
```

**Key Points:**
- Router can route to any step type: Step, Loop, Parallel, Condition
- Enables dynamic selection between one-shot and iterative processing
- Loop has its own end_condition independent of Router

---

## Selector Pattern for Media Pipelines

The Selector pattern uses Router with Pydantic models for structured input handling:

```python
from typing import List, Optional
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.router import Router
from agno.workflow.steps import Steps
from agno.workflow.types import StepInput, StepOutput
from agno.model.google import Gemini
from agno.tools.openai import OpenAITools
from pydantic import BaseModel


class MediaRequest(BaseModel):
    """Structured media generation request"""
    topic: str
    content_type: str  # "image" or "video"
    prompt: str
    style: Optional[str] = "realistic"
    duration: Optional[int] = None  # For video
    resolution: Optional[str] = "1024x1024"


# Image pipeline agents
image_generator = Agent(
    name="Image Generator",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[OpenAITools()],
    instructions="Generate images using DALL-E based on prompts.",
)

image_analyzer = Agent(
    name="Image Analyzer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze generated images for quality and relevance.",
)

# Video pipeline agents
video_generator = Agent(
    name="Video Generator",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Generate video content based on prompts.",
)

video_analyzer = Agent(
    name="Video Analyzer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze video content for quality.",
)

# Create pipeline step groups
image_pipeline = Steps(
    name="Image Pipeline",
    steps=[
        Step(name="Generate Image", agent=image_generator),
        Step(name="Analyze Image", agent=image_analyzer),
    ],
)

video_pipeline = Steps(
    name="Video Pipeline",
    steps=[
        Step(name="Generate Video", agent=video_generator),
        Step(name="Analyze Video", agent=video_analyzer),
    ],
)


def media_selector(step_input: StepInput) -> str:
    """Select pipeline based on content type"""
    user_input = (step_input.user_input or "").lower()

    if "video" in user_input:
        return "video"
    elif "image" in user_input:
        return "image"
    else:
        return "image"  # Default to image


# Media workflow with selector
media_workflow = Workflow(
    name="AI Media Generation",
    description="Routes to appropriate media generation pipeline",
    steps=[
        Router(
            name="Media Type Router",
            router=media_selector,
            routes={
                "image": image_pipeline,
                "video": video_pipeline,
            },
        ),
    ],
)

if __name__ == "__main__":
    # Generate image
    media_workflow.print_response(
        "Create an image of a futuristic city at sunset",
    )

    # Generate video
    media_workflow.print_response(
        "Create a video showing ocean waves",
    )
```

---

## Selector Pattern Benefits

| Benefit | Description |
|---------|-------------|
| **Modular Pipelines** | Each media type is a self-contained Steps group |
| **Single Entry Point** | One workflow handles multiple content types |
| **Type Safety** | Pydantic models enforce structured inputs |
| **Easy Extension** | Add new pipelines without changing router |

---

## Conversational Workflow with Conditions

Combine WorkflowAgent with Condition for conversational flows:

```python
import asyncio
from agno.agent import Agent
from agno.workflow import Workflow, Step, WorkflowAgent
from agno.workflow.condition import Condition
from agno.workflow.types import StepInput
from agno.model.google import Gemini
from agno.db.postgres import PostgresDb

db = PostgresDb("postgresql+psycopg://user:pass@localhost/db")

# Story agents
story_writer = Agent(
    name="Story Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write a 100 word story based on the topic.",
)

story_editor = Agent(
    name="Story Editor",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Review and improve story grammar and flow.",
)

story_formatter = Agent(
    name="Story Formatter",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Format story into prologue, body, and epilogue.",
)


def needs_editing(step_input: StepInput) -> bool:
    """Determine if story needs editing"""
    story = step_input.previous_step_content or ""
    word_count = len(story.split())
    has_complex_punctuation = any(p in story for p in ["!", "?", ";", ":"])
    return word_count > 50 or has_complex_punctuation


def add_references(step_input: StepInput) -> str:
    """Add references to story"""
    content = step_input.previous_step_content or ""
    return f"{content}\n\nReferences: https://docs.agno.com"


# WorkflowAgent for conversation
workflow_agent = WorkflowAgent(
    model=Gemini(id="gemini-2.5-flash"),
    num_history_runs=4,  # Remember last 4 interactions
)

# Conversational workflow with conditions
story_workflow = Workflow(
    name="Story Generation",
    description="Generate stories with conditional editing",
    agent=workflow_agent,
    db=db,
    steps=[
        Step(name="Write Story", agent=story_writer),
        Condition(
            name="Editing Check",
            evaluator=needs_editing,
            steps=[Step(name="Edit Story", agent=story_editor)],
        ),
        Step(name="Format Story", agent=story_formatter),
        Step(name="Add References", executor=add_references),
    ],
)


async def main():
    # First story
    await story_workflow.aprint_response(
        "Tell me a story about a brave knight",
        stream=True,
    )

    # Follow-up (uses conversation history)
    await story_workflow.aprint_response(
        "What was the knight's name?",
        stream=True,
    )

    # New story
    await story_workflow.aprint_response(
        "Now tell me about a cat",
        stream=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Conversational Flow

```
User: "Tell me a story about a knight"
    ↓
WorkflowAgent decides: Execute workflow
    ↓
Write Story → [Condition: needs editing?]
    ↓                    ↓
    Yes → Edit Story     No → Skip
    ↓                    ↓
    └────────────────────┘
    ↓
Format Story → Add References → Response

User: "What was the knight's name?"
    ↓
WorkflowAgent decides: Answer from history (no workflow execution)
    ↓
Direct answer from session memory
```

---

## Loop with Parallel Research

Complete pattern combining Loop and Parallel:

```python
from typing import List
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.loop import Loop
from agno.workflow.parallel import Parallel
from agno.workflow.types import StepOutput
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

# Research agents
research_agent = Agent(
    name="Research Agent",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[HackerNewsTools(), DuckDuckGoTools()],
    instructions="Research topics thoroughly.",
)

analysis_agent = Agent(
    name="Analysis Agent",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze and summarize research findings.",
)

content_agent = Agent(
    name="Content Agent",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Create engaging content from research.",
)

# Steps
research_hackernews = Step(name="HackerNews", agent=research_agent)
research_web = Step(name="Web Search", agent=research_agent)
trend_analysis = Step(name="Trend Analysis", agent=analysis_agent)
sentiment_analysis = Step(name="Sentiment Analysis", agent=analysis_agent)
create_content = Step(name="Create Content", agent=content_agent)


def research_evaluator(outputs: List[StepOutput]) -> bool:
    """Check if research is comprehensive enough"""
    if not outputs:
        return False

    total_length = sum(len(o.content or "") for o in outputs)

    if total_length > 500:
        print(f"✅ Research complete: {total_length} chars")
        return True

    print(f"❌ Need more research: {total_length} chars")
    return False


# Workflow: Loop with Parallel inside
workflow = Workflow(
    name="Comprehensive Research",
    description="Parallel research in iterative loop until quality met",
    steps=[
        Loop(
            name="Research Loop",
            steps=[
                Parallel(
                    research_hackernews,
                    research_web,
                    trend_analysis,
                    name="Parallel Research",
                ),
                sentiment_analysis,  # Sequential after parallel
            ],
            end_condition=research_evaluator,
            max_iterations=3,
        ),
        create_content,
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        "Research AI and machine learning trends",
        stream=True,
    )
```

---

## Loop with Parallel Flow

```
Iteration 1:
    ┌─────────────────┐
    │ Parallel Block  │
    │ ├── HackerNews  │
    │ ├── Web Search  │  (run concurrently)
    │ └── Trend       │
    └─────────────────┘
           ↓
    Sentiment Analysis
           ↓
    Evaluate: 200 chars → Continue

Iteration 2:
    ┌─────────────────┐
    │ Parallel Block  │
    │ ├── HackerNews  │
    │ ├── Web Search  │  (run concurrently)
    │ └── Trend       │
    └─────────────────┘
           ↓
    Sentiment Analysis
           ↓
    Evaluate: 600 chars → Stop loop
           ↓
    Create Content
```

---

## Complete Multi-Pattern Example

Combining Router, Loop, Parallel, and Condition:

```python
import asyncio
from typing import List
from agno.agent import Agent
from agno.workflow import Workflow, Step, WorkflowAgent
from agno.workflow.router import Router
from agno.workflow.loop import Loop
from agno.workflow.parallel import Parallel
from agno.workflow.condition import Condition
from agno.workflow.types import StepInput, StepOutput
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.db.postgres import PostgresDb

db = PostgresDb("postgresql+psycopg://user:pass@localhost/db")

# Agents
quick_researcher = Agent(
    name="Quick Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Quick web search for facts.",
)

deep_researcher = Agent(
    name="Deep Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Thorough multi-source research.",
)

analyst = Agent(
    name="Analyst",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze research findings.",
)

writer = Agent(
    name="Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write clear, engaging content.",
)

editor = Agent(
    name="Editor",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Edit for clarity and accuracy.",
)


def route_by_complexity(step_input: StepInput) -> str:
    """Route based on query complexity"""
    query = (step_input.user_input or "").lower()

    if any(kw in query for kw in ["comprehensive", "detailed", "analysis"]):
        return "deep"
    else:
        return "quick"


def quality_met(outputs: List[StepOutput]) -> bool:
    """Check if quality threshold reached"""
    if not outputs:
        return False
    last = outputs[-1].content or ""
    return len(last) > 500


def needs_editing(step_input: StepInput) -> bool:
    """Check if content needs editing"""
    content = step_input.previous_step_content or ""
    return len(content.split()) > 100


# Quick path
quick_path = Step(name="Quick Research", agent=quick_researcher)

# Deep path with loop and parallel
deep_path = Loop(
    name="Deep Research Loop",
    steps=[
        Parallel(
            Step(name="Deep Research 1", agent=deep_researcher),
            Step(name="Deep Research 2", agent=deep_researcher),
            name="Parallel Deep Research",
        ),
        Step(name="Analyze", agent=analyst),
    ],
    end_condition=quality_met,
    max_iterations=2,
)


# Full workflow
advanced_workflow = Workflow(
    name="Advanced Research Pipeline",
    description="Routes to quick or deep research with quality assurance",
    agent=WorkflowAgent(model=Gemini(id="gemini-2.5-flash")),
    db=db,
    steps=[
        Router(
            name="Complexity Router",
            router=route_by_complexity,
            routes={
                "quick": quick_path,
                "deep": deep_path,
            },
        ),
        Step(name="Write", agent=writer),
        Condition(
            name="Editing Gate",
            evaluator=needs_editing,
            steps=[Step(name="Edit", agent=editor)],
        ),
    ],
)


async def main():
    # Simple query - quick path
    await advanced_workflow.aprint_response(
        "What is machine learning?",
        stream=True,
    )

    # Complex query - deep path
    await advanced_workflow.aprint_response(
        "Comprehensive analysis of AI trends in 2025",
        stream=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Multi-Pattern Flow

```
User Query
    ↓
Router: Evaluate complexity
    ├── "quick" → Quick Research (single step)
    │
    └── "deep" → Deep Research Loop
                    ├── Parallel research (2 agents)
                    └── Analysis
                    (repeats until quality_met)
    ↓
Writer: Create content
    ↓
Condition: needs_editing?
    ├── Yes → Editor
    └── No → Skip
    ↓
Final Response
```

---

## Pattern Selection Guide

| Use Case | Pattern |
|----------|---------|
| **Topic-based routing** | Router with keyword detection |
| **Quality-driven iteration** | Loop with end_condition |
| **Concurrent processing** | Parallel for independent tasks |
| **Optional processing** | Condition for skip/execute |
| **Media type selection** | Selector with Steps groups |
| **Conversational memory** | WorkflowAgent with num_history_runs |
| **Complex adaptive** | Router → Loop → Parallel |

---

## Best Practices

### Do's

1. **Clear routing logic** - Make router decisions predictable
2. **Reasonable loop limits** - Always set max_iterations
3. **Independent parallel tasks** - Only parallelize independent work
4. **Test all paths** - Verify every route works correctly
5. **Use descriptive names** - Make flow understandable

### Don'ts

1. **Don't over-complicate** - Start simple, add complexity as needed
2. **Don't infinite loop** - Always have reachable end conditions
3. **Don't ignore order** - Remember parallel results arrive unordered
4. **Don't mix concerns** - Keep each pattern focused

---

## Summary

| Pattern | Key Feature |
|---------|-------------|
| **Router → Loop** | Dynamic choice between simple and iterative |
| **Selector** | Route to modular pipeline groups |
| **Conversational + Condition** | History-aware with conditional steps |
| **Loop + Parallel** | Concurrent execution per iteration |
| **Multi-Pattern** | Router → Loop → Parallel → Condition |

---

## Related Documentation

- **Router Patterns:** `docs(new)/workflows/07-grouped-advanced.md`
- **Loop Patterns:** `docs(new)/workflows/06-loops-iterative.md`
- **Conditional Patterns:** `docs(new)/workflows/05-conditional-parallel.md`
- **Advanced Examples:** `docs(new)/workflows/15-advanced-examples.md`

---

*Last Updated: December 2025 | AGNO 2.3.4*
