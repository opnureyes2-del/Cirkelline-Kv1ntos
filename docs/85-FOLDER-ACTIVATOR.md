# Folder Activator & Codeword Manager v2.6.0

## ODIN v2.0.0+ - The All-Father
### Phase 5 Iteration 3: Event-Driven Commander Activation & AWS Authorization

**Date:** 2025-12-18
**Version:** 2.6.0
**Status:** ACTIVE
**Author:** Rasmus & Claude Opus 4.5

---

## OVERVIEW

Phase 5 Iteration 3 implements intelligent folder monitoring and secure AWS deployment authorization within the KV1NTOS/ODIN ecosystem. This enables event-driven activation of Commander Units when folders are accessed, with codeword-based security for production deployments.

### New Components

| Component | File | Lines | Purpose |
|-----------|------|-------|---------
| **Folder Activator** | `folder_activator.py` | ~2,000 | Event-driven folder monitoring with 7 optimizations |
| **Codeword Manager** | `codeword_manager.py` | ~620 | AWS deployment authorization with single-use tokens |

### Updated Components

| Component | Changes |
|-----------|---------|
| **KV1NT Daemon** | 17 new methods for folder & codeword management |
| **VERSION** | Updated to 2.6.0 |
| **Component Count** | 36 → 38 components |

---

## THE 7 SUPER ADMIN MANDATED OPTIMIZATIONS

### 1. Event-Driven Monitoring

**Directive:** "Din Folder Activator skal danse til rytmen af systemets egne filsystem-events"

**Implementation:**
- **INotify (Linux)**: Primary watcher using `inotify_simple` for instant response
- **Watchdog (Cross-platform)**: Fallback using `watchdog` library
- **Polling (Final fallback)**: Traditional polling when others unavailable

```python
# Priority order
if INOTIFY_AVAILABLE:
    watcher = INotifyWatcher(path, callback)
elif WATCHDOG_AVAILABLE:
    watcher = WatchdogWatcher(path, callback)
else:
    watcher = PollingWatcher(path, callback, interval=1.0)
```

**Events monitored:** ACCESS, MODIFY, CREATE, DELETE, MOVE, OPEN, CLOSE, ATTRIB

### 2. Smart Caching & Indexing

**Directive:** "Implementer en smart cache og indeksering af kendte Commander Unit mapper"

**Implementation:**
- `FolderCache` class with indexed lookups
- Path → folder_id index for O(1) access
- Type → [folder_ids] index for type-based queries
- Loaded at daemon startup from database
- No full directory scans needed

```python
class FolderCache:
    def __init__(self):
        self._path_index: Dict[str, str] = {}      # path → folder_id
        self._type_index: Dict[FolderType, List[str]] = {}  # type → [folder_ids]
        self._configs: Dict[str, FolderConfig] = {}  # folder_id → config
```

### 3. Dynamic Scope Adjustment (Resource-Aware)

**Directive:** "Dynamisk og ressourcebevidst orkestrering"

**Implementation:**
- `ResourceMonitor` tracks CPU, memory, and disk usage
- Automatic scope adjustment based on resource levels:

| Resource Level | Monitoring Mode |
|----------------|-----------------|
| NORMAL | FULL (all events) |
| HIGH | REDUCED (important events) |
| CRITICAL | MINIMAL (critical only) |

```python
def _on_resource_level_change(self, level: ResourceLevel):
    if level == ResourceLevel.CRITICAL:
        self._set_all_folders_mode(MonitoringMode.MINIMAL)
    elif level == ResourceLevel.HIGH:
        self._set_all_folders_mode(MonitoringMode.REDUCED)
    else:
        self._restore_folder_modes()
```

### 4. Distributed Event Bus Integration (AWS/Git)

**Directive:** "Indfør en letvægts, distribueret event-bus"

**Implementation:**
- `EventBus` class with publish/subscribe pattern
- Local folder events
- Git repository events (via hooks)
- AWS events (SQS/SNS ready)

