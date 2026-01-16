import logging
from datetime import datetime, timedelta
import time
import bcrypt
from tzlocal import get_localzone_name
import httpx

# Phase B: Unified Logging Integration
try:
    from unified_logging import setup_admiral_logging
    logger = setup_admiral_logging(
        service_name="cirkelline-kv1ntos",
        level=logging.INFO
    )
    logger.info("✅ Unified logging initialized for cirkelline-kv1ntos")
except (ImportError, Exception) as e:
    # Fallback to basic logging if unified_logging not available or fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('cirkelline.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    if isinstance(e, ImportError):
        logger.warning("⚠️ Unified logging not available, using basic logging")
    else:
        logger.warning(f"⚠️ Unified logging setup failed: {e}, using basic logging")

logger.info("Starting Cirkelline AgentOS...")

# Load environment variables from .env file
import os
import uuid
import shutil
from dotenv import load_dotenv
load_dotenv()
logger.info("Environment variables loaded from .env")

# DEBUG: Print DATABASE_URL to verify it's being set correctly (only in debug mode)
if os.getenv('AGNO_DEBUG', 'false').lower() == 'true':
    print(f"DEBUG: DATABASE_URL = {os.getenv('DATABASE_URL')}")
    logger.info(f"DEBUG: DATABASE_URL from environment = {os.getenv('DATABASE_URL')}")

# Force enable monitoring (environment variable not working)
os.environ["AGNO_MONITOR"] = "true"
os.environ["AGNO_DEBUG"] = "false"
logger.info("Monitoring forcefully enabled via code")

from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.message import Message
from agno.os import AgentOS
from agno.team import Team
from agno.db.postgres import PostgresDb
from agno.run import RunContext
from agno.vectordb.pgvector import PgVector, SearchType
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.exa import ExaTools
from agno.tools.tavily import TavilyTools
from agno.tools.reasoning import ReasoningTools
from agno.memory import MemoryManager
from agno.tools.user_control_flow import UserControlFlowTools
from cirkelline.tools.media import DocumentProcessingTools
import uvicorn
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Body, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import jwt as pyjwt
from sqlalchemy import text

# ════════════════════════════════════════════════════════════════
# STAGE 1: CREATE FASTAPI APP FIRST (before AgentOS)
# ════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Cirkelline AgentOS",
    description="Multi-Agent System with Knowledge Filtering",
    version="1.3.3"
)

logger.info("✅ Stage 1: FastAPI app created at module level")

# ════════════════════════════════════════════════════════════════
# IMPORT EXTRACTED INFRASTRUCTURE
# ════════════════════════════════════════════════════════════════

# Database connections (Phase 1)
from cirkelline.database import db, vector_db

# Gateway Client Integration (Cross-Platform SSO)
from cirkelline.shared.gateway_client import GatewayClient

# Initialize gateway client
gateway_client = GatewayClient(
    gateway_url=os.getenv("GATEWAY_URL", "http://localhost:7779"),
    platform_code=os.getenv("GATEWAY_PLATFORM_CODE", "cirkelline"),
    api_key=os.getenv("GATEWAY_API_KEY", ""),
    timeout=5.0
)
logger.info(f"✅ Gateway client initialized: {gateway_client.gateway_url}")

# ════════════════════════════════════════════════════════════════
# DATABASE MIGRATIONS (v1.3.0 - Workflow Tables)
# ════════════════════════════════════════════════════════════════
def run_migrations():
    """Run database migrations on startup."""
    try:
        from cirkelline.middleware.middleware import _shared_engine
        from sqlalchemy import text as sql_text

        with _shared_engine.connect() as conn:
            # Create archive table
            conn.execute(sql_text("""
                CREATE TABLE IF NOT EXISTS ai.agno_memories_archive (
                    id SERIAL PRIMARY KEY,
                    original_memory_id VARCHAR NOT NULL,
                    user_id VARCHAR NOT NULL,
                    memory JSONB NOT NULL,
                    topics JSONB,
                    input VARCHAR,
                    created_at TIMESTAMP,
                    archived_at TIMESTAMP DEFAULT NOW(),
                    optimization_run_id VARCHAR
                )
            """))
            conn.execute(sql_text("CREATE INDEX IF NOT EXISTS idx_archive_user_id ON ai.agno_memories_archive(user_id)"))
            conn.execute(sql_text("CREATE INDEX IF NOT EXISTS idx_archive_run_id ON ai.agno_memories_archive(optimization_run_id)"))

            # Create workflow runs table
            conn.execute(sql_text("""
                CREATE TABLE IF NOT EXISTS ai.workflow_runs (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR UNIQUE NOT NULL,
                    workflow_name VARCHAR NOT NULL,
                    user_id VARCHAR,
                    status VARCHAR NOT NULL,
                    started_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP,
                    current_step VARCHAR,
                    steps_completed JSONB DEFAULT '[]',
                    input_data JSONB,
                    output_data JSONB,
                    error_message TEXT,
                    metrics JSONB
                )
            """))
            conn.execute(sql_text("CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON ai.workflow_runs(status)"))
            conn.execute(sql_text("CREATE INDEX IF NOT EXISTS idx_workflow_runs_user ON ai.workflow_runs(user_id)"))

            conn.commit()
            logger.info("✅ Database migrations completed (v1.3.0 workflow tables)")
    except Exception as e:
        logger.warning(f"⚠️ Database migration warning: {e}")

