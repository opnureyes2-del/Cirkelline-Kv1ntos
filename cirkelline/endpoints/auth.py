"""
Authentication & User Profile Endpoints
========================================
Handles user registration, login, profile management, and user statistics.
"""

import os
import json
import uuid
import time
import bcrypt
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import text

from cirkelline.config import logger
from cirkelline.models import SignupRequest, LoginRequest, ProfileUpdateRequest
from cirkelline.middleware.middleware import log_activity
from cirkelline.shared import (
    decode_jwt_token,
    generate_jwt_token,
    load_admin_profile,
    load_tier_info,
    get_db_session
)

# Create router
router = APIRouter()

# Admin emails for privilege checking
ADMIN_EMAILS = {
    "opnureyes2@gmail.com": "Ivo",
    "opnureyes2@gmail.com": "Rasmus",
    "test_admin@example.com": "Test Admin"  # FOR TESTING ONLY
}

# ═══════════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/api/auth/signup")
async def signup(request: Request, signup_data: SignupRequest):
    """User signup with password hashing and default tier subscription"""
    try:
        with get_db_session() as session:
            # Check if email already exists
            result = session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": signup_data.email}
            )
            existing_user = result.fetchone()

            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")

            # Hash password
            password_hash = bcrypt.hashpw(
                signup_data.password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            # Create user
            user_id = str(uuid.uuid4())
            result = session.execute(
                text("""
                    INSERT INTO users (id, email, hashed_password, display_name, created_at, updated_at)
                    VALUES (:id, :email, :hashed_password, :display_name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id, email, display_name
                """),
                {
                    "id": user_id,
                    "email": signup_data.email,
                    "hashed_password": password_hash,
                    "display_name": signup_data.display_name
                }
            )

            new_user = result.fetchone()
            session.commit()
            
            # Create default Member subscription for new user
            from services.tier_service import TierService
            from cirkelline.database import db
            from sqlalchemy import create_engine
            
            db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
            engine = create_engine(db_url)
            
            subscription_id, _ = await TierService.create_subscription(
                engine=engine,
                user_id=str(new_user[0]),
                tier_slug='member',
                billing_cycle='monthly'
            )
            
            logger.info(f"✅ Created Member subscription for new user {new_user[0]}")

            # Check if admin
            is_admin = signup_data.email in ADMIN_EMAILS
            
            # Load admin profile if admin
            admin_profile = None
            if is_admin:
                admin_profile = load_admin_profile(str(new_user[0]), session)
                if not admin_profile:
                    # Fallback admin profile
                    admin_profile = {
                        "name": ADMIN_EMAILS[signup_data.email],
                        "role": "CEO & Creator"
                    }
            
            # Load tier information
            tier_info = load_tier_info(str(new_user[0]), session)
            
            # Generate JWT
            token = generate_jwt_token(
                user_id=str(new_user[0]),
                email=new_user[1],
                display_name=new_user[2],
                is_admin=is_admin,
                admin_profile=admin_profile,
                tier_info=tier_info
            )

            logger.info(f"✅ User signed up: {new_user[1]} (admin={is_admin})")

            # Log successful signup
            await log_activity(
                request=request,
                user_id=str(new_user[0]),
                action_type="user_signup",
                success=True,
                status_code=200,
                is_admin=is_admin
            )

            return {
                "success": True,
                "token": token,
                "user": {
                    "id": str(new_user[0]),
                    "email": new_user[1],
                    "display_name": new_user[2],
                    "is_admin": is_admin
                }
            }

    except HTTPException as he:
        # Log failed signup attempt
        await log_activity(
            request=request,
            user_id="unknown",
            action_type="user_signup",
            success=False,
            status_code=he.status_code,
            error_message=he.detail,
            error_type="HTTPException"
        )
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Log error
        await log_activity(
            request=request,
            user_id="unknown",
            action_type="user_signup",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__
        )

        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.post("/api/auth/login")
async def login(request: Request, login_data: LoginRequest):
    """User login with password verification"""
    try:
        with get_db_session() as session:
            # Find user by email
            result = session.execute(
                text("""
                    SELECT id, email, hashed_password, display_name
                    FROM users
                    WHERE email = :email
                """),
                {"email": login_data.email}
            )
            user = result.fetchone()

            if not user:
                await log_activity(
                    request=request,
                    user_id="unknown",
                    action_type="user_login",
                    success=False,
                    status_code=401,
                    error_message="User not found",
                    error_type="AuthenticationError"
                )
                raise HTTPException(status_code=401, detail="Invalid email or password")

            # Verify password
            password_match = bcrypt.checkpw(
                login_data.password.encode('utf-8'),
                user[2].encode('utf-8')
            )

            if not password_match:
                await log_activity(
                    request=request,
                    user_id=str(user[0]),
                    action_type="user_login",
                    success=False,
                    status_code=401,
                    error_message="Invalid password",
                    error_type="AuthenticationError"
                )
                raise HTTPException(status_code=401, detail="Invalid password")

            # Update last_login timestamp
            session.execute(
                text("""
                    UPDATE users
                    SET last_login = NOW()
                    WHERE id = :user_id
                """),
                {"user_id": user[0]}
            )
            session.commit()

            # Check if admin
            is_admin = login_data.email in ADMIN_EMAILS
            
            # Load admin profile if admin
            admin_profile = None
            if is_admin:
                admin_profile = load_admin_profile(str(user[0]), session)
                if not admin_profile:
                    # Fallback admin profile
                    admin_profile = {
                        "name": ADMIN_EMAILS[login_data.email],
                        "role": "CEO & Creator"
                    }
            
            # Load tier information
            tier_info = load_tier_info(str(user[0]), session)
            
            # Generate JWT
            token = generate_jwt_token(
                user_id=str(user[0]),
                email=user[1],
                display_name=user[3],
                is_admin=is_admin,
                admin_profile=admin_profile,
                tier_info=tier_info
            )

            logger.info(f"✅ User logged in: {user[1]} (admin={is_admin})")

            # Log successful login
            await log_activity(
                request=request,
                user_id=str(user[0]),
                action_type="user_login",
                success=True,
                status_code=200,
                is_admin=is_admin
            )

            return {
                "success": True,
                "token": token,
                "user": {
                    "id": str(user[0]),
                    "email": user[1],
                    "display_name": user[3],
                    "is_admin": is_admin
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# USER PROFILE ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.patch("/api/user/profile")
async def update_user_profile(request: Request, profile_update: ProfileUpdateRequest):
    """Update user profile (display name, bio, location, job_title, instructions)"""
    
    # Decode JWT to get user_id
    try:
        payload = decode_jwt_token(request)
        user_id = payload.get("user_id")
        email = payload.get("email")
    except HTTPException:
        raise

    # Update database
    try:
        with get_db_session() as session:
            # Get current preferences
            result = session.execute(
                text("SELECT preferences FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            preferences = row[0] if row and row[0] else {}

            # Update preferences with new values
            if profile_update.bio is not None:
                preferences['bio'] = profile_update.bio
            if profile_update.location is not None:
                preferences['location'] = profile_update.location
            if profile_update.job_title is not None:
                preferences['job_title'] = profile_update.job_title
            if profile_update.instructions is not None:
                preferences['instructions'] = profile_update.instructions
                logger.info(f"📝 Saving custom instructions for user {user_id[:20]}... ({len(profile_update.instructions)} chars)")

            # Update user with display_name and preferences
            result = session.execute(
                text("""
                    UPDATE users
                    SET display_name = :name,
                        preferences = :prefs,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :user_id
                    RETURNING id, email, display_name
                """),
                {
                    "name": profile_update.display_name,
                    "prefs": json.dumps(preferences),
                    "user_id": user_id
                }
            )

            updated_user = result.fetchone()
            session.commit()

            if not updated_user:
                raise HTTPException(status_code=404, detail="User not found")

            # Check if admin
            is_admin = updated_user[1] in ADMIN_EMAILS
            
            # Load admin profile if admin
            admin_profile = None
            if is_admin:
                admin_profile = load_admin_profile(user_id, session)
                if not admin_profile:
                    admin_profile = {
                        "name": ADMIN_EMAILS.get(updated_user[1], updated_user[2]),
                        "role": "CEO & Creator"
                    }
            
            # Load tier information
            tier_info = load_tier_info(user_id, session)
            
            # Generate new JWT with updated info
            new_token = generate_jwt_token(
                user_id=str(updated_user[0]),
                email=updated_user[1],
                display_name=updated_user[2],
                is_admin=is_admin,
                admin_profile=admin_profile,
                tier_info=tier_info
            )

            logger.info(f"✅ Profile updated for user {user_id}")

            # Log successful profile update
            await log_activity(
                request=request,
                user_id=user_id,
                action_type="profile_update",
                success=True,
                status_code=200,
                details={
                    "display_name": profile_update.display_name,
                    "has_instructions": bool(profile_update.instructions)
                }
            )

            return {
                "success": True,
                "token": new_token,
                "user": {
                    "id": str(updated_user[0]),
                    "email": updated_user[1],
                    "display_name": updated_user[2]
                }
            }

    except HTTPException as he:
        # Log failed update
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="profile_update",
            success=False,
            status_code=he.status_code,
            error_message=he.detail,
            error_type="HTTPException"
        )
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Log error
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="profile_update",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__
        )

        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/api/user/statistics")
async def get_user_statistics(request: Request):
    """
    Get user statistics and profile data.
    Returns activity stats, preferences, and profile fields.
    """
    # Decode JWT to get user_id
    try:
        payload = decode_jwt_token(request)
        user_id = payload.get("user_id")
        email = payload.get("email")
    except HTTPException:
        raise

    try:
        with get_db_session() as session:
            # Get user data and preferences
            user_result = session.execute(
                text("SELECT created_at, preferences FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            user_row = user_result.fetchone()
            
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            created_at = user_row[0]
            preferences = user_row[1] if user_row[1] else {}

            # Calculate member since days
            now = datetime.now(timezone.utc)
            if created_at.tzinfo is None:
                created_aware = created_at.replace(tzinfo=timezone.utc)
            else:
                created_aware = created_at
            member_since_days = (now - created_aware).days

            # Get statistics from database
            stats_result = session.execute(
                text("""
                    SELECT
                        COUNT(DISTINCT session_id) as conversations,
                        COUNT(*) as messages_sent
                    FROM ai.agno_sessions
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            stats_row = stats_result.fetchone()

            # Get document count
            docs_result = session.execute(
                text("""
                    SELECT COUNT(*) FROM ai.agno_knowledge
                    WHERE metadata->>'user_id' = :user_id
                """),
                {"user_id": user_id}
            )
            doc_count = docs_result.scalar()

            # Get memory count
            memory_result = session.execute(
                text("SELECT COUNT(*) FROM ai.agno_memories WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            memory_count = memory_result.scalar()

            # Check Google connection
            google_result = session.execute(
                text("SELECT 1 FROM google_tokens WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            has_google = google_result.fetchone() is not None

            return {
                "success": True,
                "user_id": user_id,
                "email": email,
                "created_at": created_at.isoformat(),
                "member_since_days": member_since_days,
                "statistics": {
                    "conversations_started": stats_row[0] or 0,
                    "messages_sent": stats_row[1] or 0,
                    "messages_received": stats_row[1] or 0,  # Same as sent for now
                    "documents_uploaded": doc_count or 0,
                    "memories_captured": memory_count or 0,
                    "last_active": int(datetime.now().timestamp()),
                    "favorite_theme": preferences.get('theme', 'light'),
                    "favorite_accent": preferences.get('accentColor', 'blue')
                },
                "profile": {
                    "bio": preferences.get('bio', ''),
                    "location": preferences.get('location', ''),
                    "job_title": preferences.get('job_title', ''),
                    "instructions": preferences.get('instructions', '')
                },
                "connected_services": {
                    "google": has_google,
                    "microsoft": False,
                    "github": False,
                    "discord": False
                },
                "recent_activity": []  # Placeholder for now
            }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Statistics fetch error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")


@router.get("/api/user/preferences")
async def get_user_preferences(request: Request):
    """Get user preferences"""
    
    # Decode JWT to get user_id
    try:
        payload = decode_jwt_token(request)
        user_id = payload.get("user_id")
    except HTTPException:
        raise

    try:
        with get_db_session() as session:
            result = session.execute(
                text("SELECT preferences FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            preferences = row[0] if row and row[0] else {}

            return {
                "success": True,
                "preferences": preferences
            }

    except Exception as e:
        logger.error(f"Preferences fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


logger.info("✅ Auth and user profile endpoints loaded")
