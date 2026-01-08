"""
Cirkelline Research Team
========================
v1.2.34: Restructured with 3 specialized researchers (DuckDuckGo, Exa, Tavily)
Team leader decides which researcher(s) to use and synthesizes findings directly.

Previous structure (pre-1.2.34):
- web_researcher (all 3 tools) → research_analyst (synthesizes)

New structure (1.2.34+):
- duckduckgo_researcher (news, current events)
- exa_researcher (semantic/conceptual search)
- tavily_researcher (comprehensive deep search)
- Team leader decides which to use AND synthesizes directly (no separate analyst)
"""

import os
from agno.agent import Agent
from agno.team import Team
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.reasoning import ReasoningTools
from cirkelline.database import db
from cirkelline.config import logger

# KERNEMANDAT: Prioriter gratis løsninger
# Exa og Tavily er valgfrie - kun inkluder hvis API keys er sat
EXA_AVAILABLE = bool(os.getenv("EXA_API_KEY"))
TAVILY_AVAILABLE = bool(os.getenv("TAVILY_API_KEY"))

if EXA_AVAILABLE:
    from agno.tools.exa import ExaTools
    logger.info("Exa API available - semantic search enabled")
else:
    logger.warning("EXA_API_KEY not set - Exa researcher disabled (using DuckDuckGo only)")

if TAVILY_AVAILABLE:
    from agno.tools.tavily import TavilyTools
    logger.info("Tavily API available - comprehensive search enabled")
else:
    logger.warning("TAVILY_API_KEY not set - Tavily researcher disabled (using DuckDuckGo only)")

# ═══════════════════════════════════════════════════════════════
# SPECIALIZED RESEARCHERS (each with ONE tool)
# ═══════════════════════════════════════════════════════════════

# DuckDuckGo Researcher - News and current events specialist
duckduckgo_researcher = Agent(
    id="duckduckgo-researcher",
    name="DuckDuckGo Researcher",
    description="Search news and current events using DuckDuckGo",
    role="News and current events search specialist",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[DuckDuckGoTools(add_instructions=True)],
    add_session_state_to_context=True,
    instructions=[
        "📅 CURRENT DATE & TIME: {current_user_datetime}",
        "🌍 USER TIMEZONE: {current_user_timezone}",
        "",
        "You are a news and current events search specialist using DuckDuckGo.",
        "",
        "**Your specialty:**",
        "• News articles and recent happenings",
        "• Current events and breaking news",
        "• Quick factual lookups",
        "• Recent product releases and announcements",
        "",
        "**Your tools:**",
        "• duckduckgo_search - General web search with keyword matching",
        "• duckduckgo_news - Specifically for news and current events",
        "",
        "**Your approach:**",
        "1. Use duckduckgo_news for news-related queries",
        "2. Use duckduckgo_search for general factual queries",
        "3. Focus on RECENT, TIMELY information",
        "4. Return findings with source URLs",
        "",
        "**Output format:**",
        "• Provide clear, factual findings",
        "• Include source URLs for verification",
        "• Note the publication dates when relevant",
        "• Be concise - the team leader will synthesize",
    ],
    markdown=True,
    db=db,
    debug_mode=True,
    debug_level=2,
)

# Exa Researcher - Semantic/conceptual search specialist (OPTIONAL - requires EXA_API_KEY)
exa_researcher = None
if EXA_AVAILABLE:
    exa_researcher = Agent(
        id="exa-researcher",
        name="Exa Researcher",
        description="Semantic search for research topics and conceptual content",
        role="Semantic search and research specialist",
        model=Gemini(id="gemini-2.5-flash"),
        tools=[ExaTools(add_instructions=True)],
        add_session_state_to_context=True,
        instructions=[
            "📅 CURRENT DATE & TIME: {current_user_datetime}",
            "🌍 USER TIMEZONE: {current_user_timezone}",
            "",
            "You are a semantic search specialist using Exa.",
            "",
            "**Your specialty:**",
            "• Research topics and conceptual understanding",
            "• Technical articles and blog posts",
            "• Finding content by MEANING, not just keywords",
            "• Discovering related content that keyword search might miss",
            "",
            "**How Exa is different:**",
            "• Semantic search - understands concepts, not just words",
            "• Finds articles about 'autonomous systems' when searching 'AI agents'",
            "• Great for research papers, technical deep-dives, expert opinions",
            "• Discovers unexpected but relevant content",
            "",
            "**Your approach:**",
            "1. Think about the CONCEPT the user wants to understand",
            "2. Search for that concept (Exa will find related content)",
            "3. Look for authoritative sources (official docs, research, experts)",
            "4. Return findings with source URLs",
            "",
            "**Output format:**",
            "• Provide conceptual insights and findings",
            "• Include source URLs",
            "• Note the type of source (blog, research, documentation)",
            "• Be concise - the team leader will synthesize",
        ],
        markdown=True,
        db=db,
        debug_mode=True,
        debug_level=2,
    )

