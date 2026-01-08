# Conditional and Parallel Workflow Patterns

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/workflow-patterns/conditional-workflow

---

## Introduction

This document covers two powerful workflow patterns:

1. **Conditional Workflows** - Execute steps based on evaluator functions
2. **Parallel Workflows** - Execute independent steps concurrently

These patterns can be combined for sophisticated automation.

---

## Part 1: Conditional Workflows

Execute steps conditionally based on content analysis or business logic.

### Core Concept

```python
from agno.workflow.condition import Condition

Condition(
    name="condition_name",
    evaluator=my_evaluator_function,  # Returns True/False
    steps=[step_to_run_if_true],
)
```

### How It Works

1. Evaluator function receives `StepInput`
2. Returns `True` → Execute the steps
3. Returns `False` → Skip the steps

---

### Basic Conditional Example

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.condition import Condition
from agno.workflow.types import StepInput
from agno.tools.duckduckgo import DuckDuckGoTools

# Define agents
researcher = Agent(
    name="Researcher",
    instructions="Research the topic thoroughly.",
    tools=[DuckDuckGoTools()],
)

summarizer = Agent(
    name="Summarizer",
    instructions="Create a clear summary of findings.",
)

fact_checker = Agent(
    name="Fact Checker",
    instructions="Verify facts and claims.",
    tools=[DuckDuckGoTools()],
)

writer = Agent(
    name="Writer",
    instructions="Write comprehensive articles.",
)

# Define evaluator function
def needs_fact_checking(step_input: StepInput) -> bool:
    """Determine if content needs fact-checking"""
    summary = step_input.previous_step_content or ""

    # Keywords suggesting factual claims
    fact_indicators = [
        "study shows",
        "research indicates",
        "according to",
        "statistics",
        "data shows",
        "survey",
        "report",
        "million",
        "billion",
        "percent",
        "%",
        "increase",
        "decrease",
    ]

    return any(indicator in summary.lower() for indicator in fact_indicators)

# Define steps
research_step = Step(name="research", agent=researcher)
summarize_step = Step(name="summarize", agent=summarizer)
fact_check_step = Step(name="fact_check", agent=fact_checker)
write_step = Step(name="write_article", agent=writer)

