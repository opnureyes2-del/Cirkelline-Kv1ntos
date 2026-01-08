# CODE GUARDIAN v2.1.0
## Autonomous Code Quality Observer

**Part of:** ODIN v2.0.0 - The All-Father
**Date:** 2025-12-18
**Author:** Rasmus & Claude Opus 4.5
**Location:** `~/.claude-agent/code_guardian.py`

---

## OVERVIEW

The **Code Guardian** is an autonomous code quality observer that continuously monitors, analyzes, and suggests improvements for the entire Cirkelline ecosystem. It operates as a vigilant sentinel, detecting issues before they become problems.

### Key Responsibilities

1. **OBSERVE** - Watch for code changes in real-time
2. **ANALYZE** - Static analysis, pattern detection, security scanning
3. **SUGGEST** - Categorized improvement suggestions
4. **FIX** - Auto-fix safe issues (with approval workflow)
5. **REPORT** - Generate quality reports and metrics

### Multi-Layer Analysis

```
CODE CHANGE DETECTED
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                   CODE GUARDIAN                          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Security   │  │  Code Smell  │  │   Pattern    │  │
│  │   Analyzer   │  │   Analyzer   │  │   Analyzer   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │          │
│         ▼                  ▼                  ▼          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Documentation Analyzer               │   │
│  └─────────────────────────┬────────────────────────┘   │
│                            │                             │
│                            ▼                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │          OBSERVATIONS + SUGGESTIONS               │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
        │
        ▼
   DATABASE PERSISTENCE (guardian.db)
```

---

## INSTALLATION & FILES

### File Locations

| File | Purpose | Lines |
|------|---------|-------|
| `~/.claude-agent/code_guardian.py` | Core component | ~1,320 |
| `~/.claude-agent/guardian.db` | SQLite database | - |
| `~/.claude-agent/logs/guardian.log` | Log file | - |
| `.git/hooks/pre-commit` | Git hook (optional) | ~40 |

### Dependencies

- Python 3.12+ (standard library only)
- No external dependencies required

### Quick Verification

```bash
# Check version
python3 ~/.claude-agent/code_guardian.py --version
# Output: Code Guardian v2.1.0

# Check status
python3 ~/.claude-agent/code_guardian.py --status

# Scan a file
python3 ~/.claude-agent/code_guardian.py --scan ~/path/to/file.py
```

---

## ANALYZERS

### 1. Security Analyzer

Detects security vulnerabilities using regex pattern matching.

| Pattern | Description | Severity |
|---------|-------------|----------|
| Hardcoded secrets | `password|secret|api_key = "..."` | CRITICAL |
| SQL injection | `execute("...%s...")` | HIGH |
| Command injection | `subprocess.call(... + ...)` | HIGH |
| Eval usage | `eval(...)` | HIGH |
| Pickle usage | `pickle.load(...)` | MEDIUM |
| Debug mode | `DEBUG = True` | MEDIUM |
| Weak crypto | `md5(...)`, `sha1(...)` | LOW |

**Example Detection:**

```python
# This code triggers CRITICAL:
DATABASE_PASSWORD = "secret123"  # Hardcoded secret detected

# This code triggers HIGH:
cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)  # SQL injection
```

### 2. Code Smell Analyzer

Uses AST parsing to detect structural issues.

| Check | Threshold | Severity |
|-------|-----------|----------|
| Function length | > 50 lines | MEDIUM |
| Parameter count | > 5 parameters | LOW |
| Nested depth | > 4 levels | MEDIUM |
| Class methods | > 20 methods | MEDIUM |

**Example Detection:**

```python
# This triggers MEDIUM (too many parameters):
def process_user(name, email, phone, address, city, state, zip):
    pass
# Suggestion: Consider using a dataclass to group related parameters
```

### 3. Pattern Analyzer

Detects common anti-patterns and technical debt.

| Pattern | Description | Severity |
|---------|-------------|----------|
| Print statements | `print()` in production code | LOW |
| TODO/FIXME | Unfinished work markers | INFO |
| Bare except | `except:` without type | MEDIUM |
| Magic numbers | Hardcoded numeric values | LOW |

**Example Detection:**

```python
# This triggers MEDIUM:
try:
    risky_operation()
except:  # Bare except clause - catching all exceptions can hide bugs
    pass

# Suggestion: Specify the exception type(s) to catch
```

### 4. Documentation Analyzer

Uses AST parsing to find documentation gaps.

