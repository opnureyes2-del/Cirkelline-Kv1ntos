# Technology Stack - cirkelline-kv1ntos

**Version:** 3.0.0 (KV1NTOS + v1.3.8 Base)
**Status:** Experimental - Untested
**Last Updated:** 2025-12-20

---

## Stack Overview

cirkelline-kv1ntos uses a modern Python/JavaScript stack with advanced AI capabilities.

```
┌─────────────────────────────────────────┐
│ FRONTEND                                │
│ Next.js 15 + React + TypeScript         │
│ TailwindCSS + Zustand                   │
│ Running on Port 3000                    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ BACKEND                                 │
│ FastAPI 0.109+ (Python 3.12+)           │
│ AGNO v2.3.4 (Multi-Agent Orchestration) │
│ Running on Port 7777                    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ AI & LLM                                │
│ Google Gemini 2.5 Flash                 │
│ AGNO Agent Framework                    │
│ pgvector (768-dim embeddings)           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ DATA LAYER                              │
│ PostgreSQL 17 + pgvector                │
│ Redis 6+ (caching)                      │
│ RabbitMQ (message queue)                │
└─────────────────────────────────────────┘
```

---

## Frontend Stack

### Core Framework
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Next.js** | 15 | React framework (App Router) |
| **React** | 19+ | UI library |
| **TypeScript** | Latest | Type safety |

### Styling & UI
| Technology | Version | Purpose |
|-----------|---------|---------|
| **TailwindCSS** | Latest | Utility-first CSS |
| **Shadcn/ui** | Latest (if used) | Component library |

### State & Logic
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Zustand** | Latest | State management (persistent) |
| **React Query** | Latest (if used) | Data fetching |
| **Axios** | Latest | HTTP client |

### Real-time Communication
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Server-Sent Events (SSE)** | Native | Streaming responses |
| **WebSocket** | Optional | Bidirectional comms |

### Build & Dev Tools
| Technology | Version | Purpose |
|-----------|---------|---------|
| **pnpm** | Latest | Package manager |
| **Webpack** | Next.js built-in | Module bundler |
| **Babel** | Next.js built-in | Transpiler |

### Key Components
```
cirkelline-ui/
├── src/
│   ├── app/
│   │   ├── page.tsx          # Login page
│   │   ├── chat/page.tsx     # Main chat interface
│   │   └── memories/page.tsx # Memories viewer
│   ├── components/
│   │   ├── ChatInput.tsx     # Message input + file upload
│   │   ├── ChatMessages.tsx  # Message display
│   │   └── Sidebar/          # Session navigation
│   ├── hooks/
│   │   ├── useAIStreamHandler.tsx  # SSE streaming
│   │   └── useSessionLoader.tsx    # Session loading
│   ├── contexts/
│   │   └── AuthContext.tsx   # JWT auth + user state
│   └── store.ts              # Zustand state
└── .env.local
```

---

## Backend Stack

### Core Framework
| Technology | Version | Purpose |
|-----------|---------|---------|
| **FastAPI** | 0.109+ | Web API framework |
| **Python** | 3.12+ | Runtime |
| **Uvicorn** | 0.27+ | ASGI server |

### Agent Orchestration
| Technology | Version | Purpose |
|-----------|---------|---------|
| **AGNO** | 2.3.4 | Multi-agent orchestration framework |
| **Agent** | AGNO built-in | Specialist agents |
| **Team** | AGNO built-in | Agent groups/teams |
| **AgentOS** | AGNO built-in | System orchestrator |

### AI & NLP
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Google Gemini** | 2.5 Flash | LLM (primary model) |
| **google-genai** | 1.52+ | Google API client |
| **pgvector** | Latest | Vector embeddings (768-dim) |

### Database & ORM
| Technology | Version | Purpose |
|-----------|---------|---------|
| **SQLAlchemy** | 2.0+ | SQL toolkit + ORM |
| **psycopg** | Latest | PostgreSQL adapter |
| **Alembic** | 1.14+ | Database migrations |

