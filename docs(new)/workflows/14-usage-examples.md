# Workflow Usage Examples

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/usage

---

## Introduction

This document provides practical usage examples for common workflow patterns. It focuses on:

1. **Streaming with AgentOS** - Real-time streaming in production
2. **Async Events Streaming** - Processing workflow events asynchronously
3. **Practical Pattern Examples** - Complete working examples

For pattern concepts, see `04-basic-patterns.md` through `07-grouped-advanced.md`.

---

## Streaming with AgentOS

When deploying workflows with AgentOS, custom functions can stream their agent responses directly to the UI.

### Key Concepts

1. Use `async` functions with `AsyncIterator` return type
2. Call agents with `arun(stream=True, stream_events=True)`
3. Yield events to stream them to AgentOS
4. Yield final `StepOutput` when done

---

### Basic Streaming Custom Function

```python
from typing import AsyncIterator, Union
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.db.in_memory import InMemoryDb
from agno.model.google import Gemini
from agno.os import AgentOS
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput
from agno.run.workflow import WorkflowRunOutputEvent

# Define agents
hackernews_agent = Agent(
    name="Hackernews Agent",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[HackerNewsTools()],
    instructions="Extract key insights from Hackernews posts",
)

web_agent = Agent(
    name="Web Agent",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Search the web for latest trends",
)

# Research team
research_team = Team(
    name="Research Team",
    members=[hackernews_agent, web_agent],
    instructions="Research tech topics comprehensively",
)

# Content planner with in-memory db for streaming
content_planner = Agent(
    name="Content Planner",
    model=Gemini(id="gemini-2.5-flash"),
    instructions=[
        "Plan content schedule over 4 weeks",
        "Create 3 posts per week",
    ],
    db=InMemoryDb(),  # Required for streaming
)


async def streaming_content_planning(
    step_input: StepInput,
) -> AsyncIterator[Union[WorkflowRunOutputEvent, StepOutput]]:
    """
    Async streaming custom function for AgentOS.

    Events from content_planner.arun() automatically get
    workflow context injected by the execution system.
    """
    message = step_input.input
    previous = step_input.previous_step_content

    prompt = f"""
    CONTENT PLANNING REQUEST:

    Topic: {message}
    Research: {previous[:500] if previous else "No research"}

    Create a detailed content plan.
    """

    try:
        # Stream agent response
        response_iterator = content_planner.arun(
            prompt,
            stream=True,
            stream_events=True,
        )

        # Yield each event to stream to AgentOS
        async for event in response_iterator:
            yield event

        # Get final response
        response = content_planner.get_last_run_output()

        # Yield final StepOutput
        enhanced = f"""
        ## Content Plan

        **Topic:** {message}
        **Research Used:** {"Yes" if previous else "No"}

        {response.content}
        """.strip()

        yield StepOutput(content=enhanced)

    except Exception as e:
        yield StepOutput(
            content=f"Planning failed: {str(e)}",
            success=False,
        )


# Define steps
research_step = Step(
    name="Research Step",
    team=research_team,
)

planning_step = Step(
    name="Content Planning Step",
    executor=streaming_content_planning,
)

# Create workflow
streaming_workflow = Workflow(
    name="Streaming Content Workflow",
    description="Content creation with streaming",
    db=SqliteDb(db_file="tmp/workflow.db"),
    steps=[research_step, planning_step],
)

# Initialize AgentOS
agent_os = AgentOS(
    description="Content Creation System",
    workflows=[streaming_workflow],
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="streaming_workflow:app", reload=True)
```

---

### Parallel Steps with Streaming

Stream from multiple parallel custom functions:

