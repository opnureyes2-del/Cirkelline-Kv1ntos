# Conversational Workflows (WorkflowAgent)

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/conversational-workflows

---

## Introduction

A `WorkflowAgent` wraps a workflow to make it user-facing and conversational. It decides when to:

1. **Answer directly** - Handle greetings, clarifications, simple questions
2. **Execute the workflow** - Run the full workflow for complex requests

This creates a natural conversational interface while maintaining workflow structure.

---

## Core Concept

```python
from agno.workflow import Workflow, WorkflowAgent

# Define your workflow
workflow = Workflow(
    name="Research Pipeline",
    steps=[research_step, analysis_step, report_step],
)

# Wrap it with WorkflowAgent
workflow_agent = WorkflowAgent(
    workflow=workflow,
    name="Research Assistant",
    instructions="Help users with research tasks.",
)

# Now it can converse AND execute workflows
workflow_agent.print_response("Hello!")  # Answers directly
workflow_agent.print_response("Research AI trends")  # Executes workflow
```

---

## How It Works

```
User Message
    ↓
WorkflowAgent receives message
    ↓
Decision: Answer or Execute?
    ├── Simple query → Answer directly (no workflow)
    └── Complex task → Execute workflow → Return result
    ↓
Response to User
```

The WorkflowAgent uses its instructions and judgment to decide the appropriate action.

---

## Basic Example

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step, WorkflowAgent
from agno.model.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools

# Define agents for the workflow
researcher = Agent(
    name="Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Research topics thoroughly.",
)

writer = Agent(
    name="Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write clear, engaging content.",
)

# Define workflow steps
research_step = Step(
    name="Research",
    agent=researcher,
    description="Research the topic",
)

writing_step = Step(
    name="Write",
    agent=writer,
    description="Write the content",
)

# Create the workflow
content_workflow = Workflow(
    name="Content Creation Pipeline",
    description="Research and write content",
    steps=[research_step, writing_step],
)

# Wrap with WorkflowAgent
content_assistant = WorkflowAgent(
    workflow=content_workflow,
    name="Content Assistant",
    model=Gemini(id="gemini-2.5-flash"),
    instructions=[
        "You are a helpful content creation assistant.",
        "For simple questions, answer directly.",
        "For content creation requests, use the workflow.",
        "Be friendly and helpful in all interactions.",
    ],
    markdown=True,
)

if __name__ == "__main__":
    # This answers directly (no workflow)
    content_assistant.print_response("Hi! What can you help me with?")

    # This executes the workflow
    content_assistant.print_response(
        "Write an article about sustainable energy trends"
    )
```

---

## WorkflowAgent Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `workflow` | `Workflow` | The workflow to wrap |
| `name` | `str` | Agent name |
| `model` | `Model` | Model for the agent |
| `instructions` | `List[str]` | Behavioral instructions |
| `markdown` | `bool` | Enable markdown output |
| `db` | `Database` | Database for persistence |
| `session_id` | `str` | Session identifier |
| `user_id` | `str` | User identifier |

---

## When Does WorkflowAgent Execute?

The agent decides based on:

1. **Message complexity** - Simple vs complex requests
2. **Instructions** - Your guidance on when to execute
3. **Intent detection** - Understanding user's goal

### Examples

| User Message | Action | Reason |
|--------------|--------|--------|
| "Hello!" | Answer directly | Simple greeting |
| "What can you do?" | Answer directly | Explanation request |
| "Thanks!" | Answer directly | Acknowledgment |
| "Write an article about AI" | Execute workflow | Content creation task |
| "Research climate change" | Execute workflow | Research task |
| "Create a report on sales" | Execute workflow | Complex task |

---

## Guiding Execution Decisions

Use instructions to control when the workflow runs:

```python
# Explicit guidance
workflow_agent = WorkflowAgent(
    workflow=research_workflow,
    name="Research Assistant",
    instructions=[
        "You help users with research tasks.",
        "",
        "USE THE WORKFLOW when users ask to:",
        "- Research a topic",
        "- Write a report",
        "- Analyze information",
        "- Create content",
        "",
        "ANSWER DIRECTLY when users:",
        "- Say hello or goodbye",
        "- Ask what you can do",
        "- Ask clarifying questions",
        "- Thank you or acknowledge",
        "",
        "Be helpful and conversational.",
    ],
)
```

---

## Conversational Context

WorkflowAgent maintains conversation history:

```python
from agno.db.sqlite import SqliteDb

