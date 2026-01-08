# CIRKELLINE INTERNAL FLOW ANALYSIS

**Last Updated:** 2025-10-12
**Version:** v1.1.18
**Purpose:** Complete visual breakdown of how Cirkelline processes user messages

---

## Table of Contents
1. [High-Level Flow](#high-level-flow)
2. [Detailed Step-by-Step Breakdown](#detailed-step-by-step-breakdown)
3. [AGNO Framework Capabilities](#agno-framework-capabilities)
4. [Knowledge Base Flow](#knowledge-base-flow)
5. [Team Delegation Flow](#team-delegation-flow)
6. [Configuration Analysis](#configuration-analysis)
7. [Optimization Opportunities](#optimization-opportunities)

---

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      USER SENDS MESSAGE                              │
│                  "Help me plan a trip to Japan"                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND RECEIVES MESSAGE                          │
│              (POST /teams/cirkelline/runs)                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   JWT MIDDLEWARE EXTRACTS                            │
│    • user_id (from JWT token)                                        │
│    • user_name (e.g., "Ivo", "Guest", or display name)              │
│    • user_role (e.g., "CEO & Creator", "User", "Visitor")           │
│    • user_type (e.g., "Admin", "Regular", "Anonymous")              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              CIRKELLINE.RUN() CALLED WITH:                           │
│    • input: "Help me plan a trip to Japan"                           │
│    • session_id: "uuid-1234-5678"                                    │
│    • user_id: "user-uuid"                                            │
│    • knowledge_filters: {"user_id": "user-uuid"}                     │
│    • dependencies: {"user_name": "Ivo", ...}                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 AGNO FRAMEWORK INITIALIZATION                        │
│  (This happens BEFORE Cirkelline thinks - AUTOMATIC)                │
│                                                                       │
│  1️⃣ LOAD USER MEMORIES (from database)                              │
│     • Search ai.agno_user_memories                                   │
│     • Filter by user_id                                              │
│     • Add to context: "User's name is X, likes Y, etc."             │
│                                                                       │
│  2️⃣ LOAD SESSION HISTORY (from current session)                     │
│     • Get last 10 messages from ai.agno_runs                         │
│     • Filter by session_id + user_id                                 │
│     • Add to context: Previous conversation turns                    │
│                                                                       │
│  3️⃣ SEARCH PAST SESSIONS (semantic search)                          │
│     • Search ai.agno_sessions_summaries (vector search)              │
│     • Find 5 most relevant past sessions                             │
│     • Add to context: "You previously discussed X with user"         │
│                                                                       │
│  4️⃣ INJECT DEPENDENCIES (user profile)                              │
│     • Add user_name, user_role, user_type to context                │
│     • Available in Cirkelline's instructions via {user_type}         │
│                                                                       │
│  5️⃣ PREPARE KNOWLEDGE BASE FILTERS                                  │
│     • Set filters: {"user_id": "user-uuid"}                          │
│     • Ready for search_knowledge_base tool                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CIRKELLINE RECEIVES:                              │
│                                                                       │
│  📝 User Message: "Help me plan a trip to Japan"                    │
│                                                                       │
│  🧠 Context Loaded:                                                  │
│     • Memories: "User is Ivo, CEO, likes travel, etc."              │
│     • Current Session: [Last 10 messages in this chat]              │
│     • Past Sessions: "You helped plan Europe trip 2 months ago"     │
│     • User Profile: {user_type: "Admin"}                             │
│                                                                       │
│  🔧 Tools Available:                                                 │
│     • search_knowledge_base (with user_id filter)                    │
│     • think (reasoning tool)                                         │
│     • delegate_to_audio_specialist                                   │
│     • delegate_to_video_specialist                                   │
│     • delegate_to_image_specialist                                   │
│     • delegate_to_document_specialist                                │
│     • delegate_to_research_team                                      │
│     • delegate_to_law_team                                           │
│                                                                       │
│  📋 Instructions: [All instructions from lines 542-683]              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 CIRKELLINE READS INSTRUCTIONS                        │
│                   (Gemini 2.5 Flash processes)                       │
│                                                                       │
│  Step 1: Check "KNOWLEDGE BASE SEARCH RULES"                         │
│          → User said "trip to Japan", not "my notes"                 │
│          → Don't trigger knowledge search                            │
│                                                                       │
│  Step 2: Check "CURRENT USER PROFILE"                                │
│          → User Type: Admin (from dependencies)                      │
│          → Knows this is Ivo, one of creators                        │
│                                                                       │
│  Step 3: Check "COMMUNICATION STYLE"                                 │
│          → "Always ask clarifying questions before acting (3-5)"     │
│          → "Always gather context first, then help"                  │
│          → Must be warm and conversational                           │
│                                                                       │
│  Step 4: Check "CRITICAL: GATHER CONTEXT BEFORE ACTING"              │
│          → See examples: "Trip Planning" section                     │
│          → Must ask about: dates, location, companions, budget       │
│                                                                       │
│  Step 5: Check "TECHNICAL ROUTING"                                   │
│          → No media attached → Don't delegate to specialists yet     │
│          → Research needed → Will delegate to research_team later    │
│          → But FIRST: Must ask clarifying questions                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  CIRKELLINE DECIDES TO RESPOND                       │
│                    (Based on instructions)                           │
│                                                                       │
│  Decision: Don't delegate yet - need context!                        │
│                                                                       │
│  Reasoning (internal):                                               │
│  • Instructions say "ASK CLARIFYING QUESTIONS FIRST (3-5)"           │
│  • User said "help me plan a trip to Japan"                          │
│  • Need to know: dates, from where, alone/with others, budget        │
│  • Must be warm and conversational                                   │
│  • Don't mention delegation or teams                                 │
│                                                                       │
│  Cirkelline generates response:                                      │
│  "I'd love to help you plan your trip to Japan! Let me ask a few     │
│   questions so I can give you the best recommendations:              │
│                                                                       │
│   • When are you planning to go?                                     │
│   • Where are you traveling from?                                    │
│   • Will you be going alone or with others?                          │
│   • What's your budget range?                                        │
│   • What interests you most - culture, nature, food, or adventure?"  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    RESPONSE SENT TO USER                             │
│                                                                       │
│  Stream Events (SSE format):                                         │
│  • event: TeamRunStarted                                             │
│  • event: ModelResponse (chunks of text)                             │
│  • event: TeamRunCompleted                                           │
│                                                                       │
│  User sees questions appear in chat                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│               AGNO FRAMEWORK SAVES TO DATABASE                       │
│                  (Happens automatically)                             │
│                                                                       │
│  1️⃣ Save to ai.agno_runs:                                           │
│     • run_id, session_id, user_id                                    │
│     • user_message: "Help me plan a trip to Japan"                   │
│     • assistant_message: "I'd love to help... [questions]"           │
│     • created_at: timestamp                                          │
│                                                                       │
│  2️⃣ Extract memories (if any new facts mentioned):                  │
│     • None this turn - just asking questions                         │
│                                                                       │
│  3️⃣ Update session metadata:                                        │
│     • Increment message_count                                        │
│     • Update last_interaction_at                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Step-by-Step Breakdown

### Phase 1: User Message → Backend

```
USER ACTION                  TECHNICAL DETAILS
───────────────────────────────────────────────────────────────────────
User types message     →     Frontend sends POST request
"Plan trip to Japan"         {
                               message: "Plan trip to Japan",
                               stream: true,
                               session_id: "uuid" or null
                             }

                      →     Headers include:
                               Authorization: Bearer <JWT_TOKEN>

                      →     Backend endpoint:
                               POST /teams/cirkelline/runs
```

### Phase 2: Authentication & Context Loading

```
MIDDLEWARE LAYER            WHAT HAPPENS
───────────────────────────────────────────────────────────────────────
JWT Middleware       →     Decodes JWT token
                           Extracts:
                           • user_id: "6f174494-1055-474c-8d6f-73afb6610745"
                           • user_name: "Ivo" (if admin)
                           • user_role: "CEO & Creator" (if admin)
                           • user_type: "Admin" (or "Regular", "Anonymous")

                    →     Sets request.state.dependencies = {
                             user_name: "Ivo",
                             user_role: "CEO & Creator",
                             user_type: "Admin"
                           }

Knowledge Filter     →     Sets knowledge_filters = {
                             user_id: "6f174494-1055-474c-8d6f-73afb6610745"
                           }

                           This ensures user only sees their own docs
                           in knowledge base searches
```

### Phase 3: AGNO Framework Automatic Context Loading

**This is the most important part** - AGNO does this BEFORE Cirkelline even thinks:

```
AGNO OPERATION              SQL QUERY / ACTION
───────────────────────────────────────────────────────────────────────
1. LOAD USER MEMORIES

Query:                      SELECT memory, created_at
                            FROM ai.agno_user_memories
                            WHERE user_id = '6f174494...'
                            ORDER BY created_at DESC
                            LIMIT 50

Result adds to context:     "User memories:
                            • User's name is Ivo
                            • User is CEO and co-founder
                            • User likes efficient solutions
                            • User previously mentioned budget concerns
                            • ..."

───────────────────────────────────────────────────────────────────────
2. LOAD CURRENT SESSION HISTORY

Configuration:              num_history_runs = 10
                           (loads last 10 messages from THIS session)

Query:                      SELECT input, output, created_at
                            FROM ai.agno_runs
                            WHERE session_id = 'current-session-uuid'
                              AND user_id = '6f174494...'
                            ORDER BY created_at DESC
                            LIMIT 10

Result adds to context:     [Previous 10 messages in this conversation]

                            User: "Hello"
                            Cirkelline: "Hi Ivo! How can I help?"
                            User: "Plan trip to Japan"
                            ...

───────────────────────────────────────────────────────────────────────
3. SEARCH PAST SESSIONS (Vector Search)

Configuration:              search_session_history = True
                           num_history_sessions = 5
                           (finds 5 most RELEVANT past sessions)

Query:                      Vector search in ai.agno_sessions_summaries
                            Search for: "Plan trip to Japan"
                            Filter: user_id = '6f174494...'
                            Limit: 5

Result adds to context:     "Relevant past sessions:
                            • 2 months ago: Helped plan Europe trip
                            • 3 weeks ago: Discussed travel insurance
                            • 1 month ago: Research on best time to visit Asia
                            • ..."

───────────────────────────────────────────────────────────────────────
4. INJECT DEPENDENCIES

What happens:               AGNO injects dependencies into context:

                            {user_type} → "Admin"
                            {user_name} → "Ivo"
                            {user_role} → "CEO & Creator"

                            These are available in instructions but
                            NOT visible in message content (fixed v1.1.12)

───────────────────────────────────────────────────────────────────────
5. PREPARE TOOLS

Knowledge Base Tool:        search_knowledge_base(
                              query: str,
                              filters: {"user_id": "6f174494..."}
                            )

                            Only returns user's private documents

Delegation Tools:           delegate_to_audio_specialist()
                           delegate_to_video_specialist()
                           delegate_to_image_specialist()
                           delegate_to_document_specialist()
                           delegate_to_research_team()
                           delegate_to_law_team()

Reasoning Tool:            think(reasoning: str)
                           For chain-of-thought reasoning
```

### Phase 4: Cirkelline's Decision Making Process

Now Cirkelline has **ALL this context** loaded. Here's how she processes:

```
CIRKELLINE'S INTERNAL THOUGHT PROCESS
───────────────────────────────────────────────────────────────────────
Step 1: Parse Input
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input: "Help me plan a trip to Japan"

Check memories:
• User is Ivo (admin, CEO)
• Previously helped with Europe trip
• User prefers detailed planning

Check current session history:
• This is a new request (no context from earlier in this session)

Check past sessions:
• Found relevant session about travel

───────────────────────────────────────────────────────────────────────
Step 2: Read Instructions (in order)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. KNOWLEDGE BASE SEARCH RULES (lines 546-553)
   ✗ User didn't say "my notes" or "my documents"
   → Don't trigger knowledge search

2. CURRENT USER PROFILE (lines 555-559)
   ✓ User Type: Admin
   → Internally recognize this is Ivo, creator
   → But communicate the SAME warm way

3. COMMUNICATION STYLE (lines 571-599)
   ✓ "Always warm, thoughtful, and conversational"
   ✓ "Always ask clarifying questions before acting (3-5)"
   ✓ "Always gather context first, then help"
   → MUST ask questions first!

4. CRITICAL: GATHER CONTEXT BEFORE ACTING (lines 601-634)
   ✓ User requested "help with research, planning"
   → See "Trip Planning" examples:
      • When are you planning to go?
      • Where are you traveling from?
      • Are you going alone or with others?
      • What's your budget range?
      • What interests you most?
   → MUST ask these BEFORE delegating

5. TECHNICAL ROUTING (lines 661-672)
   ✓ No media attached
   ✓ Will need "Web research → Research Team" later
   → But NOT YET - must ask questions first!

───────────────────────────────────────────────────────────────────────
Step 3: Make Decision
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Decision:
→ Do NOT delegate to research_team yet
→ Do NOT provide immediate detailed answer
→ ASK clarifying questions first (3-5 questions)
→ Be warm and conversational
→ Reference past Europe trip (from memories)

Reasoning:
• Instructions say "ASK CLARIFYING QUESTIONS FIRST (3-5 questions)"
• Instructions say "Don't delegate to teams until you understand what they really need"
• Instructions provide EXACT examples for "Trip Planning"
• Must follow "CRITICAL - NO EXCEPTIONS" rules

───────────────────────────────────────────────────────────────────────
Step 4: Generate Response
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Output:
"I'd love to help you plan your trip to Japan! I remember we had a
great time planning your Europe trip a couple months ago.

Let me ask a few questions so I can give you the best recommendations:

• When are you planning to go?
• Where are you traveling from?
• Will you be going alone or with others?
• What's your budget range?
• What interests you most? (nature, culture, food, adventure)"

Note:
• Referenced past Europe trip (from past sessions search)
• Used warm, conversational tone
• Asked exactly 5 questions (as instructed)
• Followed "Trip Planning" example structure
• Did NOT delegate yet
• Did NOT mention "you are an admin"
```

### Phase 5: User Responds → Cirkelline Delegates

```
USER RESPONDS WITH CONTEXT
───────────────────────────────────────────────────────────────────────
User: "Next spring (March-April), from Copenhagen, going with my wife,
       budget around $5000, interested in culture and food mostly"

───────────────────────────────────────────────────────────────────────
CIRKELLINE'S SECOND TURN
───────────────────────────────────────────────────────────────────────

Step 1: Parse Response
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Now has full context:
• When: March-April (spring)
• From: Copenhagen
• Who: Couple (Ivo + wife)
• Budget: $5000
• Interests: Culture + food

───────────────────────────────────────────────────────────────────────
Step 2: Read Instructions Again
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Check "CRITICAL: GATHER CONTEXT BEFORE ACTING":
✓ "ONLY AFTER GATHERING CONTEXT:"
  → "Delegate to your specialist teams with the full context"
  → "Give them specific, targeted instructions based on what you learned"

Check "TECHNICAL ROUTING":
✓ "Web research → Research Team"

───────────────────────────────────────────────────────────────────────
Step 3: Delegate to Research Team
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Action:
delegate_to_research_team(
  task: "Research best cultural experiences and food destinations in
         Japan for a couple visiting in March-April from Copenhagen,
         with a $5000 budget. Focus on:
         • Best cities for culture and cuisine
         • Cherry blossom season timing
         • Food experiences (sushi, ramen, kaiseki)
         • Cultural sites (temples, gardens, traditional areas)
         • Budget-friendly accommodation
         • Flights from Copenhagen"
)

───────────────────────────────────────────────────────────────────────
RESEARCH TEAM EXECUTES (Internal Process)
───────────────────────────────────────────────────────────────────────

Research Team Orchestrator:
→ Reads task
→ Delegates to Web Researcher

Web Researcher:
→ Uses DuckDuckGo to search:
   • "Japan travel March April cherry blossoms"
   • "Best food cities Japan Tokyo Osaka"
   • "Japan cultural experiences couples"
   • "Copenhagen to Tokyo flights"
→ Gathers findings with URLs

Research Team Orchestrator:
→ Receives findings from Web Researcher
→ Delegates to Research Analyst

Research Analyst:
→ Synthesizes findings into organized report
→ Creates sections: Overview, Cities, Food, Culture, Logistics, Budget

Research Team:
→ Returns complete report to Cirkelline

───────────────────────────────────────────────────────────────────────
Step 4: Cirkelline Receives Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cirkelline gets structured report with:
• Best cities: Tokyo, Kyoto, Osaka
• Cherry blossom timing: Late March - early April
• Food recommendations: Tsukiji Market, Dotonbori, kaiseki in Kyoto
• Cultural sites: Senso-ji, Fushimi Inari, tea ceremonies
• Flight info: SAS direct Copenhagen → Tokyo ~$800/person
• Accommodation: Mid-range hotels ~$100-150/night
• Source URLs for all info

───────────────────────────────────────────────────────────────────────
Step 5: Cirkelline Rewrites in Her Voice
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Check "HOW TO RESPOND" (lines 649-658):
✓ "REWRITE everything in your own casual, conversational voice"
✓ "Explain like you're talking to a friend over coffee"
✓ "NO bullet points or formal structure in your final response"
✓ "Make it feel natural and personalized"

Output:
"Perfect timing for Japan! March-April is absolutely magical – you'll
catch the cherry blossoms in full bloom, which is just breathtaking.

For culture and food, I'd suggest splitting your time between Tokyo,
Kyoto, and Osaka. Tokyo is incredible for its mix of traditional and
modern – you have to visit Tsukiji fish market early morning for the
freshest sushi you'll ever taste. Kyoto is where you'll find those
stunning temples and traditional tea ceremonies. And Osaka? That's
your food paradise – Dotonbori street is where all the best street
food is.

With your budget, you could easily do 10-12 days. Flights from
Copenhagen are around $800 per person with SAS, and mid-range hotels
run about $100-150 a night. That leaves plenty for amazing meals and
experiences.

Want me to put together a more detailed day-by-day itinerary? Or would
you like specific restaurant recommendations for any of these cities?"

Note:
• Completely rewritten in conversational tone
• No bullet points (as instructed)
• Feels natural and personal
• References their specific interests
• Asks follow-up question
• Does NOT mention "I delegated to research team"
• Acts like SHE did all the research herself
```

---

## AGNO Framework Capabilities

These are **automatic features** provided by AGNO when you configure Cirkelline:

```python
cirkelline = Team(
    # ... members, model, tools ...

    # MEMORY FEATURES
    enable_user_memories=True,           # ← Stores facts about users
    enable_session_summaries=True,       # ← Creates summaries to prevent context overflow

    # HISTORY FEATURES
    add_history_to_context=True,         # ← Loads past messages
    num_history_runs=10,                 # ← Last 10 messages from CURRENT session
    search_session_history=True,         # ← Vector search past sessions
    num_history_sessions=5,              # ← 5 most relevant PAST sessions

    # KNOWLEDGE FEATURES
    knowledge=knowledge,                 # ← Knowledge base instance
    search_knowledge=True,               # ← Enables search_knowledge_base tool

    # DATABASE
    db=db,                               # ← PostgreSQL connection (for memories, history)
)
```

### What Each Feature Does:

#### 1. User Memories (`enable_user_memories=True`)

```
AUTOMATIC BEHAVIOR
───────────────────────────────────────────────────────────────────────
During conversation:
• AGNO extracts facts: "User's name is Ivo", "User is CEO"
• Stores in ai.agno_user_memories table
• Automatically loads on next conversation

Example:
Session 1:
User: "My name is Ivo and I run a SaaS company"
→ AGNO stores: "User's name is Ivo", "User runs SaaS company"

Session 2 (days later):
User: "Hello"
→ AGNO loads: "User's name is Ivo", "User runs SaaS company"
→ Cirkelline: "Hi Ivo! How's the SaaS going?"
```

#### 2. Session Summaries (`enable_session_summaries=True`)

```
AUTOMATIC BEHAVIOR
───────────────────────────────────────────────────────────────────────
Problem: Long conversations exceed context limits

Solution: AGNO creates summaries

How it works:
• After N messages, AGNO summarizes conversation
• Summary stored in ai.agno_sessions_summaries
• Next message gets: [Summary] + [Recent messages]
• Prevents context overflow

Example:
Messages 1-20: Full context
Messages 21+: [Summary of 1-20] + [Messages 11-21]

This is why Cirkelline can have LONG conversations!
```

#### 3. Current Session History (`num_history_runs=10`)

```
AUTOMATIC BEHAVIOR
───────────────────────────────────────────────────────────────────────
Loads last 10 messages from CURRENT session

Example session:
User: "Hello"                          ← Message 1
Cirkelline: "Hi! How can I help?"      ← Message 2
User: "Plan trip to Japan"             ← Message 3
Cirkelline: "Great! Let me ask..."     ← Message 4
User: "March-April, from Copenhagen"   ← Message 5
Cirkelline: "Perfect timing..."        ← Message 6

When processing message 7:
→ AGNO loads messages 1-6 automatically
→ Cirkelline has full conversation context
```

#### 4. Past Sessions Search (`search_session_history=True`)

```
AUTOMATIC BEHAVIOR
───────────────────────────────────────────────────────────────────────
Uses VECTOR SEARCH to find relevant past conversations

How it works:
• Current message: "Plan trip to Japan"
• AGNO searches ai.agno_sessions_summaries (vector embeddings)
• Finds 5 most semantically similar past sessions
• Adds to context: "You previously discussed..."

Example:
Current: "Plan trip to Japan"

Finds:
• Session from 2 months ago: "Europe trip planning"
• Session from 3 weeks ago: "Travel insurance"
• Session from 1 month ago: "Best time to visit Asia"

Result:
Cirkelline: "I remember we planned your Europe trip!"
          (from past session search)
```

#### 5. Knowledge Base (`search_knowledge=True`)

```
AUTOMATIC BEHAVIOR
───────────────────────────────────────────────────────────────────────
Gives Cirkelline a tool: search_knowledge_base()

How it works:
• User: "What's in my notes about X?"
• Cirkelline sees instruction: "IMMEDIATELY search knowledge base"
• Calls: search_knowledge_base(query="X", filters={"user_id": "..."})
• Returns: User's private documents (filtered by user_id)

User isolation:
• knowledge_filters = {"user_id": "user-uuid"}
• Passed to cirkelline.arun()
• Every knowledge search automatically filtered
• Users NEVER see others' documents
```

---

## Knowledge Base Flow

```
USER UPLOADS DOCUMENT
───────────────────────────────────────────────────────────────────────
Frontend:
• User drags-and-drops "Travel Budget 2025.pdf"
• POST /api/knowledge/upload with file + JWT

Backend:
• Extracts user_id from JWT
• Saves file temporarily: /tmp/cirkelline_uploads/xxx.pdf
• Creates metadata:
  {
    "user_id": "6f174494...",
    "user_type": "Admin",
    "access_level": "private",
    "uploaded_by": "6f174494...",
    "uploaded_at": "2025-10-12T15:30:00",
    "uploaded_via": "frontend_chat"
  }
• Calls knowledge.add_content_async(file, metadata)

AGNO Knowledge System:
• Reads PDF content
• Chunks into passages (~500 words each)
• Generates embeddings using Gemini
• Stores in ai.agno_knowledge_contents (text + metadata)
• Stores embeddings in ai.cirkelline_knowledge_vectors

───────────────────────────────────────────────────────────────────────
USER ASKS ABOUT DOCUMENT
───────────────────────────────────────────────────────────────────────
User: "What's in my budget document?"

Cirkelline sees instruction:
"When user asks about 'my notes', 'my documents', 'what I uploaded', 'my files':
 • IMMEDIATELY search knowledge base using search_knowledge_base tool"

Cirkelline calls:
search_knowledge_base(
  query="budget document travel 2025",
  filters={"user_id": "6f174494..."}  ← Automatic user isolation!
)

AGNO executes:
• Generates embedding for query
• Vector search in ai.cirkelline_knowledge_vectors
• Filters: WHERE metadata->>'user_id' = '6f174494...'
• Returns: Top 5 relevant passages from user's documents ONLY

Cirkelline receives:
[
  "Passage 1: Budget breakdown - Flights: $1600...",
  "Passage 2: Accommodation costs: $1200 for 10 nights...",
  "Passage 3: Food budget: $800 for 10 days..."
]

Cirkelline responds:
"Looking at your Travel Budget 2025 document, I see you've allocated
$1600 for flights, $1200 for accommodation, and $800 for food. That's
a total of $3600, leaving you with $1400 for activities and experiences.
That seems pretty solid for a 10-day trip!"
```

---

## Team Delegation Flow

```
WHEN CIRKELLINE DELEGATES
───────────────────────────────────────────────────────────────────────
Example: User asks for web research

Cirkelline: "I need to search for current information"
Action: delegate_to_research_team("Find X, Y, Z")

───────────────────────────────────────────────────────────────────────
RESEARCH TEAM RECEIVES TASK
───────────────────────────────────────────────────────────────────────
research_team = Team(
  name="Research Team",
  members=[web_researcher, research_analyst],
  instructions=["You coordinate web research by delegating..."]
)

Research Team Orchestrator thinks:
• Received task: "Find X, Y, Z"
• Instructions say: "1. Delegate search task to Web Researcher"
• Action: delegate_to_web_researcher("Search for X, Y, Z")

───────────────────────────────────────────────────────────────────────
WEB RESEARCHER EXECUTES
───────────────────────────────────────────────────────────────────────
web_researcher = Agent(
  name="Web Researcher",
  tools=[DuckDuckGoTools(), ExaTools(), TavilyTools()],
  instructions=["Try DuckDuckGo first, then Gemini search..."]
)

Web Researcher thinks:
• Task: "Search for X, Y, Z"
• Instructions say: "Try DuckDuckGo first"
• Action: duckduckgo_search("X")
• Gets results
• Action: duckduckgo_search("Y")
• Gets results
• Action: duckduckgo_search("Z")
• Gets results
• Returns: [All findings with URLs]

───────────────────────────────────────────────────────────────────────
RESEARCH TEAM ORCHESTRATOR CONTINUES
───────────────────────────────────────────────────────────────────────
Research Team receives Web Researcher findings

Research Team thinks:
• Instructions say: "2. Have Research Analyst synthesize findings"
• Action: delegate_to_research_analyst("Synthesize these findings: ...")

───────────────────────────────────────────────────────────────────────
RESEARCH ANALYST EXECUTES
───────────────────────────────────────────────────────────────────────
research_analyst = Agent(
  name="Research Analyst",
  instructions=["Synthesize findings into clear insights..."]
)

Research Analyst thinks:
• Received raw findings
• Instructions say: "Create cohesive analysis"
• Creates structured report:
  ## Overview
  ...
  ## Key Findings
  ...
  ## Conclusions
  ...
• Returns: [Synthesized report]

───────────────────────────────────────────────────────────────────────
BACK TO CIRKELLINE
───────────────────────────────────────────────────────────────────────
Cirkelline receives Research Team output:
• Structured report with findings
• Source URLs included

Cirkelline's instructions say:
"When specialists provide you with reports:
 • REWRITE everything in your own casual, conversational voice
 • Explain like you're talking to a friend over coffee
 • NO bullet points or formal structure in your final response
 • Act like YOU did all the work yourself"

Cirkelline rewrites:
"So I looked into this, and here's what I found...
[Casual, conversational explanation]
...
What do you think? Want me to dig deeper into any of this?"

User sees:
• Natural, warm response
• NO mention of "research team" or "web researcher"
• Feels like Cirkelline did everything herself
```

---

## Configuration Analysis

### Current Cirkelline Settings:

```python
cirkelline = Team(
    model=Gemini(id="gemini-2.5-flash"),    # ← Fast, efficient model

    # MEMORY
    enable_user_memories=True,               # ✅ Remembers user facts
    enable_session_summaries=True,           # ✅ Prevents context overflow

    # HISTORY
    add_history_to_context=True,             # ✅ Loads conversation history
    num_history_runs=10,                     # ✅ Last 10 messages (current session)
    search_session_history=True,             # ✅ Searches past sessions
    num_history_sessions=5,                  # ✅ 5 most relevant past sessions

    # KNOWLEDGE
    knowledge=knowledge,                     # ✅ Private knowledge base
    search_knowledge=True,                   # ✅ Can search user's docs

    # OUTPUT
    markdown=True,                           # ✅ Rich formatting
    show_members_responses=False,            # ✅ Hides internal delegation

    # DATABASE
    db=db,                                   # ✅ PostgreSQL for persistence
)
```

### What This Means:

| Feature | Status | Impact on User Experience |
|---------|--------|---------------------------|
| **User Memories** | ✅ Enabled | Cirkelline remembers facts across sessions |
| **Session Summaries** | ✅ Enabled | Can have very long conversations |
| **10 message history** | ✅ Enabled | Always knows recent context |
| **5 past session search** | ✅ Enabled | References past conversations naturally |
| **Private knowledge** | ✅ Enabled | Can search user's uploaded documents |
| **Hidden delegation** | ✅ Enabled | Seamless experience (doesn't mention teams) |

---

## Optimization Opportunities

Based on this analysis, here are ways to improve Cirkelline:

### 1. **Fine-tune History Configuration**

**Current:**
```python
num_history_runs=10          # Last 10 messages from current session
num_history_sessions=5       # 5 most relevant past sessions
```

**Consider:**
- Increase to `num_history_runs=15` for longer context in current session
- Adjust `num_history_sessions=3` if past sessions aren't always relevant
- **Test impact on response time and quality**

### 2. **Memory Extraction Control**

**Current:** AGNO automatically extracts memories

**Optimization:** Add explicit memory instructions:

```python
instructions=[
    # ... existing instructions ...

    "═══════════════════════════════════════",
    "MEMORY MANAGEMENT",
    "═══════════════════════════════════════",
    "",
    "What to remember:",
    "• User's name, role, company",
    "• Personal preferences (communication style, interests)",
    "• Important facts (budget, timeline, constraints)",
    "• Recurring needs or patterns",
    "",
    "What NOT to remember:",
    "• Temporary information (one-time requests)",
    "• Session-specific context (already in history)",
    "• Sensitive information (unless user explicitly asks)",
]
```

### 3. **Improve Question-Asking Strategy**

**Current:** Generic "ask 3-5 questions"

**Better:** Tiered approach:

```python
"CONTEXT GATHERING STRATEGY",
"",
"Level 1 - Quick tasks (1-2 questions):",
"• 'What's the capital of France?' → Answer directly",
"• 'Explain X' → Answer directly",
"",
"Level 2 - Medium tasks (2-3 questions):",
"• Research topics → Ask: depth needed, specific angle",
"• Analysis requests → Ask: what aspects to focus on",
"",
"Level 3 - Complex planning (3-5 questions):",
"• Trip planning → Ask: dates, budget, preferences, companions",
"• Project planning → Ask: timeline, constraints, goals, team size",
"",
"Level 4 - Ongoing collaboration (5+ questions):",
"• Building something → Deep dive into requirements",
```

### 4. **Knowledge Base Triggers**

**Current:** Only triggers on specific phrases

**Better:** More intelligent detection:

```python
"KNOWLEDGE BASE TRIGGERS",
"",
"Immediately search when user asks about:",
"• Direct: 'my notes', 'my documents', 'what I uploaded'",
"• Implicit: 'what did I tell you about X', 'check my file on X'",
"• Reference: 'look at my budget', 'in my notes I mentioned'",
"",
"Don't search when:",
"• General knowledge questions",
"• Asking you to create NEW notes",
```

### 5. **Add Proactive Features**

**Current:** Reactive only

**Add proactive capabilities:**

```python
"PROACTIVE ASSISTANCE",
"",
"When you notice patterns:",
"• User frequently asks about similar topics → Suggest creating a template",
"• Recurring questions → Offer to save information for quick access",
"• Multiple sessions on same project → Offer to create summary",
"",
"Examples:",
"• 'I notice we've discussed travel planning 3 times. Want me to create",
"   a travel checklist template you can reuse?'",
"• 'You've asked about budget several times. Should I save these",
"   numbers for quick reference?'",
```

### 6. **Model Selection Strategy**

**Current:** Always uses `gemini-2.5-flash`

**Consider:** Dynamic model selection:

```python
# For simple questions: gemini-2.5-flash (fast, cheap)
# For complex analysis: gemini-2.5-pro (better reasoning)
# For very long documents: gemini-2.5-pro (larger context)
```

**Implementation:**
```python
"MODEL SELECTION (Internal)",
"",
"Use current model (Flash) for:",
"• Conversation and questions",
"• Simple research and summaries",
"• Quick analysis",
"",
"Consider delegating to Pro model for:",
"• Very long document analysis (>50 pages)",
"• Complex reasoning tasks",
"• Multi-step planning with many constraints",
```

### 7. **Session Summary Timing**

**Current:** AGNO decides when to create summaries

**Consider:** Manual control:

```python
enable_session_summaries=True,
summary_frequency=20,  # Summarize every 20 messages
```

### 8. **Enhanced Delegation Instructions**

**Current:** "Delegate to teams, rewrite response"

**Better:** More specific guidance:

```python
"DELEGATION GUIDELINES",
"",
"When to delegate to Research Team:",
"• User asks about current events, latest information",
"• Need to verify facts, find sources",
"• Comparison shopping, product research",
"",
"When to delegate to Law Team:",
"• Legal questions, case law",
"• Contract review, policy interpretation",
"",
"When to handle yourself:",
"• General knowledge (pre-2025)",
"• Personal advice, conversation",
"• Using user's uploaded documents",
"",
"After delegation:",
"• Extract the KEY insights (don't repeat everything)",
"• Rewrite in YOUR warm, conversational style",
"• Add personal touch based on user memories",
"• Ask thoughtful follow-up questions",
```

---

## Summary: The Complete Flow

```
USER SENDS MESSAGE
        ↓
┌───────────────────────────────────────────────────────────────┐
│ BACKEND RECEIVES                                              │
│ • Extracts JWT (user_id, user_name, user_role, user_type)    │
│ • Sets knowledge filters (user_id isolation)                  │
│ • Generates/uses session_id                                   │
└────────────────────────────┬──────────────────────────────────┘
                             ↓
┌───────────────────────────────────────────────────────────────┐
│ AGNO FRAMEWORK LOADS CONTEXT (Automatic)                      │
│ 1. User memories from database                                │
│ 2. Last 10 messages from current session                      │
│ 3. 5 most relevant past sessions (vector search)             │
│ 4. Injects user profile (dependencies)                        │
│ 5. Prepares knowledge base with user_id filter               │
└────────────────────────────┬──────────────────────────────────┘
                             ↓
┌───────────────────────────────────────────────────────────────┐
│ CIRKELLINE PROCESSES                                          │
│ • Has full context loaded                                     │
│ • Reads instructions in order                                 │
│ • Follows rules (ask questions first, be warm, etc.)          │
│ • Decides: answer directly, ask questions, or delegate        │
└────────────────────────────┬──────────────────────────────────┘
                             ↓
┌───────────────────────────────────────────────────────────────┐
│ IF NEEDS HELP                                                 │
│ • Delegates to specialist teams                               │
│ • Teams execute with their own agents                         │
│ • Results returned to Cirkelline                              │
│ • Cirkelline rewrites in her voice                            │
└────────────────────────────┬──────────────────────────────────┘
                             ↓
┌───────────────────────────────────────────────────────────────┐
│ RESPONSE SENT TO USER                                         │
│ • Warm, conversational                                        │
│ • No mention of internal delegation                           │
│ • References memories naturally                               │
│ • Asks follow-up questions                                    │
└────────────────────────────┬──────────────────────────────────┘
                             ↓
┌───────────────────────────────────────────────────────────────┐
│ AGNO SAVES (Automatic)                                        │
│ • Message saved to ai.agno_runs                               │
│ • New memories extracted and stored                           │
│ • Session metadata updated                                    │
└───────────────────────────────────────────────────────────────┘
```

**Key Insights:**
1. **Context Loading is Automatic** - AGNO does this before Cirkelline thinks
2. **Instructions Drive Behavior** - Cirkelline follows them strictly
3. **Delegation is Hidden** - User never sees internal processes
4. **Memory Persists** - Facts remembered across sessions
5. **User Isolation Works** - Knowledge base filtered by user_id

---

**See Also:**
- [01-ARCHITECTURE.md](./01-ARCHITECTURE.md) - System architecture
- [05-BACKEND-REFERENCE.md](./05-BACKEND-REFERENCE.md) - Backend API
- [04-DATABASE-REFERENCE.md](./04-DATABASE-REFERENCE.md) - Database schema
