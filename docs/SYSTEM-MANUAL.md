# CIRKELLINE SYSTEM MANUAL
**Komplet Arkitektur Dokumentation | v1.0 | 2025-12-12**

---

## DEL 1: SYSTEM OVERBLIK

### 1.1 Hvad er Cirkelline?

Cirkelline er et **multi-agent AI orkestrations-system** bestående af:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CIRKELLINE ØKOSYSTEM                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐   │
│  │  CIRKELLINE     │     │   LIB-ADMIN     │     │ COSMIC LIBRARY  │   │
│  │  (Hovedplatform)│     │   (CKC Admin)   │     │ (Training)      │   │
│  │   Port: 7777    │────▶│   Port: 7779    │────▶│   Port: 7778    │   │
│  └────────┬────────┘     └────────┬────────┘     └─────────────────┘   │
│           │                       │                                     │
│           ▼                       ▼                                     │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐   │
│  │  COMMANDO-      │     │      CLA        │     │   CONSULTING    │   │
│  │  CENTER         │     │  (Desktop App)  │     │   (Website)     │   │
│  │   Port: 8000    │     │   (Tauri)       │     │   Port: 3000    │   │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        5 DATABASES                               │   │
│  │  5432 (Consulting) │ 5433 (Commando) │ 5530 (lib-admin)        │   │
│  │  5532 (cirkelline) │ 5534 (Cosmic)                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Komponent Hierarki

```
NIVEAU 1: PLATFORME
├── cirkelline-system     → Brugervendt AI assistent
├── lib-admin-main        → Administrator kontrol panel
├── Cosmic-Library-main   → Agent trænings akademi
├── Commando-Center-main  → Meta-kognitivt hjerne center
└── Cirkelline-Consulting → Konsultation booking

NIVEAU 2: MODULER
├── CKC-Core             → Kommandant og Mastermind moduler
├── CLA                  → Desktop app med Commander Unit
├── Headquarters         → Event bus, knowledge graph
└── Intelligence         → Collaboration, anomaly detection

NIVEAU 3: AGENTER
├── Cirkelline Orchestrator
├── Research Team (3 researchers)
├── Law Team (2 agents)
├── Specialist Agents (4 types)
├── HASA Agents (17 agents)
├── Kommandanter (4+ types)
└── Mastermind (18 moduler)
```

---

## DEL 2: SERVERE OG PORTE

### 2.1 Backend Servere

| Server | Port | Teknologi | Formål |
|--------|------|-----------|--------|
| **cirkelline-system** | 7777 | FastAPI + AGNO | Hovedplatform, chat, agenter |
| **lib-admin** | 7779 | FastAPI + CrewAI | Admin hub, 17 HASA agenter |
| **Cosmic-Library** | 7778 | FastAPI + CrewAI | Training, knowledge domains |
| **Commando-Center** | 8000 | FastAPI | Task orchestration, routing |
| **Consulting** | 3000 | Next.js API | Booking, scheduling |

### 2.2 Frontend Servere

| Server | Port | Teknologi | Formål |
|--------|------|-----------|--------|
| **cirkelline-ui** | 3000 | Next.js 15 | Chat interface |
| **lib-admin frontend** | 3002 | Next.js 15 | Admin dashboard |
| **Cosmic frontend** | 3000 | Next.js 15 | Training UI |
| **Consulting** | 3000 | Next.js 15 | Booking UI |

### 2.3 Databaser

| Database | Port | Type | Data |
|----------|------|------|------|
| **cirkelline-postgres** | 5532 | PostgreSQL 17 + pgvector | Sessions, memories, embeddings |
| **lib-admin-db** | 5530 | PostgreSQL | Users, subscriptions, VIP |
| **cosmic-db** | 5534 | PostgreSQL + pgvector | Training data, knowledge |
| **odin-eye** | 5433 | PostgreSQL 16 | Command orchestration |
| **consulting-db** | 5432 | PostgreSQL 15 | Bookings, scheduling |

### 2.4 Support Services

| Service | Port | Formål |
|---------|------|--------|
| **Ollama** | 11434 | Lokal LLM inference (LLaMA 3) |
| **ChromaDB** | 8001 | Vector embeddings for RAG |
| **Redis** | 6380 | Cache og sessions |
| **Nginx** | 8090 | API gateway, reverse proxy |
| **Portainer** | 9000 | Docker management UI |
| **Supabase Studio** | 3001 | Database UI |
| **Mailhog** | 8025 | Email testing |

---

## DEL 3: AGENTER OG TEAMS

### 3.1 Cirkelline Hovedplatform

```
CIRKELLINE ORCHESTRATOR
│
├── SPECIALIST AGENTS
│   ├── Audio Specialist   → Transcription, lyd-ID
│   ├── Video Specialist   → Scene analyse
│   ├── Image Specialist   → OCR, billedbeskrivelse
│   └── Document Specialist → PDF, DOCX processing
│
├── RESEARCH TEAM
│   ├── DuckDuckGo Researcher → Nyheder, aktuelle events
│   ├── Exa Researcher        → Semantisk, konceptuel
│   └── Tavily Researcher     → Comprehensive research
│
└── LAW TEAM
    ├── Legal Researcher → Finder juridiske kilder
    └── Legal Analyst    → Analyserer og rådgiver
```

