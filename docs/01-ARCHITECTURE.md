# ARCHITECTURE REFERENCE

**Last Updated:** 2025-12-02
**Current Version:** v1.2.34.6

---

## Table of Contents
- [System Overview](#system-overview)
- [Multi-Agent Architecture](#multi-agent-architecture)
- [Request Flow](#request-flow)
- [AGNO Teams Explained](#agno-teams-explained)
- [Runtime Mode Context Injection](#runtime-mode-context-injection) 🔴 NEW (v1.2.24)
- [Session Management Architecture](#session-management-architecture)
- [Memory System Architecture](#memory-system-architecture) 🔴 NEW (v1.2.34.6)
- [Knowledge Base Architecture](#knowledge-base-architecture)
- [Authentication Architecture](#authentication-architecture)
- [Singleton Pattern & State Management](#singleton-pattern--state-management)
- [Component Interactions](#component-interactions)
- [Quick Reference](#quick-reference)

---

## System Overview

Cirkelline is a **multi-agent orchestration system** built on top of AGNO (Agent Network Operating System). It provides intelligent task routing, session management, and private knowledge base access through a conversational interface.

### Core Principles

1. **Intelligent Routing**: User requests are analyzed and routed to specialist agents or teams
2. **User Isolation**: All data (sessions, memories, knowledge) is isolated by user_id
3. **Conversational Interface**: All complexity is hidden behind a friendly chat interface
4. **Orchestrated Execution**: A main orchestrator delegates to specialists and synthesizes responses

### Technology Stack

```
Frontend:
├── Next.js 14 (App Router)
├── TypeScript
├── Zustand (State Management)
├── TailwindCSS
└── Server-Sent Events (SSE)

Backend:
├── FastAPI
├── AGNO Framework (v2.1.1)
├── Google Gemini 2.5 Flash
├── PostgreSQL with pgvector
└── SQLAlchemy

Infrastructure:
├── AWS ECS Fargate
├── AWS RDS PostgreSQL
├── AWS Secrets Manager
└── Application Load Balancer
```

---

## Multi-Agent Architecture

### Agent Hierarchy

```
Cirkelline (Main Orchestrator)
│
├── Specialist Agents
│   ├── Audio Specialist
│   ├── Video Specialist
│   ├── Image Specialist
│   └── Document Specialist
│
└── Specialist Teams
    ├── Research Team
    │   ├── DuckDuckGo Researcher (news, current events)
    │   ├── Exa Researcher (semantic, conceptual)
    │   └── Tavily Researcher (comprehensive)
    │
    └── Law Team
        ├── Legal Researcher
        └── Legal Analyst
```

### Agent Types

#### 1. Cirkelline (Main Orchestrator)
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline/orchestrator/cirkelline_team.py`

**Role:** Central coordinator that routes requests and synthesizes responses

**Capabilities:**
- Analyzes user intent
- Routes to appropriate specialists
- Gathers clarifying questions before delegation
- Rewrites specialist responses in conversational tone
- Manages conversation flow

**Key Features:**
- Knowledge base search integration
- User memory storage
- Session summaries (prevents context overflow)
- Admin profile awareness
- Multimodal input handling

**Instructions Pattern:**
```python
instructions=[
    "You are Cirkelline, a warm and thoughtful personal assistant.",
    "User Type: {user_type}",
    "CRITICAL: GATHER CONTEXT BEFORE ACTING",
    "When specialists provide reports, REWRITE in conversational voice",
    "NEVER mention specialists or delegation to user"
]
```

#### 2. Specialist Agents

**Audio Specialist** (lines 251-273)
- Transcribes speech
- Identifies speakers and sounds
- Native Gemini multimodal processing

**Video Specialist** (lines 276-299)
- Describes scenes and actions
- Extracts timestamps
- Analyzes both visual and audio

**Image Specialist** (lines 302-324)
- Detailed image description
- OCR text extraction
- Logo and symbol identification

**Document Specialist** (lines 327-356)
- PDF processing (native Gemini)
- DOCX conversion tools
- Knowledge base search integration

#### 3. Specialist Teams

**Research Team** (`research_team.py`)
```
Team Leader (Coordinator + Synthesizer)
  ├─> DuckDuckGo Researcher (news, current events)
  ├─> Exa Researcher (semantic, conceptual)
  └─> Tavily Researcher (comprehensive)
```

**Specialized Researchers:**
- DuckDuckGo Researcher: News, current events, quick facts
- Exa Researcher: Semantic/conceptual search, research topics
- Tavily Researcher: Comprehensive deep search, analysis

**Process (v1.2.34):**
1. Team leader analyzes request using think()
2. Leader decides which researcher(s) to use
3. Delegates to appropriate specialist(s)
4. Leader synthesizes findings directly (no separate analyst)
5. Returns unified response

**Law Team** (lines 493-525)
```
Coordinator
  ├─> Legal Researcher (finds sources)
  └─> Legal Analyst (provides analysis)
```

**Specialization:**
- Legal research and case law
- Statute analysis
- Professional legal documentation

---

## Request Flow

### Complete Request Journey

```
User Input
    ↓
Frontend (React/Next.js)
    ↓ [POST /teams/cirkelline/runs]
    ↓ [JWT Token in Authorization header]
    ↓
Backend FastAPI
    ↓
JWT Middleware (extracts user_id, dependencies)
    ↓
Custom Endpoint (/teams/cirkelline/runs)
    ↓ [Builds knowledge_filters]
    ↓ [Passes dependencies to AGNO]
    ↓
Cirkelline Orchestrator
    ↓ [Analyzes intent]
    ↓
┌────────────────┬────────────────┬────────────────┐
│                │                │                │
Image?       Document?       Research?       Legal?
│                │                │                │
Image         Document       Research         Law
Specialist    Specialist      Team            Team
│                │                │                │
└────────────────┴────────────────┴────────────────┘
                        ↓
            Specialist Response
                        ↓
        Cirkelline Synthesizes
                        ↓
            Conversational Output
                        ↓
            SSE Stream to Frontend
                        ↓
                User Sees Response
```

### Detailed Flow with Code References

#### Step 1: Frontend Initiates Request
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useAIStreamHandler.tsx` (lines 104-172)

```typescript
// User sends message
formData.append('message', input)
formData.append('stream', 'true')
formData.append('session_id', sessionId ?? '')
formData.append('user_id', getUserId())

// POST to backend
await streamResponse({
  apiUrl: RunUrl,
  headers: getAuthHeaders(), // Includes JWT
  requestBody: formData
})
```

#### Step 2: Backend Receives Request
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/custom_cirkelline.py`

```python
@app.post("/teams/cirkelline/runs")
async def cirkelline_with_filtering(
    request: Request,
    message: str = Form(...),
    stream: bool = Form(False),
    session_id: Optional[str] = Form(None),
):
    # Extract user_id from JWT middleware
    user_id = getattr(request.state, 'user_id', 'anonymous')

    # Build knowledge filters for user isolation
    knowledge_filters = {"user_id": user_id}

    # Get admin profile data from JWT
    dependencies = getattr(request.state, 'dependencies', {})

    # Generate unique session ID if needed
    if not session_id:
        actual_session_id = str(uuid.uuid4())
    else:
        actual_session_id = session_id
```

#### Step 3: AGNO Processes Request
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/custom_cirkelline.py`

```python
async for event in cirkelline.arun(
    input=message,
    stream=True,
    session_id=actual_session_id,
    user_id=user_id,
    knowledge_filters=knowledge_filters,
    dependencies=dependencies
):
```

**What AGNO Does:**
1. Loads session from database (if existing)
2. Retrieves user memories
3. Loads recent conversation history
4. Applies knowledge filters
5. Injects dependencies into agent context
6. Routes to appropriate agent/team
7. Streams events back

#### Step 4: Agent Execution

```
Cirkelline analyzes: "Can you transcribe this audio?"
    ↓
Routes to Audio Specialist
    ↓
Audio Specialist processes with Gemini multimodal
    ↓
Returns transcription
    ↓
Cirkelline rewrites in friendly tone
    ↓
Streams to user
```

#### Step 5: Frontend Processes Stream
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useAIStreamHandler.tsx` (lines 176-410)

```typescript
onChunk: (chunk: RunResponse) => {
  if (chunk.event === RunEvent.RunContent) {
    // Append content to message
    lastMessage.content += uniqueContent
  } else if (chunk.event === RunEvent.ToolCallStarted) {
    // Show tool execution
    lastMessage.tool_calls.push(chunk.tool)
  } else if (chunk.event === RunEvent.RunCompleted) {
    // Finalize message
  }
}
```

---

## AGNO Teams Explained

### What is an AGNO Team?

An AGNO Team is a **coordinator agent** that manages a group of specialist agents. The coordinator analyzes requests, delegates to members, and synthesizes their responses.

### Team Structure

```python
Team(
    name="Research Team",
    model=Gemini(id="gemini-2.5-flash"),
    members=[web_researcher, research_analyst],
    tools=[ReasoningTools()],
    instructions=[
        "You coordinate web research by delegating to specialists.",
        "1. Delegate search task to Web Researcher",
        "2. WAIT for Web Researcher's COMPLETE results",
        "3. Delegate to Research Analyst WITH the search findings",
        "4. WAIT for Research Analyst's COMPLETE synthesis",
        "5. Present ONE clear, complete answer"
    ],
    # ═══ CRITICAL AGNO v2 TEAM COORDINATION SETTINGS ═══
    share_member_interactions=True,   # ← Research Analyst sees Web Researcher's work
    show_members_responses=True,      # ← Parent team sees this team's synthesis
    store_member_responses=True,      # ← Enable proper synthesis of outputs
    # Note: mode parameter DEPRECATED in AGNO v2 (coordinate is default)
    # ═══════════════════════════════════════════════════
    db=db,
    enable_user_memories=True,
    enable_session_summaries=True,
    add_history_to_context=True,
    num_history_runs=5,
    search_session_history=True,
    num_history_sessions=3,
    markdown=True
)
```

**AGNO v2 Coordination Parameters:**
- `share_member_interactions=True` - Members see each other's work during the same run (CRITICAL for nested teams)
- `show_members_responses=True` - Parent team sees this team's member responses
- `store_member_responses=True` - Enables proper synthesis and context retention

### Why Teams?

1. **Separation of Concerns**: Each agent has one focused job
2. **Better Results**: Specialists are experts in their domain
3. **Transparent Workflow**: Coordinator explicitly delegates
4. **User Experience**: User sees ONE response, not multiple

### Team Execution Flow

```
User: "Research the best laptops for coding in 2025"
    ↓
Cirkelline routes to Research Team
    ↓
Research Team Coordinator:
  ├─> "Web Researcher, search for laptop reviews"
  │   └─> Web Researcher: [searches multiple sources]
  └─> "Research Analyst, synthesize these findings"
      └─> Research Analyst: [creates cohesive analysis]
    ↓
Research Team Coordinator synthesizes final response
    ↓
Returns to Cirkelline
    ↓
Cirkelline rewrites in conversational tone
    ↓
User sees: "Here's what I found about coding laptops..."
```

### Key Configuration

**show_members_responses=False**
- Hides internal delegation messages
- User only sees final synthesized response
- Keeps interface clean

**enable_session_summaries=True**
- Prevents context overflow
- Summarizes long conversations
- Maintains relevance

**num_history_runs=5**
- Loads last 5 conversation turns
- Maintains context without bloat

---

## Runtime Mode Context Injection

**Introduced:** v1.2.24
**Purpose:** Enable mode-based behavior (Deep Research Mode) while maintaining instruction serializability
**Pattern:** Static base instructions + dynamic context appended at runtime

### The Challenge

**Problem:** How to make agent behavior conditional on runtime values while keeping instructions serializable?

**Requirements:**
1. AGNO `/teams` endpoint requires serializable instructions (JSON-compatible)
2. Agent behavior must change based on `deep_research` flag in session_state
3. No dynamic instruction generation (breaks serializability)
4. No callable functions in instructions (not JSON-serializable)
5. Clear, unambiguous instructions for the agent

**Previous Approaches That Failed:**
- ❌ Dynamic instruction generation via lambda functions → TypeError in `/teams` endpoint
- ❌ Conditional logic in string templates → Agent couldn't evaluate at runtime
- ❌ Session state checks in instructions → Agent had no visibility into runtime values

### The Solution: Runtime Mode Context Injection

**Architecture Pattern:**

```python
# 1. Define static base instructions (always the same)
cirkelline = Team(
    name="Cirkelline",
    instructions=[
        "You are Cirkelline, a warm and thoughtful personal assistant.",
        "You help users with various tasks through intelligent routing.",
        # ... all other base instructions
    ],
    # ... other configuration
)

# 2. Before each request: Backup original instructions
original_instructions = cirkelline.instructions.copy()

# 3. Dynamically append mode-specific context
mode_context = ["", "🔴 CURRENT MODE FOR THIS REQUEST:"]

if deep_research:
    mode_context.extend([
        "✅ DEEP RESEARCH MODE IS ACTIVE",
        "• For research questions: DELEGATE to Research Team",
        "• For legal questions: DELEGATE to Law Team",
        "• Use delegate_task_to_member() for comprehensive analysis"
    ])
else:
    mode_context.extend([
        "✅ QUICK SEARCH MODE IS ACTIVE (Default)",
        "• For research questions: Use exa_search() or tavily_search() DIRECTLY",
        "• DO NOT delegate to Research Team or Law Team",
        "• Answer directly with search tool results"
    ])

# Apply mode-specific context for this run only
runtime_instructions = cirkelline.instructions + mode_context
cirkelline.instructions = runtime_instructions

# 4. Run the agent
cirkelline.arun(...)

# 5. After request: Restore original instructions
cirkelline.instructions = original_instructions
```

### Key Benefits

**1. Serializability Maintained:**
- Base instructions are static lists (JSON-serializable)
- `/teams` endpoint works perfectly
- No lambda functions or dynamic generation

**2. Explicit Mode Communication:**
- Agent receives clear, unambiguous instructions
- "🔴 CURRENT MODE FOR THIS REQUEST" indicator is unmissable
- No need for agent to "check session_state" (which it couldn't do anyway)

**3. No Leakage Between Requests:**
- Instructions backed up before modification
- Restored after each request
- Each request gets fresh mode-specific context

**4. Scalable Pattern:**
- Easy to add new modes (Balanced, Auto, etc.)
- Follows same pattern as tool restoration
- Well-tested and proven architecture

### Implementation Details

**File:** `my_os.py`

**Lines 3448-3449: Instruction Backup**
```python
# v1.2.24: Backup original instructions before appending mode context
original_instructions = cirkelline.instructions.copy() if cirkelline.instructions else []
```

**Lines 3459-3485: Mode Context Injection**
```python
# v1.2.24: Dynamically append current mode to instructions
mode_context = ["", "🔴 CURRENT MODE FOR THIS REQUEST:"]

if deep_research:
    mode_context.extend([
        "✅ DEEP RESEARCH MODE IS ACTIVE",
        "• For research questions: DELEGATE to Research Team",
        "• For legal questions: DELEGATE to Law Team",
        "• Use delegate_task_to_member() for comprehensive analysis"
    ])
else:
    mode_context.extend([
        "✅ QUICK SEARCH MODE IS ACTIVE (Default)",
        "• For research questions: Use exa_search() or tavily_search() DIRECTLY",
        "• DO NOT delegate to Research Team or Law Team",
        "• Answer directly with search tool results"
    ])

# Append mode context to instructions for this run only
runtime_instructions = cirkelline.instructions + mode_context
cirkelline.instructions = runtime_instructions
```

**Lines 3706-3709: Restoration (Streaming Path)**
```python
finally:
    # CRITICAL: Restore original Cirkelline configuration
    cirkelline.tools = original_tools
    cirkelline.instructions = original_instructions
    logger.info("🧹 Restored original Cirkelline configuration after stream")
```

**Lines 3736-3739: Restoration (Non-Streaming Path)**
```python
# CRITICAL: Restore original Cirkelline configuration
cirkelline.tools = original_tools
cirkelline.instructions = original_instructions
logger.info("🧹 Restored original Cirkelline configuration after non-streaming request")
```

### Request Flow with Mode Context

```
1. Frontend sends request with deep_research=true/false
        ↓
2. Backend extracts deep_research flag
        ↓
3. Passed to session_state dict
        ↓
4. Before cirkelline.arun():
   - Backup original instructions
   - Append mode-specific context based on deep_research flag
   - Apply runtime instructions
        ↓
5. Agent runs with explicit mode instructions
   "🔴 CURRENT MODE FOR THIS REQUEST: ✅ DEEP RESEARCH MODE IS ACTIVE"
        ↓
6. Agent follows mode-specific behavior
        ↓
7. After cirkelline.arun():
   - Restore original instructions
   - Mode context discarded
        ↓
8. Next request gets fresh mode context (no leakage)
```

### Why This Pattern Works

**1. Agent Visibility:**
- Agent can't "check session_state" from text instructions
- Instead, we explicitly tell the agent what mode is active
- Instructions are clear and actionable

**2. Clean Separation:**
- Base instructions never change
- Mode context is temporary and request-scoped
- No state pollution between requests

**3. Debugging Friendly:**
- Easy to log what mode was active
- Instructions visible in team definition
- Clear causality between flag and behavior

**4. Future-Proof:**
- Adding "Balanced Mode" just adds another elif branch
- Auto-mode detection could set deep_research dynamically
- Pattern scales to any number of modes

### Comparison to Alternatives

| Approach | Serializable? | Agent Visibility? | Scalable? | Result |
|----------|--------------|-------------------|-----------|--------|
| Dynamic Instructions (lambda) | ❌ No | ✅ Yes | ❌ No | TypeError in /teams |
| Session State Checks in Text | ✅ Yes | ❌ No | ⚠️ Maybe | Agent can't evaluate |
| **Runtime Context Injection** | ✅ Yes | ✅ Yes | ✅ Yes | **Works Perfectly** |

### Similar Patterns in Codebase

This pattern follows the same approach as:

**Tool Restoration Pattern (my_os.py:3440-3447):**
```python
# Backup original tools
original_tools = cirkelline.tools.copy()

# Apply session-specific tools
filtered_tools = filter_google_tools_by_user(original_tools, user_id)
cirkelline.tools = filtered_tools

# ... run agent ...

# Restore original tools
cirkelline.tools = original_tools
```

Both patterns share:
- Backup → Modify → Restore lifecycle
- Request-scoped modifications
- No state leakage
- Clean separation of concerns

### Testing and Validation

**Test Case 1: Quick Search Mode**
- deep_research=False → Agent uses tavily_search directly
- Response time: 5-10 seconds
- ✅ Works as expected

**Test Case 2: Deep Research Mode**
- deep_research=True → Agent delegates to Research Team
- Response time: 60-90 seconds
- ✅ Works as expected

**Test Case 3: Mode Persistence**
- Toggle ON in session → stays ON for subsequent messages
- New session → resets to False (default)
- ✅ Works as expected

**Test Case 4: No Leakage**
- User A: deep_research=True
- User B: deep_research=False (same time)
- Each user gets correct mode context
- ✅ No cross-contamination

### Future Enhancements

**Potential Future Modes:**

1. **Balanced Mode:**
   - Medium-depth research (30-40 seconds)
   - Uses Research Team but with fewer search iterations

2. **Auto Mode:**
   - System analyzes query complexity
   - Automatically sets deep_research based on heuristics
   - User can override if needed

3. **Custom Modes:**
   - Users define their own mode parameters
   - Saved as user preferences
   - Applied via same runtime context injection

All of these would use the same architectural pattern - just different mode_context strings.

### Related Documentation

- **Implementation Guide:** [docs/24-DEEP-RESEARCH-MODE-IMPLEMENTATION.md](./24-DEEP-RESEARCH-MODE-IMPLEMENTATION.md)
- **Feature Documentation:** [docs/08-FEATURES.md#deep-research-mode](./08-FEATURES.md#deep-research-mode)
- **API Reference:** [docs/05-BACKEND-REFERENCE.md](./05-BACKEND-REFERENCE.md)

---

## Session Management Architecture

### Session Lifecycle

```
User clicks "New Chat"
    ↓
Frontend generates NO session_id (empty string)
    ↓
Backend receives empty session_id
    ↓
Backend generates UUID: str(uuid.uuid4())
    ↓
AGNO creates new session in database
    ↓
Backend returns session_id in first event
    ↓
Frontend updates URL: ?session={uuid}
    ↓
Frontend optimistically adds to sidebar
    ↓
Subsequent messages use same session_id
```

### Session Storage

**Database Table:** `ai.agno_sessions`

```sql
CREATE TABLE ai.agno_sessions (
    session_id VARCHAR PRIMARY KEY,
    session_type VARCHAR,
    team_id VARCHAR,
    user_id VARCHAR,  -- CRITICAL for isolation
    session_data JSON,
    runs JSON,
    created_at BIGINT,
    updated_at BIGINT
);

CREATE INDEX idx_agno_sessions_user_id ON ai.agno_sessions(user_id);
```

### Session Isolation

**Backend Implementation:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/custom_cirkelline.py`

```python
# Generate unique session ID if not provided
if not session_id:
    actual_session_id = str(uuid.uuid4())
    logger.info(f"🆕 Generated NEW session ID: {actual_session_id}")
else:
    actual_session_id = session_id

# Pass user_id to AGNO for isolation
cirkelline.arun(
    session_id=actual_session_id,
    user_id=user_id  # AGNO stores this with session
)
```

**Frontend Loading:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useSessionLoader.tsx`

```typescript
// Load only user's sessions
const response = await fetch(
  `${selectedEndpoint}/teams/${teamId}/sessions`,
  { headers: getAuthHeaders() }
)
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
    "user_role": "CEO & Creator",
    "user_type": "Admin"
  },
  "runs": [
    {
      "input": "Hello!",
      "response": "Hi Ivo! How can I help?",
      "created_at": 1728567890
    }
  ],
  "created_at": 1728567890,
  "updated_at": 1728567920
}
```

---

## Memory System Architecture

**Introduced:** v1.2.34 | **Updated:** v1.2.34.6
**Purpose:** Store and retrieve user-specific information across conversations using topic-based filtering

### Overview

Cirkelline uses AGNO's memory system with intelligent topic-based retrieval. Key principle: **Memories are filtered at the SQL level - we do NOT load all memories into context**.

### Architecture

```
USER MESSAGE
    │
    ▼
CIRKELLINE ORCHESTRATOR
    │ • Extracts topic keywords from conversation
    │ • Calls search_memories(topics=[...])
    │ • Uses results for context-aware response
    │
    ▼ (after run completes)
MEMORY MANAGER (automatic)
    │ • Extracts memorable info from conversation
    │ • Creates new memories with topic tags
    │ • Stores in PostgreSQL (ai.agno_memories)
    │
    ▼
DATABASE (SQL-level filtering)
    • WHERE topics LIKE '%"family"%'
    • Returns ONLY matching memories
```

### Memory Creation (v1.2.34.6)

**MemoryManager with Aggressive Capture:**

```python
# cirkelline/orchestrator/cirkelline_team.py
memory_manager = MemoryManager(
    model=Gemini(id="gemini-2.5-flash"),
    db=db,
    additional_instructions="""
IMPORTANT: Be AGGRESSIVE about capturing memories. Extract and store:
- PERSONAL FACTS: Names, birthdays, locations, occupation
- RELATIONSHIPS: Family members, friends, pets (including names)
- PREFERENCES: Favorite things, likes/dislikes
- EVENTS & MILESTONES: Recent events, upcoming plans
- WORK/PROJECTS: Current projects, job details
- INTERESTS & HOBBIES: Activities, sports, creative pursuits

RULES:
- If user mentions pet/family/friend BY NAME → create memory
- If user shares personal fact → create memory
- If user expresses strong preference → create memory
- Do NOT require explicit "remember this"
"""
)
```

### Memory Retrieval (v1.2.34.4)

**IntelligentMemoryTool with SQL-level filtering:**

```python
# cirkelline/tools/memory_search_tool.py
def search_memories(self, topics: List[str], user_id: str, limit: int = 10):
    """
    SQL generates: WHERE topics LIKE '%"travel"%' AND topics LIKE '%"Japan"%'
    Returns ONLY memories matching those topics
    """
    memories = self.database.get_user_memories(
        user_id=user_id,
        topics=topics,  # SQL-level filtering
        limit=limit
    )
```

### Configuration

**Team configuration (cirkelline_team.py):**

| Setting | Value | Purpose |
|---------|-------|---------|
| `memory_manager` | Explicit instance | Required for Teams to create memories |
| `add_memories_to_context` | `False` | Don't load all memories - use search tool |
| `enable_user_memories` | `True` | Auto-extract memories after each run |
| `enable_agentic_memory` | `True` | Agent can update memories via tool |

### Token Efficiency

| Approach | Tokens | Issue |
|----------|--------|-------|
| Load ALL memories | ~5,000+ | Bloats context, expensive |
| Topic-based filtering | ~200-500 | Only relevant memories loaded |

### Example Flow

```
1. User: "What do you remember about my family?"
2. Cirkelline extracts: topics=["family"]
3. SQL: WHERE topics LIKE '%"family"%'
4. Returns: Only 2 family memories (not all 111)
5. Response: "I remember your sister Emma got engaged to Marcus!"
```

### Database Schema

**Table:** `ai.agno_memories`

| Column | Type | Description |
|--------|------|-------------|
| `memory_id` | VARCHAR | AGNO-generated memory ID |
| `user_id` | VARCHAR | User who owns this memory |
| `memory` | TEXT | The memory content |
| `topics` | JSONB | Topic tags (e.g., `["family", "relationships"]`) |

### Related Documentation

- **[57-MEMORY.md](./57-MEMORY.md)** - Complete memory system documentation

---

## Knowledge Base Architecture

### Components

```
Knowledge Base
├── Metadata Storage (ai.agno_knowledge)
├── Vector Storage (ai.cirkelline_knowledge_vectors)
├── Embeddings (Gemini text-embedding-004)
└── Search (Hybrid: Vector + BM25)
```

### Upload Flow

```
User uploads PDF in chat
    ↓
Frontend: POST /api/knowledge/upload
    ↓ [JWT token for user_id]
    ↓
Backend: /api/knowledge/upload endpoint
    ↓ [Extract user_id from JWT]
    ↓ [Save file to /tmp/cirkelline_uploads]
    ↓
Create metadata:
{
  "user_id": "uuid",
  "user_type": "admin",
  "access_level": "private",
  "uploaded_by": "uuid",
  "uploaded_at": "ISO-8601",
  "uploaded_via": "frontend_chat"
}
    ↓
knowledge.add_content_async(
  name=filename,
  path=temp_path,
  metadata=metadata
)
    ↓
AGNO processes document:
  ├─> Chunks text
  ├─> Generates embeddings
  ├─> Stores in vector DB with metadata
  └─> Stores metadata in knowledge table
    ↓
Returns success to frontend
```

### Knowledge Filtering

**Backend Implementation:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/custom_cirkelline.py`

```python
def get_private_knowledge_filters(user_id: str) -> Dict:
    """
    Build knowledge filters for private documents only.
    Returns only user's private documents.
    """
    return {"user_id": user_id}

# Usage in endpoint
knowledge_filters = {"user_id": user_id}

cirkelline.arun(
    knowledge_filters=knowledge_filters  # AGNO applies this
)
```

**How AGNO Filters:**
```sql
-- When searching knowledge base, AGNO adds WHERE clause:
SELECT * FROM ai.cirkelline_knowledge_vectors
WHERE metadata->>'user_id' = 'current-user-id'
  AND embedding <=> query_vector < threshold
ORDER BY embedding <=> query_vector
LIMIT 5;
```

### Vector Search

**Embedding Model:** Gemini text-embedding-004 (768 dimensions)

**Search Algorithm:** HNSW (Hierarchical Navigable Small World)

**Hybrid Search:**
1. Vector similarity search (semantic)
2. BM25 keyword search (lexical)
3. Combine and rank results

**Configuration:** `/home/eenvy/Desktop/cirkelline/my_os.py`

```python
vector_db = PgVector(
    db_url=os.getenv("DATABASE_URL"),
    table_name="cirkelline_knowledge_vectors",
    embedder=GeminiEmbedder(),
    search_type=SearchType.hybrid
)
```

---

## Authentication Architecture

### JWT Flow

```
User logs in
    ↓
POST /api/auth/login
    ↓
Backend verifies password
    ↓
Checks if admin (hardcoded emails)
    ↓
Loads admin profile from DB (if admin)
    ↓
Generates JWT with claims:
{
  "user_id": "uuid",
  "email": "email",
  "display_name": "name",
  "user_name": "Ivo",
  "user_role": "CEO & Creator",
  "user_type": "Admin",
  "is_admin": true,
  "admin_context": "...",
  "admin_preferences": "...",
  "admin_instructions": "...",
  "iat": 1728567890,
  "exp": 1729172690  // 7 days
}
    ↓
Returns token to frontend
    ↓
Frontend stores in localStorage
    ↓
All future requests include:
Authorization: Bearer {token}
```

### Middleware Chain

**File:** `/home/eenvy/Desktop/cirkelline/cirkelline/middleware/middleware.py`

```
Request comes in
    ↓
SessionsDateFilterMiddleware
  ├─> Handles date-filtered session queries
  └─> Passes through if not /sessions with date params
    ↓
SessionLoggingMiddleware
  ├─> Logs session operations (delete, rename)
  └─> Passes through if not session operation
    ↓
JWT Middleware
  ├─> Decodes JWT token
  ├─> Extracts user_id
  ├─> Extracts dependencies (user_name, user_role, user_type)
  └─> Sets request.state values
    ↓
Custom Endpoint
  ├─> Reads user_id from request.state.user_id
  ├─> Verifies authentication (rejects anon-* and empty users)
  └─> Passes to AGNO
    ↓
AGNO Agent
  ├─> Receives dependencies in instructions
  └─> Adapts behavior based on user_type
```

**Note (v1.3.4):** AnonymousUserMiddleware was removed. Accounts are now required to use Cirkelline.

### Admin Profile Injection

**Login/Signup:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/auth.py`

```python
if is_admin:
    # Load profile from database
    admin_result = session.execute(
        text("""
            SELECT name, role, personal_context,
                   preferences, custom_instructions
            FROM admin_profiles
            WHERE user_id = :user_id
        """),
        {"user_id": str(user[0])}
    )
    admin_profile = admin_result.fetchone()

    # Add to JWT claims
    jwt_payload.update({
        "user_name": admin_profile[0],
        "user_role": admin_profile[1],
        "user_type": "Admin",
        "admin_context": admin_profile[2],
        "admin_preferences": admin_profile[3],
        "admin_instructions": admin_profile[4]
    })
```

### Authentication Requirements (v1.3.4)

**Note:** As of v1.3.4, anonymous users are no longer supported. All users must create an account to use Cirkelline.

**Frontend Protection:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/app/page.tsx`

```typescript
// If no valid JWT, user sees only the login/register screen
// Nothing else is rendered - can't be bypassed via dev tools
const isAnonymous = !user || user.isAnonymous
if (isAnonymous) {
  return (
    <div className="...">
      <LoginForm /> or <RegisterForm />
    </div>
  )
}
// Only authenticated users see the full app
```

**Backend Protection:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/custom_cirkelline.py`

```python
# Rejects any request with anon-* user IDs
if user_id.startswith("anon-"):
    raise HTTPException(
        status_code=401,
        detail="Account required. Please sign up or log in."
    )
```

---

## Singleton Pattern & State Management

### The Challenge: Multi-User Shared State

**Problem:** The Cirkelline Team object is a singleton created once when the server starts and shared across ALL user requests.

**Location:** `/home/eenvy/Desktop/cirkelline/my_os.py` (line ~1056)

```python
# MODULE LEVEL - Runs ONCE when server starts
cirkelline = Team(
    members=[audio_agent, video_agent, ...],
    instructions=[...],  # Original instructions
    tools=[...],         # Original tools
    ...
)
```

### Two Types of Isolation

#### 1. Database Isolation ✅ (Already Working)

User data is isolated through SQL filtering:

```python
# Sessions
SELECT * FROM ai.agno_sessions WHERE user_id = :current_user

# Memories
SELECT * FROM ai.agno_memories WHERE user_id = :current_user

# Documents
SELECT * FROM ai.cirkelline_knowledge
WHERE metadata->>'user_id' = :current_user
```

**How it works:** Every database query includes `WHERE user_id = 'current-user'`

#### 2. In-Memory State ❌ (Requires Manual Management)

Shared Python objects are NOT automatically isolated:

```python
cirkelline.instructions  # Python list in server memory
cirkelline.tools         # Python list in server memory
```

**Problem:** These are shared across ALL users in the same Python process!

### The Leakage Problem

**Without proper cleanup, state leaks between users:**

```
Timeline:

Request 1 - User A (instructions: "Always respond in Danish")
  → cirkelline.instructions = [original] + [Danish instructions]
  → Response sent
  ⚠️  Instructions list STILL contains Danish instructions!

Request 2 - User B (no custom instructions)
  → cirkelline.instructions = [original] + [Danish instructions] ← Still there!
  → User B gets Danish responses even though they didn't ask!

Request 3 - User C (instructions: "Be very technical")
  → cirkelline.instructions = [original] + [Danish] + [Technical]
  → Both User A's AND User C's instructions are now active!
  → Instructions list keeps growing...
```

### The Solution: Save-Modify-Restore Pattern

**Implementation:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/custom_cirkelline.py`

```python
# 1. SAVE original state before modifying
original_instructions = cirkelline.instructions.copy()
original_tools = cirkelline.tools.copy()

# 2. MODIFY for THIS request only
if user_instructions:
    cirkelline.instructions.extend(custom_instructions_section)
if has_google:
    cirkelline.tools.extend(google_tools)

# 3. RUN the request
cirkelline.arun(input=message, ...)

# 4. RESTORE original state for next request
finally:
    cirkelline.instructions = original_instructions
    cirkelline.tools = original_tools
    logger.info("🧹 Restored original Cirkelline configuration")
```

### Architecture Diagram

```
┌─────────────────────────────────────────┐
│   FastAPI Server (Single Python Process)│
│                                          │
│   ┌─────────────────────────────────┐   │
│   │ cirkelline = Team(...)          │   │ ← Created ONCE at startup
│   │ (Singleton, shared by all)      │   │
│   └─────────────────────────────────┘   │
│                                          │
│   ┌─────────────────────────────────┐   │
│   │ Request 1 (User A)              │   │ ← Save → Modify → Restore
│   ├─────────────────────────────────┤   │
│   │ Request 2 (User B)              │   │ ← Save → Modify → Restore
│   ├─────────────────────────────────┤   │
│   │ Request 3 (User C)              │   │ ← Save → Modify → Restore
│   └─────────────────────────────────┘   │
│                                          │
│   All requests modify the SAME object   │
│   but cleanup ensures no leakage        │
└─────────────────────────────────────────┘
```

### Real-World Analogy

**Database Isolation (Already Working):**
- Each customer has their own table, order, and bill at a restaurant
- Waiter checks table number before serving
- ✅ Works automatically through SQL WHERE clauses

**In-Memory State (Requires Management):**
- The chef's recipe book is shared by everyone
- Customer A writes "add extra salt" in the book
- Without cleanup → ALL future customers get extra salt!
- With cleanup → Use sticky notes, remove after each order

### Why Alternative Solutions Don't Work

#### 1. Create New Team Per Request ❌
```python
# Don't do this!
cirkelline = Team(...)  # Create new team for every request
```
**Problems:**
- Too expensive (loads models, tools, databases)
- Loses session context and memory
- AGNO not designed for this pattern
- Would slow down every request

#### 2. Use Dependency Injection ❌
```python
# Can't do this with AGNO
cirkelline.arun(input=message, instructions=custom_instructions)
```
**Problems:**
- AGNO's `run()` doesn't accept instructions parameter
- Instructions are set at Team creation time, not per-run
- Would require framework changes

#### 3. Pass Instructions in Message ❌
```python
# Unreliable
message = f"{user_instructions}\n\nUser question: {actual_message}"
```
**Problems:**
- Not guaranteed to be followed
- Conflicts with other instructions
- Can be overridden by prompt engineering
- Less reliable than system-level instructions

### Where This Pattern is Used

#### 1. Custom User Instructions
**Location:** `my_os.py:1782-1800, 1833-1837, 1854-1856`

```python
# User A: "Always respond in Danish"
# User B: "Be very technical"
# Both get their custom behavior without interference
```

#### 2. Google Tools (Per-User)
**Location:** `my_os.py:1777-1780`

```python
# User A: Has Google connected → Add Gmail/Calendar tools
# User B: No Google → Don't add tools
# User A's tools don't appear for User B
```

### Verification & Logging

**Backend logs show the pattern:**
```bash
📝 User has custom instructions: Always respond in Danish...
📝 Injecting user custom instructions into Cirkelline
🔍 Instructions count BEFORE: 120
🔍 Instructions count AFTER: 130
[Request processing...]
🧹 Restored original Cirkelline configuration after stream
🔍 Instructions count RESTORED: 120
```

### Critical Implementation Notes

1. **Always use `.copy()`** when saving original state:
   ```python
   original = cirkelline.instructions.copy()  # ✅ Creates new list
   original = cirkelline.instructions          # ❌ Same reference!
   ```

2. **Use `finally` block** to ensure cleanup even on errors:
   ```python
   try:
       cirkelline.arun(...)
   finally:
       cirkelline.instructions = original  # Always runs
   ```

3. **Both streaming and non-streaming** need cleanup:
   - Streaming: Cleanup in generator's `finally` block
   - Non-streaming: Cleanup after `cirkelline.arun()`

4. **Order matters:**
   ```python
   # ✅ Correct order
   save → modify → run → restore

   # ❌ Wrong - restore happens before run completes
   save → modify → restore → run
   ```

### Future Considerations

If more per-user customizations are needed:
- Follow the same Save-Modify-Restore pattern
- Consider creating a context manager:
  ```python
  with cirkelline_context(user_id) as ctx:
      ctx.add_instructions(user_instructions)
      ctx.add_tools(user_tools)
      ctx.run(message)
  # Automatic cleanup on context exit
  ```

### Testing Multi-User Isolation

**Test Script:**
```python
# User A - Set Danish instructions
# User B - Set no instructions
# User A - Send message → Should get Danish
# User B - Send message → Should get English
# User A - Send message → Should STILL get Danish (no interference)
```

**Key Assertion:** User B's request must NOT show Danish responses, proving cleanup worked.

---

## Component Interactions

### Complete System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐         │
│  │ AuthContext│  │   Zustand  │  │ SSE Handler  │         │
│  └──────┬─────┘  └──────┬─────┘  └──────┬───────┘         │
│         │                │                │                  │
│         └────────────────┴────────────────┘                  │
│                          ↓                                   │
└─────────────────────────│────────────────────────────────────┘
                          │ HTTP POST + SSE
                          ↓
┌─────────────────────────│────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          Middleware Chain                            │   │
│  │  ┌─────────────────┐  ┌──────────────────┐         │   │
│  │  │ Anonymous User  │→ │  JWT Middleware  │         │   │
│  │  │   Middleware    │  │                  │         │   │
│  │  └─────────────────┘  └──────────────────┘         │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │      Custom Endpoint                                 │   │
│  │      /teams/cirkelline/runs                          │   │
│  │                                                      │   │
│  │  • Extract user_id                                   │   │
│  │  • Build knowledge_filters                           │   │
│  │  • Generate session_id if needed                     │   │
│  │  • Pass to AGNO                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
└─────────────────────────│────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────│────────────────────────────────────┐
│                    AGNO FRAMEWORK                            │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Cirkelline Orchestrator                      │   │
│  │                                                      │   │
│  │  • Analyzes intent                                   │   │
│  │  • Gathers context                                   │   │
│  │  • Routes to specialists                             │   │
│  │  • Synthesizes responses                             │   │
│  └───────┬───────────┬──────────┬────────────┬──────────┘   │
│          │           │          │            │              │
│   ┌──────▼─────┐ ┌──▼──────┐ ┌─▼────────┐ ┌─▼──────────┐  │
│   │   Image    │ │Document │ │Research  │ │  Law       │  │
│   │ Specialist │ │Specialist│ │  Team    │ │  Team      │  │
│   └────────────┘ └──────────┘ └──────────┘ └────────────┘  │
│                          ↓                                   │
└─────────────────────────│────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────│────────────────────────────────────┐
│                     POSTGRESQL                               │
│                          ↓                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   public     │  │      ai      │  │   pgvector       │  │
│  │              │  │              │  │                  │  │
│  │ • users      │  │ • sessions   │  │ • vectors        │  │
│  │ • admins     │  │ • memories   │  │ • embeddings     │  │
│  │              │  │ • knowledge  │  │ • HNSW index     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow: Complete Message

```
1. User types "Analyze this image" + uploads photo
     ↓
2. Frontend (useAIStreamHandler.tsx):
   - Creates FormData with message + file
   - Adds JWT token to headers
   - POSTs to /teams/cirkelline/runs
     ↓
3. Backend Middleware:
   - JWT decoded: user_id, dependencies
   - request.state.user_id = "uuid"
   - request.state.dependencies = {...}
     ↓
4. Custom Endpoint:
   - Reads user_id from request.state
   - Creates knowledge_filters
   - Generates session_id if needed
   - Calls cirkelline.arun() with filters
     ↓
5. AGNO Framework:
   - Loads session from DB (filtered by user_id)
   - Loads user memories (filtered by user_id)
   - Injects dependencies into instructions
   - Applies knowledge filters
     ↓
6. Cirkelline Orchestrator:
   - Reads instructions with {user_name}, {user_type}
   - Sees image attachment
   - Routes to Image Specialist
     ↓
7. Image Specialist:
   - Processes image with Gemini multimodal
   - Returns detailed analysis
     ↓
8. Cirkelline Synthesizes:
   - Rewrites in conversational tone
   - Adds personalization
   - Streams response
     ↓
9. Backend Streams SSE:
   - event: RunContent
   - data: {content: "..."}
     ↓
10. Frontend Processes:
    - Appends content to message
    - Updates UI in real-time
    - Saves session to sidebar
     ↓
11. User sees: "I can see this is a photo of..."
```

---

## Quick Reference

### Key Files

```bash
# Backend
/home/eenvy/Desktop/cirkelline/my_os.py                    # Main system
/home/eenvy/Desktop/cirkelline/.env                        # Config

# Frontend
/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/
├── contexts/AuthContext.tsx                               # Auth
├── hooks/useAIStreamHandler.tsx                           # Streaming
├── store.ts                                               # State
└── api/routes.ts                                          # API routes

# Database
ai.agno_sessions                                           # Sessions
ai.agno_memories                                           # Memories
ai.agno_knowledge                                          # Knowledge metadata
ai.cirkelline_knowledge_vectors                            # Embeddings
public.users                                               # Users
public.admin_profiles                                      # Admin data
```

### Key Concepts

```python
# User Isolation
user_id = getattr(request.state, 'user_id')
knowledge_filters = {"user_id": user_id}

# Session Generation
if not session_id:
    session_id = str(uuid.uuid4())

# Admin Context
dependencies = {
    "user_name": "Ivo",
    "user_type": "Admin",
    "admin_context": "..."
}

# Team Structure (AGNO v2)
Team(
    members=[specialist1, specialist2],
    share_member_interactions=True,   # Members see each other's work
    show_members_responses=True,      # Parent sees member responses
    store_member_responses=True,      # Enable synthesis
    enable_session_summaries=True
    # Note: mode parameter deprecated in AGNO v2
)
```

### Architecture Decisions

| Decision | Reason |
|----------|--------|
| Teams over individual agents | Better results through specialization |
| Session summaries enabled | Prevents context overflow |
| share_member_interactions=True | Enables team coordination (AGNO v2) |
| show_members_responses=True | Parent teams see synthesis (AGNO v2) |
| Hybrid vector search | Better retrieval accuracy |
| JWT in middleware | Centralized auth handling |
| Optimistic session add | Instant UI feedback |
| User isolation at DB level | Security by design |

---

## AGNO v2 Migration Notes

**Updated:** 2025-11-13 (v1.2.23)

### Deprecated Parameters (REMOVED)

**`mode` Parameter:**
- **Status:** DEPRECATED in AGNO v2
- **Old Values:** `"route"`, `"coordinate"`, `"collaborate"`
- **Migration:**
  - `mode="coordinate"` → Now default behavior (no parameter needed)
  - `mode="route"` → Use `respond_directly=True`
  - `mode="collaborate"` → Use `delegate_task_to_all_members=True`

**`enable_agentic_context` Parameter:**
- **Status:** REMOVED in AGNO v2
- **Migration:** Functionality replaced by `share_member_interactions` and other state management parameters

### Current AGNO v2 Parameters

**Team Coordination (v1.2.23 Delegation Fix):**

```python
Team(
    name="Research Team",
    # ═══ CRITICAL COORDINATION PARAMETERS ═══
    share_member_interactions=True,   # Members see each other's work (Default: False)
    show_members_responses=True,      # Parent sees member responses (Default: False)
    store_member_responses=True,      # Enable synthesis (Default: False)
    # ═══════════════════════════════════════
    members=[agent1, agent2],
    instructions=[...],
    # Other parameters...
)
```

**Parameter Descriptions:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `share_member_interactions` | bool | False | Members can see each other's work during the same run. CRITICAL for nested team coordination. |
| `show_members_responses` | bool | False | Include member responses in team output. CRITICAL for parent teams to see synthesis. |
| `store_member_responses` | bool | False | Store member responses for synthesis. CRITICAL for output retention. |
| `respond_directly` | bool | False | Replaces `mode="route"`. Member responds directly to user. |
| `delegate_task_to_all_members` | bool | False | Replaces `mode="collaborate"`. All members get same task. |

**Why These Parameters Matter:**

Without proper configuration, nested teams cannot coordinate:
- Research Analyst won't see Web Researcher's findings
- Cirkelline won't see Research Team's synthesis
- Delegation appears to "freeze" (announced but nothing happens)

See [docs/19-DELEGATION-FREEZE-FIX.md](./19-DELEGATION-FREEZE-FIX.md) for complete technical details on the v1.2.23 fix.

**Documentation Verified:** All parameters verified against official AGNO documentation using Agno MCP (https://docs.agno.com/mcp).

---

**See Also:**

**Core References:**
- [00-OVERVIEW.md](./00-OVERVIEW.md) - Complete startup guide and documentation index
- [05-BACKEND-REFERENCE.md](./05-BACKEND-REFERENCE.md) - API endpoints and backend details
- [06-FRONTEND-REFERENCE.md](./06-FRONTEND-REFERENCE.md) - Frontend architecture
- [04-DATABASE-REFERENCE.md](./04-DATABASE-REFERENCE.md) - Database schema

**Features & Integration:**
- [12-GOOGLE-SERVICES.md](./12-GOOGLE-SERVICES.md) - ⭐ Google OAuth, Gmail, Calendar, Sheets integration
- [51-FEEDBACK-SYSTEM.md](./51-FEEDBACK-SYSTEM.md) - User feedback system
- [52-USER-MANAGEMENT-SYSTEM.md](./52-USER-MANAGEMENT-SYSTEM.md) - User management
- [53-REAL-TIME-ACTIVITY-LOGGING.md](./53-REAL-TIME-ACTIVITY-LOGGING.md) - Activity logging
- [54-KNOWLEDGE-DOCUMENT-SYSTEM.md](./54-KNOWLEDGE-DOCUMENT-SYSTEM.md) - Private document system
