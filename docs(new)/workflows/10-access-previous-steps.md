# Accessing Previous Step Outputs

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/access-previous-steps

---

## Introduction

When building workflows, steps often need access to outputs from previous steps. AGNO provides several ways to access this data:

1. **`previous_step_content`** - Content from the immediately preceding step
2. **`previous_step_outputs`** - Dictionary of all previous step outputs by name
3. **`get_step_content()`** - Get specific step output by name
4. **`get_all_previous_content()`** - Get all previous content as formatted string

---

## StepInput Structure

Every custom function receives a `StepInput` object:

```python
@dataclass
class StepInput:
    input: str                              # Original workflow input
    previous_step_content: Optional[str]    # Last step's output
    previous_step_outputs: Dict[str, StepOutput]  # All outputs by name
    additional_data: Optional[Dict[str, Any]]     # Extra data passed in
```

---

## Method 1: Previous Step Content

Access the output from the immediately preceding step:

```python
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput

def second_step(step_input: StepInput) -> StepOutput:
    """Access output from the previous step"""

    # Get content from the step that ran before this one
    previous_content = step_input.previous_step_content

    if previous_content:
        result = f"Building on previous: {previous_content[:200]}..."
    else:
        result = "No previous content available"

    return StepOutput(content=result)


workflow = Workflow(
    name="Sequential Pipeline",
    steps=[
        Step(name="Step 1", agent=first_agent),
        Step(name="Step 2", executor=second_step),  # Gets Step 1 output
        Step(name="Step 3", agent=third_agent),     # Gets Step 2 output
    ],
)
```

---

## Method 2: Previous Step Outputs Dictionary

Access all previous step outputs by their names:

```python
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput

def synthesis_step(step_input: StepInput) -> StepOutput:
    """Access multiple previous step outputs by name"""

    # Dictionary of all previous outputs
    all_outputs = step_input.previous_step_outputs

    # Access specific steps by name
    research_output = all_outputs.get("Research")
    analysis_output = all_outputs.get("Analysis")

    # Build synthesis from multiple sources
    synthesis = f"""
    ## Synthesis Report

    ### Research Findings
    {research_output.content if research_output else "N/A"}

    ### Analysis Results
    {analysis_output.content if analysis_output else "N/A"}

    ### Combined Insights
    [Synthesized from both sources]
    """

    return StepOutput(content=synthesis)


workflow = Workflow(
    name="Multi-Source Pipeline",
    steps=[
        Step(name="Research", agent=researcher),
        Step(name="Analysis", agent=analyst),
        Step(name="Synthesis", executor=synthesis_step),
    ],
)
```

---

## Method 3: get_step_content() Helper

Use the `get_step_content()` function for cleaner access:

```python
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput, get_step_content

def final_step(step_input: StepInput) -> StepOutput:
    """Use get_step_content() helper"""

    # Get specific step content by name
    research = get_step_content(step_input, "Research")
    analysis = get_step_content(step_input, "Analysis")
    review = get_step_content(step_input, "Review")

    # Combine all sources
    final = f"""
    # Final Report

    ## Research
    {research or "No research data"}

    ## Analysis
    {analysis or "No analysis data"}

    ## Review
    {review or "No review data"}
    """

    return StepOutput(content=final)


workflow = Workflow(
    name="Report Pipeline",
    steps=[
        Step(name="Research", agent=researcher),
        Step(name="Analysis", agent=analyst),
        Step(name="Review", agent=reviewer),
        Step(name="Final", executor=final_step),
    ],
)
```

---

## Method 4: get_all_previous_content() Helper

Get all previous content as a formatted string:

```python
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput, get_all_previous_content

def summary_step(step_input: StepInput) -> StepOutput:
    """Get all previous outputs in one call"""

    # Get formatted string of all previous content
    all_content = get_all_previous_content(step_input)

    # Pass to agent for summarization
    summary_prompt = f"""
    Summarize the following workflow outputs:

    {all_content}

    Create a concise executive summary.
    """

    response = summary_agent.run(summary_prompt)
    return StepOutput(content=response.content)


workflow = Workflow(
    name="Summary Pipeline",
    steps=[
        Step(name="Data Collection", agent=collector),
        Step(name="Processing", agent=processor),
        Step(name="Analysis", agent=analyst),
        Step(name="Summary", executor=summary_step),
    ],
)
```

---

## Accessing Parallel Step Outputs

When steps run in parallel, access their combined outputs:

