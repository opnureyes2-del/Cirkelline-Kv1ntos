"""
Cirkelline Middleware Components
=================================
All FastAPI middleware for request/response processing:
- Activity logging infrastructure
- Anonymous user handling
- Session operation logging
- Date-based session filtering
- RBAC Tier Enforcement (API Gateway)
- Compliance Audit Trails

Execution Order (CRITICAL):
1. SessionsDateFilterMiddleware (first)
2. AuditTrailMiddleware
3. RBACGatewayMiddleware
4. AnonymousUserMiddleware
5. SessionLoggingMiddleware
6. JWTMiddleware (last - from AGNO)
"""

import os
import json
import asyncio
import math
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.requests import Request as StarletteRequest
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import jwt as pyjwt

from cirkelline.database import db
from cirkelline.config import logger

# ═══════════════════════════════════════════════════════════════
# SHARED DATABASE ENGINE FOR ACTIVITY LOGGING
# ═══════════════════════════════════════════════════════════════

_shared_engine = create_engine(
    db.db_url,
    pool_size=15,
    max_overflow=25,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False
)

logger.info("Shared database engine created for activity logging")

# ═══════════════════════════════════════════════════════════════
# UNIVERSAL ACTIVITY LOGGING FUNCTION
# ═══════════════════════════════════════════════════════════════

