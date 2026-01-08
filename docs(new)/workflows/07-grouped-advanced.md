# Grouped Steps and Advanced Workflow Patterns

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/workflow-patterns/grouped-steps-workflow

---

## Introduction

This document covers:

1. **Grouped Steps (Steps)** - Reusable step sequences for modular design
2. **Advanced Patterns** - Combining multiple patterns for sophisticated workflows

---

## Part 1: Grouped Steps (Steps Object)

Organize multiple steps into logical, reusable sequences.

### Core Concept

```python
from agno.workflow.steps import Steps

article_sequence = Steps(
    name="article_creation",
    description="Complete article workflow",
    steps=[research_step, writing_step, editing_step],
)
```

### How It Works

1. Group related steps into a `Steps` object
2. Use the Steps object in workflows like a single step
3. Steps execute sequentially within the group
4. Reuse across multiple workflows

---

### Basic Grouped Steps Example

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.steps import Steps
from agno.tools.duckduckgo import DuckDuckGoTools

# Define agents
researcher = Agent(
    name="Research Agent",
    tools=[DuckDuckGoTools()],
    instructions="Research the topic and provide key facts.",
)

writer = Agent(
    name="Writing Agent",
    instructions="Write comprehensive articles. Make it engaging.",
)

editor = Agent(
    name="Editor Agent",
    instructions="Review and edit for clarity, grammar, and flow.",
)

# Define individual steps
research_step = Step(
    name="research",
    agent=researcher,
    description="Research the topic",
)

writing_step = Step(
    name="writing",
    agent=writer,
    description="Write article",
)

editing_step = Step(
    name="editing",
    agent=editor,
    description="Edit and polish",
)

# Create a Steps sequence
article_creation_sequence = Steps(
    name="article_creation",
    description="Complete article workflow from research to edit",
    steps=[research_step, writing_step, editing_step],
)

# Use in workflow
workflow = Workflow(
    name="Article Creation Workflow",
    description="Automated article creation",
    steps=[article_creation_sequence],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Write an article about renewable energy benefits",
        markdown=True,
    )
```

---

### Multiple Step Groups

Use multiple grouped sequences in one workflow:

```python
# Research sequence
research_sequence = Steps(
    name="research_phase",
    description="Multi-source research",
    steps=[
        Step(name="web_research", agent=web_researcher),
        Step(name="data_analysis", agent=analyst),
    ],
)

# Content sequence
content_sequence = Steps(
    name="content_phase",
    description="Content creation and review",
    steps=[
        Step(name="writing", agent=writer),
        Step(name="editing", agent=editor),
        Step(name="review", agent=reviewer),
    ],
)

# Combined workflow
workflow = Workflow(
    name="Full Content Pipeline",
    steps=[
        research_sequence,
        content_sequence,
    ],
)
```

---

### Reusing Step Groups

Same sequence in multiple workflows:

```python
# Define reusable sequence once
quality_assurance_sequence = Steps(
    name="qa_phase",
    description="Quality assurance checks",
    steps=[
        Step(name="fact_check", agent=fact_checker),
        Step(name="grammar_check", agent=grammar_agent),
        Step(name="style_review", agent=style_agent),
    ],
)

# Use in blog workflow
blog_workflow = Workflow(
    name="Blog Pipeline",
    steps=[
        blog_research_step,
        blog_writing_step,
        quality_assurance_sequence,  # Reused
    ],
)

