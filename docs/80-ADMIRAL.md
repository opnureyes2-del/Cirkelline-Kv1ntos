# ADMIRAL v2.1.0
## Strategic Governance & Approval Workflow Orchestrator

**Part of:** ODIN v2.0.0 - The All-Father
**Date:** 2025-12-18
**Author:** Rasmus & Claude Opus 4.5
**Location:** `~/.claude-agent/admiral.py`

---

## OVERVIEW

The **Admiral** is the strategic governance layer of the ODIN ecosystem, providing policy enforcement, approval workflows, and system health oversight. It ensures all development activities comply with established standards and require appropriate authorization.

### Key Responsibilities

1. **GOVERN** - Define and enforce policies
2. **APPROVE** - Multi-tier approval workflow
3. **COORDINATE** - Orchestrate improvements
4. **MONITOR** - Track system health
5. **REPORT** - Generate strategic reports

### Governance Architecture

```
                ACTION REQUEST
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│                      ADMIRAL                              │
│                                                           │
│  ┌────────────────┐    ┌────────────────┐                │
│  │    POLICY      │    │    APPROVAL    │                │
│  │    ENGINE      │───▶│    WORKFLOW    │                │
│  └────────────────┘    └───────┬────────┘                │
│                                │                          │
│                                ▼                          │
│  ┌───────────────────────────────────────────────┐       │
│  │              TIER DETERMINATION               │       │
│  │                                               │       │
│  │  AUTO → GUARDIAN → ADMIRAL → SUPER_ADMIN     │       │
│  └───────────────────────────────────────────────┘       │
│                                                           │
└──────────────────────────────────────────────────────────┘
                      │
                      ▼
             APPROVED / REJECTED / ESCALATED
```

---

## INSTALLATION & FILES

### File Locations

| File | Purpose | Lines |
|------|---------|-------|
| `~/.claude-agent/admiral.py` | Core component | ~1,100 |
| `~/.claude-agent/admiral.db` | SQLite database | - |
| `~/.claude-agent/logs/admiral.log` | Log file | - |

### Dependencies

- Python 3.12+ (standard library only)
- Integration with Odin and Guardian

### Quick Verification

```bash
# Check version
python3 ~/.claude-agent/admiral.py --version
# Output: Admiral v2.1.0

# Check status
python3 ~/.claude-agent/admiral.py --status

# List policies
python3 ~/.claude-agent/admiral.py --policies

# Show pending approvals
python3 ~/.claude-agent/admiral.py --pending

# Generate health report
python3 ~/.claude-agent/admiral.py --health
```

---

## GOVERNANCE POLICIES

### Default Policies (9 total)

**Security Policies (MANDATORY/REQUIRED):**

| ID | Name | Enforcement | Description |
|----|------|-------------|-------------|
| POL_SEC_001 | No Hardcoded Secrets | MANDATORY | No passwords, API keys, or tokens in code |
| POL_SEC_002 | JWT Authentication Required | REQUIRED | All API endpoints must use JWT |
| POL_SEC_003 | No Eval or Exec | MANDATORY | No eval() or exec() with user input |

**Architecture Policies:**

| ID | Name | Enforcement | Description |
|----|------|-------------|-------------|
| POL_ARC_001 | User Isolation Pattern | MANDATORY | All data access filtered by user_id |
| POL_ARC_002 | Singleton Pattern for Services | RECOMMENDED | Core services use singleton pattern |

**Quality Policies:**

| ID | Name | Enforcement | Description |
|----|------|-------------|-------------|
| POL_QUAL_001 | Test Coverage Minimum | RECOMMENDED | Coverage should be ≥70% |
| POL_QUAL_002 | Function Size Limit | ADVISORY | Functions ≤50 lines |

**Documentation & Process:**

| ID | Name | Enforcement | Description |
|----|------|-------------|-------------|
| POL_DOC_001 | Public API Documentation | REQUIRED | Public functions must have docstrings |
| POL_PROC_001 | Code Review Required | REQUIRED | All changes must be reviewed |

### Enforcement Levels