workflow_agent = WorkflowAgent(
    workflow=content_workflow,
    name="Content Assistant",
    db=SqliteDb(db_file="tmp/workflow_agent.db"),
    instructions=[
        "Remember our conversation history.",
        "Reference previous discussions when relevant.",
    ],
)

# First interaction
workflow_agent.print_response(
    "Hi, I'm interested in AI articles",
    session_id="user-123",
)

# Follow-up (remembers context)
workflow_agent.print_response(
    "Can you write one about machine learning?",
    session_id="user-123",
)
```

---

## Streaming Responses

WorkflowAgent supports streaming:

```python
# Synchronous streaming
workflow_agent.print_response(
    "Write about renewable energy",
    stream=True,
)

# Async streaming
import asyncio

async def stream_response():
    await workflow_agent.aprint_response(
        "Research quantum computing",
        stream=True,
    )

asyncio.run(stream_response())
```

---

## With Session State

Share state between conversational context and workflow:

```python
from agno.db.sqlite import SqliteDb

workflow_agent = WorkflowAgent(
    workflow=personalized_workflow,
    name="Personal Assistant",
    db=SqliteDb(db_file="tmp/assistant.db"),
    instructions=[
        "You are a personalized assistant.",
        "Remember user preferences from our conversations.",
        "Use these preferences when running the workflow.",
    ],
)

# First conversation sets preferences
workflow_agent.print_response(
    "I prefer detailed technical content",
    session_id="user-456",
)

# Workflow execution uses those preferences
workflow_agent.print_response(
    "Write an article about neural networks",
    session_id="user-456",
)
```

---

## CLI Application Mode

Run WorkflowAgent as an interactive CLI:

```python
workflow_agent = WorkflowAgent(
    workflow=research_workflow,
    name="Research CLI",
    instructions=["Interactive research assistant."],
)

# Start CLI mode
workflow_agent.cli_app(
    session_id="cli-session",
    user="User",
    emoji="🔬",
    stream=True,
)
```

This starts an interactive terminal session:
```
🔬 User: Hello!
🤖 Research CLI: Hi! I'm your research assistant. I can help you research topics and create reports. What would you like to explore?

🔬 User: Research the latest in quantum computing
🤖 Research CLI: [Executes workflow and streams results]
```

---

## Multi-Step Conversation Before Workflow

Gather information before executing:

```python
workflow_agent = WorkflowAgent(
    workflow=custom_report_workflow,
    name="Report Generator",
    instructions=[
        "You create custom reports.",
        "",
        "BEFORE running the workflow, ask about:",
        "1. The topic they want researched",
        "2. The target audience",
        "3. Preferred length and format",
        "",
        "Once you have these details, run the workflow.",
        "Pass the gathered information to the workflow.",
    ],
)

# Conversation flow:
# User: "I need a report"
# Agent: "What topic should I cover?"
# User: "AI in healthcare"
# Agent: "Who is the target audience?"
# User: "Hospital executives"
# Agent: "Preferred length?"
# User: "Executive summary, 2 pages"
# Agent: [Now executes workflow with all context]
```

---

## Handling Workflow Results

Process and present workflow results conversationally:

```python
workflow_agent = WorkflowAgent(
    workflow=analysis_workflow,
    name="Data Analyst",
    instructions=[
        "You analyze data and provide insights.",
        "",
        "After the workflow completes:",
        "- Summarize key findings",
        "- Highlight important insights",
        "- Offer to explain any part in detail",
        "- Ask if they need additional analysis",
        "",
        "Make the results accessible and actionable.",
    ],
)
```

---

## Error Handling

Handle workflow errors gracefully:

```python
workflow_agent = WorkflowAgent(
    workflow=research_workflow,
    name="Research Assistant",
    instructions=[
        "Help users with research.",
        "",
        "If the workflow encounters an error:",
        "- Apologize for the issue",
        "- Explain what happened briefly",
        "- Suggest alternatives or retry",
        "- Offer to help in another way",
        "",
        "Never expose technical error details to users.",
    ],
)
```

---

## Combining with Regular Agent Features

WorkflowAgent inherits Agent capabilities:

```python
from agno.tools.duckduckgo import DuckDuckGoTools

