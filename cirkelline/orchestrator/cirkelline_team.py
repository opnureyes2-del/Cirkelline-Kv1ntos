"""
Cirkelline Main Orchestrator
=============================
Main orchestrator team that coordinates all specialist agents and teams.
Receives user requests and intelligently routes to appropriate specialists.
"""

import os
from agno.team import Team
from agno.models.google import Gemini
from agno.memory import MemoryManager  # v1.2.34.5: Explicit MemoryManager for memory creation
from agno.tools.duckduckgo import DuckDuckGoTools  # v1.2.34: Added for news/current events
from agno.tools.reasoning import ReasoningTools
from agno.tools.user_control_flow import UserControlFlowTools
# v1.2.34.1: REMOVED MemoryTools - using enable_user_memories=True instead (auto-memory)

# KERNEMANDAT: Prioriter gratis løsninger - Exa og Tavily er valgfrie
EXA_AVAILABLE = bool(os.getenv("EXA_API_KEY"))
TAVILY_AVAILABLE = bool(os.getenv("TAVILY_API_KEY"))

if EXA_AVAILABLE:
    from agno.tools.exa import ExaTools
if TAVILY_AVAILABLE:
    from agno.tools.tavily import TavilyTools

# Import all specialist agents
from cirkelline.agents.specialists import audio_agent, video_agent, image_agent, document_agent

# Import specialist teams
from cirkelline.agents.research_team import research_team
from cirkelline.agents.law_team import law_team

# Import orchestrator components
# NOTE: memory_manager.py DEPRECATED in v1.2.34 - now using MemoryTools for agent-controlled memory
from cirkelline.orchestrator.instructions import get_cirkelline_instructions

# Import tools and infrastructure
from cirkelline.tools.knowledge_tools import FilteredKnowledgeSearchTool
from cirkelline.tools.notion_tools import NotionTools
from cirkelline.tools.memory_search_tool import IntelligentMemoryTool  # v1.2.34.4: Intelligent memory search
from cirkelline.tools.ckc_tools import get_ckc_tools  # v1.3.3: CKC Bridge integration
from cirkelline.database import db
from cirkelline.knowledge_base import knowledge
from cirkelline.config import logger, ADMIN_USER_IDS

# Create custom knowledge search tool with permission filtering
filtered_search_tool = FilteredKnowledgeSearchTool(
    knowledge_base=knowledge,
    database=db,
    admin_ids=ADMIN_USER_IDS
)

# Create Notion workspace integration tools
notion_tools = NotionTools(database=db)

# v1.2.34.4: Intelligent memory search tool
# Uses search_user_memories(retrieval_method="agentic") to select ONLY relevant memories
# Instead of loading all 194 memories every request
memory_search_tool = IntelligentMemoryTool(database=db)

# v1.3.3: CKC Bridge tools - enables Cirkelline to interact with CKC ecosystem
# Provides: get_ckc_status, create_ckc_task, start_mastermind_session, list_learning_rooms
ckc_tools = get_ckc_tools()

# v1.2.34.5: Explicit MemoryManager for memory CREATION
# Required for enable_user_memories=True to work with Teams
# v1.2.34.6: Added additional_instructions for aggressive memory capture
# v1.3.0: Added STANDARD_TOPICS and topic rules for consistency (Memory Optimization Workflow prep)
STANDARD_TOPICS = [
    "preferences", "goals", "relationships", "family", "identity",
    "emotional state", "communication style", "behavioral patterns",
    "work", "projects", "deadlines", "skills", "expertise",
    "interests", "hobbies", "sports", "music", "travel",
    "programming", "ai", "technology", "software", "hardware",
    "location", "events", "calendar", "history",
    "legal", "research", "news", "finance",
]

