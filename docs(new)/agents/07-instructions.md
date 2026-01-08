# Agent Instructions

**Source:** https://docs.agno.com/basics/agents/usage/instructions

Instructions are detailed guidelines provided to an agent to shape its behavior and personality. They function as a system prompt that influences how the agent responds to user queries.

---

## Table of Contents

1. [What Instructions Are](#what-instructions-are)
2. [Instruction Formats](#instruction-formats)
3. [Dynamic Instructions](#dynamic-instructions)
4. [Session State in Instructions](#session-state-in-instructions)
5. [Best Practices](#best-practices)
6. [Common Patterns](#common-patterns)

---

## What Instructions Are

Instructions define **who the agent is** and **how it should behave**. They are injected into the system prompt sent to the language model.

**Instructions shape:**
- Agent personality and tone
- Response format and structure
- Behavioral guidelines
- Domain expertise
- Output style preferences
- Ethical guardrails

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful assistant that speaks concisely.",
)

agent.print_response("What is Python?")
```

---

## Instruction Formats

AGNO supports three instruction formats:

### 1. String Format (Simple)

**Best for:** Single, concise instructions

```python
from agno.agent import Agent

agent = Agent(
    instructions="Share a 2 sentence story about"
)

agent.print_response("Love in the year 12000.")
```

### 2. List Format (Multiple Instructions)

**Best for:** Organized, multi-part instructions

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions=[
        "You are a helpful coding assistant.",
        "Always explain your code step by step.",
        "Use Python best practices.",
        "Include error handling in examples.",
    ],
)
```

**Benefits:**
- Easier to read and maintain
- Can add/remove instructions dynamically
- Clear separation of concerns

### 3. Multi-line String Format (Detailed)

**Best for:** Complex, narrative instructions

```python
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions=dedent("""\
        You are an enthusiastic news reporter with a flair for storytelling.

        Your style guidelines:
        - Use vivid, engaging language
        - Start with a catchy headline
        - Include relevant emoji for emphasis
        - End with a memorable sign-off

        Behavioral expectations:
        - Verify all facts before reporting
        - Maintain high energy throughout
        - Make complex topics accessible
    """),
    markdown=True,
)
```

---

## Dynamic Instructions

Dynamic instructions change based on runtime context. AGNO supports two patterns:

### Pattern 1: Function with Agent Parameter

**Use case:** Access agent properties (name, model, tools)

```python
from typing import List
from agno.agent import Agent

def get_instructions(agent: Agent) -> List[str]:
    """Generate instructions based on agent properties."""
    return [
        f"Your name is {agent.name}!",
        "Talk in haiku's!",
        "Use poetry to answer questions.",
    ]

agent = Agent(
    name="AgentX",
    instructions=get_instructions,  # Pass the function, not the result
    markdown=True,
)

agent.print_response("Who are you?", stream=True)
```

**Key points:**
- Function receives the `Agent` instance
- Returns `str` or `List[str]`
- Called at runtime, not at initialization
- Can access `agent.name`, `agent.model`, `agent.tools`, etc.

### Pattern 2: Function with RunContext Parameter

**Use case:** Access session state for personalization

```python
from agno.agent import Agent
from agno.run import RunContext

def get_instructions(run_context: RunContext) -> str:
    """Generate instructions based on session state."""
    if not run_context.session_state:
        run_context.session_state = {}

    # Access user-specific data from session state
    user_id = run_context.session_state.get("current_user_id")

    if user_id:
        return f"Make the story about {user_id}."

    return "Make the story about the user."

agent = Agent(instructions=get_instructions)
agent.print_response("Write a 2 sentence story", user_id="john.doe")
```

**Key points:**
- Function receives `RunContext` with session state
- Access `run_context.session_state` for user data
- AGNO automatically adds `current_user_id` and `current_session_id`
- Perfect for multi-user applications

### Pattern 3: Callable with Deep Research Mode (Advanced)

**Use case:** Completely different instructions based on mode

```python
from agno.agent import Agent
from agno.run import RunContext

def get_dynamic_instructions(run_context: RunContext) -> List[str]:
    """Return different instructions based on deep_research flag."""

    session_state = run_context.session_state or {}
    deep_research = session_state.get("deep_research", False)
    user_name = session_state.get("user_name", "User")

    base_instructions = [
        f"You are helping {user_name}.",
        "Be friendly and conversational.",
    ]

    if deep_research:
        # Deep research mode - delegate to research team
        return base_instructions + [
            "For research queries, ALWAYS delegate to the Research Team.",
            "DO NOT use web search tools directly.",
            "Let specialists handle comprehensive research.",
        ]
    else:
        # Quick mode - use tools directly
        return base_instructions + [
            "For quick lookups, use web search tools directly.",
            "Keep responses concise and fast.",
        ]

agent = Agent(
    instructions=get_dynamic_instructions,
    # ... other config
)
```

---

## Session State in Instructions

AGNO supports template syntax to inject session state variables directly into instructions.

### Basic Template Syntax

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    # Initialize session state
    session_state={"user_name": "John"},
    # Reference variables with {variable_name}
    instructions="User's name is {user_name}. Be friendly!",
    markdown=True,
)

agent.print_response("What is my name?", stream=True)
# Agent knows the user's name is John
```

### Multiple Variables

```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    session_state={
        "user_name": "Alice",
        "user_role": "Developer",
        "preferred_language": "Python",
    },
    instructions=[
        "User's name is {user_name}.",
        "User's role is {user_role}.",
        "Preferred programming language: {preferred_language}.",
        "Tailor your responses accordingly.",
    ],
)
```

### Auto-Injected Variables

AGNO automatically adds these to session state:
- `current_user_id` - The user_id passed to run()
- `current_session_id` - The session_id passed to run()

```python
agent = Agent(
    instructions=[
        "Current User ID: {current_user_id}",
        "Current Session ID: {current_session_id}",
    ],
)

agent.print_response(
    "Who am I?",
    user_id="john_doe",
    session_id="session_123"
)
```

### Teams with Session State

```python
from agno.team import Team

team = Team(
    members=[agent1, agent2],
    session_state={"user_name": "John"},
    instructions="User's name is {user_name}",
    markdown=True,
)

team.print_response("What is my name?", stream=True)
```

---

## Best Practices

### 1. Define Clear Role and Personality

```python
# GOOD - Clear role definition
instructions = [
    "You are an expert Python developer with 10 years of experience.",
    "You specialize in FastAPI and async programming.",
    "You value clean, readable code over clever solutions.",
]

# BAD - Vague role
instructions = "You are helpful."
```

### 2. Specify Output Format

```python
# GOOD - Clear format expectations
instructions = [
    "Always structure your responses with:",
    "1. A brief summary (1-2 sentences)",
    "2. Detailed explanation with code examples",
    "3. Potential gotchas or edge cases",
]

# BAD - No format guidance
instructions = "Explain things well."
```

### 3. Include Behavioral Guidelines

```python
# GOOD - Explicit behavior
instructions = [
    "If you don't know something, say so clearly.",
    "Always verify facts before presenting them.",
    "Ask clarifying questions when the request is ambiguous.",
    "Never make up information.",
]
```

### 4. Add Domain Context

```python
# GOOD - Domain-specific context
instructions = [
    "You are helping users of a project management app.",
    "Users can create projects, tasks, and milestones.",
    "The app uses a Kanban-style board.",
    "Common terms: sprint, backlog, story points.",
]
```

### 5. Set Ethical Guardrails

```python
# GOOD - Clear boundaries
instructions = [
    "Never share personal data or credentials.",
    "Decline requests for harmful or illegal content.",
    "Respect user privacy at all times.",
    "If unsure about safety, err on the side of caution.",
]
```

### 6. Use Callable Instructions for Dynamic Behavior

```python
# GOOD - Dynamic based on context
def get_instructions(run_context: RunContext) -> List[str]:
    user_tier = run_context.session_state.get("tier", "free")

    base = ["You are a helpful assistant."]

    if user_tier == "premium":
        base.append("Provide detailed, comprehensive responses.")
    else:
        base.append("Keep responses concise (under 200 words).")

    return base

# BAD - Static instructions that can't adapt
instructions = "You are a helpful assistant."
```

---

## Common Patterns

### Pattern 1: News Reporter Agent

```python
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions=dedent("""\
        You are an enthusiastic news reporter with a flair for storytelling.

        Style Guidelines:
        - Use vivid, engaging language
        - Start with a catchy headline
        - Include relevant emoji for emphasis
        - Reference local landmarks and culture
        - End with a memorable sign-off

        Behavioral Guidelines:
        - Verify all facts before reporting
        - Maintain high energy throughout
        - Make complex topics accessible
        - Include quotes when relevant
    """),
    markdown=True,
)
```

### Pattern 2: Technical Assistant

```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions=[
        "You are a senior software engineer specializing in Python.",
        "Always provide working code examples.",
        "Explain the 'why' behind your recommendations.",
        "Follow PEP 8 style guidelines.",
        "Include type hints in all function signatures.",
        "Handle errors gracefully with try/except blocks.",
        "Suggest tests for critical functionality.",
    ],
    markdown=True,
)
```

### Pattern 3: Customer Support Agent

```python
from agno.run import RunContext

def get_support_instructions(run_context: RunContext) -> List[str]:
    session_state = run_context.session_state or {}
    user_name = session_state.get("user_name", "Customer")
    user_tier = session_state.get("tier", "free")

    instructions = [
        f"You are helping {user_name} with customer support.",
        "Be empathetic, patient, and solution-focused.",
        "Always acknowledge the customer's concern first.",
        "Provide step-by-step solutions when possible.",
    ]

    if user_tier == "premium":
        instructions.append("This is a premium customer - prioritize their issue.")
        instructions.append("Offer to escalate to a human agent if needed.")

    return instructions

agent = Agent(
    instructions=get_support_instructions,
    # ... other config
)
```

### Pattern 4: Multi-Mode Agent (Quick vs Deep)

```python
from agno.run import RunContext

def get_mode_instructions(run_context: RunContext) -> List[str]:
    """Return different instructions based on research mode."""
    session_state = run_context.session_state or {}
    deep_research = session_state.get("deep_research", False)

    if deep_research:
        return [
            "You are in DEEP RESEARCH mode.",
            "Provide comprehensive, well-researched answers.",
            "Cite sources when possible.",
            "Take your time to be thorough.",
            "Delegate to specialist teams for complex queries.",
        ]
    else:
        return [
            "You are in QUICK mode.",
            "Provide concise, direct answers.",
            "Keep responses under 200 words.",
            "Use bullet points for clarity.",
            "Prioritize speed over depth.",
        ]

agent = Agent(
    instructions=get_mode_instructions,
)
```

### Pattern 5: Location-Aware Agent

```python
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGoTools()],
    session_state={"location": "New York City"},
    instructions=[
        "You are a local guide for {location}.",
        "When searching, focus on {location} results.",
        "Reference local landmarks and neighborhoods.",
        "Provide practical, local insider tips.",
    ],
    markdown=True,
)
```

---

## Summary

**Key Takeaways:**

1. **Three Formats:** String, List, or Callable
2. **Dynamic Instructions:** Use callable with `Agent` or `RunContext` parameter
3. **Session State Templates:** Use `{variable_name}` syntax
4. **Auto Variables:** `current_user_id` and `current_session_id` are auto-injected
5. **Best Practices:**
   - Define clear role and personality
   - Specify output format
   - Include behavioral guidelines
   - Add domain context
   - Set ethical guardrails
   - Use callable for dynamic behavior

**Next Steps:**
- Explore [Session State](../../state/) for persistent user data
- Learn about [Memory](../../memory/) for long-term agent memory
- Check [Teams](../../teams/) for multi-agent coordination
