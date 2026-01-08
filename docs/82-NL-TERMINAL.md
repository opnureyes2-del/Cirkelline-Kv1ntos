# NL TERMINAL v2.3.0

## Natural Language Interface for ODIN Ecosystem

**Part of:** ODIN v2.0.0 - The All-Father
**Component:** Phase 4 of ODIN Implementation
**Location:** `~/.claude-agent/nl_terminal.py`
**Lines:** ~1,380
**Database:** `~/.claude-agent/nl_terminal.db`

---

## OVERVIEW

The NL Terminal provides intuitive natural language interaction with the KV1NTOS/ODIN ecosystem. It translates natural language commands into actionable code, system commands, and research queries.

### Key Capabilities

1. **PARSE** - Understand natural language intent
2. **TRANSLATE** - Convert NL to actionable commands
3. **GENERATE** - Create code from descriptions
4. **EXECUTE** - Run commands with context
5. **LEARN** - Improve from usage patterns

### Architecture Position

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INPUT                              │
│               "create a function to validate emails"        │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    NL TERMINAL v2.3.0                       │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Intent        │  │ Code          │  │ Response      │   │
│  │ Recognizer    │→ │ Generator     │→ │ Builder       │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   KV1NTOS DAEMON v2.3.0                     │
│         (30 Components including NL Terminal)               │
└─────────────────────────────────────────────────────────────┘
```

---

## INSTALLATION

The NL Terminal is automatically initialized with KV1NTOS v2.3.0.

### Manual Verification

```bash
# Check version
python3 ~/.claude-agent/nl_terminal.py --version

# Check status
python3 ~/.claude-agent/nl_terminal.py --status

# Start interactive mode
python3 ~/.claude-agent/nl_terminal.py --interactive
```

### Via KV1NTOS Daemon

```python
from kv1nt_daemon import get_kv1nt

kv1nt = get_kv1nt()

# Process natural language
response = kv1nt.nl_process("create a function to validate emails")
print(response['content'])

# Check status
print(kv1nt.nl_status())

# View history
history = kv1nt.nl_history(10)
```

---

## ENUMS

### IntentCategory

Categories of recognized user intent:

| Value | Description | Example |
|-------|-------------|---------|
| `CODE_GENERATION` | Generate new code | "create a function to..." |
| `CODE_MODIFICATION` | Modify existing code | "change the function..." |
| `CODE_EXPLANATION` | Explain code | "what does this code do?" |
| `BUG_FIX` | Fix bugs | "fix the error in..." |
| `REFACTOR` | Refactor code | "refactor this function" |
| `TEST_GENERATION` | Generate tests | "write tests for..." |
| `DOCUMENTATION` | Generate documentation | "document this module" |
| `RESEARCH` | Research topics | "research best practices for..." |
| `SYSTEM_COMMAND` | System operations | "show status" |
| `FILE_OPERATION` | File operations | "read file /path/to/file" |
| `GIT_OPERATION` | Git operations | "commit changes" |
| `DEPLOYMENT` | Deployment operations | "deploy to production" |
| `QUESTION` | General questions | "what is a decorator?" |
| `CUSTOM_COMMAND` | Custom user commands | "/deploy-prod" |
| `UNKNOWN` | Unrecognized intent | - |

### ExecutionMode

How the command should be executed:

| Value | Description |
|-------|-------------|
| `IMMEDIATE` | Execute immediately without confirmation |
| `PREVIEW` | Show what would happen (dry-run) |
| `INTERACTIVE` | Ask for confirmation before execution |
| `BATCH` | Queue for batch execution |

### ResponseType

Type of response returned:

| Value | Description |
|-------|-------------|
| `CODE` | Code output |
| `TEXT` | Text response |
| `TABLE` | Tabular data |
| `TREE` | Tree structure |
| `DIFF` | Diff output |
| `ERROR` | Error message |
| `SUGGESTION` | Follow-up suggestions |
| `CONFIRMATION` | Confirmation request |

### ConfidenceLevel

Confidence in intent recognition:

| Value | Threshold |
|-------|-----------|
| `HIGH` | > 0.8 |
| `MEDIUM` | 0.5 - 0.8 |
| `LOW` | < 0.5 |

---

## DATACLASSES

### Intent

Recognized user intent:

```python
@dataclass
class Intent:
    intent_id: str               # Unique identifier
    category: IntentCategory     # Intent category
    description: str             # Original description
    entities: Dict[str, Any]     # Extracted entities
    confidence: float            # 0.0 - 1.0
    original_input: str          # Original user input
    language: Optional[str]      # Target language (python, typescript, etc.)
    target_file: Optional[str]   # Target file if applicable
    context_required: bool       # Needs context to execute
    requires_confirmation: bool  # Needs user confirmation
    suggested_mode: ExecutionMode # Recommended execution mode
