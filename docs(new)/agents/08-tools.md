# AGNO Tools Documentation

> **Source:** https://docs.agno.com/basics/tools/overview
> **Last Updated:** 2025-11-29

---

## What Are Tools?

Tools are functions your AGNO Agents can use to get things done. They enable agents to interact with external systems and perform practical actions beyond text generation.

**Tools allow agents to:**
- Search the web
- Execute SQL queries
- Send emails
- Call APIs
- Access 120+ pre-built toolkits

---

## How Tools Work

The execution follows an LLM loop pattern:

```
1. Agent sends run context and tool definitions to the model
2. Model responds with a message OR a tool call
3. If tool called → executes and returns result to model
4. Model processes updated context
5. Repeat until final response (no more tool calls)
```

---

## Adding Tools to Agents

### Basic Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[DuckDuckGoTools()],
    markdown=True,
)

agent.print_response("What are the latest news in AI?")
```

### Multiple Toolkits

```python
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
from agno.tools.reasoning import ReasoningTools

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[
        DuckDuckGoTools(),
        YFinanceTools(),
        ReasoningTools(add_instructions=True),
    ],
)
```

---

## Function Tools (Custom Functions)

AGNO automatically converts Python functions into tool definitions.

### Basic Function Tool

```python
def get_weather(city: str) -> str:
    """Get the weather for a given city.

    Args:
        city (str): The city to get the weather for.

    Returns:
        str: Weather description for the city.
    """
    return f"The weather in {city} is sunny."

agent = Agent(
    tools=[get_weather],
)
```

### Best Practices for Function Tools

1. **Always include docstrings** with `Args` section
2. **Use descriptive function names** (LLM uses name to decide when to call)
3. **Include type hints** for all parameters
4. **Document each argument clearly** (LLM reads these descriptions)

**Why docstrings matter:**
```python
# BAD - LLM doesn't know what this does
def fetch(x):
    return data[x]

# GOOD - LLM understands purpose and parameters
def fetch_user_profile(user_id: str) -> dict:
    """Fetch a user's profile information from the database.

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        dict: User profile containing name, email, and preferences.
    """
    return database.get_user(user_id)
```

---

## Toolkits (Pre-built Collections)

A Toolkit is a collection of functions that work together and share internal state.

### Popular Toolkits

| Toolkit | Purpose |
|---------|---------|
| `DuckDuckGoTools` | Web search |
| `YFinanceTools` | Stock/financial data |
| `ExaTools` | Advanced web search |
| `TavilyTools` | Web research |
| `ReasoningTools` | Structured thinking (think, analyze) |
| `SlackTools` | Slack integration |
| `GoogleCalendarTools` | Calendar management |
| `GmailTools` | Email operations |
| `NotionTools` | Notion integration |
| `GitHubTools` | GitHub operations |
| `KnowledgeTools` | Knowledge base search |
| `UserControlFlowTools` | Request user input |

### Toolkit Parameters

```python
from agno.tools.slack import SlackTools

slack_tools = SlackTools(
    # Custom instructions for this toolkit
    instructions=["Use send_message to send messages..."],

    # Add instructions to agent's system message
    add_instructions=True,

    # Only include specific tools
    include_tools=["send_message", "list_channels"],

    # Exclude specific tools
    exclude_tools=["delete_message"],

    # Tools requiring user confirmation
    requires_confirmation_tools=["delete_channel"],

    # Tools executed outside agent loop
    external_execution_required_tools=[],

    # Stop agent after these tools
    stop_after_tool_call_tools=["final_answer"],

    # Show results to user
    show_result_tools=["get_status"],

    # Enable result caching
    cache_results=True,
    cache_ttl=3600,  # 1 hour
)
```

---

## Creating Custom Toolkits

```python
from typing import List
from agno.tools import Toolkit
from agno.utils.log import logger

class ShellTools(Toolkit):
    def __init__(self, working_directory: str = "/", **kwargs):
        # Store internal state
        self.working_directory = working_directory

        # List of tool functions
        tools = [
            self.run_shell_command,
            self.list_files,
        ]

        # Initialize parent with name and tools
        super().__init__(
            name="shell_tools",
            tools=tools,
            instructions="Use these tools to interact with the filesystem.",
            **kwargs
        )

    def list_files(self, directory: str) -> str:
        """List the files in the given directory.

        Args:
            directory (str): The directory to list files from.

        Returns:
            str: List of files in the directory.
        """
        import os
        path = os.path.join(self.working_directory, directory)
        try:
            files = os.listdir(path)
            return "\n".join(files)
        except Exception as e:
            logger.warning(f"Failed to list files: {e}")
            return f"Error: {e}"

    def run_shell_command(self, args: List[str], tail: int = 100) -> str:
        """Run a shell command and return the output.

        Args:
            args (List[str]): Command as list of strings.
            tail (int): Number of output lines to return.

        Returns:
            str: Command output or error message.
        """
        import subprocess
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                cwd=self.working_directory
            )
            if result.returncode != 0:
                return f"Error: {result.stderr}"
            return "\n".join(result.stdout.split("\n")[-tail:])
        except Exception as e:
            return f"Error: {e}"