### Tools & Integrations
| Technology | Version | Purpose |
|-----------|---------|---------|
| **DuckDuckGo Search** | Latest | Web search tool |
| **Exa Search** | Latest | AI-powered search |
| **Tavily** | Latest | Web research tool |
| **pypdf** | Latest | PDF processing |
| **python-docx** | Latest | DOCX processing |
| **BeautifulSoup4** | Latest | HTML parsing |

### Authentication & Security
| Technology | Version | Purpose |
|-----------|---------|---------|
| **PyJWT** | 2.8+ | JWT token management |
| **bcrypt** | 4.1+ | Password hashing |
| **cryptography** | 43.0+ | Encryption library |

### Backend Structure
```
/home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/
├── my_os.py                  # Main backend (1,152 lines)
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Project metadata
├── .env                      # Environment variables
├── Dockerfile                # Container image
├── cirkelline/               # Package directory
│   ├── __init__.py
│   ├── agents/               # Agent definitions
│   │   ├── specialists.py    # Specialist agents
│   │   ├── research_team.py  # Research team
│   │   └── law_team.py       # Law team
│   ├── orchestrator/         # Orchestration
│   │   └── cirkelline_team.py
│   ├── tools/                # Custom tools
│   │   ├── media.py          # Media processing
│   │   └── ...
│   ├── database/             # Database layer
│   │   └── db.py
│   ├── middleware/           # Middleware
│   │   └── middleware.py     # JWT + user isolation
│   └── routers/              # API endpoints
│       ├── auth.py
│       ├── knowledge.py
│       └── ...
└── alembic/                  # Database migrations
```

---

## Database & Infrastructure

### Primary Database
| Technology | Version | Purpose |
|-----------|---------|---------|
| **PostgreSQL** | 17 | Relational database |
| **pgvector** | Latest | Vector extension |

### Database Details
- **Host:** localhost:5532 (Docker) or RDS endpoint (AWS)
- **Database Name:** cirkelline
- **User:** cirkelline
- **Connection Pool:** SQLAlchemy connection pooling
- **Schemas:**
  - `public` - Users and auth
  - `ai` - Sessions, memories, knowledge

### Caching Layer
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Redis** | 6+ | In-memory cache |

### Redis Details
- **Port:** 6381 (local Docker)
- **Purpose:** Session caching, message buffering
- **Configuration:** Standard Redis (no cluster)

### Message Queue
| Technology | Version | Purpose |
|-----------|---------|---------|
| **RabbitMQ** | Latest | Async task queue |

### RabbitMQ Details
- **Port:** 5672 (AMQP)
- **Purpose:** Async workflow processing
- **Configuration:** Standard single-node

### Docker
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Docker Desktop** | Latest | Containerization |
| **docker-compose** | 3.8+ | Service orchestration |

### Docker Compose Services
```yaml
services:
  cirkelline-postgres:
    image: pgvector/pgvector:pg17
    ports:
      - "5532:5432"
    environment:
      POSTGRES_DB: cirkelline
      POSTGRES_USER: cirkelline
      POSTGRES_PASSWORD: cirkelline123

  redis:
    image: redis:7-alpine
    ports:
      - "6381:6379"

  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"
```

---

## AI & LLM Configuration

### Primary LLM: Google Gemini 2.5 Flash
```python
model = Gemini(id="gemini-2.5-flash")
```

**Specifications:**
- **Provider:** Google AI Studio
- **Model ID:** `gemini-2.5-flash`
- **API Key:** `GOOGLE_API_KEY` environment variable
- **Rate Limit:** 1,500 RPM (Tier 1)
- **Context Window:** 1M tokens
- **Latency:** ~500-1000ms per request

### Embeddings: Gemini Embeddings
```python
embedder = GeminiEmbedder(model_id="models/embedding-001")
```

**Specifications:**
- **Dimensions:** 768
- **Model:** Google Gemini Embeddings
- **Use Case:** Document chunking and semantic search
- **Storage:** pgvector in PostgreSQL