```python
class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._message_queue: queue.Queue = queue.Queue()

    def publish(self, topic: str, message: EventBusMessage):
        # Notify all subscribers

    def subscribe(self, topic: str, callback: Callable):
        # Add subscriber
```

**Topics:**
- `folder.accessed`, `folder.modified`, `folder.activated`
- `git.push`, `git.commit`
- `aws.deploy`, `aws.update`

### 5. Audit Trail & Reporting

**Directive:** "Føre en præcis revisionslog"

**Implementation:**
- Every folder activation logged with:
  - Timestamp
  - Device/user context
  - Event type that triggered activation
  - Duration and outcome
- Queryable audit trail per folder

```python
@dataclass
class AuditEntry:
    audit_id: str
    folder_id: str
    event_type: EventType
    triggered_by: str           # Device/user
    context: str                # Additional context
    timestamp: datetime
    duration_ms: Optional[int]
    outcome: str
    details: Dict[str, Any]
```

### 6. Granular Configuration Management

**Directive:** "Granulær konfigurationsstyring via Agent Factory interface"

**Implementation:**
- Per-folder configuration with:
  - Priority level (1-10)
  - Monitoring mode
  - Event filters
  - Activation hooks
  - Custom metadata

```python
@dataclass
class FolderConfig:
    folder_id: str
    name: str
    path: Path
    folder_type: FolderType
    priority: int = 5
    monitoring_mode: MonitoringMode = MonitoringMode.FULL
    event_filters: List[EventType] = field(default_factory=list)
    activation_hooks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 7. Self-Healing & Restart Logic

**Directive:** "Selvhelende og genstartslogik"

**Implementation:**
- `SelfHealer` class with:
  - Error tracking with decay over time
  - Recovery procedures for common failures
  - Restart procedures for critical failures
  - Health status monitoring

```python
class SelfHealer:
    MAX_ERRORS = 5
    ERROR_DECAY_SECONDS = 300  # Errors "heal" after 5 minutes

    async def handle_error(self, component: str, error: Exception):
        # Track error
        # If threshold exceeded, trigger recovery
        # If recovery fails, trigger restart
```

---

## FOLDER ACTIVATOR

### Folder Types

| Type | Description |
|------|-------------|
| `COMMANDER_UNIT` | Commander Unit folders that activate on access |
| `GIT_REPO` | Git repository working copies |
| `AWS_ENVIRONMENT` | AWS environment configurations |
| `LOCALSTACK` | Localstack development environments |
| `PROJECT` | General project folders |
| `CUSTOM` | Custom folder types |

### Monitoring Modes

| Mode | Events Captured |
|------|-----------------|
| `FULL` | All events (ACCESS, MODIFY, CREATE, DELETE, etc.) |
| `REDUCED` | Important events (MODIFY, CREATE, DELETE) |
| `MINIMAL` | Critical events (DELETE only) |
| `SUSPENDED` | No monitoring |

### Activation Flow

```
1. Folder Event Detected (inotify/watchdog/polling)
   ↓
2. Event Debouncing (100ms default)
   ↓
3. Device Verification (Super Admin check via ODIN)
   ↓
4. Audit Trail Entry Created
   ↓
5. Commander Unit Activation (if applicable)
   ↓
6. Event Bus Notification
   ↓
7. Flock Summoning (if configured)
```

### CLI Usage

```bash
# Show status
python folder_activator.py status

# List monitored folders
python folder_activator.py folders

# View audit trail
python folder_activator.py audit [folder_id]

# View statistics
python folder_activator.py stats
```

### Database: `folder_activator.db`

**Tables:**
- `folder_configs` - Folder registration and configuration
- `folder_states` - Current folder states
- `activation_events` - Activation history
- `audit_trail` - Complete audit log
- `resource_snapshots` - Resource monitoring history
- `event_bus_messages` - Event bus message log

---

## CODEWORD MANAGER

### Purpose

The Codeword Manager provides the final authorization step for AWS production deployments. It generates single-use, time-limited codewords that must be provided by Super Admin to authorize deployment.

### Workflow

```
1. Agent/Commander passes all tests
   ↓