```python
from agno.workflow import Workflow, Step, Parallel
from agno.workflow.types import StepInput, StepOutput

def combine_parallel_outputs(step_input: StepInput) -> StepOutput:
    """Access outputs from parallel steps"""

    outputs = step_input.previous_step_outputs

    # Each parallel step has its output in the dictionary
    tech_research = outputs.get("Tech Research")
    market_research = outputs.get("Market Research")
    competitor_research = outputs.get("Competitor Research")

    combined = f"""
    ## Combined Research

    ### Technology
    {tech_research.content if tech_research else "N/A"}

    ### Market
    {market_research.content if market_research else "N/A"}

    ### Competitors
    {competitor_research.content if competitor_research else "N/A"}
    """

    return StepOutput(content=combined)


workflow = Workflow(
    name="Parallel Research Pipeline",
    steps=[
        Parallel(
            Step(name="Tech Research", agent=tech_researcher),
            Step(name="Market Research", agent=market_researcher),
            Step(name="Competitor Research", agent=competitor_researcher),
            name="Research Phase",
        ),
        Step(name="Combine", executor=combine_parallel_outputs),
    ],
)
```

---

## Accessing Loop Iteration Outputs

Access outputs from loop iterations:

```python
from agno.workflow import Workflow, Step, Loop
from agno.workflow.types import StepInput, StepOutput, StepOutput
from typing import List

def process_after_loop(step_input: StepInput) -> StepOutput:
    """Access combined outputs from loop iterations"""

    # After a loop, previous_step_content contains the final iteration
    final_iteration = step_input.previous_step_content

    # previous_step_outputs contains outputs from the loop steps
    outputs = step_input.previous_step_outputs

    return StepOutput(
        content=f"Loop completed. Final output: {final_iteration}"
    )


def quality_check(outputs: List[StepOutput]) -> bool:
    """End condition for the loop"""
    if not outputs:
        return False
    return len(outputs[-1].content or "") > 500


workflow = Workflow(
    name="Iterative Pipeline",
    steps=[
        Loop(
            name="Research Loop",
            steps=[
                Step(name="Research", agent=researcher),
                Step(name="Refine", agent=refiner),
            ],
            end_condition=quality_check,
            max_iterations=3,
        ),
        Step(name="Process", executor=process_after_loop),
    ],
)
```

---

## Accessing Conditional Step Outputs

Handle outputs from conditional branches:

```python
from agno.workflow import Workflow, Step
from agno.workflow.condition import Condition
from agno.workflow.types import StepInput, StepOutput

def is_tech_topic(step_input: StepInput) -> bool:
    content = step_input.input or ""
    return "tech" in content.lower() or "ai" in content.lower()


def process_conditionally(step_input: StepInput) -> StepOutput:
    """Handle output from conditional step (may or may not exist)"""

    outputs = step_input.previous_step_outputs

    # Check if the conditional step ran
    tech_analysis = outputs.get("Tech Analysis")

    if tech_analysis:
        result = f"Tech analysis available: {tech_analysis.content}"
    else:
        result = "No tech analysis (condition was false)"

    return StepOutput(content=result)


workflow = Workflow(
    name="Conditional Pipeline",
    steps=[
        Step(name="Initial", agent=initial_agent),
        Condition(
            name="Tech Check",
            evaluator=is_tech_topic,
            steps=[Step(name="Tech Analysis", agent=tech_analyst)],
        ),
        Step(name="Process", executor=process_conditionally),
    ],
)
```

---

## Accessing Router-Selected Step Outputs

Handle outputs from dynamically routed steps:

```python
from agno.workflow import Workflow, Step
from agno.workflow.router import Router
from agno.workflow.types import StepInput, StepOutput
from typing import List

def route_by_topic(step_input: StepInput) -> List[Step]:
    topic = step_input.input.lower()
    if "sales" in topic:
        return [sales_step]
    elif "support" in topic:
        return [support_step]
    return [general_step]


def handle_routed_output(step_input: StepInput) -> StepOutput:
    """Process output from whichever step was selected"""

    outputs = step_input.previous_step_outputs

    # Check which step ran
    sales = outputs.get("Sales Handler")
    support = outputs.get("Support Handler")
    general = outputs.get("General Handler")

    # Use whichever output exists
    if sales:
        result = f"Sales response: {sales.content}"
    elif support:
        result = f"Support response: {support.content}"
    elif general:
        result = f"General response: {general.content}"
    else:
        result = "No handler output found"

    return StepOutput(content=result)


sales_step = Step(name="Sales Handler", agent=sales_agent)
support_step = Step(name="Support Handler", agent=support_agent)
general_step = Step(name="General Handler", agent=general_agent)

workflow = Workflow(
    name="Routed Pipeline",
    steps=[
        Router(
            name="Topic Router",
            selector=route_by_topic,
            choices=[sales_step, support_step, general_step],
        ),
        Step(name="Process", executor=handle_routed_output),
    ],
)
```

---

## Complete Example: Multi-Step Pipeline

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step, Parallel
from agno.workflow.types import StepInput, StepOutput, get_step_content
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools

# Define agents
researcher = Agent(
    name="Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Research topics thoroughly.",
)

