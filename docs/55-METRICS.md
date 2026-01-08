# 55. Token Usage Metrics System

**Version:** 1.0.0
**Last Updated:** 2025-11-26
**Status:** ✅ Production Ready

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [Backend Implementation](#backend-implementation)
5. [API Endpoints](#api-endpoints)
6. [Frontend Dashboard](#frontend-dashboard)
7. [Cost Calculations](#cost-calculations)
8. [Testing & Verification](#testing--verification)
9. [Deployment Guide](#deployment-guide)
10. [Future Enhancements](#future-enhancements)

---

## Overview

The Token Usage Metrics System provides comprehensive tracking, analytics, and cost monitoring for all AI model interactions in Cirkelline. Every message processed by the system is tracked with detailed token usage and cost information, enabling admins to monitor resource consumption and optimize spending.

### Key Features

- ✅ **Automatic Token Tracking** - Captures metrics for every request (streaming & non-streaming)
- ✅ **Per-Agent Breakdown** - Tracks usage for each agent individually (Cirkelline, Research Team, etc.)
- ✅ **Per-User Analytics** - Monitor token usage by individual users
- ✅ **Cost Calculations** - Accurate cost tracking based on Gemini 2.5 Flash Tier 1 pricing
- ✅ **Timeline Data** - Historical tracking for trend analysis
- ✅ **Cost Projections** - Daily, weekly, monthly, and yearly cost estimates
- ✅ **Admin Dashboard** - Beautiful, responsive UI for viewing all metrics
- ✅ **Flexible Filtering** - Filter by agent, user, or date range

### Pricing Model

**Gemini 2.5 Flash (Tier 1)**
- Input tokens: $0.075 per 1M tokens
- Output tokens: $0.30 per 1M tokens

---

## Architecture

### System Flow

```
User Message
    ↓
Custom Cirkelline Endpoint (/api/teams/cirkelline/runs)
    ↓
AGNO Agent/Team Execution
    ↓
Response Generated (with metrics object)
    ↓
Metrics Extraction & Storage
    ↓
PostgreSQL (ai.agno_sessions.metrics JSONB column)
    ↓
Admin API Endpoint (/api/admin/token-usage)
    ↓
Frontend Dashboard (/admin/metrics)
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
│  ┌────────────────────────────────────────────────┐    │
│  │  Admin Metrics Dashboard (/admin/metrics)      │    │
│  │  - Summary Cards                                │    │
│  │  - Agent Breakdown Table                        │    │
│  │  - User Analytics Table                         │    │
│  │  - Cost Projections                             │    │
│  │  - Filtering (agent_id, user_id, date)         │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                     API Layer                            │
│  ┌────────────────────────────────────────────────┐    │
│  │  GET /api/admin/token-usage                     │    │
│  │  - Query parameters: agent_id, user_id,        │    │
│  │    start_date, end_date, group_by               │    │
│  │  - Returns: summary, by_agent, by_user,        │    │
│  │    timeline, projections                        │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                  Business Logic Layer                    │
│  ┌────────────────────────────────────────────────┐    │
│  │  Metrics Capture (custom_cirkelline.py)        │    │
│  │  - Extract metrics from AGNO response           │    │
│  │  - Calculate costs                              │    │
│  │  - Store in database                            │    │
│  │  - Works for streaming & non-streaming          │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                   Database Layer                         │
│  ┌────────────────────────────────────────────────┐    │
│  │  ai.agno_sessions table                         │    │
│  │  - metrics JSONB column (array of objects)      │    │
│  │  - GIN index for fast queries                   │    │
│  │  - Each metric contains:                        │    │
│  │    * timestamp                                   │    │
│  │    * agent_id, agent_name, agent_type           │    │
│  │    * input/output/total tokens                  │    │
│  │    * input/output/total cost                    │    │
│  │    * model, message preview, response preview   │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Table: `ai.agno_sessions`

**New Column Added:**
```sql
ALTER TABLE ai.agno_sessions
ADD COLUMN IF NOT EXISTS metrics JSONB DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS idx_agno_sessions_metrics
ON ai.agno_sessions USING GIN (metrics);
```

### Metrics JSONB Structure

Each element in the `metrics` array is a JSON object:

```json
{
  "timestamp": "2025-11-26T13:08:38.490479",
  "agent_id": "cirkelline",
  "agent_name": "Cirkelline",
  "agent_type": "team",
  "input_tokens": 24730,
  "output_tokens": 125,
  "total_tokens": 24855,
  "model": "gemini-2.5-flash",
  "message_preview": "What is 12+8? (first 100 chars)",
  "response_preview": "20! Is there anything else I can help you with? (first 100 chars)",
  "input_cost": 0.00185475,
  "output_cost": 0.0000375,
  "total_cost": 0.00189225
}
```

### Index Performance

The GIN index enables fast queries on JSONB data:

```sql
-- Filter by agent_id
SELECT * FROM ai.agno_sessions
WHERE metrics @> '[{"agent_id": "cirkelline"}]'::jsonb;

-- Count total tokens per agent
SELECT
  metric->>'agent_name' as agent,
  SUM((metric->>'total_tokens')::bigint) as total_tokens
FROM ai.agno_sessions, jsonb_array_elements(metrics) as metric
GROUP BY metric->>'agent_name';
```

### Migration Script

Location: `/database_migrations/001_add_metrics_column.sql`

**To Apply:**
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -f /path/to/001_add_metrics_column.sql
```

---

## Backend Implementation

### 1. Metrics Capture (`cirkelline/endpoints/custom_cirkelline.py`)

#### Helper Functions

```python
def calculate_token_costs(input_tokens: int, output_tokens: int) -> dict:
    """Calculate costs for Gemini 2.5 Flash (Tier 1) token usage."""
    input_cost = (input_tokens / 1_000_000) * 0.075
    output_cost = (output_tokens / 1_000_000) * 0.30
    total_cost = input_cost + output_cost
    return {
        "input_cost": round(input_cost, 8),
        "output_cost": round(output_cost, 8),
        "total_cost": round(total_cost, 8)
    }

def create_metric_object(...) -> dict:
    """Create a standardized metric object for storage."""
    # Returns complete metric object with all fields

async def store_metrics_in_database(session_id: str, metric_object: dict):
    """Store metric object in agno_sessions.metrics JSONB array."""
    # Uses PostgreSQL JSONB concatenation operator ||
```

#### Non-Streaming Metrics Capture

```python
if response and hasattr(response, 'metrics') and response.metrics:
    metrics = response.metrics

    # Extract token counts (AGNO Metrics object has attributes)
    input_tokens = getattr(metrics, 'input_tokens', 0) or 0
    output_tokens = getattr(metrics, 'output_tokens', 0) or 0
    total_tokens = getattr(metrics, 'total_tokens', 0) or (input_tokens + output_tokens)
    model = getattr(metrics, 'model', 'gemini-2.5-flash') or 'gemini-2.5-flash'

    # Create and store metric
    metric_obj = create_metric_object(...)
    await store_metrics_in_database(actual_session_id, metric_obj)
```

#### Streaming Metrics Capture

```python
async def capture_streaming_metrics(session_id: str, message: str):
    """Background task to capture metrics after streaming completes."""
    await asyncio.sleep(2)  # Wait for AGNO to persist run data

    # Query session_data from database
    # Extract metrics from latest run
    # Store in metrics column
```

### 2. Response Validation

Added comprehensive validation before returning responses:

```python
# Validate response exists
if not response:
    raise HTTPException(status_code=500, detail="Failed to generate response")

# Validate content attribute
if not hasattr(response, 'content'):
    raise HTTPException(status_code=500, detail="Invalid response format")

# Validate content is not empty
if not response.content:
    raise HTTPException(status_code=500, detail="Empty response generated")

# Validate content is string
if not isinstance(response.content, str):
    raise HTTPException(status_code=500, detail="Invalid response content type")

# Validate content is JSON serializable
try:
    json.dumps(response.content)
except (TypeError, ValueError) as e:
    raise HTTPException(status_code=500, detail="Response content cannot be serialized")
```

---

## API Endpoints

### GET `/api/admin/token-usage`

Comprehensive token usage analytics endpoint for admin users.

#### Authentication

Requires JWT token with `is_admin: true`.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | string | No | Filter by specific agent (e.g., "cirkelline", "research-team") |
| `user_id` | string | No | Filter by specific user UUID |
| `start_date` | string (ISO 8601) | No | Filter from date |
| `end_date` | string (ISO 8601) | No | Filter to date |
| `group_by` | string | No | Group timeline data: "day", "week", or "month" |

#### Response Structure

```json
{
  "success": true,
  "data": {
    "summary": {
      "message_count": 1,
      "total_tokens": 24855,
      "input_tokens": 24730,
      "output_tokens": 125,
      "total_cost": 0.00189225,
      "input_cost": 0.00185475,
      "output_cost": 0.0000375
    },
    "by_agent": [
      {
        "agent_id": "cirkelline",
        "agent_name": "Cirkelline",
        "agent_type": "team",
        "message_count": 1,
        "total_tokens": 24855,
        "input_tokens": 24730,
        "output_tokens": 125,
        "total_cost": 0.00189225,
        "avg_tokens_per_message": 24855.0
      }
    ],
    "by_user": [
      {
        "user_id": "ee461076-8cbb-4626-947b-956f293cf7bf",
        "email": "opnureyes2@gmail.com",
        "display_name": "eenvy",
        "message_count": 1,
        "total_tokens": 24855,
        "total_cost": 0.00189225
      }
    ],
    "timeline": [],
    "projections": {
      "daily_average": 0.0019,
      "weekly_projection": 0.0132,
      "monthly_projection": 0.0568,
      "yearly_projection": 0.69
    },
    "filters_applied": {
      "agent_id": null,
      "user_id": null,
      "start_date": null,
      "end_date": null,
      "group_by": null
    }
  }
}
```

#### Example Requests

**Get all metrics:**
```bash
curl -X GET "http://localhost:7777/api/admin/token-usage" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Filter by agent:**
```bash
curl -X GET "http://localhost:7777/api/admin/token-usage?agent_id=cirkelline" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Filter by date range:**
```bash
curl -X GET "http://localhost:7777/api/admin/token-usage?start_date=2025-11-01&end_date=2025-11-30" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Get timeline grouped by day:**
```bash
curl -X GET "http://localhost:7777/api/admin/token-usage?group_by=day" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

#### Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Authentication required"
}
```

**403 Forbidden:**
```json
{
  "detail": "Admin access required"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to get token usage: <error message>"
}
```

---

## Frontend Dashboard

### Location

`/admin/metrics` - Accessible only to admin users

### Components

#### 1. Summary Cards (Top Row)

Four key metric cards:
- **Total Messages** - Count of all messages processed
- **Total Tokens** - Aggregate token usage (input + output breakdown)
- **Total Cost** - Cumulative cost in USD
- **Monthly Projection** - Estimated monthly cost

#### 2. Agent Filter (Top Right)

Dropdown to filter metrics by specific agent or view all agents aggregated.

#### 3. Agent Breakdown Table

Displays per-agent statistics:
- Agent name and type
- Message count
- Total tokens
- Average tokens per message
- Total cost

Sortable and scrollable for many agents.

#### 4. Top Users Table

Shows top 20 users by token usage:
- User display name and email
- Message count
- Total tokens used
- Total cost

Only displayed if not filtering by specific user.

#### 5. Cost Projections

Four projection cards:
- Daily Average
- Weekly Projection
- Monthly Projection (highlighted)
- Yearly Projection

Based on historical usage patterns.

### Design System

Uses existing Cirkelline design tokens:
- `light-surface` / `dark-surface` - Card backgrounds
- `light-text` / `dark-text` - Primary text
- `light-text-secondary` / `dark-text-secondary` - Secondary text
- `accent` - Highlights and interactive elements
- `border-primary` - Card borders

### Responsive Behavior

- Mobile: Single column layout
- Tablet: 2 columns for summary cards
- Desktop: 4 columns for summary cards
- Tables: Horizontal scroll on small screens

---

## Cost Calculations

### Pricing Formula

```typescript
const GEMINI_FLASH_PRICING = {
  INPUT_TOKENS_PER_MILLION: 0.075,   // $0.075 per 1M input tokens
  OUTPUT_TOKENS_PER_MILLION: 0.30    // $0.30 per 1M output tokens
}

function calculateCost(input_tokens: number, output_tokens: number): number {
  const input_cost = (input_tokens / 1_000_000) * GEMINI_FLASH_PRICING.INPUT_TOKENS_PER_MILLION
  const output_cost = (output_tokens / 1_000_000) * GEMINI_FLASH_PRICING.OUTPUT_TOKENS_PER_MILLION
  return input_cost + output_cost
}
```

### Example Calculation

**Scenario:** 24,730 input tokens + 125 output tokens

```
Input cost:  (24,730 / 1,000,000) × $0.075 = $0.00185475
Output cost: (125 / 1,000,000) × $0.30 = $0.0000375
Total cost:  $0.00189225
```

### Projection Calculations

```python
# Get date range
days_span = (max_date - min_date).days + 1

# Calculate daily average
daily_avg = total_cost / max(days_span, 1)

# Project forward
projections = {
    "daily_average": daily_avg,
    "weekly_projection": daily_avg * 7,
    "monthly_projection": daily_avg * 30,
    "yearly_projection": daily_avg * 365
}
```

---

## Testing & Verification

### Backend Testing

**1. Test Metrics Capture:**
```bash
# Send a test message
TOKEN="<your-jwt-token>"
curl -X POST http://localhost:7777/api/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 12+8?", "stream": false}'
```

**2. Verify Database Storage:**
```sql
SELECT
  session_id,
  jsonb_array_length(metrics) as metric_count,
  metrics->-1->>'total_tokens' as latest_tokens,
  metrics->-1->>'total_cost' as latest_cost
FROM ai.agno_sessions
WHERE metrics IS NOT NULL
ORDER BY created_at DESC
LIMIT 5;
```

**3. Test API Endpoint:**
```bash
TOKEN="<admin-jwt-token>"

# Get all metrics
curl -s -X GET "http://localhost:7777/api/admin/token-usage" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Filter by agent
curl -s -X GET "http://localhost:7777/api/admin/token-usage?agent_id=cirkelline" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.summary'
```

### Frontend Testing

**1. Access Dashboard:**
- Login as admin user
- Navigate to `/admin/metrics`
- Verify all cards display correctly

**2. Test Filtering:**
- Select different agents from dropdown
- Verify metrics update correctly

**3. Verify Calculations:**
- Check that token counts match backend data
- Verify cost calculations are accurate
- Confirm projections make sense

### Expected Results

**Test Message:** "What is 12+8?"

- **Tokens:** ~24,855 total (24,730 input + 125 output)
- **Cost:** ~$0.00189225
- **Response Time:** < 3 seconds (non-streaming)
- **Database:** Metrics stored within 2 seconds

---

## Deployment Guide

### Prerequisites

- PostgreSQL 16+ with JSONB support
- Backend deployed with updated code
- Frontend deployed with new metrics page
- Admin user accounts configured

### Deployment Steps

#### 1. Database Migration

```bash
# Connect to database
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline

# Run migration
\i /database_migrations/001_add_metrics_column.sql

# Verify column exists
\d ai.agno_sessions

# Verify index exists
\di ai.idx_agno_sessions_metrics
```

#### 2. Backend Deployment

**Local:**
```bash
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py
```

**AWS ECS:**
```bash
# Build Docker image
docker build --platform linux/amd64 \
  -t 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.2.33 .

# Push to ECR
aws ecr get-login-password --region eu-north-1 | \
  docker login --username AWS --password-stdin \
  710504360116.dkr.ecr.eu-north-1.amazonaws.com

docker push 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.2.33

# Update ECS service
aws ecs update-service \
  --cluster cirkelline-system-cluster \
  --service cirkelline-system-backend-service \
  --force-new-deployment \
  --region eu-north-1
```

#### 3. Frontend Deployment

**Vercel:**
```bash
cd ~/Desktop/cirkelline/cirkelline-ui

# Build
pnpm build

# Deploy
vercel --prod
```

**Manual:**
```bash
# Push to GitHub
git add .
git commit -m "feat: Add token usage metrics system"
git push origin main

# Vercel auto-deploys from GitHub
```

#### 4. Verification

**Check Backend:**
```bash
curl https://api.cirkelline.com/api/admin/token-usage \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**Check Frontend:**
- Visit https://cirkelline.com/admin/metrics
- Login as admin
- Verify dashboard loads
- Send test message
- Refresh metrics page
- Confirm new metrics appear

### Rollback Plan

If issues occur:

**1. Database Rollback:**
```sql
ALTER TABLE ai.agno_sessions DROP COLUMN IF EXISTS metrics;
DROP INDEX IF EXISTS idx_agno_sessions_metrics;
```

**2. Backend Rollback:**
```bash
# Revert to previous ECS task definition
aws ecs update-service \
  --cluster cirkelline-system-cluster \
  --service cirkelline-system-backend-service \
  --task-definition cirkelline-system-backend:<previous-version> \
  --region eu-north-1
```

**3. Frontend Rollback:**
- Revert Git commit
- Redeploy to Vercel

---

## Future Enhancements

### Short-Term (1-2 months)

1. **Export Functionality**
   - CSV export of metrics data
   - PDF reports for stakeholders
   - Email scheduled reports

2. **Advanced Filtering**
   - Multiple agent selection
   - Custom date ranges with calendar picker
   - Saved filter presets

3. **Visualization Improvements**
   - Line charts for timeline data
   - Pie charts for agent distribution
   - Cost trends over time

4. **Alerts & Notifications**
   - Email alerts when costs exceed threshold
   - Slack integration for daily summaries
   - Budget warnings

### Medium-Term (3-6 months)

1. **Usage Quotas**
   - Per-user token limits
   - Per-agent budget allocation
   - Automatic throttling when limits reached

2. **Cost Optimization**
   - Identify expensive queries
   - Suggest prompt optimizations
   - A/B testing for efficiency

3. **Predictive Analytics**
   - ML-based cost predictions
   - Anomaly detection for unusual usage
   - Capacity planning recommendations

4. **Multi-Model Support**
   - Track multiple AI models separately
   - Compare model costs and performance
   - Automatic model selection based on cost/quality

### Long-Term (6-12 months)

1. **Enterprise Features**
   - Department-level tracking
   - Cost center allocation
   - Charge-back reports

2. **Advanced Analytics**
   - User behavior patterns
   - Peak usage time analysis
   - Efficiency benchmarking

3. **Integration**
   - Billing system integration
   - Accounting software export
   - Third-party analytics tools

---

## Troubleshooting

### Common Issues

**1. Metrics Not Capturing**

**Symptoms:** No metrics in database after sending messages

**Causes:**
- AGNO response doesn't include metrics object
- Database connection issues
- Metrics extraction errors

**Solutions:**
```bash
# Check server logs
tail -f /tmp/cirkelline.log | grep "Metrics"

# Verify database connection
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT 1;"

# Check column exists
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "\d ai.agno_sessions"
```

**2. Dashboard Not Loading**

**Symptoms:** Blank page or loading spinner never stops

**Causes:**
- API endpoint returning errors
- CORS issues
- JWT token expired

**Solutions:**
```bash
# Check API endpoint directly
curl -X GET "http://localhost:7777/api/admin/token-usage" \
  -H "Authorization: Bearer <TOKEN>"

# Check browser console for errors
# Check network tab for failed requests
```

**3. Incorrect Cost Calculations**

**Symptoms:** Costs don't match expected values

**Causes:**
- Wrong pricing tier
- Token count extraction issues
- Rounding errors

**Solutions:**
```sql
-- Verify stored data
SELECT
  metrics->-1->>'input_tokens' as input,
  metrics->-1->>'output_tokens' as output,
  metrics->-1->>'total_cost' as cost
FROM ai.agno_sessions
WHERE metrics IS NOT NULL
LIMIT 1;

-- Manually calculate
-- (input / 1000000) * 0.075 + (output / 1000000) * 0.30 = expected cost
```

**4. Performance Issues**

**Symptoms:** Slow dashboard loading

**Causes:**
- Large metrics arrays
- Missing database index
- Inefficient queries

**Solutions:**
```sql
-- Check index exists and is being used
EXPLAIN ANALYZE
SELECT * FROM ai.agno_sessions
WHERE metrics @> '[{"agent_id": "cirkelline"}]'::jsonb;

-- If index not used, recreate
DROP INDEX IF EXISTS idx_agno_sessions_metrics;
CREATE INDEX idx_agno_sessions_metrics ON ai.agno_sessions USING GIN (metrics);

-- Vacuum and analyze
VACUUM ANALYZE ai.agno_sessions;
```

---

## Support & Maintenance

### Monitoring

**Key Metrics to Watch:**
- Metrics capture success rate (should be 100%)
- API endpoint response time (should be < 500ms)
- Database query performance (should be < 100ms)
- Dashboard load time (should be < 2s)

**Logging:**
```bash
# Backend logs
tail -f /tmp/cirkelline.log | grep -E "(Metrics|Token)"

# Database logs
docker logs cirkelline-postgres | grep ERROR
```

### Backup & Recovery

**Database Backup:**
```bash
# Backup just metrics
docker exec -t cirkelline-postgres pg_dump \
  -U cirkelline -d cirkelline \
  --table=ai.agno_sessions \
  --data-only \
  > agno_sessions_backup.sql

# Restore
docker exec -i cirkelline-postgres psql \
  -U cirkelline -d cirkelline \
  < agno_sessions_backup.sql
```

### Maintenance Tasks

**Monthly:**
- Review cost trends
- Optimize expensive queries
- Archive old metrics (if needed)
- Update projections

**Quarterly:**
- Analyze agent performance
- Review user usage patterns
- Plan capacity upgrades
- Update documentation

---

## Conclusion

The Token Usage Metrics System provides comprehensive visibility into AI resource consumption and costs. With automatic tracking, detailed analytics, and beautiful visualizations, admins can effectively monitor and optimize their AI spending.

**Key Takeaways:**
- ✅ Fully automated - no manual tracking required
- ✅ Real-time data - metrics captured with every request
- ✅ Comprehensive - tracks all agents and users
- ✅ Actionable - provides projections and breakdowns
- ✅ Scalable - efficient database design with indexing

**Questions or Issues?**
- Check [Troubleshooting](#troubleshooting) section
- Review server logs
- Contact Ivo (opnureyes2@gmail.com)

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-26
**Next Review:** 2025-12-26