| Check | Description | Severity |
|-------|-------------|----------|
| Missing function docstring | Public functions without docstring | LOW |
| Missing class docstring | Classes without docstring | MEDIUM |

**Example Detection:**

```python
# This triggers LOW:
def calculate_total(items):  # Missing docstring: calculate_total
    return sum(items)

# Suggestion: Add a docstring describing what calculate_total does
```

---

## DATABASE SCHEMA

### Tables

**1. observations** - All detected code issues

```sql
CREATE TABLE observations (
    observation_id TEXT PRIMARY KEY,
    observation_type TEXT NOT NULL,     -- 'security_risk', 'code_smell', etc.
    severity TEXT NOT NULL,             -- 'critical', 'high', 'medium', 'low', 'info'
    file_path TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    code_snippet TEXT,
    suggestion TEXT,
    fix_category TEXT DEFAULT 'manual', -- 'safe', 'review', 'manual', 'complex'
    auto_fix_code TEXT,
    confidence REAL DEFAULT 0.8,
    detected_at TEXT,
    resolved INTEGER DEFAULT 0,
    resolved_at TEXT,
    metadata TEXT DEFAULT '{}'
);
```

**2. suggestions** - Improvement suggestions

```sql
CREATE TABLE suggestions (
    suggestion_id TEXT PRIMARY KEY,
    observation_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    fix_type TEXT,                      -- 'refactor', 'add', 'remove', 'modify'
    target_file TEXT,
    target_lines TEXT,                  -- JSON: [start, end]
    original_code TEXT,
    suggested_code TEXT,
    impact TEXT DEFAULT 'low',          -- 'low', 'medium', 'high'
    effort TEXT DEFAULT 'moderate',     -- 'trivial', 'easy', 'moderate', 'complex'
    approved INTEGER DEFAULT 0,
    approved_by TEXT,
    applied INTEGER DEFAULT 0,
    applied_at TEXT,
    created_at TEXT,
    FOREIGN KEY (observation_id) REFERENCES observations(observation_id)
);
```

**3. fix_history** - Applied fixes

```sql
CREATE TABLE fix_history (
    fix_id TEXT PRIMARY KEY,
    suggestion_id TEXT,
    file_path TEXT NOT NULL,
    changes_made TEXT,                  -- JSON array
    backup_path TEXT,
    success INTEGER DEFAULT 0,
    error TEXT,
    applied_at TEXT,
    applied_by TEXT,
    FOREIGN KEY (suggestion_id) REFERENCES suggestions(suggestion_id)
);
```

**4. scan_history** - Scan executions

```sql
CREATE TABLE scan_history (
    scan_id TEXT PRIMARY KEY,
    scope TEXT NOT NULL,                -- 'file', 'directory', 'staged', 'changed', 'full'
    files_scanned INTEGER DEFAULT 0,
    observations_found INTEGER DEFAULT 0,
    duration_ms REAL DEFAULT 0,
    started_at TEXT,
    completed_at TEXT,
    summary TEXT DEFAULT '{}'           -- JSON
);
```

### Indexes

```sql
-- Observations indexes
CREATE INDEX idx_obs_file ON observations(file_path);
CREATE INDEX idx_obs_type ON observations(observation_type);
CREATE INDEX idx_obs_severity ON observations(severity);
CREATE INDEX idx_obs_resolved ON observations(resolved);

-- Suggestions indexes
CREATE INDEX idx_sugg_approved ON suggestions(approved);
CREATE INDEX idx_sugg_applied ON suggestions(applied);
```

---

## ENUMS

### ObservationType

```python
class ObservationType(Enum):
    CODE_SMELL = "code_smell"           # Code quality issues
    SECURITY_RISK = "security_risk"     # Security vulnerabilities
    PERFORMANCE_HINT = "performance_hint"  # Performance improvements
    TECHNICAL_DEBT = "technical_debt"   # Technical debt indicators
    PATTERN_VIOLATION = "pattern_violation"  # Architecture pattern violations
    MISSING_TESTS = "missing_tests"     # Untested code
    DOC_GAP = "doc_gap"                 # Missing documentation
    STYLE_ISSUE = "style_issue"         # Code style issues
    COMPLEXITY = "complexity"           # High complexity indicators
    DUPLICATION = "duplication"         # Code duplication
```

### SeverityLevel

```python
class SeverityLevel(Enum):
    INFO = "info"           # Informational only
    LOW = "low"             # Minor issues
    MEDIUM = "medium"       # Should be addressed
    HIGH = "high"           # Important to fix
    CRITICAL = "critical"   # Must fix immediately
```

