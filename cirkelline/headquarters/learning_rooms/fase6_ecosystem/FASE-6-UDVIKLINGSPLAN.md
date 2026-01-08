# FASE 6: ECOSYSTEM ACTIVATION & MONETIZATION
# UDVIKLINGSPLAN MED UDVIDET MANDAT

**Version:** 1.0.0
**Oprettet:** 2025-12-09
**Status:** AKTIV UDVIKLING
**Parallel Udvikling:** JA (Track A + Track B)

---

## 1. EXECUTIVE SUMMARY

FASE 6 aktiverer Cirkellines fulde potentiale med:
1. **Lokal Kommandor (CLA + Commander Unit)** - Desktop agent med integreret research pipeline
2. **Multi-Bibliotek Arkitektur** - Cosmic Library + Notion synkroniseret
3. **Historiker & Bibliotekar Kommandanter** - Videndomane-specifikke agenter
4. **API Marketplace** - Monetarisering af Web3 intelligence
5. **Organisk Enhedsbidrag** - Decentraliseret resource sharing

---

## 2. ARKITEKTUR OVERVIEW

```
+------------------------------------------------------------------------------+
|                        CIRKELLINE ECOSYSTEM                                    |
+------------------------------------------------------------------------------+
|                                                                               |
|  +-------------------------+     +-------------------------+                  |
|  |    LOKAL KOMMANDOR      |     |    CENTRAL PLATFORM     |                  |
|  |    (CLA + Commander)    |     |    (CKC Backend)        |                  |
|  +-------------------------+     +-------------------------+                  |
|  | - Tauri Desktop App     |     | - FastAPI Backend       |                  |
|  | - Rust Inference Engine |<--->| - Agent Orchestrator    |                  |
|  | - Commander Unit        |gRPC | - Knowledge Hub         |                  |
|  | - Local LLM Fallback    |     | - User Management       |                  |
|  | - Offline Capabilities  |     | - Session Storage       |                  |
|  +-------------------------+     +-------------------------+                  |
|            |                              |                                   |
|            v                              v                                   |
|  +-------------------------+     +-------------------------+                  |
|  |    LOCAL STORAGE        |     |    COSMIC LIBRARY       |                  |
|  +-------------------------+     +-------------------------+                  |
|  | - User Data (isoleret)  |     | - Multi-Bibliotek Hub   |                  |
|  | - Cached Models         |     | - Vector Store          |                  |
|  | - Sync Queue            |     | - Notion Integration    |                  |
|  +-------------------------+     +--------+----------------+                  |
|                                          |                                    |
|                    +---------------------+---------------------+              |
|                    |                     |                     |              |
|                    v                     v                     v              |
|           +----------------+    +----------------+    +----------------+      |
|           | BIBLIOTEK A    |    | BIBLIOTEK B    |    | BIBLIOTEK N    |      |
|           | (Web3 Research)|    | (Legal Domain) |    | (Custom...)    |      |
|           +----------------+    +----------------+    +----------------+      |
|           | Historiker-K   |    | Historiker-K   |    | Historiker-K   |      |
|           | Bibliotekar-K  |    | Bibliotekar-K  |    | Bibliotekar-K  |      |
|           | Agent Learning |    | Agent Learning |    | Agent Learning |      |
|           | Database       |    | Database       |    | Database       |      |
|           +----------------+    +----------------+    +----------------+      |
|                                                                               |
+------------------------------------------------------------------------------+
```

---

## 3. PARALLEL UDVIKLINGS TRACKS

### TRACK A: Lokal Kommandor (CLA + Commander Unit)
**Prioritet:** P0 (Kritisk Sti)
**Team:** Desktop Integration

### TRACK B: API Marketplace & Monetarisering
**Prioritet:** P0 (Kritisk Sti)
**Team:** Backend Integration

Begge tracks korer parallel og synkroniseres via felles API kontrakter.

---

## 4. TRACK A: LOKAL KOMMANDOR

### 4.1 Nuvaerende CLA Struktur