| Level | Description | Bypass |
|-------|-------------|--------|
| MANDATORY | Cannot bypass under any circumstances | Never |
| REQUIRED | Must follow, Super Admin can override | Super Admin only |
| RECOMMENDED | Should follow, Admiral can override | Admiral+ |
| ADVISORY | Suggestion only, informational | Any |

---

## APPROVAL WORKFLOW

### Approval Tiers

```
┌─────────────────────────────────────────────────────────┐
│                   APPROVAL TIERS                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  AUTO          - Automatic approval for safe actions    │
│       ↓                                                 │
│  GUARDIAN      - Code Guardian review required          │
│       ↓                                                 │
│  ADMIRAL       - Admiral strategic decision             │
│       ↓                                                 │
│  SUPER_ADMIN   - Human approval mandatory               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Tier Determination Matrix

| Action Type | Risk Level | Policy Violations | Required Tier |
|-------------|------------|-------------------|---------------|
| Any | CRITICAL | Any | SUPER_ADMIN |
| Any | Any | MANDATORY violation | SUPER_ADMIN |
| SECURITY | Any | None | ADMIRAL |
| DEPLOYMENT | Any | None | ADMIRAL |
| AGENT_CREATE | Any | None | ADMIRAL |
| Any | HIGH | None | ADMIRAL |
| DATABASE | Any | None | GUARDIAN |
| CONFIG_CHANGE | Any | None | GUARDIAN |
| Any | MEDIUM | None | GUARDIAN |
| Any | SAFE/LOW | None | AUTO |

### Action Types

```python
class ActionType(Enum):
    CODE_CHANGE = "code_change"         # Code modifications
    CONFIG_CHANGE = "config_change"     # Configuration changes
    DEPLOYMENT = "deployment"           # Deployment actions
    DATABASE = "database"               # Database operations
    SECURITY = "security"               # Security-related
    AGENT_CREATE = "agent_create"       # Creating new agents
    SYSTEM_COMMAND = "system_command"   # System commands
    INTEGRATION = "integration"         # Integration operations
```

### Risk Levels

```python
class RiskLevel(Enum):
    SAFE = "safe"       # No risk
    LOW = "low"         # Minor risk
    MEDIUM = "medium"   # Moderate risk
    HIGH = "high"       # Significant risk
    CRITICAL = "critical"  # Maximum risk
```

---

## DATABASE SCHEMA

### Tables

**1. policies** - Governance policy definitions

```sql
CREATE TABLE policies (
    policy_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,         -- 'security', 'architecture', etc.
    description TEXT,
    enforcement TEXT DEFAULT 'recommended',
    rules TEXT DEFAULT '[]',        -- JSON array of rules
    violations_count INTEGER DEFAULT 0,
    last_violation TEXT,
    created_at TEXT,
    updated_at TEXT,
    enabled INTEGER DEFAULT 1,
    metadata TEXT DEFAULT '{}'
);
```

**2. approvals** - Approval requests

```sql
CREATE TABLE approvals (
    request_id TEXT PRIMARY KEY,
    action_type TEXT NOT NULL,
    action_description TEXT,
    risk_level TEXT DEFAULT 'low',
    required_tier TEXT DEFAULT 'auto',
    status TEXT DEFAULT 'pending',  -- pending, approved, rejected, escalated
    requester TEXT,
    target_file TEXT,
    changes TEXT,                   -- JSON
    policy_violations TEXT DEFAULT '[]',
    approved_by TEXT,
    approval_notes TEXT,
    created_at TEXT,
    resolved_at TEXT,
    expires_at TEXT,
    metadata TEXT DEFAULT '{}'
);
```

**3. governance_events** - Audit log

```sql
CREATE TABLE governance_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    policy_id TEXT,
    request_id TEXT,
    actor TEXT,
    description TEXT,
    severity TEXT DEFAULT 'info',
    timestamp TEXT,
    metadata TEXT DEFAULT '{}'
);
```

**4. health_reports** - System health snapshots

```sql
CREATE TABLE health_reports (
    report_id TEXT PRIMARY KEY,
    overall_status TEXT,
    components TEXT DEFAULT '{}',   -- JSON
    metrics TEXT DEFAULT '{}',      -- JSON
    issues TEXT DEFAULT '[]',       -- JSON
    recommendations TEXT DEFAULT '[]',
    generated_at TEXT,
    period_start TEXT,
    period_end TEXT
);
```

**5. improvement_plans** - System improvement tracking

```sql
CREATE TABLE improvement_plans (
    plan_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    target_components TEXT DEFAULT '[]',
    steps TEXT DEFAULT '[]',
    expected_benefit TEXT,
    effort_estimate TEXT DEFAULT 'moderate',
    priority INTEGER DEFAULT 3,
    status TEXT DEFAULT 'proposed',
    created_at TEXT,
    approved_at TEXT,
    completed_at TEXT
);
```

### Indexes

```sql
CREATE INDEX idx_policies_category ON policies(category);
CREATE INDEX idx_policies_enabled ON policies(enabled);
CREATE INDEX idx_approvals_status ON approvals(status);
CREATE INDEX idx_approvals_tier ON approvals(required_tier);
CREATE INDEX idx_approvals_requester ON approvals(requester);
CREATE INDEX idx_events_type ON governance_events(event_type);
CREATE INDEX idx_events_timestamp ON governance_events(timestamp);
CREATE INDEX idx_plans_status ON improvement_plans(status);
```

---

## CORE API

### Admiral Class

The main singleton class for governance operations.

#### Constructor

```python
admiral = get_admiral()  # Singleton accessor
```

#### check_policies(action_type, target, changes)

Check an action against governance policies.

```python
from admiral import get_admiral, ActionType