```python
from agno.workflow import Workflow, Step, Parallel
from agno.workflow.types import StepInput, StepOutput
from agno.run.workflow import WorkflowRunOutputEvent
from typing import AsyncIterator, Union

# HackerNews research function
async def hackernews_research(
    step_input: StepInput,
) -> AsyncIterator[Union[WorkflowRunOutputEvent, StepOutput]]:
    """Stream HackerNews research"""
    message = step_input.input

    prompt = f"""
    HACKERNEWS RESEARCH:

    Topic: {message}

    Tasks:
    1. Search relevant HackerNews posts
    2. Extract key insights and trends
    3. Summarize technical developments
    """

    try:
        response_iterator = hackernews_agent.arun(
            prompt,
            stream=True,
            stream_events=True,
        )
        async for event in response_iterator:
            yield event

        response = hackernews_agent.get_last_run_output()
        content = response.content if response else "No content"

        yield StepOutput(
            content=f"## HackerNews Results\n\n{content}"
        )

    except Exception as e:
        yield StepOutput(
            content=f"HackerNews research failed: {str(e)}",
            success=False,
        )


# Web search research function
async def web_research(
    step_input: StepInput,
) -> AsyncIterator[Union[WorkflowRunOutputEvent, StepOutput]]:
    """Stream web research"""
    message = step_input.input

    prompt = f"""
    WEB RESEARCH:

    Topic: {message}

    Tasks:
    1. Search for latest news and articles
    2. Identify market trends
    3. Gather statistical data
    """

    try:
        response_iterator = web_agent.arun(
            prompt,
            stream=True,
            stream_events=True,
        )
        async for event in response_iterator:
            yield event

        response = web_agent.get_last_run_output()
        content = response.content if response else "No content"

        yield StepOutput(
            content=f"## Web Research Results\n\n{content}"
        )

    except Exception as e:
        yield StepOutput(
            content=f"Web research failed: {str(e)}",
            success=False,
        )


# Create parallel streaming workflow
hackernews_step = Step(
    name="HackerNews Research",
    executor=hackernews_research,
)

web_step = Step(
    name="Web Research",
    executor=web_research,
)

synthesis_step = Step(
    name="Synthesis",
    executor=streaming_content_planning,
)

parallel_streaming_workflow = Workflow(
    name="Parallel Streaming Workflow",
    description="Parallel research with streaming",
    db=SqliteDb(db_file="tmp/workflow.db"),
    steps=[
        Parallel(
            hackernews_step,
            web_step,
            name="Parallel Research",
        ),
        synthesis_step,
    ],
)
```

---

## Async Events Streaming

Process workflow events programmatically with async iteration.

### WorkflowRunEvent Types

| Event | Description |
|-------|-------------|
| `workflow_started` | Workflow execution began |
| `workflow_completed` | Workflow execution finished |
| `step_started` | A step began execution |
| `step_completed` | A step finished execution |
| `condition_execution_started` | Condition evaluation began |
| `condition_execution_completed` | Condition evaluation finished |
| `loop_iteration_started` | Loop iteration began |
| `loop_iteration_completed` | Loop iteration finished |
| `parallel_execution_started` | Parallel execution began |
| `parallel_execution_completed` | Parallel execution finished |

---

### Basic Async Event Streaming

```python
import asyncio
from typing import AsyncIterator
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from agno.workflow.types import StepInput, StepOutput
from agno.run.workflow import WorkflowRunOutputEvent, WorkflowRunEvent
from agno.db.sqlite import SqliteDb
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from textwrap import dedent

# Define agents
web_agent = Agent(
    name="Web Agent",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    role="Search the web for latest news",
)

hackernews_agent = Agent(
    name="Hackernews Agent",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[HackerNewsTools()],
    role="Extract insights from Hackernews",
)

writer_agent = Agent(
    name="Writer Agent",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write a blog post on the topic",
)

# Research team
research_team = Team(
    name="Research Team",
    members=[hackernews_agent, web_agent],
    instructions="Research tech topics comprehensively",
)


# Async generator functions for steps
async def prepare_search_input(
    step_input: StepInput,
) -> AsyncIterator[StepOutput]:
    """Prepare input for web search"""
    topic = step_input.input

    content = dedent(f"""\
        Research the following topic:
        <topic>
        {topic}
        </topic>

        Search for at least 10 relevant articles.
    """)

    yield StepOutput(content=content)


async def prepare_writer_input(
    step_input: StepInput,
) -> AsyncIterator[StepOutput]:
    """Prepare input for writer"""
    topic = step_input.input
    research = step_input.previous_step_content

    content = dedent(f"""\
        Write a blog post on:
        <topic>
        {topic}
        </topic>

        Using this research:
        <research>
        {research}
        </research>
    """)

    yield StepOutput(content=content)


async def main():
    # Create workflow
    workflow = Workflow(
        name="Blog Post Workflow",
        description="Create blog posts from research",
        steps=[
            prepare_search_input,
            research_team,
            prepare_writer_input,
            writer_agent,
        ],
        db=SqliteDb(db_file="tmp/workflow.db"),
    )

    # Run with async streaming
    response: AsyncIterator[WorkflowRunOutputEvent] = workflow.arun(
        input="AI trends in 2025",
        markdown=True,
        stream=True,
        stream_events=True,
    )

    # Process events
    async for event in response:
        match event.event:
            case WorkflowRunEvent.workflow_started.value:
                print(f"🚀 Workflow started: {event.workflow_name}")

            case WorkflowRunEvent.step_started.value:
                print(f"  ▶ Step started: {event.step_id}")

            case WorkflowRunEvent.step_completed.value:
                print(f"  ✓ Step completed: {event.step_id}")

            case WorkflowRunEvent.workflow_completed.value:
                print(f"🏁 Workflow completed!")

            case WorkflowRunEvent.condition_execution_started.value:
                print(f"  ? Condition evaluating...")

            case WorkflowRunEvent.condition_execution_completed.value:
                print(f"  ? Condition evaluated")

            case WorkflowRunEvent.parallel_execution_started.value:
                print(f"  ⫘ Parallel execution started")

            case WorkflowRunEvent.parallel_execution_completed.value:
                print(f"  ⫘ Parallel execution completed")

            case _:
                # Content events
                if event.content:
                    print(event.content, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
```