```

### NLContext

Context for NL processing:

```python
@dataclass
class NLContext:
    current_file: Optional[str]           # Currently active file
    current_directory: str                # Current working directory
    recent_files: List[str]               # Last 10 files accessed
    recent_commands: List[str]            # Last 50 commands
    current_task: Optional[str]           # Current task description
    session_id: Optional[str]             # Session identifier
    user_preferences: Dict[str, Any]      # User settings
    variables: Dict[str, Any]             # Custom variables
```

### NLResponse

Response from NL Terminal:

```python
@dataclass
class NLResponse:
    response_id: str                 # Unique identifier
    response_type: ResponseType      # Type of response
    content: Any                     # Main content
    explanation: Optional[str]       # Explanation of result
    suggestions: List[str]           # Follow-up suggestions
    execution_time_ms: float         # Processing time
    metadata: Dict[str, Any]         # Additional metadata
```

### CustomCommand

User-defined custom command:

```python
@dataclass
class CustomCommand:
    command_id: str                  # Unique identifier
    name: str                        # Command name
    trigger: str                     # Regex pattern trigger
    description: str                 # What the command does
    actions: List[Dict[str, Any]]    # Actions to perform
    created_at: datetime             # Creation timestamp
    usage_count: int                 # Times used
    enabled: bool                    # Is enabled
```

---

## DATABASE SCHEMA

### Tables

**1. command_history**
```sql
CREATE TABLE command_history (
    command_id TEXT PRIMARY KEY,
    input TEXT NOT NULL,
    intent_category TEXT,
    intent_confidence REAL,
    response_type TEXT,
    success INTEGER DEFAULT 1,
    execution_time_ms REAL,
    timestamp TEXT,
    context TEXT DEFAULT '{}'
)
```

**2. custom_commands**
```sql
CREATE TABLE custom_commands (
    command_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    trigger TEXT NOT NULL,
    description TEXT,
    actions TEXT DEFAULT '[]',
    created_at TEXT,
    usage_count INTEGER DEFAULT 0,
    enabled INTEGER DEFAULT 1
)
```

**3. code_templates**
```sql
CREATE TABLE code_templates (
    template_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    pattern TEXT NOT NULL,
    language TEXT DEFAULT 'python',
    template TEXT NOT NULL,
    parameters TEXT DEFAULT '[]',
    example TEXT,
    usage_count INTEGER DEFAULT 0
)
```

**4. intent_patterns**
```sql
CREATE TABLE intent_patterns (
    pattern_id TEXT PRIMARY KEY,
    pattern TEXT NOT NULL,
    intent_category TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TEXT,
    last_used TEXT
)
```

**5. sessions**
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    context TEXT DEFAULT '{}',
    started_at TEXT,
    last_activity TEXT,
    command_count INTEGER DEFAULT 0
)
```

### Indexes

```sql
CREATE INDEX idx_history_timestamp ON command_history(timestamp)
CREATE INDEX idx_history_category ON command_history(intent_category)
CREATE INDEX idx_patterns_category ON intent_patterns(intent_category)
```

---

## INTENT PATTERNS

The NL Terminal uses regex patterns for intent recognition. Patterns support both English and Danish:

### CODE_GENERATION
```regex
(?:create|generate|write|make|build)\s+(?:a\s+)?(?:function|method|class|endpoint|component|module)
(?:add|implement)\s+(?:a\s+)?(?:new\s+)?(?:function|feature|endpoint)
(?:code|script)\s+(?:for|that|to)\s+
(?:kan du|lav|opret|skriv)\s+(?:en\s+)?(?:funktion|klasse|endpoint)
```

