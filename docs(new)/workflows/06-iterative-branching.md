# Iterative and Branching Workflow Patterns

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/workflow-patterns/iterative-workflow

---

## Introduction

This document covers two advanced workflow patterns:

1. **Iterative Workflows (Loop)** - Repeat steps until a condition is met
2. **Branching Workflows (Router)** - Dynamic path selection based on input

---

## Part 1: Iterative Workflows (Loop)

Execute steps repeatedly until quality thresholds are met.

### Core Concept

```python
from agno.workflow import Loop

Loop(
    name="loop_name",
    steps=[step1, step2],
    end_condition=my_evaluator,  # Returns True to exit
    max_iterations=3,            # Safety limit
)
```

### How It Works

1. Execute all steps in the loop
2. Call `end_condition` with outputs
3. If `True` → Exit loop, continue workflow
4. If `False` → Repeat (until `max_iterations`)

---

### Basic Loop Example

```python
from typing import List
from agno.agent import Agent
from agno.workflow import Workflow, Step, Loop
from agno.workflow.types import StepOutput
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

# Research agents
research_agent = Agent(
    name="Research Agent",
    tools=[HackerNewsTools(), DuckDuckGoTools()],
    instructions="Research the topic thoroughly.",
    markdown=True,
)

content_agent = Agent(
    name="Content Agent",
    instructions="Create engaging content based on research.",
    markdown=True,
)

# Research steps
research_hn_step = Step(
    name="Research HackerNews",
    agent=research_agent,
    description="Research from HackerNews",
)

research_web_step = Step(
    name="Research Web",
    agent=research_agent,
    description="Research from web sources",
)

content_step = Step(
    name="Create Content",
    agent=content_agent,
    description="Create final content",
)


# End condition function
def research_evaluator(outputs: List[StepOutput]) -> bool:
    """
    Evaluate if research is sufficient.
    Returns True to exit loop, False to continue.
    """
    if not outputs:
        return False

    # Check if any output has substantial content
    for output in outputs:
        if output.content and len(output.content) > 200:
            print(f"Research sufficient: {len(output.content)} chars")
            return True

    print("Research insufficient - continuing loop")
    return False


# Build workflow with loop
workflow = Workflow(
    name="Research and Content Workflow",
    description="Research in loop until quality met",
    steps=[
        Loop(
            name="Research Loop",
            steps=[research_hn_step, research_web_step],
            end_condition=research_evaluator,
            max_iterations=3,
        ),
        content_step,
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Research AI and machine learning trends",
    )
```

---

### Quality-Based Loop

```python
def quality_check(outputs: List[StepOutput]) -> bool:
    """Exit when quality score is high enough"""
    if not outputs:
        return False

    # Calculate quality metrics
    total_length = sum(len(o.content or "") for o in outputs)
    has_sources = any("http" in (o.content or "") for o in outputs)
    has_data = any(char.isdigit() for o in outputs for char in (o.content or ""))

    # Quality threshold
    if total_length > 500 and has_sources and has_data:
        print("Quality threshold met!")
        return True

    print(f"Quality check: length={total_length}, sources={has_sources}, data={has_data}")
    return False
```

---

### Loop with Parallel Steps

Combine Loop with Parallel for iterative multi-source research:

```python
from agno.workflow import Workflow, Step, Loop, Parallel

# Create analysis steps
trend_analysis_step = Step(
    name="Trend Analysis",
    agent=analysis_agent,
    description="Analyze trending patterns",
)

sentiment_analysis_step = Step(
    name="Sentiment Analysis",
    agent=analysis_agent,
    description="Analyze sentiment and opinions",
)

# End condition
def comprehensive_evaluator(outputs: List[StepOutput]) -> bool:
    """Check if research is comprehensive"""
    if not outputs:
        return False

    total_length = sum(len(o.content or "") for o in outputs)

    if total_length > 500:
        print(f"Comprehensive research: {total_length} chars")
        return True

    print(f"Need more research: {total_length} chars")
    return False


# Workflow with loop containing parallel steps
workflow = Workflow(
    name="Advanced Research Workflow",
    description="Parallel research in loop until comprehensive",
    steps=[
        Loop(
            name="Research Loop with Parallel",
            steps=[
                Parallel(
                    research_hn_step,
                    research_web_step,
                    trend_analysis_step,
                    name="Parallel Research & Analysis",
                ),
                sentiment_analysis_step,
            ],
            end_condition=comprehensive_evaluator,
            max_iterations=3,
        ),
        content_step,
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Research AI trends and create summary",
        stream=True,
    )
```

---

