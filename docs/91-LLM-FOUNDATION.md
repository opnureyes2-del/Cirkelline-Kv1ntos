# KV1NTOS v2.10.0 - LLM Foundation

**Version:** 2.10.0
**Date:** 2025-12-19
**Location:** `~/.claude-agent/`
**Components:** 46 total (~47,000 lines)

---

## OVERVIEW

v2.10.0 introduces the **LLM Foundation** - the critical infrastructure for OPUS-NIVEAU code generation capabilities.

### Core Principle

> **LLM CORE IS THE GATEKEEPER** - Without LLM integration, intelligent code generation is not possible. This is the foundation for all v3.0.0 capabilities.

### New Components

| Component | Lines | Purpose |
|-----------|-------|---------|
| `llm_core.py` | ~1,200 | Claude API + Ollama fallback |
| `context_manager.py` | ~800 | 128K token window management |

---

## LLM CORE

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        LLM CORE v2.10.0                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Claude    │    │   Ollama    │    │  Response   │         │
│  │  Provider   │    │  Provider   │    │   Cache     │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                            ▼                                    │
│              ┌─────────────────────────┐                       │
│              │       LLM Core          │                       │
│              │  - generate()           │                       │
│              │  - generate_code()      │                       │
│              │  - explain_code()       │                       │
│              │  - review_code()        │                       │
│              │  - fix_bug()            │                       │
│              │  - reason()             │                       │
│              └─────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Providers

```python
class LLMProvider(Enum):
    CLAUDE_OPUS = "claude-opus-4-5-20251101"
    CLAUDE_SONNET = "claude-sonnet-4-20250514"
    CLAUDE_HAIKU = "claude-haiku-4-5-20251101"
    OLLAMA_LLAMA = "llama3:70b"
    OLLAMA_CODESTRAL = "codestral:22b"
    OLLAMA_QWEN = "qwen2.5-coder:32b"
```

### Task Types

```python
class TaskType(Enum):
    CODE_GENERATION = "code_generation"
    CODE_EXPLANATION = "code_explanation"
    CODE_REVIEW = "code_review"
    BUG_DETECTION = "bug_detection"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    TEST_GENERATION = "test_generation"
    DOCUMENTATION = "documentation"
    REASONING = "reasoning"
    CONVERSATION = "conversation"
```

### Usage

```python
from llm_core import get_llm_core, LLMContext

# Get singleton instance
llm = get_llm_core()

# Generate code
result = await llm.generate_code(
    intent="Create a function to validate email addresses",
    language="python"
)
print(result.code)
print(result.explanation)

# Explain existing code
explanation = await llm.explain_code(
    code="def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)",
    detail_level="detailed"
)

# Review code
review = await llm.review_code(
    code=my_code,
    focus_areas=["security", "performance"]
)
print(f"Score: {review['score']}")
print(f"Issues: {review['issues']}")

# Fix a bug
fixed = await llm.fix_bug(
    code=buggy_code,
    bug_description="Off-by-one error in loop"
)

# General reasoning
answer = await llm.reason(
    "How should I structure a microservices architecture?"
)
```

### Fallback Strategy

```
Primary: Claude API (Sonnet by default)
         ↓ if unavailable or fails
Fallback: Ollama (llama3:70b)
         ↓ if unavailable
Error: Return failed response
```

### Response Caching

```python
class CacheStrategy(Enum):
    NONE = "none"       # No caching
    MEMORY = "memory"   # In-memory only
    DISK = "disk"       # Disk only
    HYBRID = "hybrid"   # Both memory and disk
```

- Memory cache: 1000 entries, LRU eviction
- Disk cache: `~/.claude-agent/llm_cache/`
- TTL: 1 hour
- Cache key: SHA256 of messages + temperature

---