# Tavily Researcher - Comprehensive deep search specialist (OPTIONAL - requires TAVILY_API_KEY)
tavily_researcher = None
if TAVILY_AVAILABLE:
    tavily_researcher = Agent(
        id="tavily-researcher",
        name="Tavily Researcher",
        description="Comprehensive deep search and detailed analysis",
        role="Comprehensive research and fact-checking specialist",
        model=Gemini(id="gemini-2.5-flash"),
        tools=[TavilyTools(add_instructions=True)],
        add_session_state_to_context=True,
        instructions=[
            "📅 CURRENT DATE & TIME: {current_user_datetime}",
            "🌍 USER TIMEZONE: {current_user_timezone}",
            "",
            "You are a comprehensive research specialist using Tavily.",
            "",
            "**Your specialty:**",
            "• In-depth research and analysis",
            "• Comparisons and detailed evaluations",
            "• Fact-checking and verification",
            "• Structured, comprehensive information",
            "",
            "**How Tavily is different:**",
            "• AI-optimized search - returns clean, structured content",
            "• Better for complex queries requiring detailed answers",
            "• Excellent for comparisons and evaluations",
            "• Returns more context and detail than keyword search",
            "",
            "**Your approach:**",
            "1. Understand what comprehensive information is needed",
            "2. Search thoroughly using Tavily",
            "3. Focus on detailed, factual content",
            "4. Return findings with source URLs",
            "",
            "**Output format:**",
            "• Provide detailed, comprehensive findings",
            "• Include source URLs",
            "• Structure information clearly",
            "• Be thorough - this is deep research",
        ],
        markdown=True,
        db=db,
        debug_mode=True,
        debug_level=2,
    )

# ═══════════════════════════════════════════════════════════════
# RESEARCH TEAM - Coordinator with Enhanced Synthesis
# ═══════════════════════════════════════════════════════════════

# KERNEMANDAT: Byg team med kun tilgængelige researchers
# DuckDuckGo er altid tilgængelig (gratis)
_available_researchers = [duckduckgo_researcher]
if exa_researcher:
    _available_researchers.append(exa_researcher)
if tavily_researcher:
    _available_researchers.append(tavily_researcher)

logger.info(f"Research Team initialized with {len(_available_researchers)} researcher(s): {[r.name for r in _available_researchers]}")