memory_manager = MemoryManager(
    model=Gemini(id="gemini-2.5-flash"),
    db=db,
    additional_instructions=f"""
IMPORTANT: Be SELECTIVE about capturing memories. Only store LASTING personal facts about the USER.

## WHAT TO CAPTURE (lasting personal facts):

1. IDENTITY: Name, role, location, background, occupation
2. RELATIONSHIPS: Family members, friends, pets WITH NAMES (e.g., "Sister Emma", "Dog Max")
3. PREFERENCES: Communication style, tools they prefer, technical choices, likes/dislikes
4. INTERESTS: Hobbies, goals, expertise areas, sports teams, music taste
5. LIFE EVENTS: Milestones, achievements, significant changes

## WHAT TO NEVER CAPTURE:

- ONE-TIME TASKS: "send email to X", "create event for today", "look up X"
- EPHEMERAL QUERIES: "what's the weather", "latest news", "what time is it"
- TECHNICAL IMPLEMENTATION DETAILS: Code, APIs, line numbers, versions, endpoints, database columns
- REQUEST ARTIFACTS: The question itself (only capture lasting facts revealed)
- CONVERSATION MECHANICS: "User asked about...", "User wanted to know..."

## THE KEY QUESTION:

Ask: "Would the user want this remembered 6 MONTHS from now?"
- If NO → Don't capture (it's ephemeral)
- If YES → Capture (it's a lasting personal fact)

## EXAMPLES:

CAPTURE:
- "User's sister Emma got engaged to Marcus" → lasting relationship fact
- "User prefers TypeScript over JavaScript" → lasting preference
- "User is CEO of Cirkelline, works with Rasmus" → identity + relationships

DO NOT CAPTURE:
- "User asked about implementing a feature" → one-time task
- "User wants to send an email" → ephemeral request
- "GET /api/user endpoint at line 4553" → technical detail (AI can access code)
- "Fixed bug in v1.1.17" → one-time fix, no future value

TOPIC RULES (CRITICAL - follow these exactly):
- ALWAYS use lowercase topics (never "PREFERENCES", always "preferences")
- PREFER these standard topics: {", ".join(STANDARD_TOPICS)}
- If no standard topic fits, create a NEW broad category (e.g., "cooking", "pets", "health")
- NEVER use specific details as topics (BAD: "Apollo 11", "Benfica", "pasta carbonara")
- Use broad categories instead (GOOD: "history", "sports", "cooking")
- Maximum 3 topics per memory
"""
)

# KERNEMANDAT: Byg tools liste dynamisk baseret på tilgængelige API keys
# DuckDuckGo er altid tilgængelig (gratis)
_available_tools = [
    memory_search_tool,  # ✅ v1.2.34.4: Intelligent memory search (NOT loading all 194)
    DuckDuckGoTools(add_instructions=True),  # ✅ GRATIS: News, current events, quick facts
    ReasoningTools(add_instructions=True),
    UserControlFlowTools(
        instructions="Use get_user_input when you need to gather structured information or clarify requirements before taking action. This allows you to pause execution and ask the user specific questions.",
        add_instructions=True,
        enable_get_user_input=True
    ),
    filtered_search_tool,  # ← Custom knowledge search with permission filtering
    notion_tools,  # ← Notion workspace integration tools
    ckc_tools,  # ✅ v1.3.3: CKC Bridge - Mastermind, Learning Rooms, Task Management
]

# Tilføj betalte søgeværktøjer KUN hvis API keys er sat
if EXA_AVAILABLE:
    _available_tools.insert(2, ExaTools(add_instructions=True))  # Semantic search
    logger.info("✅ ExaTools tilføjet til Cirkelline (EXA_API_KEY fundet)")
else:
    logger.warning("⚠️ ExaTools ikke tilgængelig - EXA_API_KEY ikke sat (kun DuckDuckGo)")

if TAVILY_AVAILABLE:
    _available_tools.insert(3 if EXA_AVAILABLE else 2, TavilyTools(add_instructions=True))  # Deep search
    logger.info("✅ TavilyTools tilføjet til Cirkelline (TAVILY_API_KEY fundet)")
else:
    logger.warning("⚠️ TavilyTools ikke tilgængelig - TAVILY_API_KEY ikke sat (kun DuckDuckGo)")

logger.info(f"Cirkelline tools: {len(_available_tools)} aktive værktøjer")

