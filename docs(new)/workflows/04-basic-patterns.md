# Basic Workflow Patterns

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/workflow-patterns/overview

---

## Introduction

This document covers the fundamental workflow patterns:

1. **Sequential Workflows** - Linear step-by-step execution
2. **Step-Based Workflows** - Named steps for better organization
3. **Custom Function Workflows** - Python functions as steps
4. **Fully Python Workflows** - Complete control with a single function

---

## Pattern 1: Sequential Workflows

Linear, deterministic processes where each step depends on the output of the previous step.

**Example Flow:** Research → Data Processing → Content Creation → Final Review

### Basic Sequential Pattern

```python
from agno.workflow import Workflow

workflow = Workflow(
    name="Content Pipeline",
    steps=[
        research_agent,      # Step 1: Research
        analysis_agent,      # Step 2: Analyze
        writer_agent,        # Step 3: Write
    ]
)

workflow.print_response(
    "Analyze the competitive landscape for fintech startups",
    markdown=True
)
```

### Mixed Executors (Agent + Team + Function)

```python
from agno.workflow import Workflow, StepOutput

def data_preprocessor(step_input):
    """Custom preprocessing between agent steps"""
    raw_data = step_input.previous_step_content
    processed = clean_and_format(raw_data)
    return StepOutput(content=processed)

workflow = Workflow(
    name="Mixed Execution Pipeline",
    steps=[
        research_team,       # Team: Multi-agent research
        data_preprocessor,   # Function: Data cleaning
        content_agent,       # Agent: Final content creation
    ]
)

workflow.print_response("Research AI market trends", markdown=True)
```

### When to Use Sequential

- Linear processes with clear dependencies
- Each step requires output from the previous step
- Predictable, auditable execution is needed
- Simple pipelines without branching

---

## Pattern 2: Step-Based Workflows

Named steps provide better logging, debugging, and platform support.

### Basic Named Steps

```python
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow, Step
from agno.db.sqlite import SqliteDb
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

# Define agents
hackernews_agent = Agent(
    name="HackerNews Agent",
    tools=[HackerNewsTools()],
    instructions="Extract insights from HackerNews posts",
)

web_agent = Agent(
    name="Web Agent",
    tools=[DuckDuckGoTools()],
    instructions="Search the web for trends",
)

# Define team
research_team = Team(
    name="Research Team",
    members=[hackernews_agent, web_agent],
    instructions="Research topics from multiple sources",
)

content_planner = Agent(
    name="Content Planner",
    instructions="Create a 4-week content plan with 3 posts/week",
)

# Define NAMED steps
research_step = Step(
    name="Research Step",
    team=research_team,
    description="Multi-source research phase",
)

planning_step = Step(
    name="Content Planning Step",
    agent=content_planner,
    description="Create content schedule",
)

# Build workflow with named steps
workflow = Workflow(
    name="Content Creation Workflow",
    description="Research and plan content",
    db=SqliteDb(
        session_table="workflow_session",
        db_file="tmp/workflow.db",
    ),
    steps=[research_step, planning_step],
)

if __name__ == "__main__":
    workflow.print_response(
        input="AI trends in 2025",
        markdown=True,
    )
```

### Benefits of Named Steps

| Benefit | Description |
|---------|-------------|
| **Better Logging** | Clear step identification in logs |
| **Easier Debugging** | Know exactly which step failed |
| **Platform Support** | Enhanced visibility in AgentOS |
| **Output Access** | Access outputs by step name |

### Accessing Step Outputs by Name

```python
def final_step(step_input: StepInput) -> StepOutput:
    # Access specific step output by name
    all_outputs = step_input.previous_step_outputs

    research_output = all_outputs.get("Research Step")
    planning_output = all_outputs.get("Content Planning Step")

    # Use both outputs
    combined = f"""
    Research: {research_output.content[:500]}
    Plan: {planning_output.content}
    """

    return StepOutput(content=combined)
```

### When to Use Step-Based

- When you need clear step identification
- For better debugging and monitoring
- When step outputs need to be accessed by name
- In production workflows requiring auditability

---

## Pattern 3: Custom Function Workflows

Maximum flexibility with custom Python logic for step execution.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Custom Logic** | Implement complex business rules |
| **Agent Integration** | Call agents/teams within your logic |
| **Data Flow Control** | Transform outputs between steps |
| **Error Handling** | Custom error recovery logic |

### Basic Custom Function

