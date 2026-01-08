# Building Agents

**AGNO Version:** 2.2.13
**Source:** https://docs.agno.com/basics/agents/building-agents

---

## What is an Agent?

Agents are AI programs where a language model controls the flow of execution.

**Core components:**
- **Model:** LLM controlling execution (decides when to reason, use tools, respond)
- **Instructions:** Prompts guiding the model's behavior
- **Tools:** Enable actions and external system interactions

**Optional components:**
- **Memory:** Store/recall previous interactions
- **Storage:** Save session history in database (makes agents stateful)
- **Knowledge:** Information to search at runtime (Agentic RAG)
- **Reasoning:** "Think" before responding for better reliability

---

## Your First Agent

### Minimal Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=["You are a helpful AI assistant."],
    markdown=True,
)

agent.print_response("Hello!")
```

That's it! Three required elements: **Model + Instructions + Markdown**

---

### Agent with Tools

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[HackerNewsTools()],
    instructions="Write a report on the topic. Output only the report.",
    markdown=True,
)

agent.print_response("Trending startups and products.", stream=True)
```

---

## Essential Parameters

**Minimal (required):**
```python
Agent(model=OpenAIChat(id="gpt-5-mini"))
```

**Recommended:**
```python
Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    name="My Agent",
    role="Brief description",
    instructions=["List of instructions"],
    tools=[...],
    markdown=True,
)
```

**Common parameters:**
- `model` - LLM to use (required)
- `name` - Agent identifier
- `role` - Brief description (used in teams)
- `instructions` - How agent should behave
- `tools` - Actions agent can take
- `markdown` - Format output nicely
- `db` - Database for persistence

---

## Models

AGNO supports multiple providers:

```python
# OpenAI
from agno.models.openai import OpenAIChat
model = OpenAIChat(id="gpt-5-mini")

# Anthropic
from agno.models.anthropic import Claude
model = Claude(id="claude-sonnet-4-5")

# Google
from agno.models.google import Gemini
model = Gemini(id="gemini-2.5-flash")
```

---

## Instructions

Instructions guide how your agent behaves - **most important part**.

**String:**
```python
instructions="Write a report on the topic. Output only the report."
```

**List:**
```python
instructions=[
    "You are a research assistant.",
    "Search for information on the given topic.",
    "Summarize findings in bullet points.",
    "Include sources for all claims."
]
```

**Callable (dynamic):**
```python
def get_instructions(run_context):
    if run_context.metadata.get("mode") == "detailed":
        return ["Provide detailed analysis with examples."]
    else:
        return ["Provide brief summary."]

agent = Agent(
    model=model,
    instructions=get_instructions  # Function!
)
```

### Best Practices

**✅ DO:**
- Be specific and clear
- Provide examples
- Include output format
- List capabilities

**❌ DON'T:**
- Be vague ("be helpful")
- Contradict yourself
- Make instructions too long

---

## Tools

Tools enable actions beyond text generation.

### Built-in Tools

```python
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.calculator import CalculatorTools

agent = Agent(
    model=model,
    tools=[
        DuckDuckGoTools(),
        CalculatorTools(),
    ]
)
```

### Multiple Tools

```python
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.newspaper4k import Newspaper4kTools

agent = Agent(
    model=model,
    tools=[DuckDuckGoTools(), Newspaper4kTools()],
    instructions=[
        "Search for top 5 links on the topic.",
        "Read each URL and extract article text.",
        "Analyze and prepare a summary."
    ],
)
```

### Custom Tools

```python
from agno.tools import Toolkit

class MyCustomTool(Toolkit):
    def __init__(self):
        super().__init__(name="my_custom_tool")

    def my_function(self, param: str) -> str:
        """Docstring becomes tool description"""
        return result

agent = Agent(
    model=model,
    tools=[MyCustomTool()]
)
```

### Tool Choice

```python
agent = Agent(
    tools=[DuckDuckGoTools()],
    tool_choice="auto"  # Options: "auto", "required", "none"
)
```

### Tool Call Limit

```python
agent = Agent(
    tools=[YFinanceTools()],
    tool_call_limit=1  # Max tool calls per run
)
```

---

## Memory

Memory gives agents ability to remember users across conversations.

### Basic Memory

```python
agent = Agent(
    model=model,
    enable_user_memories=True,
    db=db  # Database required
)
```

### Custom Memory Manager

```python
from agno.memory import MemoryManager

custom_memory = MemoryManager(
    memory_capture_instructions="""
    Capture about the user:
    - Name and role
    - Preferences and goals
    - Recurring topics
    - Technical expertise level
    """
)

agent = Agent(
    model=model,
    enable_user_memories=True,
    memory_manager=custom_memory,
    db=db
)
```

