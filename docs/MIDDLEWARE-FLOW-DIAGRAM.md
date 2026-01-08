# Middleware Flow Diagram

**Date:** 2025-12-16 (Updated v1.3.4)
**Purpose:** Visual representation of middleware execution flow

---

## Request Flow Through Middleware (v1.3.4)

**Note:** AnonymousUserMiddleware was removed in v1.3.4. Accounts are now required.

```
┌─────────────────────────────────────────────────────────────────┐
│                      INCOMING HTTP REQUEST                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. SessionsDateFilterMiddleware                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ • Intercepts: GET /sessions with date filters            │  │
│  │ • Decodes JWT to get user_id                             │  │
│  │ • Queries ai.agno_sessions directly                      │  │
│  │ • Returns JSONResponse (short-circuits if filters exist) │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Filters present? │
                    └─────────────────┘
                         Yes │  │ No
         ┌───────────────────┘  └─────────────────┐
         │                                         │
         ▼                                         ▼
┌────────────────────┐              ┌─────────────────────────────────────┐
│ Return filtered    │              │  2. SessionLoggingMiddleware        │
│ results (STOP)     │              │  ┌───────────────────────────────┐  │
└────────────────────┘              │  │ • Intercepts session ops:     │  │
                                    │  │   - DELETE /sessions/{id}     │  │
                                    │  │   - POST /sessions/{id}/rename│  │
                                    │  │ • Logs to activity_logs table │  │
                                    │  │ • Calls log_activity()        │  │
                                    │  └───────────────────────────────┘  │
                                    └─────────────────────────────────────┘
                                                      │
                                                      ▼
                                    ┌─────────────────────────────────────┐
                                    │  3. JWTMiddleware (AGNO)            │
                                    │  ┌───────────────────────────────┐  │
                                    │  │ • Decode JWT token            │  │
                                    │  │ • Extract claims:             │  │
                                    │  │   - user_id                   │  │
                                    │  │   - session_id                │  │
                                    │  │   - user_name                 │  │
                                    │  │   - user_role                 │  │
                                    │  │   - user_type                 │  │
                                    │  │   - tier_slug                 │  │
                                    │  │   - tier_level                │  │
                                    │  │ • Inject into request.state   │  │
                                    │  └───────────────────────────────┘  │
                                    └─────────────────────────────────────┘
                                                      │
                                                      ▼
                                    ┌─────────────────────────────────────┐
                                    │         REQUEST HANDLER             │
                                    │    (API Endpoint / AGNO Route)      │
                                    │  ┌───────────────────────────────┐  │
                                    │  │ v1.3.4: Endpoints verify auth │  │
                                    │  │ Reject anon-* and empty users │  │
                                    │  └───────────────────────────────┘  │
                                    └─────────────────────────────────────┘
```

---

## Response Flow (Reverse Order)

```
┌─────────────────────────────────────────────────────────────────┐
│                       REQUEST HANDLER                            │
│                  (Generates Response)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. JWTMiddleware (AGNO)                                        │
│  • No response modification                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. SessionLoggingMiddleware                                    │
│  • Logs activity AFTER response generated                       │
│  • Checks response.status_code for success/failure              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. SessionsDateFilterMiddleware                                │
│  • No response modification (already returned early if needed)   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTGOING HTTP RESPONSE                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## CORS Middleware Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   CORS PREFLIGHT REQUEST                         │
│                    (OPTIONS method)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  CORSMiddleware (FastAPI built-in)                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ • Check Origin header                                     │  │
│  │ • Match against allow_origins list:                      │  │
│  │   - http://localhost:3000                                │  │
│  │   - http://localhost:3001                                │  │
│  │   - https://cirkelline-system-ui.vercel.app              │  │
│  │   - https://cirkelline.com                               │  │
│  │   - etc.                                                 │  │
│  │ • Add CORS headers:                                      │  │
│  │   - Access-Control-Allow-Origin                          │  │
│  │   - Access-Control-Allow-Credentials: true               │  │
│  │   - Access-Control-Allow-Methods: *                      │  │
│  │   - Access-Control-Allow-Headers: *                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ Return 200 OK with CORS headers│
              └───────────────────────────────┘
```

---

## State Injection Flow (v1.3.4)

```
┌─────────────────────────────────────────────────────────────────┐
│                      REQUEST OBJECT                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │     request.state (initially empty)        │
        └────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  JWTMiddleware                                                  │
│  If Authorization header present:                               │
│    Decodes JWT and sets:                                        │
│    request.state.user_id = decoded["user_id"]                   │
│    request.state.session_id = decoded.get("session_id")         │
│    request.state.dependencies["user_name"] = decoded["user_name"]│
│    request.state.dependencies["user_role"] = decoded["user_role"]│
│    request.state.dependencies["user_type"] = decoded["user_type"]│
│    request.state.dependencies["tier_slug"] = decoded["tier_slug"]│
│    request.state.dependencies["tier_level"] = decoded["tier_level"]│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │  request.state (populated from JWT)        │
        │  • user_id (from JWT or None)              │
        │  • session_id (from JWT if present)        │
        │  • dependencies dict with all claims       │
        └────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │    Endpoint handler verifies auth:         │
        │    if not user_id or user_id.startswith('anon-'):
        │        raise HTTPException(401)            │
        └────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                REQUEST WITHOUT VALID JWT                         │
│               (missing or expired token)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │  JWTMiddleware processes request           │
        │  No valid token → user_id = None           │
        └────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │  Endpoint handler (e.g., custom_cirkelline)│
        │  Checks user_id:                           │
        │  - if not user_id: raise 401               │
        │  - if user_id.startswith('anon-'): 401    │
        └────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────┐
        │  Return 401 Unauthorized                   │
        │  "Account required. Please sign up or log in."
        └────────────────────────────────────────────┘
```