# Run migrations on startup
run_migrations()

# Specialist agents (Phase 4)
from cirkelline.agents.specialists import audio_agent, video_agent, image_agent, document_agent

# Teams (Phase 4-5)
from cirkelline.agents.research_team import research_team
from cirkelline.agents.law_team import law_team
from cirkelline.orchestrator.cirkelline_team import cirkelline

# ════════════════════════════════════════════════════════════════
# IMPORT AND REGISTER ALL EXTRACTED ROUTERS
# ════════════════════════════════════════════════════════════════

# Core API endpoints (Phase 7)
from cirkelline.endpoints.auth import router as auth_router
from cirkelline.endpoints.user import router as user_router
from cirkelline.endpoints.knowledge import router as knowledge_router
from cirkelline.endpoints.sessions import router as sessions_router
from cirkelline.endpoints.custom_cirkelline import router as cirkelline_router

# Google integration endpoints (Phase 8B, 8C, 8D)
from cirkelline.integrations.google.oauth_endpoints import router as google_oauth_router
from cirkelline.integrations.google.gmail_endpoints import router as gmail_router
from cirkelline.integrations.google.calendar_endpoints import router as calendar_router
from cirkelline.integrations.google.tasks_endpoints import router as tasks_router

# Notion integration endpoints (Phase 8E, 8F)
from cirkelline.integrations.notion import (
    notion_oauth_router,
    notion_database_router,
    notion_legacy_router
)

# User endpoints - memories and feedback (Phase 8G, moved to endpoints/ in v1.2.30)
from cirkelline.endpoints.memories import router as memories_router
from cirkelline.endpoints.feedback import router as feedback_router
from cirkelline.endpoints.preferences import router as preferences_router
from cirkelline.endpoints.subscriptions import router as subscriptions_router

# Admin endpoints (Phase 9)
from cirkelline.admin import (
    admin_users_router,
    admin_stats_router,
    admin_subscriptions_router,
    admin_activity_router,
    admin_workflows_router
)

# Terminal API endpoint (FASE 1.3 - Terminal Integration)
from cirkelline.api.terminal import router as terminal_router

# KV1NT Dashboard API (FASE 2.2 - KV1NT Integration)
from cirkelline.endpoints.kv1nt_dashboard import router as kv1nt_router

# CKC Control Panel API (v1.3.3 - CKC Bridge Integration)
from cirkelline.ckc.api import control_panel_router as ckc_router

# CKC Folder Switcher API (v1.3.5 - Super Admin Folder Navigation)
from cirkelline.ckc.api import folder_switcher_router as ckc_folder_router

# Register all routers with FastAPI app
app.include_router(auth_router, tags=["Authentication"])
app.include_router(user_router, tags=["User Profile"])
app.include_router(knowledge_router, tags=["Knowledge Base"])
app.include_router(sessions_router, tags=["Sessions"])
app.include_router(cirkelline_router, tags=["Cirkelline Team"])

app.include_router(google_oauth_router, tags=["Google OAuth"])
app.include_router(gmail_router, tags=["Gmail"])
app.include_router(calendar_router, tags=["Google Calendar"])
app.include_router(tasks_router, tags=["Google Tasks"])

app.include_router(notion_oauth_router, tags=["Notion OAuth"])
app.include_router(notion_database_router, tags=["Notion Databases"])
app.include_router(notion_legacy_router, tags=["Notion Legacy"])

app.include_router(memories_router, tags=["Memories"])
app.include_router(feedback_router, tags=["Feedback"])
app.include_router(preferences_router, tags=["User Preferences"])
app.include_router(subscriptions_router, tags=["User Subscriptions"])

app.include_router(admin_users_router, tags=["Admin - Users"])
app.include_router(admin_stats_router, tags=["Admin - Stats"])
app.include_router(admin_subscriptions_router, tags=["Admin - Subscriptions"])
app.include_router(admin_activity_router, tags=["Admin - Activity"])
app.include_router(admin_workflows_router, tags=["Admin - Workflows"])

# Terminal API (FASE 1.3)
app.include_router(terminal_router, tags=["Terminal"])

