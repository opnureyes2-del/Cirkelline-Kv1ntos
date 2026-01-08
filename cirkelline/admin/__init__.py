"""
Admin Module
============
Admin-only endpoints for system management.

Provides:
- User management (list users, get user details)
- System statistics (overall system stats)
- Subscription management (list subscriptions, assign tiers, subscription stats)
- Activity logging (activity logs, activity stream)
- Workflow management (list workflows, trigger runs, view stats)

Import routers to add to FastAPI app.
"""

from cirkelline.admin.users import router as admin_users_router
from cirkelline.admin.stats import router as admin_stats_router
from cirkelline.admin.subscriptions import router as admin_subscriptions_router
from cirkelline.admin.activity import router as admin_activity_router, broadcast_activity_log
from cirkelline.admin.workflows import router as admin_workflows_router

__all__ = [
    'admin_users_router',
    'admin_stats_router',
    'admin_subscriptions_router',
    'admin_activity_router',
    'broadcast_activity_log',
    'admin_workflows_router'
]
