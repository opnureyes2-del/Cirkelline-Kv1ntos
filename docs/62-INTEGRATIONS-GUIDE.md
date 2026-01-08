# CIRKELLINE INTEGRATIONS GUIDE

**Dato:** 2025-12-18
**Version:** v1.0.0
**Status:** KOMPLET

---

## OVERBLIK

Denne guide dokumenterer alle integrationspunkter mellem Cirkelline økosystemets komponenter.

---

## 1. DATABASE INTEGRATIONER

### 1.1 PostgreSQL Connections

| Database | Container | Port | Brugere | Formål |
|----------|-----------|------|---------|--------|
| cirkelline | cirkelline-postgres | 5532 | cirkelline-system | Hovedsystem data |
| cirkelline | cirkelline-db | 5432 | cirkelline-consulting | Consulting portal |
| cc | cc-postgres | 5433 | commando-center | Infrastructure data |
| ckc | ckc-postgres | 5533 | ckc modules | CKC state storage |

### 1.2 Connection Strings

```python
# cirkelline-system (.env)
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline

# Production (AWS RDS)
DATABASE_URL=postgresql+psycopg://user:pass@cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com:5432/cirkelline
```

### 1.3 Database Schema

**AI Schema Tables:**
```sql
ai.agno_sessions      -- Chat sessioner
ai.agno_memories      -- User memories
ai.agno_knowledge     -- Document metadata
ai.cirkelline_knowledge_vectors  -- 768-dim embeddings
```

**Public Schema Tables:**
```sql
public.users          -- Auth (hashed_password)
public.admin_profiles -- Admin data
public.google_tokens  -- Google OAuth (encrypted)
public.notion_tokens  -- Notion OAuth (encrypted)
public.tiers          -- Subscription tiers
```

---

## 2. CACHE INTEGRATIONER

### 2.1 Redis Instances

| Instance | Container | Port | Formål |
|----------|-----------|------|--------|
| cirkelline-redis | cirkelline-redis | 6379 | Session cache, rate limiting |
| cc-redis | cc-redis | 6380 | Infrastructure cache |

### 2.2 Usage Pattern

```python
# Session caching
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.setex(f"session:{session_id}", 3600, session_data)

# Rate limiting
r.incr(f"rate:{user_id}")
r.expire(f"rate:{user_id}", 60)
```

---

## 3. AI SERVICE INTEGRATIONER

### 3.1 Google Gemini

**Model:** `gemini-2.5-flash`
**Tier:** 1 (1,500 RPM)

```python
# cirkelline/agents/specialists.py
from agno import Agent, Gemini

agent = Agent(
    name="Specialist",
    model=Gemini(id="gemini-2.5-flash"),
    instructions=[...],
    markdown=True,
    db=db
)
```

### 3.2 Search Providers

| Provider | API | Formål |
|----------|-----|--------|
| DuckDuckGo | duckduckgo_search | News, current events |
| Exa | EXA_API_KEY | Semantic search |
| Tavily | TAVILY_API_KEY | Comprehensive search |

### 3.3 External APIs

```python
# Google OAuth
GOOGLE_CLIENT_ID=<client-id>
GOOGLE_CLIENT_SECRET=<client-secret>
GOOGLE_TOKEN_ENCRYPTION_KEY=<64-char-hex>

# Notion OAuth
NOTION_CLIENT_ID=<client-id>
NOTION_CLIENT_SECRET=<client-secret>
NOTION_TOKEN_ENCRYPTION_KEY=<64-char-hex>
```

---

## 4. MESSAGE QUEUE INTEGRATION

### 4.1 RabbitMQ

| Setting | Value |
|---------|-------|
| Container | ckc-rabbitmq |
| AMQP Port | 5672 |
| Management Port | 15672 |
| Default User | guest/guest |

### 4.2 Queue Structure

```
ckc.events.folder_switched     # Folder switch events
ckc.events.agent_completed     # Agent task completion
ckc.events.system_status       # Health updates
```

---

## 5. OBJECT STORAGE INTEGRATION

### 5.1 Minio (S3-Compatible)

| Setting | Value |
|---------|-------|
| Container | cc-minio |
| API Port | 9100 |
| Console Port | 9101 |
| Access Key | minioadmin |
| Secret Key | minioadmin |

### 5.2 Buckets

```
knowledge-base/     # Uploaded documents
agent-artifacts/    # Generated files
backups/            # System backups
```

---

## 6. AWS SIMULATION (LocalStack)

### 6.1 Configuration

| Setting | Value |
|---------|-------|
| Container | cirkelline-localstack |
| Gateway | localhost:4566 |
| Services | S3, SQS, Lambda, SecretsManager |