**Memory parameters:**
- `enable_user_memories` - Auto-create/update memories
- `enable_agentic_memory` - Give agent tools to manage memories
- `memory_manager` - Custom memory logic
- `add_memories_to_context` - Include memories in responses

---

## Storage (Database)

Storage makes agents stateful for multi-turn conversations.

### Setup Database

```python
from agno.db.postgres import PostgresDb

db = PostgresDb(
    table_name="agent_sessions",
    db_url="postgresql+psycopg://user:pass@host:port/db"
)

agent = Agent(
    model=model,
    db=db
)
```

### Session Features

```python
agent = Agent(
    model=model,
    db=db,
    enable_session_summaries=True,  # Auto-summarize long conversations
    add_history_to_context=True,    # Include past messages
    num_history_runs=10,            # Last 10 turns
)
```

**What database enables:**
- Multi-turn conversations
- Session history
- Resuming conversations
- Context across runs

---

## Knowledge

Knowledge is information the agent can search at runtime (Agentic RAG).

### Setup

```python
from agno.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.knowledge.embedder.openai import OpenAIEmbedder

knowledge = Knowledge(
    vector_db=PgVector(
        table_name="agent_knowledge",
        db_url="postgresql+psycopg://..."
    ),
    embedder=OpenAIEmbedder()
)

agent = Agent(
    model=model,
    knowledge=knowledge,
    search_knowledge=True
)
```

**How it works:**
1. Documents uploaded and chunked
2. Chunks converted to embeddings
3. Stored in vector database
4. Agent searches at runtime
5. Retrieved info added to context

**Knowledge parameters:**
- `knowledge` - Knowledge base instance
- `search_knowledge` - Auto-search when needed
- `add_knowledge_to_context` - Add references to prompt
- `knowledge_filters` - Filter by metadata

---

## Best Practices

### 1. Start Simple, Add Complexity

**AGNO Philosophy:** "Start simple -- just a model, tools, and basic instructions. Once that works, layer in more functionality."

```python
# Step 1: Minimal
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=["You are a helpful assistant."]
)

# Step 2: Add tools
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    instructions=["Search for information to answer questions."]
)

# Step 3: Add database
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    db=db,
)

# Step 4: Add memory
agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    db=db,
    enable_user_memories=True,
)
```

### 2. Well-Defined Tasks

**Good starting points:**
- Classification
- Summarization
- Data extraction
- Knowledge search
- Document processing

These early wins help validate what works.

### 3. Clear Instructions

**✅ Good:**
```python
instructions=[
    "You are a research assistant.",
    "For each query:",
    "1. Search for relevant information",
    "2. Summarize key findings",
    "3. Cite sources",
]
```

**❌ Vague:**
```python
instructions=["Be helpful and friendly"]
```

### 4. Use Markdown

```python
agent = Agent(
    markdown=True  # Enables headers, bullets, formatting
)
```

### 5. Database for Production

**Development:**
```python
agent = Agent(model=model)  # Sessions lost after restart
```

**Production:**
```python
agent = Agent(
    model=model,
    db=db,  # Persistence enabled
    enable_session_summaries=True,
    enable_user_memories=True,
)
```

### 6. Test Thoroughly

Test with:
- ✅ Good inputs
- ✅ Bad inputs
- ✅ Empty inputs
- ✅ Long inputs
- ✅ Unexpected formats

### 7. Name Your Agents

Important for teams:
```python
agent = Agent(
    id="research-agent",
    name="Research Agent",
    role="Search and analyze information",
    model=model
)
```

---

## Complete Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.db.postgres import PostgresDb

# Database setup
db = PostgresDb(
    table_name="agent_sessions",
    db_url="postgresql+psycopg://..."
)

# Production-ready agent
agent = Agent(
    name="Research Assistant",
    role="Search and summarize information",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    instructions=[
        "You are a research assistant.",
        "Search for information on topics.",
        "Provide concise summaries with sources."
    ],
    markdown=True,
    db=db,
    enable_user_memories=True,
    enable_session_summaries=True,
    add_history_to_context=True,
    num_history_runs=10,
)

# Run agent
agent.print_response("Latest AI news")
```

---

## Summary

**Building Blocks:**
- **Minimal:** Model + Instructions + Markdown
- **Production:** + Tools + Database + Memory + Knowledge

**Key Principles:**
1. Start simple, add gradually
2. Be specific with instructions
3. Use tools wisely
4. Enable persistence (database)
5. Test thoroughly

**Next Steps:**
- 02-running-agents.md - How to execute agents
- 03-debugging-agents.md - Troubleshooting
- 07-instructions.md - Writing better instructions
- 08-tools.md - Custom tools

---

**AGNO Documentation:** https://docs.agno.com/basics/agents/building-agents
**Version:** 1.0
