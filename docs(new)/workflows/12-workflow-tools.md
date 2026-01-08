# Workflow Tools

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/workflow-tools

---

## Introduction

`WorkflowTools` enables agents to execute workflows as tools. This allows an agent to:

- Invoke complex multi-step workflows on demand
- Choose between multiple workflows based on the task
- Combine workflow execution with regular tools
- Delegate complex tasks to specialized pipelines

---

## Core Concept

```python
from agno.workflow.tools import WorkflowTools

# Create toolkit from workflow
tools = WorkflowTools(workflows=[my_workflow])

# Give tools to an agent
agent = Agent(
    name="Orchestrator",
    tools=[tools],
    instructions="Use the workflow when needed.",
)
```

---

## How It Works

```
User Message
    ↓
Agent receives message
    ↓
Agent decides to use workflow tool
    ↓
Agent calls: workflow_name(input="...")
    ↓
Workflow executes all steps
    ↓
Result returns to agent
    ↓
Agent formats response for user
```

The workflow's `name` becomes the tool name, and `description` becomes the tool description.

---

## Basic Example

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.tools import WorkflowTools
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools

# Define a research workflow
researcher = Agent(
    name="Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Research topics thoroughly.",
)

writer = Agent(
    name="Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write clear summaries.",
)

research_workflow = Workflow(
    name="research_and_summarize",
    description="Research a topic and create a summary",
    steps=[
        Step(name="Research", agent=researcher),
        Step(name="Summarize", agent=writer),
    ],
)

# Create WorkflowTools from the workflow
workflow_tools = WorkflowTools(workflows=[research_workflow])

# Create an orchestrator agent with workflow tools
orchestrator = Agent(
    name="Orchestrator",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[workflow_tools],
    instructions=[
        "You are a helpful assistant.",
        "When users need research, use the research_and_summarize workflow.",
        "For simple questions, answer directly.",
    ],
)

if __name__ == "__main__":
    # Simple question - answers directly
    orchestrator.print_response("What is 2+2?")

    # Research request - uses workflow tool
    orchestrator.print_response(
        "Research the latest developments in quantum computing"
    )
```

---

## Multiple Workflows

Provide multiple workflows for different tasks:

```python
from agno.workflow import Workflow, Step
from agno.workflow.tools import WorkflowTools

# Research workflow
research_workflow = Workflow(
    name="deep_research",
    description="Comprehensive research on a topic with multiple sources",
    steps=[
        Step(name="Web Research", agent=web_researcher),
        Step(name="Academic Research", agent=academic_researcher),
        Step(name="Synthesis", agent=synthesizer),
    ],
)

# Content creation workflow
content_workflow = Workflow(
    name="create_content",
    description="Create polished content from a topic or outline",
    steps=[
        Step(name="Draft", agent=writer),
        Step(name="Edit", agent=editor),
        Step(name="Format", agent=formatter),
    ],
)

# Data analysis workflow
analysis_workflow = Workflow(
    name="analyze_data",
    description="Analyze data and provide insights",
    steps=[
        Step(name="Process", agent=processor),
        Step(name="Analyze", agent=analyst),
        Step(name="Report", agent=reporter),
    ],
)

# Bundle all workflows into tools
workflow_tools = WorkflowTools(
    workflows=[
        research_workflow,
        content_workflow,
        analysis_workflow,
    ]
)

# Orchestrator with access to all workflows
orchestrator = Agent(
    name="Smart Assistant",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[workflow_tools],
    instructions=[
        "You are a versatile assistant with specialized workflows.",
        "",
        "Available workflows:",
        "- deep_research: For comprehensive research tasks",
        "- create_content: For writing and content creation",
        "- analyze_data: For data analysis and insights",
        "",
        "Choose the appropriate workflow based on the task.",
        "For simple questions, answer directly.",
    ],
)
```

---

## WorkflowTools Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `workflows` | `List[Workflow]` | Workflows to expose as tools |

### Workflow Requirements

For a workflow to work well as a tool:

```python
# Good - clear name and description
workflow = Workflow(
    name="research_topic",  # Becomes tool name
    description="Research a topic and summarize findings",  # Tool description
    steps=[...],
)