2. Admiral approval obtained
   ↓
3. Deployment package created
   ↓
4. System generates unique codeword
   ↓
5. Codeword sent to Super Admin (terminal/file)
   ↓
6. Super Admin provides codeword to authorize
   ↓
7. Codeword verified (hash comparison)
   ↓
8. If valid: Mark as used, proceed with deployment
   If invalid: Log attempt, reject deployment
```

### Codeword Format

Codewords use NATO phonetic alphabet for readability:

```
BRAVO-HOTEL-ZULU-4521
```

- 3 NATO words (26 options each)
- 4-digit number (0000-9999)
- Total combinations: 26³ × 10,000 = 175,760,000

### Deployment Types

| Type | Description |
|------|-------------|
| `agent_production` | New agent deployment to production |
| `agent_update` | Agent update in production |
| `system_deployment` | System-wide deployment |
| `infrastructure` | Infrastructure changes |
| `database_migration` | Database migrations |
| `security_update` | Security patches |
| `rollback` | Rollback operations |

### Security Features

1. **Hashed Storage**: Codewords are NEVER stored in plain text
2. **Single Use**: Each codeword can only be used once
3. **Time Limited**: Default 24-hour expiration
4. **Failed Attempt Tracking**: Too many failures revoke codeword
5. **Audit Trail**: Every attempt logged with device/IP

### CLI Usage

```bash
# Show status
python codeword_manager.py status

# List pending codewords
python codeword_manager.py pending

# View statistics
python codeword_manager.py stats

# Generate test codeword
python codeword_manager.py generate

# Verify codeword
python codeword_manager.py verify <package_id> <codeword>
```

### Database: `codeword_manager.db`

**Tables:**
- `codewords` - Codeword records (hashed)
- `deployment_packages` - Deployment package definitions
- `verification_attempts` - All verification attempts

---

## KV1NT DAEMON INTEGRATION

### New Methods (17 total)

```python
# Folder Activator (9 methods)
kv1nt.folder_activator              # Property
kv1nt.register_folder(...)          # Register folder for monitoring
kv1nt.unregister_folder(...)        # Remove folder from monitoring
kv1nt.list_monitored_folders()      # List all monitored folders
kv1nt.set_folder_monitoring_mode()  # Change monitoring mode
kv1nt.get_folder_audit_trail()      # Get audit history
await kv1nt.activate_folder(...)    # Manual activation
kv1nt.folder_activator_status()     # Get status
kv1nt.folder_activator_stats()      # Get statistics

# Codeword Manager (8 methods)
kv1nt.codeword_manager              # Property
kv1nt.create_deployment_package()   # Create package
kv1nt.generate_codeword(...)        # Generate codeword
kv1nt.authorize_deployment(...)     # Verify codeword
kv1nt.revoke_codeword(...)          # Revoke pending codeword
kv1nt.list_pending_codewords()      # List pending
kv1nt.codeword_manager_status()     # Get status
kv1nt.codeword_manager_stats()      # Get statistics
```

### Example Usage

```python
# Register Commander Unit folder
result = kv1nt.register_folder(
    path="/home/rasmus/commanders/legal",
    folder_type="commander_unit",
    name="Legal Commander",
    priority=8,
    monitoring_mode="full"
)
print(f"Registered: {result['folder_id']}")

# Create deployment package
package = kv1nt.create_deployment_package(
    name="Legal Commander v1.0.0",
    deployment_type="agent_production",
    target_environment="production",
    components=["legal_commander", "legal_agent"],
    description="Deploy Legal Commander to production"
)

# Generate codeword (displayed to Super Admin)
codeword = kv1nt.generate_codeword(package["package_id"])
# Output: ALPHA-FOXTROT-KILO-7823