## CONTEXT MANAGER

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   CONTEXT MANAGER v2.10.0                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Context   │    │   Context   │    │   Context   │         │
│  │ Compressor  │    │ Prioritizer │    │   Cache     │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                            ▼                                    │
│              ┌─────────────────────────┐                       │
│              │    Context Manager       │                       │
│              │  - create_window()       │                       │
│              │  - add_file_context()    │                       │
│              │  - add_system_prompt()   │                       │
│              │  - estimate_tokens()     │                       │
│              └─────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Context Priority

```python
class ContextPriority(Enum):
    CRITICAL = 5    # Must include (system prompt, user message)
    HIGH = 4        # Very important (current file)
    MEDIUM = 3      # Important (related files)
    LOW = 2         # Nice to have (examples)
    MINIMAL = 1     # Only if space (comments)
```

### Compression Levels

```python
class CompressionLevel(Enum):
    NONE = 0        # No compression
    LIGHT = 1       # Remove comments, whitespace
    MEDIUM = 2      # + Remove docstrings
    HEAVY = 3       # + Extract signatures only
    EXTREME = 4     # Minimal: just names
```

### Usage

```python
from context_manager import get_context_manager, ContextPriority

cm = get_context_manager()

# Add context elements
elements = [
    cm.add_system_prompt("You are a Python expert."),
    cm.add_user_message("Fix this bug"),
    cm.add_file_context(
        "/path/to/main.py",
        file_content,
        priority=ContextPriority.HIGH
    ),
    cm.add_file_context(
        "/path/to/utils.py",
        utils_content,
        priority=ContextPriority.MEDIUM
    ),
]

# Create optimized window
window = cm.create_window(
    elements,
    target_file="/path/to/main.py",
    intent="fix bug",
    max_tokens=8000
)

print(f"Total tokens: {window.total_tokens}")
print(f"Compression: {window.compression_applied}")
print(f"Truncated: {window.truncated_elements}")
```

### Token Estimation

- Rough estimate: 4 characters = 1 token
- Model limits tracked per model
- Budget allocation by category:
  - System prompt: 10%
  - Current file: 30%
  - Related files: 25%
  - Codebase context: 15%
  - Conversation: 15%
  - Reserved: 5%

---

## DAEMON INTEGRATION

### New Properties

```python
kv1nt.llm_core          # LLMCore instance
kv1nt.context_manager   # ContextManager instance
```

### New Methods

```python
# Code generation
await kv1nt.generate_code(intent, language, current_file)
await kv1nt.explain_code(code, language, detail_level)
await kv1nt.review_code(code, language, focus_areas)
await kv1nt.fix_bug(code, bug_description, language)
await kv1nt.reason(question)

# Status
kv1nt.llm_status()            # Dict with version, providers, stats
kv1nt.llm_status_formatted()  # Formatted string
kv1nt.context_status()        # Dict with version, max_tokens, cache
```

---

## COMPONENT STATISTICS

### v2.10.0 Summary

| Metric | Value |
|--------|-------|
| Total Components | 46 |
| Total Lines | ~47,000 |
| New Components | 2 |
| New Methods | 10 |
| New Enums | 8 |
| New Dataclasses | 7 |

### Progression

```
v2.9.0  →  v2.10.0
  44         46
 components  components
```

---

## NEXT STEPS (v2.11.0)

With LLM Foundation in place, the next iteration adds:

1. **Knowledge Graph** (`knowledge_graph.py`)
   - 768-dim vector embeddings
   - Semantic code search
   - Cross-file relationships

This enables semantic understanding for intelligent code generation.

---

## CHANGELOG

### v2.10.0 (2025-12-19)

**Added:**
- `llm_core.py` (~1,200 lines)
  - ClaudeProvider class
  - OllamaProvider class
  - ResponseCache class
  - LLMCore orchestrator
- `context_manager.py` (~800 lines)
  - ContextCompressor class
  - ContextPrioritizer class
  - ContextManager class
- 10 new daemon methods
- 8 new enums
- 7 new dataclasses

**Updated:**
- kv1nt_daemon.py to v2.10.0
- VERSION file to 2.10.0
- Component count: 44 → 46

---

*Documentation Version: 1.0*
*Created: 2025-12-19*
*Author: Claude Opus 4.5*
