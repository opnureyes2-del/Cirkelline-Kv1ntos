# System Architecture - cirkelline-kv1ntos

**Project:** cirkelline-kv1ntos
**Version:** 3.0.0 (KV1NTOS)
**Type:** Multi-Agent AI Orchestration System
**Base Version:** Cirkelline v1.3.8
**Status:** EXPERIMENTAL - Untested

---

## Overview

cirkelline-kv1ntos is an enhanced experimental version of the Cirkelline System with a sophisticated multi-layered AI orchestration framework called **KV1NTOS** (Knowledge + Autonomous Orchestration).

### Architecture Tiers

```
┌─────────────────────────────────────────────┐
│  Frontend Layer (Next.js 15 + TypeScript)   │
│  - Chat Interface                           │
│  - Session Management                       │
│  - Document Upload                          │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│  API Layer (FastAPI 0.109+)                 │
│  - Authentication (JWT)                     │
│  - Knowledge Filtering                      │
│  - Session Endpoints                        │
│  - Memory Management                        │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│  Orchestration Layer (AGNO v2.3.4)          │
│  ├── Cirkelline (Main Orchestrator)         │
│  ├── ODIN (Master Orchestrator - KV1NTOS)  │
│  ├── Admiral (Strategic Governance)        │
│  └── NL Terminal (Natural Language Control)│
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│  Agent Layer (AGNO Agents)                  │
│  ├── Specialist Agents (4)                  │
│  │   ├── Audio Specialist                   │
│  │   ├── Video Specialist                   │
│  │   ├── Image Specialist                   │
│  │   └── Document Specialist                │
│  ├── Research Team                          │
│  ├── Law Team                               │
│  ├── Agent Factory (Dynamic Creation)       │
│  └── Flock Management                       │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│  Knowledge Layer                            │
│  ├── Vector DB (pgvector)                   │
│  ├── Embeddings (Gemini 768-dim)            │
│  ├── Hybrid Search (Semantic + BM25)        │
│  └── Knowledge Graph (KV1NTOS)              │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│  Infrastructure                             │
│  ├── PostgreSQL 17 (Database)               │
│  ├── pgvector (Vector Storage)              │
│  ├── Redis 6+ (Caching)                     │
│  └── RabbitMQ (Message Queue)               │
└─────────────────────────────────────────────┘
```

---

## Core Components

### 1. Frontend Layer
- **Framework:** Next.js 15 with App Router
- **Language:** TypeScript
- **State Management:** Zustand (persistent)
- **Styling:** TailwindCSS
- **Port:** 3000
- **Real-time:** Server-Sent Events (SSE)

**Key Components:**
- Chat interface with message streaming
- Session sidebar with history
- File upload for documents
- Memory viewer
- Authentication forms

### 2. API Layer (FastAPI)
- **Framework:** FastAPI 0.109+
- **Port:** 7777
- **Language:** Python 3.12+

**Key Endpoints:**
- `POST /teams/cirkelline/runs` - Main chat endpoint
- `POST /api/auth/login` - User authentication
- `POST /api/auth/signup` - User registration
- `POST /api/knowledge/upload` - Document upload
- `GET /api/memories` - Retrieve user memories
- `GET /health` - Health check
- `GET /config` - System configuration

**Security:**
- JWT middleware (7-day expiration)
- User isolation by `user_id`
- bcrypt password hashing
- CORS protection

### 3. Orchestration Layer

#### Main Orchestrator (Cirkelline)
Routes user messages to appropriate agents:
- Analyzes intent
- Determines routing logic
- Rewrites responses in friendly tone
- Manages conversation flow

#### KV1NTOS Enhancements
- **ODIN:** Master orchestrator coordinating all agents
- **Admiral:** Strategic governance layer
- **Flock Management:** Organize agents into collaborative groups
- **Learning Rooms:** Virtual training environments
- **NL Terminal:** Natural language system control
- **Code Guardian:** Autonomous code quality monitoring