# KV1NT Dashboard (FASE 2.2)
app.include_router(kv1nt_router, tags=["KV1NT Dashboard"])

# CKC Control Panel (v1.3.3 - CKC Bridge Integration)
app.include_router(ckc_router, prefix="/api/ckc", tags=["CKC Control Panel"])

# CKC Folder Switcher (v1.3.5 - Super Admin Folder Navigation)
app.include_router(ckc_folder_router, prefix="/api/ckc", tags=["CKC Folder Switcher"])

# Phase B7: Cross-Platform Navigation
try:
    from cirkelline.endpoints.cross_platform_auth import router as cross_platform_router
    app.include_router(cross_platform_router, prefix="/auth", tags=["Cross-Platform Auth"])
    logger.info("✅ Cross-Platform Auth API loaded (/auth/*)")
except ImportError as e:
    logger.warning(f"⚠️ Cross-Platform Auth not available: {e}")

logger.info("✅ All extracted routers registered with FastAPI app")

# Custom /config endpoint - MUST be before AgentOS creation
@app.get("/config")
async def health_check():
    """Health check endpoint for ALB target group"""
    return {
        "status": "healthy",
        "service": "cirkelline-system-backend",
        "version": "1.3.3",
        "gateway": "connected" if gateway_client.is_configured else "not_configured"
    }
logger.info("✅ Health check endpoint /config configured")

@app.get("/api/gateway/status")
async def gateway_status():
    """Check connection status to CKC Gateway."""
    try:
        platforms = await gateway_client.get_platforms()
        if platforms:
            return {
                "connected": True,
                "gateway_url": gateway_client.gateway_url,
                "platform_code": gateway_client.platform_code,
                "available_platforms": len(platforms),
                "platforms": platforms,
                "status": "operational"
            }
        else:
            return {
                "connected": False,
                "gateway_url": gateway_client.gateway_url,
                "error": "No platforms returned"
            }
    except Exception as e:
        return {
            "connected": False,
            "gateway_url": gateway_client.gateway_url,
            "error": str(e)
        }
logger.info("✅ Gateway status endpoint /api/gateway/status configured")

# TEMPORARY: Database migration endpoint to fix agno_memories schema
@app.post("/admin/fix-memory-schema")
async def fix_memory_schema():
    """Fix agno_memories created_at column type from TIMESTAMP to BIGINT"""
    try:
        from sqlalchemy import text, create_engine
        import os

        db_url = os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with engine.connect() as conn:
            # Get current schema
            result = conn.execute(text("""
                SELECT column_name, data_type FROM information_schema.columns
                WHERE table_schema = 'ai' AND table_name = 'agno_memories'
                ORDER BY ordinal_position
            """))
            before = {row[0]: row[1] for row in result.fetchall()}

            # Only fix created_at - it's the problematic one
            if before.get('created_at') == 'timestamp with time zone':
                conn.execute(text("ALTER TABLE ai.agno_memories ALTER COLUMN created_at DROP DEFAULT"))
                conn.execute(text("""
                    ALTER TABLE ai.agno_memories
                    ALTER COLUMN created_at TYPE bigint
                    USING EXTRACT(EPOCH FROM created_at)::bigint
                """))
                conn.commit()
                return {"status": "created_at_fixed", "before": before}
            else:
                return {"status": "already_ok", "schema": before}

    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "trace": traceback.format_exc()}

logger.info("✅ Database migration endpoint /admin/fix-memory-schema configured")

# Knowledge base
knowledge = Knowledge(
    name="Cirkelline Knowledge Base",
    description="Information about the Cirkelline project",
    contents_db=db,
    vector_db=vector_db,
)

# Async knowledge loading function (for future use)
async def load_knowledge_async():
    """
    Load knowledge base asynchronously at startup.
    Uncomment the code below when you have documents to load.
    """
    try:
        logger.info("Loading knowledge base asynchronously...")

        # Example: Add documentation
        # await knowledge.add_content_async(
        #     name="Cirkelline Documentation",
        #     path="docs/",
        #     metadata={"type": "documentation", "version": "1.0"}
        # )

        # Example: Add from URL
        # await knowledge.add_content_async(
        #     name="API Reference",
        #     url="https://example.com/api-docs.pdf",
        #     metadata={"type": "reference"}
        # )

        # Load into vector database
        # await knowledge.aload(recreate=False)

        logger.info("Knowledge base loaded successfully")
    except Exception as e:
        logger.error(f"Error loading knowledge: {e}")

# Uncomment to load knowledge at startup:
# import asyncio
# asyncio.run(load_knowledge_async())


# ════════════════════════════════════════════════════════════════



# STAGE 2: CONFIGURE MIDDLEWARES ON APP (before AgentOS)
# ════════════════════════════════════════════════════════════════

# Import middleware dependencies
from agno.os.middleware import JWTMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