```python
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput

def custom_processor(step_input: StepInput) -> StepOutput:
    """Custom processing function"""
    message = step_input.input
    previous = step_input.previous_step_content

    # Custom business logic
    processed = f"""
    ## Processed Output

    **Original Input:** {message}
    **Previous Step:** {previous[:200] if previous else "None"}

    **Processing Result:** Custom transformation applied.
    """

    return StepOutput(content=processed)

# Use in workflow
processing_step = Step(
    name="Custom Processing",
    executor=custom_processor,
    description="Apply custom transformations",
)

workflow = Workflow(
    name="Custom Workflow",
    steps=[research_agent, processing_step, writer_agent],
)
```

### Calling Agents Inside Functions

```python
from agno.agent import Agent
from agno.workflow.types import StepInput, StepOutput

content_planner = Agent(
    name="Content Planner",
    instructions="Create detailed content plans",
)

def custom_content_planning(step_input: StepInput) -> StepOutput:
    """Custom function that orchestrates an agent"""
    message = step_input.input
    previous = step_input.previous_step_content

    # Build a custom prompt
    planning_prompt = f"""
    STRATEGIC CONTENT PLANNING REQUEST:

    Core Topic: {message}
    Research Results: {previous[:500] if previous else "No research"}

    Requirements:
    1. Create comprehensive content strategy
    2. Identify content formats and channels
    3. Provide timeline recommendations
    4. Include engagement strategies

    Create a detailed, actionable content plan.
    """

    try:
        # Call the agent inside the function
        response = content_planner.run(planning_prompt)

        # Enhance the output
        enhanced = f"""
        ## Strategic Content Plan

        **Topic:** {message}
        **Research Used:** {"Yes" if previous else "No"}

        {response.content}

        ---
        *Custom enhancements applied*
        """

        return StepOutput(content=enhanced)

    except Exception as e:
        return StepOutput(
            content=f"Planning failed: {str(e)}",
            success=False,
            error=str(e),
        )

# Use in workflow
planning_step = Step(
    name="Content Planning Step",
    executor=custom_content_planning,
)
```

### Class-Based Executors

For complex, configurable logic:

```python
from agno.workflow.types import StepInput, StepOutput

class ContentPlanningExecutor:
    """Configurable class-based executor"""

    def __init__(self, max_weeks: int = 4, posts_per_week: int = 3):
        self.max_weeks = max_weeks
        self.posts_per_week = posts_per_week
        self.planner = Agent(
            name="Planner",
            instructions=f"Plan for {max_weeks} weeks, {posts_per_week} posts/week"
        )

    def __call__(self, step_input: StepInput) -> StepOutput:
        """Execute the planning logic"""
        prompt = f"""
        Plan content for {self.max_weeks} weeks.
        Posts per week: {self.posts_per_week}
        Topic: {step_input.input}
        """

        response = self.planner.run(prompt)
        return StepOutput(content=response.content)

# Create configured instance
planning_step = Step(
    name="Content Planning",
    executor=ContentPlanningExecutor(max_weeks=8, posts_per_week=5),
)
```

### Async Custom Functions with Streaming

For AgentOS streaming support:

```python
from typing import AsyncIterator, Union
from agno.workflow.types import StepInput, StepOutput
from agno.run.workflow import WorkflowRunOutputEvent

async def streaming_custom_function(
    step_input: StepInput,
) -> AsyncIterator[Union[WorkflowRunOutputEvent, StepOutput]]:
    """Async streaming custom function"""
    message = step_input.input
    previous = step_input.previous_step_content

    prompt = f"Create content plan for: {message}"

    try:
        # Stream agent response
        response_iterator = content_planner.arun(
            prompt,
            stream=True,
            stream_events=True,
        )

        async for event in response_iterator:
            yield event  # Stream events to caller

        # Get final response
        response = content_planner.get_last_run_output()

        # Yield final StepOutput
        yield StepOutput(content=response.content)

    except Exception as e:
        yield StepOutput(
            content=f"Failed: {str(e)}",
            success=False,
        )
```

### When to Use Custom Functions

- Complex business rules and transformations
- Orchestrating multiple agents within a step
- Custom error handling and recovery
- Data transformation between steps
- Integration with external systems

---

## Pattern 4: Fully Python Workflows

Complete control with a single function replacing all steps.

### When to Use

- Maximum flexibility needed
- Workflows 1.0 migration
- Complex orchestration logic
- Custom control flow requirements

### Basic Implementation