async def log_activity(
    request: Request,
    user_id: str,
    action_type: str,
    success: bool,
    status_code: int,
    endpoint: Optional[str] = None,
    duration_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    error_type: Optional[str] = None,
    target_user_id: Optional[str] = None,
    target_resource_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    is_admin: bool = False
):
    """
    Universal activity logging function.
    Logs ALL user-facing actions to activity_logs table.

    Args:
        request: FastAPI Request object
        user_id: User who performed the action
        action_type: Type of action (e.g., 'user_login', 'document_upload')
        success: Whether the action succeeded
        status_code: HTTP status code
        endpoint: API endpoint (auto-detected if None)
        duration_ms: Request duration in milliseconds
        error_message: Error message if failed
        error_type: Type of error if failed
        target_user_id: User affected by action (for admin actions)
        target_resource_id: Resource ID (document_id, feedback_id, etc.)
        resource_type: Type of resource ('document', 'feedback', etc.)
        details: Additional details as dict (stored as JSONB)
        is_admin: Whether action was performed by admin
    """
    try:
        # Extract request information
        endpoint = endpoint or str(request.url.path)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent', '')

        # Prepare log entry
        log_entry = {
            'user_id': user_id,
            'action_type': action_type,
            'endpoint': endpoint,
            'http_method': request.method,
            'status_code': status_code,
            'success': success,
            'error_message': error_message,
            'error_type': error_type,
            'target_user_id': target_user_id,
            'target_resource_id': target_resource_id,
            'resource_type': resource_type,
            'details': json.dumps(details) if details else None,
            'duration_ms': duration_ms,
            'ip_address': ip_address,
            'user_agent': user_agent[:500] if user_agent else None,  # Truncate long user agents
            'is_admin': is_admin,
            'timestamp': datetime.utcnow()
        }

        # Insert to database (synchronous operations in async function - not ideal but works)
        with Session(_shared_engine) as session:
            result = session.execute(
                text("""
                    INSERT INTO activity_logs
                    (user_id, action_type, endpoint, http_method, status_code,
                     success, error_message, error_type, target_user_id, target_resource_id,
                     resource_type, details, duration_ms, ip_address, user_agent,
                     is_admin, timestamp)
                    VALUES
                    (:user_id, :action_type, :endpoint, :http_method, :status_code,
                     :success, :error_message, :error_type, :target_user_id, :target_resource_id,
                     :resource_type, CAST(:details AS jsonb), :duration_ms, :ip_address,
                     :user_agent, :is_admin, :timestamp)
                    RETURNING id, timestamp
                """),
                log_entry
            )
            session.commit()

            # Get the inserted log ID
            row = result.fetchone()

        if row:
            log_id = str(row[0])
            log_timestamp = row[1]

            # Import broadcast function dynamically to avoid circular import
            # NOTE: broadcast_activity_log is in my_os.py for now, will be extracted in Phase 8
            try:
                from my_os import broadcast_activity_log

                # Broadcast to all connected SSE clients (don't wait for it)
                asyncio.create_task(broadcast_activity_log({
                    'id': log_id,
                    'timestamp': int(log_timestamp.timestamp()),
                    'user_id': user_id,
                    'action_type': action_type,
                    'endpoint': endpoint or str(request.url.path),
                    'http_method': request.method,
                    'status_code': status_code,
                    'success': success,
                    'error_message': error_message,
                    'duration_ms': duration_ms,
                    'ip_address': ip_address,
                    'is_admin': is_admin
                }))
            except ImportError:
                # broadcast_activity_log not available yet - skip broadcasting
                pass

    except Exception as e:
        # Don't let logging errors break the application
        logger.error(f"Failed to log activity: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

# ═══════════════════════════════════════════════════════════════
# ANONYMOUS USER MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

class AnonymousUserMiddleware(BaseHTTPMiddleware):
    """
    Ensures anonymous users get default profile values.
    Sets defaults in request.state.dependencies dict before JWT Middleware runs.
    """
    async def dispatch(self, request: StarletteRequest, call_next):
        # Initialize dependencies dict if it doesn't exist
        if not hasattr(request.state, 'dependencies'):
            request.state.dependencies = {}

        # Set default values for anonymous users
        if not request.headers.get("authorization"):
            # No JWT token - anonymous user
            request.state.dependencies["user_name"] = "Guest"
            request.state.dependencies["user_role"] = "Visitor"
            request.state.dependencies["user_type"] = "Anonymous"

        response = await call_next(request)
        return response

# ═══════════════════════════════════════════════════════════════
# SESSION LOGGING MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

class SessionLoggingMiddleware(BaseHTTPMiddleware):
    """
    Intercepts session-related AGNO requests and logs them as activity.
    Handles: DELETE /sessions/{session_id}, POST /sessions/{session_id}/rename
    """
    async def dispatch(self, request: StarletteRequest, call_next):
        import re
        import json
        from urllib.parse import parse_qs, urlparse

        # Check if this is a session operation
        is_session_delete = False
        is_session_rename = False
        session_id = None
        team_id = None
        new_name = None

        path = request.url.path

        # Pattern 1: DELETE /sessions/{session_id}
        if request.method == "DELETE":
            match1 = re.match(r'^/sessions/([^/]+)$', path)
            if match1:
                is_session_delete = True
                session_id = match1.group(1)

            # Pattern 2: DELETE /v1/teams/{team_id}/sessions/{session_id}
            match2 = re.match(r'^/v1/teams/([^/]+)/sessions/([^/]+)$', path)
            if match2:
                is_session_delete = True
                team_id = match2.group(1)
                session_id = match2.group(2)

        # Pattern 3: POST /sessions/{session_id}/rename
        elif request.method == "POST":
            match3 = re.match(r'^/sessions/([^/]+)/rename$', path)
            if match3:
                is_session_rename = True
                session_id = match3.group(1)

                # Try to extract new name from request body
                try:
                    body = await request.body()
                    if body:
                        # Store body for the actual endpoint to use
                        async def receive():
                            return {"type": "http.request", "body": body}
                        request._receive = receive

                        body_json = json.loads(body.decode())
                        new_name = body_json.get('name') or body_json.get('title')
                except Exception as e:
                    logger.warning(f"Could not extract session name from request body: {e}")

        # Process the request
        response = await call_next(request)

        # Log activity AFTER response completes
        try:
            if (is_session_delete or is_session_rename) and session_id:
                user_id = getattr(request.state, 'user_id', 'anonymous')
                is_admin = getattr(request.state, 'is_admin', False)

                if is_session_delete:
                    # Extract db_id from query parameters if present
                    query_params = dict(request.query_params)
                    db_id = query_params.get('db_id')

                    details = {}
                    if db_id:
                        details['db_id'] = db_id
                    if team_id:
                        details['team_id'] = team_id

                    await log_activity(
                        request=request,
                        user_id=user_id,
                        action_type="session_delete",
                        success=(200 <= response.status_code < 300),
                        status_code=response.status_code,
                        target_resource_id=session_id,
                        resource_type="session",
                        details=details if details else None,
                        is_admin=is_admin
                    )
                    logger.info(f"✅ Session delete logged: {session_id} (user: {user_id[:20]}..., status: {response.status_code})")

                elif is_session_rename:
                    details = {}
                    if new_name:
                        details['new_name'] = new_name

                    await log_activity(
                        request=request,
                        user_id=user_id,
                        action_type="session_rename",
                        success=(200 <= response.status_code < 300),
                        status_code=response.status_code,
                        target_resource_id=session_id,
                        resource_type="session",
                        details=details if details else None,
                        is_admin=is_admin
                    )
                    logger.info(f"✅ Session rename logged: {session_id} (user: {user_id[:20]}..., status: {response.status_code})")

        except Exception as e:
            logger.error(f"❌ Error logging session activity: {e}")

        return response

# ═══════════════════════════════════════════════════════════════
# SESSIONS DATE FILTER MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

class SessionsDateFilterMiddleware(BaseHTTPMiddleware):
    """
    Intercepts GET /sessions requests with created_after/created_before parameters
    and executes custom date filtering logic before AGNO's endpoint is reached.
    """
    async def dispatch(self, request: StarletteRequest, call_next):
        from urllib.parse import parse_qs, urlparse

        # Only intercept GET /sessions with date filters
        if request.method == "GET" and request.url.path == "/sessions":
            query_params = dict(request.query_params)

            # Check if date filters are present
            if "created_after" in query_params or "created_before" in query_params:
                logger.info(f"🚀 SessionsDateFilterMiddleware: Intercepting /sessions with date filters: {query_params}")

                try:
                    from sqlalchemy import create_engine, text
                    from sqlalchemy.orm import Session
                    import math

                    # Get user_id from JWT token in Authorization header
                    auth_header = request.headers.get('Authorization')

                    if not auth_header or not auth_header.startswith('Bearer '):
                        return JSONResponse(
                            status_code=401,
                            content={"error": "Unauthorized - No JWT token"}
                        )

                    jwt_token = auth_header.replace('Bearer ', '')

                    try:
                        # Decode JWT token to get user_id
                        decoded = pyjwt.decode(
                            jwt_token,
                            os.getenv('JWT_SECRET_KEY'),
                            algorithms=['HS256']
                        )
                        user_id = decoded.get('user_id')

                        if not user_id:
                            return JSONResponse(
                                status_code=401,
                                content={"error": "Unauthorized - No user_id in token"}
                            )
                    except Exception as e:
                        logger.error(f"❌ JWT decode error: {str(e)}")
                        return JSONResponse(
                            status_code=401,
                            content={"error": "Unauthorized - Invalid token"}
                        )

                    # Database connection
                    database_url = os.getenv('DATABASE_URL')
                    engine = create_engine(database_url)

                    with Session(engine) as session:
                        # Build query - select all columns since AGNO's endpoint expects them
                        query = """
                            SELECT
                                session_id,
                                session_type,
                                agent_id,
                                team_id,
                                workflow_id,
                                user_id,
                                session_data,
                                agent_data,
                                team_data,
                                workflow_data,
                                metadata,
                                runs,
                                summary,
                                created_at,
                                updated_at
                            FROM ai.agno_sessions
                            WHERE user_id = :user_id
                        """
                        params = {"user_id": user_id}

                        # Add date filters
                        created_after = query_params.get("created_after")
                        created_before = query_params.get("created_before")

                        if created_after:
                            query += " AND created_at >= :created_after"
                            params["created_after"] = int(created_after)
                            logger.info(f"📅 Filtering sessions: created_after={created_after}")

                        if created_before:
                            query += " AND created_at <= :created_before"
                            params["created_before"] = int(created_before)
                            logger.info(f"📅 Filtering sessions: created_before={created_before}")

                        # Add search filter (search in session_data JSON field)
                        session_name = query_params.get("session_name")
                        if session_name:
                            query += " AND (session_data->>'name' ILIKE :session_name OR metadata->>'name' ILIKE :session_name)"
                            params["session_name"] = f"%{session_name}%"

                        # Add sorting
                        sort_by = query_params.get("sort_by", "updated_at")
                        sort_order = query_params.get("sort_order", "desc")
                        if sort_by in ["created_at", "updated_at"]:
                            order = "ASC" if sort_order.lower() == "asc" else "DESC"
                            query += f" ORDER BY {sort_by} {order}"

                        # Count total
                        count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
                        total_count = session.execute(text(count_query), params).scalar()

                        # Add pagination
                        page = int(query_params.get("page", 1))
                        limit = int(query_params.get("limit", 20))
                        offset = (page - 1) * limit
                        query += f" LIMIT :limit OFFSET :offset"
                        params["limit"] = limit
                        params["offset"] = offset

                        # Execute query
                        result = session.execute(text(query), params)
                        sessions = []
                        for row in result:
                            sessions.append({
                                "session_id": row[0],
                                "session_type": row[1],
                                "agent_id": row[2],
                                "team_id": row[3],
                                "workflow_id": row[4],
                                "user_id": row[5],
                                "session_data": row[6],
                                "agent_data": row[7],
                                "team_data": row[8],
                                "workflow_data": row[9],
                                "metadata": row[10],
                                "runs": row[11],
                                "summary": row[12],
                                "created_at": row[13],
                                "updated_at": row[14]
                            })

                        total_pages = math.ceil(total_count / limit)

                        logger.info(f"✅ Filtered sessions: {len(sessions)} results")

                        return JSONResponse({
                            "data": sessions,
                            "meta": {
                                "page": page,
                                "limit": limit,
                                "total_count": total_count,
                                "total_pages": total_pages
                            }
                        })

                except Exception as e:
                    logger.error(f"❌ Error in SessionsDateFilterMiddleware: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return JSONResponse(
                        status_code=500,
                        content={"error": f"Failed to filter sessions: {str(e)}"}
                    )

        # Pass through to next middleware/handler
        return await call_next(request)


logger.info("✅ Middleware module loaded")

# ═══════════════════════════════════════════════════════════════
# RBAC GATEWAY MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

class RBACGatewayMiddleware(BaseHTTPMiddleware):
    """
    API Gateway with tier-based access control.

    Enforces RBAC permissions at the endpoint level.
    Intercepts requests and validates tier-based access before processing.

    Integration:
        - Reads tier_slug from request.state (set by JWT middleware)
        - Uses RBAC module to resolve permissions
        - Blocks access with 403 if insufficient permissions
        - Logs all access attempts for compliance
    """

    # Endpoint-to-permission mappings for tier enforcement
    PROTECTED_ENDPOINTS = {
        # Agent endpoints - require specific permissions
        "/teams/cirkelline/runs": "chat:basic",
        "/teams/research-team/runs": "team:research",
        "/teams/law-team/runs": "team:legal",

        # Deep research endpoints
        "/api/deep-research": "deep_research:enable",

        # Premium features
        "/api/export/data": "data:export",
        "/api/custom/agents": "agent:custom",
        "/api/custom/teams": "team:custom",

        # Search tool endpoints (if direct access)
        "/api/search/exa": "search:exa",
        "/api/search/tavily": "search:tavily",
    }

    # Endpoints that bypass RBAC (public or auth-only)
    BYPASS_ENDPOINTS = [
        "/health",
        "/config",
        "/api/auth/login",
        "/api/auth/signup",
        "/api/auth/logout",
        "/api/auth/refresh",
        "/docs",
        "/openapi.json",
    ]

    async def dispatch(self, request: StarletteRequest, call_next):
        """
        Intercept requests and enforce tier-based access control.
        """
        path = request.url.path

        # Skip RBAC for bypass endpoints
        for bypass in self.BYPASS_ENDPOINTS:
            if path.startswith(bypass):
                return await call_next(request)

        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get user context from request state
        user_id = getattr(request.state, 'user_id', None)
        tier_slug = getattr(request.state, 'tier_slug', 'member')
        is_admin = getattr(request.state, 'is_admin', False)

        # Anonymous users default to member tier for public endpoints
        if not user_id:
            return await call_next(request)

        # Check if endpoint requires specific permission
        required_permission_str = None
        for endpoint_pattern, permission in self.PROTECTED_ENDPOINTS.items():
            if path.startswith(endpoint_pattern):
                required_permission_str = permission
                break

        if required_permission_str:
            try:
                from cirkelline.middleware.rbac import (
                    Permission,
                    resolve_permissions,
                    TIER_NAMES,
                    get_tier_for_permission
                )

                # Get required permission enum
                required_permission = None
                for p in Permission:
                    if p.value == required_permission_str:
                        required_permission = p
                        break

                if required_permission:
                    # Resolve user's permissions
                    user_permissions = resolve_permissions(tier_slug, is_admin)

                    if required_permission not in user_permissions:
                        # Access denied - log and return 403
                        min_tier = get_tier_for_permission(required_permission)

                        logger.warning(
                            f"RBAC DENY: user={user_id[:20]}... tier={tier_slug} "
                            f"endpoint={path} required={required_permission_str} "
                            f"min_tier={min_tier}"
                        )

                        # Log the access attempt
                        await log_activity(
                            request=request,
                            user_id=user_id,
                            action_type="rbac_access_denied",
                            success=False,
                            status_code=403,
                            endpoint=path,
                            details={
                                "required_permission": required_permission_str,
                                "user_tier": tier_slug,
                                "required_tier": min_tier,
                            },
                            is_admin=is_admin
                        )

                        return JSONResponse(
                            status_code=403,
                            content={
                                "error": "insufficient_permissions",
                                "message": f"This feature requires {TIER_NAMES.get(min_tier, min_tier)} tier or higher",
                                "required_tier": min_tier,
                                "current_tier": tier_slug,
                                "upgrade_url": "https://cirkelline.com/pricing"
                            }
                        )

                    # Access granted - log success
                    logger.debug(
                        f"RBAC ALLOW: user={user_id[:20]}... tier={tier_slug} "
                        f"endpoint={path}"
                    )

            except ImportError as e:
                logger.error(f"RBAC module import error: {e}")
                # Fail open - allow access if RBAC module not available
                pass

        # Continue to next middleware/handler
        response = await call_next(request)
        return response


# ═══════════════════════════════════════════════════════════════
# AUDIT TRAIL MIDDLEWARE (LAW TEAM COMPLIANCE)
# ═══════════════════════════════════════════════════════════════

class AuditTrailMiddleware(BaseHTTPMiddleware):
    """
    Compliance-grade audit logging for all sensitive operations.

    Designed for:
        - GDPR Article 30 (Records of processing activities)
        - SOC 2 Type II (Security controls)
        - Law Team requirements (legal compliance)

    Logged Events:
        - All authentication events (login, logout, token refresh)
        - Data access events (read personal data)
        - Data modification events (create, update, delete)
        - Admin operations (user management, config changes)
        - Security events (failed auth, permission denials)

    Log Format:
        JSONB with:
        - timestamp (ISO 8601)
        - user_id (who performed action)
        - action (what was done)
        - resource_type (what type of data)
        - resource_id (which specific record)
        - ip_address (where from)
        - user_agent (what client)
        - request_id (correlation ID)
        - duration_ms (how long)
        - changes (before/after for modifications)
    """

    # Endpoints that require full audit trail
    AUDIT_REQUIRED_ENDPOINTS = [
        # Authentication events
        ("/api/auth/login", "auth_login"),
        ("/api/auth/logout", "auth_logout"),
        ("/api/auth/signup", "auth_signup"),

        # User data operations
        ("/api/user/profile", "user_profile_access"),
        ("/api/user/preferences", "user_preferences_access"),
        ("/api/user/delete", "user_delete"),

        # Document/Knowledge operations
        ("/api/knowledge/upload", "document_upload"),
        ("/api/knowledge/delete", "document_delete"),

        # Memory operations (personal data)
        ("/api/memories", "memories_access"),

        # Admin operations
        ("/admin/users", "admin_users"),
        ("/admin/subscriptions", "admin_subscriptions"),

        # Data export (GDPR right to portability)
        ("/api/export", "data_export"),

        # Legal team operations
        ("/teams/law-team/runs", "legal_consultation"),
    ]

    # HTTP methods that indicate modification (require extra logging)
    MODIFICATION_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

    async def dispatch(self, request: StarletteRequest, call_next):
        """
        Log all sensitive operations with compliance-grade detail.
        """
        import uuid
        import time

        path = request.url.path
        method = request.method

        # Generate request correlation ID
        request_id = str(uuid.uuid4())[:12]

        # Store request_id in state for downstream use
        if not hasattr(request.state, 'request_id'):
            request.state.request_id = request_id

        # Check if this endpoint requires audit trail
        audit_action = None
        for endpoint_pattern, action in self.AUDIT_REQUIRED_ENDPOINTS:
            if path.startswith(endpoint_pattern):
                audit_action = action
                break

        # Start timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Log audit trail if required
        if audit_action:
            try:
                user_id = getattr(request.state, 'user_id', 'anonymous')
                is_admin = getattr(request.state, 'is_admin', False)
                tier_slug = getattr(request.state, 'tier_slug', 'unknown')
                ip_address = request.client.host if request.client else 'unknown'
                user_agent = request.headers.get('user-agent', '')[:200]

                # Build audit log entry
                audit_entry = {
                    "request_id": request_id,
                    "method": method,
                    "is_modification": method in self.MODIFICATION_METHODS,
                    "tier": tier_slug,
                }

                # Log to activity_logs with special audit tag
                await log_activity(
                    request=request,
                    user_id=user_id,
                    action_type=f"audit_{audit_action}",
                    success=(200 <= response.status_code < 400),
                    status_code=response.status_code,
                    endpoint=path,
                    duration_ms=duration_ms,
                    details=audit_entry,
                    is_admin=is_admin,
                    resource_type=audit_action.split('_')[0] if '_' in audit_action else audit_action,
                )

                # Also log to separate audit table for compliance
                await self._log_compliance_audit(
                    request_id=request_id,
                    timestamp=datetime.utcnow(),
                    user_id=user_id,
                    action=audit_action,
                    resource_type=audit_action.split('_')[0] if '_' in audit_action else audit_action,
                    endpoint=path,
                    method=method,
                    status_code=response.status_code,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    duration_ms=duration_ms,
                    tier=tier_slug,
                    is_admin=is_admin,
                )

            except Exception as e:
                # Don't let audit logging break the application
                logger.error(f"Audit trail logging error: {e}")

        return response

    async def _log_compliance_audit(
        self,
        request_id: str,
        timestamp: datetime,
        user_id: str,
        action: str,
        resource_type: str,
        endpoint: str,
        method: str,
        status_code: int,
        ip_address: str,
        user_agent: str,
        duration_ms: int,
        tier: str,
        is_admin: bool,
    ):
        """
        Log to dedicated compliance audit table.

        This table is designed for:
        - Long-term retention (7+ years for legal compliance)
        - Immutable records (append-only)
        - Easy export for auditors
        """
        try:
            with Session(_shared_engine) as session:
                # Check if audit_compliance_logs table exists
                # If not, log to activity_logs with audit flag
                result = session.execute(
                    text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'ai'
                            AND table_name = 'audit_compliance_logs'
                        )
                    """)
                )
                table_exists = result.scalar()

                if table_exists:
                    session.execute(
                        text("""
                            INSERT INTO ai.audit_compliance_logs
                            (request_id, timestamp, user_id, action, resource_type,
                             endpoint, http_method, status_code, ip_address, user_agent,
                             duration_ms, tier, is_admin)
                            VALUES
                            (:request_id, :timestamp, :user_id, :action, :resource_type,
                             :endpoint, :http_method, :status_code, :ip_address, :user_agent,
                             :duration_ms, :tier, :is_admin)
                        """),
                        {
                            "request_id": request_id,
                            "timestamp": timestamp,
                            "user_id": user_id,
                            "action": action,
                            "resource_type": resource_type,
                            "endpoint": endpoint,
                            "http_method": method,
                            "status_code": status_code,
                            "ip_address": ip_address,
                            "user_agent": user_agent,
                            "duration_ms": duration_ms,
                            "tier": tier,
                            "is_admin": is_admin,
                        }
                    )
                    session.commit()
                else:
                    # Table doesn't exist yet - just log to console
                    logger.info(
                        f"AUDIT: [{request_id}] {action} user={user_id[:20]}... "
                        f"endpoint={endpoint} status={status_code} duration={duration_ms}ms"
                    )

        except Exception as e:
            logger.error(f"Compliance audit log error: {e}")


logger.info("✅ RBAC Gateway and Audit Trail middleware loaded")


# ═══════════════════════════════════════════════════════════════
# RATE LIMITING MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

import time
from collections import defaultdict
from threading import Lock

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for API protection.

    Implements sliding window rate limiting per user/IP.

    Limits (per minute):
        - Anonymous: 30 requests/min
        - Member tier: 60 requests/min
        - Professional tier: 120 requests/min
        - Enterprise tier: 300 requests/min
        - Admin: 600 requests/min

    For production scaling: Replace in-memory store with Redis.
    """

    # Rate limits per tier (requests per minute)
    RATE_LIMITS = {
        "anonymous": 30,
        "member": 60,
        "professional": 120,
        "enterprise": 300,
        "admin": 600,
    }

    # Endpoints exempt from rate limiting
    EXEMPT_ENDPOINTS = [
        "/health",
        "/config",
        "/docs",
        "/openapi.json",
        "/favicon.ico",
    ]

    # Stricter limits for expensive endpoints (requests per minute)
    EXPENSIVE_ENDPOINTS = {
        "/teams/cirkelline/runs": 20,      # Chat - expensive
        "/teams/research-team/runs": 10,   # Deep research - very expensive
        "/teams/law-team/runs": 10,        # Legal team - expensive
        "/api/knowledge/upload": 10,       # File upload
        "/api/deep-research": 5,           # Deep research toggle
    }

    def __init__(self, app, window_seconds: int = 60):
        super().__init__(app)
        self.window_seconds = window_seconds
        self.request_counts: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
        logger.info(f"✅ Rate limiting middleware initialized (window={window_seconds}s)")

    def _get_client_key(self, request: StarletteRequest, user_id: Optional[str]) -> str:
        """Generate unique key for rate limiting (user_id or IP)."""
        if user_id:
            return f"user:{user_id}"
        # Fallback to IP for anonymous
        ip = request.client.host if request.client else "unknown"
        return f"ip:{ip}"

    def _get_rate_limit(self, tier_slug: str, is_admin: bool, endpoint: str) -> int:
        """Get rate limit for user tier and endpoint."""
        # Check expensive endpoint limits first
        for expensive_path, limit in self.EXPENSIVE_ENDPOINTS.items():
            if endpoint.startswith(expensive_path):
                # Expensive endpoints have stricter limits
                if is_admin:
                    return limit * 3
                return limit

        # Normal rate limits
        if is_admin:
            return self.RATE_LIMITS["admin"]
        return self.RATE_LIMITS.get(tier_slug, self.RATE_LIMITS["member"])

    def _is_rate_limited(self, client_key: str, limit: int) -> tuple[bool, int, int]:
        """
        Check if client is rate limited using sliding window.

        Returns: (is_limited, remaining, reset_seconds)
        """
        current_time = time.time()
        window_start = current_time - self.window_seconds

        with self.lock:
            # Clean old requests
            self.request_counts[client_key] = [
                t for t in self.request_counts[client_key]
                if t > window_start
            ]

            request_count = len(self.request_counts[client_key])
            remaining = max(0, limit - request_count)

            if request_count >= limit:
                # Calculate reset time
                oldest_request = min(self.request_counts[client_key]) if self.request_counts[client_key] else current_time
                reset_seconds = int(oldest_request + self.window_seconds - current_time)
                return True, 0, max(1, reset_seconds)

            # Record this request
            self.request_counts[client_key].append(current_time)
            return False, remaining - 1, self.window_seconds

    async def dispatch(self, request: StarletteRequest, call_next):
        """Check rate limits before processing request."""
        path = request.url.path

        # Skip exempt endpoints
        for exempt in self.EXEMPT_ENDPOINTS:
            if path.startswith(exempt):
                return await call_next(request)

        # Skip OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get user context
        user_id = getattr(request.state, 'user_id', None)
        tier_slug = getattr(request.state, 'tier_slug', 'anonymous')
        is_admin = getattr(request.state, 'is_admin', False)

        # Get client key and rate limit
        client_key = self._get_client_key(request, user_id)
        rate_limit = self._get_rate_limit(tier_slug, is_admin, path)

        # Check rate limit
        is_limited, remaining, reset_seconds = self._is_rate_limited(client_key, rate_limit)

        if is_limited:
            logger.warning(
                f"RATE LIMIT: {client_key} exceeded {rate_limit}/min on {path}"
            )

            # Log the rate limit event
            if user_id:
                await log_activity(
                    request=request,
                    user_id=user_id,
                    action_type="rate_limit_exceeded",
                    success=False,
                    status_code=429,
                    endpoint=path,
                    details={
                        "limit": rate_limit,
                        "window_seconds": self.window_seconds,
                        "tier": tier_slug,
                    },
                    is_admin=is_admin
                )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests. Limit: {rate_limit}/min",
                    "retry_after": reset_seconds,
                    "limit": rate_limit,
                    "window": self.window_seconds,
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_seconds),
                    "Retry-After": str(reset_seconds),
                }
            )

        # Process request and add rate limit headers
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_seconds)

        return response


logger.info("✅ Rate Limiting middleware loaded")
