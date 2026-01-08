# AGNO Workflows Documentation Index

**AGNO Version:** 2.3.4
**Total Files:** 17

---

## Quick Reference

| When you need to... | Read this |
|---------------------|-----------|
| Understand what workflows are | `01-overview.md` |
| Build your first workflow | `02-building-workflows.md` |
| Run and get output | `03-running-workflows.md` |
| Add conditions or parallel | `05-conditional-parallel.md` |
| Add loops | `06-iterative-branching.md` |
| Use structured Pydantic I/O | `17-structured-io-events.md` |
| Make workflow conversational | `09-conversational-workflows.md` |
| Run in background | `13-background-execution.md` |

---

## Documentation Structure

### Fundamentals (01-03)

| File | Description |
|------|-------------|
| `01-overview.md` | What are workflows, core concepts, when to use |
| `02-building-workflows.md` | Creating workflows, adding steps, configuration |
| `03-running-workflows.md` | run(), arun(), print_response(), output structure |

### Core Constructs (04-07)

| File | Description |
|------|-------------|
| `04-basic-patterns.md` | Sequential steps, agent steps, function steps, Teams |
| `05-conditional-parallel.md` | Condition, Parallel, else_steps, combining |
| `06-iterative-branching.md` | Loop, end_condition, max_iterations |
| `07-grouped-advanced.md` | Steps grouping, Router, dynamic routing |

### Features (08-13)

| File | Description |
|------|-------------|
| `08-additional-data.md` | Passing extra data via additional_data parameter |
| `09-conversational-workflows.md` | WorkflowAgent, conversation history, when to execute |
| `10-access-previous-steps.md` | previous_step_content, get_step_content(), helpers |
| `11-early-stop.md` | StepOutput with stop=True, validation gates |
| `12-workflow-tools.md` | WorkflowTools, exposing workflows as agent tools |
| `13-background-execution.md` | background=True, polling, get_run(), webhooks |

### Advanced (14-17)

| File | Description |
|------|-------------|
| `14-usage-examples.md` | Streaming with AgentOS, async events, mixed executors |
| `15-advanced-examples.md` | Condition+Parallel combinations, nested patterns |
| `16-router-loop-selector.md` | Router→Loop, Selector pattern, multi-pattern combos |
| `17-structured-io-events.md` | Pydantic I/O, input_schema, events, cancellation |

---

## Key Concepts Quick Reference

### Workflow Constructs

```python
from agno.workflow import (
    Workflow,           # Main workflow container
    Step,               # Basic execution unit
    WorkflowAgent,      # Conversational wrapper
)
from agno.workflow.condition import Condition   # Branching
from agno.workflow.parallel import Parallel     # Concurrent execution
from agno.workflow.loop import Loop             # Iteration
from agno.workflow.router import Router         # Dynamic routing
from agno.workflow.steps import Steps           # Step grouping
from agno.workflow.tools import WorkflowTools   # Expose as tools
```

### Step Types

| Type | Usage |
|------|-------|
| Agent Step | `Step(name="X", agent=my_agent)` |
| Team Step | `Step(name="X", team=my_team)` |
| Function Step | `Step(name="X", executor=my_function)` |
| Class Step | `Step(name="X", executor=MyClass())` |

### StepInput/StepOutput

```python
from agno.workflow.types import StepInput, StepOutput

def my_step(step_input: StepInput) -> StepOutput:
    # Access input
    user_input = step_input.user_input
    previous = step_input.previous_step_content
    data = step_input.additional_data

    # Return output
    return StepOutput(
        content="Result",
        stop=False,  # True to halt workflow
        metadata={"key": "value"},
    )
```

### Running Workflows

```python
# Synchronous
response = workflow.run(input="Query")
workflow.print_response(input="Query", stream=True)

# Asynchronous
response = await workflow.arun(input="Query")
await workflow.aprint_response(input="Query", stream=True)

# Background
response = await workflow.arun(input="Query", background=True)
result = workflow.get_run(response.run_id)
```

---

## Learning Path

**Beginner:**
1. `01-overview.md` - Understand concepts
2. `02-building-workflows.md` - Build first workflow
3. `03-running-workflows.md` - Run and get results
4. `04-basic-patterns.md` - Basic step patterns

**Intermediate:**
5. `05-conditional-parallel.md` - Add branching/concurrency
6. `06-iterative-branching.md` - Add loops
7. `08-additional-data.md` - Pass extra data
8. `10-access-previous-steps.md` - Chain step outputs

**Advanced:**
9. `07-grouped-advanced.md` - Router, Steps grouping
10. `09-conversational-workflows.md` - WorkflowAgent
11. `13-background-execution.md` - Background runs
12. `17-structured-io-events.md` - Pydantic I/O

**Examples:**
13. `14-usage-examples.md` - Streaming patterns
14. `15-advanced-examples.md` - Complex combinations
15. `16-router-loop-selector.md` - Multi-pattern examples

---

## Common Patterns

### Research Pipeline
```
Research (Parallel) → Merge → Analyze → Report
Files: 05, 15, 16
```

### Quality Loop
```
Generate → Validate → [Loop if needed] → Publish
Files: 06, 11
```

### Adaptive Routing
```
Router → [Quick Path | Deep Path with Loop] → Output
Files: 07, 16
```

### Conversational
```
WorkflowAgent → [Execute or Answer] → Maintain History
Files: 09, 16
```

---

*Last Updated: December 2025 | AGNO 2.3.4*