---

### Filtering Executor Events

Control what events are streamed:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.model.google import Gemini

agent = Agent(
    name="Research Agent",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Research topics thoroughly.",
)

workflow = Workflow(
    name="Research Workflow",
    steps=[Step(name="Research", agent=agent)],
    stream=True,
    stream_executor_events=False,  # Filter out agent/team events
)

# This will only show workflow and step events
# Not internal agent execution events
for event in workflow.run(
    "What is Python?",
    stream=True,
    stream_events=True,
):
    event_name = event.event if hasattr(event, "event") else type(event).__name__
    print(f"Event: {event_name}")
```

---

## Mixed Executor Patterns

### Sequence of Functions and Agents

Combine custom preprocessing with agents and teams:

```python
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from agno.workflow.types import StepInput, StepOutput
from agno.db.sqlite import SqliteDb
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from textwrap import dedent

# Define agents
web_agent = Agent(
    name="Web Agent",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    role="Search the web",
)

hackernews_agent = Agent(
    name="Hackernews Agent",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[HackerNewsTools()],
    role="Extract Hackernews insights",
)

writer_agent = Agent(
    name="Writer Agent",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write engaging blog posts",
)

# Research team
research_team = Team(
    name="Research Team",
    members=[hackernews_agent, web_agent],
    instructions="Research topics comprehensively",
)


# Preprocessing functions
def prepare_search_input(step_input: StepInput) -> StepOutput:
    """Prepare input for research team"""
    topic = step_input.input

    content = dedent(f"""\
        I'm writing a blog post on:
        <topic>
        {topic}
        </topic>

        Search for at least 10 relevant articles.
    """)

    return StepOutput(content=content)


def prepare_writer_input(step_input: StepInput) -> StepOutput:
    """Prepare input for writer"""
    topic = step_input.input
    research = step_input.previous_step_content

    content = dedent(f"""\
        Write a blog post on:
        <topic>
        {topic}
        </topic>

        Research results:
        <research>
        {research}
        </research>
    """)

    return StepOutput(content=content)


# Create workflow mixing functions, teams, and agents
content_workflow = Workflow(
    name="Blog Post Workflow",
    description="Create blog posts from research",
    db=SqliteDb(db_file="tmp/workflow.db"),
    steps=[
        prepare_search_input,  # Function: Prepare input
        research_team,         # Team: Multi-agent research
        prepare_writer_input,  # Function: Transform for writer
        writer_agent,          # Agent: Write final content
    ],
)

if __name__ == "__main__":
    content_workflow.print_response(
        input="AI trends in 2025",
        markdown=True,
    )
```

---

### Class-Based Executors

Create reusable, configurable step executors:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput
from agno.db.sqlite import SqliteDb
from agno.model.google import Gemini

# Agent for use in executor
content_planner = Agent(
    name="Content Planner",
    model=Gemini(id="gemini-2.5-flash"),
    instructions=[
        "Plan content schedules",
        "Create actionable content strategies",
    ],
)


class ContentPlanningExecutor:
    """
    Configurable class-based executor.

    Benefits:
    - Configuration at initialization
    - Stateful execution across runs
    - Reusable across workflows
    """

    def __init__(
        self,
        weeks: int = 4,
        posts_per_week: int = 3,
        include_analytics: bool = True,
    ):
        self.weeks = weeks
        self.posts_per_week = posts_per_week
        self.include_analytics = include_analytics
        self.execution_count = 0

    def __call__(self, step_input: StepInput) -> StepOutput:
        """Execute content planning with configuration"""
        self.execution_count += 1

        message = step_input.input
        previous = step_input.previous_step_content

        prompt = f"""
        CONTENT PLANNING REQUEST #{self.execution_count}:

        Topic: {message}
        Research: {previous[:500] if previous else "No research"}

        Configuration:
        - Plan for {self.weeks} weeks
        - {self.posts_per_week} posts per week
        - Analytics: {"Include" if self.include_analytics else "Skip"}

        Create a detailed content plan.
        """

        try:
            response = content_planner.run(prompt)

            enhanced = f"""
            ## Content Plan (Run #{self.execution_count})

            **Configuration:**
            - Weeks: {self.weeks}
            - Posts/Week: {self.posts_per_week}
            - Analytics: {self.include_analytics}

            **Strategy:**
            {response.content}
            """.strip()

            return StepOutput(content=enhanced)

        except Exception as e:
            return StepOutput(
                content=f"Planning failed: {str(e)}",
                success=False,
            )


# Create configured executors
short_plan_executor = ContentPlanningExecutor(
    weeks=2,
    posts_per_week=2,
    include_analytics=False,
)

long_plan_executor = ContentPlanningExecutor(
    weeks=8,
    posts_per_week=5,
    include_analytics=True,
)

# Use in workflows
short_workflow = Workflow(
    name="Quick Content Plan",
    steps=[
        Step(name="Research", agent=research_agent),
        Step(name="Short Plan", executor=short_plan_executor),
    ],
)

detailed_workflow = Workflow(
    name="Detailed Content Plan",
    steps=[
        Step(name="Research", agent=research_agent),
        Step(name="Long Plan", executor=long_plan_executor),
    ],
)
```