---

## Dependencies Graph (v1.3.4)

```
┌────────────────────────────────────────────────────────────────┐
│                   FastAPI Application                          │
└────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
┌───────────────────────────┐  ┌────────────────────────────┐
│  CORSMiddleware           │  │  Custom Middleware Stack   │
│  (FastAPI built-in)       │  │                            │
└───────────────────────────┘  └────────────────────────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                        ▼                    ▼                    ▼
        ┌─────────────────────┐  ┌──────────────────┐  ┌────────────────┐
        │SessionsDateFilter   │  │SessionLogging    │  │JWTMiddleware   │
        │Middleware           │  │Middleware        │  │(AGNO)          │
        └─────────────────────┘  └──────────────────┘  └────────────────┘
                │                         │                      │
                │                         │                      │
                ▼                         ▼                      ▼
        ┌──────────────┐         ┌───────────────┐      ┌────────────────┐
        │ • JWT decode │         │ log_activity()│      │ • JWT decode   │
        │ • SQLAlchemy │         │ function      │      │ • Set state    │
        │ • Database   │         └───────────────┘      └────────────────┘
        └──────────────┘                   │
                │                          │
                │                          ▼
                │                  ┌────────────────┐
                │                  │ activity_logs  │
                │                  │ table          │
                │                  └────────────────┘
                │
                ▼
        ┌─────────────────────────┐
        │ ai.agno_sessions table  │
        └─────────────────────────┘
```

---

## Configuration Dependencies

```
Environment Variables
├── JWT_SECRET_KEY
│   ├── Used by: SessionsDateFilterMiddleware
│   └── Used by: JWTMiddleware
│
└── DATABASE_URL
    ├── Used by: _shared_engine (activity logging)
    └── Used by: SessionsDateFilterMiddleware (session queries)


Database Tables
├── activity_logs
│   └── Written by: log_activity() → called by SessionLoggingMiddleware
│
└── ai.agno_sessions
    └── Queried by: SessionsDateFilterMiddleware (direct SQL)


External Functions
├── log_activity()
│   ├── Location: cirkelline/middleware/middleware.py
│   ├── Called by: SessionLoggingMiddleware
│   └── Depends on: _shared_engine
│
└── _shared_engine
    ├── Location: cirkelline/middleware/middleware.py
    ├── Type: SQLAlchemy Engine
    └── Used by: log_activity()
```

---

## Execution Timeline Examples

```
Time    Event                              Middleware                    Action
──────────────────────────────────────────────────────────────────────────────
t=0ms   GET /sessions?created_after=X      → SessionsDateFilter        Intercept
t=2ms                                      → Decode JWT                Extract user_id
t=5ms                                      → Query database            SELECT from ai.agno_sessions
t=15ms                                     → Return JSONResponse       ✓ STOP (short-circuit)
──────────────────────────────────────────────────────────────────────────────

Time    Event                              Middleware                    Action
──────────────────────────────────────────────────────────────────────────────
t=0ms   POST /teams/cirkelline/runs        → SessionsDateFilter        Pass through
        (with valid JWT)
t=1ms                                      → SessionLogging            Pass through
t=2ms                                      → JWTMiddleware             Decode, extract user
t=3ms                                      → Endpoint handler          Verify auth ✓
t=500ms                                    ← Response                  Return to client
──────────────────────────────────────────────────────────────────────────────

Time    Event                              Middleware                    Action
──────────────────────────────────────────────────────────────────────────────
t=0ms   POST /teams/cirkelline/runs        → SessionsDateFilter        Pass through
        (NO JWT - unauthenticated)
t=1ms                                      → SessionLogging            Pass through
t=2ms                                      → JWTMiddleware             No token, user_id=None
t=3ms                                      → Endpoint handler          Check auth
t=4ms                                      → Raise HTTPException       401 Unauthorized
t=5ms   ← Response (401)                   ← Return error              ✓ STOP
──────────────────────────────────────────────────────────────────────────────

Time    Event                              Middleware                    Action
──────────────────────────────────────────────────────────────────────────────
t=0ms   DELETE /sessions/abc123            → SessionsDateFilter        Pass through
t=1ms                                      → SessionLogging            Detect DELETE
t=2ms                                      → Store session_id          = abc123
t=3ms                                      → JWTMiddleware             Extract user_id
t=4ms                                      → Endpoint handler          Process delete
t=50ms  ← Response (200 OK)                ← SessionLogging            Log activity
t=51ms                                     ← log_activity()            Write to DB
t=55ms  ← Response                         ← Return to client          ✓ Done
──────────────────────────────────────────────────────────────────────────────
```

---

**Status:** Updated for v1.3.4 (removed AnonymousUserMiddleware)
**Last Updated:** 2025-12-16
**Maintained By:** Development Team
