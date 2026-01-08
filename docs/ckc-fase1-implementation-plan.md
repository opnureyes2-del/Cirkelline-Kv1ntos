# CKC Fase 1: Infrastruktur Implementation Plan

**Version:** 1.0.0 | **Status:** Aktiv | **Dato:** 2025-12-10

---

## Vision: CKC som Det Centrale Nervesystem

CKC fungerer som det intelligente nervesystem der forbinder alle platforme:
- **Hjernen:** Kommandanten (strategiske beslutninger, opgavefordeling)
- **Sanseorganerne:** CKC Connectors (modtager data fra platforme)
- **Musklerne:** Specialiserede Agenter (udfører handlinger)
- **Feedback Loops:** Kontinuerlig læring og korrektion

---

## Arkitektur Beslutninger

| Komponent | Valg | Begrundelse |
|-----------|------|-------------|
| **Database** | Separat PostgreSQL (ckc-postgres) | Isolation, "Ground Truth" for agenthukommelse |
| **Message Queue** | RabbitMQ (kritisk) + Redis (flygtig) | Hybrid for robusthed + hastighed |
| **Notion** | Fuld CRUD (når klar) | Komplet integration med økosystem |

---

## Fase 1.1: CKC PostgreSQL Database Setup

### Formål
Oprette dedikeret PostgreSQL database som primær datakilde for:
- Agent hukommelse og læringsdata
- Work-loop logs og beslutningshistorik
- Task context persistence
- Audit trail

### Deliverables

#### 1.1.1 Docker Container Setup
```yaml
# docker-compose.ckc.yml
services:
  ckc-postgres:
    image: postgres:17
    container_name: ckc-postgres
    environment:
      POSTGRES_USER: ckc
      POSTGRES_PASSWORD: ${CKC_DB_PASSWORD}
      POSTGRES_DB: ckc_brain
    ports:
      - "5533:5432"
    volumes:
      - ckc_postgres_data:/var/lib/postgresql/data
```

#### 1.1.2 Database Schema
```sql
-- Core Tables
CREATE SCHEMA ckc;

-- Task Context Persistence
CREATE TABLE ckc.task_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id VARCHAR(50) UNIQUE NOT NULL,
    task_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    original_prompt TEXT,
    current_agent VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    flags JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow Steps
CREATE TABLE ckc.workflow_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id VARCHAR(50) REFERENCES ckc.task_contexts(context_id),
    step_id VARCHAR(100) NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    action VARCHAR(200),
    status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB DEFAULT '{}',
    output_data JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent Memory
CREATE TABLE ckc.agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) NOT NULL,
    memory_type VARCHAR(50) NOT NULL, -- 'episodic', 'semantic', 'procedural'
    content JSONB NOT NULL,
    importance FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Learning Events
CREATE TABLE ckc.learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id INTEGER NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(100),
    content JSONB NOT NULL,
    integrity_hash VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ILCP Messages (Persistence)
CREATE TABLE ckc.ilcp_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(100) UNIQUE NOT NULL,
    sender_room_id INTEGER NOT NULL,
    recipient_room_id INTEGER NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    content JSONB NOT NULL,
    task_context_data JSONB,
    validation_mode VARCHAR(20),
    is_validated BOOLEAN DEFAULT FALSE,
    validation_errors TEXT[],
    status VARCHAR(50) DEFAULT 'pending', -- pending, delivered, acknowledged, failed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ
);

-- Knowledge Entries (Bibliotekar)
CREATE TABLE ckc.knowledge_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    tags TEXT[] DEFAULT '{}',
    references TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    version INTEGER DEFAULT 1,
    access_count INTEGER DEFAULT 0,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Trail
CREATE TABLE ckc.audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    actor VARCHAR(100),
    old_value JSONB,
    new_value JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_task_contexts_task_id ON ckc.task_contexts(task_id);
CREATE INDEX idx_task_contexts_status ON ckc.task_contexts(status);
CREATE INDEX idx_workflow_steps_context ON ckc.workflow_steps(context_id);
CREATE INDEX idx_agent_memory_agent ON ckc.agent_memory(agent_id);
CREATE INDEX idx_ilcp_messages_status ON ckc.ilcp_messages(status);
CREATE INDEX idx_knowledge_entries_category ON ckc.knowledge_entries(category);
CREATE INDEX idx_knowledge_entries_tags ON ckc.knowledge_entries USING GIN(tags);
CREATE INDEX idx_audit_trail_entity ON ckc.audit_trail(entity_type, entity_id);
```

