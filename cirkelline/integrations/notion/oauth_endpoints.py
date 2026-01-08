"""
Notion OAuth Endpoints
======================
OAuth flow endpoints for Notion workspace connection/disconnection.
"""

import os
import base64
import requests
import jwt as pyjwt
from datetime import datetime
from urllib.parse import urlencode
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cirkelline.config import logger
from cirkelline.database import db
from cirkelline.middleware.middleware import _shared_engine
from utils.encryption import encrypt_token
from cirkelline.integrations.notion.notion_helpers import discover_and_store_user_databases_sync

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# NOTION OAUTH START ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/oauth/notion/start")
async def notion_oauth_start(request: Request, token: str = None):
    """
    Start Notion OAuth flow - redirects user to Notion authorization

    Frontend calls this with JWT token as query parameter.
    Redirects user directly to Notion consent screen.

    Notion OAuth flow:
    1. Build authorization URL with client_id, redirect_uri, and state
    2. Redirect user to Notion authorization page
    3. User grants permissions to their workspace
    4. Notion redirects back to callback with authorization code
    """
    try:
        # Decode JWT from query parameter (not middleware)
        if not token:
            raise HTTPException(status_code=401, detail="Token required")

        jwt_secret = os.getenv("JWT_SECRET_KEY")
        try:
            payload = pyjwt.decode(token, jwt_secret, algorithms=["HS256"])
            user_id = payload.get('user_id')
        except Exception as e:
            logger.error(f"JWT decode error: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        # Get Notion OAuth credentials from environment
        client_id = os.getenv("NOTION_CLIENT_ID")
        client_secret = os.getenv("NOTION_CLIENT_SECRET")
        redirect_uri = os.getenv("NOTION_REDIRECT_URI")

        if not all([client_id, client_secret, redirect_uri]):
            logger.error("Notion OAuth credentials not configured")
            raise HTTPException(
                status_code=500,
                detail="Notion OAuth not configured on server"
            )

        # Use user_id as state parameter for CSRF protection
        state = user_id

        # Build Notion authorization URL
        # https://developers.notion.com/docs/authorization#step-1-navigate-the-user-to-the-integrations-authorization-url
        auth_params = {
            'client_id': client_id,
            'response_type': 'code',
            'owner': 'user',  # Request user-level access
            'redirect_uri': redirect_uri,
            'state': state
        }

        authorization_url = f"https://api.notion.com/v1/oauth/authorize?{urlencode(auth_params)}"

        logger.info(f"✅ Redirecting user {user_id[:20]}... to Notion OAuth")

        # Redirect user to Notion authorization page
        return RedirectResponse(url=authorization_url, status_code=302)

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Notion OAuth start error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to start Notion OAuth flow: {str(e)}")

logger.info("✅ Notion OAuth start endpoint configured")

@router.get("/api/oauth/notion/callback")
async def notion_oauth_callback(request: Request, code: str, state: str = None, error: str = None):
    """
    Handle Notion OAuth callback - exchanges authorization code for access token

    Notion redirects here after user grants permissions.
    We exchange the authorization code for an access token and store it encrypted.

    Notion OAuth callback flow:
    1. Receive authorization code and state from Notion
    2. Exchange code for access token via POST to Notion token endpoint
    3. Get workspace information from token response
    4. Encrypt access token with AES-256-GCM
    5. Store in notion_tokens table
    6. Redirect user back to frontend with success indicator
    """
    try:
        # Check for authorization errors
        if error:
            logger.error(f"Notion OAuth error: {error}")
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            return RedirectResponse(url=f"{frontend_url}/?notion=error&reason={error}", status_code=302)

        # Get user_id from state parameter (NOT JWT - Notion doesn't send JWT)
        user_id = state

        if not user_id:
            raise HTTPException(status_code=400, detail="State parameter (user_id) missing")

        if not code:
            raise HTTPException(status_code=400, detail="Authorization code missing")

        # Get Notion OAuth credentials
        client_id = os.getenv("NOTION_CLIENT_ID")
        client_secret = os.getenv("NOTION_CLIENT_SECRET")
        redirect_uri = os.getenv("NOTION_REDIRECT_URI")

        if not all([client_id, client_secret, redirect_uri]):
            raise HTTPException(status_code=500, detail="Notion OAuth not configured")

        # Exchange authorization code for access token
        # https://developers.notion.com/docs/authorization#step-2-notion-redirects-the-user-back-to-your-server
        token_url = "https://api.notion.com/v1/oauth/token"

        # Notion uses Basic Auth with client_id:client_secret
        auth_string = f"{client_id}:{client_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        token_response = requests.post(
            token_url,
            headers={
                'Authorization': f'Basic {encoded_auth}',
                'Content-Type': 'application/json'
            },
            json={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri
            }
        )

        if token_response.status_code != 200:
            logger.error(f"Notion token exchange failed: {token_response.status_code} - {token_response.text}")
            raise HTTPException(status_code=500, detail="Failed to exchange authorization code")

        token_data = token_response.json()

        # Extract token and workspace information
        access_token = token_data.get('access_token')
        workspace_id = token_data.get('workspace_id')
        workspace_name = token_data.get('workspace_name')
        workspace_icon = token_data.get('workspace_icon')
        bot_id = token_data.get('bot_id')
        owner = token_data.get('owner', {})
        owner_email = owner.get('user', {}).get('person', {}).get('email') if isinstance(owner.get('user'), dict) else None

        if not access_token:
            raise HTTPException(status_code=500, detail="Access token not received from Notion")

        # Encrypt access token before storing
        encrypted_access_token = encrypt_token(access_token)

        # Store in database using shared engine
        with Session(_shared_engine) as session:
            # Delete existing tokens for this user (UNIQUE constraint on user_id)
            session.execute(
                text("DELETE FROM notion_tokens WHERE user_id = :user_id"),
                {"user_id": user_id}
            )

            # Insert new tokens
            session.execute(
                text("""
                    INSERT INTO notion_tokens
                    (user_id, workspace_id, workspace_name, workspace_icon, access_token, bot_id, owner_email)
                    VALUES (:user_id, :workspace_id, :workspace_name, :workspace_icon, :access_token, :bot_id, :owner_email)
                """),
                {
                    "user_id": user_id,
                    "workspace_id": workspace_id,
                    "workspace_name": workspace_name,
                    "workspace_icon": workspace_icon,
                    "access_token": encrypted_access_token,
                    "bot_id": bot_id,
                    "owner_email": owner_email
                }
            )
            session.commit()

        logger.info(f"✅ Stored Notion tokens for user {user_id[:20]}... (Workspace: {workspace_name})")

        # 🔍 NEW: Discover and store user's Notion databases
        logger.info(f"🔍 Starting automatic database discovery for user {user_id[:20]}...")
        try:
            discovery_result = discover_and_store_user_databases_sync(user_id, access_token)
            if discovery_result.get("success"):
                logger.info(f"✅ Database discovery completed: {discovery_result.get('discovered')} found, {discovery_result.get('stored')} stored")
            else:
                logger.warning(f"⚠️ Database discovery had issues: {discovery_result.get('error')}")
        except Exception as discovery_error:
            # Don't fail OAuth flow if discovery fails - user can sync manually later
            logger.error(f"⚠️ Database discovery failed (non-critical): {discovery_error}")

        # Redirect back to frontend with success indicator
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        redirect_url = f"{frontend_url}/?notion=connected"

        return RedirectResponse(url=redirect_url, status_code=302)

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Notion OAuth callback error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to complete Notion OAuth: {str(e)}")