admiral = get_admiral()

result = admiral.check_policies(
    action_type=ActionType.CODE_CHANGE,
    target="/path/to/file.py",
    changes={"lines_added": 50}
)

print(f"Passed: {result.passed}")
print(f"Violations: {len(result.violations)}")
print(f"Required tier: {result.required_tier.value}")
```

#### request_approval(action_type, description, requester, ...)

Request approval for an action.

```python
request = admiral.request_approval(
    action_type=ActionType.DEPLOYMENT,
    action_description="Deploy new authentication system",
    requester="kv1nt",
    risk_level=RiskLevel.HIGH,
    target_file=None,
    changes={"feature": "auth_v2"},
    timeout_hours=24
)

print(f"Request ID: {request.request_id}")
print(f"Status: {request.status.value}")
print(f"Required tier: {request.required_tier.value}")
```

#### approve(request_id, approver, notes)

Approve a pending request.

```python
success = admiral.approve(
    request_id="abc123",
    approver="rasmus",
    notes="Reviewed and approved for production"
)
```

#### reject(request_id, rejector, reason)

Reject a pending request.

```python
success = admiral.reject(
    request_id="abc123",
    rejector="rasmus",
    reason="Security concerns not addressed"
)
```

#### escalate(request_id, escalator, reason)

Escalate to higher approval tier.

```python
success = admiral.escalate(
    request_id="abc123",
    escalator="kv1nt",
    reason="Requires Super Admin review for production deployment"
)
```

#### list_pending_approvals(tier, requester)

Get pending approval requests.

```python
# All pending
pending = admiral.list_pending_approvals()

# Pending at specific tier
pending = admiral.list_pending_approvals(tier=ApprovalTier.ADMIRAL)

# Pending by requester
pending = admiral.list_pending_approvals(requester="kv1nt")
```

#### generate_health_report(period_days)

Generate system health report.

```python
report = admiral.generate_health_report(period_days=7)

print(f"Overall: {report.overall_status.value}")
print(f"Components: {report.components}")
print(f"Metrics: {report.metrics}")
print(f"Recommendations: {report.recommendations}")
```

#### list_policies(category, enabled_only)

List governance policies.

```python
# All enabled policies
policies = admiral.list_policies()

# Security policies only
policies = admiral.list_policies(category=PolicyCategory.SECURITY)

# Include disabled
policies = admiral.list_policies(enabled_only=False)
```

---

## ENUMS

### PolicyCategory

```python
class PolicyCategory(Enum):
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    QUALITY = "quality"
    PROCESS = "process"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
