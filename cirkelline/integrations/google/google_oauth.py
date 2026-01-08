"""
Google OAuth Helper Functions
==============================
Helper functions for Google OAuth2 token management and credentials retrieval.
"""

import os
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from google.oauth2.credentials import Credentials

from cirkelline.config import logger
from cirkelline.middleware.middleware import _shared_engine
from utils.encryption import decrypt_token, encrypt_token


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
                    error_text = response.text
                    logger.error(f"Token refresh failed: {error_text}")

                    # v1.3.4: Auto-delete permanently invalid tokens
                    # When Google returns invalid_grant, the token can never be refreshed
                    # Delete it so user sees "Not Connected" and can reconnect fresh
                    if 'invalid_grant' in error_text:
                        logger.error(f"🗑️ Token permanently invalid for {user_id} - deleting broken token")
                        session.execute(
                            text("DELETE FROM google_tokens WHERE user_id = :user_id"),
                            {"user_id": user_id}
                        )
                        session.commit()

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


logger.info("✅ Google OAuth helper functions loaded")