```
cla/
├── src/                      # React Frontend
│   ├── components/           # UI Components
│   │   ├── chat/            # Chat interface
│   │   ├── models/          # Model selection
│   │   └── settings/        # Configuration
│   ├── services/            # API Services
│   ├── stores/              # Zustand State
│   └── types/               # TypeScript Types
│
├── src-tauri/               # Rust Backend
│   └── src/
│       ├── commands/        # Tauri Commands
│       ├── inference/       # Local LLM Engine
│       ├── models/          # Data Models
│       ├── security/        # Security Module
│       ├── telemetry/       # Usage Tracking
│       └── utils/           # Utilities
```

### 4.2 Commander Unit Integration

**Ny Struktur (Post-Integration):**

```
cla/
├── src-tauri/src/
│   ├── commands/
│   │   ├── mod.rs
│   │   ├── chat.rs
│   │   ├── models.rs
│   │   └── commander.rs       # NY: Commander Unit commands
│   │
│   ├── commander/              # NY: Commander Unit Module
│   │   ├── mod.rs
│   │   ├── unit.rs            # Core Commander logic
│   │   ├── decision_engine.rs # Autonomous decisions
│   │   ├── task_scheduler.rs  # Research task queue
│   │   ├── feedback_loop.rs   # Learning from outcomes
│   │   └── sync.rs            # CKC synchronization
│   │
│   ├── research/               # NY: Research Pipeline
│   │   ├── mod.rs
│   │   ├── pipeline.rs        # Research orchestration
│   │   ├── adapters/
│   │   │   ├── github.rs      # GitHub monitoring
│   │   │   ├── arxiv.rs       # Research papers
│   │   │   └── social.rs      # Social media (Lens, Farcaster)
│   │   └── processors/
│   │       ├── nlp.rs         # Entity extraction
│   │       └── scorer.rs      # Relevance scoring
│   │
│   └── inference/
│       ├── mod.rs
│       ├── engine.rs
│       ├── llama.rs           # llama.cpp integration
│       └── ollama.rs          # Ollama fallback
```

### 4.3 Definition of Done (DoD) - Track A

```yaml
DoD_Track_A:
  functional:
    - [ ] Commander Unit korer autonomt i CLA
    - [ ] Research pipeline scanner GitHub/arXiv lokalt
    - [ ] gRPC forbindelse til CKC backend operationel
    - [ ] Offline mode med local LLM fungerer
    - [ ] Sync queue handler network disconnects

  integration:
    - [ ] Commander findings pushes til Cosmic Library
    - [ ] User data forbliver isoleret (aldrig synkroniseret)
    - [ ] Agent learning data synkroniseres til central DB

  ux:
    - [ ] Research status vises i system tray
    - [ ] Notifikationer for vigtige findings
    - [ ] Settings panel for Commander configuration
```

### 4.4 Implementation Tasks

| Task ID | Beskrivelse | Status | Blokeret af |
|---------|-------------|--------|-------------|
| A-001 | Opret commander/ modul i Rust | PENDING | - |
| A-002 | Implementer decision_engine.rs | PENDING | A-001 |
| A-003 | Implementer research pipeline adapters | PENDING | A-001 |
| A-004 | gRPC client til CKC | PENDING | A-001 |
| A-005 | Sync queue med offline support | PENDING | A-004 |
| A-006 | UI integration (system tray, notifications) | PENDING | A-002 |

---

## 5. TRACK B: API MARKETPLACE

### 5.1 API Gateway Arkitektur

```
+------------------------+
|   API GATEWAY          |
|   (Kong/FastAPI)       |
+------------------------+
| - Rate Limiting        |
| - Authentication       |
| - Usage Metering       |
| - Billing Integration  |
+----------+-------------+
           |
           v
+----------+-------------+
|   MONETIZABLE APIs     |
+------------------------+
| /api/v1/web3/scan      |
| /api/v1/web3/analyze   |
| /api/v1/ai/research    |
| /api/v1/ai/report      |
+------------------------+
```

### 5.2 Pricing Tiers