```

### EnforcementLevel

```python
class EnforcementLevel(Enum):
    ADVISORY = "advisory"       # Suggestion only
    RECOMMENDED = "recommended" # Should follow
    REQUIRED = "required"       # Must follow
    MANDATORY = "mandatory"     # Cannot bypass
```

### ApprovalTier

```python
class ApprovalTier(Enum):
    AUTO = "auto"               # Automatic approval
    GUARDIAN = "guardian"       # Code Guardian review
    ADMIRAL = "admiral"         # Admiral decision
    SUPER_ADMIN = "super_admin" # Human approval
```

### ApprovalStatus

```python
class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
```

### HealthStatus

```python
class HealthStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
```

---

## DATACLASSES

### GovernancePolicy

```python
@dataclass
class GovernancePolicy:
    policy_id: str
    name: str
    category: PolicyCategory
    description: str
    enforcement: EnforcementLevel
    rules: List[Dict[str, Any]]
    violations_count: int = 0
    last_violation: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### ApprovalRequest

```python
@dataclass
class ApprovalRequest:
    request_id: str
    action_type: ActionType
    action_description: str
    risk_level: RiskLevel
    required_tier: ApprovalTier
    status: ApprovalStatus
    requester: str
    target_file: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    policy_violations: List[str] = field(default_factory=list)
    approved_by: Optional[str] = None
    approval_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### PolicyCheckResult

```python
@dataclass
class PolicyCheckResult:
    passed: bool
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    policies_checked: int
    highest_enforcement: Optional[EnforcementLevel] = None
    required_tier: ApprovalTier = ApprovalTier.AUTO
    timestamp: Optional[datetime] = None
```

### SystemHealthReport

```python
@dataclass
class SystemHealthReport:
    report_id: str
    overall_status: HealthStatus
    components: Dict[str, HealthStatus]
    metrics: Dict[str, Any]
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime
    period_start: datetime
    period_end: datetime
```

---

## TERMINAL COMMANDS

### Via KV1NTOS Daemon

```bash
# Show Admiral status
kv1nt admiral status

# Check policies for an action
kv1nt admiral check code_change /path/to/file.py

# Request approval
kv1nt admiral request deployment "Deploy auth v2" --risk high

# Approve pending request
kv1nt admiral approve <request_id> --notes "Approved"

# Reject pending request
kv1nt admiral reject <request_id> --reason "Security issue"

# List pending approvals
kv1nt admiral pending

# Generate health report
kv1nt admiral health
```

### Direct CLI

```bash
# Show version
python3 ~/.claude-agent/admiral.py --version

# Show status
python3 ~/.claude-agent/admiral.py --status

# List policies
python3 ~/.claude-agent/admiral.py --policies

# Show pending approvals
python3 ~/.claude-agent/admiral.py --pending

# Generate health report
python3 ~/.claude-agent/admiral.py --health
```

---

## INTEGRATION WITH KV1NTOS

The Admiral integrates with the KV1NTOS daemon:

### Daemon Methods

```python
# Access Admiral directly
@property
def admiral(self) -> Admiral:
    return self._admiral

# Get status
def admiral_status(self) -> str:
    return self._admiral.format_status()

# Check policies
def admiral_check_policies(self, action_type: str, target: str = None) -> dict:
    action = AdmiralActionType(action_type)
    result = self._admiral.check_policies(action, target)
    return result.to_dict()

# Request approval
def admiral_request_approval(
    self,
    action_type: str,
    description: str,
    requester: str = "kv1nt",
    risk_level: str = "low"
) -> dict:
    # ...

# Approve request
def admiral_approve(self, request_id: str, approver: str, notes: str = None) -> bool:
    return self._admiral.approve(request_id, approver, notes)

# Reject request
def admiral_reject(self, request_id: str, rejector: str, reason: str) -> bool:
    return self._admiral.reject(request_id, rejector, reason)

# List pending
def admiral_pending(self) -> list:
    pending = self._admiral.list_pending_approvals()
    return [p.to_dict() for p in pending]

# Health report
def admiral_health_report(self) -> dict:
    report = self._admiral.generate_health_report()
    return report.to_dict()
