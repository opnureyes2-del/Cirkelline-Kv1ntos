# Early Stop

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/early-stop

---

## Introduction

Early stop allows you to halt workflow execution before all steps complete. This is useful for:

- Validation failures
- Quality gates
- Error detection
- Budget/time limits
- Safety checks

---

## Core Concept

```python
from agno.workflow.types import StepOutput

def validation_step(step_input):
    if not valid:
        return StepOutput(
            content="Validation failed",
            stop=True,  # Stop entire workflow
        )
    return StepOutput(content="Valid, continue...")
```

---

## How It Works

1. Step returns `StepOutput` with `stop=True`
2. Workflow immediately halts
3. Remaining steps are skipped
4. Final output is the stopping step's content

```
Step 1 → Step 2 (stop=True) → Step 3 (skipped) → Step 4 (skipped)
                    ↓
              Workflow ends here
```

---

## Basic Example

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput
from agno.model.google import Gemini

# Define agents
researcher = Agent(
    name="Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Research topics thoroughly.",
)

writer = Agent(
    name="Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write engaging content.",
)


def content_validator(step_input: StepInput) -> StepOutput:
    """Validate content and stop if invalid"""
    content = step_input.previous_step_content or ""

    # Check for required elements
    has_sources = "source" in content.lower() or "http" in content.lower()
    has_data = any(char.isdigit() for char in content)
    sufficient_length = len(content) > 200

    if not has_sources:
        return StepOutput(
            content="STOPPED: Research lacks sources. Please provide cited information.",
            stop=True,
        )

    if not has_data:
        return StepOutput(
            content="STOPPED: Research lacks data points. Please include statistics.",
            stop=True,
        )

    if not sufficient_length:
        return StepOutput(
            content="STOPPED: Research is too brief. Please provide more detail.",
            stop=True,
        )

    # All validations passed
    return StepOutput(
        content=f"Validated content:\n\n{content}",
        stop=False,  # Continue workflow (default)
    )


