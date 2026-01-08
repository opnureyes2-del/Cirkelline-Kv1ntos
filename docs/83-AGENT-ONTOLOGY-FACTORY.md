# Agent Ontology & Factory v2.4.0

## ODIN v2.0.0+ - The All-Father
### Phase 5 Iteration 1: Autonomous Agent Creation Foundation

**Date:** 2025-12-18
**Version:** 2.4.0
**Status:** ACTIVE
**Author:** Rasmus & Claude Opus 4.5

---

## OVERVIEW

Phase 5 Iteration 1 implements the foundation for autonomous agent creation within the KV1NTOS/ODIN ecosystem. This enables ODIN to create, manage, and deploy specialist agents autonomously.

### New Components

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| **Agent Ontology** | `agent_ontology.py` | ~810 | Formal agent definition schema & registry |
| **Agent Factory** | `agent_factory.py` | ~2,050 | Autonomous agent creation system |
| **Agent Sandbox** | `agent_sandbox.py` | ~1,200 | **MANDATORY** Docker containerization |

### Updated Components

| Component | Changes |
|-----------|---------|
| **Admiral** | 3 new agent-specific policies (POL_AGENT_001/002/003) |
| **KV1NT Daemon** | 12 new methods for agent creation & management |
| **VERSION** | Updated to 2.4.0 |

---

## AGENT ONTOLOGY

The Agent Ontology provides a formal, machine-readable definition system for all agents.

### Core Dataclasses

```python
@dataclass
class AgentOntology:
    """Complete formal agent definition."""
    agent_id: str
    name: str
    version: str
    type: AgentType  # SPECIALIST, COMMANDER, LEARNING, SYSTEM, ORCHESTRATOR
    purpose: str
    description: str
    domain_expertise: List[str]
    capabilities: List[Capability]
    tool_access_privileges: List[ToolAccess]
    resource_requirements: ResourceSpec
    autonomy_level: AutonomyLevel  # SUGGESTIVE, GUIDED, EXECUTABLE, AUTONOMOUS
    communication_protocols: List[Protocol]
    quality_thresholds: QualitySpec
    performance_metrics: PerformanceMetrics
    training_data_sources: List[str]
    status: AgentStatus  # DRAFT, DEVELOPMENT, TESTING, ACTIVE, DEPRECATED
```

### Enums

- **AgentType**: `SPECIALIST`, `COMMANDER`, `SYSTEM`, `LEARNING`, `ORCHESTRATOR`
- **AgentStatus**: `DRAFT`, `DEVELOPMENT`, `TESTING`, `STAGING`, `ACTIVE`, `DEPRECATED`, `ARCHIVED`
- **AutonomyLevel**: `SUGGESTIVE`, `GUIDED`, `EXECUTABLE`, `AUTONOMOUS`, `SUPERVISED`
- **AccessLevel**: `NONE`, `READ`, `WRITE`, `EXECUTE`, `ADMIN`
- **CapabilityCategory**: `CODE_GENERATION`, `CODE_ANALYSIS`, `TESTING`, `DOCUMENTATION`, etc.

### Database: `agent_ontology.db`

**Tables:**
- `agents` - Core ontology storage
- `capabilities` - Searchable capabilities
- `tool_permissions` - Access control
- `agent_versions` - Version history
- `performance_history` - Performance tracking

### CLI Usage

```bash
# Show status
python agent_ontology.py status

# List all agents
python agent_ontology.py list

# Validate a spec file
python agent_ontology.py validate my_agent.yaml

# Register an agent
python agent_ontology.py register my_agent.yaml
```

---

## AGENT FACTORY

The Agent Factory enables autonomous creation of specialist agents from:
1. **Ontology specifications** (YAML/JSON)
2. **Natural language descriptions**
3. **Task requirement analysis**

### Creation Methods

```python
# From specification file
ontology, request = await factory.create_from_spec("agent.yaml")

# From natural language
ontology, request = await factory.create_from_nl(
    description="A specialist for React component testing",
    domain="testing",
    capabilities=["test_generation", "code_analysis"]
)

# From task analysis
agents, requests = await factory.create_from_task_analysis(
    task_description="Refactor authentication system",
    required_capabilities=["code_generation", "security"]
)
```

### Agent Templates (5 Built-in)