#### 1.1.3 Python Database Layer
Fil: `cirkelline/ckc/infrastructure/database.py`

- AsyncPG connection pool
- Repository pattern for each table
- Automatic serialization/deserialization
- Migration support med Alembic

### Verifikation
- [ ] Docker container kører
- [ ] Schema oprettet
- [ ] Python layer kan CRUD operationer
- [ ] Eksisterende in-memory data kan migreres

---

## Fase 1.2: RabbitMQ Event Bus Integration

### Formål
Implementere robust message queue for:
- Asynkron kommunikation mellem agenter
- Garanteret message delivery
- Dead-letter queues for fejlhåndtering
- Event streaming til alle platforme

### Deliverables

#### 1.2.1 RabbitMQ Docker Setup
```yaml
# docker-compose.ckc.yml (tilføj)
  ckc-rabbitmq:
    image: rabbitmq:3-management
    container_name: ckc-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: ckc
      RABBITMQ_DEFAULT_PASS: ${CKC_MQ_PASSWORD}
    ports:
      - "5672:5672"   # AMQP
      - "15672:15672" # Management UI
    volumes:
      - ckc_rabbitmq_data:/var/lib/rabbitmq
```

#### 1.2.2 Exchange & Queue Architecture
```
Exchanges:
├── ckc.tasks (direct)          # Task assignments til specifikke agenter
├── ckc.events (fanout)         # System-wide events
├── ckc.ilcp (topic)            # Inter-room messaging (room.* patterns)
├── ckc.feedback (direct)       # Agent feedback til Kommandant
└── ckc.dlx (fanout)            # Dead-letter exchange

Queues:
├── tasks.tool_explorer
├── tasks.creative_synthesizer
├── tasks.knowledge_architect
├── tasks.virtual_world_builder
├── tasks.quality_assurance
├── events.dashboard
├── events.audit
├── ilcp.room.{id}
├── feedback.kommandant
└── dlq.all                     # Dead-letter queue
```

#### 1.2.3 Python Message Bus Layer
Fil: `cirkelline/ckc/infrastructure/message_bus.py`

```python
# Core Classes:
- CKCEventBus: Hovedklasse for publish/subscribe
- MessagePublisher: Async message sending
- MessageConsumer: Async message receiving med callbacks
- DeadLetterHandler: Håndtering af fejlede beskeder
```

### Verifikation
- [ ] RabbitMQ container kører
- [ ] Exchanges og queues oprettet
- [ ] Python kan publish/consume
- [ ] Dead-letter fungerer
- [ ] ILCP routing via MQ

---

## Fase 1.3: CKC Connectors Framework

### Formål
Letvægts-moduler der forbinder eksterne platforme til CKC Event Bus:
- Input Streams: Events fra platforme → CKC
- Output Channels: CKC instruktioner → platforme

### Deliverables

#### 1.3.1 Base Connector Class
Fil: `cirkelline/ckc/connectors/base.py`

```python
class CKCConnector(ABC):
    """Base class for all platform connectors."""

    @abstractmethod
    async def connect(self) -> bool

    @abstractmethod
    async def subscribe_events(self, callback: Callable)

    @abstractmethod
    async def execute_action(self, action: Dict) -> Dict

    @abstractmethod
    async def health_check(self) -> bool
```

#### 1.3.2 Initial Connectors
```
cirkelline/ckc/connectors/
├── __init__.py
├── base.py                 # Base connector class
├── notion_connector.py     # Notion API integration
├── webhook_connector.py    # Generic webhook receiver
├── internal_connector.py   # Internal CKC-to-CKC
└── slack_connector.py      # (Future) Slack integration
```

#### 1.3.3 Connector Registry
Fil: `cirkelline/ckc/infrastructure/connector_registry.py`

