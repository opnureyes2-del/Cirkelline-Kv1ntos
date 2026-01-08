# Project Overview - cirkelline-kv1ntos

**Project Name:** cirkelline-kv1ntos
**Type:** Multi-Agent AI Orchestration System (Enhanced)
**Owner:** Rasmus (experimental work)
**Status:** EXPERIMENTAL - Untested
**Version:** 3.0.0 (KV1NTOS + Cirkelline v1.3.8 base)
**Last Updated:** 2025-12-20

---

## Mission Statement

Build an advanced AI orchestration system that intelligently routes user requests to specialized AI agents through a natural conversational interface, with deep learning capabilities and autonomous optimization.

---

## What is cirkelline-kv1ntos?

### Base System: Cirkelline v1.3.8
A multi-agent AI system where users interact with one friendly assistant that secretly delegates tasks to specialists:
- Audio processing (transcription, sound ID)
- Video analysis (scene recognition)
- Image processing (OCR, descriptions)
- Document handling (PDF, DOCX)
- Web research (synthesis, analysis)
- Legal research (case law, analysis)

### Experimental Enhancement: KV1NTOS
Rasmus added a sophisticated orchestration framework adding:
- **Agent Factory** - Dynamic agent creation
- **ODIN** - Master orchestrator
- **Admiral** - Strategic governance
- **Flock Management** - Collaborative teams
- **Knowledge Graph** - Semantic relationships
- **Code Guardian** - Quality monitoring
- **NL Terminal** - Natural language control
- **Learning Rooms** - Agent training environments

---

## Key Features

### 1. Conversational Interface
- Single chat interface feels like talking to one assistant
- Behind-the-scenes delegation to specialists
- Natural language processing
- Context-aware responses
- Session persistence

### 2. Multi-Agent Architecture
```
Cirkelline (Main)
├── Specialist Agents (4)
│   ├── Audio
│   ├── Video
│   ├── Image
│   └── Document
├── Teams
│   ├── Research (Web Researcher + Analyst)
│   └── Law (Legal Researcher + Analyst)
└── Dynamic Agents
    └── Agent Factory (KV1NTOS)
```

### 3. Knowledge Management
- Vector-based semantic search
- User-private document library
- Hybrid search (semantic + keyword)
- 768-dimensional embeddings
- HNSW indexes for performance

### 4. User Isolation
- All data filtered by user_id
- Private documents per user
- Private memory per user
- Private sessions per user
- Secure by design

### 5. KV1NTOS Orchestration (Experimental)
- ODIN: Master orchestrator
- Admiral: Strategic layer
- Flock: Collaborative teams
- Continuous optimization
- Cross-agent learning
- Knowledge graphs

---

## Architecture at a Glance

```
FRONTEND (Next.js 15)
   ↓ [User message + JWT]
API Layer (FastAPI)
   ↓ [Extract user_id]
Middleware (JWT auth)
   ↓ [Filter by user_id]
Custom Endpoint
   ↓ [Apply context]
Cirkelline Orchestrator
   ↓ [Analyze intent]
Specialist/Team
   ↓ [Process]
Rewriter (Cirkelline)
   ↓ [Friendly tone]
SSE Stream → Frontend
   ↓
User sees response
```

---

## Technology Stack (Summary)

| Layer | Tech | Version |
|-------|------|---------|
| **Frontend** | Next.js 15 | Latest |
| **Language** | TypeScript | Latest |
| **Backend** | FastAPI | 0.109+ |
| **Runtime** | Python | 3.12+ |
| **Agent Framework** | AGNO | 2.3.4 |
| **LLM** | Google Gemini | 2.5 Flash |
| **Database** | PostgreSQL 17 | Latest |
| **Vectors** | pgvector | Latest |
| **Caching** | Redis | 6+ |
| **Queue** | RabbitMQ | Latest |

---

## Project Statistics

### Codebase
- **Total Lines:** 63,000+ (includes KV1NTOS)
- **Base Lines:** ~11,000 (Cirkelline v1.3.8)
- **Added Lines:** ~52,000 (KV1NTOS enhancements)
- **Python Files:** 46 (core agent system)
- **TypeScript Files:** 25+ (frontend)
- **Documentation:** 130 files (76 new from KV1NTOS)

