"""
Google OAuth Endpoints
=======================
OAuth flow endpoints for Google account connection/disconnection.
"""

import os
import requests
import jwt as pyjwt
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow

from cirkelline.config import logger
from cirkelline.database import db
from cirkelline.middleware.middleware import _shared_engine
from utils.encryption import encrypt_token, decrypt_token

# Create router
router = APIRouter()

# Define required scopes for Gmail, Calendar, Sheets, and Tasks
GOOGLE_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# ═══════════════════════════════════════════════════════════════
# GOOGLE OAUTH START ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/oauth/google/start")
async def google_oauth_start(request: Request, token: str = None):
    """
    Start Google OAuth flow - redirects user to Google authorization

    Frontend calls this with JWT token as query parameter.
    Redirects user directly to Google consent screen.
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

        # Get Google OAuth credentials from environment
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

        if not all([client_id, client_secret, redirect_uri]):
            logger.error("Google OAuth credentials not configured")
            raise HTTPException(
                status_code=500,
                detail="Google OAuth not configured on server"
            )

        # Create OAuth flow
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=GOOGLE_SCOPES
        )
        flow.redirect_uri = redirect_uri

        # Use user_id as state parameter for CSRF protection
        state = user_id

        # Generate authorization URL
        authorization_url, _ = flow.authorization_url(
            access_type='offline',  # Get refresh token
            include_granted_scopes='true',
            prompt='consent',  # Force consent screen to get refresh token
            state=state
        )

        logger.info(f"✅ Redirecting user {user_id[:20]}... to Google OAuth")

        # Redirect user to Google authorization page
        return RedirectResponse(url=authorization_url, status_code=302)

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"OAuth start error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth flow: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# GOOGLE OAUTH CALLBACK ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/oauth/google/callback")
async def google_oauth_callback(request: Request, code: str, state: str = None):
    """
    Handle OAuth callback from Google

    Google redirects here after user authorizes.
    Exchanges code for tokens and stores them encrypted in database.
    """
    try:
        # Get user_id from state parameter (not JWT - Google callback doesn't include JWT)
        # State was set to user_id in the start endpoint for CSRF protection
        user_id = state
        if not user_id:
            raise HTTPException(status_code=400, detail="State parameter missing")

        # Get Google OAuth credentials
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

        if not all([client_id, client_secret, redirect_uri]):
            raise HTTPException(status_code=500, detail="Google OAuth not configured")

        # Recreate flow (must match start endpoint)
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=GOOGLE_SCOPES
        )
        flow.redirect_uri = redirect_uri

        # Exchange authorization code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Encrypt tokens before storing
        encrypted_access_token = encrypt_token(credentials.token)
        encrypted_refresh_token = encrypt_token(credentials.refresh_token)

        # Calculate token expiry
        token_expiry = datetime.now() + timedelta(seconds=3600)  # Google tokens expire in 1 hour

        # Get user email from Google
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v1/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        user_email = user_info_response.json().get('email', '')

        # Store in database using shared engine
        with Session(_shared_engine) as session:
            # Delete existing tokens for this user (UNIQUE constraint on user_id)
            session.execute(
                text("DELETE FROM google_tokens WHERE user_id = :user_id"),
                {"user_id": user_id}
            )

            # Insert new tokens
            session.execute(
                text("""
                    INSERT INTO google_tokens
                    (user_id, access_token, refresh_token, token_expiry, scopes, email)
                    VALUES (:user_id, :access_token, :refresh_token, :token_expiry, :scopes, :email)
                """),
                {
                    "user_id": user_id,
                    "access_token": encrypted_access_token,
                    "refresh_token": encrypted_refresh_token,
                    "token_expiry": token_expiry,
                    "scopes": GOOGLE_SCOPES,
                    "email": user_email
                }
            )
            session.commit()

        logger.info(f"✅ Stored Google tokens for user {user_id[:20]}... ({user_email})")

        # Redirect back to frontend root with success indicator
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        redirect_url = f"{frontend_url}/?google=connected"

        return RedirectResponse(url=redirect_url, status_code=302)

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to complete OAuth: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# GOOGLE OAUTH STATUS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/oauth/google/status")
async def google_oauth_status(request: Request):
    """
    Check if user has connected Google account

    Returns connection status and connected email if available.
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Check database for existing tokens
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            result = session.execute(
                text("""
                    SELECT email, created_at, scopes
                    FROM google_tokens
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            row = result.fetchone()

            if row:
                return {
                    "connected": True,
                    "email": row[0],
                    "connected_at": row[1].isoformat() if row[1] else None,
                    "scopes": row[2]
                }
            else:
                return {
                    "connected": False,
                    "email": None
                }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"OAuth status check error: {e}")
        raise HTTPException(status_code=500, detail="Failed to check connection status")


# ═══════════════════════════════════════════════════════════════
# GOOGLE OAUTH DISCONNECT ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/api/oauth/google/disconnect")
async def google_oauth_disconnect(request: Request):
    """
    Disconnect Google account - revokes tokens and deletes from database

    User can reconnect later if needed.
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
            # Get current tokens
            result = session.execute(
                text("""
                    SELECT access_token, email
                    FROM google_tokens
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            row = result.fetchone()

            if not row:
                return {
                    "success": True,
                    "message": "No Google account connected"
                }

            # Decrypt access token for revocation
            try:
                access_token = decrypt_token(row[0])
                email = row[1]

                # Revoke the token with Google
                requests.post(
                    'https://oauth2.googleapis.com/revoke',
                    params={'token': access_token},
                    headers={'content-type': 'application/x-www-form-urlencoded'}
                )
                logger.info(f"Revoked Google token for {email}")
            except Exception as revoke_error:
                # Continue even if revocation fails (token might be expired)
                logger.warning(f"Token revocation failed (continuing): {revoke_error}")

            # Delete from database
            session.execute(
                text("DELETE FROM google_tokens WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            session.commit()

            logger.info(f"✅ Disconnected Google account for user {user_id[:20]}...")

            return {
                "success": True,
                "message": "Google account disconnected successfully"
            }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"OAuth disconnect error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to disconnect Google account")


logger.info("✅ Google OAuth endpoints loaded")