# Use in report workflow
report_workflow = Workflow(
    name="Report Pipeline",
    steps=[
        report_research_step,
        report_writing_step,
        quality_assurance_sequence,  # Reused
    ],
)
```

---

### When to Use Grouped Steps

| Use Case | Example |
|----------|---------|
| **Logical Grouping** | Research, Content, QA phases |
| **Reusability** | Same QA sequence in multiple workflows |
| **Organization** | Keep related steps together |
| **Modularity** | Mix and match step sequences |

---

## Part 2: Advanced Patterns

Combine multiple patterns for sophisticated workflows.

### Pattern Combination Overview

You can combine:
- **Condition** - Conditional logic
- **Parallel** - Concurrent execution
- **Loop** - Iterative execution
- **Router** - Dynamic routing
- **Steps** - Grouped sequences
- **Custom Functions** - Python logic

---

### Nested Steps with Condition and Parallel

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.steps import Steps
from agno.workflow.condition import Condition
from agno.workflow.parallel import Parallel
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.exa import ExaTools
from agno.tools.hackernews import HackerNewsTools

# Define agents
researcher = Agent(
    name="Research Agent",
    tools=[DuckDuckGoTools()],
    instructions="Research the topic thoroughly.",
)

tech_researcher = Agent(
    name="Tech Researcher",
    tools=[HackerNewsTools()],
    instructions="Research tech topics from HackerNews.",
)

news_researcher = Agent(
    name="News Researcher",
    tools=[ExaTools()],
    instructions="Research current news and trends.",
)

writer = Agent(
    name="Writer",
    instructions="Write comprehensive articles.",
)

editor = Agent(
    name="Editor",
    instructions="Edit for clarity and flow.",
)

content_agent = Agent(
    name="Content Agent",
    instructions="Prepare content for writing.",
)

# Define steps
initial_research_step = Step(name="InitialResearch", agent=researcher)
tech_research_step = Step(name="TechResearch", agent=tech_researcher)
news_research_step = Step(name="NewsResearch", agent=news_researcher)
content_prep_step = Step(name="ContentPrep", agent=content_agent)
writing_step = Step(name="Writing", agent=writer)
editing_step = Step(name="Editing", agent=editor)


# Condition evaluator
def is_tech_topic(step_input) -> bool:
    """Check if topic is tech-related"""
    message = step_input.input.lower() if step_input.input else ""
    tech_keywords = ["ai", "machine learning", "tech", "software", "startup"]
    return any(keyword in message for keyword in tech_keywords)


# Complex Steps sequence with nested patterns
article_creation_sequence = Steps(
    name="ArticleCreation",
    description="Article workflow with conditional parallel research",
    steps=[
        initial_research_step,
        # Condition with Parallel inside
        Condition(
            name="TechResearchCondition",
            description="If tech topic, do specialized parallel research",
            evaluator=is_tech_topic,
            steps=[
                Parallel(
                    tech_research_step,
                    news_research_step,
                    name="SpecializedResearch",
                    description="Parallel tech and news research",
                ),
                content_prep_step,
            ],
        ),
        writing_step,
        editing_step,
    ],
)

# Workflow using the complex sequence
workflow = Workflow(
    name="Enhanced Article Workflow",
    description="Conditional parallel research in grouped steps",
    steps=[article_creation_sequence],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Write about AI developments in machine learning",
        markdown=True,
        stream=True,
    )
```

---

### Multi-Pattern Workflow

Combining all patterns in one workflow:

```python
from agno.workflow import Workflow, Step, Parallel, Loop
from agno.workflow.condition import Condition
from agno.workflow.router import Router
from agno.workflow.types import StepInput, StepOutput
from typing import List

# Custom post-processor function
def research_post_processor(step_input: StepInput) -> StepOutput:
    """Post-process and consolidate research data"""
    research_data = step_input.previous_step_content or ""

    try:
        # Analyze research quality
        word_count = len(research_data.split())
        has_tech = any(kw in research_data.lower()
                      for kw in ["technology", "ai", "software"])
        has_business = any(kw in research_data.lower()
                          for kw in ["market", "business", "revenue"])

        # Create enhanced summary
        enhanced = f"""
        ## Research Analysis Report

        **Data Quality:** {"High" if word_count > 200 else "Limited"}

        **Coverage:**
        - Technical: {"Yes" if has_tech else "No"}
        - Business: {"Yes" if has_business else "No"}

        **Findings:**
        {research_data}
        """

        return StepOutput(content=enhanced.strip(), success=True)

    except Exception as e:
        return StepOutput(
            content=f"Post-processing failed: {str(e)}",
            success=False,
            error=str(e),
        )


# Condition evaluators
def is_tech_topic(step_input: StepInput) -> bool:
    content = step_input.input or ""
    return any(kw in content.lower() for kw in ["tech", "ai", "software"])

def is_business_topic(step_input: StepInput) -> bool:
    content = step_input.input or ""
    return any(kw in content.lower() for kw in ["market", "business", "strategy"])

# Loop end condition
def research_quality_check(outputs: List[StepOutput]) -> bool:
    if not outputs:
        return False
    total_len = sum(len(o.content or "") for o in outputs)
    return total_len > 300

# Router selector
def content_type_selector(step_input: StepInput) -> List[Step]:
    content = step_input.previous_step_content or ""
    if "technical" in content.lower():
        return [technical_report_step]
    elif "market" in content.lower():
        return [market_report_step]
    else:
        return [general_report_step]


# Advanced multi-pattern workflow
workflow = Workflow(
    name="Advanced Multi-Pattern Workflow",
    steps=[
        # Parallel conditions for research
        Parallel(
            Condition(
                name="Tech Check",
                evaluator=is_tech_topic,
                steps=[Step(name="Tech Research", agent=tech_researcher)],
            ),
            Condition(
                name="Business Check",
                evaluator=is_business_topic,
                steps=[
                    # Loop inside condition
                    Loop(
                        name="Deep Business Research",
                        steps=[Step(name="Market Research", agent=market_researcher)],
                        end_condition=research_quality_check,
                        max_iterations=3,
                    )
                ],
            ),
            name="Conditional Research Phase",
        ),
        # Custom function step
        Step(
            name="Research Post-Processing",
            executor=research_post_processor,
            description="Consolidate research findings",
        ),
        # Router for content type
        Router(
            name="Content Type Router",
            selector=content_type_selector,
            choices=[technical_report_step, market_report_step, general_report_step],
        ),
        # Final review
        Step(name="Final Review", agent=reviewer),
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        "Create comprehensive analysis of sustainable technology trends "
        "and their business impact for 2025",
        markdown=True,
    )
```