```yaml
tiers:
  free:
    price: 0
    limits:
      web3_scan: 10/day
      web3_analyze: 5/day
      ai_research: 5/day
    features:
      - basic_scanning
      - community_support

  starter:
    price: 49/month
    limits:
      web3_scan: 1000/month
      web3_analyze: 100/month
      ai_research: 100/month
    features:
      - priority_scanning
      - email_support
      - webhook_notifications

  pro:
    price: 199/month
    limits:
      web3_scan: 10000/month
      web3_analyze: 1000/month
      ai_research: 1000/month
    features:
      - all_starter_features
      - custom_alerts
      - api_priority
      - dedicated_support

  enterprise:
    price: custom
    limits: unlimited
    features:
      - all_pro_features
      - sla_guarantee
      - on_premise_option
      - custom_integrations
```

### 5.3 Definition of Done (DoD) - Track B

```yaml
DoD_Track_B:
  functional:
    - [ ] API Gateway med rate limiting operationel
    - [ ] Developer portal med dokumentation live
    - [ ] API key management (create, revoke, rotate)
    - [ ] Usage analytics dashboard
    - [ ] Stripe billing integration

  business:
    - [ ] 4 pricing tiers implementeret
    - [ ] Trial period flow fungerer
    - [ ] Upgrade/downgrade flows testet

  security:
    - [ ] OAuth 2.0 authentication
    - [ ] Request validation og sanitization
    - [ ] Audit logging for alle API calls
```

---

## 6. MULTI-BIBLIOTEK ARKITEKTUR

### 6.1 Cosmic Library som Hub

Cosmic Library fungerer som central hub for flere videndomaner:

```
cosmic_library/
├── core/
│   ├── hub.py              # Multi-bibliotek router
│   ├── registry.py         # Bibliotek registration
│   └── sync_engine.py      # Notion synchronization
│
├── libraries/
│   ├── base.py             # Abstract Library class
│   ├── web3_research.py    # Web3 Research Library
│   ├── legal_domain.py     # Legal Domain Library
│   └── custom_factory.py   # Dynamic library creation
│
├── kommandanter/
│   ├── historiker.py       # Historiker-Kommandant base
│   ├── bibliotekar.py      # Bibliotekar-Kommandant base
│   └── implementations/
│       ├── web3_historiker.py
│       ├── web3_bibliotekar.py
│       ├── legal_historiker.py
│       └── legal_bibliotekar.py
│
└── databases/
    ├── user_data/          # Bruger-specifikke data (ISOLERET)
    ├── agent_learning/     # Agent laring (DELT)
    └── knowledge_base/     # Viden repositories
```

### 6.2 Historiker-Kommandant Interface

```python
class HistorikerKommandant(ABC):
    """
    Ansvarlig for historisk bevaring og kontekstualisering.

    Hver videndomane har sin egen Historiker der:
    - Vedligeholder temporal kontekst
    - Tracker evolution af viden over tid
    - Identificerer patterns og trends
    - Preserverer historiske versioner
    """

    domain: str

    @abstractmethod
    async def record_event(self, event: KnowledgeEvent) -> None:
        """Registrer videns-event med timestamp og kontekst."""
        pass

    @abstractmethod
    async def get_timeline(
        self,
        topic: str,
        start: datetime,
        end: datetime
    ) -> Timeline:
        """Hent tidslinje for et emne."""
        pass

    @abstractmethod
    async def analyze_evolution(self, topic: str) -> EvolutionReport:
        """Analyser hvordan viden om et emne har udviklet sig."""
        pass

    @abstractmethod
    async def find_patterns(
        self,
        window: timedelta
    ) -> List[Pattern]:
        """Identificer patterns i videns-udvikling."""
        pass
```

### 6.3 Bibliotekar-Kommandant Interface

```python
class BibliotekarKommandant(ABC):
    """
    Ansvarlig for organisering, klassifikation og soging.

    Hver videndomane har sin egen Bibliotekar der:
    - Organiserer viden i logiske kategorier
    - Vedligeholder taxonomier og ontologier
    - Faciliterer effektiv soging
    - Forbinder relateret viden
    """

    domain: str

    @abstractmethod
    async def classify(self, content: Content) -> Classification:
        """Klassificer indhold i domane-specifikke kategorier."""
        pass

    @abstractmethod
    async def index(self, content: Content) -> IndexEntry:
        """Indekser indhold for effektiv soging."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None
    ) -> SearchResults:
        """Sog i biblioteket med optional filtre."""
        pass

    @abstractmethod
    async def find_related(
        self,
        content_id: str,
        depth: int = 1
    ) -> List[RelatedContent]:
        """Find relateret indhold."""
        pass

    @abstractmethod
    async def get_taxonomy(self) -> Taxonomy:
        """Hent domanens taxonomi."""
        pass
```

