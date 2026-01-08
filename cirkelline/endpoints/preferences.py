"""
User Preferences Management Endpoints
======================================
Handles user preference updates (theme, sidebar, banner dismissal).
"""

import os
import json
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cirkelline.config import logger

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════

class PreferencesUpdateRequest(BaseModel):
    theme: Optional[str] = None
    accentColor: Optional[str] = None
    sidebar: Optional[dict] = None
    bannerDismissed: Optional[bool] = None
    sidebarCollapsed: Optional[bool] = None
    timezone: Optional[str] = None  # ✅ v1.2.33: User's browser timezone (e.g., "America/New_York")
    topbarIconsExpanded: Optional[bool] = None  # ✅ TopBar app icons expanded/collapsed state

# ═══════════════════════════════════════════════════════════════
# PREFERENCES UPDATE ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.patch("/api/user/preferences")
async def update_user_preferences(request: Request, preferences: PreferencesUpdateRequest):
    """Update user preferences (theme, accent color, sidebar state, etc.)"""

    # Get user_id from JWT middleware
    user_id = getattr(request.state, 'user_id', None)

    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Database connection
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        engine = create_engine(database_url)

        with Session(engine) as session:
            # Get current preferences
            result = session.execute(
                text("SELECT preferences FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            current_prefs = row[0] if row and row[0] else {}

            # Update with new preferences
            if preferences.theme is not None:
                current_prefs['theme'] = preferences.theme
            if preferences.accentColor is not None:
                current_prefs['accentColor'] = preferences.accentColor
            if preferences.sidebar is not None:
                current_prefs['sidebar'] = preferences.sidebar
            if preferences.bannerDismissed is not None:
                current_prefs['bannerDismissed'] = preferences.bannerDismissed
            if preferences.sidebarCollapsed is not None:
                current_prefs['sidebarCollapsed'] = preferences.sidebarCollapsed
            if preferences.timezone is not None:
                current_prefs['timezone'] = preferences.timezone  # ✅ v1.2.33: User timezone
            if preferences.topbarIconsExpanded is not None:
                current_prefs['topbarIconsExpanded'] = preferences.topbarIconsExpanded

            # Save back to database
            session.execute(
                text("UPDATE users SET preferences = :prefs WHERE id = :user_id"),
                {"prefs": json.dumps(current_prefs), "user_id": user_id}
            )
            session.commit()

            logger.info(f"✅ Preferences updated for user {user_id}: {current_prefs}")

            return {
                "success": True,
                "preferences": current_prefs
            }

    except Exception as e:
        logger.error(f"Preferences update error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

logger.info("✅ User preferences endpoint loaded")