### 4. Agent Layer

#### Specialist Agents (4)
1. **Audio Agent** - Transcription, sound identification
2. **Video Agent** - Scene analysis, content extraction
3. **Image Agent** - OCR, image description
4. **Document Agent** - PDF, DOCX processing

#### Teams
- **Research Team** - Web research and synthesis
  - Web Researcher (searches)
  - Research Analyst (synthesizes)
- **Law Team** - Legal research and analysis
  - Legal Researcher (finds sources)
  - Legal Analyst (provides analysis)

#### Agent Factory (KV1NTOS)
- Dynamic agent creation
- Runtime composition
- Automatic capability detection

#### Flock Management (KV1NTOS)
- Group agents into teams
- Manage collaborative workflows
- Enable cross-agent learning

### 5. Knowledge Layer

#### Vector Database
- **Type:** PostgreSQL 17 + pgvector extension
- **Storage:** `ai.cirkelline_knowledge_vectors` table
- **Embedding Size:** 768 dimensions (Gemini)
- **Search Type:** Hybrid (semantic + BM25)

#### Embeddings
- **Provider:** Google Gemini API
- **Model:** gemini-2.5-flash
- **Dimensions:** 768
- **Rate Limit:** 1,500 RPM (Tier 1)

#### Knowledge Sources
- User-uploaded documents
- Web search results
- Conversation memory
- Knowledge graphs

### 6. Infrastructure

#### Database (PostgreSQL 17)
- **Port:** 5532 (Docker)
- **Container:** cirkelline-postgres
- **Connection:** `postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline`
- **Schemas:**
  - `public` - Users and auth
  - `ai` - Sessions, memories, knowledge

#### Schema Structure
```
ai schema:
├── agno_sessions (Chat sessions)
├── agno_memories (User memories)
├── agno_memories_archive (Archived memories)
├── agno_knowledge (Document metadata)
├── cirkelline_knowledge_vectors (Vector embeddings)
└── workflow_runs (Workflow execution tracking)

public schema:
├── users (Authentication)
└── admin_profiles (Admin extended data)
```

#### Caching (Redis)
- **Port:** 6381
- **Purpose:** Session caching, message buffering
- **Configuration:** Standard Redis 6+

#### Message Queue (RabbitMQ)
- **Port:** 5672
- **Purpose:** Async task processing
- **Configuration:** Standard RabbitMQ

---

## Request Flow

```
1. User Message
   ↓
2. Frontend (Next.js)
   - Capture input
   - Authenticate with JWT
   ↓
3. POST /teams/cirkelline/runs
   - Send message + session_id
   - Backend extracts JWT claims
   ↓
4. JWT Middleware
   - Verify token
   - Extract user_id
   - Load admin profile (if applicable)
   ↓
5. Custom Endpoint
   - Filter knowledge by user_id
   - Apply context from admin profile
   ↓
6. Cirkelline Orchestrator
   - Analyze user intent
   - Route to specialist/team
   ↓
7. Specialist Agent/Team
   - Process request
   - Access filtered knowledge
   - Generate response
   ↓
8. Cirkelline (Rewriter)
   - Synthesize response
   - Apply conversational tone
   - Add context
   ↓
9. SSE Stream → Frontend → User
```

---

## Key Architectural Decisions

### 1. User Isolation by user_id
- ALL data filtered at database query level
- Sessions, memories, documents isolated
- Enables multi-user safety
- Privacy by design

### 2. Conversational Interface
- Users interact with one "assistant"
- Agent orchestration hidden
- Clean, intuitive experience
- Transparent when needed

### 3. Knowledge Filtering
- User documents searchable only by that user
- Hybrid search (semantic + keyword)
- 768-dimensional embeddings
- HNSW indexes for performance

### 4. Session Management
- Backend generates UUIDs for new chats
- Persistent session history
- Summary function prevents context overflow
- AGNO enables session summaries