### 6.4 Agent Learning Database Schema

```sql
-- Separat fra brugerdata - deles pa tvaers af systemet
CREATE SCHEMA agent_learning;

-- Domane-specifikke laeringer
CREATE TABLE agent_learning.domain_learnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(100) NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    learning_type VARCHAR(50) NOT NULL,  -- 'pattern', 'fact', 'correction', 'preference'
    content JSONB NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    source_session_id UUID,  -- Reference, IKKE user_id
    created_at TIMESTAMPTZ DEFAULT NOW(),
    validated_at TIMESTAMPTZ,
    validation_count INT DEFAULT 0
);

-- Kryds-domane correlationer
CREATE TABLE agent_learning.cross_domain_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_domain VARCHAR(100) NOT NULL,
    source_learning_id UUID REFERENCES agent_learning.domain_learnings(id),
    target_domain VARCHAR(100) NOT NULL,
    target_learning_id UUID REFERENCES agent_learning.domain_learnings(id),
    link_type VARCHAR(50) NOT NULL,  -- 'related', 'contradicts', 'supports', 'extends'
    strength FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Historiker timeline data
CREATE TABLE agent_learning.knowledge_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(100) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    historiker_notes TEXT
);

-- Bibliotekar taxonomi
CREATE TABLE agent_learning.taxonomy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(100) NOT NULL,
    category_path TEXT[] NOT NULL,  -- ['Web3', 'DeFi', 'Lending']
    category_name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES agent_learning.taxonomy(id),
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_learnings_domain ON agent_learning.domain_learnings(domain);
CREATE INDEX idx_learnings_agent ON agent_learning.domain_learnings(agent_id);
CREATE INDEX idx_timeline_domain_topic ON agent_learning.knowledge_timeline(domain, topic);
CREATE INDEX idx_taxonomy_domain ON agent_learning.taxonomy(domain);
```

---

## 7. NOTION INTEGRATION

### 7.1 Synkroniserings Arkitektur

```
+-------------------+     +-------------------+     +-------------------+
|   COSMIC LIBRARY  |<--->|   SYNC ENGINE     |<--->|   NOTION API      |
+-------------------+     +-------------------+     +-------------------+
| - Vector Store    |     | - Bidirectional   |     | - Databases       |
| - Kategorier      |     | - Conflict Res.   |     | - Pages           |
| - Metadata        |     | - Delta Sync      |     | - Blocks          |
+-------------------+     +-------------------+     +-------------------+
```

### 7.2 Sync Configuration

```yaml
notion_sync:
  databases:
    research_findings:
      cosmic_library_category: "web3_research"
      sync_direction: "bidirectional"
      conflict_resolution: "latest_wins"
      fields_map:
        title: "name"
        content: "analysis"
        tags: "categories"
        status: "validation_status"

    legal_documents:
      cosmic_library_category: "legal_domain"
      sync_direction: "notion_to_cosmic"
      fields_map:
        title: "document_name"
        content: "full_text"
        jurisdiction: "metadata.jurisdiction"

  sync_schedule:
    full_sync: "0 */6 * * *"  # Every 6 hours
    delta_sync: "*/15 * * * *"  # Every 15 minutes

  rate_limits:
    requests_per_second: 3
    backoff_multiplier: 2
```

---

## 8. ORGANISK ENHEDSBIDRAG

### 8.1 Resource Contribution Model

```python
class ResourceContribution:
    """
    Decentraliseret resource sharing model.

    Brugere kan bidrage med:
    - GPU compute tid til model inference
    - CPU cycles til data processing
    - Storage til distributed caching
    - Bandwidth til content distribution
    """

    @dataclass
    class ContributionMetrics:
        gpu_hours: float
        cpu_hours: float
        storage_gb_hours: float
        bandwidth_gb: float

    @dataclass
    class RewardCalculation:
        base_credits: int
        quality_multiplier: float  # Baseret pa uptime og reliability
        demand_multiplier: float   # Baseret pa network eftersporgsel
        total_credits: int
```