### FixCategory

```python
class FixCategory(Enum):
    SAFE = "safe"           # Safe to auto-fix
    REVIEW = "review"       # Needs code review
    MANUAL = "manual"       # Requires manual fix
    COMPLEX = "complex"     # Complex refactoring needed
```

### ScanScope

```python
class ScanScope(Enum):
    FILE = "file"           # Single file
    DIRECTORY = "directory" # Directory tree
    STAGED = "staged"       # Git staged files
    CHANGED = "changed"     # Git changed files
    FULL = "full"           # Full codebase
```

### GuardianAction

```python
class GuardianAction(Enum):
    OBSERVE = "observe"     # Just observe and record
    SUGGEST = "suggest"     # Suggest improvements
    AUTO_FIX = "auto_fix"   # Automatically fix
    BLOCK = "block"         # Block commit/action
    REPORT = "report"       # Generate report
```

---

## DATACLASSES

### CodeObservation

```python
@dataclass
class CodeObservation:
    observation_id: str
    observation_type: ObservationType
    severity: SeverityLevel
    file_path: str
    line_start: int
    line_end: int
    title: str
    description: str
    code_snippet: str = ""
    suggestion: str = ""
    fix_category: FixCategory = FixCategory.MANUAL
    auto_fix_code: str = ""
    confidence: float = 0.8
    detected_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### GuardianSuggestion

```python
@dataclass
class GuardianSuggestion:
    suggestion_id: str
    observation_id: str
    title: str
    description: str
    fix_type: str  # "refactor", "add", "remove", "modify"
    target_file: str
    target_lines: Tuple[int, int]
    original_code: str
    suggested_code: str
    impact: str  # "low", "medium", "high"
    effort: str  # "trivial", "easy", "moderate", "complex"
    approved: bool = False
    approved_by: Optional[str] = None
    applied: bool = False
    applied_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
```

### ScanResult

```python
@dataclass
class ScanResult:
    scan_id: str
    scope: ScanScope
    files_scanned: int
    observations_found: int
    observations: List[CodeObservation]
    duration_ms: float
    started_at: datetime
    completed_at: datetime
    summary: Dict[str, int] = field(default_factory=dict)
```

### FixResult

```python
@dataclass
class FixResult:
    success: bool
    suggestion_id: str
    file_path: str
    changes_made: List[str]
    backup_path: Optional[str] = None
    error: Optional[str] = None
    applied_at: Optional[datetime] = None
```

---

## CORE API

### CodeGuardian Class

The main singleton class that orchestrates all analysis.

#### Constructor

```python
guardian = get_code_guardian()  # Singleton accessor
```

#### observe(target, scope)

Main scanning method.

```python
from code_guardian import get_code_guardian, ScanScope

guardian = get_code_guardian()

# Scan single file
result = guardian.observe("path/to/file.py", ScanScope.FILE)

# Scan directory
result = guardian.observe("path/to/directory", ScanScope.DIRECTORY)

# Scan Git staged files
result = guardian.observe("", ScanScope.STAGED)

# Full codebase scan
result = guardian.observe("", ScanScope.FULL)

# Access results
print(f"Files: {result.files_scanned}")
print(f"Issues: {result.observations_found}")
print(f"Duration: {result.duration_ms:.1f}ms")
for obs in result.observations:
    print(f"  [{obs.severity.value}] {obs.title}")
```

#### quick_scan(files)

Fast scan for pre-commit hooks. Returns only HIGH and CRITICAL issues.

```python
# Scan staged files
issues = guardian.quick_scan()

# Scan specific files
issues = guardian.quick_scan(["file1.py", "file2.py"])

# Check if commit should be blocked
if issues:
    print(f"Blocking commit: {len(issues)} critical issues")
```

#### get_observations(filters)

Query observations with filters.

```python
from code_guardian import ObservationType, SeverityLevel

# All unresolved
obs = guardian.get_observations(resolved=False)

# Security issues only
obs = guardian.get_observations(
    observation_type=ObservationType.SECURITY_RISK
)

# Critical severity only
obs = guardian.get_observations(
    severity=SeverityLevel.CRITICAL,
    limit=50
)

# Specific file
obs = guardian.get_observations(
    file_path="/path/to/file.py"
)
```

#### auto_fix(observation_id, approved_by)

Apply auto-fix for SAFE issues.

```python
result = guardian.auto_fix(
    observation_id="abc123def456",
    approved_by="rasmus"
)