analyst = Agent(
    name="Analyst",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze data and provide insights.",
)

writer = Agent(
    name="Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write clear, engaging content.",
)


# Custom function that accesses multiple previous outputs
def create_report(step_input: StepInput) -> StepOutput:
    """Create final report from all previous step outputs"""

    # Method 1: Direct access to previous step
    immediate_previous = step_input.previous_step_content

    # Method 2: Access specific steps by name
    outputs = step_input.previous_step_outputs
    web_research = outputs.get("Web Research")
    market_research = outputs.get("Market Research")
    analysis = outputs.get("Analysis")

    # Method 3: Helper function
    web_content = get_step_content(step_input, "Web Research")
    market_content = get_step_content(step_input, "Market Research")

    # Build comprehensive report
    report = f"""
    # Comprehensive Report

    ## Executive Summary
    Based on research and analysis from multiple sources.

    ## Web Research Findings
    {web_content or "No web research available"}

    ## Market Research Findings
    {market_content or "No market research available"}

    ## Analysis
    {analysis.content if analysis else "No analysis available"}

    ## Recommendations
    [Based on the combined findings above]
    """

    return StepOutput(content=report)


# Build workflow
workflow = Workflow(
    name="Comprehensive Report Pipeline",
    description="Research, analyze, and report",
    steps=[
        # Parallel research from multiple sources
        Parallel(
            Step(name="Web Research", agent=researcher),
            Step(name="Market Research", agent=researcher),
            name="Research Phase",
        ),
        # Analysis step (receives parallel outputs)
        Step(name="Analysis", agent=analyst),
        # Final report (accesses all previous outputs)
        Step(name="Report", executor=create_report),
        # Optional: Polish with writer
        Step(name="Polish", agent=writer),
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Research sustainable technology trends and market opportunities",
        markdown=True,
    )
```

---

## Accessing Step Metadata

Step outputs can include metadata:

```python
from agno.workflow.types import StepInput, StepOutput

def step_with_metadata(step_input: StepInput) -> StepOutput:
    """Create output with metadata"""
    return StepOutput(
        content="Processed data",
        metadata={
            "sources_count": 5,
            "confidence": 0.85,
            "processing_time": 2.3,
        },
    )


def use_metadata(step_input: StepInput) -> StepOutput:
    """Access metadata from previous step"""

    outputs = step_input.previous_step_outputs
    previous = outputs.get("Data Step")

    if previous and previous.metadata:
        confidence = previous.metadata.get("confidence", 0)
        sources = previous.metadata.get("sources_count", 0)

        if confidence < 0.7:
            return StepOutput(
                content="Low confidence - needs review",
                success=False,
            )

    return StepOutput(content="Proceeding with high confidence data")
```

---

## Best Practices

### Naming Steps

```python
# Good - descriptive, unique names
Step(name="Web Research", agent=researcher)
Step(name="Market Analysis", agent=analyst)
Step(name="Executive Summary", agent=writer)

# Bad - generic, ambiguous names
Step(name="Step 1", agent=researcher)
Step(name="Process", agent=analyst)
Step(name="Output", agent=writer)
```

### Safe Access Patterns

```python
def safe_access(step_input: StepInput) -> StepOutput:
    """Always handle missing data gracefully"""

    # Safe access to previous content
    previous = step_input.previous_step_content or ""

    # Safe access to specific step
    outputs = step_input.previous_step_outputs or {}
    research = outputs.get("Research")
    research_content = research.content if research else "No data"

    # Using helper (returns None if not found)
    analysis = get_step_content(step_input, "Analysis") or "Not available"

    return StepOutput(content=f"Research: {research_content}")
```

### Don't Assume Step Order

```python
def flexible_step(step_input: StepInput) -> StepOutput:
    """Check what's available, don't assume"""

    outputs = step_input.previous_step_outputs

    # Check what actually ran
    available_steps = list(outputs.keys())
    print(f"Available outputs: {available_steps}")

    # Build from what's available
    content_parts = []
    for step_name, output in outputs.items():
        if output.content:
            content_parts.append(f"## {step_name}\n{output.content}")

    return StepOutput(content="\n\n".join(content_parts))
```

---

## Summary

| Method | Use Case |
|--------|----------|
| `previous_step_content` | Quick access to last step |
| `previous_step_outputs` | Access multiple named steps |
| `get_step_content()` | Clean access by step name |
| `get_all_previous_content()` | All content formatted |

---

## Related Documentation

- **Building Workflows:** `docs(new)/workflows/02-building-workflows.md`
- **Basic Patterns:** `docs(new)/workflows/04-basic-patterns.md`
- **Parallel Patterns:** `docs(new)/workflows/05-conditional-parallel.md`

---

*Last Updated: December 2025 | AGNO 2.3.4*