# Bad - vague name and no description
workflow = Workflow(
    name="wf1",  # Unclear what this does
    steps=[...],  # No description
)
```

---

## Combining with Regular Tools

Mix workflow tools with regular tools:

```python
from agno.agent import Agent
from agno.workflow.tools import WorkflowTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.calculator import CalculatorTools

# Workflow tools for complex tasks
workflow_tools = WorkflowTools(
    workflows=[research_workflow, content_workflow]
)

# Regular tools for simple tasks
search_tools = DuckDuckGoTools()
calc_tools = CalculatorTools()

# Agent with both
smart_agent = Agent(
    name="Multi-Tool Agent",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[
        workflow_tools,   # For complex multi-step tasks
        search_tools,     # For quick searches
        calc_tools,       # For calculations
    ],
    instructions=[
        "You have multiple capabilities:",
        "",
        "WORKFLOWS (for complex tasks):",
        "- research_topic: Deep research with analysis",
        "- create_content: Full content creation pipeline",
        "",
        "DIRECT TOOLS (for simple tasks):",
        "- DuckDuckGo: Quick web searches",
        "- Calculator: Math calculations",
        "",
        "Choose the most efficient approach for each task.",
    ],
)
```

---

## Agent Decision Making

The agent decides when to use workflows based on:

1. **Task complexity** - Simple vs multi-step tasks
2. **Your instructions** - Guidance on when to use each
3. **Tool descriptions** - What each workflow does

### Examples

| User Request | Tool Used | Reason |
|--------------|-----------|--------|
| "What's 5 + 3?" | Calculator | Simple math |
| "What's the weather?" | DuckDuckGo | Quick lookup |
| "Research AI trends and write a report" | research_workflow | Complex, multi-step |
| "Create an article about climate change" | content_workflow | Content creation task |

---

## Workflow Execution Flow

When agent calls a workflow tool:

```python
# User says: "Research AI trends and write a report"

# 1. Agent decides to use workflow
# Agent calls: deep_research(input="AI trends")

# 2. Workflow executes
# Step 1: Web Research → findings
# Step 2: Academic Research → more findings
# Step 3: Synthesis → combined report

# 3. Result returns to agent
# Agent receives: combined report

# 4. Agent responds to user
# Agent: "Here's what I found about AI trends: [report]"
```

---

## Streaming with Workflow Tools

Workflow tools support streaming:

```python
# Agent with workflow tools
agent = Agent(
    name="Research Agent",
    tools=[workflow_tools],
    instructions=["Use workflows for research tasks."],
)

# Streaming execution
agent.print_response(
    "Research quantum computing developments",
    stream=True,
)
```

---

## Async Execution

Works with async patterns:

```python
import asyncio

async def main():
    agent = Agent(
        name="Async Agent",
        tools=[workflow_tools],
    )

    # Async execution
    response = await agent.arun(
        "Research and report on renewable energy"
    )
    print(response.content)

    # Async streaming
    await agent.aprint_response(
        "Create an article about AI ethics",
        stream=True,
    )