---

### Early Termination Pattern

Stop workflow when quality conditions aren't met:

```python
def validation_step(step_input: StepInput) -> StepOutput:
    """Validate data and potentially stop workflow"""
    validation_result = step_input.previous_step_content or ""

    if "INVALID" in validation_result.upper():
        return StepOutput(
            content="Validation failed. Workflow stopped.",
            stop=True,  # Stop entire workflow
        )
    else:
        return StepOutput(
            content="Validation passed. Continuing...",
            stop=False,
        )

workflow = Workflow(
    name="Data Processing with Validation",
    steps=[
        data_validator,      # Validate input
        validation_step,     # Check and possibly stop
        data_processor,      # Only if validation passed
        report_generator,    # Only if processing completed
    ],
)
```

---

### Conversation-Aware Workflow Pattern

Use workflow history for context-aware processing:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.db.sqlite import SqliteDb

tutor_agent = Agent(
    name="AI Tutor",
    instructions=[
        "You are an expert tutor providing personalized support.",
        "You have access to our full conversation history.",
        "Build on previous discussions - don't repeat information.",
        "Reference what the student has told you earlier.",
        "Adapt your teaching style based on what you've learned.",
    ],
)

tutor_workflow = Workflow(
    name="AI Tutor",
    description="Conversational tutoring with history awareness",
    db=SqliteDb(db_file="tmp/tutor_workflow.db"),
    steps=[
        Step(name="AI Tutoring", agent=tutor_agent),
    ],
    add_workflow_history_to_steps=True,  # Enable history
)

def demo_tutoring():
    """Interactive tutoring session"""
    tutor_workflow.cli_app(
        session_id="tutor_demo",
        user="Student",
        emoji="",
        stream=True,
        show_step_details=True,
    )

if __name__ == "__main__":
    demo_tutoring()
```

---

## Pattern Selection Guide

| Requirement | Recommended Pattern |
|-------------|---------------------|
| Linear pipeline | Sequential |
| Need logging/debugging | Step-Based |
| Custom transformations | Custom Function |
| Total control | Fully Python |
| Conditional processing | Condition |
| Independent parallel tasks | Parallel |
| Quality-driven iteration | Loop |
| Dynamic path selection | Router |
| Reusable sequences | Steps |
| Complex combinations | Multi-Pattern |

---

## Best Practices for Advanced Patterns

### General

1. **Start simple** - Add complexity only when needed
2. **Test components** - Verify each pattern works alone first
3. **Use meaningful names** - Clear identification in logs
4. **Add descriptions** - Document purpose of each component

### Nesting

1. **Limit depth** - Avoid excessive nesting (3 levels max)
2. **Keep it readable** - Extract complex logic to functions
3. **Monitor performance** - Nested patterns can be slow

### Debugging

1. **Enable streaming** - See progress in real-time
2. **Log decisions** - Print in evaluators and selectors
3. **Use debug_mode** - Enable detailed logging
4. **Check step outputs** - Verify data flow between steps

### Production

1. **Add database** - Persist sessions and state
2. **Set limits** - max_iterations on loops
3. **Handle errors** - Graceful failure with stop=True
4. **Monitor metrics** - Track execution time and costs

---

## Summary

| Pattern | Purpose |
|---------|---------|
| **Steps** | Group related steps for reuse |
| **Nested Patterns** | Condition/Parallel inside Steps |
| **Multi-Pattern** | Combine all patterns |
| **Early Termination** | Stop on validation failure |
| **History-Aware** | Use workflow history for context |

---

## Related Documentation

- **Overview:** `docs(new)/workflows/01-overview.md`
- **Building:** `docs(new)/workflows/02-building-workflows.md`
- **Running:** `docs(new)/workflows/03-running-workflows.md`
- **Basic Patterns:** `docs(new)/workflows/04-basic-patterns.md`
- **Conditional/Parallel:** `docs(new)/workflows/05-conditional-parallel.md`
- **Iterative/Branching:** `docs(new)/workflows/06-iterative-branching.md`

---

*Last Updated: December 2025 | AGNO 2.3.4*