```

### MCP Bridge Registration

```python
self._mcp.register("admiral", self._admiral)
```

---

## INTEGRATION WITH ODIN & GUARDIAN

### Odin Integration

Admiral provides governance oversight for Odin's actions:

```python
# Before Odin executes a system command
policy_check = admiral.check_policies(
    action_type=ActionType.SYSTEM_COMMAND,
    target=command_target
)

if not policy_check.passed:
    # Request approval if violations found
    request = admiral.request_approval(...)
```

### Guardian Integration

Admiral receives suggestions from Guardian for policy compliance:

```python
# Guardian detects security issue
observation = guardian.observe(file_path)

# Admiral records as policy violation
if observation.severity == "critical":
    admiral.record_violation("POL_SEC_001")
```

---

## HEALTH MONITORING

### Component Health Checks

The Admiral monitors health of:

1. **Odin** - Ecosystem Commander status
2. **Guardian** - Code quality observations
3. **Admiral** - Approval backlog

### Health Metrics Collected

```python
metrics = {
    "approval_requests": 15,
    "approvals_approved": 10,
    "approvals_rejected": 3,
    "approvals_pending": 2,
    "total_policy_violations": 5,
    "policies_count": 9
}
```

### Health Status Determination

| Status | Condition |
|--------|-----------|
| EXCELLENT | All components healthy, no issues |
| GOOD | Minor warnings, no critical issues |
| WARNING | Some components degraded |
| DEGRADED | Multiple issues requiring attention |
| CRITICAL | System functionality impaired |

---

## BEST PRACTICES

### 1. Regular Policy Review

```bash
# Weekly policy review
python3 ~/.claude-agent/admiral.py --policies

# Check for violations
SELECT * FROM policies WHERE violations_count > 0;
```

### 2. Monitor Pending Approvals

```bash
# Daily check
python3 ~/.claude-agent/admiral.py --pending

# Set up alerts for stale requests
```

### 3. Generate Health Reports

```bash
# Weekly health report
python3 ~/.claude-agent/admiral.py --health
```

### 4. Review Governance Events

```bash
# Query event log
sqlite3 ~/.claude-agent/admiral.db \
  "SELECT * FROM governance_events ORDER BY timestamp DESC LIMIT 10"
```

---

## TROUBLESHOOTING

### Issue: "Policy check failing unexpectedly"

```python
# Check policy rules
policy = admiral.get_policy("POL_SEC_001")
print(policy.rules)

# Verify pattern matching
import re
with open(target_file) as f:
    content = f.read()
for rule in policy.rules:
    if re.search(rule["pattern"], content):
        print(f"Match: {rule}")
```

### Issue: "Approval requests timing out"

```bash
# Check timeout settings
cat ~/.claude-agent/admiral.py | grep timeout_hours

# Clean up expired requests
sqlite3 ~/.claude-agent/admiral.db \
  "UPDATE approvals SET status='expired' WHERE expires_at < datetime('now')"
```

### Issue: "Health report shows degraded"

```bash
# Check each component
python3 ~/.claude-agent/odin.py --status
python3 ~/.claude-agent/code_guardian.py --status
python3 ~/.claude-agent/admiral.py --pending
```

---

## CHANGELOG

### v2.1.0 (2025-12-18)
- Initial release as part of ODIN v2.0.0
- 9 default governance policies
- Multi-tier approval workflow (AUTO/GUARDIAN/ADMIRAL/SUPER_ADMIN)
- System health monitoring
- Integration with Odin and Guardian
- SQLite persistence (5 tables, 8 indexes)
- Full CLI interface
- KV1NTOS daemon integration (7 methods)

---

## ROADMAP

### v2.2.0 (Planned)
- Custom policy creation via CLI
- Policy templates for common scenarios
- Approval notification system
- Enhanced health metrics

### v3.0.0 (Future)
- Multi-device approval workflow
- Mobile notification integration
- AI-assisted policy suggestions
- Compliance reporting

---

*Admiral v2.1.0 - Part of ODIN v2.0.0 - The All-Father*
*"Strategic governance, unwavering oversight"*