### Alternative Models (Available but not used)
- **OpenAI GPT-4:** Requires `OPENAI_API_KEY`
- **Anthropic Claude:** Not configured
- **Local LLMs:** Not configured

---

## Environment Variables

### Critical Variables
```bash
# Google API
GOOGLE_API_KEY=AIzaSy...          # Gemini API (Tier 1: 1500 RPM)

# Database
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline

# Authentication
JWT_SECRET_KEY=<64-char-hex>      # Generated with secrets.token_hex(32)

# Search APIs
EXA_API_KEY=<exa-key>
TAVILY_API_KEY=<tavily-key>

# Configuration
AGNO_MONITOR=true
AGNO_DEBUG=false
```

### Optional Variables
```bash
OPENAI_API_KEY=sk-placeholder     # Required by AGNO, not used
ENVIRONMENT=development           # development, staging, production
LOG_LEVEL=INFO
```

---

## Development Dependencies

```
pytest>=7.0.0              # Testing framework
pytest-asyncio>=0.21.0     # Async test support
pytest-cov>=4.0.0          # Coverage reporting
httpx>=0.25.0              # HTTP testing client
black>=23.0.0              # Code formatter
ruff>=0.1.0                # Linter
mypy>=1.0.0                # Type checker
```

---

## Version Matrix

| Component | Version | Min Required | Notes |
|-----------|---------|--------------|-------|
| Python | 3.12 | 3.11 | 3.12+ recommended |
| PostgreSQL | 17 | 14 | pgvector extension required |
| Node.js | 18+ | 16 | For Next.js frontend |
| pnpm | Latest | 7.0 | Package manager for frontend |
| Docker | Latest | 20.10 | For local development |
| AGNO | 2.3.4 | 2.1.0 | Multi-agent framework |

---

## Deployment Infrastructure (AWS)

### Production Setup (When Ready)
| Component | Type | Configuration |
|-----------|------|---------------|
| **Backend** | AWS ECS Fargate | Docker container, ALB |
| **Database** | AWS RDS | PostgreSQL 17, db.t3.medium |
| **Frontend** | Vercel | Next.js deployment |
| **Storage** | AWS S3 | Document/media storage |
| **Secrets** | AWS Secrets Manager | API keys, credentials |

### Deployment Checklist
- [ ] Docker image builds successfully
- [ ] Image includes `curl` for health checks
- [ ] Environment variables set in AWS Systems Manager
- [ ] RDS database created with pgvector
- [ ] Application tested locally first
- [ ] Pre-deployment validation complete

---

## Performance Characteristics

| Metric | Target | Actual | Notes |
|--------|--------|--------|-------|
| **API Latency** | <2s | TODO | With streaming |
| **Vector Search** | <100ms | TODO | HNSW index |
| **Concurrent Users** | 100+ | TODO | Untested |
| **Memory** | 2GB | TODO | Baseline + agents |
| **Database Connections** | 1,000 | TODO | Connection pool |

---

## Security Features

### Authentication
- JWT tokens (7-day expiration)
- bcrypt password hashing
- CORS protection
- User isolation by user_id

### Data Protection
- All queries filtered by user_id
- HTTPS for production
- Secrets in environment variables
- No credentials in code

### Monitoring
- AGNO monitoring enabled
- Request logging
- Error tracking
- Database query logging

---

## Known Issues & Limitations

- **API Keys Missing:** EXA_API_KEY, TAVILY_API_KEY not configured
- **Untested:** No production validation
- **Performance:** Single-instance only (not scaled)
- **Integration:** Projects isolated, no cross-system comms
- **KV1NTOS Features:** Experimental, not verified

---

## CHANGELOG

| Date | Time | Description | Author |
|------|------|-------------|--------|
| 2026-01-01 | 23:50 | Initial TECH_STACK.md created with MEDIUM detail | Kv1nt |

---

**Last Updated:** 2026-01-01
**Status:** MEDIUM Detail Level Complete
**Document Type:** INTRO Documentation
