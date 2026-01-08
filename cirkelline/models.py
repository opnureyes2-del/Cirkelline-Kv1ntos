"""
Cirkelline Pydantic Models Module
==================================
Request/response models for API endpoints.
"""

from pydantic import BaseModel
from typing import Optional

# ════════════════════════════════════════════════════════════════
# USER PROFILE MODELS
# ════════════════════════════════════════════════════════════════

class ProfileUpdateRequest(BaseModel):
    display_name: str
    bio: Optional[str] = None
    location: Optional[str] = None
    job_title: Optional[str] = None
    instructions: Optional[str] = None

# ════════════════════════════════════════════════════════════════
# AUTHENTICATION MODELS
# ════════════════════════════════════════════════════════════════

class SignupRequest(BaseModel):
    email: str
    password: str
    display_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

# ════════════════════════════════════════════════════════════════
# USER PREFERENCES MODELS
# ════════════════════════════════════════════════════════════════

class PreferencesUpdateRequest(BaseModel):
    theme: Optional[str] = None
    accentColor: Optional[str] = None
    sidebar: Optional[dict] = None
    bannerDismissed: Optional[bool] = None
    sidebarCollapsed: Optional[bool] = None