| Template | Type | Purpose |
|----------|------|---------|
| `specialist_v1` | SPECIALIST | Base specialist agent |
| `commander_v1` | COMMANDER | Commander with delegation |
| `learning_v1` | LEARNING | Agent with continuous learning |
| `api_v1` | API | API/endpoint specialist |
| `data_v1` | DATA | Database/data specialist |

### Generated Directory Structure

```
~/.claude-agent/agents/{agent_name}_{timestamp}/
├── __init__.py
├── {agent_name}.py           # Main agent class
├── config.json               # Agent configuration
├── ontology.yaml             # Agent definition
├── requirements.txt          # Dependencies
├── Dockerfile                # Container image
├── VERSION
├── tests/
│   └── test_{agent_name}.py
└── docs/
    └── README.md
```

### CLI Usage

```bash
# Show factory status
python agent_factory.py status

# List all agents
python agent_factory.py list

# List templates
python agent_factory.py templates

# Create from spec
python agent_factory.py create my_agent.yaml

# View creation history
python agent_factory.py history
```

---

## AGENT SANDBOX

**CRITICAL: ALL new agents MUST run in isolated Docker containers.**

The Agent Sandbox provides mandatory Docker containerization with:
- Complete container isolation
- Enforced resource limits (CPU, RAM, storage)
- Security restrictions (no-root, dropped capabilities)
- Real-time monitoring
- Full lifecycle management

### Security Levels

| Level | Restrictions |
|-------|--------------|
| **MAXIMUM** | Read-only filesystem, no network, all caps dropped |
| **HIGH** | Read-only filesystem, internal network, all caps dropped |
| **STANDARD** | Writable filesystem, internal network, all caps dropped |
| **MINIMAL** | Writable filesystem, internal network, some caps (dev only) |

### Resource Profiles

| Profile | CPU | RAM | Storage |
|---------|-----|-----|---------|
| **MINIMAL** | 0.5 | 256 MB | 128 MB |
| **LIGHT** | 1.0 | 512 MB | 256 MB |
| **STANDARD** | 2.0 | 1 GB | 512 MB |
| **HEAVY** | 4.0 | 2 GB | 1 GB |
| **INTENSIVE** | 8.0 | 4 GB | 2 GB |

### Deployment

```python
# Deploy to sandbox
success, instance = await sandbox.deploy_agent(
    agent_id="abc123",
    agent_name="TestAgent",
    agent_path=Path("/path/to/agent"),
    resource_profile=ResourceProfile.STANDARD,
    security_level=SecurityLevel.HIGH
)

# Execute in sandbox
exit_code, stdout, stderr = await sandbox.execute_in_sandbox(
    container_id="abc123",
    command=["python", "-c", "print('hello')"]
)
```

### CLI Usage

```bash
# Show sandbox status
python agent_sandbox.py status

# List active agents
python agent_sandbox.py list

# View container logs
python agent_sandbox.py logs <container_id>

# Stop container
python agent_sandbox.py stop <container_id>

# Remove container
python agent_sandbox.py remove <container_id>
```

---

## ADMIRAL POLICIES (NEW)

Three new mandatory policies for agent creation:

### POL_AGENT_001: No Unrestricted File Access
- **Enforcement:** MANDATORY
- **Description:** New agents cannot have unrestricted filesystem access
- **Rules:**
  - Scope cannot be `*`
  - Allowed paths: `/home/*/agents/*`, `/tmp/*`

### POL_AGENT_002: Resource Limits Required
- **Enforcement:** REQUIRED
- **Description:** All agents must specify resource limits
- **Rules:**
  - Required: `cpu_cores`, `memory_mb`, `storage_mb`
  - Max CPU: 8.0 cores
  - Max Memory: 4096 MB
  - Docker limits required

### POL_AGENT_003: Super Admin Approval for Production
- **Enforcement:** MANDATORY
- **Description:** Production deployment requires Super Admin approval
- **Rules:**
  - Production environment: Super Admin tier
  - AUTONOMOUS agents: Super Admin tier
  - Docker sandbox: Required

---

## KV1NT DAEMON INTEGRATION

### New Methods (12 total)