---

### Async Class-Based Executor

For async/streaming support:

```python
from typing import AsyncIterator, Union
from agno.workflow.types import StepInput, StepOutput
from agno.run.workflow import WorkflowRunOutputEvent

class AsyncContentPlanningExecutor:
    """Async class-based executor with streaming"""

    def __init__(self, weeks: int = 4):
        self.weeks = weeks

    async def __call__(
        self,
        step_input: StepInput,
    ) -> AsyncIterator[Union[WorkflowRunOutputEvent, StepOutput]]:
        """Async execution with streaming"""
        message = step_input.input

        prompt = f"Create {self.weeks}-week content plan for: {message}"

        try:
            response_iterator = content_planner.arun(
                prompt,
                stream=True,
                stream_events=True,
            )

            async for event in response_iterator:
                yield event

            response = content_planner.get_last_run_output()

            yield StepOutput(content=response.content)

        except Exception as e:
            yield StepOutput(
                content=f"Failed: {str(e)}",
                success=False,
            )


# Use async executor
async_planning_step = Step(
    name="Async Planning",
    executor=AsyncContentPlanningExecutor(weeks=6),
)
```

---

## Function Instead of Steps

Use a single function for complete workflow control:

```python
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from agno.workflow.types import WorkflowExecutionInput
from agno.db.sqlite import SqliteDb
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

# Define agents and team
hackernews_agent = Agent(
    name="Hackernews Agent",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[HackerNewsTools()],
    role="Extract Hackernews insights",
)

web_agent = Agent(
    name="Web Agent",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    role="Search the web",
)

research_team = Team(
    name="Research Team",
    members=[hackernews_agent, web_agent],
    instructions="Research tech topics comprehensively",
)

content_planner = Agent(
    name="Content Planner",
    model=Gemini(id="gemini-2.5-flash"),
    instructions=["Plan content for 4 weeks", "3 posts per week"],
)


def custom_workflow_function(
    workflow: Workflow,
    execution_input: WorkflowExecutionInput,
):
    """
    Single function replaces all steps.

    Benefits:
    - Complete control over execution flow
    - Access to workflow features (storage, sessions)
    - Good for Workflows 1.0 migration
    """
    print(f"Executing: {workflow.name}")

    # Step 1: Research
    research_response = research_team.run(execution_input.input)
    research_content = research_response.content

    # Step 2: Create planning prompt
    planning_prompt = f"""
    CONTENT PLANNING:

    Topic: {execution_input.input}
    Research: {research_content[:500]}

    Create a detailed content plan.
    """

    # Step 3: Generate plan
    content_plan = content_planner.run(planning_prompt)

    # Return final content
    return content_plan.content


# Create workflow with single function
content_workflow = Workflow(
    name="Content Creation Workflow",
    description="Complete content creation with custom control",
    db=SqliteDb(db_file="tmp/workflow.db"),
    steps=custom_workflow_function,  # Single function
)

if __name__ == "__main__":
    content_workflow.print_response(
        input="AI trends in 2025",
    )
```

---

## Summary

| Pattern | Use Case |
|---------|----------|
| **Streaming AgentOS** | Production deployments with real-time UI |
| **Async Events** | Programmatic event processing |
| **Mixed Executors** | Functions + Agents + Teams together |
| **Class Executors** | Configurable, reusable step logic |
| **Function Workflow** | Complete control, Workflows 1.0 style |

---

## Related Documentation

- **Basic Patterns:** `docs(new)/workflows/04-basic-patterns.md`
- **Conditional/Parallel:** `docs(new)/workflows/05-conditional-parallel.md`
- **Advanced Patterns:** `docs(new)/workflows/07-grouped-advanced.md`

---

*Last Updated: December 2025 | AGNO 2.3.4*