### Loop Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Loop identifier |
| `steps` | `List` | Steps to execute each iteration |
| `end_condition` | `Callable` | Function returning True to exit |
| `max_iterations` | `int` | Maximum loop iterations (safety) |
| `description` | `str` | Loop description |

---

### When to Use Loops

| Use Case | Example |
|----------|---------|
| **Quality Assurance** | Research until content is substantial |
| **Data Collection** | Gather until threshold met |
| **Iterative Refinement** | Improve output each iteration |
| **Retry Logic** | Retry until success |

---

## Part 2: Branching Workflows (Router)

Dynamic path selection based on input analysis.

### Core Concept

```python
from agno.workflow.router import Router

Router(
    name="router_name",
    selector=my_selector_function,  # Returns List[Step]
    choices=[step1, step2, step3],  # Available paths
)
```

### How It Works

1. Selector function receives `StepInput`
2. Returns list of steps to execute
3. Only selected steps run
4. Workflow continues to next step

---

### Basic Router Example

```python
from typing import List
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.router import Router
from agno.workflow.types import StepInput
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

# Specialized research agents
hackernews_agent = Agent(
    name="HackerNews Researcher",
    instructions="Research tech news from HackerNews",
    tools=[HackerNewsTools()],
)

web_agent = Agent(
    name="Web Researcher",
    instructions="Research general web information",
    tools=[DuckDuckGoTools()],
)

content_agent = Agent(
    name="Content Publisher",
    instructions="Create engaging, well-structured articles",
)

# Research steps
research_hn = Step(
    name="research_hackernews",
    agent=hackernews_agent,
    description="Research from HackerNews",
)

research_web = Step(
    name="research_web",
    agent=web_agent,
    description="General web research",
)

publish_content = Step(
    name="publish_content",
    agent=content_agent,
    description="Create final content",
)


# Router selector function
def research_strategy_router(step_input: StepInput) -> List[Step]:
    """Select research strategy based on topic"""
    topic = step_input.input or ""
    topic = topic.lower()

    # Deep tech keywords
    deep_tech_keywords = [
        "ai developments",
        "machine learning",
        "programming languages",
        "developer tools",
        "startup trends",
        "tech industry",
        "software engineering",
    ]

    # Check topic type
    if any(keyword in topic for keyword in deep_tech_keywords):
        print(f"Deep tech topic: Using HackerNews research")
        return [research_hn]
    else:
        print(f"General topic: Using web research")
        return [research_web]


# Build workflow with router
workflow = Workflow(
    name="Adaptive Research Workflow",
    description="Selects research strategy based on topic",
    steps=[
        Router(
            name="research_strategy_router",
            selector=research_strategy_router,
            choices=[research_hn, research_web],
            description="Choose research approach",
        ),
        publish_content,
    ],
)

if __name__ == "__main__":
    print("=== Testing with tech topic ===")
    workflow.print_response("Latest AI developments in machine learning")

    print("\n=== Testing with general topic ===")
    workflow.print_response("Best practices for project management")
```

---

### Multi-Path Router

Route to multiple steps based on topic:

```python
def multi_path_selector(step_input: StepInput) -> List[Step]:
    """Select multiple research paths"""
    topic = step_input.input or ""
    topic = topic.lower()

    selected_steps = []

    # Check for tech content
    if any(kw in topic for kw in ["tech", "ai", "software"]):
        selected_steps.append(tech_research_step)

    # Check for business content
    if any(kw in topic for kw in ["market", "business", "revenue"]):
        selected_steps.append(business_research_step)

    # Check for academic content
    if any(kw in topic for kw in ["research", "study", "academic"]):
        selected_steps.append(academic_research_step)

    # Default to general research if nothing matched
    if not selected_steps:
        selected_steps.append(general_research_step)

    print(f"Selected {len(selected_steps)} research paths")
    return selected_steps
```

---

### Router with Loop

Combine Router with Loop for adaptive iterative processing:

```python
from agno.workflow import Workflow, Step, Loop
from agno.workflow.router import Router

# Create a Loop step for deep tech research
deep_tech_research_loop = Loop(
    name="Deep Tech Research Loop",
    steps=[research_hn],
    end_condition=research_quality_check,
    max_iterations=3,
    description="Iterative deep research on tech topics",
)


def research_strategy_with_loop(step_input: StepInput) -> List[Step]:
    """Route to simple or iterative research"""
    topic = step_input.input or ""
    topic = topic.lower()

    # Complex tech topics get iterative research
    complex_indicators = [
        "comprehensive",
        "deep analysis",
        "detailed research",
        "thorough investigation",
    ]

    if any(indicator in topic for indicator in complex_indicators):
        print("Complex topic: Using iterative research loop")
        return [deep_tech_research_loop]
    else:
        print("Simple topic: Using single research pass")
        return [research_web]


workflow = Workflow(
    name="Adaptive Research with Loop",
    description="Routes between simple and iterative research",
    steps=[
        Router(
            name="research_router",
            selector=research_strategy_with_loop,
            choices=[research_web, deep_tech_research_loop],
        ),
        publish_content,
    ],
)
```