### 3.2 lib-admin HASA Agents (17 stk)

```
HASA AGENTS
├── CSA (Content Screen Agent)      → Skærmanalyse
├── FEIA (Frontend Intent Agent)    → Brugerintention
├── DMA (Document Management Agent) → Dokumenthåndtering
├── Representative                  → Formularer og data
├── RAG Integration                 → Retrieval augmented
├── Autonomy Dashboard             → Agent autonomi
├── Platform Controller            → Platform styring
├── Voice Control                  → Stemmestyring
├── Assistive Orchestrator         → Tilgængelighed
├── Near Contact                   → Kontakt håndtering
├── ISEN-HASA                      → Sikkerhed
├── GDPR Accessibility             → GDPR compliance
├── Airweave Features              → MCP integration
├── Extended Features              → Udvidede funktioner
├── Context Engine                 → Kontekst håndtering
├── OCR Engine                     → Tekstgenkendelse
└── DocFlow Pipeline               → Dokument flow
```

### 3.3 CKC-Core Kommandanter

```
KOMMANDANTER
├── Historiker     → Database historik tracking
├── Bibliotekar    → Vidensbase management
├── Web3           → Blockchain integration
└── Legal          → Juridisk compliance

HVER KOMMANDANT HAR:
├── core.py        → Hovedlogik
├── delegation.py  → Opgave delegering
└── mvp_room.py    → Træningsrum
```

### 3.4 Mastermind Moduler (18 stk)

```
MASTERMIND
├── coordinator.py       → Hovedkoordinator
├── session.py          → Session management
├── roles.py            → Rolledefinitioner
├── feedback.py         → Feedback håndtering
├── resources.py        → Ressource allokering
├── context.py          → Kontekst management
├── os_dirigent.py      → OS integration
├── optimization.py     → Performance tuning
├── ethics.py           → Etisk validering
├── messaging.py        → Intern kommunikation
├── training_room.py    → Træningsrum
├── self_optimization.py → Selvforbedring
├── marketplace.py      → Agent marketplace
├── ux.py               → User experience
├── economics.py        → Token/ressource økonomi
├── super_admin_control.py → Admin kontrol
└── output_integrity.py → Output validering
```

---

## DEL 4: ENDPOINTS OVERSIGT

### 4.1 cirkelline-system (90+ endpoints)

**Auth:**
- `POST /api/auth/signup` - Opret bruger
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout

**Chat:**
- `POST /teams/cirkelline/runs` - Send besked til Cirkelline
- `POST /teams/research-team/runs` - Direkte til Research Team
- `POST /teams/law-team/runs` - Direkte til Law Team

**Knowledge:**
- `POST /api/knowledge/upload` - Upload dokument
- `GET /api/knowledge/search` - Søg i knowledge base
- `DELETE /api/knowledge/{id}` - Slet dokument

**Sessions:**
- `GET /api/sessions` - Hent brugerens sessions
- `GET /api/sessions/{id}` - Hent specifik session

**Memories:**
- `GET /api/memories` - Hent brugerens memories
- `POST /api/memories/search` - Søg i memories

**Google Integration (28 endpoints):**
- OAuth, Gmail, Calendar, Tasks

**Notion Integration (14 endpoints):**
- OAuth, databases, pages

### 4.2 lib-admin (100+ endpoints)

**Commander Unit (nyligt tilføjet):**
- `GET /api/commander/unit/status` - Unit status
- `POST /api/commander/unit/start` - Start unit
- `POST /api/commander/unit/stop` - Stop unit
- `POST /api/commander/unit/tasks` - Tilføj research task
- `GET /api/commander/unit/tasks` - Hent task queue
- `GET /api/commander/unit/findings` - Hent findings
- `POST /api/commander/unit/sync` - Force sync
- `PUT /api/commander/unit/autonomy` - Sæt autonomi level

**Admin:**
- `GET /api/admin/users` - Liste brugere
- `GET /api/admin/stats` - System statistik

**HASA Agents:**
- `GET /api/{agent}/status` - Agent status
- `POST /api/{agent}/process` - Process request

---

## DEL 5: DATA FLOW

### 5.1 Chat Request Flow

```
[Bruger]
    ↓ besked
[Frontend (Next.js)]
    ↓ POST /teams/cirkelline/runs + JWT
[FastAPI Middleware]
    ↓ JWT validering, user_id extraction
[Cirkelline Orchestrator]
    ↓ Analyser intent
[Specialist Agent/Team]
    ↓ Process opgave
[Response med SSE streaming]
    ↓
[Frontend viser svar]
```

### 5.2 Knowledge Upload Flow

```
[Bruger uploader fil]
    ↓
[Frontend sender til /api/knowledge/upload]
    ↓
[Backend extraherer tekst]
    ↓
[AGNO chunker og embedder]
    ↓
[pgvector gemmer 768-dim embeddings]
    ↓
[Metadata gemmes med user_id filter]
```