# Build workflow with validation gate
workflow = Workflow(
    name="Validated Content Pipeline",
    description="Research with quality validation",
    steps=[
        Step(name="Research", agent=researcher),
        Step(name="Validate", executor=content_validator),
        Step(name="Write", agent=writer),  # Only runs if validation passes
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Research the latest AI developments",
        markdown=True,
    )
```

---

## StepOutput Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `Any` | Required | Step output content |
| `stop` | `bool` | `False` | Stop workflow if True |
| `success` | `bool` | `True` | Whether step succeeded |
| `error` | `str` | `None` | Error message if failed |
| `metadata` | `Dict` | `None` | Additional metadata |

---

## Validation Patterns

### Data Quality Check

```python
def data_quality_check(step_input: StepInput) -> StepOutput:
    """Stop if data quality is insufficient"""
    data = step_input.previous_step_content or ""

    # Quality metrics
    word_count = len(data.split())
    has_numbers = any(c.isdigit() for c in data)
    has_structure = "##" in data or "- " in data

    quality_score = 0
    quality_score += 1 if word_count > 100 else 0
    quality_score += 1 if has_numbers else 0
    quality_score += 1 if has_structure else 0

    if quality_score < 2:
        return StepOutput(
            content=f"Quality check failed (score: {quality_score}/3). "
                    "Data needs improvement before proceeding.",
            stop=True,
            metadata={"quality_score": quality_score},
        )

    return StepOutput(
        content=data,
        metadata={"quality_score": quality_score},
    )
```

---

### Error Detection

```python
def error_detector(step_input: StepInput) -> StepOutput:
    """Stop on detected errors"""
    content = step_input.previous_step_content or ""

    # Check for error indicators
    error_phrases = [
        "error occurred",
        "failed to",
        "could not",
        "unable to",
        "no results found",
        "API error",
    ]

    for phrase in error_phrases:
        if phrase in content.lower():
            return StepOutput(
                content=f"Error detected: '{phrase}' found in output. "
                        "Workflow stopped for review.",
                stop=True,
                success=False,
                error=phrase,
            )

    return StepOutput(content=content)
```

---

### Minimum Content Length

```python
def length_validator(step_input: StepInput) -> StepOutput:
    """Stop if content is too short"""
    content = step_input.previous_step_content or ""
    min_length = 500  # Minimum characters

    if len(content) < min_length:
        return StepOutput(
            content=f"Content too short ({len(content)} chars, "
                    f"minimum {min_length}). Stopping workflow.",
            stop=True,
        )

    return StepOutput(content=content)
```

---

### Required Keywords

```python
def keyword_validator(step_input: StepInput) -> StepOutput:
    """Stop if required keywords are missing"""
    content = step_input.previous_step_content or ""
    content_lower = content.lower()

    required_keywords = ["conclusion", "summary", "recommendation"]
    missing = [kw for kw in required_keywords if kw not in content_lower]

    if missing:
        return StepOutput(
            content=f"Missing required sections: {', '.join(missing)}. "
                    "Please include all required sections.",
            stop=True,
            metadata={"missing_keywords": missing},
        )

    return StepOutput(content=content)
```

---

### Budget/Time Check

```python
import time

class BudgetChecker:
    """Track and enforce budget limits"""

    def __init__(self, max_time_seconds: int = 60):
        self.start_time = None
        self.max_time = max_time_seconds

    def start(self):
        self.start_time = time.time()

    def check(self, step_input: StepInput) -> StepOutput:
        """Stop if time budget exceeded"""
        if self.start_time is None:
            self.start_time = time.time()

        elapsed = time.time() - self.start_time

        if elapsed > self.max_time:
            return StepOutput(
                content=f"Time budget exceeded ({elapsed:.1f}s > {self.max_time}s). "
                        "Stopping to prevent overrun.",
                stop=True,
                metadata={"elapsed_seconds": elapsed},
            )

        return StepOutput(
            content=step_input.previous_step_content,
            metadata={"elapsed_seconds": elapsed},
        )


# Usage
budget = BudgetChecker(max_time_seconds=30)

workflow = Workflow(
    name="Time-Limited Pipeline",
    steps=[
        Step(name="Research", agent=researcher),
        Step(name="Budget Check", executor=budget.check),
        Step(name="Analysis", agent=analyst),
        Step(name="Budget Check 2", executor=budget.check),
        Step(name="Report", agent=reporter),
    ],
)
```

---

### Content Safety Check

```python
def safety_check(step_input: StepInput) -> StepOutput:
    """Stop if content contains unsafe material"""
    content = step_input.previous_step_content or ""

    # Basic patterns (use proper safety APIs in production)
    unsafe_patterns = [
        "harmful instructions",
        "dangerous activity",
        "illegal content",
    ]

    for pattern in unsafe_patterns:
        if pattern in content.lower():
            return StepOutput(
                content="Content flagged for safety review. Workflow stopped.",
                stop=True,
                success=False,
                metadata={"flagged_pattern": pattern},
            )

    return StepOutput(content=content)
```

---

## Early Stop with Conditions

Combine early stop with conditional logic:

```python
from agno.workflow import Workflow, Step
from agno.workflow.condition import Condition
from agno.workflow.types import StepInput, StepOutput

def needs_review(step_input: StepInput) -> bool:
    """Check if content needs human review"""
    content = step_input.previous_step_content or ""
    return "uncertain" in content.lower() or "unclear" in content.lower()


def human_review_gate(step_input: StepInput) -> StepOutput:
    """Stop for human review if flagged"""
    return StepOutput(
        content="Content flagged for human review. "
                "Please review before proceeding.",
        stop=True,
        metadata={"requires_human_review": True},
    )


workflow = Workflow(
    name="Review Pipeline",
    steps=[
        Step(name="Generate", agent=generator),
        Condition(
            name="Review Check",
            evaluator=needs_review,
            steps=[
                Step(name="Review Gate", executor=human_review_gate),
            ],
        ),
        Step(name="Publish", agent=publisher),  # Skipped if review gate triggers
    ],
)
```

---

## Early Stop in Loops

Stop a loop early based on quality:

```python
from agno.workflow import Workflow, Step, Loop
from agno.workflow.types import StepInput, StepOutput, StepOutput
from typing import List

def quality_evaluator(outputs: List[StepOutput]) -> bool:
    """End loop when quality is sufficient"""
    if not outputs:
        return False

    last_output = outputs[-1]
    content = last_output.content or ""

    # Check if quality threshold met
    return len(content) > 1000 and "conclusion" in content.lower()


def quality_gate(step_input: StepInput) -> StepOutput:
    """Stop entire workflow if quality never achieved"""
    content = step_input.previous_step_content or ""

    # This runs after loop exits (either by condition or max_iterations)
    if len(content) < 500:
        return StepOutput(
            content="Loop completed but quality still insufficient. "
                    "Manual intervention required.",
            stop=True,
        )

    return StepOutput(content=content)


workflow = Workflow(
    name="Quality Loop Pipeline",
    steps=[
        Loop(
            name="Research Loop",
            steps=[
                Step(name="Research", agent=researcher),
                Step(name="Refine", agent=refiner),
            ],
            end_condition=quality_evaluator,
            max_iterations=3,
        ),
        Step(name="Quality Gate", executor=quality_gate),
        Step(name="Publish", agent=publisher),
    ],
)
```

---

## Handling Stop in Response

Check if workflow was stopped early:

```python
from agno.workflow import Workflow

workflow = Workflow(name="My Workflow", steps=[...])

response = workflow.run(input="Process this")

# Check the final step's output
if response.step_results:
    last_step = response.step_results[-1]

    # Check if it was a stopping step
    if hasattr(last_step, 'stop') and last_step.stop:
        print("Workflow stopped early!")
        print(f"Reason: {last_step.content}")
    else:
        print("Workflow completed normally")

print(f"Final content: {response.content}")
```

---

## Streaming with Early Stop

Early stop works with streaming:

```python
from agno.run.workflow import WorkflowRunEvent

async def process_with_streaming():
    response_stream = workflow.arun(
        input="Process this data",
        stream=True,
        stream_events=True,
    )

    async for event in response_stream:
        if event.event == WorkflowRunEvent.step_completed.value:
            print(f"Step completed: {event.step_id}")

        elif event.event == WorkflowRunEvent.workflow_completed.value:
            # Check if stopped early
            print("Workflow ended")

        elif event.content:
            print(event.content, end="")
```

---

## Complete Example

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools

# Agents
researcher = Agent(
    name="Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Research topics with sources and data.",
)

analyst = Agent(
    name="Analyst",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze findings and draw conclusions.",
)

writer = Agent(
    name="Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write clear, engaging reports.",
)


# Validation steps
def validate_research(step_input: StepInput) -> StepOutput:
    """Validate research quality"""
    content = step_input.previous_step_content or ""

    checks = {
        "has_sources": "http" in content or "source" in content.lower(),
        "has_data": any(c.isdigit() for c in content),
        "sufficient_length": len(content) > 300,
    }

    failed = [k for k, v in checks.items() if not v]

    if failed:
        return StepOutput(
            content=f"Research validation failed: {', '.join(failed)}",
            stop=True,
            metadata={"failed_checks": failed},
        )

    return StepOutput(
        content=content,
        metadata={"validation": "passed"},
    )


def validate_analysis(step_input: StepInput) -> StepOutput:
    """Validate analysis quality"""
    content = step_input.previous_step_content or ""

    required = ["conclusion", "insight", "finding"]
    has_required = any(word in content.lower() for word in required)

    if not has_required:
        return StepOutput(
            content="Analysis lacks conclusions or insights. "
                    "Please provide actionable analysis.",
            stop=True,
        )

    return StepOutput(content=content)


# Build pipeline with validation gates
workflow = Workflow(
    name="Validated Research Pipeline",
    description="Research → Validate → Analyze → Validate → Write",
    steps=[
        Step(name="Research", agent=researcher),
        Step(name="Validate Research", executor=validate_research),
        Step(name="Analyze", agent=analyst),
        Step(name="Validate Analysis", executor=validate_analysis),
        Step(name="Write Report", agent=writer),
    ],
)

if __name__ == "__main__":
    response = workflow.print_response(
        input="Research renewable energy market trends",
        markdown=True,
    )
```

---

## Best Practices

### Do's

1. **Clear messages** - Explain why workflow stopped
2. **Include metadata** - Add context for handling
3. **Test thoroughly** - Ensure validation catches issues
4. **Use at key points** - Place gates after critical steps

### Don'ts

1. **Don't overuse** - Only stop for genuine problems
2. **Don't be too strict** - Allow reasonable variation
3. **Don't hide details** - Include actionable feedback
4. **Don't forget edge cases** - Handle empty/null content

---

## Summary

| Concept | Description |
|---------|-------------|
| `stop=True` | StepOutput flag to halt workflow |
| **Validation Gate** | Step that checks and potentially stops |
| **Quality Check** | Verify content meets requirements |
| **Error Detection** | Stop on errors or issues |
| **Budget Limits** | Stop when limits exceeded |

---

## Related Documentation

- **Building Workflows:** `docs(new)/workflows/02-building-workflows.md`
- **Running Workflows:** `docs(new)/workflows/03-running-workflows.md`
- **Conditional Patterns:** `docs(new)/workflows/05-conditional-parallel.md`

---

*Last Updated: December 2025 | AGNO 2.3.4*