### 5. Hybrid Vector Search
- Semantic search (vector similarity)
- Keyword search (BM25)
- Combined scoring
- Better retrieval accuracy

### 6. JWT-based Authentication
- Centralized auth in middleware
- 7-day token expiration
- Admin profiles injected transparently
- Bcrypt password hashing

---

## KV1NTOS Enhancements (Experimental)

### Agent Factory (v2.4.0)
- Dynamic agent creation
- Runtime capability composition
- Automatic skill detection
- Self-configuring agents

### Flock Orchestrator (v2.5.0)
- Collaborative agent groups
- Learning rooms for agent training
- Cross-team coordination
- Swarm optimization

### Continuous Optimization (v2.7.0)
- Memory compression
- Performance tuning
- Resource allocation
- Workload balancing

### Knowledge Graph (v2.11.0)
- Semantic relationship mapping
- Entity extraction
- Context linking
- Cross-document reasoning

### Admiral (v2.1.0)
- Strategic decision making
- Long-term planning
- Priority management
- Governance enforcement

### Code Guardian (v2.1.0)
- Autonomous code monitoring
- Quality metrics tracking
- Issue detection
- Continuous improvement

### NL Terminal (v2.3.0)
- Natural language commands
- System control interface
- Query interface
- Conversational debugging

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Next.js | 15 | Web UI |
| | TypeScript | Latest | Type safety |
| | TailwindCSS | Latest | Styling |
| | Zustand | Latest | State management |
| **Backend** | FastAPI | 0.109+ | API framework |
| | Python | 3.12+ | Runtime |
| | AGNO | 2.3.4 | Multi-agent orchestration |
| **AI** | Google Gemini | 2.5 Flash | LLM |
| | pgvector | Latest | Vector storage |
| **Database** | PostgreSQL | 17 | Primary DB |
| | Redis | 6+ | Caching |
| | RabbitMQ | Latest | Message queue |
| **Deployment** | Docker | Latest | Containerization |
| | AWS ECS Fargate | Latest | Production (when stable) |

---

## Performance Characteristics

- **Latency:** <2s for typical queries (streaming)
- **Throughput:** 100+ concurrent sessions
- **Vector Search:** <100ms (HNSW index)
- **Memory:** ~2GB baseline (scales with agents)
- **Database:** <1,000 concurrent connections

---

## Known Limitations

- **Untested:** No production validation yet
- **Experimental Features:** KV1NTOS features not verified
- **Single User Instance:** Designed for 1-3 concurrent users
- **No Persistence:** Agent state not persisted (stateless design)
- **Integration:** Projects are isolated, no cross-system comms

---

## FEJLHÅNDTERING

### Problem 1: FastAPI Backend Fails to Start

**Symptom:**
- `uvicorn main:app` crashes with error
- Port 8000 not responding
- Error: "ModuleNotFoundError" or "ImportError"

**Årsag:**
- Missing Python dependencies (AGNO, pgvector client)
- PostgreSQL not running (container stopped)
- Port 8000 already in use
- .env file missing required variables

**Diagnosticering (Bash):**
```bash
# 1. Check backend dependencies
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/cirkelline-ui
source venv/bin/activate
pip list | grep -i "agno\|psycopg2\|pgvector"

# 2. Check PostgreSQL container
docker ps | grep kv1ntos-postgres

# 3. Check port 8000
netstat -tuln | grep 8000

# 4. Check .env file
cat .env | grep -E "DATABASE_URL|GEMINI_API_KEY"
```

**Fix (Steps):**
1. Install missing dependencies: `pip install -r requirements.txt`
2. Start PostgreSQL: `docker compose up -d postgres`
3. Kill process on port 8000: `lsof -ti:8000 | xargs kill -9`
4. Copy .env.example to .env: `cp .env.example .env`
5. Add Gemini API key to .env
6. Start backend: `uvicorn main:app --reload --port 8000`