### 8.2 Contribution Credits System

```yaml
credits_system:
  earning_rates:
    gpu_inference_hour: 100 credits
    cpu_processing_hour: 20 credits
    storage_gb_month: 10 credits
    bandwidth_gb: 5 credits

  spending_options:
    api_request: 1 credit
    premium_feature_access: 50 credits/month
    priority_processing: 10 credits
    custom_model_training: 1000 credits

  quality_bonuses:
    uptime_99_percent: 1.5x multiplier
    fast_response_time: 1.2x multiplier
    early_adopter: 2x multiplier (first 100 users)
```

---

## 9. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Uge 1-2)

| Task | Track | Status |
|------|-------|--------|
| Opret Commander Unit modul i CLA | A | PENDING |
| Setup API Gateway med basic auth | B | PENDING |
| Design multi-bibliotek database schema | - | PENDING |
| Definer Historiker/Bibliotekar interfaces | - | PENDING |

### Phase 2: Core Integration (Uge 3-4)

| Task | Track | Status |
|------|-------|--------|
| Implementer research pipeline i Rust | A | PENDING |
| Implementer pricing tiers | B | PENDING |
| Bygge forste Historiker implementation | - | PENDING |
| Bygge forste Bibliotekar implementation | - | PENDING |

### Phase 3: Sync & Polish (Uge 5-6)

| Task | Track | Status |
|------|-------|--------|
| gRPC sync mellem CLA og CKC | A | PENDING |
| Stripe billing integration | B | PENDING |
| Notion sync engine | - | PENDING |
| Agent learning database migration | - | PENDING |

### Phase 4: Launch Preparation (Uge 7-8)

| Task | Track | Status |
|------|-------|--------|
| End-to-end testing | ALL | PENDING |
| Documentation | ALL | PENDING |
| Beta user onboarding | ALL | PENDING |
| Production deployment | ALL | PENDING |

---

## 10. VALIDATION CHECKPOINTS

### HCV-6.1: Lokal Kommandor UX
- [ ] Commander status er synlig og forstaeligt
- [ ] Research findings prasenteres intuitivt
- [ ] Offline mode er transparent for brugeren
- [ ] Sync status kommunikeres klart

### HCV-6.2: API Marketplace
- [ ] Developer onboarding er smooth
- [ ] Pricing er transparent
- [ ] Usage metrics er nojagtige
- [ ] Billing er korrekt

### HCV-6.3: Multi-Bibliotek
- [ ] Navigation mellem biblioteker er intuitiv
- [ ] Sogeresultater er relevante
- [ ] Historik er brugbar
- [ ] Taxonomi er forstaeelig

### HCV-6.4: Organisk Bidrag
- [ ] Contribution tracking er transparent
- [ ] Credits system er retfaerdigt
- [ ] Resource usage er optimalt
- [ ] Rewards er motiverende

---

## 11. MISSING PIECES

| ID | Beskrivelse | Blokerer | Plan |
|----|-------------|----------|------|
| MP-005 | Marketing Website | Launch | Prioriter i Phase 4 |
| MP-006 | Customer Support System | Launch | Integrer Intercom/Zendesk |
| MP-011 | Notion OAuth Flow | Sync | Implementer i Phase 3 |
| MP-012 | Stripe Webhook Handler | Billing | Implementer i Phase 3 |

---

## 12. SUCCESS METRICS

```yaml
success_criteria:
  technical:
    - Commander Unit autonomy: >24h uptime
    - API latency: <200ms p95
    - Sync reliability: >99.9%
    - Offline capability: Full functionality

  business:
    - API signups: >100 in first month
    - Paid conversions: >5%
    - MRR target: $5,000 by month 3

  user_experience:
    - NPS score: >50
    - Setup time: <5 minutes
    - Documentation coverage: 100%
```

---

*Genereret som del af FASE 6 Ecosystem Activation*
*Version 1.0.0 - 2025-12-09*