# Import custom middleware classes from modularized code
from cirkelline.middleware.middleware import (
    SessionsDateFilterMiddleware,
    AnonymousUserMiddleware,
    SessionLoggingMiddleware,
    RateLimitMiddleware
)

# Import gateway authentication middleware (Phase B2: CKC Gateway Integration)
from cirkelline.middleware.gateway_middleware import (
    GatewayAuthMiddleware,
    StrictGatewayAuthMiddleware
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://cirkelline-system-ui.vercel.app",
        "https://cirkelline-system-ui-*.vercel.app",  # For preview deployments
        "https://cirkelline.com",
        "https://www.cirkelline.com",
        "https://api.cirkelline.com",  # Backend domain (for CORS preflight)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware (ORDER IS CRITICAL - see docs/MIDDLEWARE-FLOW-DIAGRAM.md)
# Execution order: SessionsDateFilter → Anonymous → SessionLogging → GatewayAuth → JWT (from AGNO)
app.add_middleware(SessionLoggingMiddleware)
app.add_middleware(AnonymousUserMiddleware)
app.add_middleware(SessionsDateFilterMiddleware)

# Add Gateway Authentication Middleware (Phase B2: CKC Gateway Integration - 2026-01-16)
# Validates tokens against CKC Gateway (lib-admin on port 7779)
# Sets user context in request.state for downstream use
# Falls back to local JWT validation if gateway unavailable
app.add_middleware(GatewayAuthMiddleware)

# Add JWT Middleware with proper configuration (was deleted during v1.2.30 modularization)
# This extracts user_id, session_id, and tier information from JWT tokens
app.add_middleware(
    JWTMiddleware,
    secret_key=os.getenv("JWT_SECRET_KEY"),
    algorithm="HS256",
    user_id_claim="user_id",
    session_id_claim="session_id",
    dependencies_claims=["user_name", "user_role", "user_type", "tier_slug", "tier_level"],
    validate=False
)

# Add Rate Limiting Middleware (runs FIRST - protects all endpoints)
# Added: 2025-12-14 for scalability to 1M users
app.add_middleware(RateLimitMiddleware, window_seconds=60)

logger.info("✅ Stage 2: All middleware registered (CORS + Custom + GatewayAuth + JWT + RateLimit configured)")
logger.info("✅ Phase B2: CKC Gateway Authentication Middleware Active")


from typing import Optional
from fastapi import Form
from fastapi.responses import StreamingResponse, JSONResponse
import json

# ════════════════════════════════════════════════════════════════
# INTELLIGENT SESSION NAMING HELPERS
# ════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════
# CUSTOM ENDPOINT WITH KNOWLEDGE FILTERING (before AgentOS)
# ════════════════════════════════════════════════════════════════


logger.info("✅ Stage 3: Custom Cirkelline endpoint with dynamic stream handling")

# ════════════════════════════════════════════════════════════════
# HEALTH CHECK ENDPOINT FOR ALB
# ════════════════════════════════════════════════════════════════

# NOTE: /config endpoint registered AFTER AgentOS initialization (see line ~320)

# ════════════════════════════════════════════════════════════════
# STAGE 4: CREATE AGENTOS WITH base_app PARAMETER
# ════════════════════════════════════════════════════════════════

try:
    # DEBUG: AgentOS initialization progress (only shown when AGNO_DEBUG=true)
    if os.getenv('AGNO_DEBUG', 'false').lower() == 'true':
        print("=" * 80)
        print("DEBUG: Starting Stage 4 - AgentOS initialization")
        print("=" * 80)
    logger.info("Stage 4: Starting AgentOS initialization...")

    if os.getenv('AGNO_DEBUG', 'false').lower() == 'true':
        print("DEBUG: Stage 4.1 - Verifying agents exist...")
        print(f"  - audio_agent: {type(audio_agent).__name__}")
        print(f"  - video_agent: {type(video_agent).__name__}")
        print(f"  - image_agent: {type(image_agent).__name__}")
        print(f"  - document_agent: {type(document_agent).__name__}")
    logger.info("Stage 4.1: All specialist agents verified")

    if os.getenv('AGNO_DEBUG', 'false').lower() == 'true':
        print("DEBUG: Stage 4.2 - Verifying teams exist...")
        print(f"  - cirkelline team: {type(cirkelline).__name__}")
        print(f"  - research_team: {type(research_team).__name__}")
        print(f"  - law_team: {type(law_team).__name__}")
    logger.info("Stage 4.2: All teams verified")

    if os.getenv('AGNO_DEBUG', 'false').lower() == 'true':
        print("DEBUG: Stage 4.3 - Creating AgentOS instance...")
    logger.info("Stage 4.3: Creating AgentOS with base_app...")

    agent_os = AgentOS(
        id="cirkelline-v1",
        description="Cirkelline Multi-Agent System with Orchestrating Team",
        agents=[
            audio_agent,
            video_agent,
            image_agent,
            document_agent,
        ],
        teams=[
            cirkelline,
            research_team,
            law_team,
        ],
        base_app=app,  # ← Use our pre-configured app with middlewares and custom endpoint
        on_route_conflict="preserve_base_app",  # ← Keep our custom endpoint, don't override it
    )

    if os.getenv('AGNO_DEBUG', 'false').lower() == 'true':
        print("DEBUG: Stage 4.4 - AgentOS instance created successfully")
    logger.info("Stage 4.4: AgentOS instance created")

    if os.getenv('AGNO_DEBUG', 'false').lower() == 'true':
        print("DEBUG: Stage 4.5 - Getting app from AgentOS...")
    # Get the app (should return the same app instance we created)
    app = agent_os.get_app()

    if os.getenv('AGNO_DEBUG', 'false').lower() == 'true':
        print("DEBUG: Stage 4.6 - App retrieved successfully")
    logger.info("✅ Stage 4: AgentOS configured with base_app parameter")
    if os.getenv('AGNO_DEBUG', 'false').lower() == 'true':
        print("=" * 80)
        print("DEBUG: Stage 4 completed successfully!")
        print("=" * 80)

except Exception as e:
    print("=" * 80)
    print(f"❌ STAGE 4 CRASH: {type(e).__name__}: {str(e)}")
    print("=" * 80)
    logger.error(f"STAGE 4 CRASH: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    logger.error(traceback.format_exc())
    raise

# ════════════════════════════════════════════════════════════════
# CUSTOM API ENDPOINTS (after AgentOS)
# ════════════════════════════════════════════════════════════════






# ════════════════════════════════════════════════════════════════
# GOOGLE OAUTH HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════

async def refresh_google_token(user_id: str) -> bool:
    """
    Refresh expired Google access token using refresh token.

    Args:
        user_id: User ID to refresh tokens for

    Returns:
        True if refresh successful, False if failed or no refresh token

    This function:
    1. Retrieves encrypted tokens from database
    2. Decrypts the refresh token
    3. Uses Google OAuth2 to get new access token
    4. Encrypts and stores new access token
    5. Updates expiry time in database
    """
    try:
        from utils.encryption import decrypt_token, encrypt_token
        # Get current tokens from database
        with Session(_shared_engine) as session:
            result = session.execute(
                text("""
                    SELECT access_token, refresh_token, token_expiry
                    FROM google_tokens
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            row = result.fetchone()

            if not row:
                logger.warning(f"No Google tokens found for user {user_id}")
                return False

            # Decrypt refresh token
            encrypted_refresh = row[1]
            if not encrypted_refresh:
                logger.warning(f"No refresh token available for user {user_id}")
                return False

            refresh_token = decrypt_token(encrypted_refresh)

            # Use Google OAuth2 to refresh access token
            token_uri = "https://oauth2.googleapis.com/token"
            refresh_data = {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(token_uri, data=refresh_data)

                if response.status_code != 200:
                    logger.error(f"Token refresh failed: {response.text}")
                    return False

                token_data = response.json()
                new_access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)  # Default 1 hour

                # Encrypt new access token
                encrypted_access = encrypt_token(new_access_token)

                # Calculate new expiry time
                new_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

                # Update database with new access token and expiry
                session.execute(
                    text("""
                        UPDATE google_tokens
                        SET access_token = :access_token,
                            token_expiry = :expiry,
                            updated_at = :updated_at
                        WHERE user_id = :user_id
                    """),
                    {
                        "access_token": encrypted_access,
                        "expiry": new_expiry,
                        "updated_at": datetime.utcnow(),
                        "user_id": user_id
                    }
                )
                session.commit()

                logger.info(f"✅ Successfully refreshed Google token for user {user_id}")
                return True

    except Exception as e:
        logger.error(f"Error refreshing Google token: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def get_user_google_credentials(user_id: str):
    """
    Get decrypted Google credentials for user (for AGNO toolkit use).

    Args:
        user_id: User ID to get credentials for

    Returns:
        google.oauth2.credentials.Credentials object or None if not found

    This function:
    1. Retrieves tokens from database
    2. Checks if access token is expired
    3. Auto-refreshes if needed
    4. Decrypts tokens
    5. Returns Credentials object for AGNO tools (Gmail, Calendar, Sheets)
    """
    try:
        from utils.encryption import decrypt_token
        # Get tokens from database
        with Session(_shared_engine) as session:
            result = session.execute(
                text("""
                    SELECT access_token, refresh_token, token_expiry, scopes
                    FROM google_tokens
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            row = result.fetchone()

            if not row:
                logger.warning(f"No Google credentials found for user {user_id}")
                return None

            encrypted_access = row[0]
            encrypted_refresh = row[1]
            token_expiry = row[2]
            scopes = row[3]

            # Check if token is expired (with 5-minute buffer)
            if token_expiry:
                buffer_time = datetime.utcnow() + timedelta(minutes=5)
                if token_expiry < buffer_time:
                    logger.info(f"Access token expired, auto-refreshing for user {user_id}")
                    refresh_success = await refresh_google_token(user_id)

                    if refresh_success:
                        # Re-fetch the updated tokens
                        result = session.execute(
                            text("""
                                SELECT access_token, refresh_token
                                FROM google_tokens
                                WHERE user_id = :user_id
                            """),
                            {"user_id": user_id}
                        )
                        row = result.fetchone()
                        encrypted_access = row[0]
                        encrypted_refresh = row[1]
                    else:
                        logger.warning(f"Failed to refresh expired token for user {user_id}")
                        return None

            # Decrypt tokens
            access_token = decrypt_token(encrypted_access)
            refresh_token = decrypt_token(encrypted_refresh) if encrypted_refresh else None

            # Create and return Credentials object
            from google.oauth2.credentials import Credentials

            # scopes is already an array from PostgreSQL, convert to list
            scopes_list = list(scopes) if scopes else []

            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GOOGLE_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
                scopes=scopes_list
            )

            logger.info(f"✅ Retrieved Google credentials for user {user_id}")
            return credentials

    except Exception as e:
        logger.error(f"Error getting Google credentials: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# ════════════════════════════════════════════════════════════════
# GOOGLE OAUTH ENDPOINTS
# ════════════════════════════════════════════════════════════════

# NOTION DYNAMIC DATABASE DISCOVERY HELPERS
# ════════════════════════════════════════════════════════════════

def get_database_schema(notion_client, database_id: str) -> dict:
    """
    Retrieve full schema for a Notion database

    Returns:
        {
            "id": "database-uuid",
            "title": "Database Title",
            "properties": {
                "Name": {"id": "prop-id", "type": "title", "name": "Name"},
                "Status": {"id": "prop-id", "type": "status", "name": "Status", "options": [...]},
                ...
            }
        }
    """
    try:
        db = notion_client.data_sources.retrieve(data_source_id=database_id)

        schema = {
            "id": db["id"],
            "title": "",
            "properties": {}
        }

        # Extract database title
        title_list = db.get("title", [])
        if title_list and len(title_list) > 0:
            schema["title"] = title_list[0].get("text", {}).get("content", "")

        # Extract property definitions
        for prop_name, prop_config in db.get("properties", {}).items():
            prop_type = prop_config.get("type")
            property_schema = {
                "id": prop_config.get("id"),
                "type": prop_type,
                "name": prop_name
            }

            # Include type-specific configuration
            if prop_type in ["select", "multi_select"]:
                options = prop_config.get(prop_type, {}).get("options", [])
                property_schema["options"] = [{"name": opt.get("name"), "color": opt.get("color")} for opt in options]

            elif prop_type == "status":
                status_config = prop_config.get("status", {})
                options = status_config.get("options", [])
                property_schema["options"] = [{"name": opt.get("name"), "color": opt.get("color")} for opt in options]
                property_schema["groups"] = status_config.get("groups", [])

            schema["properties"][prop_name] = property_schema

        return schema

    except Exception as e:
        logger.error(f"Error getting database schema for {database_id}: {e}")
        raise

def classify_database_type(schema: dict) -> str:
    """
    Attempt to identify database type from its properties

    Returns: 'tasks', 'projects', 'companies', 'documentation', or 'custom'
    """
    props = [p.lower() for p in schema["properties"].keys()]
    title = schema.get("title", "").lower()

    # Check database title first (most reliable)
    if "task" in title:
        return "tasks"
    elif "project" in title:
        return "projects"
    elif "compan" in title or "client" in title or "domain" in title:
        return "companies"
    elif "doc" in title or "knowledge" in title or "wiki" in title:
        return "documentation"

    # Fallback to property analysis
    # Tasks database indicators
    if any("task" in p for p in props) and any("status" in p for p in props):
        return "tasks"

    # Projects database indicators
    if any("project" in p for p in props) and any(("timeline" in p or "start" in p or "end" in p) for p in props):
        return "projects"

    # Companies database indicators
    if any(("company" in p or "domain" in p or "website" in p) for p in props) and any("industry" in p or "size" in p for p in props):
        return "companies"

    # Documentation database indicators
    if any(("doc" in p or "article" in p or "page" in p) for p in props) and any("category" in p or "tag" in p for p in props):
        return "documentation"

    return "custom"

def extract_property_value(prop_data: dict, prop_type: str):
    """
    Extract value from a Notion property based on its type

    Handles all 15+ Notion property types dynamically
    """
    if not prop_data or prop_data.get("type") != prop_type:
        return None

    try:
        # Title property
        if prop_type == "title":
            title_list = prop_data.get("title", [])
            if title_list and len(title_list) > 0:
                return title_list[0].get("text", {}).get("content", "")

        # Rich text property
        elif prop_type == "rich_text":
            text_list = prop_data.get("rich_text", [])
            if text_list and len(text_list) > 0:
                return text_list[0].get("text", {}).get("content", "")

        # Select property
        elif prop_type == "select":
            select_data = prop_data.get("select")
            if select_data:
                return select_data.get("name", "")

        # Multi-select property
        elif prop_type == "multi_select":
            return [item.get("name", "") for item in prop_data.get("multi_select", [])]

        # Status property
        elif prop_type == "status":
            status_data = prop_data.get("status")
            if status_data:
                return status_data.get("name", "")

        # Date property
        elif prop_type == "date":
            date_data = prop_data.get("date")
            if date_data:
                return date_data.get("start", "")

        # Checkbox property
        elif prop_type == "checkbox":
            return prop_data.get("checkbox", False)

        # Number property
        elif prop_type == "number":
            return prop_data.get("number")

        # URL property
        elif prop_type == "url":
            return prop_data.get("url", "")

        # Email property
        elif prop_type == "email":
            return prop_data.get("email", "")

        # Phone property
        elif prop_type == "phone_number":
            return prop_data.get("phone_number", "")

        # People property
        elif prop_type == "people":
            return [person.get("name", "") for person in prop_data.get("people", [])]

        # Files property
        elif prop_type == "files":
            return [file.get("name", "") for file in prop_data.get("files", [])]

        # Created/edited time
        elif prop_type in ["created_time", "last_edited_time"]:
            return prop_data.get(prop_type, "")

        # Created/edited by
        elif prop_type in ["created_by", "last_edited_by"]:
            user = prop_data.get(prop_type, {})
            return user.get("name", "")

    except Exception as e:
        logger.error(f"Error extracting property value for type {prop_type}: {e}")
        return None

    return None

def discover_and_store_user_databases_sync(user_id: str, access_token: str):
    """
    Discover all Notion databases for a user and store them in notion_user_databases table

    This function:
    1. Searches for all databases using Notion Search API
    2. Retrieves schema for each database
    3. Auto-classifies database type
    4. Stores in database registry

    Uses synchronous version for compatibility with existing code
    """
    try:
        from notion_client import Client
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session
        import json

        notion = Client(auth=access_token)

        logger.info(f"🔍 Starting database discovery for user {user_id[:8]}...")

        # Step 1: Search for all databases (use "data_source" for API v2025-09-03)
        databases = []
        start_cursor = None
        discovered_count = 0

        while True:
            try:
                search_params = {
                    "filter": {"property": "object", "value": "data_source"},
                    "page_size": 100
                }
                if start_cursor:
                    search_params["start_cursor"] = start_cursor

                response = notion.search(**search_params)

                for result in response.get("results", []):
                    if result.get("object") == "data_source":
                        db_id = result["id"]
                        title_list = result.get("title", [])
                        db_title = title_list[0].get("text", {}).get("content", "Untitled") if title_list else "Untitled"

                        databases.append({
                            "id": db_id,
                            "title": db_title,
                            "url": result.get("url", ""),
                            "created_time": result.get("created_time", ""),
                            "last_edited_time": result.get("last_edited_time", "")
                        })
                        discovered_count += 1

                # Handle pagination
                if not response.get("has_more", False):
                    break
                start_cursor = response.get("next_cursor")

            except Exception as e:
                logger.error(f"Error during search iteration: {e}")
                break

        logger.info(f"📊 Discovered {discovered_count} databases")

        # Step 2: Get schema for each database and store
        engine = create_engine(os.getenv("DATABASE_URL"))

        with Session(engine) as session:
            stored_count = 0

            for db in databases:
                try:
                    # Get full schema
                    schema = get_database_schema(notion, db["id"])

                    # Classify database type
                    db_type = classify_database_type(schema)

                    # Extract property order with Name/title first for better UX
                    properties = schema.get("properties", {})
                    property_keys = list(properties.keys())

                    # Find the title property (usually "Name")
                    title_property = None
                    for prop_name, prop_config in properties.items():
                        if prop_config.get("type") == "title":
                            title_property = prop_name
                            break

                    # Put title first, then the rest in Notion's original order
                    if title_property and title_property in property_keys:
                        property_order = [title_property] + [k for k in property_keys if k != title_property]
                    else:
                        property_order = property_keys

                    logger.info(f"   ├─ {db['title'][:40]}: {db_type}")

                    # Store in database registry with property order
                    session.execute(
                        text("""
                            INSERT INTO notion_user_databases
                            (user_id, database_id, database_title, database_type, schema, property_order, last_synced)
                            VALUES (:user_id, :database_id, :database_title, :database_type, CAST(:schema AS jsonb), CAST(:property_order AS jsonb), NOW())
                            ON CONFLICT (user_id, database_id)
                            DO UPDATE SET
                                database_title = EXCLUDED.database_title,
                                database_type = EXCLUDED.database_type,
                                schema = EXCLUDED.schema,
                                property_order = EXCLUDED.property_order,
                                last_synced = NOW()
                        """),
                        {
                            "user_id": user_id,
                            "database_id": db["id"],
                            "database_title": db["title"],
                            "database_type": db_type,
                            "schema": json.dumps(schema),
                            "property_order": json.dumps(property_order)
                        }
                    )
                    stored_count += 1

                except Exception as e:
                    logger.error(f"Error processing database {db['title']}: {e}")
                    continue

            session.commit()
            logger.info(f"✅ Stored {stored_count} databases in registry for user {user_id[:8]}")

        return {"success": True, "discovered": discovered_count, "stored": stored_count}

    except Exception as e:
        logger.error(f"❌ Error discovering databases for user {user_id[:8]}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

logger.info("✅ Notion dynamic database discovery helpers loaded")



async def activity_log_stream(request: Request, token: str = Query(...)):
    """
    SSE endpoint for real-time activity log updates.
    Streams new activity logs to connected admin clients as they happen.

    Note: Token is passed as query param because EventSource doesn't support custom headers.
    """
    # Verify admin access
    try:
        payload = pyjwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=["HS256"]
        )
        user_id = payload.get("user_id")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user_id or user_id.startswith("anon-"):
        raise HTTPException(status_code=401, detail="Authentication required")

    # Check if user is admin
    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        admin_check = session.execute(
            text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id LIMIT 1"),
            {"user_id": user_id}
        )
        is_admin = admin_check.fetchone() is not None

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Create queue for this client
    client_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    activity_log_clients.add(client_queue)

    async def event_generator():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"

            # Stream events to client
            while True:
                # Wait for new activity log
                log_data = await client_queue.get()

                # Send to client
                event_json = json.dumps({
                    'type': 'new_activity',
                    'data': log_data
                })
                yield f"data: {event_json}\n\n"

        except asyncio.CancelledError:
            # Client disconnected
            activity_log_clients.discard(client_queue)
            raise
        finally:
            # Cleanup
            activity_log_clients.discard(client_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

logger.info("✅ Activity logs SSE stream endpoint configured")

# ════════════════════════════════════════════════════════════════
# NOTE: Knowledge filtering is now applied at Team initialization level
# via knowledge_retriever parameter. No endpoint override needed.
# ════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════
# MIDDLEWARES CONFIGURED AT STAGE 2 (before AgentOS creation)
# ════════════════════════════════════════════════════════════════
# Middlewares are now registered on the app BEFORE AgentOS is created
# See Stage 2 section above for middleware configuration

if __name__ == "__main__":
    logger.info("═" * 50)
    logger.info("CIRKELLINE AGENTOS STARTING")
    logger.info("═" * 50)
    logger.info(f"Total Agents: {len(agent_os.agents)}")
    logger.info(f"Total Teams: {len(agent_os.teams)}")
    logger.info(f"Database: {db.db_url}")
    logger.info(f"Database: SQLAlchemy automatic pooling (pool_size=5, max_overflow=10 per worker)")
    logger.info(f"Workers: 1 process = 15 total connections available")

    # Check monitoring status with debugging
    agno_monitor_value = os.getenv("AGNO_MONITOR")
    logger.info(f"DEBUG - AGNO_MONITOR value: '{agno_monitor_value}'")

    if agno_monitor_value:
        monitoring_enabled = agno_monitor_value.lower().strip() == "true"
    else:
        logger.warning("AGNO_MONITOR not set in environment!")
        monitoring_enabled = False

    logger.info(f"Monitoring: {'ENABLED' if monitoring_enabled else 'DISABLED'}")
    logger.info(f"Session Summaries: ENABLED")
    logger.info(f"AWS Ready: 1 worker + listening on 0.0.0.0")
    logger.info("═" * 50)

    try:
        # Single-process uvicorn (no workers parameter = single process, no master/worker split)
        logger.info("Starting uvicorn in single-process mode...")
        uvicorn.run(
            app,                  # Pass app object directly for single-process mode
            host="0.0.0.0",       # Listen on all interfaces (required for AWS)
            port=7777,
            log_level="info",
            access_log=True,
            # NO workers parameter = single process mode (no master/worker split)
        )
    except KeyboardInterrupt:
        logger.info("Shutting down Cirkelline AgentOS...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise