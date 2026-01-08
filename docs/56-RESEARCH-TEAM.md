# Research Team - Complete Documentation

**Version:** v1.2.34
**Status:** PRODUCTION READY
**Created:** 2025-12-01
**Last Updated:** 2025-12-01

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Evolution](#architecture-evolution)
3. [Team Structure](#team-structure)
4. [Specialized Researchers](#specialized-researchers)
5. [Search Tools Guide](#search-tools-guide)
6. [Team Leader & Synthesis](#team-leader--synthesis)
7. [Integration Modes](#integration-modes)
8. [Configuration Reference](#configuration-reference)
9. [Workflow Examples](#workflow-examples)
10. [Testing & Verification](#testing--verification)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The Research Team is a specialized multi-agent team within Cirkelline that handles comprehensive web research tasks. It provides intelligent routing to specialized researchers and expert synthesis of findings.

### Key Features

- **3 Specialized Researchers**: Each with a single search tool optimized for specific query types
- **Intelligent Routing**: Team leader decides which researcher(s) to use based on query analysis
- **Built-in Synthesis**: Team leader synthesizes findings directly (no separate analyst)
- **Cost Optimization**: Only uses needed researchers, not always all three
- **Concurrent Execution**: With `arun()`, multiple researchers can work in parallel

### When Research Team is Used

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Quick Search** | `deep_research=false` (default) | Cirkelline uses search tools directly |
| **Deep Research** | `deep_research=true` (user toggle) | Cirkelline delegates to Research Team |

---

## Architecture Evolution

### Pre-v1.2.34 Structure (Sequential)

```
Research Team (Old)
├── Web Researcher
│   └── Tools: DuckDuckGo + Exa + Tavily (ALL 3)
│   └── Role: Search web, stop after first success
│
└── Research Analyst
    └── Tools: None (receives findings)
    └── Role: Synthesize and analyze findings
```

**Problems:**
- Web Researcher had all tools but was told to "stop after first success"
- No intelligent routing - couldn't leverage tool strengths
- Sequential flow: Researcher → Analyst (extra hop)
- Analyst added latency without clear benefit

### v1.2.34 Structure (Coordinator)

```
Research Team (New)
│
├── Team Leader (Gemini 2.5 Flash)
│   └── Tools: ReasoningTools (think/analyze)
│   └── Role: Decide which researchers + synthesize findings
│
├── DuckDuckGo Researcher
│   └── Tool: DuckDuckGoTools only
│   └── Specialty: News, current events, quick facts
│
├── Exa Researcher
│   └── Tool: ExaTools only
│   └── Specialty: Semantic search, research topics, conceptual
│
└── Tavily Researcher
    └── Tool: TavilyTools only
    └── Specialty: Comprehensive deep search, comparisons
```

**Benefits:**
- Each researcher is a specialist with one tool
- Team leader intelligently routes based on query type
- Team leader synthesizes directly (analyst methodology built-in)
- Can use 1, 2, or all 3 researchers as needed
- With `arun()`, parallel execution when multiple researchers used

---

## Team Structure

### File Location

```
cirkelline/agents/research_team.py
```

### Components

```python
# Three specialized researchers
duckduckgo_researcher = Agent(...)   # News & current events
exa_researcher = Agent(...)          # Semantic & conceptual search
tavily_researcher = Agent(...)       # Comprehensive deep search

# Team with coordinator pattern
research_team = Team(
    id="research-team",
    name="Research Team",
    members=[duckduckgo_researcher, exa_researcher, tavily_researcher],
    # Team leader decides which researchers to use
    # Team leader synthesizes findings directly
)
```

### AGNO Team Pattern

The Research Team uses the **Coordinator** pattern (default):

| Parameter | Value | Effect |
|-----------|-------|--------|
| `respond_directly` | `False` (default) | Team leader synthesizes responses |
| `delegate_to_all_members` | `False` (default) | Team leader chooses which researchers |
| `determine_input_for_members` | `True` (default) | Team leader crafts specific tasks |

This means:
- Team leader analyzes the research request
- Team leader decides which researcher(s) to delegate to
- Team leader synthesizes all findings into one response

---

## Specialized Researchers

### 1. DuckDuckGo Researcher

**ID:** `duckduckgo-researcher`

**Tool:** `DuckDuckGoTools`
- `duckduckgo_search` - General web search with keyword matching
- `duckduckgo_news` - News-specific search

**Best For:**
- News and current events
- Breaking news and recent happenings
- Quick factual lookups
- Recent product releases and announcements
- Time-sensitive queries

**Example Queries:**
- "What's the latest news about AI agents?"
- "Recent SpaceX launches"
- "Today's stock market updates"
- "Weather in Copenhagen"

**How DuckDuckGo Works:**
- **Keyword-based search** - finds pages containing your exact words
- Fast and reliable for news
- Best when user wants CURRENT information

```python
duckduckgo_researcher = Agent(
    id="duckduckgo-researcher",
    name="DuckDuckGo Researcher",
    description="Search news and current events using DuckDuckGo",
    role="News and current events search specialist",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools(add_instructions=True)],
    instructions=[
        "You are a news and current events search specialist using DuckDuckGo.",
        "Use duckduckgo_news for news-related queries",
        "Use duckduckgo_search for general factual queries",
        "Focus on RECENT, TIMELY information",
        "Return findings with source URLs",
    ],
)
```

---

### 2. Exa Researcher

**ID:** `exa-researcher`

**Tool:** `ExaTools`
- `search_exa` - Semantic search
- `get_contents` - Retrieve full page content
- `find_similar` - Find similar content
- `exa_answer` - Direct answers from search

**Best For:**
- Research topics and conceptual understanding
- Technical articles and blog posts
- Finding content by MEANING, not just keywords
- Discovering related content keyword search might miss
- Research papers, technical deep-dives, expert opinions

**Example Queries:**
- "How do AI agents work?"
- "Best practices for microservices architecture"
- "Understanding quantum computing concepts"
- "Machine learning optimization techniques"

**How Exa is Different:**
- **Semantic search** - understands concepts, not just words
- Finds articles about "autonomous systems" when searching "AI agents"
- Discovers unexpected but relevant content
- Great for research and learning

```python
exa_researcher = Agent(
    id="exa-researcher",
    name="Exa Researcher",
    description="Semantic search for research topics and conceptual content",
    role="Semantic search and research specialist",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[ExaTools(add_instructions=True)],
    instructions=[
        "You are a semantic search specialist using Exa.",
        "Exa uses semantic search - finds content by MEANING",
        "Good for: research papers, blog posts, technical content",
        "Can find related content even without exact keyword matches",
        "Return findings with source URLs",
    ],
)
```

---

### 3. Tavily Researcher

**ID:** `tavily-researcher`

**Tool:** `TavilyTools`
- `web_search_using_tavily` - AI-optimized comprehensive search

**Best For:**
- In-depth research and analysis
- Comparisons and detailed evaluations
- Fact-checking and verification
- Structured, comprehensive information
- Complex queries requiring detailed answers

**Example Queries:**
- "Compare React vs Vue for enterprise applications"
- "GDPR compliance requirements for SaaS"
- "Best CRM platforms for small businesses"
- "Detailed analysis of electric vehicle market"

**How Tavily is Different:**
- **AI-optimized search** - returns clean, structured content
- Better for complex queries requiring detailed answers
- Excellent for comparisons and evaluations
- Returns more context and detail than keyword search

```python
tavily_researcher = Agent(
    id="tavily-researcher",
    name="Tavily Researcher",
    description="Comprehensive deep search and detailed analysis",
    role="Comprehensive research and fact-checking specialist",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[TavilyTools(add_instructions=True)],
    instructions=[
        "You are a comprehensive research specialist using Tavily.",
        "Tavily is AI-optimized - returns structured, detailed content",
        "Good for: comparisons, fact-checking, thorough research",
        "Return detailed findings with source URLs",
    ],
)
```

---

## Search Tools Guide

### Quick Reference

| Tool | Type | Speed | Depth | Best For |
|------|------|-------|-------|----------|
| **DuckDuckGo** | Keyword | Fast | Shallow | News, current events, quick facts |
| **Exa** | Semantic | Medium | Medium | Research topics, conceptual, related content |
| **Tavily** | AI-optimized | Slower | Deep | Comparisons, analysis, comprehensive research |

### Decision Matrix

```
Query Type Analysis:
┌─────────────────────────────────────────────────────────────┐
│  "latest news about..."     → DuckDuckGo (news/current)     │
│  "recent events..."         → DuckDuckGo (news/current)     │
│  "what happened today..."   → DuckDuckGo (news/current)     │
├─────────────────────────────────────────────────────────────┤
│  "how does X work..."       → Exa (conceptual)              │
│  "best practices for..."    → Exa (research/conceptual)     │
│  "explain..."               → Exa (conceptual)              │
│  "understanding..."         → Exa (research)                │
├─────────────────────────────────────────────────────────────┤
│  "compare..."               → Tavily (comprehensive)        │
│  "detailed analysis of..."  → Tavily (comprehensive)        │
│  "evaluate..."              → Tavily (comprehensive)        │
│  "requirements for..."      → Tavily (comprehensive)        │
└─────────────────────────────────────────────────────────────┘
```

### When to Use Multiple Researchers

| Scenario | Researchers Used |
|----------|------------------|
| Simple news query | DuckDuckGo only |
| Conceptual question | Exa only |
| Comprehensive comparison | Tavily + Exa |
| Thorough research project | All 3 researchers |
| Breaking news + context | DuckDuckGo + Exa |

---

## Team Leader & Synthesis

### Role

The Team Leader (Cirkelline's Gemini model) acts as both **coordinator** and **analyst**:

1. **Analyze** the research request using `think()` tool
2. **Decide** which researcher(s) to delegate to
3. **Delegate** tasks to chosen researchers
4. **Wait** for complete findings
5. **Synthesize** findings using built-in methodology

### Synthesis Methodology

The team leader follows this synthesis approach (previously the Research Analyst's role):

#### Step 1: Evaluate Source Quality

**HIGH CREDIBILITY (trust these):**
- Official documentation, company sites
- Established news (Reuters, AP, major newspapers)
- Academic/research institutions
- Government agencies

**MEDIUM CREDIBILITY (use with context):**
- Reputable blogs from domain experts
- Industry news sites (TechCrunch, Ars Technica)
- Professional publications

**LOWER CREDIBILITY (verify before using):**
- Anonymous sources, user comments
- Sites with obvious bias
- Outdated information (check dates!)

#### Step 2: Identify Patterns Across Sources

- What do MOST sources agree on? (likely accurate)
- What appears in multiple sources? (corroboration)
- What's consistently mentioned? (important themes)
- What's only mentioned once? (unique insight or outlier)

#### Step 3: Handle Conflicting Information

When sources disagree:
- Note the conflict explicitly
- Trust official docs over forums
- Prefer newer info over old
- Present both perspectives if both credible

#### Step 4: Structure Response

1. **Direct answer** to the research question
2. **Key findings** (most important insights)
3. **Supporting details** (organized by THEME, not by source)
4. **Considerations** (caveats, conflicts, limitations)
5. **Sources** (cite where information came from)

#### Step 5: Quality Check

Ensure response is:
- Synthesized (themes, not source-by-source listing)
- Credible (higher weight to official sources)
- Balanced (mentions strengths AND limitations)
- Clear (organized logically)
- Actionable (helps user make decisions)

---

## Integration Modes

### Quick Search Mode (Default)

**Trigger:** `deep_research=false` in request

**Flow:**
```
User Query → Cirkelline → Uses DuckDuckGo/Exa/Tavily directly → Response
```

**Cirkelline's Tools in Quick Search:**
- `DuckDuckGoTools` (duckduckgo_search, duckduckgo_news)
- `ExaTools` (search_exa, get_contents, find_similar, exa_answer)
- `TavilyTools` (web_search_using_tavily)

**Cirkelline's Guidance:**
```
Web Search Tool Selection Guide:

DuckDuckGo → News, current events, quick facts
  • "today's news", "latest iPhone release", "weather in Tokyo"

Exa → Research topics, conceptual understanding
  • "how do AI agents work", "best practices for microservices"

Tavily → Comprehensive research, in-depth analysis
  • "compare React vs Vue", "GDPR compliance requirements"
```

**Characteristics:**
- Fast (5-15 seconds)
- Single search tool
- Direct answer from Cirkelline
- Lower token cost

---

### Deep Research Mode

**Trigger:** `deep_research=true` in request (user toggle in UI)

**Flow:**
```
User Query → Cirkelline → Delegates to Research Team
                                    ↓
                            Team Leader analyzes
                                    ↓
                     ┌──────────────┼──────────────┐
                     ↓              ↓              ↓
              DuckDuckGo      Exa Research    Tavily
              Researcher      (if needed)    Researcher
                     ↓              ↓              ↓
                     └──────────────┼──────────────┘
                                    ↓
                         Team Leader synthesizes
                                    ↓
                    Comprehensive Response → User
```

**Cirkelline's Tools in Deep Research:**
- Search tools (DuckDuckGo, Exa, Tavily) are **REMOVED**
- Only delegation tools remain
- Forces Cirkelline to delegate to Research Team

**Characteristics:**
- Thorough (30-90 seconds)
- Multiple researchers possible
- Multi-source synthesis
- Higher token cost, better quality

---

## Configuration Reference

### Research Team Configuration

```python
research_team = Team(
    # Identity
    id="research-team",
    name="Research Team",
    description="Comprehensive web research using specialized searchers",

    # Model
    model=Gemini(id="gemini-2.5-flash"),

    # Team Members
    members=[duckduckgo_researcher, exa_researcher, tavily_researcher],

    # Team Leader Tools
    tools=[ReasoningTools(add_instructions=True)],  # think() and analyze()

    # Tool Configuration
    tool_choice="auto",      # Let model decide when to use tools
    tool_call_limit=20,      # Prevent runaway loops

    # Context & State
    add_session_state_to_context=True,  # Access user timezone, etc.

    # Member Interaction
    share_member_interactions=True,   # Members see each other's work
    show_members_responses=True,      # Leader sees all responses
    store_member_responses=True,      # Responses stored in session

    # Session Management
    db=db,
    enable_session_summaries=True,
    add_history_to_context=True,
    num_history_runs=5,
    search_session_history=True,
    num_history_sessions=3,

    # Output
    markdown=True,

    # Debug
    debug_mode=True,
    debug_level=2,
)
```

### Individual Researcher Configuration

Each researcher shares common configuration:

```python
researcher = Agent(
    id="xxx-researcher",
    name="Xxx Researcher",
    description="...",
    role="...",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[XxxTools(add_instructions=True)],
    add_session_state_to_context=True,
    instructions=[
        "Current date/time and timezone from session_state",
        "Specialty description",
        "Tool usage guidance",
        "Output format requirements",
    ],
    markdown=True,
    db=db,
    debug_mode=True,
    debug_level=2,
)
```

---

## Workflow Examples

### Example 1: Simple News Query

**User:** "What's the latest AI news?"

**Team Leader Analysis:**
```
think(thought='User wants recent AI news - DuckDuckGo is best for current events')
```

**Delegation:**
```
delegate_task_to_member(
    member_name='DuckDuckGo Researcher',
    task='Search for the latest AI news and developments'
)
```

**Result:** Only DuckDuckGo Researcher used (fast, cost-effective)

---

### Example 2: Conceptual Research

**User:** "How do vector databases work?"

**Team Leader Analysis:**
```
think(thought='User wants conceptual understanding - Exa is best for semantic search')
```

**Delegation:**
```
delegate_task_to_member(
    member_name='Exa Researcher',
    task='Research how vector databases work, their architecture and use cases'
)
```

**Result:** Only Exa Researcher used (semantic understanding)

---

### Example 3: Comprehensive Comparison

**User:** "Compare the best project management tools"

**Team Leader Analysis:**
```
think(thought='User needs comprehensive comparison - use multiple researchers for thorough coverage')
```

**Delegations:**
```
delegate_task_to_member(
    member_name='Tavily Researcher',
    task='Comprehensive comparison of top project management tools with features, pricing, pros/cons'
)
delegate_task_to_member(
    member_name='Exa Researcher',
    task='Research user experiences and expert opinions on project management tools'
)
```

**Result:** Both Tavily and Exa Researchers used, findings synthesized

---

### Example 4: Breaking News + Context

**User:** "What's happening with the OpenAI drama and what does it mean for AI?"

**Team Leader Analysis:**
```
think(thought='User wants both current news AND contextual understanding - DuckDuckGo for news, Exa for analysis')
```

**Delegations:**
```
delegate_task_to_member(
    member_name='DuckDuckGo Researcher',
    task='Find the latest news about the OpenAI situation'
)
delegate_task_to_member(
    member_name='Exa Researcher',
    task='Research analysis and expert opinions on the implications for AI industry'
)
```

**Result:** Both researchers contribute, team leader synthesizes into coherent response

---

## Testing & Verification

### Test Quick Search Mode

```bash
TOKEN="your_jwt_token"

# News query - should use DuckDuckGo
curl -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=What are the latest news about AI agents?" \
  -F "user_id=your_user_id" \
  -F "stream=false" \
  -F "deep_research=false"
```

**Expected Logs:**
```
🔍 Quick Search mode
Added tool duckduckgo_search
Added tool duckduckgo_news
```

### Test Deep Research Mode

```bash
# Comprehensive research - should delegate to Research Team
curl -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Research the best practices for building AI agents in 2025" \
  -F "user_id=your_user_id" \
  -F "stream=false" \
  -F "deep_research=true"
```

**Expected Logs:**
```
🔬 Deep Research Mode: Removed search tools (ExaTools, TavilyTools, DuckDuckGoTools)
delegate_task_to_member(...) completed
Team ID: research-team
Agent ID: duckduckgo-researcher
Agent ID: exa-researcher
Agent ID: tavily-researcher
```

### Verify Researcher Usage

Check backend logs for which researchers were actually used:

```bash
cat /tmp/cirkelline.log | grep -E "(DuckDuckGo Researcher|Exa Researcher|Tavily Researcher) Findings"
```

**Expected Output (for comprehensive query):**
```
DuckDuckGo Researcher Findings: ...
Exa Researcher Findings: ...
Tavily Researcher Findings: ...
```

---

## Troubleshooting

### Issue: Research Team Not Being Used in Deep Research Mode

**Symptoms:**
- `deep_research=true` in request
- But Cirkelline uses search tools directly

**Diagnosis:**
```bash
cat /tmp/cirkelline.log | grep -E "Deep Research|Removed search tools"
```

**Fix:**
1. Verify tool removal code in `custom_cirkelline.py`
2. Check `deep_research` parameter is being passed correctly
3. Restart backend to load latest code

### Issue: Only One Researcher Used for Complex Query

**Symptoms:**
- Complex comparison query
- Only Tavily Researcher responds

**Diagnosis:**
- This may be intentional - team leader decides
- Check logs for `think()` reasoning

**If problematic:**
- Review team leader instructions
- Ensure instructions encourage multi-researcher use for comparisons

### Issue: Slow Response Times

**Symptoms:**
- Deep Research takes > 90 seconds

**Diagnosis:**
```bash
cat /tmp/cirkelline.log | grep -E "Run Start|Run End|completed"
```

**Potential Fixes:**
1. Use `arun()` for concurrent researcher execution
2. Reduce `num_history_runs` and `num_history_sessions`
3. Optimize researcher instructions

### Issue: Poor Synthesis Quality

**Symptoms:**
- Response is source-by-source listing instead of themes
- Missing key information

**Fix:**
- Review team leader synthesis instructions
- Ensure "Step 4: Structure Response" guidelines are followed
- Consider adding more specific synthesis examples

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.2.33 | Pre-Dec 2025 | Old structure: web_researcher + research_analyst |
| v1.2.34 | 2025-12-01 | New structure: 3 specialized researchers, team leader synthesizes |

### Migration Notes

**From v1.2.33 to v1.2.34:**

1. Removed `web_researcher` (had all 3 tools)
2. Removed `research_analyst` (separate synthesis agent)
3. Added `duckduckgo_researcher` (single tool)
4. Added `exa_researcher` (single tool)
5. Added `tavily_researcher` (single tool)
6. Enhanced team leader instructions with synthesis methodology
7. Added `DuckDuckGoTools` to Cirkelline for Quick Search mode

---

## Related Documentation

- [31-DEEP-RESEARCH.md](./31-DEEP-RESEARCH.md) - Deep Research toggle feature
- [01-ARCHITECTURE.md](./01-ARCHITECTURE.md) - System architecture
- [CLAUDE.md](../CLAUDE.md) - Project overview

## Code Locations

| Component | Location |
|-----------|----------|
| Research Team | `cirkelline/agents/research_team.py` |
| Cirkelline Tools | `cirkelline/orchestrator/cirkelline_team.py` |
| Quick Search Instructions | `cirkelline/orchestrator/instructions.py` |
| Deep Research Toggle | `cirkelline/endpoints/custom_cirkelline.py` |

---

**Document Status:** COMPLETE
**Implementation Status:** PRODUCTION READY
**Last Updated:** 2025-12-01