- Dynamic connector loading
- Health monitoring
- Auto-reconnect logic
- Event routing configuration

### Verifikation
- [ ] Base connector implementeret
- [ ] Webhook connector fungerer
- [ ] Internal connector til agent-kommunikation
- [ ] Registry kan liste og monitorere connectors

---

## Fase 1.4: Knowledge Bank Sync Interface

### Formål
Synkronisere viden mellem:
- CKC's interne vidensgraf (Bibliotekar)
- Notion workspaces
- Private dokumenter
- Ekstern Knowledge Bank

### Deliverables

#### 1.4.1 Sync Manager
Fil: `cirkelline/ckc/infrastructure/knowledge_sync.py`

```python
class KnowledgeSyncManager:
    """Manages bidirectional sync between knowledge sources."""

    async def sync_from_notion(self, workspace_id: str)
    async def sync_to_notion(self, entries: List[KnowledgeEntry])
    async def sync_from_documents(self, path: str)
    async def resolve_conflicts(self, local: Entry, remote: Entry)
    async def get_sync_status(self) -> SyncStatus
```

#### 1.4.2 Standardized Knowledge Interface
Fil: `cirkelline/ckc/infrastructure/knowledge_interface.py`

```python
# Unified interface for all knowledge operations
async def search_knowledge(query: str, sources: List[str]) -> List[Entry]
async def get_entry(entry_id: str, source: str) -> Entry
async def create_entry(entry: Entry, target: str) -> str
async def update_entry(entry_id: str, updates: Dict, target: str)
async def delete_entry(entry_id: str, target: str)
```

### Verifikation
- [ ] Kan læse fra intern vidensgraf
- [ ] Kan synkronisere til/fra Notion (læse først)
- [ ] Conflict resolution fungerer
- [ ] Sync status tracking

---

## Fase 1.5: Unified Control Panel API

### Formål
Backend API for CKC Frontend (kommandocentral):
- Samlet visning af aktive opgaver
- Agent status overview
- Realtids-logs
- HITL godkendelsespunkter

### Deliverables

#### 1.5.1 FastAPI Router
Fil: `cirkelline/ckc/api/control_panel.py`

```python
# Endpoints:
GET  /api/ckc/overview           # Full system overview
GET  /api/ckc/tasks              # Active tasks with status
GET  /api/ckc/agents             # Agent status and metrics
GET  /api/ckc/rooms              # Learning room status
GET  /api/ckc/hitl/pending       # Pending HITL approvals
POST /api/ckc/hitl/{id}/approve  # Approve HITL request
POST /api/ckc/hitl/{id}/reject   # Reject HITL request
WS   /api/ckc/stream             # Real-time event stream
```

#### 1.5.2 WebSocket Event Streaming
- Real-time task updates
- Agent status changes
- HITL notification push
- Log streaming

### Verifikation
- [ ] REST endpoints fungerer
- [ ] WebSocket stream leverer events
- [ ] HITL approval flow fungerer end-to-end
- [ ] Dashboard kan vise live data

---

## Implementation Order

```
Week 1: Database Foundation
├── 1.1.1 Docker setup
├── 1.1.2 Schema creation
└── 1.1.3 Python database layer

Week 2: Message Bus
├── 1.2.1 RabbitMQ setup
├── 1.2.2 Queue architecture
└── 1.2.3 Python message bus

Week 3: Connectors & Knowledge
├── 1.3.1-1.3.3 Connector framework
└── 1.4.1-1.4.2 Knowledge sync

Week 4: Control Panel & Integration
├── 1.5.1-1.5.2 Control Panel API
└── Integration testing
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Database uptime | 99.9% |
| Message delivery rate | 99.99% |
| Average message latency | < 100ms |
| Connector health check interval | 30s |
| HITL response time | < 5min (human) |

---

## Næste Skridt

1. **START:** Fase 1.1.1 - Docker container setup for ckc-postgres
2. Opret database schema
3. Implementer Python database layer
4. Test med eksisterende CKC komponenter

---

*CKC - Det Centrale Nervesystem for Cirkelline Økosystemet*