workflow_agent = WorkflowAgent(
    workflow=content_workflow,
    name="Smart Assistant",
    # Agent can use tools directly (not through workflow)
    tools=[DuckDuckGoTools()],
    instructions=[
        "You're a smart content assistant.",
        "",
        "For quick lookups, use your search tools directly.",
        "For full content creation, use the workflow.",
        "",
        "Choose the appropriate approach for each request.",
    ],
)

# Quick search (uses tool directly)
workflow_agent.print_response("What's the weather in Tokyo?")

# Full content (uses workflow)
workflow_agent.print_response("Write a comprehensive guide about Tokyo")
```

---

## Async Execution

Full async support:

```python
import asyncio
from agno.workflow import WorkflowAgent

async def main():
    # Non-streaming async
    response = await workflow_agent.arun(
        "Research machine learning trends",
        session_id="async-session",
    )
    print(response.content)

    # Streaming async
    await workflow_agent.aprint_response(
        "Write about the findings",
        stream=True,
        session_id="async-session",
    )

asyncio.run(main())
```

---

## Production Pattern

Complete production-ready setup:

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step, WorkflowAgent
from agno.model.google import Gemini
from agno.db.postgres import PostgresDb
from agno.tools.duckduckgo import DuckDuckGoTools

# Database for persistence
db = PostgresDb(
    connection_string="postgresql+psycopg://user:pass@localhost/db"
)

# Define workflow agents
researcher = Agent(
    name="Researcher",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Research thoroughly with citations.",
)

writer = Agent(
    name="Writer",
    model=Gemini(id="gemini-2.5-flash"),
    instructions="Write clear, engaging content.",
)

# Define workflow
content_workflow = Workflow(
    name="Content Pipeline",
    steps=[
        Step(name="Research", agent=researcher),
        Step(name="Write", agent=writer),
    ],
    db=db,
)

# Create production WorkflowAgent
content_assistant = WorkflowAgent(
    workflow=content_workflow,
    name="Content Assistant",
    model=Gemini(id="gemini-2.5-flash"),
    db=db,
    instructions=[
        "You are a professional content assistant.",
        "",
        "CAPABILITIES:",
        "- Research any topic thoroughly",
        "- Write articles, reports, summaries",
        "- Answer questions about content creation",
        "",
        "WORKFLOW TRIGGERS:",
        "- 'Write about...'",
        "- 'Create an article on...'",
        "- 'Research and report on...'",
        "",
        "DIRECT RESPONSES:",
        "- Greetings and farewells",
        "- Questions about your capabilities",
        "- Clarifying questions",
        "",
        "Be professional, helpful, and thorough.",
    ],
    markdown=True,
)

if __name__ == "__main__":
    # Interactive CLI for testing
    content_assistant.cli_app(
        session_id="test-session",
        stream=True,
    )
```

---

## WorkflowAgent vs Regular Agent

| Feature | Regular Agent | WorkflowAgent |
|---------|---------------|---------------|
| **Single task** | Yes | Yes |
| **Multi-step pipeline** | Manual | Automatic |
| **Conversation** | Yes | Yes |
| **Workflow execution** | No | Yes |
| **Decision making** | Tools only | Answer vs Execute |
| **State management** | Session | Session + Workflow |

---

## Best Practices

### Do's

1. **Clear instructions** - Define when to execute vs answer
2. **Conversational tone** - Make interactions natural
3. **Use persistence** - Enable session continuity
4. **Handle errors gracefully** - User-friendly error messages

### Don'ts

1. **Don't over-trigger** - Not every message needs workflow
2. **Don't ignore context** - Use conversation history
3. **Don't expose internals** - Hide technical details
4. **Don't forget streaming** - Better UX with real-time output

---

## Summary

| Concept | Description |
|---------|-------------|
| **WorkflowAgent** | Agent wrapper for workflows |
| **Dual Mode** | Answer directly OR execute workflow |
| **Instructions** | Guide execution decisions |
| **Session** | Maintains conversation context |
| **Streaming** | Real-time response output |

---

## Related Documentation

- **Workflows Overview:** `docs(new)/workflows/01-overview.md`
- **Running Workflows:** `docs(new)/workflows/03-running-workflows.md`
- **Session Management:** `docs(new)/workflows/01-overview.md#workflow-sessions`

---

*Last Updated: December 2025 | AGNO 2.3.4*