# Usage
agent = Agent(tools=[ShellTools(working_directory="/home/user")])
```

---

## Toolkit Instructions

Toolkits can have their own instructions that get injected into the agent's system message.

```python
class CalculatorTools(Toolkit):
    def __init__(self, **kwargs):
        tools = [self.add, self.subtract, self.multiply, self.divide]

        # Custom instructions for this toolkit
        instructions = """
        Use these tools to perform calculations.
        Always validate inputs before execution.
        Return results with appropriate precision.
        """

        super().__init__(
            name="calculator_tools",
            tools=tools,
            instructions=instructions,
            add_instructions=True,  # Inject into system message
            **kwargs
        )
```

**Where instructions appear:**
```
System Message Structure:
├── Agent description
├── Agent instructions
├── Expected output
├── Team members (if Team)
├── <additional_information> tags
└── Toolkit instructions (injected here)
```

---

## Built-in Tool Parameters

Tools automatically receive special parameters without declaring them:

### run_context

Access session state, dependencies, and knowledge filters:

```python
def my_tool(query: str, run_context) -> str:
    """Search with user context.

    Args:
        query (str): Search query.
    """
    user_id = run_context.session_state.get("user_id")
    # Use user_id to filter results
    return search_for_user(query, user_id)
```

### Media Parameters

```python
def process_media(
    prompt: str,
    images: List[Image] = None,      # Input images
    videos: List[Video] = None,      # Input videos
    audio: List[Audio] = None,       # Input audio
    files: List[File] = None,        # Input files
) -> str:
    """Process uploaded media.

    Args:
        prompt (str): User's request.
    """
    if images:
        # Process images
        pass
    return "Processed"
```

---

## Tool Results

### Simple Returns

```python
# These work directly
def simple_tool() -> str:
    return "Hello"

def dict_tool() -> dict:
    return {"status": "ok", "count": 42}

def list_tool() -> list:
    return ["item1", "item2"]
```

### Media Returns (ToolResult)

```python
from agno.tools.function import ToolResult
from agno.media import Image

def generate_image(prompt: str) -> ToolResult:
    """Generate an image from prompt.

    Args:
        prompt (str): Image description.
    """
    image = Image(
        id="img_123",
        url="https://example.com/image.png",
        original_prompt=prompt
    )
    return ToolResult(
        content=f"Generated image for: {prompt}",
        images=[image]
    )
```

---

## Concurrent Tool Execution

Tools execute concurrently when using async methods:

```python
# Concurrent execution
await agent.arun("Search for X and Y")  # Tools run in parallel
agent.aprint_response("...")            # Tools run in parallel

# Sequential execution
agent.run("...")                        # Tools run one at a time
agent.print_response("...")             # Tools run one at a time
```

**Requirements:**
- Model must support parallel function calling
- OpenAI has `parallel_tool_calls=True` by default
- Sync functions run on separate threads
- Async functions run concurrently

---

## Tool Hooks

Perform validation, logging, or custom logic before/after tool calls:

```python
def logger_hook(
    function_name: str,
    function_call: Callable,
    arguments: Dict[str, Any]
):
    """Log all tool calls."""
    print(f"Calling {function_name} with {arguments}")
    result = function_call(**arguments)
    print(f"Result: {result}")
    return result

def confirmation_hook(
    function_name: str,
    function_call: Callable,
    arguments: Dict[str, Any]
):
    """Require confirmation for certain tools."""
    if function_name == "delete_file":
        confirm = input(f"Delete {arguments['path']}? (y/n): ")
        if confirm.lower() != 'y':
            raise ValueError("User cancelled deletion")
    return function_call(**arguments)