```python
from agno.workflow import Workflow
from agno.workflow.types import WorkflowExecutionInput

def custom_workflow_function(
    workflow: Workflow,
    execution_input: WorkflowExecutionInput
):
    """Single function handles entire workflow"""

    # Step 1: Research
    research_result = research_team.run(execution_input.input)
    print("Research complete")

    # Step 2: Analyze
    analysis_result = analysis_agent.run(research_result.content)
    print("Analysis complete")

    # Step 3: Custom logic
    if "urgent" in execution_input.input.lower():
        # Fast path
        return f"URGENT: {analysis_result.content}"
    else:
        # Standard path
        final_result = writer_agent.run(analysis_result.content)
        return final_result.content

# Create workflow with single function
workflow = Workflow(
    name="Function-Based Workflow",
    steps=custom_workflow_function,  # Single function replaces all steps
)

workflow.print_response(
    "Evaluate the market potential for quantum computing",
    markdown=True
)
```

### Complete Example with Teams and Agents

```python
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from agno.workflow.types import WorkflowExecutionInput
from agno.db.sqlite import SqliteDb
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

# Define agents
hackernews_agent = Agent(
    name="HackerNews Agent",
    tools=[HackerNewsTools()],
    instructions="Extract key insights from HackerNews",
)

web_agent = Agent(
    name="Web Agent",
    tools=[DuckDuckGoTools()],
    instructions="Search for latest trends",
)

# Define team
research_team = Team(
    name="Research Team",
    members=[hackernews_agent, web_agent],
    instructions="Research tech topics comprehensively",
)

content_planner = Agent(
    name="Content Planner",
    instructions="Create a 4-week content plan with 3 posts/week",
)


def custom_execution_function(
    workflow: Workflow,
    execution_input: WorkflowExecutionInput
):
    """Complete custom orchestration"""
    print(f"Executing workflow: {workflow.name}")

    # Run research team
    research_response = research_team.run(execution_input.input)
    research_content = research_response.content

    # Build planning prompt
    planning_prompt = f"""
    STRATEGIC CONTENT PLANNING REQUEST:

    Core Topic: {execution_input.input}
    Research Results: {research_content[:500]}

    Requirements:
    1. Create comprehensive content strategy
    2. Leverage research findings
    3. Identify content formats and channels
    4. Provide timeline recommendations

    Create a detailed, actionable content plan.
    """

    # Run content planner
    content_plan = content_planner.run(planning_prompt)

    return content_plan.content


# Create workflow
content_workflow = Workflow(
    name="Content Creation Workflow",
    description="Full custom orchestration",
    db=SqliteDb(
        session_table="workflow_session",
        db_file="tmp/workflow.db",
    ),
    steps=custom_execution_function,
)

if __name__ == "__main__":
    content_workflow.print_response(
        input="AI trends in 2025",
        markdown=True,
    )
```

### Benefits of Fully Python Workflows

| Benefit | Description |
|---------|-------------|
| **Full Control** | Complete control over execution flow |
| **Workflow Features** | Still get storage, streaming, sessions |
| **Migration Path** | Easy migration from Workflows 1.0 |
| **Complex Logic** | Handle any orchestration pattern |

---

## Pattern Comparison

| Pattern | Complexity | Flexibility | Use Case |
|---------|------------|-------------|----------|
| **Sequential** | Low | Low | Simple linear pipelines |
| **Step-Based** | Low | Medium | Production workflows needing logging |
| **Custom Function** | Medium | High | Complex transformations between steps |
| **Fully Python** | High | Highest | Complete custom control |

---

## Best Practices

### Sequential Workflows

1. Keep steps focused on single responsibilities
2. Use clear, descriptive agent names
3. Consider adding validation between steps

### Step-Based Workflows

1. Always name your steps descriptively
2. Add descriptions for documentation
3. Use database persistence for production

### Custom Function Workflows

1. Always return `StepOutput`
2. Handle errors gracefully with `success=False`
3. Use `try/except` for agent calls
4. Consider class-based executors for complex logic

### Fully Python Workflows

1. Add logging for debugging
2. Return clear final output
3. Handle errors at each stage
4. Consider breaking into smaller functions

---

## Summary

| Pattern | Key Feature |
|---------|-------------|
| **Sequential** | Simple linear execution |
| **Step-Based** | Named steps for tracking |
| **Custom Function** | Python logic as steps |
| **Fully Python** | Single function control |

---

## Related Documentation

- **Conditional/Parallel:** `docs(new)/workflows/05-conditional-parallel.md`
- **Iterative/Branching:** `docs(new)/workflows/06-iterative-branching.md`
- **Advanced Patterns:** `docs(new)/workflows/07-grouped-advanced.md`

---

*Last Updated: December 2025 | AGNO 2.3.4*