# Main Cirkelline orchestrator team
cirkelline = Team(
    id="cirkelline",
    members=[
        audio_agent,
        video_agent,
        image_agent,
        document_agent,
        research_team,
        law_team,
    ],
    model=Gemini(id="gemini-2.5-flash"),  # v1.2.24: Using search tools instead of native search

    # ═══ CRITICAL AGNO TEAM COORDINATION SETTINGS ═══
    # Note: mode="coordinate" removed - deprecated in AGNO v2 (coordinate is now default)
    # Note: enable_agentic_context removed - deprecated in AGNO v2
    add_session_state_to_context=True,    # ← 🔥 FIX v1.2.26: Make session_state visible to model
    share_member_interactions=True,       # ← See nested team outputs
    show_members_responses=True,          # ← 🔥 CRITICAL: Include specialist responses
    store_member_responses=True,          # ← 🔥 CRITICAL: Capture all outputs
    # ═══════════════════════════════════════════════

    tools=_available_tools,  # ✅ KERNEMANDAT: Dynamisk baseret på tilgængelige API keys
    tool_choice="auto",  # ✅ Allow autonomous tool usage including think()
    tool_call_limit=25,  # ✅ v1.2.33: Prevent runaway loops, control costs
    name="Cirkelline",
    description="Personal assistant that helps with everyday tasks",
    # v1.2.27: Callable instructions - receives RunContext with metadata containing deep_research flag
    # Function returns COMPLETELY DIFFERENT instructions based on mode (no conflicting tool mentions)
    instructions=get_cirkelline_instructions,  # ← FUNCTION, not list!
    db=db,
    memory_manager=memory_manager,  # v1.2.34.5: Explicit MemoryManager for memory creation
    # ═══════════════════════════════════════
    # KNOWLEDGE CONFIGURATION - USING CUSTOM TOOL INSTEAD
    # ═══════════════════════════════════════
    knowledge=knowledge,                              # ← Knowledge base (for document uploads)
    search_knowledge=False,                          # ← Disable built-in search (use custom tool instead!)
    # v1.2.34.4: Intelligent memory configuration
    # - add_memories_to_context=False: DON'T auto-load all 194 memories
    # - enable_user_memories=True: Still CREATE memories at end of runs
    # - enable_agentic_memory=True: Agent can update memories via tool
    # Agent uses search_memories() tool for intelligent retrieval instead
    add_memories_to_context=False,        # ✅ v1.2.34.4: DON'T auto-load all memories
    enable_user_memories=True,            # ✅ v1.2.34.4: Still create memories
    enable_agentic_memory=True,           # ✅ v1.2.34.4: Agent can update memories
    enable_session_summaries=True,        # Prevent context overflow
    # Note: add_datetime_to_context removed in v1.2.33 - callable instructions already handle user timezone via session_state
    add_history_to_context=True,
    num_history_runs=3,                   # ✅ v1.2.34: Reduced from 5 (saves ~500 tokens)
    search_session_history=True,
    num_history_sessions=1,               # ✅ v1.2.34: Reduced from 3 (saves ~300 tokens)
    read_chat_history=True,               # ✅ v1.2.33: Access ANY message from ANY session via get_chat_history() tool
    compress_tool_results=True,           # ✅ v1.2.34: Compress old tool results after 3 calls (saves context tokens)
    markdown=True,
    # Note: show_members_responses and store_member_responses already defined above in AGNO configuration block
    store_events=True,                    # ✅ AGNO Official: Retain all run events
    debug_mode=True,   # Enable detailed logging
    debug_level=2,     # Verbose debug output
)

# ═══ CRITICAL: Resolve forward reference in session_naming.py ═══
# session_naming.py needs access to cirkelline team for intelligent session naming
# This must be called AFTER cirkelline team is created
from cirkelline.helpers.session_naming import set_cirkelline_team
set_cirkelline_team(cirkelline)
# ═══════════════════════════════════════════════════════════════

logger.info("✅ Cirkelline orchestrator module loaded")
