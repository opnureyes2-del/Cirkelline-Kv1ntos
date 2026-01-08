# AGNO Run Metadata & Metrics Documentation

> **Source:** https://docs.agno.com/basics/agents/usage/agent-run-metadata
> **Related:** https://docs.agno.com/basics/sessions/metrics/overview
> **Last Updated:** 2025-11-29

---

## Overview

Every agent run has two types of associated data:

| Type | Description | Source |
|------|-------------|--------|
| **Metadata** | Custom business context (tags, IDs, priorities) | You provide |
| **Metrics** | System measurements (tokens, duration, latency) | AGNO automatic |

Together, they enable comprehensive tracking, analytics, and operational visibility.

---

## Run Metadata (Custom Business Context)

### What Is It?

Metadata lets you attach custom key-value pairs to runs for tracking purposes. Think of it as labeling packages for shipment tracking.

### How to Use

```python
response = agent.run(
    "Help me with my billing issue",
    metadata={
        # Business tracking
        "ticket_id": "SUP-2024-001234",
        "priority": "high",
        "request_type": "billing_support",

        # Customer context
        "customer_tier": "enterprise",
        "customer_id": "cust_abc123",

        # Operational info
        "department": "support",
        "sla_deadline": "2024-01-15T14:00:00Z",
        "escalation_level": 2,

        # Analytics
        "business_impact": "critical",
        "estimated_resolution_time_minutes": 30
    }
)
```

### Common Metadata Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `ticket_id` | Link to external ticketing system | "SUP-2024-001234" |
| `priority` | Urgency level | "high", "medium", "low" |
| `request_type` | Categorize the request | "billing", "technical", "sales" |
| `customer_tier` | Customer classification | "enterprise", "pro", "free" |
| `customer_id` | Link to customer record | "cust_abc123" |
| `user_id` | User identifier | "user_xyz789" |
| `department` | Handling department | "support", "engineering" |
| `sla_deadline` | Time-sensitive deadline | ISO 8601 timestamp |
| `escalation_level` | Support tier | 1, 2, 3 |
| `business_impact` | Criticality | "critical", "high", "normal" |
| `agent_version` | Track agent versions | "v1.2.3" |
| `environment` | Deployment context | "production", "staging" |

### Use Cases

1. **Support Ticket Integration**
   - Link AI runs to helpdesk tickets
   - Track resolution times per ticket

2. **SLA Monitoring**
   - Attach deadlines to runs
   - Alert on at-risk responses

3. **Customer Analytics**
   - Analyze usage by tier
   - Identify high-value customer patterns

4. **Compliance/Audit**
   - Tag runs for regulatory purposes
   - Maintain audit trails

5. **A/B Testing**
   - Tag runs with experiment IDs
   - Compare performance across variants

---

## Run Metrics (Automatic System Measurements)

### What Is It?

AGNO automatically collects performance and usage data for every run. No configuration needed.

### Available Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `input_tokens` | int | Tokens sent to model |
| `output_tokens` | int | Tokens received from model |
| `total_tokens` | int | Sum of input + output |
| `duration` | float | Run time in seconds |
| `time_to_first_token` | float | Latency to first response (seconds) |
| `reasoning_tokens` | int | Tokens used for reasoning (if applicable) |
| `cache_read_tokens` | int | Tokens read from cache |
| `cache_write_tokens` | int | Tokens written to cache |
| `audio_input_tokens` | int | Audio input tokens |
| `audio_output_tokens` | int | Audio output tokens |
| `audio_total_tokens` | int | Sum of audio tokens |
| `provider_metrics` | dict | Provider-specific data |

### Accessing Metrics

```python
from agno.agent import Agent
from agno.models.google import Gemini
from agno.db.postgres import PostgresDb

agent = Agent(
    model=Gemini(id="gemini-2.5-flash"),
    db=PostgresDb(...),
)

response = agent.run("What's the news?")

# Per-run metrics
print(response.metrics.to_dict())
# {
#     "input_tokens": 150,
#     "output_tokens": 500,
#     "total_tokens": 650,
#     "duration": 2.3,
#     "time_to_first_token": 0.4,
#     ...
# }
```

---

## Metrics at Multiple Levels

AGNO provides metrics at three levels of granularity:

```
Session (full conversation)
├── Run 1 (first user message)
│   ├── Message 1 (assistant) → metrics
│   ├── Message 2 (tool call) → metrics
│   └── Message 3 (assistant) → metrics
├── Run 2 (second user message)
│   └── Message 1 (assistant) → metrics
└── Session Metrics (aggregated totals)
```

### Per-Message Metrics

```python
for message in response.messages:
    if message.role == "assistant":
        print(f"Message content: {message.content[:50]}...")
        print(f"Metrics: {message.metrics.to_dict()}")
```

### Per-Run Metrics

```python
# Aggregated metrics for the entire run
print(response.metrics.to_dict())
```

