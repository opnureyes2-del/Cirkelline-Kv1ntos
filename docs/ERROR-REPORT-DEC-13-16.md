# Production Error Report: Dec 13-16, 2025

**Generated:** 2025-12-16
**Time Range:** Dec 13 17:07 UTC (Ubuntu dual boot message) → Dec 16 present
**Total Error Lines:** 2,968

---

## Error Summary

| # | Error Type | Count | Severity | Status |
|---|------------|-------|----------|--------|
| 1 | Google Token Refresh Failed | 133 | Medium | Investigate |
| 2 | Gemini 429 Rate Limit | 39 | High | Investigate |
| 3 | Tool Compression Failed | 35 | High | **FIXED** (disabled compression) |
| 4 | Task Exception Never Retrieved | 15 | Medium | Investigate |
| 5 | ASGI Exception (Invalid UUID) | 14 | High | Investigate |
| 6 | Metrics Column Missing | 5 | Medium | Investigate |
| 7 | Journal Queue Null user_id | 4 | Medium | Investigate |
| 8 | Exa Search Function Not Found | 3 | High | Investigate |
| 9 | Memory Year Out of Range | 2 | High | **FIXED** (v1.3.3) |
| 10 | Admin Stats Operator Error | 2 | Low | Investigate |
| 11 | JWT Expired/Invalid | 3 | Low | Expected behavior |

---

## Detailed Error Analysis

### 1. Google Token Refresh Failed (133 occurrences)

**Error:**
```
ERROR - Token refresh failed: {
  "error": "invalid_grant",
  "error_description": "Bad Request"
}
```

**When:** Throughout Dec 13-16
**Impact:** Google services (Gmail, Calendar) unavailable for affected users
**Root Cause:** OAuth refresh tokens expired or revoked
**User Impact:** Medium - Google features don't work, but core chat works

**Sample Log:**
```
2025-12-13T17:07:16.133 - ERROR - Token refresh failed: {"error": "invalid_grant", "error_description": "Bad Request"}
```

---

### 2. Gemini 429 Rate Limit (39 occurrences)

**Error:**
```
ERROR    Error from Gemini API: 429 RESOURCE_EXHAUSTED
ERROR    Model provider error after 1 attempts: <Response [429 Too Many Requests]>
```

**When:** Sporadic, especially Dec 15 21:33
**Impact:** User gets error message, needs to retry
**Root Cause:** Hitting Gemini Tier 1 rate limits (1,500 RPM)
**User Impact:** High - Chat fails completely

**Sample Log:**
```
2025-12-15T21:33:00.578 - ERROR - Model provider error after 1 attempts: <Response [429 Too Many Requests]>
2025-12-15T21:33:00.579 - ERROR - Maximum retries exceeded (3 attempts). The service is experiencing high load.
```

---

### 3. Tool Compression Failed (35 occurrences) - **FIXED**

**Error:**
```
ERROR    Unknown error from Gemini API:
ERROR    Model provider error after 1 attempts:
ERROR    Error compressing tool result:
```

**When:** Dec 13 17:07 (caused empty response bug)
**Impact:** Empty response returned to user
**Root Cause:** `compress_tool_results=True` in AGNO - compression API call fails
**Fix Applied:** Set `compress_tool_results=False` in cirkelline_team.py:173

---

### 4. Task Exception Never Retrieved (15 occurrences)

**Error:**
```
ERROR - Task exception was never retrieved
```

**When:** Throughout Dec 13-16
**Impact:** Background task failures (possibly journal generation)
**Root Cause:** Async task exceptions not being caught
**User Impact:** Low - Background operations fail silently

---

### 5. ASGI Exception - Invalid UUID (14 occurrences)

**Error:**
```
ERROR:    Exception in ASGI application
psycopg.errors.InvalidTextRepresentation: invalid input syntax for type uuid: "anon-cbcd5b88-508e-438c-9a8f-70752231b48c"
```

**When:** Dec 13 14:30 - 15:43
**Impact:** 500 Internal Server Error
**Root Cause:** Anonymous user ID format "anon-xxx" being passed to UUID column
**User Impact:** High - Request fails completely

