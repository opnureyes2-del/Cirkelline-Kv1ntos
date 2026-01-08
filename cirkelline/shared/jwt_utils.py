"""
JWT Utilities
=============
Helper functions for JWT token generation and verification.
"""

import os
import time
import jwt as pyjwt
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from cirkelline.config import logger


def generate_jwt_token(
    user_id: str,
    email: str,
    display_name: str,
    is_admin: bool = False,
    admin_profile: Optional[Dict[str, Any]] = None,
    tier_info: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate JWT token with user information and tier data.
    
    Args:
        user_id: User's unique identifier
        email: User's email address
        display_name: User's display name
        is_admin: Whether user is an admin
        admin_profile: Admin profile data (name, role) if applicable
        tier_info: Tier information (tier_slug, tier_level, status)
    
    Returns:
        Encoded JWT token string
    """
    jwt_payload = {
        "user_id": user_id,
        "email": email,
        "display_name": display_name,
        "iat": int(time.time()),
        "exp": int(time.time()) + (7 * 24 * 60 * 60)  # 7 days
    }
    
    if is_admin and admin_profile:
        jwt_payload.update({
            "user_name": admin_profile.get("name", display_name),
            "user_role": admin_profile.get("role", "CEO & Creator"),
            "user_type": "Admin",
            "is_admin": True,
            "admin_name": admin_profile.get("name", display_name),
            "admin_role": admin_profile.get("role", "CEO & Creator")
        })
    elif is_admin:
        # Fallback if no profile
        jwt_payload.update({
            "user_name": display_name,
            "user_role": "CEO & Creator",
            "user_type": "Admin",
            "is_admin": True,
            "admin_name": display_name,
            "admin_role": "CEO & Creator"
        })
    else:
        jwt_payload.update({
            "user_name": display_name,
            "user_role": "User",
            "user_type": "Regular",
            "is_admin": False
        })
    
    # Add tier information
    if tier_info:
        jwt_payload.update({
            "tier_slug": tier_info.get("tier_slug", "member"),
            "tier_level": tier_info.get("tier_level", 1),
            "subscription_status": tier_info.get("status", "active")
        })
    else:
        # Default tier
        jwt_payload.update({
            "tier_slug": "member",
            "tier_level": 1,
            "subscription_status": "active"
        })
    
    # Sign JWT
    token = pyjwt.encode(
        jwt_payload,
        os.getenv("JWT_SECRET_KEY"),
        algorithm="HS256"
    )
    
    return token


def decode_jwt_token(request: Request) -> Dict[str, Any]:
    """
    Decode and verify JWT token from request Authorization header.
    
    Args:
        request: FastAPI Request object
    
    Returns:
        Dictionary containing decoded JWT payload
    
    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    auth_header = request.headers.get("authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated - Missing or invalid Authorization header"
        )
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    try:
        payload = pyjwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=["HS256"]
        )
        return payload
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except pyjwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )


def load_admin_profile(user_id: str, session: Session) -> Optional[Dict[str, Any]]:
    """
    Load admin profile from database.
    
    Args:
        user_id: User's unique identifier
        session: SQLAlchemy session
    
    Returns:
        Dictionary with admin profile data or None if not found
    """
    try:
        result = session.execute(
            text("""
                SELECT name, role, personal_context, preferences, custom_instructions
                FROM admin_profiles
                WHERE user_id = :user_id
            """),
            {"user_id": user_id}
        )
        row = result.fetchone()
        
        if row:
            return {
                "name": row[0],
                "role": row[1],
                "personal_context": row[2],
                "preferences": row[3],
                "custom_instructions": row[4]
            }
        return None
    except Exception as e:
        logger.error(f"Error loading admin profile: {e}")
        return None


def load_tier_info(user_id: str, session: Session) -> Dict[str, Any]:
    """
    Load user's subscription tier information.
    
    Args:
        user_id: User's unique identifier
        session: SQLAlchemy session
    
    Returns:
        Dictionary with tier information (tier_slug, tier_level, status)
    """
    try:
        result = session.execute(
            text("""
                SELECT s.tier_slug, t.tier_level, s.status
                FROM user_subscriptions s
                JOIN user_tiers t ON s.tier_slug = t.slug
                WHERE s.user_id = :user_id AND s.status = 'active'
                LIMIT 1
            """),
            {"user_id": user_id}
        )
        row = result.fetchone()
        
        if row:
            return {
                "tier_slug": row[0],
                "tier_level": row[1],
                "status": row[2]
            }
        else:
            # Default to member tier
            return {
                "tier_slug": "member",
                "tier_level": 1,
                "status": "active"
            }
    except Exception as e:
        logger.error(f"Error loading tier info: {e}")
        # Return default tier on error
        return {
            "tier_slug": "member",
            "tier_level": 1,
            "status": "active"
        }


logger.info("✅ JWT utilities module loaded")
