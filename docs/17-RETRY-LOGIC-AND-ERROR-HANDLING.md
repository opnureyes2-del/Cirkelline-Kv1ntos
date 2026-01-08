# Rate Limit Retry Logic & Error Handling

**Version:** v1.2.18
**Last Updated:** 2025-11-06
**Status:** ✅ Production Ready

## 📋 Table of Contents

- [Overview](#overview)
- [Problem Identification](#problem-identification)
- [Root Cause Analysis](#root-cause-analysis)
- [Solution Architecture](#solution-architecture)
- [Implementation Details](#implementation-details)
- [User Experience](#user-experience)
- [Testing](#testing)
- [Deployment](#deployment)
- [Monitoring](#monitoring)

---

## Overview

This document describes the implementation of automatic retry logic with exponential backoff to handle Google Gemini API rate limit errors (429 RESOURCE_EXHAUSTED). The system now gracefully handles rate limits by:

1. **Automatically retrying** failed requests up to 3 times
2. **Honoring Google's retry delays** from error responses
3. **Showing real-time status** to users during retries
4. **Displaying clear error messages** if all retries fail

### Key Features

- ✅ Automatic retry with exponential backoff
- ✅ Respects Google API retry delay recommendations
- ✅ Real-time user feedback during retry attempts
- ✅ Clear error messaging when retries exhausted
- ✅ Full visibility in "Behind the Scenes" timeline
- ✅ Session persistence after successful retry

---

## Problem Identification

### Symptoms

**On AWS Production:**
- User sends query asking about previous conversation
- "Behind the Scenes" shows activity (tool calls executing)
- `get_previous_session_messages` tool completes successfully
- **NO RESPONSE arrives** to user
- Session disappears after page refresh

**On Localhost:**
- Same queries work perfectly
- Sessions persist correctly
- Full responses delivered

### User Impact

- Silent failures with no feedback
- Lost sessions after refresh
- Complete confusion about system state
- No indication whether system is working or broken

### Initial Misdiagnosis

Initially blamed API key rate limits because:
- AWS logs showed 429 errors
- Different API keys used on localhost vs AWS
- Assumed key configuration issue

**User proved this wrong** by demonstrating:
- Simple "test" message worked on AWS (ruled out key/deployment issues)
- Complex session retrieval query failed consistently
- Google API dashboard showed far from rate limits
- Same API key worked perfectly on localhost

---

## Root Cause Analysis

### The Real Problem

AWS CloudWatch logs revealed the actual issue:

```
2025-11-06 09:05:35 - INFO - TeamToolCallCompleted | get_previous_session_messages() completed in 0.0853s
2025-11-06 09:05:36 - INFO - HTTP Request: POST https://generativelanguage.googleapis.com/... - 429 Too Many Requests
2025-11-06 09:05:36 - ERROR - Error from Gemini API: 429 RESOURCE_EXHAUSTED
```

**Key Finding:**
```json
{
  "error": {
    "code": 429,
    "message": "You exceeded your current quota...",
    "details": [{
      "quotaMetric": "generativelanguage.googleapis.com/generate_content_paid_tier_input_token_count",
      "quotaId": "GenerateContentPaidTierInputTokensPerModelPerMinute",
      "quotaValue": "1000000"
    }]
  }
}
```

### Why It Happens

**Request Flow:**
1. User asks: "What did I ask you before?"
2. Cirkelline calls `get_previous_session_messages` tool
3. Tool retrieves FULL conversation history (succeeds in ~0.08s)
4. Cirkelline attempts to generate response with:
   - System instructions (~2,000 tokens)
   - Admin profile context (~500 tokens)
   - Knowledge base context (variable)
   - Tool definitions (~1,000 tokens)
   - **ENTIRE conversation history** (can be 100,000+ tokens)
   - Current user message
5. **Total input exceeds 1M tokens/minute quota**
6. Google API returns 429 with retry delay
7. No retry logic exists → Request fails
8. No response sent → Session not saved

### Token Accumulation Example

| Component | Tokens | Notes |
|-----------|--------|-------|
| System Instructions | ~2,000 | Cirkelline's base instructions |
| Admin Profile | ~500 | If admin user |
| Tool Definitions | ~1,000 | All available tools |
| Knowledge Context | ~5,000 | Recent documents |
| **Previous Messages** | **~900,000** | **50 messages * 18,000 avg tokens** |
| Current Message | ~100 | User's query |
| **TOTAL** | **~908,600** | **Exceeds 1M/minute on single call** |

### Why Localhost Works

- Minimal concurrent traffic
- Fresh sessions with short history
- Stays well under quota limits
- If quota hit, next request succeeds after 1-minute window

### Why AWS Fails

- Production traffic from multiple users
- Long conversation histories
- Session retrieval queries immediately hit quota
- No retry → immediate failure
- Sessions not saved → disappear on refresh

---

## Solution Architecture

### Design Principles

1. **Automatic Retry**: Don't burden user with manual retries
2. **Honor API Guidance**: Use Google's recommended retry delays
3. **Exponential Backoff**: If no delay specified, use 5s → 10s → 20s
4. **User Transparency**: Show what's happening during retries
5. **Fail Gracefully**: Clear error message if retries exhausted
6. **Full Observability**: Log retries in timeline

### Retry Strategy

```
┌─────────────────────────────────────────────────┐
│ Request Sent → cirkelline.arun()                 │
└─────────────────────────────────────────────────┘
                    ↓
         ┌──────────────────────┐
         │  Success?            │
         └──────────────────────┘
          ↓ Yes              ↓ No
   ┌──────────┐        ┌────────────────┐
   │ Return   │        │ 429 Error?     │
   │ Response │        └────────────────┘
   └──────────┘         ↓ Yes         ↓ No
                  ┌──────────────┐   ┌─────────────┐
                  │ Extract      │   │ Return      │
                  │ Retry Delay  │   │ Error       │
                  └──────────────┘   └─────────────┘
                         ↓
                  ┌──────────────────────────┐
                  │ Send "retry" event to UI │
                  │ Show: "Retrying in 5s"   │
                  └──────────────────────────┘
                         ↓
                  ┌──────────────┐
                  │ Wait (sleep) │
                  └──────────────┘
                         ↓
                  ┌──────────────────┐
                  │ Retry < 3?       │
                  └──────────────────┘
                   ↓ Yes        ↓ No
            ┌───────────┐   ┌────────────────┐
            │ Increment │   │ Send "error"   │
            │ Retry     │   │ "Max retries   │
            │ Attempt   │   │ exceeded"      │
            └───────────┘   └────────────────┘
                   ↓
            [Back to Request Sent]
```

### Error Types

| Type | Description | User Action |
|------|-------------|-------------|
| `rate_limit` | 429 from API, retries attempted | Wait for retries to complete |
| `general` | Non-429 error during streaming | Report to support if persistent |
| `unexpected` | Unhandled exception | Report to support with details |

---

## Implementation Details

### Backend Changes

**File:** `/home/eenvy/Desktop/cirkelline/my_os.py`
**Lines:** 2573-2728 (event_generator function)

#### 1. Retry Loop Structure

```python
async def event_generator():
    import time
    import re
    from agno.exceptions import ModelProviderError

    max_retries = 3
    retry_count = 0

    try:
        while retry_count <= max_retries:
            try:
                # Attempt cirkelline.arun()
                async for event in cirkelline.arun(...):
                    # Process events
                    yield event

                # If we get here, success!
                break

            except (ModelProviderError, Exception) as e:
                # Handle errors with retry logic
                ...
```

#### 2. Error Detection & Retry Decision

```python
error_str = str(e)
is_rate_limit = ('429' in error_str or
                 'RESOURCE_EXHAUSTED' in error_str or
                 'quota' in error_str.lower())

if is_rate_limit and retry_count < max_retries:
    # Extract retry delay from Google's error
    retry_delay = 5  # Default
    match = re.search(r'retry in (\d+(?:\.\d+)?)', error_str, re.IGNORECASE)
    if match:
        retry_delay = float(match.group(1))
    else:
        # Exponential backoff
        retry_delay = min(5 * (2 ** retry_count), 60)
```

**Delay Strategy:**
- **First Attempt**: If Google says "retry in 4.8s" → use 4.8s
- **Second Attempt**: If Google says "retry in 23s" → use 23s
- **Third Attempt**: If Google says "retry in 58s" → use 58s
- **No Delay Specified**: Use 5s → 10s → 20s (exponential backoff)

#### 3. User Status Updates

```python
# Send retry notification to UI
retry_message = f'Rate limit reached. Retrying in {int(retry_delay)} seconds... (Attempt {retry_count}/{max_retries})'
yield f"event: retry\ndata: {json.dumps({'attempt': retry_count, 'max_retries': max_retries, 'delay': retry_delay, 'message': retry_message})}\n\n"

# Wait before retrying
time.sleep(retry_delay)
continue  # Back to retry loop
```

#### 4. Failure Handling

```python
else:
    # Max retries exceeded or non-rate-limit error
    if retry_count >= max_retries:
        error_message = f"Maximum retries exceeded ({max_retries} attempts). The service is experiencing high load. Please try again in a few moments."
    else:
        error_message = f"An error occurred: {error_str}"

    # Send error to UI
    yield f"event: error\ndata: {json.dumps({'error': error_message, 'type': 'rate_limit' if is_rate_limit else 'general', 'retries': retry_count})}\n\n"
    break
```

### Frontend Changes

**File:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useAIStreamHandler.tsx`

#### 1. Retry Event Handling (Lines 506-513)

```typescript
// Handle retry events - show user we're retrying
if (chunk.event === 'retry') {
  const retryData = chunk as unknown as {
    attempt?: number
    max_retries?: number
    delay?: number
    message?: string
  }
  const statusMessage = retryData.message ||
    `Retrying... (Attempt ${retryData.attempt || 1}/${retryData.max_retries || 3})`

  console.log('🔄 RETRY EVENT:', statusMessage)
  setActivityStatus(statusMessage)  // Show in UI
  return // Don't process further
}
```

**Effect:**
- Activity indicator shows: "Rate limit reached. Retrying in 5 seconds... (Attempt 1/3)"
- User knows system is working, just waiting
- No confusion about frozen state

#### 2. Error Event Handling (Lines 515-523)

```typescript
// Handle error events - show error message to user
if (chunk.event === 'error') {
  const errorData = chunk as unknown as {
    error?: string
    type?: string
    retries?: number
  }
  const errorMessage = errorData.error || 'An error occurred'

  console.error('❌ ERROR EVENT:', errorMessage)
  setActivityStatus('')  // Clear activity status
  setStreamingErrorMessage(errorMessage)  // Show error banner
  return // Don't process further
}
```

**Effect:**
- Activity indicator clears
- Error banner appears with clear message
- User knows request failed and why

#### 3. Behind the Scenes Integration (Lines 333-348)

```typescript
case 'retry': // Backend retry notification
  const retryData = chunk as unknown as {
    attempt?: number
    max_retries?: number
    delay?: number
    message?: string
  }
  description = retryData.message ||
    `Retrying request (attempt ${retryData.attempt || 1}/${retryData.max_retries || 3})`
  status = 'in_progress'
  details.retryAttempt = retryData.attempt
  details.maxRetries = retryData.max_retries
  details.retryDelay = retryData.delay
  break

case 'error': // Backend error notification
  const errorData = chunk as unknown as {
    error?: string
    type?: string
    retries?: number
  }
  description = errorData.error || 'An error occurred'
  status = 'error'
  details.errorType = errorData.type
  details.retryAttempts = errorData.retries
  break
```

**Effect:**
- All retry attempts logged in timeline
- Shows exactly when retry occurred
- Shows delay and attempt number
- Error events show final failure with context

---

## User Experience

### Before Implementation

```
User: "What did I ask you before?"

[Behind the Scenes shows activity...]

[Silence...]

[No response ever arrives]

[User refreshes page]

[Session completely gone]

User: "WTF? Did it work or not?"
```

**Problems:**
- ❌ Silent failure
- ❌ No feedback
- ❌ Lost session
- ❌ Complete confusion

### After Implementation

#### Scenario 1: Successful Retry

```
User: "What did I ask you before?"

Activity: "Cirkelline is working..."
  ↓
Activity: "Rate limit reached. Retrying in 5 seconds... (Attempt 1/3)"
[User waits 5 seconds]
  ↓
Activity: "Cirkelline is responding..."
  ↓
Response: "You previously asked about [...]"
  ↓
Behind the Scenes:
  - get_previous_session_messages completed
  - Retry: Attempt 1/3 (5 second delay)
  - Response generation successful
```

**Result:**
- ✅ User informed of retry
- ✅ Clear progress indication
- ✅ Response delivered
- ✅ Session saved
- ✅ Full transparency

#### Scenario 2: Max Retries Exceeded

```
User: "What did I ask you before?"

Activity: "Cirkelline is working..."
  ↓
Activity: "Rate limit reached. Retrying in 5 seconds... (Attempt 1/3)"
[5 seconds]
  ↓
Activity: "Rate limit reached. Retrying in 10 seconds... (Attempt 2/3)"
[10 seconds]
  ↓
Activity: "Rate limit reached. Retrying in 20 seconds... (Attempt 3/3)"
[20 seconds]
  ↓
ERROR BANNER: "Maximum retries exceeded (3 attempts). The service is experiencing high load. Please try again in a few moments."
  ↓
Behind the Scenes:
  - get_previous_session_messages completed
  - Retry: Attempt 1/3 (5 second delay)
  - Retry: Attempt 2/3 (10 second delay)
  - Retry: Attempt 3/3 (20 second delay)
  - ERROR: Maximum retries exceeded
```

**Result:**
- ✅ User sees all retry attempts
- ✅ Clear error message explaining why
- ✅ User knows to try again later
- ✅ No confusion about system state
- ✅ Full visibility into what happened

### Retry Message Examples

| Attempt | Delay | Message |
|---------|-------|---------|
| 1 | 5s | "Rate limit reached. Retrying in 5 seconds... (Attempt 1/3)" |
| 2 | 10s | "Rate limit reached. Retrying in 10 seconds... (Attempt 2/3)" |
| 3 | 20s | "Rate limit reached. Retrying in 20 seconds... (Attempt 3/3)" |
| Failed | N/A | "Maximum retries exceeded (3 attempts). The service is experiencing high load. Please try again in a few moments." |

---

## Testing

### Test Cases

#### Test 1: Simple Query (No Rate Limit)

**Input:** "test"

**Expected:**
- ✅ Immediate response
- ✅ No retry events
- ✅ Session saved

**Verify:**
```bash
# Send request
curl -X POST http://localhost:7777/api/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "stream": true}'

# Check response arrives
# Check no retry events in stream
# Refresh page, verify session persists
```

#### Test 2: Session Retrieval Query (May Hit Rate Limit)

**Input:** "What did I ask you before?"

**Expected:**
- ⏳ Tool call `get_previous_session_messages` completes
- ⏳ May see retry event if quota hit
- ✅ Response eventually arrives (after retries)
- ✅ Session saved

**Verify:**
```bash
# Send request
curl -X POST http://localhost:7777/api/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What did I ask you before?", "stream": true, "session_id": "$SESSION_ID"}'

# Check Behind the Scenes events
# If 429 occurs, verify retry event appears
# Verify response arrives after retry
# Refresh page, verify session persists
```

#### Test 3: Forced Rate Limit (Simulate Quota Exhaustion)

**Setup:** Temporarily reduce API quota or make rapid requests

**Expected:**
- ⏳ Retry events appear
- ⏳ Shows delay countdown
- ⏳ Multiple retry attempts if needed
- ✅ Either succeeds after retry OR shows error message

**Verify:**
```python
# In my_os.py, temporarily add at start of event_generator:
raise ModelProviderError("429 RESOURCE_EXHAUSTED. retry in 2s")

# Then test to see retry logic activates
# Remove test code after verification
```

### Monitoring During Testing

**Backend Logs:**
```bash
tail -f backend.log | grep -E "(⚠️ Rate limit|🔄 RETRY|❌)"
```

**Look for:**
```
⚠️ Rate limit hit (attempt 1/3). Retrying in 5s...
⚠️ Rate limit hit (attempt 2/3). Retrying in 10s...
⚠️ Rate limit hit (attempt 3/3). Retrying in 20s...
❌ Maximum retries exceeded (3 attempts)
```

**Frontend Console:**
```javascript
// Look for:
🔄 RETRY EVENT: Rate limit reached. Retrying in 5 seconds... (Attempt 1/3)
❌ ERROR EVENT: Maximum retries exceeded...
```

**Behind the Scenes Timeline:**
- Check for retry events with attempt numbers
- Verify error events show proper context
- Confirm delay values match logs

### AWS Testing

After deployment, test on AWS specifically:

```bash
# Check CloudWatch logs
aws logs tail /ecs/cirkelline-system-backend --since 10m --region eu-north-1 --follow

# Look for retry sequences:
# 1. 429 error detected
# 2. Retry attempt logged
# 3. Sleep delay applied
# 4. Request retried
# 5. Either success OR next retry OR final error
```

---

## Deployment

### Pre-Deployment Checklist

- [ ] Backend retry logic tested on localhost
- [ ] Frontend displays retry status correctly
- [ ] Error messages show properly
- [ ] Behind the Scenes captures retry events
- [ ] Sessions persist after successful retry
- [ ] Error banner appears on max retries exceeded

### Version Numbers

**Backend:** Update version to `v1.2.18`
**Docker Image:** `cirkelline-system-backend:v1.2.18`
**ECS Task Definition:** Revision 60

### Deployment Steps

#### 1. Build Docker Image

```bash
cd ~/Desktop/cirkelline

# Build for linux/amd64 (AWS requires this)
docker build --platform linux/amd64 \
  -t 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.2.18 \
  -f Dockerfile .
```

**Verify build succeeded:**
```bash
docker images | grep v1.2.18
```

#### 2. Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region eu-north-1 | \
  docker login --username AWS --password-stdin \
  710504360116.dkr.ecr.eu-north-1.amazonaws.com

# Push image
docker push 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.2.18
```

**Verify push succeeded:**
```bash
aws ecr describe-images \
  --repository-name cirkelline-system-backend \
  --region eu-north-1 \
  --query 'imageDetails[?imageTags[?contains(@, `v1.2.18`)]]'
```

#### 3. Update Task Definition

**File:** `aws_deployment/task-definition.json`

**Change line 12:**
```json
"image": "710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.2.18"
```

**Register new task definition:**
```bash
aws ecs register-task-definition \
  --cli-input-json file://aws_deployment/task-definition.json \
  --region eu-north-1
```

**Verify registration:**
```bash
aws ecs describe-task-definition \
  --task-definition cirkelline-system-backend \
  --region eu-north-1 \
  --query 'taskDefinition.revision'
```

Should return: `60`

#### 4. Update ECS Service

```bash
aws ecs update-service \
  --cluster cirkelline-system-cluster \
  --service cirkelline-system-backend-service \
  --task-definition cirkelline-system-backend:60 \
  --force-new-deployment \
  --region eu-north-1
```

#### 5. Monitor Deployment

**Watch service status:**
```bash
watch -n 5 'aws ecs describe-services \
  --cluster cirkelline-system-cluster \
  --services cirkelline-system-backend-service \
  --region eu-north-1 \
  --query "services[0].deployments[*].[status,desiredCount,runningCount,taskDefinition]" \
  --output table'
```

**Wait for:**
- Old tasks draining
- New tasks starting
- Health checks passing
- Status: PRIMARY deployment with 1/1 running

**Check logs:**
```bash
aws logs tail /ecs/cirkelline-system-backend \
  --since 5m \
  --region eu-north-1 \
  --follow
```

**Look for:**
```
✅ Stage 4: AgentOS configured with base_app parameter
Monitoring: ENABLED
Session Summaries: ENABLED
Uvicorn running on http://0.0.0.0:7777
```

#### 6. Verify Health

```bash
# Test health endpoint
curl https://api.cirkelline.com/config

# Should return:
{
  "message": "Cirkelline AgentOS is running!",
  "version": "v1.2.18",
  ...
}
```

#### 7. Test Session Retrieval

```bash
# Get JWT token (login first)
TOKEN="your-jwt-token"

# Test session retrieval query
curl -N -X POST "https://api.cirkelline.com/api/teams/cirkelline/runs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What did I ask you before?", "stream": true, "session_id": "existing-session-id"}'

# Watch for:
# - event: retry (if 429 occurs)
# - event: run_content (response arriving)
# - Session persists after refresh
```

### Post-Deployment Verification

- [ ] Health endpoint responds
- [ ] Simple queries work ("test")
- [ ] Session retrieval queries work (with retries if needed)
- [ ] Retry events visible in stream
- [ ] Error messages display if retries fail
- [ ] Sessions persist after successful retry
- [ ] No 500 errors in CloudWatch logs
- [ ] Frontend displays retry status correctly

### Rollback Plan

If deployment fails:

```bash
# Revert to previous task definition
aws ecs update-service \
  --cluster cirkelline-system-cluster \
  --service cirkelline-system-backend-service \
  --task-definition cirkelline-system-backend:59 \
  --force-new-deployment \
  --region eu-north-1
```

---

## Monitoring

### Key Metrics

**Retry Rate:**
```bash
# Count retry events in last hour
aws logs filter-pattern "⚠️ Rate limit hit" \
  --log-group-name /ecs/cirkelline-system-backend \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --region eu-north-1 | wc -l
```

**Success After Retry:**
```bash
# Count successful completions after retry
aws logs filter-pattern "⚠️ Rate limit" \
  --log-group-name /ecs/cirkelline-system-backend \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --region eu-north-1 | \
  grep -A 5 "⚠️ Rate limit" | \
  grep "✅" | wc -l
```

**Max Retries Exceeded:**
```bash
# Count failures after max retries
aws logs filter-pattern "❌ Maximum retries exceeded" \
  --log-group-name /ecs/cirkelline-system-backend \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --region eu-north-1 | wc -l
```

### Alerts to Set Up

**High Retry Rate:**
```
WHEN retry_events_per_hour > 50
ALERT: "Unusual retry activity detected"
ACTION: Check Google API quota dashboard
```

**Retry Failure Rate:**
```
WHEN max_retries_exceeded_per_hour > 10
ALERT: "Multiple requests failing after retries"
ACTION: Investigate quota limits or API issues
```

**Average Retry Delay:**
```
TRACK: Average delay time from Google API
ALERT: If delay > 60s frequently
ACTION: May indicate sustained quota exhaustion
```

### CloudWatch Dashboard

Create dashboard with:
- Retry event count (1h, 24h)
- Success after retry count
- Max retries exceeded count
- Average retry delay
- Session persistence rate

### Log Patterns to Watch

**Healthy:**
```
✅ Response delivered without retry
✅ Retry successful on attempt 1
✅ Session saved after retry
```

**Warning:**
```
⚠️ Rate limit hit (attempt 1/3)
⚠️ Rate limit hit (attempt 2/3)
✅ Success on attempt 2
```

**Critical:**
```
⚠️ Rate limit hit (attempt 1/3)
⚠️ Rate limit hit (attempt 2/3)
⚠️ Rate limit hit (attempt 3/3)
❌ Maximum retries exceeded
```

---

## Technical Reference

### Error Response Format

**Retry Event:**
```json
{
  "event": "retry",
  "data": {
    "attempt": 1,
    "max_retries": 3,
    "delay": 5.0,
    "message": "Rate limit reached. Retrying in 5 seconds... (Attempt 1/3)"
  }
}
```

**Error Event:**
```json
{
  "event": "error",
  "data": {
    "error": "Maximum retries exceeded (3 attempts). The service is experiencing high load. Please try again in a few moments.",
    "type": "rate_limit",
    "retries": 3
  }
}
```

### Google API 429 Response

```json
{
  "error": {
    "code": 429,
    "message": "You exceeded your current quota...",
    "status": "RESOURCE_EXHAUSTED",
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.QuotaFailure",
        "violations": [{
          "quotaMetric": "generativelanguage.googleapis.com/generate_content_paid_tier_input_token_count",
          "quotaId": "GenerateContentPaidTierInputTokensPerModelPerMinute",
          "quotaDimensions": {
            "model": "gemini-2.5-flash",
            "location": "global"
          },
          "quotaValue": "1000000"
        }]
      },
      {
        "@type": "type.googleapis.com/google.rpc.RetryInfo",
        "retryDelay": "4.843473059s"
      }
    ]
  }
}
```

### Retry Delay Extraction Regex

```python
import re

error_message = "Please retry in 4.843473059s"
match = re.search(r'retry in (\d+(?:\.\d+)?)', error_message, re.IGNORECASE)

if match:
    retry_delay = float(match.group(1))  # 4.843473059
```

### Exponential Backoff Formula

```python
retry_delay = min(5 * (2 ** retry_count), 60)

# Results:
# Attempt 0: 5 seconds
# Attempt 1: 10 seconds
# Attempt 2: 20 seconds
# Attempt 3: 40 seconds
# Attempt 4: 60 seconds (capped)
```

---

## Future Improvements

### Short-term

1. **Retry Metrics Dashboard**
   - Track retry success rate
   - Monitor average delays
   - Alert on high failure rate

2. **User Preferences**
   - Allow users to configure max retries
   - Option to disable auto-retry
   - Custom retry delays

3. **Token Usage Optimization**
   - Limit conversation history tokens
   - Summarize old messages
   - Progressive context loading

### Long-term

1. **Intelligent Request Queuing**
   - Queue requests when quota near limit
   - Throttle non-urgent requests
   - Priority queue for user interactions

2. **Multi-Model Fallback**
   - Fall back to Claude if Gemini unavailable
   - Use smaller models for simple queries
   - Dynamic model selection based on quota

3. **Predictive Quota Management**
   - Track quota usage patterns
   - Predict when quota will be exceeded
   - Proactively slow request rate

4. **Conversation History Optimization**
   - Store conversation summaries
   - Only load relevant message windows
   - Compress old messages

---

## Related Documentation

- [01-ARCHITECTURE.md](./01-ARCHITECTURE.md) - System architecture overview
- [02-TROUBLESHOOTING.md](./02-TROUBLESHOOTING.md) - Common issues and solutions
- [03-AWS-DEPLOYMENT.md](./03-AWS-DEPLOYMENT.md) - AWS deployment procedures
- [05-BACKEND-REFERENCE.md](./05-BACKEND-REFERENCE.md) - Backend API reference
- [06-FRONTEND-REFERENCE.md](./06-FRONTEND-REFERENCE.md) - Frontend architecture
- [15-STREAMING-EVENT-FILTERING.md](./15-STREAMING-EVENT-FILTERING.md) - Event streaming guide

---

## Changelog

### v1.2.18 (2025-11-06)

**Added:**
- Automatic retry logic for 429 rate limit errors
- Exponential backoff with max 3 retries
- Real-time retry status display in UI
- Clear error messages when retries fail
- Full retry visibility in Behind the Scenes timeline
- Session persistence after successful retry

**Fixed:**
- Sessions no longer disappear after 429 errors
- Users now see retry progress instead of silent failure
- Clear error messaging when service unavailable

**Technical Details:**
- Backend: my_os.py lines 2573-2728
- Frontend: useAIStreamHandler.tsx lines 333-348, 506-523
- Added retry and error event handling
- Honors Google API retry delay recommendations

---

**Maintained By:** Development Team
**Last Reviewed:** 2025-11-06
**Next Review:** 2025-12-06
