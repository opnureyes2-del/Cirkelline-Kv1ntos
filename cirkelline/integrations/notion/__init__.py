"""
Notion Integration Module
=========================
Complete Notion workspace integration with OAuth and database management.

Provides:
- OAuth flow (connection, disconnection, status)
- Dynamic registry-based database endpoints (recommended)
- Legacy hardcoded database endpoints (deprecated)

Import all routers to add to FastAPI app.
"""

from cirkelline.integrations.notion.oauth_endpoints import router as notion_oauth_router
from cirkelline.integrations.notion.database_endpoints import router as notion_database_router
from cirkelline.integrations.notion.legacy_endpoints import router as notion_legacy_router

__all__ = [
    'notion_oauth_router',
    'notion_database_router',
    'notion_legacy_router'
]