### Per-Session Metrics

```python
# Aggregated metrics across all runs in session
session_metrics = agent.get_session_metrics()
print(session_metrics.to_dict())
```

---

## Team Metrics

Teams have additional aggregation levels:

```python
from agno.team import Team

team = Team(
    members=[agent1, agent2],
    store_member_responses=True,  # Enable member-level metrics
)

response = team.run("Research this topic")

# Team-level metrics (aggregated across all members)
print(response.metrics.to_dict())

# Per-member metrics (if store_member_responses=True)
for member_response in response.member_responses:
    print(f"{member_response.agent_id}: {member_response.metrics.to_dict()}")
```

---

## Practical Examples

### Example 1: Cost Tracking

```python
# Gemini 2.5 Flash pricing
INPUT_COST_PER_1M = 0.075  # $0.075 per 1M input tokens
OUTPUT_COST_PER_1M = 0.30   # $0.30 per 1M output tokens

response = agent.run("Analyze this data...")

input_cost = (response.metrics.input_tokens / 1_000_000) * INPUT_COST_PER_1M
output_cost = (response.metrics.output_tokens / 1_000_000) * OUTPUT_COST_PER_1M
total_cost = input_cost + output_cost

print(f"Run cost: ${total_cost:.6f}")
```

### Example 2: Performance Monitoring

```python
response = agent.run("Quick question")

metrics = response.metrics
print(f"Duration: {metrics.duration:.2f}s")
print(f"Time to first token: {metrics.time_to_first_token:.2f}s")

if metrics.duration > 5.0:
    alert("Slow response detected!")
```

### Example 3: SLA Compliance

```python
response = agent.run(
    "Urgent billing issue",
    metadata={
        "ticket_id": "TKT-123",
        "sla_target_seconds": 3.0,
        "priority": "high"
    }
)

if response.metrics.duration > 3.0:
    escalate_ticket("TKT-123", "SLA breach")
```

### Example 4: Analytics Dashboard

```python
# Collect metrics for dashboard
run_data = {
    "timestamp": datetime.now().isoformat(),
    "session_id": session_id,
    "user_id": user_id,

    # Custom metadata
    "customer_tier": metadata.get("customer_tier"),
    "request_type": metadata.get("request_type"),

    # System metrics
    "input_tokens": response.metrics.input_tokens,
    "output_tokens": response.metrics.output_tokens,
    "duration": response.metrics.duration,
    "ttft": response.metrics.time_to_first_token,
}

# Send to analytics system
analytics.track("agent_run", run_data)
```

---

## V2 Metric Changes

If migrating from AGNO v1, note these changes:

| V1 Field | V2 Field |
|----------|----------|
| `time` | `duration` |
| `audio_tokens` | `audio_total_tokens` |
| `input_audio_tokens` | `audio_input_tokens` |
| `output_audio_tokens` | `audio_output_tokens` |
| `cached_tokens` | `cache_read_tokens` |
| `prompt_tokens` | `input_tokens` |
| `completion_tokens` | `output_tokens` |

**Deprecated:** `prompt_tokens_details`, `completion_tokens_details` (moved to `provider_metrics`)

---

## Best Practices

### 1. Use Consistent Metadata Keys

```python
# Define standard keys for your organization
METADATA_SCHEMA = {
    "ticket_id": str,
    "priority": ["low", "medium", "high", "critical"],
    "customer_tier": ["free", "pro", "enterprise"],
    "department": str,
}
```

### 2. Track Costs Per Customer/Feature

```python
metadata = {
    "customer_id": customer_id,
    "feature": "document_analysis",
}

# Later, aggregate costs by customer_id and feature
```

### 3. Set Up Alerts on Metrics

```python
if response.metrics.duration > SLA_THRESHOLD:
    send_alert(f"SLA breach: {response.metrics.duration}s")

if response.metrics.total_tokens > TOKEN_BUDGET:
    send_alert(f"Token budget exceeded: {response.metrics.total_tokens}")
```

### 4. Store Metrics for Analysis

```python
# Store in database for historical analysis
db.insert("run_metrics", {
    "run_id": response.run_id,
    "session_id": session_id,
    "metrics": response.metrics.to_dict(),
    "metadata": metadata,
    "timestamp": datetime.now()
})
```

---

## Summary

| Feature | How to Use | What You Get |
|---------|------------|--------------|
| Metadata | `agent.run(msg, metadata={...})` | Custom business context |
| Run Metrics | `response.metrics` | Token usage, duration, latency |
| Message Metrics | `message.metrics` | Per-message breakdown |
| Session Metrics | `agent.get_session_metrics()` | Aggregated session totals |
| Team Metrics | `team_response.metrics` | Team-wide aggregation |

**Key Insight:** Metadata connects AI runs to your business context. Metrics give you operational visibility. Together, they enable comprehensive analytics, cost tracking, and SLA monitoring.