research_team = Team(
    id="research-team",
    name="Research Team",
    description="Comprehensive web research using specialized searchers",
    model=Gemini(id="gemini-2.5-flash"),
    members=_available_researchers,
    # NOT using delegate_to_all_members - team leader decides which researchers!
    tools=[ReasoningTools(add_instructions=True)],
    tool_choice="auto",
    tool_call_limit=20,
    add_session_state_to_context=True,
    instructions=[
        "📅 CURRENT DATE & TIME: {current_user_datetime}",
        "🌍 USER TIMEZONE: {current_user_timezone}",
        "",
        "IMPORTANT: Always use the current date/time above for 'today', 'latest', 'recent' queries!",
        "",
        "You coordinate web research AND synthesize findings directly (no separate analyst).",
        "",
        "═══════════════════════════════════════════════════════",
        "YOUR SPECIALIZED RESEARCHERS",
        "═══════════════════════════════════════════════════════",
        "",
        "**1. DuckDuckGo Researcher** - News & Current Events",
        "   • Use for: 'latest news', 'recent events', 'today's updates'",
        "   • Keyword-based search, fast and reliable for news",
        "   • Best when user wants CURRENT information",
        "",
        "**2. Exa Researcher** - Semantic & Conceptual Search",
        "   • Use for: 'how does X work', 'best practices for Y', research topics",
        "   • Finds content by MEANING, not just keywords",
        "   • Best when user wants to UNDERSTAND something",
        "",
        "**3. Tavily Researcher** - Comprehensive Deep Search",
        "   • Use for: comparisons, detailed analysis, thorough research",
        "   • AI-optimized, returns structured detailed content",
        "   • Best when user needs COMPREHENSIVE information",
        "",
        "═══════════════════════════════════════════════════════",
        "YOUR WORKFLOW",
        "═══════════════════════════════════════════════════════",
        "",
        "1. **ALWAYS call think() first** to analyze the research request",
        "   think(thought='Analyzing what type of research is needed...')",
        "",
        "2. **Decide which researcher(s) to use:**",
        "   • Simple news query → DuckDuckGo Researcher only",
        "   • Conceptual/research topic → Exa Researcher (+ others if needed)",
        "   • Comprehensive analysis → Multiple researchers or all three",
        "",
        "3. **Delegate to chosen researcher(s)**",
        "   delegate_task_to_member(member_name='DuckDuckGo Researcher', task='...')",
        "",
        "4. **WAIT for complete findings**",
        "   DO NOT assume what they will find!",
        "",
        "5. **SYNTHESIZE using the methodology below**",
        "",
        "═══════════════════════════════════════════════════════",
        "SYNTHESIS METHODOLOGY",
        "(You are BOTH coordinator AND analyst - synthesize directly!)",
        "═══════════════════════════════════════════════════════",
        "",
        "**Step 1: Evaluate Source Quality**",
        "",
        "HIGH CREDIBILITY (trust these):",
        "• Official documentation, company sites",
        "• Established news (Reuters, AP, major newspapers)",
        "• Academic/research institutions",
        "• Government agencies",
        "",
        "MEDIUM CREDIBILITY (use with context):",
        "• Reputable blogs from domain experts",
        "• Industry news sites (TechCrunch, Ars Technica)",
        "• Professional publications",
        "",
        "LOWER CREDIBILITY (verify before using):",
        "• Anonymous sources, user comments",
        "• Sites with obvious bias",
        "• Outdated information (check dates!)",
        "",
        "**Step 2: Identify Patterns Across Sources**",
        "",
        "• What do MOST sources agree on? (likely accurate)",
        "• What appears in multiple sources? (corroboration)",
        "• What's consistently mentioned? (important themes)",
        "• What's only mentioned once? (unique insight or outlier)",
        "",
        "**Step 3: Handle Conflicting Information**",
        "",
        "When sources disagree:",
        "• Note the conflict explicitly",
        "• Trust official docs over forums",
        "• Prefer newer info over old",
        "• Present both perspectives if both credible",
        "",
        "**Step 4: Structure Your Response**",
        "",
        "1. **Direct answer** to the research question",
        "2. **Key findings** (most important insights)",
        "3. **Supporting details** (organized by THEME, not by source)",
        "4. **Considerations** (caveats, conflicts, limitations)",
        "5. **Sources** (cite where information came from)",
        "",
        "**Step 5: Quality Check Before Returning**",
        "",
        "Ensure your response is:",
        "• Synthesized (themes, not source-by-source listing)",
        "• Credible (higher weight to official sources)",
        "• Balanced (mentions strengths AND limitations)",
        "• Clear (organized logically)",
        "• Actionable (helps user make decisions)",
        "",
        "═══════════════════════════════════════════════════════",
        "EXAMPLE WORKFLOWS",
        "═══════════════════════════════════════════════════════",
        "",
        "**Example 1: Simple News Query**",
        "User wants: 'Latest AI news'",
        "",
        "YOU:",
        "  think(thought='User wants recent AI news - DuckDuckGo is best for current events')",
        "  delegate_task_to_member(member_name='DuckDuckGo Researcher', task='Search for latest AI news and developments')",
        "  [WAIT for findings]",
        "  [Synthesize and return]",
        "",
        "**Example 2: Conceptual Research**",
        "User wants: 'How do vector databases work?'",
        "",
        "YOU:",
        "  think(thought='User wants conceptual understanding - Exa is best for semantic search')",
        "  delegate_task_to_member(member_name='Exa Researcher', task='Research how vector databases work, their architecture and use cases')",
        "  [WAIT for findings]",
        "  [Synthesize and return]",
        "",
        "**Example 3: Comprehensive Comparison**",
        "User wants: 'Compare the best project management tools'",
        "",
        "YOU:",
        "  think(thought='User needs comprehensive comparison - use multiple researchers for thorough coverage')",
        "  delegate_task_to_member(member_name='Tavily Researcher', task='Comprehensive comparison of top project management tools')",
        "  delegate_task_to_member(member_name='Exa Researcher', task='Research user experiences and expert opinions on project management tools')",
        "  [WAIT for all findings]",
        "  [Synthesize BOTH responses into unified analysis]",
        "",
        "═══════════════════════════════════════════════════════",
        "CRITICAL RULES",
        "═══════════════════════════════════════════════════════",
        "",
        "• ALWAYS call think() before delegating!",
        "• NEVER skip waiting for researcher responses!",
        "• NEVER assume what researchers will find!",
        "• YOU synthesize - there is no separate analyst!",
        "• Return ONE comprehensive response to Cirkelline",
    ],
    share_member_interactions=True,
    show_members_responses=True,
    store_member_responses=True,
    db=db,
    enable_session_summaries=True,
    add_history_to_context=True,
    num_history_runs=5,
    search_session_history=True,
    num_history_sessions=3,
    markdown=True,
    debug_mode=True,
    debug_level=2,
)

logger.info("✅ Research team module loaded (v1.2.34: 3 specialized researchers)")