if result.success:
    print(f"Fixed: {result.changes_made}")
    print(f"Backup at: {result.backup_path}")
else:
    print(f"Error: {result.error}")
```

#### get_summary()

Get summary statistics.

```python
summary = guardian.get_summary()

print(f"Total unresolved: {summary['total_unresolved']}")
print(f"By severity: {summary['by_severity']}")
print(f"By type: {summary['by_type']}")
print(f"Recent scans: {len(summary['recent_scans'])}")
```

#### format_status()

Get formatted status for terminal display.

```python
print(guardian.format_status())
# Output:
# ============================================================
#   CODE GUARDIAN STATUS
# ============================================================
#
#   Unresolved Issues: 42
#
#   BY SEVERITY:
#     CRITICAL: 2
#     HIGH: 8
#     MEDIUM: 15
#     LOW: 12
#     INFO: 5
#
#   BY TYPE:
#     - security_risk: 10
#     - code_smell: 18
#     - doc_gap: 14
#
#   RECENT SCANS:
#     - directory: 45 files, 42 issues
#     - staged: 3 files, 0 issues
#
# ============================================================
```

---

## GIT INTEGRATION

### Install Git Hooks

```python
guardian = get_code_guardian()
guardian.install_git_hooks()
# Creates .git/hooks/pre-commit
```

Or via CLI:

```bash
python3 ~/.claude-agent/code_guardian.py --install-hooks
```

### Pre-Commit Hook Behavior

1. Scans all staged Python files
2. Runs quick_scan (HIGH + CRITICAL only)
3. If issues found:
   - Displays issue details
   - Blocks commit
   - Suggests running `kv1nt guardian review`
4. If no issues: Commit proceeds

### Hook Content (Auto-Generated)

```python
#!/usr/bin/env python3
from code_guardian import get_code_guardian

guardian = get_code_guardian()
issues = guardian.quick_scan()

if not issues:
    print("Code Guardian: No critical issues found")
    exit(0)

print(f"Found {len(issues)} critical issue(s):")
for issue in issues:
    print(f"  [{issue.severity.value}] {issue.title}")
    print(f"  File: {issue.file_path}:{issue.line_start}")

print("Use 'git commit --no-verify' to bypass (not recommended)")
exit(1)
```

### Get Staged/Changed Files

```python
# Get staged files
staged = guardian.get_staged_files()
# ["/path/to/file1.py", "/path/to/file2.py"]

# Get changed (unstaged) files
changed = guardian.get_changed_files()
```

---

## TERMINAL COMMANDS

### Via KV1NTOS Daemon

```bash
# Show guardian status
kv1nt guardian status

# Scan a file or directory
kv1nt guardian scan /path/to/file.py

# Quick scan staged files
kv1nt guardian quick

# Install Git hooks
kv1nt guardian install-hooks

# Interactive review
kv1nt guardian review
```

### Direct CLI

```bash
# Show version
python3 ~/.claude-agent/code_guardian.py --version

# Show status
python3 ~/.claude-agent/code_guardian.py --status

# Scan file/directory
python3 ~/.claude-agent/code_guardian.py --scan /path/to/target

# Scan staged files
python3 ~/.claude-agent/code_guardian.py --staged

# Install hooks
python3 ~/.claude-agent/code_guardian.py --install-hooks
```

---

## INTEGRATION WITH KV1NTOS

The Code Guardian integrates with the KV1NTOS daemon through the following methods:

### Daemon Methods

```python
# In kv1nt_daemon.py

@property
def guardian(self) -> CodeGuardian:
    """Access the Code Guardian."""
    return self._guardian

def guardian_scan(self, target: str, scope: str = "file") -> Dict:
    """Scan code for issues."""
    scope_enum = ScanScope(scope)
    result = self._guardian.observe(target, scope_enum)
    return {
        "files_scanned": result.files_scanned,
        "observations": result.observations_found,
        "duration_ms": result.duration_ms,
        "summary": result.summary
    }

def guardian_status(self) -> str:
    """Get formatted guardian status."""
    return self._guardian.format_status()

def guardian_quick_scan(self) -> List[Dict]:
    """Quick scan staged files."""
    issues = self._guardian.quick_scan()
    return [obs.to_dict() for obs in issues]

def guardian_install_hooks(self) -> bool:
    """Install Git pre-commit hooks."""
    return self._guardian.install_git_hooks()
