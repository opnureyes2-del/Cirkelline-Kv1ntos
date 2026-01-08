# Advanced Workflow Examples

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/usage

---

## Introduction

This documentation covers advanced workflow patterns that combine multiple constructs like Condition, Parallel, Loop, and custom executors. These examples demonstrate real-world usage of complex workflow orchestration.

---

## Condition with Multiple Steps

A Condition can contain a list of steps that all execute when the condition is true:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.condition import Condition
from agno.workflow.types import StepInput
from agno.model.google import Gemini

# Define agents
researcher = Agent(
    name="Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Research topics thoroughly.",
)

analyst = Agent(
    name="Analyst",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze research findings.",
)

writer = Agent(
    name="Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write clear summaries.",
)

reviewer = Agent(
    name="Reviewer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Review and improve content.",
)


def needs_deep_analysis(step_input: StepInput) -> bool:
    """Check if topic requires deep analysis"""
    content = step_input.previous_step_content or ""
    complex_keywords = ["complex", "technical", "detailed", "comprehensive"]
    return any(kw in content.lower() for kw in complex_keywords)


# Workflow with conditional multi-step branch
workflow = Workflow(
    name="Conditional Multi-Step",
    steps=[
        Step(name="Research", agent=researcher),
        Condition(
            name="Deep Analysis Branch",
            evaluator=needs_deep_analysis,
            steps=[
                # All these steps run when condition is True
                Step(name="Deep Analysis", agent=analyst),
                Step(name="Expert Review", agent=reviewer),
                Step(name="Final Write", agent=writer),
            ],
        ),
        # This step always runs after the condition block
        Step(name="Summary", agent=writer),
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Research the complex technical aspects of quantum computing",
        markdown=True,
    )
```

---

## Condition with Streaming

Streaming with conditional workflows:

```python
import asyncio
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.condition import Condition
from agno.workflow.types import StepInput
from agno.model.google import Gemini


def is_technical(step_input: StepInput) -> bool:
    """Check if query is technical"""
    user_input = step_input.user_input or ""
    technical_terms = ["code", "api", "database", "programming", "algorithm"]
    return any(term in user_input.lower() for term in technical_terms)


technical_expert = Agent(
    name="Technical Expert",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Provide technical explanations with code examples.",
)

general_assistant = Agent(
    name="General Assistant",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Provide helpful general information.",
)

workflow = Workflow(
    name="Conditional Streaming",
    steps=[
        Condition(
            name="Technical Check",
            evaluator=is_technical,
            steps=[Step(name="Technical Response", agent=technical_expert)],
            else_steps=[Step(name="General Response", agent=general_assistant)],
        ),
    ],
)


async def main():
    # Streaming execution
    response_stream = workflow.arun(
        input="How do I write a recursive function?",
        stream=True,
    )

    async for chunk in response_stream:
        if hasattr(chunk, 'content') and chunk.content:
            print(chunk.content, end="", flush=True)

    print()  # Newline at end


asyncio.run(main())
```

---

## Parallel Conditions

Run multiple conditions simultaneously:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.condition import Condition
from agno.workflow.parallel import Parallel
from agno.workflow.types import StepInput
from agno.model.google import Gemini

# Specialized agents
sentiment_agent = Agent(
    name="Sentiment Analyzer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze sentiment of text.",
)

keyword_agent = Agent(
    name="Keyword Extractor",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Extract key terms and topics.",
)

summary_agent = Agent(
    name="Summarizer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Create concise summaries.",
)

technical_agent = Agent(
    name="Technical Analyst",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Provide technical analysis.",
)


def has_sentiment_request(step_input: StepInput) -> bool:
    """Check if sentiment analysis requested"""
    user_input = step_input.user_input or ""
    return "sentiment" in user_input.lower() or "feeling" in user_input.lower()


def has_keyword_request(step_input: StepInput) -> bool:
    """Check if keyword extraction requested"""
    user_input = step_input.user_input or ""
    return "keyword" in user_input.lower() or "topic" in user_input.lower()


def has_technical_request(step_input: StepInput) -> bool:
    """Check if technical analysis requested"""
    user_input = step_input.user_input or ""
    return "technical" in user_input.lower() or "code" in user_input.lower()


# Parallel conditions - each evaluated simultaneously
workflow = Workflow(
    name="Parallel Conditions Analysis",
    steps=[
        Parallel(
            Condition(
                name="Sentiment Branch",
                evaluator=has_sentiment_request,
                steps=[Step(name="Sentiment", agent=sentiment_agent)],
            ),
            Condition(
                name="Keyword Branch",
                evaluator=has_keyword_request,
                steps=[Step(name="Keywords", agent=keyword_agent)],
            ),
            Condition(
                name="Technical Branch",
                evaluator=has_technical_request,
                steps=[Step(name="Technical", agent=technical_agent)],
            ),
            name="Multi-Analysis",
        ),
        Step(name="Summary", agent=summary_agent),
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Analyze this code for sentiment and extract keywords",
        markdown=True,
    )
```

---

## Parallel with Custom Function

Combine parallel execution with custom function steps:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.parallel import Parallel
from agno.workflow.types import StepInput, StepOutput
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools

# Research agents
news_researcher = Agent(
    name="News Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Research current news.",
)

academic_researcher = Agent(
    name="Academic Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Research academic sources.",
)


def merge_research(step_input: StepInput) -> StepOutput:
    """Merge parallel research results"""
    previous_outputs = step_input.previous_step_outputs or []

    # Collect all research findings
    findings = []
    for output in previous_outputs:
        if hasattr(output, 'content') and output.content:
            findings.append(output.content)

    merged = "## Combined Research Findings\n\n"
    for i, finding in enumerate(findings, 1):
        merged += f"### Source {i}\n{finding}\n\n"

    return StepOutput(
        content=merged,
        metadata={"source_count": len(findings)},
    )


synthesis_agent = Agent(
    name="Synthesizer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Synthesize research into coherent analysis.",
)

# Workflow with parallel research + custom merge
workflow = Workflow(
    name="Parallel Research Pipeline",
    steps=[
        Parallel(
            Step(name="News Research", agent=news_researcher),
            Step(name="Academic Research", agent=academic_researcher),
            name="Research Phase",
        ),
        Step(name="Merge Results", executor=merge_research),
        Step(name="Synthesize", agent=synthesis_agent),
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Research the impact of AI on healthcare",
        markdown=True,
    )
```

---

## Parallel with Streaming and AgentOS

Complete example with AgentOS integration:

```python
import asyncio
from agno.agent import Agent
from agno.playground import AgentOS
from agno.workflow import Workflow, Step
from agno.workflow.parallel import Parallel
from agno.workflow.types import StepInput, StepOutput
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools

# Research agents
web_researcher = Agent(
    name="Web Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Research current events and news.",
)

analyst = Agent(
    name="Research Analyst",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze and interpret findings.",
)

writer = Agent(
    name="Report Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write comprehensive reports.",
)


def format_for_report(step_input: StepInput) -> StepOutput:
    """Format parallel results for report generation"""
    previous_outputs = step_input.previous_step_outputs or []
    user_input = step_input.user_input or ""

    sections = []
    for i, output in enumerate(previous_outputs, 1):
        if hasattr(output, 'content') and output.content:
            sections.append(f"## Section {i}\n{output.content}")

    formatted = f"# Research Report: {user_input}\n\n"
    formatted += "\n\n".join(sections)

    return StepOutput(content=formatted)


# Parallel research workflow
research_workflow = Workflow(
    name="Comprehensive Research",
    description="Parallel research with synthesis and reporting",
    steps=[
        Parallel(
            Step(name="Web Research", agent=web_researcher),
            Step(name="Analysis", agent=analyst),
            name="Research Phase",
        ),
        Step(name="Format", executor=format_for_report),
        Step(name="Report", agent=writer),
    ],
)

# Register with AgentOS
os = AgentOS(
    workflows=[research_workflow],
)


async def main():
    print("=== Parallel Research with Streaming ===\n")

    response_stream = research_workflow.arun(
        input="Research trends in renewable energy",
        stream=True,
    )

    async for chunk in response_stream:
        if hasattr(chunk, 'content') and chunk.content:
            print(chunk.content, end="", flush=True)

    print("\n\n=== Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Loop with Parallel Steps

Iterate with parallel execution in each iteration:

```python
from typing import List
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.loop import Loop
from agno.workflow.parallel import Parallel
from agno.workflow.types import StepInput, StepOutput
from agno.model.google import Gemini

reviewer_1 = Agent(
    name="Reviewer 1",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Review content for clarity.",
)

reviewer_2 = Agent(
    name="Reviewer 2",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Review content for accuracy.",
)

improver = Agent(
    name="Improver",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Improve content based on feedback.",
)


def quality_met(outputs: List[StepOutput]) -> bool:
    """Check if quality threshold reached"""
    if not outputs:
        return False

    last_output = outputs[-1]
    content = last_output.content or ""

    # Example quality check
    has_structure = "##" in content
    sufficient_length = len(content) > 500
    has_conclusion = "conclusion" in content.lower()

    return has_structure and sufficient_length and has_conclusion


# Loop with parallel review at each iteration
workflow = Workflow(
    name="Iterative Parallel Review",
    steps=[
        Loop(
            name="Review Loop",
            steps=[
                Parallel(
                    Step(name="Review 1", agent=reviewer_1),
                    Step(name="Review 2", agent=reviewer_2),
                    name="Parallel Review",
                ),
                Step(name="Improve", agent=improver),
            ],
            end_condition=quality_met,
            max_iterations=3,
        ),
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Write a comprehensive guide to Python best practices",
        markdown=True,
    )
```

---

## Nested Conditions

Conditions inside conditions:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.condition import Condition
from agno.workflow.types import StepInput
from agno.model.google import Gemini

beginner_helper = Agent(
    name="Beginner Helper",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Explain concepts simply for beginners.",
)

intermediate_helper = Agent(
    name="Intermediate Helper",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Provide balanced explanations.",
)

expert_helper = Agent(
    name="Expert Helper",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Provide in-depth technical details.",
)

code_generator = Agent(
    name="Code Generator",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Generate production-ready code.",
)


def is_beginner(step_input: StepInput) -> bool:
    additional = step_input.additional_data or {}
    return additional.get("skill_level") == "beginner"


def is_expert(step_input: StepInput) -> bool:
    additional = step_input.additional_data or {}
    return additional.get("skill_level") == "expert"


def wants_code(step_input: StepInput) -> bool:
    user_input = step_input.user_input or ""
    return "code" in user_input.lower() or "example" in user_input.lower()


# Nested conditions for skill-based routing
workflow = Workflow(
    name="Skill-Based Assistant",
    steps=[
        Condition(
            name="Beginner Check",
            evaluator=is_beginner,
            steps=[Step(name="Beginner Help", agent=beginner_helper)],
            else_steps=[
                Condition(
                    name="Expert Check",
                    evaluator=is_expert,
                    steps=[
                        Step(name="Expert Help", agent=expert_helper),
                        Condition(
                            name="Code Request",
                            evaluator=wants_code,
                            steps=[Step(name="Generate Code", agent=code_generator)],
                        ),
                    ],
                    else_steps=[Step(name="Intermediate Help", agent=intermediate_helper)],
                ),
            ],
        ),
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Explain recursion with code example",
        additional_data={"skill_level": "expert"},
        markdown=True,
    )
```

---

## Router with Parallel Fallback

Dynamic routing with parallel fallback:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.router import Router
from agno.workflow.parallel import Parallel
from agno.workflow.types import StepInput
from agno.model.google import Gemini

# Specialized agents
math_agent = Agent(
    name="Math Expert",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Solve mathematical problems.",
)

science_agent = Agent(
    name="Science Expert",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Answer science questions.",
)

history_agent = Agent(
    name="History Expert",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Provide historical information.",
)

general_agent = Agent(
    name="General Expert",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Answer general questions.",
)


def route_by_topic(step_input: StepInput) -> str:
    """Route to appropriate specialist"""
    user_input = (step_input.user_input or "").lower()

    if any(kw in user_input for kw in ["math", "calculate", "equation", "number"]):
        return "math_step"
    elif any(kw in user_input for kw in ["science", "physics", "chemistry", "biology"]):
        return "science_step"
    elif any(kw in user_input for kw in ["history", "historical", "ancient", "century"]):
        return "history_step"
    else:
        return "fallback"  # Route to parallel fallback


workflow = Workflow(
    name="Smart Router",
    steps=[
        Router(
            name="Topic Router",
            router=route_by_topic,
            routes={
                "math_step": Step(name="Math", agent=math_agent),
                "science_step": Step(name="Science", agent=science_agent),
                "history_step": Step(name="History", agent=history_agent),
                "fallback": Parallel(
                    # When topic unclear, consult multiple experts
                    Step(name="General", agent=general_agent),
                    Step(name="Science Check", agent=science_agent),
                    name="Multi-Expert Fallback",
                ),
            },
        ),
    ],
)

if __name__ == "__main__":
    # Clear topic - routes to specialist
    workflow.print_response("What is the quadratic formula?")

    # Unclear topic - uses parallel fallback
    workflow.print_response("Tell me about interesting phenomena")
```

---

## Class-Based Parallel Executor

Using class instances for stateful parallel processing:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.parallel import Parallel
from agno.workflow.types import StepInput, StepOutput
from agno.model.google import Gemini


class TopicAnalyzer:
    """Stateful analyzer for specific topic"""

    def __init__(self, topic: str, focus_areas: list):
        self.topic = topic
        self.focus_areas = focus_areas
        self.analysis_count = 0

    def __call__(self, step_input: StepInput) -> StepOutput:
        """Execute analysis"""
        self.analysis_count += 1
        content = step_input.previous_step_content or step_input.user_input or ""

        analysis = f"## {self.topic} Analysis (Run #{self.analysis_count})\n\n"
        analysis += f"**Focus Areas:** {', '.join(self.focus_areas)}\n\n"
        analysis += f"**Input Content:**\n{content[:500]}...\n\n"
        analysis += f"**Analysis:** Based on {self.topic} perspective...\n"

        return StepOutput(
            content=analysis,
            metadata={
                "topic": self.topic,
                "analysis_count": self.analysis_count,
            },
        )


# Create specialized analyzers
technical_analyzer = TopicAnalyzer(
    topic="Technical",
    focus_areas=["architecture", "scalability", "performance"],
)

business_analyzer = TopicAnalyzer(
    topic="Business",
    focus_areas=["market fit", "ROI", "competitive advantage"],
)

risk_analyzer = TopicAnalyzer(
    topic="Risk",
    focus_areas=["security", "compliance", "dependencies"],
)

synthesizer = Agent(
    name="Synthesizer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Synthesize multiple analyses into comprehensive report.",
)

# Parallel class-based analysis
workflow = Workflow(
    name="Multi-Perspective Analysis",
    steps=[
        Parallel(
            Step(name="Technical Analysis", executor=technical_analyzer),
            Step(name="Business Analysis", executor=business_analyzer),
            Step(name="Risk Analysis", executor=risk_analyzer),
            name="Parallel Perspectives",
        ),
        Step(name="Synthesis", agent=synthesizer),
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        input="Evaluate the proposal to migrate to microservices architecture",
        markdown=True,
    )
```

---

## Complete Production Example

Full production workflow combining multiple patterns:

```python
import asyncio
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.parallel import Parallel
from agno.workflow.condition import Condition
from agno.workflow.loop import Loop
from agno.workflow.types import StepInput, StepOutput
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.db.postgres import PostgresDb
from typing import List

# Database for persistence
db = PostgresDb("postgresql+psycopg://user:pass@localhost/db")

# Research agents
web_researcher = Agent(
    name="Web Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Research current information from the web.",
)

analyst = Agent(
    name="Research Analyst",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze research findings critically.",
)

writer = Agent(
    name="Report Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write clear, professional reports.",
)

reviewer = Agent(
    name="Quality Reviewer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Review content for quality and accuracy.",
)


def needs_deep_research(step_input: StepInput) -> bool:
    """Check if query requires deep research"""
    additional = step_input.additional_data or {}
    return additional.get("deep_research", False)


def merge_research(step_input: StepInput) -> StepOutput:
    """Merge parallel research results"""
    outputs = step_input.previous_step_outputs or []

    merged_content = "## Research Compilation\n\n"
    for i, output in enumerate(outputs, 1):
        if hasattr(output, 'content') and output.content:
            merged_content += f"### Source {i}\n{output.content}\n\n"

    return StepOutput(
        content=merged_content,
        metadata={"source_count": len(outputs)},
    )


def quality_acceptable(outputs: List[StepOutput]) -> bool:
    """Check if quality is acceptable"""
    if not outputs:
        return False

    last_content = outputs[-1].content or ""
    return len(last_content) > 1000 and "conclusion" in last_content.lower()


# Production workflow
production_workflow = Workflow(
    name="Production Research Pipeline",
    description="Comprehensive research with quality assurance",
    db=db,
    steps=[
        # Conditional deep vs quick research
        Condition(
            name="Research Depth",
            evaluator=needs_deep_research,
            steps=[
                # Deep research: parallel sources
                Parallel(
                    Step(name="Web Research 1", agent=web_researcher),
                    Step(name="Web Research 2", agent=web_researcher),
                    name="Parallel Research",
                ),
                Step(name="Merge", executor=merge_research),
            ],
            else_steps=[
                # Quick research: single source
                Step(name="Quick Research", agent=web_researcher),
            ],
        ),
        # Analysis
        Step(name="Analysis", agent=analyst),
        # Quality loop
        Loop(
            name="Quality Improvement",
            steps=[
                Step(name="Write", agent=writer),
                Step(name="Review", agent=reviewer),
            ],
            end_condition=quality_acceptable,
            max_iterations=2,
        ),
    ],
)


async def main():
    print("=== Production Research Pipeline ===\n")

    # Deep research mode
    response_stream = production_workflow.arun(
        input="Research the future of quantum computing",
        additional_data={"deep_research": True},
        stream=True,
    )

    async for chunk in response_stream:
        if hasattr(chunk, 'content') and chunk.content:
            print(chunk.content, end="", flush=True)

    print("\n\n=== Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Summary

| Pattern | Description |
|---------|-------------|
| **Condition + Steps** | Multiple steps in a conditional branch |
| **Parallel Conditions** | Multiple conditions evaluated simultaneously |
| **Parallel + Custom** | Custom functions processing parallel results |
| **Loop + Parallel** | Parallel execution within iterations |
| **Nested Conditions** | Conditions inside conditions |
| **Router + Parallel** | Dynamic routing with parallel fallbacks |
| **Class Executors** | Stateful processing with class instances |

---

## Best Practices

### Do's

1. **Clear evaluators** - Make condition functions descriptive
2. **Handle all cases** - Use else_steps for fallbacks
3. **Limit nesting** - Keep complexity manageable
4. **Use metadata** - Track decisions for debugging
5. **Test combinations** - Verify all paths work

### Don'ts

1. **Don't over-nest** - More than 3 levels is hard to maintain
2. **Don't skip fallbacks** - Always handle unexpected cases
3. **Don't ignore order** - Parallel results may arrive in any order
4. **Don't forget state** - Class executors maintain state between calls

---

## Related Documentation

- **Conditional Patterns:** `docs(new)/workflows/05-conditional-parallel.md`
- **Loop Patterns:** `docs(new)/workflows/06-loops-iterative.md`
- **Custom Executors:** `docs(new)/workflows/04-basic-patterns.md`
- **Usage Examples:** `docs(new)/workflows/14-usage-examples.md`

---

*Last Updated: December 2025 | AGNO 2.3.4*
