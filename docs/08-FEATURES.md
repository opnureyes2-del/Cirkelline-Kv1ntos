# FEATURES DOCUMENTATION

**Last Updated:** 2025-11-18
**Current Version:** v1.2.29

---

## Table of Contents
- [Feature Overview](#feature-overview)
- [Deep Research Mode](#deep-research-mode)
- [Custom User Instructions](#custom-user-instructions)
- [AI Reasoning Display](#ai-reasoning-display)
- [Token Usage & Cost Metrics](#token-usage--cost-metrics)
- [Private Knowledge Base](#private-knowledge-base)
- [Admin Profiles](#admin-profiles)
- [Session Management](#session-management)
- [Multi-Agent Routing](#multi-agent-routing)
- [File Uploads](#file-uploads)
- [Search Capabilities](#search-capabilities)
- [Memories Viewer](#memories-viewer)
- [Quick Reference](#quick-reference)

---

## Feature Overview

### Core Features (v1.2.24)

| Feature | Status | Description |
|---------|--------|-------------|
| **Deep Research Mode** | ✅ **Production** | **User-controlled research flexibility toggle. Choose between Quick Search (5-10s, direct answers) and Deep Research (60-90s, comprehensive analysis via Research Team delegation)** |
| **Google Tasks Integration** | ✅ **Production** | **Full CRUD operations for task lists and tasks. Unified OAuth, 3-view UI** |
| **Custom User Instructions** | ✅ **Production** | **Personalize Cirkelline's responses with custom rules** |
| **AI Reasoning Display** | ✅ **Production** | **See Cirkelline's thinking process in Behind the Scenes panel** |
| **Token Usage & Cost Metrics** | ✅ **Production** | **View detailed token usage and costs for every message. Track individual agent costs and conversation totals** |
| Google Services | Production | Gmail, Calendar, Tasks integration with unified OAuth |
| Notion Integration | Production | Dynamic database integration with full CRUD operations |
| Private Knowledge Base | Production | User-isolated document storage with vector search |
| Admin Profiles | Production | Custom profiles for admin users (Ivo, Rasmus) |
| Session Management | Production | Conversation persistence with sidebar |
| Multi-Agent Routing | Production | Intelligent routing to specialist agents |
| File Uploads | Production | Drag-and-drop upload to knowledge base |
| Authentication | Production | JWT-based with anonymous support |
| Streaming Responses | Production | Real-time SSE streaming |
| Hybrid Vector Search | Production | Semantic + keyword search |
| User Memories | Production | Persistent conversation memory |
| Session Summaries | Production | Automatic context summarization |
| Memories Viewer | Production | Visual interface to view and verify captured memories |

### In Development

| Feature | Status | Target |
|---------|--------|--------|
| Public Knowledge Base | Planned | Q1 2025 |
| Team Workspaces | Planned | Q2 2025 |
| Voice Input/Output | Planned | Q2 2025 |
| Mobile App | Planned | Q3 2025 |

---

## Deep Research Mode

### Overview

**Deep Research Mode** is a user-controlled toggle that gives you flexibility over how Cirkelline handles research and legal questions. Instead of always using the same approach, you can now choose between **Quick Search** (fast, direct answers) and **Deep Research** (comprehensive, multi-source analysis).

**Introduced:** v1.2.24
**Status:** ✅ Production
**Location:** Above chat input (toggle switch)

### The Problem It Solves

Before Deep Research Mode, there was a fundamental trade-off:
- **Quick searches** (5-10 seconds) were great for simple queries like "latest news" or "quick facts"
- **Comprehensive research** (60-90 seconds) was better for complex topics requiring multi-source analysis
- **BUT users had no control** - the system always used one approach

Deep Research Mode gives you the power to choose the right tool for the job.

### How It Works

#### Quick Search Mode (Default)

**What It Does:**
- Cirkelline uses search tools (`exa_search`, `tavily_search`) **directly**
- NO delegation to Research Team or Law Team
- Fast, straightforward answers

**Response Time:** 5-10 seconds

**Best For:**
- Latest news headlines
- Quick facts and definitions
- Simple questions with clear answers
- Time-sensitive queries

**Example Query:**
> "What's the latest news on AI developments?"

**What Happens:**
1. You send message
2. Cirkelline uses `tavily_search()` directly
3. Returns summarized results immediately
4. Total time: ~8 seconds

#### Deep Research Mode (Activated)

**What It Does:**
- Cirkelline **delegates** to Research Team (research questions) or Law Team (legal questions)
- Multi-agent collaboration:
  - **Research Team:** Web Researcher searches → Research Analyst synthesizes → Cirkelline presents
  - **Law Team:** Legal Researcher finds sources → Legal Analyst provides analysis → Cirkelline presents
- Comprehensive, well-sourced answers

**Response Time:** 60-90 seconds

**Best For:**
- Complex topics requiring multiple sources
- In-depth analysis and synthesis
- Legal questions requiring case law
- Research that needs verification across sources
- Strategic business decisions

**Example Query:**
> "What are the pros and cons of implementing Slack for team communication? Consider alternatives."

**What Happens:**
1. You send message with Deep Research toggle ON
2. Cirkelline delegates to Research Team
3. Web Researcher performs multiple searches
4. Research Analyst synthesizes findings
5. Cirkelline presents comprehensive answer
6. Total time: ~75 seconds

### How to Use

#### Activating Deep Research Mode

1. **Locate the Toggle**
   - Above the chat input field
   - Left side, before the message box
   - Shows "Deep Research" label

2. **Toggle ON**
   - Click the toggle switch
   - It turns accent-colored
   - "ON" badge appears
   - Tooltip confirms: "Deep Research mode active"

3. **Send Your Message**
   - Type your query as normal
   - Deep Research Mode will be used for this message and all following messages

4. **Toggle OFF (Return to Quick Search)**
   - Click toggle again to disable
   - "ON" badge disappears
   - Returns to Quick Search Mode

#### When to Use Each Mode

**Use Quick Search Mode When:**
- You need a fast answer
- The question is straightforward
- You're looking for recent news or events
- Time is more important than depth
- You already know roughly what you're looking for

**Use Deep Research Mode When:**
- The topic is complex or multi-faceted
- You need comprehensive analysis
- You want multiple perspectives
- Accuracy is critical
- You're making important decisions
- You need citations or sources

### Visual Guide

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔬 Deep Research Mode Toggle                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  [ ○───── ] Deep Research                             │      │
│  │  Quick Search Mode - Fast answers (5-10s)            │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  [ ─────● ] Deep Research [ON]                       │      │
│  │  Deep Research Mode - Comprehensive analysis (60-90s)│      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ What's on your mind?                                      │ │
│  │                                                           │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Technical Details

#### Session Persistence

Your mode choice is **saved per session**:
- Toggle ON in a conversation → stays ON for that conversation
- Start a new chat → resets to Quick Search Mode (default)
- Switch between sessions → each session remembers its own mode

#### Backend Architecture

**Static Instructions + Runtime Context Injection:**

The system uses a clever architecture pattern:
1. Cirkelline has **static base instructions** (always the same)
2. Before each message, the system **appends mode-specific context**
3. Agent sees explicit mode indicator: "🔴 CURRENT MODE FOR THIS REQUEST"
4. After the request, **instructions are restored** to base state

This approach:
- Keeps instructions serializable (required for AGNO)
- Makes mode behavior explicit and clear
- Prevents mode context leakage between requests
- Scales well for future modes

**Example Appended Context:**
```
🔴 CURRENT MODE FOR THIS REQUEST:
✅ DEEP RESEARCH MODE IS ACTIVE
• For research questions: DELEGATE to Research Team
• For legal questions: DELEGATE to Law Team
• Use delegate_task_to_member() for comprehensive analysis
```

#### Performance Comparison

| Mode | Response Time | Agents Used | Best For |
|------|--------------|-------------|----------|
| Quick Search | 5-10 seconds | Cirkelline only | Simple queries, news, facts |
| Deep Research | 60-90 seconds | Cirkelline + Research/Law Team | Complex analysis, decisions, legal |

### Examples

#### Example 1: News Query (Quick Search)

**Query:** "What are today's top tech headlines?"

**Mode:** Quick Search (toggle OFF)

**Response Time:** ~7 seconds

**What Happens:**
- Cirkelline uses `tavily_search()` directly
- Returns top 5 headlines with summaries
- Fast and efficient

#### Example 2: Platform Research (Deep Research)

**Query:** "We're considering implementing Slack for team communication. What are the pros and cons? Are there better alternatives?"

**Mode:** Deep Research (toggle ON)

**Response Time:** ~85 seconds

**What Happens:**
1. Cirkelline delegates to Research Team
2. Web Researcher searches for:
   - Slack features and pricing
   - User reviews and case studies
   - Alternative platforms (Microsoft Teams, Discord, etc.)
   - Comparison articles
3. Research Analyst synthesizes findings:
   - Pros: integrations, searchability, channels
   - Cons: cost, notification overload, learning curve
   - Alternatives: Teams (Microsoft ecosystem), Discord (gaming-friendly)
4. Cirkelline presents comprehensive analysis with recommendations

**Result:** Well-sourced, balanced analysis helping you make an informed decision

#### Example 3: Legal Question (Deep Research)

**Query:** "What are the legal implications of using AI-generated content in marketing materials?"

**Mode:** Deep Research (toggle ON)

**Response Time:** ~90 seconds

**What Happens:**
1. Cirkelline delegates to Law Team
2. Legal Researcher finds:
   - Copyright law precedents
   - AI content ownership cases
   - Regulatory guidelines
3. Legal Analyst provides:
   - Legal analysis
   - Risk assessment
   - Best practices
4. Cirkelline presents comprehensive legal guidance

**Result:** Thorough legal analysis with citations

### Troubleshooting

#### Toggle Not Appearing
- **Check:** Are you logged in?
- **Check:** Do you have an agent or team selected?
- **Fix:** Select "Cirkelline" from the team dropdown

#### Mode Not Changing Behavior
- **Check:** Is the toggle actually ON? (Look for "ON" badge)
- **Check:** Did you send a new message after toggling?
- **Fix:** Refresh the page and try again

#### Deep Research Taking Too Long
- This is expected behavior (60-90 seconds)
- If it exceeds 2 minutes, there may be an issue
- Check "Behind the Scenes" panel to see progress

### Related Features

- **[Behind the Scenes Panel](#ai-reasoning-display)** - See Research Team working in real-time
- **[Multi-Agent Routing](#multi-agent-routing)** - How Cirkelline delegates to specialists
- **[AI Reasoning Display](#ai-reasoning-display)** - View Cirkelline's thinking process

### Future Enhancements

**Planned for Future Releases:**
- **Balanced Mode:** Medium-depth research (30-40 seconds)
- **Auto Mode:** System automatically chooses best mode based on query complexity
- **User Preferences:** Set default mode per user
- **Mode Analytics:** See which mode works best for your query patterns

---

## Custom User Instructions

### Overview

**Custom User Instructions** allow you to personalize how Cirkelline responds to you by providing custom rules that are automatically applied to every conversation. This powerful feature enables you to tailor Cirkelline's behavior, tone, language, and response format to match your exact preferences.

### How to Use

#### Setting Your Instructions

1. **Navigate to Profile**
   - Click your profile icon in the top right
   - Select "Profile" from the dropdown

2. **Find Instructions Field**
   - Scroll to "Instructions for Cirkelline"
   - Enter your custom instructions (max 500 characters)

3. **Save Changes**
   - Click "Save Changes" button
   - Wait for confirmation toast

4. **Test It Out**
   - Go to chat and send a message
   - Cirkelline will follow your instructions

### Example Instructions

#### Multilingual Responses
```
Always provide answers in both English and Danish. Start with English, then provide the Danish translation.
```

**Result:** Every response will be bilingual.

#### Technical Developer Mode
```
Be very technical. Always include code examples, architectural details, and best practices. Don't simplify concepts.
```

**Result:** Responses will be technical with code examples.

#### Beginner-Friendly Learning
```
I'm learning programming. Please explain technical terms, use simple analogies, and provide step-by-step explanations.
```

**Result:** Responses will be educational and beginner-friendly.

#### Professional Business Tone
```
Maintain a formal, professional tone. Structure responses as: 1) Executive summary, 2) Analysis, 3) Recommendations. Always cite sources.
```

**Result:** Responses will be formal and well-structured.

#### Concise & Actionable
```
Keep responses short and actionable. Use bullet points. Focus on what I need to do next.
```

**Result:** Responses will be brief and action-oriented.

### How It Works

#### Behind the Scenes

When you set custom instructions, Cirkelline receives them with **ABSOLUTE PRIORITY**:

```
Your message: "What is Copenhagen known for?"

Cirkelline sees:
═══════════════════════════════════════
🎯 USER CUSTOM INSTRUCTIONS
═══════════════════════════════════════

🔴 CRITICAL: The user has provided custom instructions that MUST be followed:

Always provide answers in both English and Danish

These instructions take ABSOLUTE PRIORITY and must be applied to ALL your responses.
═══════════════════════════════════════

[Your message here]
```

**Result:**
```
**English:**
Copenhagen is known for its colorful Nyhavn harbor, world-class restaurants, sustainable urban design, and being one of the happiest cities in the world.

**Danish:**
København er kendt for sin farverige Nyhavn-havn, restauranter i verdensklasse, bæredygtig bydesign og for at være en af verdens lykkeligste byer.
```

### Technical Details

#### Storage
- **Location:** `users.preferences` JSONB column in PostgreSQL
- **Field:** `preferences.instructions`
- **Max Length:** 500 characters (enforced by frontend)

#### Per-Request Injection
```python
# 1. Load from database (once per chat message)
user_instructions = db.query("SELECT preferences->>'instructions' FROM users WHERE id = user_id")

# 2. Inject into Cirkelline
cirkelline.instructions.extend(custom_instructions_section)

# 3. Process your message
response = cirkelline.run(input=message)

# 4. CRITICAL: Clean up (prevents leakage to other users)
cirkelline.instructions = original_instructions
```

#### Multi-User Isolation
✅ **Guaranteed:** Your instructions NEVER leak to other users
✅ **How:** Proper cleanup after every request
✅ **Verified:** Save-Modify-Restore pattern with `finally` blocks

### Use Cases

#### Language Learning
```
Instructions: "Always provide translations in Spanish with pronunciation guides"
You: "How do I say 'thank you'?"
Cirkelline: "In Spanish, 'thank you' is 'gracias' (GRAH-see-ahs)..."
```

#### Code Review Assistant
```
Instructions: "Review code for security issues, performance bottlenecks, and best practices. Always suggest improvements."
You: [pastes code]
Cirkelline: "Security issues found: 1) SQL injection risk on line 23..."
```

#### Meeting Prep
```
Instructions: "Format responses as meeting agendas with time allocations and action items"
You: "Plan a 1-hour project kickoff meeting"
Cirkelline: [Provides structured agenda with timings]
```

### Limitations

- **500 character max** - Keep instructions concise
- **No sensitive data** - Don't include passwords or private information
- **General guidelines** - Works best with broad behavioral instructions

### Tips for Best Results

✅ **Be specific:** "Always cite sources" vs "Be helpful"
✅ **Be concise:** Short instructions work better than long ones
✅ **Test and iterate:** Try different phrasings to see what works
✅ **Use examples:** "Format like: 1) Summary, 2) Details"

❌ **Avoid contradictions:** Don't ask for both "Be brief" and "Be detailed"
❌ **Don't override core functions:** Instructions won't break safety features

### FAQ

**Q: Will my instructions affect other users?**
A: No! Instructions are per-user and cleaned up after each request.

**Q: Can I change my instructions anytime?**
A: Yes! Changes take effect immediately on your next message.

**Q: What if I clear my instructions?**
A: Cirkelline reverts to her default warm, conversational personality.

**Q: Do instructions work with all features?**
A: Yes! They apply to Google integration, knowledge search, document processing, and all agent responses.

---

## AI Reasoning Display

### Overview

**AI Reasoning Display** provides complete visibility into Cirkelline's thinking process. When Cirkelline reasons through complex problems, you can see the step-by-step thought process in the "Behind the Scenes" panel.

This feature uses **AGNO's ReasoningTools** which provides `think()` and `analyze()` functions that agents can autonomously choose to use when they determine reasoning would improve their response quality.

### How to Access

#### Enable Behind the Scenes Panel

```
1. During a conversation, look for "Show Behind the Scenes" button
2. Click to expand the panel
3. View all reasoning steps, tool calls, and agent work
```

**Visual Location:**
```
┌─────────────────────────────────────┐
│ Cirkelline's Response               │
│                                     │
│ [Answer to your question]           │
│                                     │
│ ▼ Show Behind the Scenes            │ ← Click here
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ ▼ Hide Behind the Scenes            │
│ ┌─────────────────────────────────┐ │
│ │ Cirkelline: Planning response   │ │
│ │                                 │ │
│ │ Let me analyze this step by     │ │
│ │ step. The user is asking...     │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Cirkelline: Planning complete   │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### When Does Reasoning Appear?

Cirkelline **autonomously decides** when to use reasoning based on query complexity:

#### ✅ Reasoning Appears For:

**Complex Calculations:**
```
Query: "I have 100 meters of fence. I want to make a rectangular garden
       with the maximum area. What dimensions should I use?"

Behind the Scenes:
  → Planning response: "This is an optimization problem. I need to find
     dimensions that maximize area given a perimeter constraint..."
  → Analysis complete: "The maximum area is achieved with a square
     (25m × 25m)..."
```

**Logic Puzzles:**
```
Query: "Three people wear hats - one red, one blue, one yellow.
       The person in the red hat can see the other two. Who can see whom?"

Behind the Scenes:
  → Planning response: "Let me reason through this step-by-step. If person
     A wears red, they can see persons B and C..."
```

**Multi-Step Problems:**
```
Query: "Think step-by-step: What is 15% of $250?"

Behind the Scenes:
  → Planning response: "To calculate 15% of $250:
     1. Convert 15% to decimal: 0.15
     2. Multiply: $250 × 0.15 = $37.50
     Therefore, 15% of $250 is $37.50"
```

**Research & Analysis:**
```
Query: "Research the pros and cons of electric vehicles.
       Think through each point carefully."

Behind the Scenes:
  → Planning response: "I'll systematically analyze EVs across multiple
     dimensions: cost, environmental impact, performance..."
  → Delegating to Research Team
  → Research Analyst synthesizing findings
  → Analysis complete
```

#### ❌ Reasoning Doesn't Appear For:

**Simple Queries:**
```
Query: "What's the capital of France?"
Answer: "Paris" (no reasoning needed)
```

**Basic Calculations:**
```
Query: "If I spend 60kr per day on smoking, how much in 1 year?"
Answer: "21,900kr per year" (straightforward math, no reasoning shown)
```

**Factual Questions:**
```
Query: "Who wrote '1984'?"
Answer: "George Orwell" (direct fact retrieval)
```

### How to Trigger Reasoning

#### Method 1: Explicit Request (Guaranteed)

Use phrases that explicitly request reasoning:

```
"Think step-by-step: [your question]"
"Reason through this carefully: [your question]"
"Analyze this systematically: [your question]"
"Show your thought process: [your question]"
```

#### Method 2: Complex Queries (Autonomous)

Ask genuinely complex questions that benefit from reasoning:

```
"What's the most cost-effective way to reduce my carbon footprint?"
"Should I buy a house now or wait 6 months given current market conditions?"
"Design a weekly meal plan for $100 that's healthy and varied"
"Explain quantum entanglement in a way a 10-year-old would understand"
```

#### Method 3: Add Reasoning Instructions to User Profile

```
Profile → Instructions for Cirkelline:
"For complex questions, always show your reasoning step-by-step"
```

### Example Reasoning Sessions

#### Example 1: Optimization Problem

**Query:**
```
"I have 100 meters of fence. I want to make a rectangular garden
 with the maximum area. What dimensions should I use?"
```

**Behind the Scenes:**
```
┌─────────────────────────────────────────────────────────┐
│ Cirkelline: Planning response                           │
│                                                         │
│ This is an optimization problem. I need to find the     │
│ dimensions of a rectangle that:                         │
│ 1. Has a perimeter of 100 meters                        │
│ 2. Maximizes the area                                   │
│                                                         │
│ Let me work through this:                               │
│ - Perimeter = 2(length + width) = 100                   │
│ - So length + width = 50                                │
│ - Area = length × width                                 │
│                                                         │
│ To maximize area with a fixed perimeter, the optimal    │
│ shape is a square where length = width = 25 meters.     │
│                                                         │
│ Maximum area = 25m × 25m = 625 square meters            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Cirkelline: Planning complete                           │
└─────────────────────────────────────────────────────────┘
```

**Visible Response:**
```
To maximize the area of your rectangular garden with 100 meters of fence,
you should make it a square with dimensions of 25m × 25m. This will give
you the maximum area of 625 square meters!
```

#### Example 2: Percentage Calculation

**Query:**
```
"Think step-by-step: What is 15% of $250?"
```

**Behind the Scenes:**
```
┌─────────────────────────────────────────────────────────┐
│ Cirkelline: Planning response                           │
│                                                         │
│ To calculate 15% of $250:                               │
│                                                         │
│ Step 1: Convert the percentage to a decimal             │
│ 15% = 15 ÷ 100 = 0.15                                   │
│                                                         │
│ Step 2: Multiply the decimal by the amount              │
│ $250 × 0.15 = $37.50                                    │
│                                                         │
│ Therefore, 15% of $250 is $37.50                        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Cirkelline: Planning complete                           │
└─────────────────────────────────────────────────────────┘
```

**Visible Response:**
```
15% of $250 is $37.50.
```

### How It Works

#### Architecture

```
User asks complex question
    ↓
Cirkelline evaluates complexity
    ↓
If complex: Uses think() tool from ReasoningTools
    ↓
AGNO Framework emits ReasoningStep events
    ↓
Backend logs: "🧠 REASONING EVENT DETECTED"
    ↓
SSE stream sends to frontend
    ↓
Frontend parses reasoning content
    ↓
Behind the Scenes panel displays reasoning
```

#### ReasoningStep Event Structure

```typescript
{
  event: "ReasoningStep" | "TeamReasoningStep",
  agent_name: "Cirkelline",
  content: {
    title: "Planning response",
    action: "I will analyze...",
    reasoning: "To solve this problem, I need to...",
    confidence: 0.9,
    next_action: "continue"
  },
  reasoning_content: "## Planning response\n\nTo solve this problem...",
  session_id: "uuid",
  run_id: "uuid"
}
```

#### Backend Configuration

**All teams configured with ReasoningTools:**

```python
# Research Team (cirkelline/agents/research_team.py)
research_team = Team(
    tools=[ReasoningTools(add_instructions=True)],
    tool_choice="auto",  # Agents decide when to use
    ...
)

# Law Team (cirkelline/agents/law_team.py)
law_team = Team(
    tools=[ReasoningTools(add_instructions=True)],
    tool_choice="auto",
    ...
)

# Cirkelline (cirkelline/orchestrator/cirkelline_team.py)
cirkelline = Team(
    tools=[
        ReasoningTools(add_instructions=True),
        UserControlFlowTools(...),
        filtered_search_tool,
        notion_tools
    ],
    tool_choice="auto",
    instructions=[
        "For complex tasks that require careful analysis, use the think() tool BEFORE taking action",
        "**When to use think():**",
        "• Logic puzzles or multi-step problems",
        "• Questions requiring deep analysis",
        "• Tasks with multiple possible approaches",
        "• Complex decision-making scenarios",
        "• Planning complicated workflows"
    ]
)
```

**Enhanced Logging (cirkelline/endpoints/custom_cirkelline.py):**

```python
if event_type in ['ReasoningStep', 'TeamReasoningStep', 'ReasoningStarted', 'ReasoningCompleted']:
    logger.info(f"🧠 REASONING EVENT DETECTED: {event_type}")
    logger.info(f"   Agent/Team: {agent_name or team_name}")
    logger.info(f"   Title: {event_data['content'].get('title')}")
    logger.info(f"   Reasoning: {event_data['content'].get('reasoning', '')[:200]}...")
```

#### Frontend Event Parsing

**useAIStreamHandler.tsx:277-291 (Critical Fix):**

```typescript
case RunEvent.ReasoningStep:
case RunEvent.TeamReasoningStep:
  // AGNO emits ReasoningStep events with the step in chunk.content
  const reasoningStep = chunk.content as any
  if (reasoningStep && reasoningStep.title) {
    description = `${source}: ${reasoningStep.title}`
    // Use pre-formatted markdown from chunk.reasoning_content
    details.reasoningContent = (chunk as any).reasoning_content || reasoningStep.reasoning
    details.action = reasoningStep.action
    details.confidence = reasoningStep.confidence
  } else {
    return null
  }
  status = 'in_progress'
  break
```

**What Changed:**
- ❌ **Before**: Looked for `chunk.extra_data.reasoning_steps` (doesn't exist)
- ✅ **After**: Uses `chunk.content` (ReasoningStep object) and `chunk.reasoning_content` (formatted markdown)

#### Frontend Display

**BehindTheScenes.tsx:86-90:**

```typescript
{event.details?.reasoningContent && (
  <div className="text-xs text-light-text dark:text-dark-text italic pl-4 py-2 border-l-2 border-border-primary">
    {event.details.reasoningContent}
  </div>
)}
```

### Autonomous Decision-Making

**Key Concept:** With `tool_choice="auto"`, agents make intelligent decisions about when reasoning is helpful.

#### Agent Decision Process

```
Agent receives query
    ↓
Evaluates complexity:
  - Is this a multi-step problem? → Use think()
  - Does this require analysis? → Use think()
  - Is this a simple fact? → Skip think()
  - Is reasoning explicitly requested? → ALWAYS use think()
    ↓
If using think():
  1. Call think() with title, reasoning text, confidence
  2. AGNO emits ReasoningStep event
  3. Frontend displays in Behind the Scenes
    ↓
If not using think():
  1. Answer directly
  2. No reasoning events emitted
  3. Clean response only
```

#### Why Autonomous?

**Benefits:**
- ✅ **Efficiency**: No reasoning overhead for simple queries
- ✅ **Intelligence**: Agent knows when reasoning adds value
- ✅ **Flexibility**: Users can force reasoning with explicit prompts
- ✅ **Clean UX**: Reasoning appears only when meaningful

**Comparison:**

| Approach | Simple Query | Complex Query |
|----------|--------------|---------------|
| **Always reason** | ❌ Unnecessary overhead | ✅ Shows thought process |
| **Never reason** | ✅ Fast response | ❌ No visibility into logic |
| **Autonomous (used)** | ✅ Fast & clean | ✅ Shows reasoning when needed |

### Testing Reasoning

#### Test Queries

**Guaranteed Reasoning (explicit):**
```
"Think step-by-step: What is 15% of $250?"
"Reason through this: Should I invest in stocks or bonds?"
"Show your work: Calculate the compound interest on $10,000 at 5% for 3 years"
```

**Likely Reasoning (complex):**
```
"I have 100 meters of fence. What rectangular dimensions maximize area?"
"Compare the lifecycle costs of electric vs. gas vehicles for 10 years"
"Design a balanced meal plan for a week under $100"
"Explain how blockchain consensus mechanisms work"
```

**No Reasoning (simple):**
```
"What's the capital of France?"
"60kr/day for a year = ?"
"Who wrote '1984'?"
"What's the weather today?"
```

#### Verification Steps

1. **Send test query** (use complex/explicit reasoning prompt)
2. **Check Behind the Scenes panel** - Should see reasoning steps
3. **Check browser console** - No errors
4. **Check backend logs** - Look for `🧠 REASONING EVENT DETECTED`

#### Backend Log Example

```bash
INFO:     🧠 REASONING EVENT DETECTED: ReasoningStep
INFO:        Agent/Team: Cirkelline
INFO:        Title: Planning response
INFO:        Reasoning: To calculate 15% of $250:

Step 1: Convert the percentage to a decimal
15% = 15 ÷ 100 = 0.15

Step 2: Multiply the decimal...
```

### Technical Details

#### AGNO ReasoningTools

**Two Approaches Available:**

1. **ReasoningTools (toolkit)** - ✅ Used in Cirkelline
   - Provides `think()` and `analyze()` as optional tools
   - Agents decide when to use them
   - Requires `tool_choice="auto"`
   - Emits dedicated reasoning events

2. **reasoning=True (native)** - ❌ Not used
   - Built into model's native reasoning
   - Less control over when/how reasoning appears
   - Different event structure

**Why ReasoningTools?**
- More explicit control
- Better visibility into reasoning steps
- Agents can choose when reasoning adds value
- Works well with AGNO's tool system

#### Event Types

**Three reasoning events:**

1. **ReasoningStarted**
   - When reasoning begins
   - Indicates agent is about to think

2. **ReasoningStep** (Main event)
   - Each think() or analyze() call
   - Contains title, reasoning text, confidence
   - **This is what appears in Behind the Scenes**

3. **ReasoningCompleted**
   - When reasoning finishes
   - Indicates agent is done thinking

#### Data Flow

```
1. Agent calls think()
   ↓
   think(
       title="Planning response",
       thought="To solve this, I need to...",
       confidence=0.9
   )

2. AGNO Framework processes
   ↓
   Validates tool call
   Creates ReasoningStep object
   Emits ReasoningStep event

3. Backend receives and logs
   ↓
   Event handler detects ReasoningStep
   Logs: "🧠 REASONING EVENT DETECTED"
   Streams to frontend via SSE

4. Frontend parses
   ↓
   useAIStreamHandler receives chunk
   Extracts chunk.content (ReasoningStep)
   Extracts chunk.reasoning_content (markdown)
   Creates BehindTheScenesEvent

5. UI displays
   ↓
   BehindTheScenes component renders
   Shows reasoning in expandable panel
   User sees thinking process
```

#### Configuration Requirements

**Must have all three:**

1. **ReasoningTools in team tools:**
   ```python
   tools=[ReasoningTools(add_instructions=True)]
   ```

2. **Auto tool choice:**
   ```python
   tool_choice="auto"  # Agents decide when to use
   ```

3. **Instructions encouraging use:**
   ```python
   instructions=[
       "For complex tasks, use the think() tool BEFORE taking action",
       "**When to use think():** [examples]"
   ]
   ```

### Files Modified

#### Backend

**my_os.py:**
- Lines 1438, 1471, 1610: ReasoningTools configuration (already correct)
- Lines 2604-2619: Enhanced reasoning event logging (NEW in v1.2.16)
- Lines 1636-1656: Reasoning instructions for Cirkelline

#### Frontend

**useAIStreamHandler.tsx:**
- Lines 277-291: ReasoningStep event parsing (FIXED in v1.2.16)
  - Changed from `chunk.extra_data.reasoning_steps` to `chunk.content`
  - Now correctly extracts reasoning content

**BehindTheScenes.tsx:**
- Lines 86-90: Reasoning display (already correct)
  - Shows `event.details.reasoningContent` in styled div

### Limitations

**Current:**
- Reasoning appears only when agent decides it's needed
- No user control over reasoning threshold
- Cannot force reasoning for all queries (by design)
- Reasoning text not editable or interactive

**Future Enhancements:**
- User setting: "Always show reasoning"
- Confidence threshold slider
- Interactive reasoning tree
- Ability to provide feedback on reasoning quality

### FAQ

**Q: Why doesn't reasoning appear for every query?**
A: Agents autonomously decide when reasoning adds value. Simple queries get direct answers. Use "Think step-by-step:" to force reasoning.

**Q: Can I make Cirkelline always show reasoning?**
A: Add to your profile instructions: "For complex questions, always show your reasoning step-by-step." This encourages (but doesn't force) reasoning.

**Q: What's the difference between reasoning and tool calls?**
A: Reasoning is internal thinking. Tool calls are actions (searches, calculations). Both appear in Behind the Scenes but serve different purposes.

**Q: Does reasoning slow down responses?**
A: Slightly, but only for complex queries where the reasoning improves answer quality. Simple queries skip reasoning for speed.

**Q: Can other agents besides Cirkelline show reasoning?**
A: Yes! Research Team and Law Team also have ReasoningTools. You'll see "Research Analyst: Synthesizing findings" in Behind the Scenes.

**Q: How do I debug reasoning issues?**
A: Check backend logs for `🧠 REASONING EVENT DETECTED`. If you see the event but not in UI, it's a frontend issue. If no event, agent chose not to reason.

---

## Token Usage & Cost Metrics

### Overview

**Token Usage & Cost Metrics** provides complete visibility into the cost of every conversation with Cirkelline. See exactly how many tokens were used, what they cost, and track individual agent/team costs when work is delegated.

**Introduced:** v1.2.31
**Status:** ✅ Production
**Location:** Behind the Scenes panel (collapsible metrics box at bottom)

### What You Can See

**Individual Agent/Team Costs:**
- Input tokens used
- Output tokens used
- Total tokens
- Input cost (in USD)
- Output cost (in USD)
- Total cost per agent

**Conversation Summary:**
- Total input tokens across all agents
- Total output tokens across all agents
- Grand total tokens
- Total cost for entire conversation

### Pricing Model

All costs use **Gemini 2.5 Flash Tier 1 pricing:**
- **Input tokens:** $0.075 per 1M tokens
- **Output tokens:** $0.30 per 1M tokens

**Example calculation:**
```
Message with 1,234 input tokens and 567 output tokens:
  Input cost:  (1,234 / 1,000,000) × $0.075 = $0.00009255
  Output cost: (567 / 1,000,000) × $0.30  = $0.0001701
  Total cost:  $0.00026265
```

### How to Access

**Step 1:** Send a message to Cirkelline

**Step 2:** Expand Behind the Scenes panel
```
┌─────────────────────────────────────┐
│ Cirkelline's Response               │
│                                     │
│ [Answer to your question]           │
│                                     │
│ ▼ Show Behind the Scenes            │ ← Click here
└─────────────────────────────────────┘
```

**Step 3:** Scroll to bottom of Behind the Scenes

**Step 4:** Click "View Metrics"
```
┌─────────────────────────────────────┐
│ ▼ Hide Behind the Scenes            │
│                                     │
│ [... agent work and reasoning ...]  │
│                                     │
│ ► View Metrics  1,801 tokens · $0.0003 │ ← Click to expand
└─────────────────────────────────────┘
```

**Step 5:** See detailed breakdown
```
┌─────────────────────────────────────┐
│ ▼ Hide Metrics  1,801 tokens · $0.0003 │
│                                     │
│ ─ Cirkelline ─────────────────      │
│ Input Tokens:        1,234          │
│ Output Tokens:         567          │
│ Total Tokens:        1,801          │
│ Input Cost:     $0.00009255         │
│ Output Cost:    $0.0001701          │
│ Total Cost:     $0.00026265         │
│                                     │
│ ══ Conversation Summary ═══════     │
│ Total Input Tokens:    1,234        │
│ Total Output Tokens:     567        │
│ Total Tokens:          1,801        │
│ Total Cost:       $0.00026265       │
└─────────────────────────────────────┘
```

### Multi-Agent Cost Tracking

When Cirkelline delegates to specialist teams, you see individual costs for each agent:

**Example: Research Query with Delegation**
```
User: "Research the latest AI developments"

Behind the Scenes Metrics:

─ Cirkelline ─────────────────
Input Tokens:         234
Output Tokens:         89
Total Tokens:        323
Total Cost:      $0.0000444

─ Research Team ──────────────
Input Tokens:       1,567
Output Tokens:        892
Total Tokens:      2,459
Total Cost:      $0.0003851

══ Conversation Summary ═══════
Total Input Tokens:  1,801
Total Output Tokens:   981
Total Tokens:        2,782
Total Cost:      $0.0004295
```

**Cost breakdown shows:**
- Cirkelline's delegation decision: ~300-500 tokens (~$0.00004)
- Research Team's work: ~2,000-3,000 tokens (~$0.0004)
- Total conversation cost: ~$0.0004-0.0005

### Typical Costs

**Simple queries** (no delegation):
```
"What's the capital of France?"
Tokens: ~50-100
Cost: ~$0.00001-0.00002
Response time: 1-2s
```

**Quick Search** (with search tools):
```
"Latest AI news"
Tokens: ~500-1,000
Cost: ~$0.00008-0.00015
Response time: 5-10s
```

**Deep Research** (with Research Team):
```
"Comprehensive analysis of electric vehicles"
Tokens: ~3,000-5,000
Cost: ~$0.0005-0.0008
Response time: 60-90s
```

**Complex delegation** (multiple teams):
```
"Research legal implications of AI in healthcare"
Tokens: ~5,000-8,000
Cost: ~$0.0008-0.0012
Response time: 90-120s
```

### Design Philosophy

**Single Collapsible Box:**
- ALL metrics in ONE place at the bottom
- No duplicate information in timeline
- Clean, minimal design

**Consistent Styling:**
- Matches existing Behind the Scenes design
- Fade borders (`border-border-primary`)
- Bold white titles (not accent colors)
- Left border with padding (not full box)

**Smart Formatting:**
- Thousand separators for token counts (1,234 not 1234)
- Appropriate decimal places for costs (<$0.01 shows 6 decimals)
- Monospace font for numeric values

### Technical Implementation

**How It Works:**

1. **Agent/Team completes run**
   - AGNO emits `RunCompletedEvent` or `TeamRunCompletedEvent`
   - Event contains `metrics` attribute with token counts

2. **Backend extracts metrics** (`custom_cirkelline.py:586-635`)
   - Extract from `event_data['metrics']` DURING streaming
   - Calculate costs using Tier 1 pricing
   - Create `MetricsUpdate` event

3. **Frontend receives event** (`useAIStreamHandler.tsx:359-382`)
   - Parse `MetricsUpdate` event
   - Create `BehindTheScenesEvent` with metrics data
   - Filter from main timeline (no duplicates)

4. **UI displays metrics** (`BehindTheScenes.tsx:240-397`)
   - Aggregate all metrics from all agents
   - Calculate running totals
   - Display in collapsible box

### Files Modified

**Backend:**
- `/cirkelline/endpoints/custom_cirkelline.py` (lines 586-635)
  - Metrics extraction from completion events
  - Cost calculation function
  - MetricsUpdate event generation

**Frontend:**
- `/cirkelline-ui/src/types/os.ts`
  - Added `MetricsUpdate` to `RunEvent` enum
  - Created `TokenMetrics` interface
  - Added metrics fields to `BehindTheScenesEvent`

- `/cirkelline-ui/src/hooks/useAIStreamHandler.tsx` (lines 359-382)
  - Parse `MetricsUpdate` events
  - Create event with tokenUsage/costs

- `/cirkelline-ui/src/components/chat/ChatArea/Messages/BehindTheScenes.tsx` (lines 240-397)
  - Filter metric events from timeline
  - Aggregate metrics from all events
  - Render collapsible metrics box

### Limitations

**Current:**
- Metrics only appear after completion (not during streaming)
- No historical cost tracking across sessions
- No budget alerts or cost predictions
- Model information not displayed (by design)

**Future Enhancements:**
- Cost breakdown by model (when using multiple models)
- Historical trends (track spending over time)
- Budget alerts (warn when approaching limits)
- Export metrics (download as CSV/JSON)
- Cost comparison (compare different query strategies)

### FAQ

**Q: Why don't I see metrics for every message?**
A: Metrics appear only for messages that complete successfully. If streaming was cancelled or errored, metrics won't be available.

**Q: Are these costs accurate?**
A: Yes! Costs are calculated using official Gemini 2.5 Flash Tier 1 pricing ($0.075/1M input, $0.30/1M output) and actual token counts from AGNO.

**Q: Why does Deep Research cost more?**
A: Deep Research delegates to Research Team, which performs multiple searches and analysis steps. Each agent run uses tokens, resulting in higher total costs.

**Q: Can I see historical costs?**
A: Not yet. Currently metrics are per-message only. Historical tracking is planned for future versions.

**Q: What if I want to reduce costs?**
A: Use Quick Search mode instead of Deep Research for simple queries. Avoid "Think step-by-step" for trivial questions. Keep uploaded documents concise.

**Q: Do metrics include knowledge base searches?**
A: Yes! When Cirkelline searches your uploaded documents, those tokens are included in the metrics.

**Q: How do I debug missing metrics?**
A: Check backend logs for `📊 METRICS FOUND IN COMPLETION EVENT`. If you see the log but no metrics in UI, it's a frontend issue. If no log, the completion event didn't contain metrics.

---

## Private Knowledge Base

### Overview

Users can upload documents that are **only accessible to them**. These documents are embedded with vector search and can be queried through natural conversation.

### How It Works

#### Phase 1: Private Only (Current)

```
All uploads are private by default
    ↓
User uploads document.pdf
    ↓
Document is tagged with user_id
    ↓
Embeddings stored with user_id in metadata
    ↓
Search automatically filters by user_id
    ↓
User only sees their own documents
```

#### Upload Flow

```
Frontend:
  User drags PDF into chat
    ↓
  POST /api/knowledge/upload
  Headers: Authorization: Bearer {jwt}
  Body: FormData with file
    ↓
Backend:
  Extract user_id from JWT
    ↓
  Save file to /tmp/cirkelline_uploads/
    ↓
  Create metadata:
  {
    "user_id": "uuid",
    "user_type": "admin",
    "access_level": "private",
    "uploaded_by": "uuid",
    "uploaded_at": "2025-10-12T10:30:00Z",
    "uploaded_via": "frontend_chat"
  }
    ↓
  Process document:
    - Extract text
    - Chunk into segments
    - Generate 768-dim embeddings (Gemini)
    - Store in vector DB with metadata
    ↓
  Store metadata in ai.agno_knowledge
    ↓
  Return success to frontend
```

### Usage Examples

#### Upload Document

**Frontend:**
```typescript
// User drags file into chat
const handleFileDrop = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_URL}/api/knowledge/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: formData
  })

  if (response.ok) {
    toast.success('File uploaded to your knowledge base!')
  }
}
```

#### Search Documents

**User asks:**
```
"What did I upload about quarterly reports?"
```

**Backend:**
```python
# Custom endpoint applies filter automatically
knowledge_filters = {"user_id": user_id}

cirkelline.run(
    input="What did I upload about quarterly reports?",
    knowledge_filters=knowledge_filters
)
```

**SQL Generated:**
```sql
SELECT
    content,
    metadata,
    embedding <=> query_embedding AS distance
FROM ai.cirkelline_knowledge_vectors
WHERE metadata->>'user_id' = 'current-user-uuid'
  AND (
    embedding <=> query_embedding < 0.5  -- Semantic search
    OR content ILIKE '%quarterly%'        -- Keyword search
  )
ORDER BY distance
LIMIT 5;
```

**Agent Response:**
```
Based on your uploaded documents, here's what I found about quarterly reports:

In "Q3-2024-Report.pdf" (page 3), you noted that revenue increased by 15%...

[Continues with detailed answer from user's documents]
```

### Database Structure

#### Metadata Table (ai.agno_knowledge)

```sql
CREATE TABLE ai.agno_knowledge (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,              -- "document.pdf"
    description TEXT,
    metadata JSONB,                     -- {"user_id": "uuid", "access_level": "private"}
    type VARCHAR,                       -- "pdf"
    size INTEGER,                       -- bytes
    status VARCHAR,                     -- "completed"
    created_at BIGINT,
    updated_at BIGINT
);

CREATE INDEX idx_agno_knowledge_metadata ON ai.agno_knowledge USING GIN (metadata);
```

#### Vector Table (ai.cirkelline_knowledge_vectors)

```sql
CREATE TABLE ai.cirkelline_knowledge_vectors (
    id SERIAL PRIMARY KEY,
    content_id INTEGER,                 -- References agno_knowledge
    embedding VECTOR(768),              -- Gemini embedding
    content TEXT,                       -- Chunk of text
    metadata JSONB                      -- Same as agno_knowledge.metadata
);

CREATE INDEX cirkelline_knowledge_vectors_embedding_idx
ON ai.cirkelline_knowledge_vectors USING HNSW (embedding);
```

### Supported File Types

| Type | Support | Notes |
|------|---------|-------|
| PDF | Native | Gemini processes directly |
| DOCX | Via tool | Converted to text |
| TXT | Native | Direct processing |
| MD | Native | Markdown parsed |
| HTML | Via tool | HTML to text |
| XML | Via tool | Structured extraction |

### Future Enhancements

#### Phase 2: Public Knowledge (Planned)

```json
{
  "metadata": {
    "user_id": "uuid",
    "access_level": "public",
    "shared_with": ["team-id-1", "team-id-2"],
    "permissions": {
      "read": ["all"],
      "write": ["owner"],
      "delete": ["owner"]
    }
  }
}
```

---

## Admin Profiles

### Overview

Admin users (Ivo and Rasmus) have **custom profiles** that provide context to the AI agents. This allows for personalized interactions and responses.

### How It Works

#### Detection

**Hardcoded Admin Emails:**
```python
ADMIN_EMAILS = {
    "opnureyes2@gmail.com": "Ivo",
    "opnureyes2@gmail.com": "Rasmus"
}

is_admin = email in ADMIN_EMAILS
```

#### Profile Loading

**On Login/Signup:**
```python
if is_admin:
    # Query database
    admin_result = session.execute(
        text("""
            SELECT name, role, personal_context,
                   preferences, custom_instructions
            FROM admin_profiles
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    )
    admin_profile = admin_result.fetchone()

    # Add to JWT
    jwt_payload.update({
        "user_name": admin_profile[0],       # "Ivo"
        "user_role": admin_profile[1],       # "CEO & Creator"
        "user_type": "Admin",
        "admin_context": admin_profile[2],   # "Founded Cirkelline..."
        "admin_preferences": admin_profile[3],  # "Prefers technical..."
        "admin_instructions": admin_profile[4]  # "Always provide..."
    })
```

#### Injection into Agent

**JWT Middleware extracts claims:**
```python
dependencies = {
    "user_name": "Ivo",
    "user_role": "CEO & Creator",
    "user_type": "Admin"
}

cirkelline.run(
    input=message,
    dependencies=dependencies
)
```

**Agent Instructions:**
```python
instructions=[
    "User Type: {user_type}",  # Injected: "Admin"

    "Adapt based on user type:",
    "• Admin users: Technical and direct",
    "• Regular users: Friendly and accessible",

    "When talking with admins, understand they built you"
]
```

### Database Schema

```sql
CREATE TABLE admin_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,           -- "Ivo"
    role VARCHAR(255) NOT NULL,           -- "CEO & Creator"
    personal_context TEXT,                -- "Founded Cirkelline in 2024..."
    preferences TEXT,                     -- "Prefers technical details..."
    custom_instructions TEXT,             -- "Always provide code examples..."
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Example Profile

**Ivo's Profile:**
```sql
INSERT INTO admin_profiles (user_id, name, role, personal_context, preferences, custom_instructions)
VALUES (
    'ivo-uuid',
    'Ivo',
    'CEO & Creator',
    'Founded Cirkelline in 2024. Focuses on AI strategy and product development. Technical background in full-stack development.',
    'Prefers technical details with code examples. Likes direct, efficient communication. Interested in AI/ML advancements.',
    'Always provide technical implementation details. Include code snippets when relevant. Be concise but thorough.'
);
```

### Usage in Conversation

**Regular User:**
```
User: "How does the knowledge base work?"
Agent: "Great question! Think of it like a personal library..."
```

**Admin User (Ivo):**
```
Ivo: "How does the knowledge base work?"
Agent: "The knowledge base uses pgvector with HNSW indexing.
        Documents are chunked into 1000-char segments, embedded
        with Gemini (768-dim), and searched via hybrid
        vector + BM25. Filtering applies at query time via
        metadata->>'user_id' WHERE clause..."
```

---

## Session Management

### Overview

Conversations are organized into **sessions**, each with a unique ID. Sessions persist across page refreshes and appear in the sidebar.

### Features

#### New Session Creation

```
User clicks "New Chat"
    ↓
Frontend: sessionId = null
    ↓
User sends first message
    ↓
Backend generates UUID
    ↓
Session stored in database with user_id
    ↓
Frontend receives session_id in first event
    ↓
URL updates: ?session={uuid}
    ↓
Session appears in sidebar immediately
```

#### Session Persistence

**Storage:**
```sql
CREATE TABLE ai.agno_sessions (
    session_id VARCHAR PRIMARY KEY,
    session_type VARCHAR,
    team_id VARCHAR,
    user_id VARCHAR,              -- User isolation
    session_data JSON,            -- User profile data
    runs JSON,                    -- Conversation history
    created_at BIGINT,
    updated_at BIGINT
);
```

**Loading:**
```typescript
// Load all user's sessions
const sessions = await fetch(
  `${API_URL}/teams/cirkelline/sessions`,
  { headers: { 'Authorization': `Bearer ${token}` } }
)

// Load specific session
const runs = await fetch(
  `${API_URL}/sessions/${sessionId}/runs`,
  { headers: { 'Authorization': `Bearer ${token}` } }
)
```

#### Session Sidebar

**Features:**
- Sorted by date (newest first)
- Shows first message as name
- Click to load session
- Delete button
- Instant update on new session

**Optimistic Update (Fixed 2025-10-12):**
```typescript
// OLD: Only added on TeamRunStarted (sometimes late)
if (chunk.event === RunEvent.TeamRunStarted) {
  addToSidebar(chunk.session_id)
}

// NEW: Add on ANY event with session_id
if (chunk.session_id && !currentSessionId) {
  addToSidebar(chunk.session_id)
}
```

### Session Data Structure

```json
{
  "session_id": "7f8e9d2c-4a5b-6c7d-8e9f-0a1b2c3d4e5f",
  "session_type": "team",
  "team_id": "cirkelline",
  "user_id": "cc74dcd6-ce96-4cfb-8295-b619ed0e0d0e",
  "session_data": {
    "user_name": "Ivo",
    "user_type": "Admin"
  },
  "runs": [
    {
      "run_input": "Hello!",
      "content": "Hi Ivo! How can I help?",
      "created_at": "2025-10-12T10:30:00Z",
      "tools": [],
      "extra_data": {}
    }
  ],
  "created_at": 1728567890,
  "updated_at": 1728567920
}
```

---

## Multi-Agent Routing

### Overview

User requests are analyzed and **automatically routed** to the appropriate specialist agent or team.

### Routing Logic

**Orchestrator (Cirkelline) analyzes intent:**

```
User: "Transcribe this audio"
    ↓
Cirkelline sees audio attachment
    ↓
Routes to Audio Specialist
    ↓
Audio Specialist processes
    ↓
Returns transcription
    ↓
Cirkelline rewrites in friendly tone
    ↓
User sees: "Here's what I heard in the audio..."
```

### Routing Table

| Intent | Target | Tools |
|--------|--------|-------|
| Image analysis | Image Specialist | Gemini multimodal |
| Audio transcription | Audio Specialist | Gemini multimodal |
| Video analysis | Video Specialist | Gemini multimodal |
| Document processing | Document Specialist | PDF tools, knowledge search |
| Web research | Research Team | DuckDuckGo, Exa, Tavily |
| Legal questions | Law Team | Legal search |
| General conversation | Cirkelline | Knowledge base |

### Example Flows

#### Research Request

```
User: "Research the best laptops for coding in 2025"
    ↓
Cirkelline:
  1. Gathers context (budget? preferences?)
  2. Routes to Research Team
    ↓
Research Team Coordinator:
  → Web Researcher: searches multiple sources
  → Research Analyst: synthesizes findings
    ↓
Cirkelline:
  Rewrites in conversational tone
    ↓
User sees:
  "I found some great options for you!

   Based on the latest reviews, here are the top picks:

   1. MacBook Pro 16" M3 Max
      - Excellent for development
      - 36GB RAM, 512GB storage
      - Price: $3,499
      ...

   [Full synthesized response]"
```

#### Document + Knowledge Search

```
User: "Summarize this PDF and compare with my previous reports"
    ↓
Cirkelline:
  1. Routes to Document Specialist
  2. Passes knowledge_filters for user isolation
    ↓
Document Specialist:
  1. Processes new PDF (Gemini native)
  2. Searches knowledge base for previous reports
  3. Compares and synthesizes
    ↓
Cirkelline:
  Presents unified response
```

### Hidden from User

**What user DOESN'T see:**
- "Delegating to Web Researcher"
- "Research Analyst synthesizing"
- "Searching knowledge base"

**What user DOES see:**
- Single, cohesive response
- Natural conversation flow
- Optional tool calls (searches, etc.)

---

## File Uploads

### Overview

Users can **drag-and-drop files** directly into the chat interface. Files are uploaded to the knowledge base and become searchable.

### Supported Methods

#### 1. Drag-and-Drop

```typescript
// ChatInput component
const handleDrop = async (e: DragEvent) => {
  e.preventDefault()
  const file = e.dataTransfer.files[0]

  if (file) {
    await uploadFile(file)
    toast.success(`${file.name} uploaded!`)
  }
}
```

#### 2. File Button

```typescript
// ChatInput component
const handleFileSelect = async (e: ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0]

  if (file) {
    await uploadFile(file)
  }
}
```

### Upload Process

```
1. User drops file
    ↓
2. Frontend: Show loading indicator
    ↓
3. POST /api/knowledge/upload
   Headers: Authorization: Bearer {token}
   Body: FormData with file
    ↓
4. Backend:
   - Extract user_id from JWT
   - Save to /tmp/cirkelline_uploads/{id}_{filename}
   - Create private metadata
   - Process document (chunk, embed, store)
   - Clean up temp file
    ↓
5. Return success
    ↓
6. Frontend: Show success toast
    ↓
7. User can immediately search the document
```

### File Size Limits

| Environment | Limit | Reason |
|-------------|-------|--------|
| Localhost | 50 MB | Python memory |
| AWS | 10 MB | ALB request size limit |

**Override AWS limit:**
```json
// task-definition.json
{
  "environment": [
    {
      "name": "MAX_UPLOAD_SIZE",
      "value": "52428800"  // 50MB
    }
  ]
}
```

### Error Handling

```typescript
try {
  await uploadFile(file)
} catch (error) {
  if (error.message.includes('401')) {
    toast.error('Please log in to upload files')
  } else if (error.message.includes('413')) {
    toast.error('File too large (max 10MB)')
  } else {
    toast.error('Upload failed: ' + error.message)
  }
}
```

---

## Search Capabilities

### Hybrid Vector Search

**Combines two approaches:**

1. **Vector Similarity (Semantic)**
   - Understands meaning
   - Finds conceptually similar content
   - Uses 768-dim Gemini embeddings

2. **BM25 (Keyword)**
   - Finds exact matches
   - Good for specific terms
   - Traditional full-text search

### Search Flow

```
User: "Find documents about Q3 revenue"
    ↓
Generate query embedding (768-dim)
    ↓
Vector search:
  SELECT * FROM cirkelline_knowledge_vectors
  WHERE metadata->>'user_id' = 'user-uuid'
  ORDER BY embedding <=> query_embedding
  LIMIT 10
    ↓
Keyword search:
  SELECT * FROM cirkelline_knowledge_vectors
  WHERE metadata->>'user_id' = 'user-uuid'
    AND content ILIKE '%Q3%'
    AND content ILIKE '%revenue%'
  LIMIT 10
    ↓
Combine and re-rank results
    ↓
Return top 5 to agent
    ↓
Agent synthesizes answer
```

### Search Configuration

```python
vector_db = PgVector(
    db_url=os.getenv("DATABASE_URL"),
    table_name="cirkelline_knowledge_vectors",
    embedder=GeminiEmbedder(),
    search_type=SearchType.hybrid,  # Vector + BM25
)
```

### Search Quality

**Similarity Threshold:**
- Distance < 0.5: Very relevant
- Distance 0.5-0.7: Somewhat relevant
- Distance > 0.7: Not relevant

**HNSW Index:**
- Fast approximate nearest neighbor search
- Sub-second search even with millions of vectors
- 95%+ recall accuracy

---

## Memories Viewer

### Overview

The **Memories Viewer** provides complete transparency into what Cirkelline learns and remembers about you. It's a dedicated interface that displays all memories captured by the Enhanced Memory Manager (v1.1.19) in an elegant, user-friendly format.

### Why It Exists

**Problem:** Users had no way to verify what memories were being captured or if the memory system was working correctly.

**Solution:** A visual dashboard showing:
- What Cirkelline learned
- What you actually said
- How memories are categorized
- When memories were captured

### How to Access

#### From Sidebar
```
1. Click "Memories" button in sidebar
   (Brain icon next to Sessions)
    ↓
2. Navigates to /memories page
    ↓
3. View all your captured memories
```

#### Direct URL
```
http://localhost:3000/memories
```

### Features

#### Memory Cards
Each memory is displayed in a card showing:

```
┌─────────────────────────────────────────┐
│ 📝 Memory Content                       │
│ "User prefers dark mode for coding"     │
│                                         │
│ 💬 From Conversation:                   │
│ "I always code in dark mode"            │
│                                         │
│ 🏷️ Topics: [preferences, development]   │
│                                         │
│ 📅 Oct 12, 2025, 7:30 PM                │
│                                         │
│ ▼ Technical details                     │
└─────────────────────────────────────────┘
```

#### Loading States
```typescript
// While fetching
<Loader2 className="animate-spin" />
"Loading your memories..."
```

#### Error Handling
```typescript
// On error
"Failed to fetch memories: [error message]"
[Try Again button]
```

#### Empty State
```typescript
// No memories yet
<Brain icon (greyed out) />
"No memories yet"
"Start chatting with Cirkelline to build your memory profile!"
```

#### Refresh Button
```typescript
// At bottom of page
<button onClick={fetchMemories}>
  <Brain icon />
  Refresh Memories
</button>
```

### Data Structure

#### API Response
```json
{
  "success": true,
  "count": 15,
  "memories": [
    {
      "memory_id": "7f8e9d2c-4a5b-6c7d-8e9f-0a1b2c3d4e5f",
      "memory": "User prefers dark mode for coding",
      "input": "I always code in dark mode",
      "topics": ["preferences", "development"],
      "updated_at": "2025-10-12T19:30:00Z",
      "agent_id": "cirkelline",
      "team_id": "cirkelline"
    }
  ]
}
```

#### Frontend Interface
```typescript
interface Memory {
  memory_id: string
  memory: string              // What Cirkelline learned
  input: string | null        // What user said
  topics: string[]            // Categories
  updated_at: string | null   // ISO timestamp
  agent_id: string | null     // Which agent captured it
  team_id: string | null      // Which team context
}
```

### Backend Implementation

#### Endpoint
```python
@app.get("/api/user/memories")
async def get_user_memories(request: Request):
    """
    Fetch all memories for authenticated user from ai.agno_memories.
    Returns comprehensive memory data with original input context.
    """
    # 1. Extract user_id from JWT
    # 2. Query database with user isolation
    # 3. Format and return memories
```

#### Database Query
```sql
SELECT
    memory_id,
    memory,
    input,
    topics,
    updated_at,
    agent_id,
    team_id
FROM ai.agno_memories
WHERE user_id = :user_id
ORDER BY updated_at DESC
```

#### Authentication
```python
# JWT token required
Authorization: Bearer {token}

# Token decoded to extract user_id
# Ensures users only see their own memories
```

### Frontend Implementation

#### Component Location
```bash
cirkelline-ui/src/app/memories/page.tsx
```

#### Key Logic
```typescript
export default function MemoriesPage() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const { token } = useAuthStore()

  const fetchMemories = async () => {
    const response = await fetch('http://localhost:7777/api/user/memories', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    const data = await response.json()
    setMemories(data.memories)
  }

  // Renders memory cards in responsive grid
}
```

#### Styling
```css
/* Gradient background matching Cirkelline aesthetic */
bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50

/* Card hover effects */
hover:shadow-lg transition-shadow

/* Dark mode support */
dark:from-gray-900 dark:via-gray-800 dark:to-indigo-900

/* Responsive grid */
grid gap-4 md:grid-cols-2 lg:grid-cols-3
```

### Use Cases

#### 1. Verify Memory Quality
```
User checks: "Did Cirkelline capture that correctly?"

Memories Viewer shows:
  Input: "I prefer TypeScript over JavaScript"
  Memory: "User prefers TypeScript over JavaScript for development"

Result: ✅ Accurate capture
```

#### 2. Audit What's Stored
```
User wonders: "What does Cirkelline know about me?"

Memories Viewer shows all 47 memories:
  - Development preferences
  - Work schedule patterns
  - Communication style
  - Technical expertise areas

Result: ✅ Full transparency
```

#### 3. Debug Memory System
```
Developer checks: "Is Enhanced MemoryManager working?"

Memories Viewer shows:
  - Recent memories appearing
  - Topics properly categorized
  - Timestamps accurate
  - Input context preserved

Result: ✅ System verified working
```

#### 4. Trust Building
```
New user skeptical: "How do I know this AI remembers things?"

After 10 conversations:
  Check Memories Viewer
  See 15 captured insights
  Verify accuracy against conversations

Result: ✅ Trust established
```

### Visual Design

#### Color Palette
```css
/* Primary accent */
indigo-600, indigo-700

/* Memory cards */
bg-white dark:bg-gray-800
border border-gray-200 dark:border-gray-700

/* Topics */
bg-indigo-100 dark:bg-indigo-900/30
text-indigo-700 dark:text-indigo-300

/* Input context */
bg-gray-50 dark:bg-gray-700/50
```

#### Icons
```typescript
import { Brain, Calendar, Tag, FileText, Loader2 } from 'lucide-react'

// Brain: Main icon, sidebar button, empty state
// Calendar: Timestamps
// Tag: Topic labels
// FileText: Original input context
// Loader2: Loading spinner
```

### Performance

#### Pagination
```
Currently: Load all memories at once
Future: Implement pagination for 100+ memories
```

#### Caching
```
Currently: Fresh fetch on page load
Future: Cache with invalidation on new captures
```

#### Real-time Updates
```
Currently: Manual refresh button
Future: WebSocket updates when new memory captured
```

### Security

#### User Isolation
```sql
-- ALWAYS filters by user_id
WHERE user_id = :user_id

-- Impossible to see other users' memories
```

#### Authentication
```python
# JWT required for all requests
# Token validated before query
# 401 returned if invalid/missing
```

### Integration with Enhanced MemoryManager

The Memories Viewer is the **visual companion** to Enhanced MemoryManager (v1.1.19):

```
Enhanced MemoryManager (v1.1.19)
  ↓ Captures memories during conversation
  ↓ Stores in ai.agno_memories
  ↓
Memories Viewer (v1.1.20)
  ↓ Fetches from ai.agno_memories
  ↓ Displays in beautiful UI
  ↓ Provides proof of capture
```

### Files Modified

#### Backend
```python
# cirkelline/endpoints/memories.py
@app.get("/api/user/memories")
async def get_user_memories(request: Request):
    # Full implementation
```

#### Frontend
```typescript
// cirkelline-ui/src/app/memories/page.tsx
// Complete memories viewer component (237 lines)

// cirkelline-ui/src/components/chat/Sidebar/Sidebar.tsx:425-468
// Added "Memories" navigation button
```

### Testing

#### Manual Testing
```bash
# 1. Start backend
cd /home/eenvy/Desktop/cirkelline
source .venv/bin/activate
python my_os.py

# 2. Start frontend
cd cirkelline-ui
npm run dev

# 3. Navigate to http://localhost:3000
# 4. Click "Memories" in sidebar
# 5. Verify memories display correctly
```

#### API Testing
```bash
# Test endpoint directly
curl -X GET http://localhost:7777/api/user/memories \
  -H "Authorization: Bearer $TOKEN"

# Expected response
{
  "success": true,
  "count": 15,
  "memories": [...]
}
```

### Future Enhancements

#### Search and Filter
```typescript
// Filter by topic
<select onChange={(e) => filterByTopic(e.target.value)}>
  <option>All Topics</option>
  <option>development</option>
  <option>preferences</option>
</select>

// Search by keyword
<input
  placeholder="Search memories..."
  onChange={(e) => searchMemories(e.target.value)}
/>
```

#### Export Memories
```typescript
// Download as JSON
<button onClick={exportAsJSON}>
  Export All Memories
</button>

// Download as markdown
<button onClick={exportAsMarkdown}>
  Export as Markdown
</button>
```

#### Edit/Delete Memories
```typescript
// Edit memory
<button onClick={() => editMemory(memory.memory_id)}>
  Edit
</button>

// Delete memory
<button onClick={() => deleteMemory(memory.memory_id)}>
  Delete
</button>
```

#### Memory Analytics
```typescript
// Show statistics
<div>
  <h3>Memory Statistics</h3>
  <p>Total memories: {memories.length}</p>
  <p>Most common topic: {getMostCommonTopic()}</p>
  <p>Memories this week: {getMemoriesThisWeek()}</p>
</div>
```

### Impact

**Before Memories Viewer:**
- ❌ No visibility into memory capture
- ❌ No way to verify system working
- ❌ Users had to trust blindly
- ❌ Debugging required database queries

**After Memories Viewer:**
- ✅ Complete transparency
- ✅ Visual proof of capture
- ✅ Trust built through visibility
- ✅ Easy verification for users and developers

---

## Notion Integration (Dynamic Discovery System)

### Overview

**Notion Integration** provides seamless access to your Notion workspace through Cirkelline, using a revolutionary **dynamic discovery system** that automatically adapts to ANY database structure. Unlike traditional hardcoded integrations, Cirkelline intelligently discovers and maps your databases, allowing you to rename, restructure, and customize your Notion workspace without breaking the integration.

**Status:** ✅ **Production** (v1.2.19 - Dynamic Discovery)
**Added:** v1.2.12 (Static), v1.2.19 (Dynamic)

### Key Features

- 🔍 **Automatic Database Discovery** - Finds ALL databases you share with Cirkelline
- 🏷️ **Smart Classification** - Auto-identifies database types (Tasks, Projects, Companies, Docs)
- 🔄 **Schema-Aware Querying** - Adapts to your property names and types
- 🌐 **Multi-User Ready** - Each user sees only their databases
- 🚀 **No Hardcoded Names** - Works even if you rename "Companies" to "Domains"!
- 📊 **Rich Property Support** - Handles all 15+ Notion property types dynamically

### How It Works

#### 1. OAuth Connection
```
User clicks "Connect Notion"
  ↓
OAuth authorization flow
  ↓
Cirkelline receives access token
  ↓
🔍 AUTOMATIC DISCOVERY TRIGGERED
  ↓
Searches for all shared databases
  ↓
Retrieves full schema for each
  ↓
Auto-classifies by analyzing structure
  ↓
Stores in database registry
  ↓
Ready for AI queries!
```

#### 2. Dynamic Database Registry

Every discovered database is stored with:
- **Database ID**: Unique Notion identifier
- **Title**: Actual name in your Notion workspace
- **Type**: Auto-classified (tasks/projects/companies/documentation/custom)
- **Schema**: Full property definitions (JSONB)
- **Last Synced**: Timestamp of last discovery

**Example Registry Entry:**
```json
{
  "database_id": "abc123...",
  "database_title": "Domains",  // Renamed from "Companies"!
  "database_type": "companies",  // Still recognized
  "schema": {
    "properties": {
      "Company Name": {"type": "title"},
      "Website": {"type": "url"},
      "Industry": {"type": "select", "options": [...]},
      "Contact": {"type": "email"}
    }
  }
}
```

#### 3. Smart Classification Logic

Cirkelline analyzes each database to determine its type:

**Tasks Database Detected If:**
- Title contains "task" OR "todo"
- Has properties: title + status + due date

**Projects Database Detected If:**
- Title contains "project" OR "initiative"
- Has properties: title + timeline/dates

**Companies Database Detected If:**
- Title contains "company", "client", "domain", "customer"
- Has properties: title + (industry OR website OR contact)

**Documentation Database Detected If:**
- Title contains "doc", "knowledge", "wiki", "notes"
- Has properties: title + (category OR tags)

**Custom Database:**
- Anything that doesn't match above patterns
- Still fully queryable!

### Usage Examples

#### Connecting Your Workspace

```
1. Click Notion icon in chat interface
2. Click "Connect Notion Workspace"
3. Authorize Cirkelline to access databases
4. 🔍 Discovery runs automatically
5. Ask Cirkelline: "Show me my tasks"
```

#### Natural Language Queries

**View Tasks:**
```
User: "Show me my tasks"
Cirkelline: 📋 **Your Tasks** (5 total)

1. **Fix login bug**
   • Status: In Progress
   • Priority: High
   • Due: 2025-11-10
   • Link: [View in Notion]

2. **Write documentation**
   • Status: To Do
   • Priority: Medium
   • Link: [View in Notion]
```

**View Projects:**
```
User: "What projects am I working on?"
Cirkelline: 📁 **Your Projects** (3 total)

1. **Website Redesign**
   • Status: Active
   • Start: 2025-11-01
   • End: 2025-12-15
```

**View Companies (Even if Renamed!):**
```
User: "Show me my domains"  // Database renamed from "Companies" to "Domains"
Cirkelline: 🏢 **Domains** (8 total)

1. **Acme Corp**
   • Industry: SaaS
   • Website: acme.com
   • Contact: hello@acme.com
```

**Create Task:**
```
User: "Create a task to review Q4 budget"
Cirkelline: ✅ **Task created in 'Tasks'!**

📝 **Review Q4 budget**
• Status: Not Started
• Priority: High
• Due: 2025-11-15

🔗 View in Notion: [link]
```

### Manual Sync

If you add new databases or rename existing ones:

**Option 1: Reconnect Notion**
- Disconnect and reconnect your workspace
- Discovery runs automatically

**Option 2: API Sync (Advanced)**
```bash
curl -X POST https://api.cirkelline.com/api/notion/databases/sync \
  -H "Authorization: Bearer $TOKEN"
```

**Option 3: Ask Cirkelline**
```
User: "Sync my Notion databases"
Cirkelline: "I'll trigger a refresh... [syncs] Done! Found 5 databases."
```

### Supported Database Types

| Type | Auto-Detected | AI Queries | Create Items |
|------|--------------|------------|--------------|
| **Tasks** | ✅ | ✅ | ✅ |
| **Projects** | ✅ | ✅ | ⏳ Coming Soon |
| **Companies** | ✅ | ✅ | ⏳ Coming Soon |
| **Documentation** | ✅ | ✅ | ⏳ Coming Soon |
| **Custom** | ✅ | ✅ | ⏳ Coming Soon |

### Supported Property Types

Cirkelline dynamically handles ALL Notion property types:

- ✅ **Title** - Page titles
- ✅ **Rich Text** - Formatted text
- ✅ **Number** - Numeric values
- ✅ **Select** - Single-choice dropdowns
- ✅ **Multi-Select** - Multiple-choice tags
- ✅ **Status** - Status indicators
- ✅ **Date** - Dates and date ranges
- ✅ **Checkbox** - True/false toggles
- ✅ **URL** - Web links
- ✅ **Email** - Email addresses
- ✅ **Phone** - Phone numbers
- ✅ **People** - User mentions
- ✅ **Files** - Attachments
- ✅ **Created Time** - Auto-timestamps
- ✅ **Last Edited Time** - Auto-timestamps
- ✅ **Created By** - Auto-attribution
- ✅ **Last Edited By** - Auto-attribution

### Technical Architecture

#### Database Registry (`notion_user_databases`)

```sql
CREATE TABLE notion_user_databases (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    database_id VARCHAR(255) NOT NULL,
    database_title VARCHAR(255),
    database_type VARCHAR(50),  -- tasks/projects/companies/documentation/custom
    user_label VARCHAR(255),    -- User can override display name
    schema JSONB NOT NULL,      -- Full property schema
    is_hidden BOOLEAN DEFAULT FALSE,
    last_synced TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, database_id)
);
```

#### Discovery Process

**When Triggered:**
1. OAuth connection (automatic)
2. Manual sync request
3. Reconnecting workspace

**What Happens:**
1. Search Notion API for all shared databases
2. For each database:
   - Retrieve full schema (GET /v1/databases/{id})
   - Extract properties and their types
   - Classify database type
   - Store in registry
3. Log results: "Discovered 5 databases, stored 5"

**API Calls:**
- `POST /v1/search` with filter: `{"object": "data_source"}`
- `GET /v1/databases/{id}` for each database
- Rate-limited to 3 requests/second (Notion API limit)

#### Query Process

**Old Hardcoded Approach (v1.2.12):**
```python
# ❌ PROBLEM: Breaks if user renames database
search_response = notion.search(...)
for db in results:
    if "Companies" in db["title"]:  # Hardcoded!
        return companies
```

**New Dynamic Approach (v1.2.19):**
```python
# ✅ SOLUTION: Query registry, use stored schema
db = registry.get_database(user_id, type="companies")
schema = db.schema
response = notion.databases.query(database_id=db.id)

for page in response:
    # Extract properties dynamically using schema
    for prop_name, prop_config in schema["properties"].items():
        value = extract_property_value(page[prop_name], prop_config["type"])
```

### Benefits

**For Users:**
- ✅ **Freedom to Organize:** Rename databases without breaking integration
- ✅ **No Setup Required:** Automatic discovery, zero configuration
- ✅ **Custom Structures:** Your property names work out of the box
- ✅ **Multi-Workspace:** Each user has isolated databases

**For Developers:**
- ✅ **Scalable:** Supports unlimited users with different structures
- ✅ **Maintainable:** No hardcoded database names to update
- ✅ **Extensible:** New property types supported automatically
- ✅ **Cacheable:** Schema stored locally, fewer API calls

### Real-World Examples

#### Example 1: Renamed Database
```
User's Notion: "Companies" → "Domains"
Old System: ❌ "No Companies database found"
New System: ✅ "🏢 Domains (8 total)..."
```

#### Example 2: Different User Structures
```
User A: "Tasks" with Status + Priority + Due Date
User B: "To-Do List" with Done Checkbox + Deadline
User C: "Work Items" with Stage + Urgency
All three: ✅ Recognized as tasks, queried correctly
```

#### Example 3: Custom Properties
```
User adds "Estimated Hours" property to Tasks
Next query: ✅ Automatically displayed
No code changes needed!
```

### Limitations

**Current Limitations:**
- ⏳ Schema updates require manual sync (no webhooks yet)
- ⏳ Deleted databases persist in registry until next sync
- ⏳ Unshared databases cannot be discovered (Notion API limitation)
- ⏳ Some complex relation properties not fully supported yet

**Planned Improvements:**
- 🔄 Periodic background sync (daily cron job)
- 🔔 Webhook support for real-time updates
- 🎨 Frontend UI for database management
- 📝 Support for creating items in all database types

### API Reference

**Endpoints:**
```
GET  /api/notion/databases        - List discovered databases
POST /api/notion/databases/sync   - Trigger re-discovery
GET  /api/notion/tasks            - Get tasks from user's database
GET  /api/notion/projects         - Get projects
GET  /api/notion/companies        - Get companies
GET  /api/notion/documentation    - Get documentation
POST /api/notion/tasks            - Create new task
```

**Tool Methods:**
```python
get_notion_tasks()          - Query tasks database
get_notion_projects()       - Query projects database
get_notion_companies()      - Query companies database
get_notion_documentation()  - Query documentation database
create_notion_task()        - Create new task
```

### Security & Privacy

- 🔒 **Token Encryption:** AES-256-GCM encryption for all OAuth tokens
- 👤 **User Isolation:** Complete separation between users
- 🔑 **JWT Authentication:** All requests require valid auth token
- 🗑️ **Cascade Deletion:** Tokens deleted when user account is deleted
- 📊 **Audit Trail:** All database access logged with user_id

### Troubleshooting

**Problem:** "No databases found"
**Solution:**
1. Verify Notion workspace is connected
2. Check databases are shared with Cirkelline integration
3. Run manual sync: POST /api/notion/databases/sync

**Problem:** "Database not showing after rename"
**Solution:** Trigger re-sync to refresh database list

**Problem:** "Properties not displaying"
**Solution:** Schema may be outdated, run sync to refresh

**Problem:** "Can't create tasks"
**Solution:** Ensure database has title property (required by Notion)

### Files Modified

**Backend (v1.2.30+ Modular Structure):**
- `cirkelline/integrations/notion/notion_helpers.py` - Discovery helpers
- `cirkelline/tools/notion_tools.py` - NotionTools (updated for dynamic querying)
- `cirkelline/integrations/notion/oauth_endpoints.py` - OAuth callback (triggers discovery)
- `cirkelline/integrations/notion/database_endpoints.py` - Database management endpoints

**Database:**
- `notion_user_databases` table - Registry storage

**Documentation:**
- `04-DATABASE-REFERENCE.md` - Table schema
- `08-FEATURES.md` - This section
- `10-CHANGELOG.md` - v1.2.19 entry

---

## Implementation Details (v1.2.19)

**⚠️ HISTORICAL DOCUMENTATION:** This section contains legacy implementation details from v1.2.19 (November 2025) BEFORE the v1.2.30 modularization. All `my_os.py` line number references in this section refer to the OLD monolithic file structure and are NO LONGER ACCURATE after v1.2.30 (November 18, 2025).

**For current file locations:** See [docs/18-NOTION-INTEGRATION.md](./18-NOTION-INTEGRATION.md) or the upcoming [docs/29-CODE-LOCATION-MAP.md](./29-CODE-LOCATION-MAP.md) for accurate modular file paths.

This section contains complete technical details about the dynamic Notion integration implementation, including bugs encountered, fixes applied, and internal architecture.

### 1. API Architecture: data_sources vs databases

**Critical Understanding:** The Notion Integration API exposes databases through the `data_sources` endpoint, NOT the standard `databases` endpoint.

#### Why data_sources API?

**Background:**
- When we first implemented Notion integration (v1.2.12), it worked using the `data_sources` API
- During the v1.2.19 dynamic implementation, we mistakenly switched to the `databases` API
- This caused 404 errors: "Could not find database with ID: xxx"

**The Key Difference:**
```python
# ❌ WRONG - Standard Notion API (doesn't work with Integrations)
response = notion_client.databases.retrieve(database_id="abc123")
results = notion_client.databases.query(database_id="abc123")

# ✅ CORRECT - Integration API (works with shared databases)
response = notion_client.data_sources.retrieve(data_source_id="abc123")
results = notion_client.data_sources.query(data_source_id="abc123")
```

**Technical Reason:**
- The Integration API treats databases as "data sources" accessible via OAuth
- Standard `databases` API requires different permissions
- Our OAuth flow grants access to data_sources, not raw database access

**Code Locations Fixed:**
- Line 5162: `get_database_schema()` - Changed retrieve call
- Line 758: `get_notion_tasks()` - Changed query call
- Line 879: `get_notion_projects()` - Changed query call
- Line 979: `get_notion_companies()` - Changed query call
- Line 1079: `get_notion_documentation()` - Changed query call

### 2. Discovery Engine: Complete Flow

#### OAuth Callback → Discovery Trigger

**File:** `my_os.py:5576-5586`

```python
@app.get("/api/oauth/notion/callback")
async def notion_oauth_callback(code: str, state: str):
    """
    Step 1: Exchange authorization code for access token
    Step 2: Encrypt and store token
    Step 3: 🔍 TRIGGER DISCOVERY
    """
    # ... OAuth token exchange ...

    # CRITICAL: Discovery MUST run after token storage
    discovered_count = await discover_and_store_notion_databases(user_id, access_token)

    return RedirectResponse(
        url=f"{FRONTEND_URL}/chat?notion_connected=true&discovered={discovered_count}"
    )
```

#### Discovery Function Architecture

**File:** `my_os.py:5185-5381`

**Function:** `discover_and_store_notion_databases(user_id: str, access_token: str)`

**Complete Code Flow:**

```python
async def discover_and_store_notion_databases(user_id: str, access_token: str) -> int:
    """
    PHASE 1: Initialize Notion Client
    """
    notion = Client(auth=access_token)

    """
    PHASE 2: Search for ALL Shared Databases
    Uses Notion Search API with filter
    """
    search_response = notion.search(
        filter={"property": "object", "value": "data_source"},
        page_size=100
    )

    databases = [r for r in search_response.get("results", []) if r.get("object") == "database"]

    """
    PHASE 3: Process Each Database
    """
    stored_count = 0

    for db in databases:
        database_id = db.get("id")
        database_title = extract_title(db)  # From title or properties

        # CRITICAL: Use data_sources.retrieve() NOT databases.retrieve()
        full_db = notion.data_sources.retrieve(data_source_id=database_id)

        # Extract complete schema
        schema = full_db  # Full response includes properties

        # Auto-classify database type
        database_type = classify_database_type(database_title, schema)

        # Store in registry
        await store_database(user_id, database_id, database_title, database_type, schema)

        stored_count += 1

    """
    PHASE 4: Log Results
    """
    print(f"✅ Stored {stored_count} databases for user {user_id}")

    return stored_count
```

#### Classification Algorithm

**File:** `my_os.py:5077-5142`

**Function:** `classify_database_type(title: str, schema: dict) -> str`

**Algorithm Logic:**

```python
def classify_database_type(title: str, schema: dict) -> str:
    """
    Multi-stage classification using title keywords + property analysis
    """
    title_lower = title.lower()
    properties = schema.get("properties", {})
    prop_names = [p.lower() for p in properties.keys()]

    # STAGE 1: Title keyword matching (case-insensitive)

    if any(keyword in title_lower for keyword in ["task", "todo", "to-do", "to do"]):
        # Verify has task-like properties
        if has_property_types(properties, ["title", "status"]) or has_property_types(properties, ["title", "checkbox"]):
            return "tasks"

    if any(keyword in title_lower for keyword in ["project", "initiative"]):
        # Verify has project-like properties
        if has_property_types(properties, ["title"]) and (has_date_property(properties) or "status" in prop_names):
            return "projects"

    if any(keyword in title_lower for keyword in ["company", "companies", "client", "domain", "customer"]):
        # Verify has company-like properties
        if has_property_types(properties, ["title"]) and any(p in prop_names for p in ["website", "industry", "email", "contact"]):
            return "companies"

    if any(keyword in title_lower for keyword in ["doc", "documentation", "knowledge", "wiki", "note"]):
        # Verify has documentation-like properties
        if has_property_types(properties, ["title"]) and any(p in prop_names for p in ["category", "tags", "type"]):
            return "documentation"

    # STAGE 2: If no match, classify as custom
    return "custom"
```

**Helper Functions:**

```python
def has_property_types(properties: dict, required_types: list) -> bool:
    """Check if schema has properties of specific types"""
    prop_types = [p.get("type") for p in properties.values()]
    return all(req_type in prop_types for req_type in required_types)

def has_date_property(properties: dict) -> bool:
    """Check if any property is a date type"""
    return any(p.get("type") == "date" for p in properties.values())
```

#### Storage Implementation

**File:** `my_os.py:5413-5436`

**Critical Fix Applied:** SQL CAST syntax for JSONB

```python
async def store_database(user_id: str, database_id: str, database_title: str, database_type: str, schema: dict):
    """
    Store database metadata in PostgreSQL registry

    CRITICAL BUG FIX: Use CAST(:schema AS jsonb) not :schema::jsonb
    The double-colon syntax doesn't work with SQLAlchemy parameterized queries
    """

    # Convert schema dict to JSON string for storage
    schema_json = json.dumps(schema)

    # Upsert query (insert or update if exists)
    query = text("""
        INSERT INTO notion_user_databases
        (user_id, database_id, database_title, database_type, schema, last_synced, created_at, updated_at)
        VALUES (:user_id, :database_id, :database_title, :database_type, CAST(:schema AS jsonb), NOW(), NOW(), NOW())
        ON CONFLICT (user_id, database_id)
        DO UPDATE SET
            database_title = EXCLUDED.database_title,
            database_type = EXCLUDED.database_type,
            schema = EXCLUDED.schema,
            last_synced = NOW(),
            updated_at = NOW()
    """)

    await db.execute(query, {
        "user_id": user_id,
        "database_id": database_id,
        "database_title": database_title,
        "database_type": database_type,
        "schema": schema_json  # String, will be cast to JSONB
    })
```

### 3. Property Extraction: Dynamic Querying

**Problem:** Each user has different property names and types. How do we extract values dynamically?

**Solution:** Use stored JSONB schema to know what properties exist and their types

#### Schema Retrieval

**File:** `my_os.py:751, 872, 972, 1072`

**Critical Fix Applied:** Don't parse JSONB as JSON

```python
async def get_notion_tasks(user_id: str) -> str:
    """
    Query tasks from user's dynamically discovered database
    """

    # Get database metadata from registry
    query = text("""
        SELECT database_id, database_title, schema
        FROM notion_user_databases
        WHERE user_id = :user_id AND database_type = 'tasks'
        LIMIT 1
    """)
    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()

    if not row:
        return "📋 No task-related database found..."

    tasks_db_id, db_title, schema_json = row

    # ❌ OLD (WRONG): schema = json.loads(schema_json)  # TypeError!
    # ✅ NEW (CORRECT): JSONB columns return already-parsed dicts
    schema = schema_json  # Already a dict from PostgreSQL

    # Now use schema to extract properties...
```

**Why This Fix Was Needed:**
- PostgreSQL JSONB columns are automatically converted to Python `dict` by psycopg
- Calling `json.loads()` on a dict throws: `TypeError: the JSON object must be str, bytes or bytearray, not dict`
- This bug prevented ALL AI queries from working

#### Dynamic Property Extraction

**File:** `my_os.py:785-855` (example from get_notion_tasks)

```python
# Get properties schema
properties_schema = schema.get("properties", {})

# Query Notion using data_sources API
response = notion.data_sources.query(data_source_id=tasks_db_id, page_size=100)

# Extract data dynamically for each page
tasks_list = []

for page in response.get("results", []):
    page_properties = page.get("properties", {})

    task_data = {
        "id": page.get("id"),
        "url": page.get("url")
    }

    # DYNAMIC EXTRACTION: Loop through ALL properties in schema
    for prop_name, prop_config in properties_schema.items():
        prop_type = prop_config.get("type")
        prop_value = page_properties.get(prop_name, {})

        # Extract based on property type
        if prop_type == "title":
            task_data["title"] = extract_title_property(prop_value)

        elif prop_type == "rich_text":
            task_data[prop_name] = extract_rich_text_property(prop_value)

        elif prop_type == "status":
            task_data[prop_name] = extract_status_property(prop_value)

        elif prop_type == "select":
            task_data[prop_name] = extract_select_property(prop_value)

        elif prop_type == "multi_select":
            task_data[prop_name] = extract_multi_select_property(prop_value)

        elif prop_type == "date":
            task_data[prop_name] = extract_date_property(prop_value)

        elif prop_type == "checkbox":
            task_data[prop_name] = extract_checkbox_property(prop_value)

        elif prop_type == "number":
            task_data[prop_name] = extract_number_property(prop_value)

        elif prop_type == "url":
            task_data[prop_name] = extract_url_property(prop_value)

        elif prop_type == "email":
            task_data[prop_name] = extract_email_property(prop_value)

        elif prop_type == "phone_number":
            task_data[prop_name] = extract_phone_property(prop_value)

        elif prop_type == "people":
            task_data[prop_name] = extract_people_property(prop_value)

        elif prop_type == "files":
            task_data[prop_name] = extract_files_property(prop_value)

        elif prop_type == "created_time":
            task_data[prop_name] = extract_timestamp_property(prop_value)

        elif prop_type == "last_edited_time":
            task_data[prop_name] = extract_timestamp_property(prop_value)

        # ... etc for all 15+ property types

    tasks_list.append(task_data)

# Format for display
return format_tasks_for_display(tasks_list, db_title)
```

**Key Benefits:**
1. **Zero Hardcoding:** Works with ANY property names
2. **Type-Safe:** Extracts values correctly based on Notion's property type
3. **Extensible:** New property types can be added without changing query logic
4. **User-Specific:** Each user's custom properties are automatically supported

### 4. Bugs Encountered & Fixed

#### Bug #1: JSON Parsing TypeError

**Error:**
```
TypeError: the JSON object must be str, bytes or bytearray, not dict
```

**Root Cause:**
- PostgreSQL JSONB columns return Python `dict` objects automatically
- Code was calling `json.loads()` on already-parsed dicts

**Files Affected:**
- `my_os.py:751` - get_notion_tasks()
- `my_os.py:872` - get_notion_projects()
- `my_os.py:972` - get_notion_companies()
- `my_os.py:1072` - get_notion_documentation()
- `my_os.py:1189` - create_notion_task()

**Fix Applied:**
```python
# BEFORE:
schema = json.loads(schema_json)  # ❌ Crashes if schema_json is dict

# AFTER:
schema = schema_json  # ✅ Already a dict from JSONB
```

**Impact:** This bug prevented ALL AI queries from working. Users would see technical error messages when asking about their Notion data.

---

#### Bug #2: Wrong Notion API Endpoints

**Error:**
```
404 Not Found: Could not find database with ID: abc123...
```

**Root Cause:**
- Original implementation (v1.2.12) correctly used `data_sources` API
- Dynamic implementation (v1.2.19) mistakenly switched to `databases` API
- OAuth integration permissions grant access to `data_sources`, not raw `databases`

**Files Affected:**
- `my_os.py:5162` - get_database_schema()
- `my_os.py:758` - get_notion_tasks()
- `my_os.py:879` - get_notion_projects()
- `my_os.py:979` - get_notion_companies()
- `my_os.py:1079` - get_notion_documentation()

**Fix Applied:**
```python
# BEFORE:
db = notion_client.databases.retrieve(database_id=database_id)
response = notion.databases.query(database_id=tasks_db_id)

# AFTER:
db = notion_client.data_sources.retrieve(data_source_id=database_id)
response = notion.data_sources.query(data_source_id=tasks_db_id)
```

**Impact:** This bug prevented database discovery and all queries from working. Critical blocker that made the entire integration non-functional.

**Technical Note:** This is documented in Notion's Integration API docs but easy to miss. Always use `data_sources` for OAuth-based integrations.

---

#### Bug #3: SQL JSONB Casting Syntax Error

**Error:**
```
psycopg.errors.SyntaxError: syntax error at or near ":"
LINE 4: ... VALUES ($1, $2, $3, $4, :schema::jsonb, ...)
                                      ^
```

**Root Cause:**
- PostgreSQL's native cast syntax `:schema::jsonb` doesn't work with SQLAlchemy parameterized queries
- SQLAlchemy replaces `:schema` with a parameter placeholder, leaving invalid `::jsonb` syntax

**File Affected:**
- `my_os.py:5413` - store_database()

**Fix Applied:**
```python
# BEFORE:
VALUES (:user_id, :database_id, :database_title, :database_type, :schema::jsonb, NOW(), ...)

# AFTER:
VALUES (:user_id, :database_id, :database_title, :database_type, CAST(:schema AS jsonb), NOW(), ...)
```

**Impact:** This bug prevented databases from being stored in the registry. Discovery would run but fail silently, leaving users with "No databases found" errors.

**Technical Note:** Always use `CAST(column AS type)` syntax with SQLAlchemy text() queries.

---

#### Bug #4: Hardcoded Database Names in User Messages

**Error:** User-facing messages still referenced "Tasks database", "Projects database", etc., violating the "works with ANY database" requirement.

**Root Cause:**
- Error messages and responses were hardcoded with specific database names
- This broke the promise that users could rename databases freely

**Files Affected:**
- `my_os.py:748` - get_notion_tasks() error message
- `my_os.py:785` - get_notion_tasks() display
- `my_os.py:869` - get_notion_projects() error message
- `my_os.py:969` - get_notion_companies() error message
- `my_os.py:1069` - get_notion_documentation() error message
- `my_os.py:1186` - create_notion_task() display
- `my_os.py:1234` - create_notion_task() error message
- `my_os.py:6330` - API endpoint error message
- `my_os.py:6368` - API endpoint error message

**Fix Applied:**

```python
# EXAMPLE 1: Error Messages
# BEFORE:
return "📋 No Tasks database found. Try saying 'sync my Notion databases'..."

# AFTER:
return "📋 No task-related database found in your Notion workspace. Make sure you've shared your task tracking database with Cirkelline, then say 'sync my Notion databases'!"

# EXAMPLE 2: Success Messages
# BEFORE:
return f"✅ **Task created in 'Tasks'!**\n\n📝 **{title}**..."

# AFTER:
return f"✅ **Task created in '{db_title}'!**\n\n📝 **{title}**..."

# EXAMPLE 3: Property Validation Errors
# BEFORE:
return "❌ Task database doesn't have a title property. Cannot create task."

# AFTER:
return f"❌ Your '{db_title}' database doesn't have a title property. Cannot create items without a title field."
```

**Impact:** This was a critical UX violation. Users who renamed databases (e.g., "Companies" → "Domains") would see confusing messages referencing the old hardcoded names.

**User Feedback:** This bug caused significant frustration, as it directly contradicted the core feature promise of "works with ANY database structure."

### 5. Common Pitfalls & How to Avoid Them

#### Pitfall #1: Assuming JSONB Needs Parsing

**Wrong:**
```python
row = db.execute(query).fetchone()
schema = json.loads(row.schema)  # ❌ TypeError if row.schema is dict
```

**Correct:**
```python
row = db.execute(query).fetchone()
schema = row.schema  # ✅ Already a dict from psycopg
```

**Rule:** PostgreSQL JSONB columns are automatically converted by psycopg. Never call `json.loads()` on them.

---

#### Pitfall #2: Using Wrong Notion API

**Wrong:**
```python
notion.databases.retrieve(database_id="abc123")  # ❌ 404 Not Found
notion.databases.query(database_id="abc123")    # ❌ 404 Not Found
```

**Correct:**
```python
notion.data_sources.retrieve(data_source_id="abc123")  # ✅ Works
notion.data_sources.query(data_source_id="abc123")    # ✅ Works
```

**Rule:** OAuth-based Notion integrations MUST use `data_sources` API, not `databases` API.

---

#### Pitfall #3: PostgreSQL Cast Syntax in SQLAlchemy

**Wrong:**
```python
query = text("INSERT INTO table (col) VALUES (:value::jsonb)")  # ❌ Syntax error
```

**Correct:**
```python
query = text("INSERT INTO table (col) VALUES (CAST(:value AS jsonb))")  # ✅ Works
```

**Rule:** Use `CAST(param AS type)` syntax with SQLAlchemy parameterized queries, not `param::type`.

---

#### Pitfall #4: Hardcoding Database Names

**Wrong:**
```python
return f"✅ Task created in 'Tasks'!"  # ❌ Breaks if user renamed database
```

**Correct:**
```python
return f"✅ Task created in '{db_title}'!"  # ✅ Uses actual database name
```

**Rule:** ALWAYS use the actual database title from the registry. Never hardcode "Tasks", "Projects", "Companies" in user-facing messages.

---

#### Pitfall #5: Forgetting to Trigger Discovery

**Wrong:**
```python
@app.get("/api/oauth/notion/callback")
async def callback(code: str):
    # Store token
    store_token(user_id, access_token)
    # ❌ MISSING: No discovery call!
    return redirect("/chat")
```

**Correct:**
```python
@app.get("/api/oauth/notion/callback")
async def callback(code: str):
    # Store token
    store_token(user_id, access_token)
    # ✅ CRITICAL: Trigger discovery immediately
    discovered_count = await discover_and_store_notion_databases(user_id, access_token)
    return redirect(f"/chat?discovered={discovered_count}")
```

**Rule:** Discovery MUST be triggered immediately after successful OAuth. Otherwise users won't see their databases.

### 6. Testing Checklist

When testing or modifying the Notion integration, verify:

#### Discovery Phase
- [ ] OAuth callback triggers discovery automatically
- [ ] All shared databases are found (check count)
- [ ] Database titles are extracted correctly
- [ ] Schemas are stored as valid JSONB
- [ ] Classification logic assigns correct types
- [ ] Registry table has entries for each database

**Test Query:**
```sql
SELECT database_id, database_title, database_type, last_synced
FROM notion_user_databases
WHERE user_id = 'test-user-id';
```

#### Query Phase
- [ ] `get_notion_tasks()` returns data from user's custom task database
- [ ] `get_notion_projects()` works with renamed databases
- [ ] `get_notion_companies()` adapts to custom property names
- [ ] All property types are extracted correctly
- [ ] Error messages never mention hardcoded database names
- [ ] Success messages use actual database titles

**Test Queries:**
```
User: "Show me my tasks"
User: "What projects am I working on?"
User: "Show me my domains"  (if user renamed Companies to Domains)
```

#### Edge Cases
- [ ] User with no databases gets helpful message
- [ ] User with database missing title property gets clear error
- [ ] Reconnecting workspace updates existing databases
- [ ] Manual sync (/api/notion/databases/sync) works
- [ ] Unsharing a database doesn't break queries (just returns empty results)

### 7. Code Location Reference

**Complete line-by-line reference for key functionality:**

#### Discovery & Classification
- **Lines 5077-5142:** Classification algorithm (`classify_database_type`)
- **Lines 5143-5181:** Helper functions (has_property_types, extract_title, etc.)
- **Lines 5185-5381:** Main discovery function (`discover_and_store_notion_databases`)
- **Lines 5413-5436:** Database storage function (`store_database`)
- **Line 5162:** Schema retrieval using data_sources API

#### NotionTools (Agent Methods)
- **Lines 696-855:** `get_notion_tasks()` - Dynamic task querying
- **Lines 856-950:** `get_notion_projects()` - Dynamic project querying
- **Lines 951-1045:** `get_notion_companies()` - Dynamic company querying
- **Lines 1046-1140:** `get_notion_documentation()` - Dynamic docs querying
- **Lines 1141-1278:** `create_notion_task()` - Dynamic task creation

#### API Endpoints
- **Lines 5576-5586:** OAuth callback (triggers discovery)
- **Lines 5797-5815:** GET /api/notion/databases (list databases)
- **Lines 5817-5908:** POST /api/notion/databases/sync (manual sync)
- **Lines 6280-6340:** GET /api/notion/tasks
- **Lines 6342-6402:** GET /api/notion/projects
- **Lines 6404-6464:** GET /api/notion/companies
- **Lines 6466-6526:** GET /api/notion/documentation
- **Lines 6528-6598:** POST /api/notion/tasks

#### Database Schema
- **Table:** `notion_user_databases`
- **Location:** PostgreSQL public schema
- **Documented In:** `/docs/04-DATABASE-REFERENCE.md`

### 8. Future Improvements

**Planned Enhancements:**

1. **Real-time Sync via Webhooks**
   - Subscribe to Notion database change events
   - Auto-update registry when databases are renamed or properties modified
   - Eliminate need for manual sync

2. **Relation Property Support**
   - Full support for database relations
   - Query related items across databases
   - Display relationship links in responses

3. **Formula & Rollup Properties**
   - Extract computed values from formula properties
   - Display rollup aggregations

4. **Batch Operations**
   - Create multiple tasks/items at once
   - Bulk updates via natural language

5. **Frontend Database Manager**
   - UI to view all discovered databases
   - Manual type assignment overrides
   - Hide/show databases from AI access
   - Custom labels for databases

6. **Page Content Extraction**
   - Read page content (not just properties)
   - Search within page text
   - Include in knowledge base for RAG queries

---

**Last Updated:** 2025-11-07
**Version:** v1.2.19
**Maintained By:** Development Team

---

## Quick Reference

### Feature Status

```
✅ Custom User Instructions
✅ AI Reasoning Display
✅ Private Knowledge Base
✅ Admin Profiles
✅ Session Management
✅ Multi-Agent Routing
✅ File Uploads
✅ Hybrid Vector Search
✅ JWT Authentication
✅ SSE Streaming
✅ User Memories
✅ Session Summaries
✅ Memories Viewer

⏳ Public Knowledge (Planned)
⏳ Team Workspaces (Planned)
⏳ Voice I/O (Planned)
```

### Key Files

```bash
# AI Reasoning Display
my_os.py:1438,1471,1610  (ReasoningTools configuration)
my_os.py:2604-2619       (Enhanced reasoning event logging)
my_os.py:1636-1656       (Reasoning instructions)
useAIStreamHandler.tsx:277-291  (ReasoningStep event parsing)
BehindTheScenes.tsx:86-90       (Reasoning display component)

# Private Knowledge
my_os.py:97-138   (Metadata functions)
my_os.py:1060-1147  (Upload endpoint)

# Admin Profiles
my_os.py:1336-1358  (Profile loading)
Database: public.admin_profiles

# Sessions
my_os.py:780-787  (Session generation)
Database: ai.agno_sessions

# Routing
my_os.py:529-689  (Cirkelline orchestrator)

# File Uploads
useFileUpload.ts  (Frontend)
my_os.py:1060-1147  (Backend)

# Memories Viewer
my_os.py:1595-1687  (Backend API endpoint)
cirkelline-ui/src/app/memories/page.tsx  (Frontend viewer)
Database: ai.agno_memories
```

### Usage Examples

```bash
# Upload document
curl -X POST http://localhost:7777/api/knowledge/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# Search uploaded documents
curl -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=What did I upload about X?" \
  -F "stream=false"

# Create new session
# Just send message with empty session_id
curl -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Hello" \
  -F "session_id="

# Get user memories
curl -X GET http://localhost:7777/api/user/memories \
  -H "Authorization: Bearer $TOKEN"
```

---

**See Also:**
- [01-ARCHITECTURE.md](./01-ARCHITECTURE.md) - System architecture
- [05-BACKEND-REFERENCE.md](./05-BACKEND-REFERENCE.md) - Backend API
- [07-DEVELOPMENT-GUIDE.md](./07-DEVELOPMENT-GUIDE.md) - Development guide