```python
# Properties
kv1nt.agent_factory      # Get Agent Factory instance
kv1nt.ontology_registry  # Get Ontology Registry instance
kv1nt.agent_sandbox      # Get Agent Sandbox instance

# Agent Creation
await kv1nt.create_agent_from_nl(
    description="Description of agent",
    domain="testing",
    capabilities=["testing", "code_analysis"]
)

await kv1nt.create_agent_from_spec(
    spec_path="/path/to/spec.yaml",
    approval_mode="required"  # skip, required, auto, super_admin
)

# Agent Management
kv1nt.list_agents(status="active", agent_type="specialist")
kv1nt.agent_factory_status()
kv1nt.agent_factory_templates()

# Sandbox Management
await kv1nt.deploy_agent_to_sandbox(
    agent_id="abc123",
    agent_name="TestAgent",
    agent_path="/path/to/agent",
    resource_profile="standard",
    security_level="high"
)

kv1nt.sandbox_status()
kv1nt.list_sandboxed_agents()
```

---

## WORKFLOW: Creating an Agent

### Step 1: Define Ontology (Optional - can use NL)

```yaml
# my_agent.yaml
agent_id: my-test-agent-001
name: TestingAgent
version: "1.0.0"
type: specialist
purpose: "Automated test generation for Python code"
domain_expertise:
  - pytest
  - unittest
  - python
capabilities:
  - name: generate_tests
    category: testing
    description: Generate pytest tests for Python functions
resource_requirements:
  cpu_cores: 1.0
  memory_mb: 512
  storage_mb: 256
autonomy_level: guided
```

### Step 2: Create Agent

```python
# From spec
result = await kv1nt.create_agent_from_spec("my_agent.yaml")

# Or from NL
result = await kv1nt.create_agent_from_nl(
    description="An agent that generates pytest tests for Python functions",
    domain="testing",
    capabilities=["test_generation"]
)
```

### Step 3: Deploy to Sandbox

```python
result = await kv1nt.deploy_agent_to_sandbox(
    agent_id=result["agent_id"],
    agent_name=result["name"],
    agent_path=result["path"],
    resource_profile="standard",
    security_level="high"
)
```

### Step 4: Use Agent

```python
# Execute task in sandbox
exit_code, stdout, stderr = await sandbox.execute_in_sandbox(
    container_id=result["container_id"],
    command=["python", "-m", "testing_agent", "generate", "/path/to/code.py"]
)
```

---

## DATABASE FILES

| Database | Path | Tables |
|----------|------|--------|
| `agent_ontology.db` | `~/.claude-agent/` | agents, capabilities, tool_permissions, agent_versions, performance_history |
| `agent_factory.db` | `~/.claude-agent/` | creation_history |
| `agent_sandbox.db` | `~/.claude-agent/` | containers, images, executions |

---

## FILE LOCATIONS

```
~/.claude-agent/
├── agent_ontology.py       # Agent definitions & registry
├── agent_factory.py        # Agent creation system
├── agent_sandbox.py        # Docker containerization
├── agent_ontology.db       # Ontology database
├── agent_factory.db        # Factory database
├── agent_sandbox.db        # Sandbox database
├── agents/                 # Created agents directory
│   └── {agent}_{timestamp}/
├── agent_templates/        # Template storage
├── containers/             # Container artifacts
└── logs/
    ├── agent_ontology.log
    ├── agent_factory.log
    └── agent_sandbox.log
```

---

## ROADMAP

### Iteration 1 (v2.4.0) - COMPLETE
- [x] Agent Ontology schema
- [x] Agent Factory with 3 creation methods
- [x] Agent Sandbox (Docker mandatory)
- [x] Admiral policies (3 new)
- [x] Daemon integration (12 new methods)
- [x] Documentation

### Iteration 2 (v2.5.0) - PLANNED
- [ ] Flock Orchestrator
- [ ] Learning Room Integration
- [ ] Agent Training System

### Iteration 3 (v2.6.0) - PLANNED
- [ ] Folder Activator
- [ ] Codeword Manager
- [ ] AWS Deployment Authorization

### Iteration 4 (v2.7.0) - PLANNED
- [ ] Continuous Optimization Engine
- [ ] Agent Self-Improvement
- [ ] Performance Feedback Loops

---

## CHANGELOG

### v2.4.0 (2025-12-18)
- Initial Phase 5 Iteration 1 implementation
- Agent Ontology system (~810 lines)
- Agent Factory with templates (~2,050 lines)
- Agent Sandbox with Docker (~1,200 lines)
- 3 new Admiral policies
- 12 new daemon methods
- 33 total components in KV1NTOS

---

*Generated by Claude Opus 4.5 for ODIN v2.0.0+ - The All-Father*