logger.info("✅ Notion OAuth callback endpoint configured")

@router.get("/api/oauth/notion/status")
async def notion_oauth_status(request: Request):
    """
    Check if user has connected Notion account

    Returns connection status and workspace information if available.
    Frontend uses this to display connection status indicator.
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get database connection
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            result = session.execute(
                text("""
                    SELECT workspace_name, workspace_icon, owner_email, created_at
                    FROM notion_tokens
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )

            row = result.fetchone()

            if row:
                return {
                    "connected": True,
                    "workspace_name": row[0],
                    "workspace_icon": row[1],
                    "owner_email": row[2],
                    "connected_at": row[3].isoformat() if row[3] else None
                }
            else:
                return {
                    "connected": False,
                    "workspace_name": None,
                    "workspace_icon": None,
                    "owner_email": None,
                    "connected_at": None
                }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Notion OAuth status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to check Notion connection status")

logger.info("✅ Notion OAuth status endpoint configured")

@router.post("/api/oauth/notion/disconnect")
async def notion_oauth_disconnect(request: Request):
    """
    Disconnect Notion account - deletes tokens from database

    Note: Notion doesn't provide a token revocation endpoint in their API.
    We simply delete the tokens from our database. User can reconnect later if needed.
    The integration will remain in their Notion workspace until manually removed.
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get database connection
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            # Check if user has Notion connected
            result = session.execute(
                text("""
                    SELECT workspace_name
                    FROM notion_tokens
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            row = result.fetchone()

            if not row:
                return {
                    "success": True,
                    "message": "No Notion workspace connected"
                }

            workspace_name = row[0]

            # Delete tokens from database
            session.execute(
                text("DELETE FROM notion_tokens WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            session.commit()

            logger.info(f"✅ Disconnected Notion workspace ({workspace_name}) for user {user_id[:20]}...")

            return {
                "success": True,
                "message": "Notion workspace disconnected successfully"
            }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Notion OAuth disconnect error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to disconnect Notion workspace")

logger.info("✅ Notion OAuth disconnect endpoint configured")


logger.info("✅ Notion OAuth endpoints loaded")