# Authorize with codeword
result = kv1nt.authorize_deployment(
    package_id=package["package_id"],
    codeword="ALPHA-FOXTROT-KILO-7823"
)
if result["authorized"]:
    print("Deployment authorized!")
```

---

## WORKFLOW: Complete Deployment

### Step 1: Register Commander Folder

```python
folder = kv1nt.register_folder(
    path="/home/rasmus/commanders/my_commander",
    folder_type="commander_unit",
    name="My Commander"
)
```

### Step 2: Folder Activation (Automatic)

When Super Admin opens the folder, FolderActivator:
1. Detects access event via inotify
2. Verifies device is Super Admin (via ODIN)
3. Creates audit entry
4. Activates Commander Unit
5. Summons specialist flock (if configured)

### Step 3: Development & Testing

Commander Unit works on task, creating agent...

### Step 4: Request Admiral Approval

```python
approval = await kv1nt.request_approval(
    action="deploy_to_production",
    resource="my_agent_v1.0.0",
    risk_level="medium"
)
```

### Step 5: Create Deployment Package

```python
package = kv1nt.create_deployment_package(
    name="My Agent v1.0.0",
    deployment_type="agent_production",
    target_environment="production",
    components=["my_agent"],
    admiral_approval_id=approval["approval_id"]
)
```

### Step 6: Generate Codeword

```python
codeword = kv1nt.generate_codeword(package["package_id"])
# Super Admin sees: HOTEL-MIKE-SIERRA-4291
```

### Step 7: Authorize Deployment

Super Admin provides codeword:

```python
result = kv1nt.authorize_deployment(
    package_id=package["package_id"],
    codeword="HOTEL-MIKE-SIERRA-4291"
)
# If authorized, proceed with AWS deployment
```

---

## DATABASE FILES

| Database | Path | Tables |
|----------|------|--------|
| `folder_activator.db` | `~/.claude-agent/` | folder_configs, folder_states, activation_events, audit_trail, resource_snapshots, event_bus_messages |
| `codeword_manager.db` | `~/.claude-agent/` | codewords, deployment_packages, verification_attempts |

---

## FILE LOCATIONS

```
~/.claude-agent/
├── folder_activator.py       # Event-driven folder monitoring
├── codeword_manager.py       # AWS deployment authorization
├── folder_activator.db       # Folder database
├── codeword_manager.db       # Codeword database
├── .codewords/
│   └── pending.txt           # Codeword delivery file (if configured)
└── logs/
    ├── folder_activator.log
    └── codeword_manager.log
```

---

## COMPONENT STATISTICS

| Metric | v2.5.0 | v2.6.0 |
|--------|--------|--------|
| Total Components | 36 | 38 |
| Total Lines | ~31,000 | ~33,600 |
| Total Databases | 27 | 29 |
| Daemon Methods | 63 | 80 |

---

## ROADMAP

### Iteration 3 (v2.6.0) - COMPLETE
- [x] Folder Activator with 7 optimizations
- [x] Codeword Manager for AWS authorization
- [x] Daemon integration (17 new methods)
- [x] Documentation

### Iteration 4 (v2.7.0) - PLANNED
- [ ] Continuous Optimization Engine
- [ ] Agent Self-Improvement
- [ ] Performance Feedback Loops

---

## CHANGELOG

### v2.6.0 (2025-12-18)
- Phase 5 Iteration 3 implementation
- Folder Activator (~2,000 lines) with all 7 optimizations:
  - Event-driven monitoring (inotify/watchdog/polling)
  - Smart caching & indexing
  - Dynamic scope adjustment
  - Distributed event bus
  - Audit trail & reporting
  - Granular configuration
  - Self-healing & restart
- Codeword Manager (~620 lines):
  - Single-use, time-limited codewords
  - Secure hash storage
  - Failed attempt tracking
  - Full audit trail
- 17 new daemon methods
- 2 new databases
- 38 total components in KV1NTOS

---

*Generated by Claude Opus 4.5 for ODIN v2.0.0+ - The All-Father*