### Database
- **Tables:** 8 (public + ai schemas)
- **Indexes:** 20+ (optimized for queries)
- **Vectors:** Up to 768-dimensional

### Performance (Target)
- **API Latency:** <2s (with streaming)
- **Vector Search:** <100ms (HNSW)
- **Concurrent Users:** 100+
- **Memory:** 2GB baseline
- **Database:** 1,000+ connections

---

## Core Components

### 1. Frontend (cirkelline-ui)
```
Next.js 15 Application
├── Chat Interface (main feature)
│   ├── Message display
│   ├── Message input
│   ├── File upload
│   └── Real-time SSE streaming
├── Session Sidebar
│   ├── New chat
│   ├── Session history
│   └── Session management
├── Memory Viewer
│   ├── User memories
│   └── Context tracking
└── Authentication
    ├── Login
    ├── Signup
    └── Profile
```

### 2. Backend (my_os.py + cirkelline/)
```
FastAPI Application
├── Authentication
│   ├── /api/auth/login
│   ├── /api/auth/signup
│   └── JWT middleware
├── Chat
│   ├── POST /teams/cirkelline/runs
│   └── SSE streaming
├── Knowledge
│   ├── /api/knowledge/upload
│   ├── /api/knowledge/search
│   └── Vector indexing
├── Memories
│   ├── /api/memories
│   ├── /api/memories/optimize
│   └── Memory archiving
└── Admin
    ├── /api/admin/users
    └── /api/admin/stats
```

### 3. Agents
```
AGNO Agents
├── Specialists (4)
│   ├── Audio Agent
│   ├── Video Agent
│   ├── Image Agent
│   └── Document Agent
├── Teams
│   ├── Research Team
│   └── Law Team
├── Orchestrators
│   ├── Cirkelline (main)
│   ├── ODIN (KV1NTOS)
│   └── Admiral (KV1NTOS)
└── Factories
    └── Agent Factory (KV1NTOS)
```

### 4. Knowledge Base
```
PostgreSQL 17 + pgvector
├── Sessions (ai.agno_sessions)
├── Memories (ai.agno_memories)
├── Documents (ai.agno_knowledge)
├── Vectors (ai.cirkelline_knowledge_vectors)
├── Workflows (ai.workflow_runs)
└── Users (public.users)
```

---

## Key Differentiators (vs Clean Version)

| Feature | Cirkelline v1.3.8 | KV1NTOS v3.0.0 |
|---------|------------------|----------------|
| **Base Agents** | 9 specialists/teams | 9 + dynamic creation |
| **Orchestration** | Single Cirkelline | Cirkelline + ODIN + Admiral |
| **Agent Management** | Static | Dynamic (Agent Factory) |
| **Flock Support** | No | Yes (collaborative groups) |
| **Learning Rooms** | No | Yes (agent training) |
| **Code Guardian** | No | Yes (quality monitoring) |
| **Knowledge Graphs** | No | Yes (semantic mapping) |
| **NL Terminal** | No | Yes (natural language control) |
| **Optimization** | Continuous (v2.7) | Continuous + Predictive |
| **Cross-Agent Learning** | No | Yes (v2.9.0) |
| **Code Lines** | 11k | 63k |
| **Documentation** | 54 files | 130 files |
| **Status** | Production | Experimental |

---

## Development Timeline

### Phase 1: Base Setup (Dec 16-17, 2025)
- Clean Cirkelline v1.3.8 from production
- Set up development environment
- Configure Docker services

### Phase 2: KV1NTOS Core (Dec 16-19, 2025)
- 52,000 lines of code added
- Agent Factory implementation
- Flock Orchestrator
- ODIN Master orchestrator
- 79 commits total

### Phase 3: Reorganization (Dec 20, 2025)
- Ivo took over
- Folder structure reorganization
- Security cleanup (API keys, credentials)
- Documentation updates

### Phase 4: Current Status (Dec 20-Jan 1)
- INTRO documentation framework created
- System ready for testing
- Waiting for verification

---

## Current Status