---

### Accessing Session State in Router

```python
from agno.run import RunContext

def stateful_router(step_input: StepInput, run_context: RunContext) -> List[Step]:
    """Router with access to session state"""

    # Check user preferences from state
    user_pref = run_context.session_state.get("research_preference", "balanced")

    if user_pref == "deep":
        return [deep_research_step, analysis_step]
    elif user_pref == "quick":
        return [quick_research_step]
    else:
        return [balanced_research_step]
```

---

### Router Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Router identifier |
| `selector` | `Callable` | Function returning `List[Step]` |
| `choices` | `List[Step]` | Available step options |
| `description` | `str` | Router description |

---

### When to Use Router

| Use Case | Example |
|----------|---------|
| **Topic-Based Routing** | Tech vs business vs general |
| **User Preferences** | Premium vs free tier processing |
| **Complexity Handling** | Simple vs complex analysis paths |
| **A/B Testing** | Route to different strategies |

---

## Combining Loop and Router

### Router Inside Loop

```python
workflow = Workflow(
    name="Iterative Adaptive Pipeline",
    steps=[
        Loop(
            name="Adaptive Research Loop",
            steps=[
                Router(
                    name="strategy_router",
                    selector=select_strategy,
                    choices=[fast_research, deep_research],
                ),
                validation_step,
            ],
            end_condition=quality_met,
            max_iterations=3,
        ),
        final_step,
    ],
)
```

### Router to Loop or Direct

```python
def complexity_router(step_input: StepInput) -> List[Step]:
    """Route to loop or direct path based on complexity"""
    topic = step_input.input or ""

    if "comprehensive" in topic.lower():
        # Complex: Use iterative approach
        return [research_loop]
    else:
        # Simple: Direct path
        return [quick_research_step]

workflow = Workflow(
    name="Complexity-Aware Workflow",
    steps=[
        Router(
            name="complexity_router",
            selector=complexity_router,
            choices=[research_loop, quick_research_step],
        ),
        synthesis_step,
    ],
)
```

---

## Streaming Events

Handle Loop and Router events in streaming:

```python
from agno.run.workflow import WorkflowRunEvent

async def process_workflow():
    response = workflow.arun(
        input="Complex AI research",
        stream=True,
        stream_events=True,
    )

    async for event in response:
        match event.event:
            case WorkflowRunEvent.loop_iteration_started.value:
                print(f"Loop iteration starting...")

            case WorkflowRunEvent.loop_iteration_completed.value:
                print(f"Loop iteration done")

            case WorkflowRunEvent.router_execution_started.value:
                print(f"Router evaluating...")

            case WorkflowRunEvent.router_execution_completed.value:
                print(f"Router selected path")

            case WorkflowRunEvent.step_started.value:
                print(f"  Step: {event.step_id}")

            case _:
                if event.content:
                    print(event.content, end="")
```

---

## Best Practices

### Loops

1. **Always set max_iterations** - Prevent infinite loops
2. **Log end_condition results** - Debug iteration decisions
3. **Return True to exit** - Remember the logic direction
4. **Handle empty outputs** - Check for None/empty lists

### Routers

1. **Have a default path** - Handle unmatched cases
2. **Keep selectors fast** - Avoid heavy computation
3. **Log selected paths** - Debug routing decisions
4. **Use descriptive names** - Clear step identification

### Combined Patterns

1. **Test each component** - Verify loops and routers separately
2. **Monitor iterations** - Watch for excessive looping
3. **Handle timeouts** - Long loops may need limits
4. **Use streaming** - See progress in real-time

---

## Summary

| Pattern | Purpose | Key Class |
|---------|---------|-----------|
| **Loop** | Repeat until condition met | `Loop` |
| **Router** | Dynamic path selection | `Router` |
| **Combined** | Adaptive iterative processing | Both |

---

## Related Documentation

- **Conditional/Parallel:** `docs(new)/workflows/05-conditional-parallel.md`
- **Basic Patterns:** `docs(new)/workflows/04-basic-patterns.md`
- **Advanced Patterns:** `docs(new)/workflows/07-grouped-advanced.md`

---

*Last Updated: December 2025 | AGNO 2.3.4*