### BUG_FIX
```regex
(?:fix|debug|repair|solve)\s+(?:the\s+)?(?:bug|error|issue|problem)
(?:why\s+is|why\s+does)\s+.+(?:not\s+working|failing|broken)
(?:ret|fiks|løs)\s+(?:fejlen|problemet|buggen)
```

### RESEARCH
```regex
(?:research|search|find\s+(?:information|info)\s+(?:about|on))\s+
(?:what\s+are|how\s+to|best\s+practices\s+for)\s+
(?:undersøg|find|søg\s+efter)\s+
```

---

## CODE TEMPLATES

### Default Templates

**1. fastapi_endpoint**
```python
@router.{method}("/{path}")
async def {function_name}(request: Request) -> Dict[str, Any]:
    """
    {description}
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"success": True}
```

**2. python_function**
```python
def {function_name}({parameters}) -> {return_type}:
    """
    {description}

    Args:
        {args_doc}

    Returns:
        {return_doc}
    """
    pass
```

**3. python_class**
```python
@dataclass
class {class_name}:
    """
    {description}
    """
    {attributes}

    def __post_init__(self) -> None:
        pass
```

**4. pytest_test**
```python
import pytest

class Test{class_name}:
    """Tests for {target}."""

    def test_{test_name}_success(self):
        # Arrange
        {arrange}
        # Act
        result = {action}
        # Assert
        assert result {assertion}
```

---

## TERMINAL COMMANDS

### Standalone CLI

```bash
# Show version
python3 ~/.claude-agent/nl_terminal.py --version

# Show status
python3 ~/.claude-agent/nl_terminal.py --status

# View command history
python3 ~/.claude-agent/nl_terminal.py --history

# Process single command
python3 ~/.claude-agent/nl_terminal.py --process "create a function to validate emails"

# Interactive mode
python3 ~/.claude-agent/nl_terminal.py --interactive
```

### Via KV1NTOS Daemon

```python
from kv1nt_daemon import get_kv1nt
kv1nt = get_kv1nt()

# Process NL input
kv1nt.nl_process("create endpoint for user profiles")

# Get status
kv1nt.nl_status()

# Get history
kv1nt.nl_history(10)

# Create custom command
kv1nt.nl_create_command("deploy-prod", "Deploy to production", [...])

# List custom commands
kv1nt.nl_list_commands()
```

---

## USAGE EXAMPLES

### Code Generation

```python
# Simple function
response = kv1nt.nl_process("create a function to validate email addresses")
print(response['content'])

# Output:
def validate_email_addresses() -> Any:
    """
    validate email addresses

    Args:
        # TODO: Document arguments

    Returns:
        # TODO: Document return value
    """
    pass
```

### FastAPI Endpoint

```python
response = kv1nt.nl_process("create a post endpoint for user registration")
# Generates FastAPI endpoint template
```

### Research (via Platform Connector)

```python
response = kv1nt.nl_process("research best practices for API design")
# Delegates to Platform Connector for deep research
```

### File Operations

```python
response = kv1nt.nl_process("read file /home/rasmus/.claude-agent/odin.py")
# Returns file contents with context update
```

### Custom Commands

```python
# Create custom command
kv1nt.nl_create_command(
    name="status-all",
    description="Show status of all systems",
    actions=[
        {"type": "command", "value": "odin --status"},
        {"type": "command", "value": "guardian --status"},
        {"type": "command", "value": "admiral --status"}
    ]
)

# Use custom command
response = kv1nt.nl_process("/status-all")
```

---

## INTEGRATION POINTS

### With KV1NTOS Daemon

```python
# kv1nt_daemon.py integration
from nl_terminal import get_nl_terminal, NLTerminal, IntentCategory, ExecutionMode

class Kv1ntOSDaemon:
    def __init__(self):
        # ... other components ...
        self._nl_terminal = get_nl_terminal()
        self._mcp.register("nl_terminal", self._nl_terminal)
```

### With Platform Connector

```python
# Research intent delegates to Platform Connector
async def _handle_research(self, intent: Intent, context: NLContext):
    from platform_connector import get_platform_connector, ResearchMode
    platform = get_platform_connector()
    result = await platform.research(topic, mode=ResearchMode.QUICK)
```