### 5.3 Cross-Platform Sync Flow

```
[CLA Desktop App]
    ↓ HTTP request
[lib-admin /api/commander/unit/*]
    ↓
[lib-admin state opdateres]
    ↓ (planlagt: Redis pub/sub)
[Andre platforme notificeres]
```

---

## DEL 6: BRUGER ISOLATION

### 6.1 Grundprincip
**ALT er filtreret med user_id**

```sql
-- Sessions
WHERE user_id = 'current-user'

-- Memories
WHERE user_id = 'current-user'

-- Documents
WHERE metadata->>'user_id' = 'current-user'
```

### 6.2 JWT Token Indhold

```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "display_name": "Name",
  "user_type": "User|Admin",
  "is_admin": false,
  "tier_slug": "member",
  "tier_level": 1,
  "exp": 1234567890
}
```

---

## DEL 7: TODO-LISTER (IKKE FÆRDIGUDVIKLET)

### 7.1 Planlagt Struktur

```python
class Todo:
    id: str
    user_id: str
    content: str
    status: str  # pending, in_progress, completed
    priority: str  # critical, high, normal, low
    due_date: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]
```

### 7.2 Planlagte Endpoints

```
POST   /api/todos          - Opret todo
GET    /api/todos          - Liste todos
PUT    /api/todos/{id}     - Opdater todo
DELETE /api/todos/{id}     - Slet todo
GET    /api/todos/active   - Aktive todos
```

### 7.3 Integration med Cirkelline

```
Bruger: "Hvad skal jeg lave i dag?"
Cirkelline: [Henter todos] "Du har 3 opgaver:
  1. [Høj] Afslut rapport - deadline i dag
  2. [Normal] Ring til kunde
  3. [Lav] Ryd op i inbox"
```

---

## DEL 8: KV1NT (IKKE IMPLEMENTERET)

### 8.1 Koncept

KV1NT er en **tids-styret assistent** der:
- Proaktivt minder om deadlines
- Forbereder mødemateriale
- Giver dag-overblik om morgenen
- Reagerer på kalender events

### 8.2 Planlagt Arkitektur

```python
class KV1NT:
    def morning_briefing(self, user_id: str) -> str:
        """Morgenoverblik med dagens opgaver"""
        pass

    def deadline_check(self, user_id: str) -> List[Alert]:
        """Check kommende deadlines"""
        pass

    def prepare_meeting(self, event_id: str) -> MeetingPrep:
        """Forbered mødemateriale"""
        pass
```

---

## DEL 9: LÆRERUM OG TRAINING ROOMS

### 9.1 Struktur

```
headquarters/
├── learning_rooms/
│   ├── hcv_fase5/          # Hyper-Cognitive Verification tests
│   │   ├── hcv_5_1_scanner_test.py
│   │   ├── hcv_5_2_analysis_test.py
│   │   ├── hcv_5_3_governance_test.py
│   │   ├── hcv_5_4_social_test.py
│   │   ├── hcv_5_5_llm_test.py
│   │   └── run_all_hcv_tests.py
│   └── [fremtidige rum]
```

### 9.2 Cosmic Library Training

```
Cosmic Library tilbyder:
├── Mentor Agents     → Overordnet vejledning
├── Coach Agents      → Specifik træning
├── Trainer Agents    → Øvelser og tests
└── Knowledge Domains → Specialiserede vidensområder
```

---

## DEL 10: SIKKERHED

### 10.1 Autentificering
- JWT tokens med 7-dages udløb
- HttpOnly cookies
- AES-256-GCM kryptering af OAuth tokens

### 10.2 Autorisering
- User isolation via user_id
- Admin roles (SUPER_ADMIN, ADMIN, OBSERVER)
- Platform-specifik adgang

### 10.3 Rate Limiting
- SlowAPI i produktion
- Disabled i test mode (TESTING=true)

---

## DEL 11: FEJLFINDING

### 11.1 Common Issues

| Problem | Løsning |
|---------|---------|
| 401 Unauthorized | Token udløbet - login igen |
| Database fejl | `docker start cirkelline-postgres` |
| Port i brug | Check med `ss -tlnp` |
| Test fejler | Sæt `TESTING=true ENVIRONMENT=testing` |

### 11.2 Log Locations

```bash
# Docker logs
docker logs cirkelline-postgres

# AWS logs
aws logs tail /ecs/cirkelline-system-backend --since 5m

# Python logs
tail -f /var/log/cirkelline/*.log
```

---

## DEL 12: EMERGENCY KONTAKT

| Ressource | Værdi |
|-----------|-------|
| **Production URL** | https://cirkelline.com |
| **API URL** | https://api.cirkelline.com |
| **AWS Account** | 710504360116 |
| **AWS Region** | eu-north-1 (Stockholm) |
| **Ivo (CEO)** | opnureyes2@gmail.com |
| **Rasmus (CEO)** | opnureyes2@gmail.com |

---

*Sidste opdatering: 2025-12-12*
*Se også: BASELINE-2025-12-12.md, ROADMAP-2025-12-12.md, UDVIKLINGS-GUIDE.md*