# Build workflow with condition
workflow = Workflow(
    name="Article Pipeline with Fact Checking",
    description="Research -> Summarize -> Condition(Fact Check) -> Write",
    steps=[
        research_step,
        summarize_step,
        Condition(
            name="fact_check_condition",
            description="Check if fact-checking is needed",
            evaluator=needs_fact_checking,
            steps=[fact_check_step],
        ),
        write_step,
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Recent breakthroughs in quantum computing",
        stream=True,
    )
```

---

### Multiple Conditions

Use multiple conditions for different checks:

```python
def is_technical_topic(step_input: StepInput) -> bool:
    """Check if topic is technical"""
    content = step_input.input or ""
    tech_keywords = ["ai", "software", "programming", "tech", "algorithm"]
    return any(kw in content.lower() for kw in tech_keywords)

def is_business_topic(step_input: StepInput) -> bool:
    """Check if topic is business-related"""
    content = step_input.input or ""
    biz_keywords = ["market", "revenue", "strategy", "investment", "growth"]
    return any(kw in content.lower() for kw in biz_keywords)

workflow = Workflow(
    name="Multi-Condition Pipeline",
    steps=[
        research_step,
        Condition(
            name="tech_condition",
            evaluator=is_technical_topic,
            steps=[tech_expert_step],
        ),
        Condition(
            name="business_condition",
            evaluator=is_business_topic,
            steps=[business_analyst_step],
        ),
        final_writer_step,
    ],
)
```

---

### Condition with Multiple Steps

Execute multiple steps when condition is true:

```python
Condition(
    name="deep_analysis_condition",
    evaluator=needs_deep_analysis,
    steps=[
        data_collection_step,
        analysis_step,
        validation_step,
    ],
)
```

---

### When to Use Conditions

| Use Case | Example |
|----------|---------|
| **Quality Gates** | Fact-check if statistics detected |
| **Content Routing** | Add technical review for tech topics |
| **Validation** | Verify data before processing |
| **Adaptive Processing** | Different handling based on content type |

---

## Part 2: Parallel Workflows

Execute independent steps concurrently for improved performance.

### Core Concept

```python
from agno.workflow import Parallel

Parallel(
    step1,
    step2,
    step3,
    name="Parallel Phase",
    description="Execute steps concurrently",
)
```

### How It Works

1. All steps in Parallel run simultaneously
2. Outputs are joined together
3. Next step receives combined output

---

### Basic Parallel Example

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step, Parallel
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

# Create agents for parallel research
researcher = Agent(
    name="Researcher",
    tools=[HackerNewsTools(), DuckDuckGoTools()],
)

writer = Agent(name="Writer")
reviewer = Agent(name="Reviewer")

# Create individual steps
research_hn_step = Step(
    name="Research HackerNews",
    agent=researcher,
    description="Research from HackerNews",
)

research_web_step = Step(
    name="Research Web",
    agent=researcher,
    description="Research from web sources",
)

write_step = Step(name="Write Article", agent=writer)
review_step = Step(name="Review Article", agent=reviewer)

# Build workflow with parallel execution
workflow = Workflow(
    name="Content Creation Pipeline",
    steps=[
        Parallel(
            research_hn_step,
            research_web_step,
            name="Research Phase",
            description="Parallel multi-source research",
        ),
        write_step,
        review_step,
    ],
)

workflow.print_response("Write about the latest AI developments")
```

---

### Multi-Source Research Pattern

```python
from agno.tools.exa import ExaTools
from agno.tools.tavily import TavilyTools

# Specialized agents for different sources
hackernews_agent = Agent(
    name="HN Researcher",
    tools=[HackerNewsTools()],
    instructions="Extract tech insights from HackerNews",
)

web_agent = Agent(
    name="Web Researcher",
    tools=[DuckDuckGoTools()],
    instructions="Find general web information",
)

exa_agent = Agent(
    name="Exa Researcher",
    tools=[ExaTools()],
    instructions="Semantic search for deep content",
)

# Parallel research from all sources
workflow = Workflow(
    name="Comprehensive Research Pipeline",
    steps=[
        Parallel(
            Step(name="HN Research", agent=hackernews_agent),
            Step(name="Web Research", agent=web_agent),
            Step(name="Exa Research", agent=exa_agent),
            name="Multi-Source Research",
        ),
        Step(name="Synthesis", agent=synthesis_agent),
        Step(name="Final Report", agent=report_agent),
    ],
)
```

---

### When to Use Parallel

| Use Case | Example |
|----------|---------|
| **Multi-Source Research** | Query multiple search engines |
| **Independent Analysis** | Technical + Business analysis |
| **Data Collection** | Gather from multiple APIs |
| **Performance** | Reduce total execution time |

---

## Combining Condition and Parallel

### Parallel Conditions

Run multiple conditions simultaneously:

```python
from agno.workflow import Workflow, Step, Parallel
from agno.workflow.condition import Condition
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.exa import ExaTools
from agno.tools.hackernews import HackerNewsTools

# Agents
hackernews_agent = Agent(
    name="HN Researcher",
    instructions="Research tech topics from HackerNews",
    tools=[HackerNewsTools()],
)

web_agent = Agent(
    name="Web Researcher",
    instructions="Research general information",
    tools=[DuckDuckGoTools()],
)

exa_agent = Agent(
    name="Exa Researcher",
    instructions="Advanced semantic search",
    tools=[ExaTools()],
)

content_agent = Agent(
    name="Content Creator",
    instructions="Create well-structured content",
)

# Condition evaluators
def should_search_hn(step_input: StepInput) -> bool:
    topic = step_input.input or ""
    tech_keywords = ["ai", "programming", "software", "tech", "startup"]
    return any(kw in topic.lower() for kw in tech_keywords)

def should_search_web(step_input: StepInput) -> bool:
    topic = step_input.input or ""
    general_keywords = ["news", "information", "research", "facts"]
    return any(kw in topic.lower() for kw in general_keywords)

def should_search_exa(step_input: StepInput) -> bool:
    topic = step_input.input or ""
    deep_keywords = ["deep", "academic", "comprehensive", "analysis"]
    return any(kw in topic.lower() for kw in deep_keywords)

# Steps
research_hn_step = Step(name="HN Research", agent=hackernews_agent)
research_web_step = Step(name="Web Research", agent=web_agent)
research_exa_step = Step(name="Exa Research", agent=exa_agent)
content_step = Step(name="Create Content", agent=content_agent)

# Workflow with parallel conditions
workflow = Workflow(
    name="Conditional Research Workflow",
    steps=[
        Parallel(
            Condition(
                name="HN Condition",
                description="Search HN for tech topics",
                evaluator=should_search_hn,
                steps=[research_hn_step],
            ),
            Condition(
                name="Web Condition",
                description="Search web for general info",
                evaluator=should_search_web,
                steps=[research_web_step],
            ),
            Condition(
                name="Exa Condition",
                description="Use Exa for deep analysis",
                evaluator=should_search_exa,
                steps=[research_exa_step],
            ),
            name="Conditional Research",
            description="Run conditional searches in parallel",
        ),
        content_step,
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Latest AI developments in machine learning",
        stream=True,
    )
```

---

### Condition Inside Parallel Steps

```python
workflow = Workflow(
    name="Complex Pipeline",
    steps=[
        initial_research_step,
        Parallel(
            Condition(
                name="tech_path",
                evaluator=is_tech_topic,
                steps=[tech_analysis_step],
            ),
            Condition(
                name="business_path",
                evaluator=is_business_topic,
                steps=[market_analysis_step],
            ),
            name="Parallel Analysis",
        ),
        synthesis_step,
    ],
)
```

---

## Accessing Run Context in Evaluators

Use session state in condition evaluators:

```python
from agno.run import RunContext
from agno.workflow.types import StepInput

def smart_evaluator(step_input: StepInput, run_context: RunContext) -> bool:
    """Evaluator with access to session state"""

    # Access session state
    user_tier = run_context.session_state.get("user_tier", "free")

    # Premium users get fact-checking
    if user_tier == "premium":
        return True

    # Free users only for claims
    content = step_input.previous_step_content or ""
    return "according to" in content.lower()

condition = Condition(
    name="smart_fact_check",
    evaluator=smart_evaluator,
    steps=[fact_check_step],
)
```

---

## Streaming with Conditions and Parallel

Handle events from conditional and parallel execution:

```python
from agno.run.workflow import WorkflowRunEvent

async def process_workflow():
    response = workflow.arun(
        input="AI market analysis",
        stream=True,
        stream_events=True,
    )

    async for event in response:
        match event.event:
            case WorkflowRunEvent.condition_execution_started.value:
                print(f"Condition starting: {event.step_id}")

            case WorkflowRunEvent.condition_execution_completed.value:
                print(f"Condition done: {event.step_id}")

            case WorkflowRunEvent.parallel_execution_started.value:
                print("Parallel execution starting...")

            case WorkflowRunEvent.parallel_execution_completed.value:
                print("Parallel execution complete!")

            case WorkflowRunEvent.step_started.value:
                print(f"  Step: {event.step_id}")

            case _:
                if event.content:
                    print(event.content, end="")
```

---

## Best Practices

### Conditions

1. **Keep evaluators simple** - Fast boolean logic
2. **Use descriptive names** - Clear condition purpose
3. **Handle edge cases** - Check for None/empty content
4. **Log decisions** - Add print statements for debugging

### Parallel

1. **Use for independent tasks** - No dependencies between steps
2. **Consider rate limits** - Multiple API calls simultaneously
3. **Name phases clearly** - "Research Phase", "Analysis Phase"
4. **Combine outputs carefully** - Next step gets joined results

### Combined Patterns

1. **Test conditions first** - Verify evaluators work correctly
2. **Monitor performance** - Parallel should be faster
3. **Handle partial failures** - Some parallel steps may fail
4. **Use streaming** - See progress in real-time

---

## Summary

| Pattern | Purpose | Key Class |
|---------|---------|-----------|
| **Condition** | Execute steps if evaluator returns True | `Condition` |
| **Parallel** | Execute independent steps concurrently | `Parallel` |
| **Combined** | Parallel conditions for adaptive processing | Both |

---

## Related Documentation

- **Basic Patterns:** `docs(new)/workflows/04-basic-patterns.md`
- **Iterative/Branching:** `docs(new)/workflows/06-iterative-branching.md`
- **Advanced Patterns:** `docs(new)/workflows/07-grouped-advanced.md`

---

*Last Updated: December 2025 | AGNO 2.3.4*