### What Works (Base System)
- Cirkelline v1.3.8 core functionality
- Agent delegation
- Session management
- Document upload
- JWT authentication
- Memory management

### What's Experimental (KV1NTOS)
- Agent Factory - **UNTESTED**
- ODIN Orchestrator - **UNTESTED**
- Flock Management - **UNTESTED**
- Learning Rooms - **UNTESTED**
- Code Guardian - **UNTESTED**
- NL Terminal - **UNTESTED**
- Knowledge Graphs - **UNTESTED**

### What's Unknown
- Overall system stability
- Performance at scale
- Feature interactions
- Production readiness

---

## Known Issues & Limitations

### Experimental Features
- No unit tests written
- No integration tests run
- No production validation
- Untested performance
- Unknown failure modes

### Design Limitations
- Single-instance only (no clustering)
- Stateless agents (no persistence)
- Projects isolated (no integration)
- No cross-system authentication

### Missing Components
- EXA_API_KEY not configured
- TAVILY_API_KEY not configured
- Some external integrations incomplete

---

## Success Criteria

### Phase 1: Verification (Current)
- [ ] System starts without errors
- [ ] Database migrations complete
- [ ] Basic authentication works
- [ ] Chat interface loads
- [ ] Can send messages

### Phase 2: Feature Testing
- [ ] Specialist agents respond
- [ ] Document upload works
- [ ] Vector search returns results
- [ ] Sessions persist
- [ ] Memory system functions

### Phase 3: KV1NTOS Testing
- [ ] Agent Factory creates agents
- [ ] ODIN coordinates tasks
- [ ] Flock management works
- [ ] Learning rooms function
- [ ] Code Guardian monitors

### Phase 4: Production (Future)
- [ ] All tests pass
- [ ] Performance benchmarks met
- [ ] Security audit passed
- [ ] Documentation complete
- [ ] Ready for deployment

---

## Development Guide

### For Developers
1. Read CLAUDE.md for context
2. Check 15_DEVELOPMENT_ENVIRONMENT.md for setup
3. Review 10_SYSTEM_ARCHITECTURE.md for design
4. Study 11_DATABASE_SCHEMA.md for data model
5. Explore my_os.py for backend logic
6. Check cirkelline-ui/src/ for frontend

### For Designers
1. Review chat interface in cirkelline-ui/src/app/chat/
2. Check components in cirkelline-ui/src/components/
3. Explore TailwindCSS configuration
4. Review Next.js routing structure

### For DevOps
1. Study docker-compose.yml
2. Review 15_DOCKER_CONFIGURATION.md
3. Check deployment files in aws_deployment/
4. Review CHANGELOG for version history

---

## Next Steps

### Immediate (Week 1-2)
- [ ] Verify system starts correctly
- [ ] Test basic chat functionality
- [ ] Confirm database works
- [ ] Run health checks

### Short Term (Week 3-4)
- [ ] Test all specialist agents
- [ ] Verify document upload
- [ ] Test vector search
- [ ] Validate memory system

### Medium Term (Month 2-3)
- [ ] Test KV1NTOS features
- [ ] Performance profiling
- [ ] Security audit
- [ ] User acceptance testing

### Long Term (Month 4+)
- [ ] Production deployment
- [ ] Integration with other systems
- [ ] Scaling infrastructure
- [ ] Continuous optimization

---

## Resources

### Documentation
- `CLAUDE.md` - Project instructions
- `README.md` - Basic overview
- `INTRO/` - Complete documentation structure
- `docs/` - Central documentation

### Code
- `my_os.py` - Main backend server
- `cirkelline/` - Python package
- `cirkelline-ui/` - Frontend app

### External References
- AGNO Documentation: docs.agno.com
- FastAPI: fastapi.tiangolo.com
- Next.js: nextjs.org
- PostgreSQL: postgresql.org

---

## CHANGELOG

| Date | Time | Description | Author |
|------|------|-------------|--------|
| 2026-01-01 | 23:50 | Initial PROJECT_OVERVIEW.md created with MEDIUM detail | Kv1nt |

---

**Last Updated:** 2026-01-01
**Status:** MEDIUM Detail Level Complete
**Document Type:** INTRO Documentation