### With Code Guardian

```python
# Generated code can be scanned
response = kv1nt.nl_process("create a function...")
if response['code_generated']:
    scan_result = kv1nt.guardian_scan(response['content'])
```

### With Admiral

```python
# High-risk operations require approval
if intent.category in [IntentCategory.DEPLOYMENT, IntentCategory.GIT_OPERATION]:
    approval = kv1nt.admiral_request_approval(
        action_type="code_execution",
        description=intent.description,
        risk_level="high"
    )
```

---

## CONFIDENCE SCORING

Intent recognition confidence is calculated as:

```python
def _calculate_confidence(match, input_text, pattern) -> float:
    # Base confidence from match ratio
    match_ratio = len(match.group()) / len(input_text)
    base_confidence = 0.5 + (match_ratio * 0.3)

    # Position bonus
    if match.start() == 0:
        base_confidence += 0.1

    # Keyword boost
    specific_keywords = ["create", "generate", "fix", "explain", "test", "deploy"]
    if any(kw in input_text.lower() for kw in specific_keywords):
        base_confidence += 0.1

    return min(base_confidence, 1.0)
```

---

## EXECUTION MODE DETERMINATION

```python
def _suggest_mode(category: IntentCategory, confidence: float) -> ExecutionMode:
    # High-risk operations need confirmation
    if category in [IntentCategory.DEPLOYMENT, IntentCategory.GIT_OPERATION]:
        return ExecutionMode.INTERACTIVE

    # Low confidence needs preview
    if confidence < 0.6:
        return ExecutionMode.PREVIEW

    return ExecutionMode.IMMEDIATE
```

---

## BEST PRACTICES

### 1. Be Specific

```python
# Good
"create a function to validate email addresses with regex"

# Less clear
"make email thing"
```

### 2. Use Context

```python
# Set context for better results
kv1nt.nl_terminal.set_current_file("/path/to/file.py")
kv1nt.nl_terminal.set_current_task("implementing user auth")
```

### 3. Create Custom Commands for Repeated Tasks

```python
kv1nt.nl_create_command(
    "quick-deploy",
    "Quick deploy to staging",
    [{"type": "bash", "value": "git push staging main"}]
)
```

### 4. Review Generated Code

Always review generated code before execution, especially for production systems.

---

## TROUBLESHOOTING

### Low Confidence Recognition

**Problem:** Intent recognized with low confidence
**Solution:**
- Use more specific keywords
- Check if the pattern exists for your intent type
- Add custom patterns for common use cases

### Research Not Working

**Problem:** Research commands fail
**Solution:**
- Ensure Platform Connector is connected
- Check API credentials
- Try `kv1nt.platform_status()` first

### Custom Command Not Found

**Problem:** Custom command returns "Unknown command"
**Solution:**
- Check if command is enabled
- Verify command name spelling
- Use `kv1nt.nl_list_commands()` to see available commands

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| v2.3.0 | 2025-12-18 | Integrated with KV1NTOS daemon |
| v2.2.0 | 2025-12-18 | Initial release with ODIN v2.0.0 |

---

## ROADMAP

### v2.4.0 (Planned)
- LLM-powered code generation (beyond templates)
- Multi-turn conversation support
- Voice input integration

### v2.5.0 (Planned)
- Learning from corrections
- Personalized patterns per user
- Cross-device sync

### v3.0.0 (Opus-Level)
- Full natural language code generation
- Context-aware file operations
- Autonomous task planning

---

## RELATED DOCUMENTATION

- [ODIN v2.0.0](78-ODIN-v2.0.0.md) - Ecosystem Commander
- [Code Guardian](79-CODE-GUARDIAN.md) - Code Quality Observer
- [Admiral](80-ADMIRAL.md) - Strategic Governance
- [Opus Code Architecture](81-OPUS-CODE-ARCHITECTURE.md) - v3.0.0 Vision
- [KV1NTOS Manual](KV1NTOS-MANUAL.md) - Complete System Guide

---

*Created: 2025-12-18*
*Author: Rasmus & Claude Opus 4.5*
*Component: 30 of 30 in KV1NTOS v2.3.0*