### 6.2 Usage

```python
import boto3

# LocalStack endpoint
client = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)
```

---

## 7. FRONTEND-BACKEND INTEGRATION

### 7.1 API Endpoints

**Base URLs:**
- Development: `http://localhost:7777`
- Production: `https://api.cirkelline.com`

**Auth Flow:**
```
POST /api/auth/login    → {email, password} → {token, user}
POST /api/auth/signup   → {email, password, name} → {user}
POST /api/auth/logout   → Authorization: Bearer <token> → {}
```

**Chat Flow:**
```
POST /teams/cirkelline/runs → {message, user_id, stream} → SSE Stream
```

### 7.2 JWT Authentication

```typescript
// Frontend (cirkelline-ui)
const response = await fetch(`${API_URL}/teams/cirkelline/runs`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'multipart/form-data'
  },
  body: formData
});
```

### 7.3 SSE Streaming

```typescript
// Real-time response streaming
const eventSource = new EventSource(`${API_URL}/stream/${runId}`);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  appendMessage(data.content);
};
```

---

## 8. CKC INTEGRATION

### 8.1 Folder Switcher API

```python
# API Endpoints (cirkelline/ckc/api/folder_switcher.py)
GET  /api/ckc/folders              # List all folders
GET  /api/ckc/folders/current      # Current context
POST /api/ckc/folders/switch       # Switch folder
GET  /api/ckc/folders/{id}         # Folder details
```

### 8.2 Terminal Commands

```python
# CKCTerminal (cirkelline/ckc/terminal.py)
await ckc.list_folders()           # List folders
await ckc.switch_folder("mastermind")  # Switch
await ckc.folder_info("mastermind")    # Details
```

### 8.3 SuperAdmin Control

```python
# cirkelline/ckc/mastermind/super_admin_control.py
control = get_super_admin_control_system()
await control.switch_ckc_folder("mastermind", "terminal")
status = control.get_comprehensive_status()
```

---

## 9. LOCAL AGENT INTEGRATION

### 9.1 CLI Commands

```bash
# Start agent
cirkelline-agent

# Agent commands
/analyze cirkelline/ckc/folder_switcher.py
/learn
/memory
/deep
/fast
/quit
```

### 9.2 Programmatic Usage

```python
from persistent_agent import create_agent

agent = create_agent()
response = agent.chat("Hvordan fungerer CKC?")
print(response)
```

### 9.3 Memory Integration

```
~/.claude-agent/
├── persistent-agent.py
├── memories/
│   ├── cirkelline_patterns.md
│   ├── conventions.md
│   └── patterns/
│       ├── agno.md
│       ├── api.md
│       └── ckc.md
└── logs/
    └── interactions_YYYY-MM-DD.jsonl
```

---

## 10. MONITORING INTEGRATION

### 10.1 Portainer

| Setting | Value |
|---------|-------|
| Container | cc-portainer |
| URL | http://localhost:9000 |
| Purpose | Container management |

### 10.2 Adminer

| Setting | Value |
|---------|-------|
| Container | cirkelline-adminer |
| URL | http://localhost:8080 |
| Purpose | Database administration |

### 10.3 Mailhog

| Setting | Value |
|---------|-------|
| Container | cirkelline-mailhog |
| SMTP | localhost:1025 |
| Web UI | http://localhost:8025 |
| Purpose | Email testing |

---

## 11. DEPLOYMENT INTEGRATION

### 11.1 AWS ECS (Production)

```
AWS Account: 710504360116
Region: eu-north-1 (Stockholm)
Cluster: cirkelline-system-cluster
Service: cirkelline-system-backend-service
```

### 11.2 Docker Build

```bash
# Build for AWS
docker build --platform linux/amd64 -f Dockerfile \
  -t 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.3.5 .

# Push to ECR
aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin 710504360116.dkr.ecr.eu-north-1.amazonaws.com
docker push 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.3.5
```

### 11.3 Vercel (Frontend)

```
Domain: cirkelline.com
Project: cirkelline-ui
Build: pnpm build
```

---

## KONKLUSION

Cirkelline økosystemet har **15+ integrationspunkter** fordelt over:
- 4 PostgreSQL databaser
- 2 Redis instances
- 3 AI service providere
- 1 Message Queue (RabbitMQ)
- 1 Object Storage (Minio)
- 1 AWS simulation (LocalStack)
- 3 Monitoring tools

Alle integrationer er dokumenteret og testet.

---

*Dokumentation oprettet: 2025-12-18*
*System: Cirkelline v1.3.5*