**Affected Endpoint:** Unknown (need to check which endpoint)

---

### 6. Metrics Column Missing (5 occurrences)

**Error:**
```
ERROR - Failed to store metrics: (psycopg.errors.UndefinedColumn) column "metrics" does not exist
```

**When:** Dec 14 02:34, 08:33
**Impact:** Token usage metrics not stored
**Root Cause:** Database schema mismatch - `metrics` column not in production DB
**User Impact:** None - Feature silently fails, chat works

---

### 7. Journal Queue Null user_id (4 occurrences)

**Error:**
```
ERROR - Failed to add to queue: (psycopg.errors.NotNullViolation) null value in column "user_id" of relation "journal_queue" violates not-null constraint
```

**When:** Dec 15 01:00, Dec 16 01:00 (daily at 01:00 UTC)
**Impact:** Journal entry not queued for processing
**Root Cause:** Scheduler trying to queue journal for user with null user_id
**User Impact:** Low - Journal not generated for that day

---

### 8. Exa Search Function Not Found (3 occurrences)

**Error:**
```
ERROR    Function exa_search not found
```

**When:** Dec 15 10:30, 11:30
**Impact:** Model tried to call `exa_search` but function doesn't exist
**Root Cause:** Tool name mismatch - AGNO renamed to `search_exa`
**User Impact:** Medium - Search fails, model may retry with different tool

---

### 9. Memory Year Out of Range (2 occurrences) - **FIXED**

**Error:**
```
ERROR    Exception reading from memory table: year 57898 is out of range
WARNING  Error in memory creation: year 57898 is out of range
```

**When:** Dec 14 02:34, 08:33
**Impact:** Memory not created/read
**Root Cause:** Timestamp stored in MILLISECONDS instead of SECONDS
**Fix Applied:** v1.3.3 fixed timestamp format (already deployed)

---

### 10. Admin Stats Operator Error (2 occurrences)

**Error:**
```
ERROR - Error getting admin stats: (psycopg.errors.UndefinedFunction) operator does not exist: bigint > timestamp with time zone
```

**When:** Unknown
**Impact:** Admin dashboard shows error
**Root Cause:** SQL type mismatch in admin stats query
**User Impact:** None for regular users, admin dashboard broken

---

### 11. JWT Expired/Invalid (3 occurrences)

**Error:**
```
ERROR - JWT decode error: Signature has expired
ERROR - JWT decode error: Signature verification failed
```

**When:** Sporadic
**Impact:** User needs to re-login
**Root Cause:** Expected behavior - tokens expire after 7 days
**User Impact:** Low - Normal auth flow

---

## Errors Already Fixed

| Error | Fix | Version |
|-------|-----|---------|
| Tool Compression Failed | Set `compress_tool_results=False` | v1.3.4 (pending) |
| Memory Year Out of Range | Fixed timestamp format MILLISECONDS→SECONDS | v1.3.3 (deployed) |
| ReasoningTools Output Leak | Added CRITICAL EXECUTION ORDER instruction | v1.3.4 (pending) |

---

## Errors Requiring Investigation

### Priority 1 (High Impact)
1. **Gemini 429 Rate Limit** - Users see errors during high load
2. **ASGI Exception Invalid UUID** - Crashes for anonymous users
3. **Exa Search Function Not Found** - Search failures

### Priority 2 (Medium Impact)
4. **Google Token Refresh Failed** - Google features broken
5. **Task Exception Never Retrieved** - Background tasks failing
6. **Metrics Column Missing** - Database schema issue

### Priority 3 (Low Impact)
7. **Journal Queue Null user_id** - Journal generation edge case
8. **Admin Stats Operator Error** - Admin-only issue

---

## Next Steps

1. [ ] Investigate ASGI Invalid UUID error - which endpoint?
2. [ ] Check if `exa_search` vs `search_exa` name mismatch in instructions
3. [ ] Add retry logic for Gemini 429 errors
4. [ ] Check production DB for missing `metrics` column
5. [ ] Fix journal queue null user_id edge case
6. [ ] Review Google OAuth token refresh flow
