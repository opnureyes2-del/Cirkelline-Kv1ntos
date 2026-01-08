# Session State Workaround - Complete Documentation

**Version:** v1.2.29.2+
**Status:** ✅ PRODUCTION READY
**Created:** 2025-11-27
**Last Updated:** 2025-11-27
**AGNO Version:** v2.2.13

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [What is the Session State Workaround?](#what-is-the-session-state-workaround)
3. [The AGNO Bug](#the-agno-bug)
4. [Architecture & Implementation](#architecture--implementation)
5. [Technical Deep Dive](#technical-deep-dive)
6. [Testing & Verification](#testing--verification)
7. [Why This Matters](#why-this-matters)
8. [Related Documentation](#related-documentation)

---

## Executive Summary

### What Was Built

Comprehensive inline documentation (60+ lines of comments) explaining the session_state workaround that makes Deep Research mode work correctly in Cirkelline.

**What It Documents:**
- How session_state is constructed (lines 289-313)
- Why we manually set `cirkelline.session_state` (lines 473-511)
- How session_state flows through `arun()` (lines 541-559, 877-882)

### The Core Issue

**AGNO v2.2.13 Bug:**
- AGNO Teams do NOT automatically set `self.session_state` during `run()`/`arun()`
- They only pass `session_state` to RunContext (internal execution context)
- Callable instructions access `agent.session_state` (direct attribute access)
- Result: Callable instructions can't see session_state without our workaround

### The Workaround

```python
# Before calling arun(), manually set the team's session_state attribute
cirkelline.session_state = session_state

# Then pass it to arun() as normal
await cirkelline.arun(
    ...,
    session_state=session_state  # This makes it available in RunContext
)
```

### Why It's Critical

**Without this workaround:**
- Deep Research mode breaks completely
- Callable instructions can't access `deep_research` flag
- Wrong instruction set is returned (mentions search tools in Deep Research mode)
- Tool errors occur: "Function 'exa_search' not found" (because tools were removed)

### Current Status

- ✅ **Workaround Implemented**: v1.2.29.2 (working since then)
- ✅ **Documentation Added**: Comprehensive inline comments (v1.2.32+)
- ✅ **Tested**: Deep Research mode working correctly
- ✅ **Production Ready**: Zero regressions, fully documented

---

## What is the Session State Workaround?

### Session State in AGNO

**What is session_state?**

From AGNO docs:
> "Session state is a dictionary that flows through the entire agent execution. It's accessible in tools (via run_context.session_state), instructions (via agent.session_state), and is persisted to the database between runs within the same session."

**How session_state is SUPPOSED to work:**

```python
# Create an agent with session_state
agent = Agent(
    session_state={"user_name": "John"}
)

# Run the agent
agent.run(session_state={"user_name": "John"})

# Access in callable instructions
def get_instructions(agent=None):
    user_name = agent.session_state.get('user_name')
    return [f"User's name is {user_name}"]
```

**The Problem in AGNO v2.2.13:**

For **Teams** (not individual Agents), AGNO doesn't set `self.session_state`:

```python
# What AGNO does internally (simplified)
class Team:
    def run(self, session_state=None):
        # ❌ AGNO DOESN'T DO THIS:
        # self.session_state = session_state

        # ✅ AGNO ONLY DOES THIS:
        run_context = RunContext(session_state=session_state)

        # Call callable instructions
        instructions = self.instructions(agent=self)  # ← agent.session_state is None!
```

### How Cirkelline Uses Session State

**What we store in session_state:**

```python
session_state = {
    "current_user_id": user_id,              # For knowledge filtering
    "current_user_type": "Regular/Admin",    # For tone/capabilities
    "current_user_name": "Ivo",              # For personalization
    "current_tier_slug": "family",           # For feature gating
    "current_tier_level": 5,                 # Tier numeric level
    "deep_research": True/False,             # 🔑 CRITICAL: Research mode flag
    "user_custom_instructions": "..."        # User preferences
}
```

**How we use it:**

1. **Callable Instructions** (`cirkelline/orchestrator/instructions.py`)
   ```python
   def get_cirkelline_instructions(agent=None):
       # Access session_state via agent.session_state
       deep_research = agent.session_state.get('deep_research', False)

       if deep_research:
           # Return Deep Research instructions (no tool names)
           return [...]
       else:
           # Return Quick Search instructions (with tool names)
           return [...]
   ```

2. **Knowledge Tools** (via RunContext)
   ```python
   def search_knowledge(query: str, run_context=None):
       user_id = run_context.session_state.get('current_user_id')
       # Filter results by user_id
       return search(query, user_id=user_id)
   ```

---

## The AGNO Bug

### Detailed Bug Analysis

**File:** `agno/team/team.py` (AGNO framework)

**What AGNO Does:**
```python
# AGNO v2.2.13 Team.run() implementation (simplified)
class Team:
    def run(self, session_state=None, **kwargs):
        # Create RunContext with session_state
        run_context = RunContext(
            session_state=session_state,
            # ... other context
        )

        # ❌ MISSING: self.session_state = session_state
        # AGNO Teams do NOT set this!

        # Call instructions (if callable)
        if callable(self.instructions):
            # Callable instructions receive Team instance
            # They try to access agent.session_state
            # But agent.session_state is None!
            instructions = self.instructions(agent=self)

        # Rest of execution...
```

**Why It's a Bug:**
1. Individual `Agent` class DOES set `self.session_state`
2. `Team` class does NOT (inconsistency in AGNO)
3. Callable instructions expect `agent.session_state` to work
4. AGNO docs show examples using `agent.session_state`

### Impact on Cirkelline

**Execution Flow Without Workaround:**

```
1. User enables Deep Research mode
2. Frontend sends deep_research=true to backend
3. Backend builds session_state dict: {"deep_research": true, ...}
4. Backend calls cirkelline.arun(session_state=session_state)
5. AGNO creates RunContext with session_state
6. AGNO calls get_cirkelline_instructions(agent=cirkelline)
7. get_cirkelline_instructions tries: agent.session_state.get('deep_research')
8. ❌ agent.session_state is None → deep_research defaults to False
9. ❌ Wrong instructions returned (Quick Search instead of Deep Research)
10. ❌ Instructions mention "exa_search" tool
11. ❌ But backend removed ExaTools when deep_research=true
12. ❌ Agent tries to call exa_search → "Function not found" error
13. ❌ Delegation freeze - nothing happens
```

**Execution Flow With Workaround:**

```
1. User enables Deep Research mode
2. Frontend sends deep_research=true to backend
3. Backend builds session_state dict: {"deep_research": true, ...}
4. ✅ Backend manually sets: cirkelline.session_state = session_state
5. Backend calls cirkelline.arun(session_state=session_state)
6. AGNO creates RunContext with session_state
7. AGNO calls get_cirkelline_instructions(agent=cirkelline)
8. get_cirkelline_instructions tries: agent.session_state.get('deep_research')
9. ✅ agent.session_state is not None → deep_research = True
10. ✅ Correct instructions returned (Deep Research mode)
11. ✅ Instructions never mention search tools
12. ✅ Tools were removed by backend (line 427-433)
13. ✅ Agent delegates to Research Team
14. ✅ Delegation works perfectly
```

---

## Architecture & Implementation

### Code Locations

**File:** `cirkelline/endpoints/custom_cirkelline.py`

**Documentation Blocks:**

1. **Lines 289-313**: Session State Construction
   - Explains what session_state IS
   - What data it contains
   - Why each field matters
   - How it flows through execution

2. **Lines 473-511**: The Workaround Itself
   - Explains the AGNO bug in detail
   - Why manual assignment is needed
   - Complete execution flow (5 steps)
   - Links to related docs

3. **Lines 541-559**: Streaming Endpoint Parameter
   - How session_state flows through `arun()`
   - Distinction between parameter vs attribute
   - Why BOTH are necessary

4. **Lines 877-882**: Non-Streaming Endpoint Parameter
   - Cross-reference to streaming endpoint
   - Same pattern for consistency

### Implementation Code

#### 1. Session State Construction (Lines 316-324)

```python
# ✅ v1.2.29: Include user profile context for agent instructions
session_state = {
    **existing_session_state,
    "current_user_id": user_id,
    "current_user_type": user_type,
    "current_user_name": user_name,
    "current_tier_slug": tier_slug,
    "current_tier_level": tier_level,
    "deep_research": deep_research  # ✅ Pass deep_research flag to agent
}
```

#### 2. The Workaround (Line 510)

```python
# ═══════════════════════════════════════════════════════════════
# 🐛 AGNO BUG WORKAROUND: Manual session_state Assignment
# ═══════════════════════════════════════════════════════════════
# Problem: AGNO v2.2.13 Teams do NOT automatically set self.session_state during run()
#          They only pass session_state to RunContext (internal execution context)
#
# Impact: Callable instructions (cirkelline/orchestrator/instructions.py) access
#         session_state via agent.session_state (direct attribute access), NOT via RunContext
#         Example: agent.session_state.get('deep_research', False) at line 45
#
# Why this matters:
# - Cirkelline uses callable instructions: instructions=get_cirkelline_instructions
# - These instructions are DYNAMIC - they return different instruction sets based on deep_research flag
# - Deep Research Mode: Returns instructions WITHOUT search tool names (delegates to Research Team)
# - Quick Search Mode: Returns instructions WITH search tool names (uses tools directly)
# - See cirkelline/orchestrator/instructions.py:44-49 for session_state access pattern
#
# The Workaround:
# Manually assign session_state to the Team instance BEFORE calling arun()
# This makes it accessible to callable instructions via agent.session_state
#
# Execution Flow:
# 1. We build session_state dict above (lines 316-324)
# 2. We manually set cirkelline.session_state = session_state HERE
# 3. We pass session_state to arun() below (line 559)
# 4. During run, callable instructions access agent.session_state
# 5. Instructions read deep_research flag and return appropriate instruction set
#
# Related Documentation:
# - AGNO docs: https://docs.agno.com/basics/state/team/overview
# - Deep Research fix: docs/26-CALLABLE-INSTRUCTIONS-DEEP-RESEARCH-FIX.md
# - Session state in instructions: https://docs.agno.com/basics/state/agent/usage/session-state-in-instructions
#
# IMPORTANT: This workaround is CRITICAL for Deep Research mode to work properly.
# Without it, callable instructions cannot access session_state, deep_research flag
# defaults to False, and the wrong instruction set is returned (causing tool errors).
# ═══════════════════════════════════════════════════════════════
cirkelline.session_state = session_state
logger.info(f"🔧 Workaround: Set cirkelline.session_state manually for callable instructions")
```

#### 3. Passing to arun() (Lines 541-559)

```python
async for event in cirkelline.arun(
    input=message,
    stream=True,
    stream_events=True,
    stream_member_events=True,
    session_id=actual_session_id,
    user_id=user_id,
    dependencies=dependencies,
    # ═══ SESSION STATE PARAMETER ═══
    # This parameter passes the session_state dict into AGNO's execution context (RunContext).
    # It contains: user context (user_id, user_type, user_name, tier info) + deep_research flag
    #
    # What happens with it during execution:
    # 1. AGNO creates RunContext and stores session_state there
    # 2. Tools access it via run_context.session_state (standard AGNO pattern)
    # 3. Callable instructions access it via agent.session_state (our workaround at line 510)
    # 4. AGNO persists it to database after run completes (for session continuity)
    # 5. Next run in same session loads it from database and merges with new values
    #
    # Key distinction:
    # - Passing it HERE makes it available in RunContext (for tools)
    # - Setting agent.session_state at line 510 makes it available to callable instructions
    # - BOTH are necessary for our architecture to work properly
    #
    # Related: See session_state construction at lines 316-324, workaround at lines 473-511
    # ═══════════════════════════════════════════════════════════
    session_state=session_state
):
```

---

## Technical Deep Dive

### Callable Instructions Pattern

**File:** `cirkelline/orchestrator/instructions.py`

```python
def get_cirkelline_instructions(agent=None):
    """
    Dynamic instructions that adapt based on deep_research flag in session_state.
    """
    # ✅ v1.2.29.1: Extract user context from session_state
    deep_research = False
    user_type = "Regular"
    user_name = None
    tier_slug = "member"
    tier_level = 1

    # 🔑 CRITICAL: Access session_state via agent.session_state
    if agent and hasattr(agent, 'session_state') and agent.session_state:
        deep_research = agent.session_state.get('deep_research', False)
        user_type = agent.session_state.get('current_user_type', 'Regular')
        user_name = agent.session_state.get('current_user_name')
        tier_slug = agent.session_state.get('current_tier_slug', 'member')
        tier_level = agent.session_state.get('current_tier_level', 1)

    # Return different instructions based on mode
    if deep_research:
        # Deep Research instructions (never mention search tools)
        return [...]
    else:
        # Quick Search instructions (mention exa_search, tavily_search)
        return [...]
```

**Why This Pattern:**
1. **Dynamic Instructions**: Different instructions based on runtime state
2. **Mode Switching**: User can toggle between Quick Search / Deep Research
3. **Tool Availability**: Must match instructions with available tools
4. **Agent Access**: Callable instructions receive `agent` parameter (Team instance)
5. **Session State**: Expected to access via `agent.session_state`

### The Two Paths to session_state

**Path 1: Tools (via RunContext)** ✅ Works Without Workaround
```python
class KnowledgeSearchTool:
    def search(self, query: str, run_context: RunContext = None):
        # RunContext is automatically injected by AGNO
        user_id = run_context.session_state.get('current_user_id')
        # This works because AGNO passes session_state to RunContext
        return search_knowledge(query, user_id)
```

**Path 2: Callable Instructions (via agent.session_state)** ❌ Broken Without Workaround
```python
def get_instructions(agent=None):
    # Agent parameter receives Team instance
    deep_research = agent.session_state.get('deep_research', False)
    # ❌ agent.session_state is None in Teams (AGNO bug)
    # ✅ Works with our workaround: cirkelline.session_state = session_state
```

### Why Both Mechanisms?

**RunContext (Parameter)**
- Used by: Tools, validators, hooks
- Access pattern: `run_context.session_state`
- Set by: AGNO automatically when you pass `session_state` to `run()`
- Works for: Both Agents and Teams

**agent.session_state (Attribute)**
- Used by: Callable instructions, custom functions
- Access pattern: `agent.session_state`
- Set by: AGNO for Agents, ❌ NOT for Teams
- Works for: Agents only (Teams need workaround)

---

## Testing & Verification

### Functional Tests

**Test 1: Deep Research Mode Works**
```bash
# Enable Deep Research mode in UI
# Send query: "Research quantum computing history"
# Expected:
# - Cirkelline announces delegation to Research Team
# - Research Team executes (Web Researcher → Research Analyst)
# - Comprehensive response returned (60-90 seconds)
# - NO "Function not found" errors
```

**Test 2: Quick Search Mode Works**
```bash
# Disable Deep Research mode in UI
# Send query: "What is the capital of France?"
# Expected:
# - Cirkelline uses exa_search/tavily_search directly
# - Fast response (3-10 seconds)
# - NO delegation to Research Team
```

**Test 3: Mode Switching Works**
```bash
# Within same session:
# 1. Send query with Deep Research OFF → Quick Search used
# 2. Enable Deep Research toggle
# 3. Send query with Deep Research ON → Research Team delegated
# 4. Disable Deep Research toggle
# 5. Send query with Deep Research OFF → Quick Search used again
# Expected: Correct mode for each request
```

### Log Verification

**Check for workaround confirmation:**
```bash
tail -f /tmp/cirkelline_documented.log | grep "Workaround"
```

**Expected Output:**
```
INFO - 🔧 Workaround: Set cirkelline.session_state manually for callable instructions
INFO - 🔍 Final session state: {'current_user_id': '...', 'deep_research': True, ...}
```

**Check callable instructions access:**
```bash
tail -f /tmp/cirkelline_documented.log | grep "USER PROFILE DEBUG"
```

**Expected Output:**
```
INFO - 🔍 USER PROFILE DEBUG: type=Admin, tier=family (level 5), display='User Type: Admin...'
```

---

## Why This Matters

### Historical Context

**Before v1.2.27:**
- Deep Research mode didn't work
- Callable instructions couldn't access `deep_research` flag
- Wrong instruction set was returned
- Tool errors occurred constantly

**The Journey:**
1. **v1.2.24**: Deep Research mode implemented (but had bugs)
2. **v1.2.25**: UI/UX improvements
3. **v1.2.26**: Four critical bugs fixed, including session_state issues
4. **v1.2.27**: Callable instructions pattern (complete fix)
5. **v1.2.29.2**: Discovered AGNO bug, implemented workaround
6. **v1.2.32+**: Comprehensive documentation added

### User Impact

**Without Workaround:**
- User enables Deep Research mode
- Nothing happens (delegation freeze)
- Tool errors in logs
- Poor user experience

**With Workaround:**
- User enables Deep Research mode
- Research Team delegation works perfectly
- Comprehensive research results
- Excellent user experience

### Developer Impact

**Without Documentation:**
- Future developers see `cirkelline.session_state = session_state`
- Think: "Why are we doing this? AGNO should handle it!"
- Remove the line
- Deep Research mode breaks
- Hours of debugging to rediscover the issue

**With Documentation:**
- Clear explanation of AGNO bug
- Detailed execution flow
- Links to related docs
- Safe from accidental removal
- Easy to maintain

---

## Related Documentation

### AGNO Documentation
- [Agent Session State](https://docs.agno.com/basics/state/agent/overview)
- [Team Session State](https://docs.agno.com/basics/state/team/overview)
- [Session State in Instructions](https://docs.agno.com/basics/state/agent/usage/session-state-in-instructions)

### Cirkelline Documentation
- [26-CALLABLE-INSTRUCTIONS-DEEP-RESEARCH-FIX.md](./26-CALLABLE-INSTRUCTIONS-DEEP-RESEARCH-FIX.md) - Original Deep Research fix
- [31-DEEP-RESEARCH.md](./31-DEEP-RESEARCH.md) - Complete Deep Research documentation
- [32-TIMEOUT-PROTECTION.md](./32-TIMEOUT-PROTECTION.md) - Request timeout handling
- [33-STREAMING-ERROR-HANDLING.md](./33-STREAMING-ERROR-HANDLING.md) - JSON serialization errors

### Code Files
- **cirkelline/endpoints/custom_cirkelline.py**
  - Lines 289-313: Session state construction
  - Lines 473-511: Workaround implementation
  - Lines 541-559: Streaming parameter documentation
  - Lines 877-882: Non-streaming parameter documentation

- **cirkelline/orchestrator/instructions.py**
  - Lines 44-49: Session state access in callable instructions
  - Complete dynamic instruction implementation

---

## Future Improvements

### Potential AGNO Fix

**Report to AGNO maintainers:**
```python
# Proposed fix for agno/team/team.py
class Team:
    def run(self, session_state=None, **kwargs):
        # ADD THIS LINE:
        if session_state is not None:
            self.session_state = session_state

        # Rest of implementation...
```

**Once AGNO fixes this:**
1. Update to new AGNO version
2. Test without workaround
3. Remove manual assignment (line 510)
4. Update documentation
5. Keep this doc as historical reference

### Alternative Patterns

**Option 1: Use RunContext Everywhere**
- Modify callable instructions to receive `run_context` instead of `agent`
- Access via `run_context.session_state` (works without workaround)
- Requires AGNO framework changes (not currently supported)

**Option 2: Dependency Injection**
- Pass `deep_research` as a dependency instead of session_state
- Requires restructuring entire instruction system
- More complex, less maintainable

**Option 3: Static Instructions**
- Remove callable instructions, use static strings
- Pass mode context via different mechanism
- Loses dynamic instruction benefits

---

**Document Status:** ✅ Complete and Production Ready
**Maintained By:** Cirkelline Development Team
**Last Reviewed:** 2025-11-27