**Prevention:**
- Document all dependencies in requirements.txt
- Add health check script: `./scripts/check_dependencies.sh`
- Use Docker Compose to start all services together
- Add .env.example with all required variables

---

### Problem 2: Vector Search Returns No Results

**Symptom:**
- Chat queries return "No relevant documents found"
- Knowledge base appears empty
- RAG system not working

**Årsag:**
- Documents not embedded yet (vectorization not run)
- pgvector extension not installed in PostgreSQL
- Embeddings table empty (no data)
- Gemini API key invalid or expired

**Diagnosticering (Bash):**
```bash
# 1. Check pgvector extension
docker exec kv1ntos-postgres psql -U postgres -d kv1ntos \
  -c "SELECT * FROM pg_extension WHERE extname='vector';"

# 2. Check embeddings count
docker exec kv1ntos-postgres psql -U postgres -d kv1ntos \
  -c "SELECT COUNT(*) FROM embeddings;"

# 3. Test Gemini API
curl https://generativelanguage.googleapis.com/v1/models \
  -H "x-goog-api-key: $GEMINI_API_KEY"

# 4. Check backend logs
tail -f logs/backend.log | grep -i "embedding\|vector"
```

**Fix (Steps):**
1. Install pgvector: `docker exec kv1ntos-postgres psql -U postgres -d kv1ntos -c "CREATE EXTENSION IF NOT EXISTS vector;"`
2. Run embedding script: `python scripts/embed_documents.py`
3. Verify embeddings created: Check count query from above
4. Test Gemini API key in .env
5. Restart backend to load new embeddings
6. Test query: `curl http://localhost:8000/api/chat -d '{"message":"test"}'`

**Prevention:**
- Run embedding script automatically on first startup
- Add database migration for pgvector extension
- Validate Gemini API key on startup
- Log embedding creation progress
- Add health check endpoint for vector search

---

### Problem 3: Multi-Agent Orchestration Timeout

**Symptom:**
- Queries take >30 seconds then timeout
- Agent coordination fails mid-execution
- Error: "Task timeout" or "Agent not responding"

**Årsag:**
- AGNO agent factory creating too many agents
- Flock orchestrator deadlock (circular dependencies)
- Gemini API rate limit hit (429 error)
- Memory exhaustion (too many active agents)

**Diagnosticering (Bash):**
```bash
# 1. Check active agents
docker exec kv1ntos-backend curl http://localhost:8000/api/agents/active

# 2. Check memory usage
docker stats kv1ntos-backend --no-stream

# 3. Check Gemini API rate limits
grep "429" logs/backend.log | wc -l

# 4. Check agent logs
tail -50 logs/agents.log | grep -i "timeout\|deadlock\|failed"
```

**Fix (Steps):**
1. Reduce agent count: Set `MAX_AGENTS=10` in .env (was unlimited)
2. Add timeout to agent tasks: `AGENT_TIMEOUT=10` seconds
3. Implement request throttling for Gemini API (max 10 req/min)
4. Restart backend to clear stuck agents
5. Monitor memory: Keep below 2GB
6. If persistent: Disable experimental features (ODIN, Admiral) temporarily

**Prevention:**
- Set conservative agent limits (MAX_AGENTS=5 initially)
- Implement graceful degradation (fallback to single agent)
- Add circuit breaker for Gemini API
- Monitor agent lifecycle (creation, execution, cleanup)
- Implement agent pooling (reuse instead of create)
- Add metrics dashboard for agent performance

---

## CHANGELOG

| Date | Time | Description | Author |
|------|------|-------------|--------|
| 2026-01-08 | 15:10 | Added FEJLHÅNDTERING section (3 problems: Backend start, Vector search, Agent timeout) | Kv1nt |
| 2026-01-01 | 23:50 | Initial SYSTEM_ARCHITECTURE.md created with MEDIUM detail | Kv1nt |

---

**Last Updated:** 2026-01-01
**Status:** MEDIUM Detail Level Complete
**Document Type:** INTRO Documentation