```

### MCP Bridge Registration

The Code Guardian is registered with the MCP Bridge for cross-component communication:

```python
self._mcp.register("guardian", self._guardian)
```

---

## AUTO-FIX WORKFLOW

### Safe Fixes

Only `SAFE` category issues can be auto-fixed:

1. **Backup** - Original file backed up to `.py.bak`
2. **Apply** - Fix applied to target line(s)
3. **Record** - Fix recorded in `fix_history` table
4. **Mark** - Observation marked as resolved

### Example Fix Flow

```python
# 1. Get observations
obs = guardian.get_observations(
    fix_category=FixCategory.SAFE,
    resolved=False
)

# 2. Review and approve
for o in obs:
    print(f"{o.title}: {o.suggestion}")

# 3. Apply fix
result = guardian.auto_fix(obs[0].observation_id, approved_by="rasmus")

# 4. Check result
if result.success:
    print(f"Fixed! Backup at: {result.backup_path}")
else:
    print(f"Failed: {result.error}")
```

### Fix Categories

| Category | Auto-Fix | Description |
|----------|----------|-------------|
| SAFE | Yes | Safe transformations (e.g., print → logger) |
| REVIEW | No | Needs human review before applying |
| MANUAL | No | Requires manual intervention |
| COMPLEX | No | Requires significant refactoring |

---

## SEVERITY ICONS

Used in terminal output:

| Severity | Icon | Action |
|----------|------|--------|
| CRITICAL | :red_circle: | Must fix immediately |
| HIGH | :orange_circle: | Fix soon |
| MEDIUM | :yellow_circle: | Should address |
| LOW | :green_circle: | Nice to fix |
| INFO | :large_blue_circle: | Informational |

---

## BEST PRACTICES

### 1. Regular Scanning

```bash
# Daily full scan
python3 ~/.claude-agent/code_guardian.py --scan ~/projects/

# Before commits
python3 ~/.claude-agent/code_guardian.py --staged
```

### 2. Install Git Hooks

```bash
# Install once per repository
python3 ~/.claude-agent/code_guardian.py --install-hooks
```

### 3. Review Before Auto-Fix

```python
# Always review before applying
obs = guardian.get_observations(fix_category=FixCategory.SAFE)
for o in obs:
    print(f"{o.title}: {o.auto_fix_code}")
    confirm = input("Apply? (y/n): ")
    if confirm == 'y':
        guardian.auto_fix(o.observation_id, "rasmus")
```

### 4. Keep Database Clean

```python
# Periodically clean old resolved issues
conn = guardian._get_conn()
conn.execute("""
    DELETE FROM observations
    WHERE resolved = 1
    AND resolved_at < datetime('now', '-30 days')
""")
conn.commit()
```

---

## ROADMAP

### Current (v2.1.0)
- 4 analyzers (Security, Smell, Pattern, Documentation)
- 10 observation types
- Git pre-commit integration
- Auto-fix for SAFE issues
- SQLite persistence

### Planned (v2.2.0)
- Real-time file watcher
- Complexity analyzer (cyclomatic complexity)
- Duplication detector
- Performance analyzer
- Integration with Admiral for approval workflow

### Future (v3.0.0)
- ML-based pattern detection
- Cross-file dependency analysis
- Custom rule definitions
- IDE integration (VSCode extension)
- Distributed scanning for large codebases

---

## TROUBLESHOOTING

### Issue: "Database locked"

```bash
# Close all guardian instances
pkill -f code_guardian

# Retry
python3 ~/.claude-agent/code_guardian.py --status
```

### Issue: "No files scanned"

Check file extensions - only `.py` files are scanned.

```python
# Verify target exists
from pathlib import Path
print(Path("/path/to/target").exists())
```

### Issue: "Git hook not running"

```bash
# Check hook exists and is executable
ls -la .git/hooks/pre-commit

# Make executable if needed
chmod +x .git/hooks/pre-commit
```

### Issue: "Too many false positives"

The analyzers use conservative patterns. For project-specific tuning:

```python
# Skip specific patterns in config (future feature)
# For now, mark as resolved to exclude from reports
guardian._mark_resolved("observation_id_here")
```

---

## CHANGELOG

### v2.1.0 (2025-12-18)
- Initial release as part of ODIN v2.0.0
- 4 core analyzers
- Git pre-commit hook integration
- Auto-fix capability for SAFE issues
- SQLite database persistence
- Full CLI interface
- Integration with KV1NTOS daemon

---

*Code Guardian v2.1.0 - Part of ODIN v2.0.0 - The All-Father*
*"Vigilant observation, proactive protection"*