agent = Agent(
    tools=[FileTools()],
    tool_hooks=[logger_hook, confirmation_hook],
)
```

### Available Hook Parameters

| Parameter | Description |
|-----------|-------------|
| `function_name` | Name of the tool being called |
| `function_call` | The actual function to execute |
| `arguments` | Dict of arguments passed to tool |
| `agent` | The Agent object (optional) |
| `team` | The Team object (optional) |
| `run_context` | RunContext with session state (optional) |

---

## Managing Tool Calls in History

Control how many tool calls appear in context:

```python
agent = Agent(
    tools=[DuckDuckGoTools()],
    # Only keep last 5 tool calls in context
    max_tool_calls_from_history=5,
)
```

**Behavior:**
- Run 1-3: Model sees tool calls [1], [1,2], [1,2,3]
- Run 4: Model sees tool calls [2,3,4] (call 1 filtered out)
- Run 5: Model sees tool calls [3,4,5] (calls 1-2 filtered out)

**Note:** Database always contains complete history. This only affects what the model sees.

---

## Tool Call Limit

> **Source:** https://docs.agno.com/basics/tools/tool-call-limit

Limit the number of tool calls an Agent can make per run. Useful for preventing loops, controlling costs, and managing performance.

### Basic Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.yfinance import YFinanceTools

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[YFinanceTools(company_news=True)],
    tool_call_limit=1,  # Max 1 tool call per run
)

# First tool call executes, second fails gracefully
agent.print_response(
    "Find TSLA price, then find Tesla news.",
    stream=True,
)
```

### Key Behaviors

| Behavior | Description |
|----------|-------------|
| **Scope** | Limit enforced across FULL RUN (not per individual request) |
| **Batch calls** | If agent tries multiple calls at once, only allowed number executes |
| **Failure mode** | Excess tool calls fail gracefully (no errors thrown) |
| **Applies to** | Both `Agent` and `Team` |

### Use Cases

1. **Prevent runaway memory operations:**
```python
agent = Agent(
    db=db,
    enable_agentic_memory=True,
    tool_call_limit=5,  # Prevents excessive memory operations
)
```

2. **Cost control:** Limit API calls to external services
3. **Sandbox testing:** Restrict agent autonomy during development
4. **Quota enforcement:** Ensure predictable resource consumption

### When to Use

- Agents with expensive external API tools
- Agentic memory enabled (memory operations = nested LLM calls)
- Testing/development environments
- Multi-tool agents that might loop

---

## ReasoningTools (Special Toolkit)

Gives any model explicit thinking tools:

```python
from agno.tools.reasoning import ReasoningTools

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[
        ReasoningTools(
            enable_think=True,       # Enable think() tool
            enable_analyze=True,     # Enable analyze() tool
            add_instructions=True,   # Add usage instructions
            add_few_shot=False,      # Add example usage
        ),
    ],
)
```

**Tools provided:**
- `think()` - Step-by-step reasoning about a problem
- `analyze()` - Detailed analysis with structured reasoning

---

## UserControlFlowTools (Special Toolkit)

Request input from users during execution:

```python
from agno.tools.user_control_flow import UserControlFlowTools

agent = Agent(
    instructions=["Ask users for input when needed"],
    tools=[
        UserControlFlowTools(
            enable_get_user_input=True,
            add_instructions=True,
        ),
    ],
)
```

**Tools provided:**
- `get_user_input()` - Pause execution and request user input

---

## Common Patterns

### Search + Reasoning

```python
agent = Agent(
    tools=[
        DuckDuckGoTools(),
        ReasoningTools(add_instructions=True),
    ],
    instructions=["Think before searching", "Analyze results carefully"],
)
```

### Multi-Source Research

```python
agent = Agent(
    tools=[
        ExaTools(),
        TavilyTools(),
        YFinanceTools(),
    ],
    instructions=["Use multiple sources", "Cross-reference findings"],
)
```

### Interactive Assistant

```python
agent = Agent(
    tools=[
        UserControlFlowTools(),
        GoogleCalendarTools(),
        GmailTools(),
    ],
    instructions=["Ask for clarification when needed"],
)
```

---

## Summary

| Concept | Description |
|---------|-------------|
| **Tools** | Functions agents can call to perform actions |
| **Toolkits** | Collections of related tools with shared state |
| **Function Tools** | Custom Python functions as tools |
| **Tool Instructions** | Per-toolkit guidance injected into system message |
| **Tool Hooks** | Pre/post execution logic for validation/logging |
| **ToolResult** | Return type for media content |
| **run_context** | Access to session state and dependencies |
| **tool_call_limit** | Max tool calls per run (prevents loops, controls costs) |

**Key Best Practices:**
1. Write clear docstrings with Args sections
2. Use descriptive function names
3. Add type hints to all parameters
4. Use `add_instructions=True` for toolkit guidance
5. Use async methods for concurrent tool execution