asyncio.run(main())
```

---

## Production Example

Complete production-ready setup:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.tools import WorkflowTools
from agno.model.google import Gemini
from agno.db.postgres import PostgresDb
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.exa import ExaTools

# Database for persistence
db = PostgresDb("postgresql+psycopg://user:pass@localhost/db")

# Define specialized agents
web_researcher = Agent(
    name="Web Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Research current events and news.",
)

deep_researcher = Agent(
    name="Deep Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[ExaTools()],
    instructions="Find in-depth, authoritative sources.",
)

analyst = Agent(
    name="Analyst",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Analyze and synthesize research findings.",
)

writer = Agent(
    name="Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write clear, engaging content.",
)

# Define workflows with clear names and descriptions
quick_research = Workflow(
    name="quick_research",
    description="Quick research on current topics. Use for simple factual questions. Takes 5-10 seconds.",
    steps=[
        Step(name="Search", agent=web_researcher),
    ],
    db=db,
)

deep_research = Workflow(
    name="deep_research",
    description="Comprehensive research with multiple sources and analysis. Use for complex topics requiring thorough investigation. Takes 30-60 seconds.",
    steps=[
        Step(name="Web Search", agent=web_researcher),
        Step(name="Deep Search", agent=deep_researcher),
        Step(name="Analysis", agent=analyst),
    ],
    db=db,
)

content_creation = Workflow(
    name="content_creation",
    description="Create polished content including articles, reports, or summaries. Use for writing tasks.",
    steps=[
        Step(name="Research", agent=web_researcher),
        Step(name="Write", agent=writer),
    ],
    db=db,
)

# Bundle workflows
workflow_tools = WorkflowTools(
    workflows=[quick_research, deep_research, content_creation]
)

# Create main orchestrator
main_agent = Agent(
    name="Cirkelline",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[workflow_tools],
    db=db,
    instructions=[
        "You are Cirkelline, a helpful AI assistant.",
        "",
        "WORKFLOW SELECTION:",
        "- quick_research: Simple factual questions",
        "  Example: 'What is the capital of France?'",
        "",
        "- deep_research: Complex analysis or comprehensive research",
        "  Example: 'Analyze the impact of AI on healthcare'",
        "",
        "- content_creation: Writing articles, reports, summaries",
        "  Example: 'Write an article about climate change'",
        "",
        "DIRECT ANSWERS (no workflow needed):",
        "- Greetings and small talk",
        "- Simple calculations",
        "- Questions about your capabilities",
        "",
        "Be friendly, helpful, and efficient.",
    ],
    markdown=True,
)

if __name__ == "__main__":
    # Interactive testing
    main_agent.cli_app(stream=True)
```

---

## Error Handling

Handle workflow errors gracefully:

```python
orchestrator = Agent(
    name="Robust Agent",
    tools=[workflow_tools],
    instructions=[
        "You have access to specialized workflows.",
        "",
        "If a workflow fails or returns an error:",
        "- Acknowledge the issue",
        "- Explain what happened briefly",
        "- Suggest alternatives",
        "- Offer to try a different approach",
        "",
        "Never expose technical error details to users.",
    ],
)
```

---

## Naming Conventions

Good workflow naming for tools:

```python
# Good - verb_noun format, descriptive
Workflow(name="research_topic", description="...")
Workflow(name="create_report", description="...")
Workflow(name="analyze_data", description="...")
Workflow(name="summarize_document", description="...")

# Good - domain-specific names
Workflow(name="deep_research", description="...")
Workflow(name="quick_lookup", description="...")
Workflow(name="content_pipeline", description="...")

# Bad - vague or confusing names
Workflow(name="wf1", description="...")
Workflow(name="process", description="...")
Workflow(name="do_stuff", description="...")
```

---

## Best Practices

### Do's

1. **Descriptive names** - Workflow names become tool names
2. **Clear descriptions** - Help agent choose correctly
3. **Good instructions** - Guide when to use each workflow
4. **Combine wisely** - Mix workflow and regular tools
5. **Test thoroughly** - Ensure agent picks right tool

### Don'ts

1. **Don't overcomplicate** - Keep workflow list manageable
2. **Don't overlap** - Workflows should have distinct purposes
3. **Don't vague** - Clear names and descriptions
4. **Don't forget direct** - Some tasks don't need workflows

---

## Summary

| Concept | Description |
|---------|-------------|
| `WorkflowTools` | Expose workflows as agent tools |
| **Tool Name** | Comes from workflow's `name` |
| **Tool Description** | Comes from workflow's `description` |
| **Multiple Workflows** | Agent chooses based on task |
| **Combined Tools** | Mix workflows with regular tools |

---

## Related Documentation

- **Workflows Overview:** `docs(new)/workflows/01-overview.md`
- **Building Workflows:** `docs(new)/workflows/02-building-workflows.md`
- **Running Workflows:** `docs(new)/workflows/03-running-workflows.md`

---

*Last Updated: December 2025 | AGNO 2.3.4*
