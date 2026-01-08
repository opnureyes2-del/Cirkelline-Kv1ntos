# ⚠️ IMPORTANT - RASMUS'S LOCAL DEVELOPMENT COPY

**🔒 Security Status:** Credentials Secured (2025-12-20)
**🚫 Git Push:** BLOCKED (production protected)
**📖 Setup Guide:** [RASMUS_SETUP_GUIDE.md](./RASMUS_SETUP_GUIDE.md)
**🔐 Changes Made:** [SECURITY_CHANGES.md](./SECURITY_CHANGES.md)

**This is a LOCAL DEVELOPMENT COPY for learning and experimentation.**

- ✅ **Safe to commit locally** (commits stay on your computer)
- ✅ **Safe to test on localhost** (port 7777)
- ❌ **CANNOT push to production** (git push is blocked)
- 📞 **Questions?** Ask Ivo (opnureyes2@gmail.com)

**Production:** https://cirkelline.com (managed by Ivo only)

---

# CIRKELLINE

**Version:** v1.1.30 | **Last Updated:** 2025-10-24 

---

# RULES: 
- Read /docs to get full context about Cirkelline
- Research official documentation (docs.agno.com) while planning or fixing
- Ask questions if anything is unclear  
- Provide completion report with test results
**When the task is done, tested and confirmed to be working**
- Update all relevant documentation files

---

## 🎯 What is Cirkelline?

**Cirkelline is a multi-agent AI orchestration system** - a personal assistant that intelligently routes tasks to specialist AI agents through a conversational interface.

**Core Concept:** One friendly interface (Cirkelline) that delegates to specialist agents (Audio, Video, Image, Document, Research, Legal) without the user knowing. It feels like talking to one smart assistant, but behind the scenes, work is orchestrated across multiple specialized AI models.

**Production Status:** ✅ Deployed on AWS (backend) + Vercel (frontend) at `https://cirkelline.com`

---

## 🏗️ Technology Stack

### Backend (Python)
- **Framework:** AgentOS (AGNO) v2.1.1 - Multi-agent orchestration
- **API:** FastAPI - Web framework
- **AI Model:** Google Gemini 2.5 Flash (Tier 1: 1,500 RPM)
- **Database:** PostgreSQL 17 with pgvector extension
- **Vector Search:** HNSW + BM25 hybrid search (768-dim embeddings)
- **Auth:** JWT tokens (7-day expiration)

### Frontend (Next.js)
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **State:** Zustand (persistent)
- **Styling:** TailwindCSS
- **Real-time:** Server-Sent Events (SSE)

### Infrastructure
- **Production:** AWS ECS Fargate + RDS + ALB
- **Database:** PostgreSQL 16.10 on RDS (20GB, db.t3.medium)
- **Secrets:** AWS Secrets Manager
- **Frontend:** Vercel

---

## 📐 System Architecture

### Multi-Agent Hierarchy
```
Cirkelline (Main Orchestrator)
│
├── Specialist Agents
│   ├── Audio Specialist (transcription, sound ID)
│   ├── Video Specialist (scene analysis)
│   ├── Image Specialist (OCR, description)
│   └── Document Specialist (PDF, DOCX processing)
│
└── Specialist Teams
    ├── Research Team
    │   ├── Web Researcher (searches)
    │   └── Research Analyst (synthesizes)
    └── Law Team
        ├── Legal Researcher (finds sources)
        └── Legal Analyst (provides analysis)
```

### Request Flow
```
User Message
    ↓
Frontend (React/Next.js)
    ↓ [POST /teams/cirkelline/runs + JWT]
Backend (FastAPI)
    ↓ [JWT Middleware extracts user_id]
Custom Endpoint
    ↓ [Applies knowledge filters by user_id]
Cirkelline Orchestrator
    ↓ [Analyzes intent & routes to specialists]
Specialist Agent/Team
    ↓ [Processes & returns result]
Cirkelline
    ↓ [Rewrites in friendly, conversational tone]
SSE Stream → Frontend → User
```

### Key Design Principles
1. **User Isolation:** All data filtered by `user_id` (sessions, memories, documents)
2. **Conversational Interface:** User never knows about internal agent delegation
3. **Private Knowledge:** Each user has their own searchable document library
4. **Session Persistence:** All conversations saved and retrievable
5. **Emotional Intelligence:** Enhanced memory captures user preferences, context, and emotional state

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Python 3.12+
- Node.js 18+
- pnpm

### Local Setup (3 Steps)

```bash
# 1. Start Database
docker start cirkelline-postgres
# If doesn't exist: see docs/00-OVERVIEW.md

# 2. Start Backend (Terminal 1)
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py
# Runs on http://localhost:7777

# 3. Start Frontend (Terminal 2)
cd ~/Desktop/cirkelline/cirkelline-ui
pnpm dev
# Runs on http://localhost:3000
```

**Test Login:** `opnureyes2@gmail.com` / `cirkelline123`

---

## 🔑 Critical Concepts

### 1. User Isolation
**EVERYTHING is filtered by `user_id`:**
- Sessions: `WHERE user_id = 'current-user'`
- Memories: `WHERE user_id = 'current-user'`  
- Documents: `WHERE metadata->>'user_id' = 'current-user'`

**Why:** Multiple users can use the system without seeing each other's data.

### 2. Session Management
- **New Chat:** Frontend sends empty `session_id` → Backend generates UUID
- **Existing Chat:** Frontend sends existing `session_id` → Backend loads from DB
- **Storage:** [`ai.agno_sessions`](./docs/04-DATABASE-REFERENCE.md) table with `user_id` index
- **Critical Fix (v1.1.16):** Backend MUST generate UUID, not pass `None` to AGNO

### 3. Private Knowledge Base
**Upload Flow:**
```
User uploads PDF
    ↓
Frontend: POST /api/knowledge/upload (with JWT)
    ↓
Backend: Extract user_id, create metadata
    ↓
AGNO: Chunk document → Generate embeddings → Store with metadata
    ↓
Vector DB: 768-dim Gemini embeddings in ai.cirkelline_knowledge_vectors
```

**Search:** Hybrid (semantic + keyword) filtered by `user_id` in metadata

### 4. Admin Profiles
- **Admins:** `opnureyes2@gmail.com` (Ivo), `opnureyes2@gmail.com` (Rasmus)
- **Storage:** [`admin_profiles`](./docs/04-DATABASE-REFERENCE.md) table (name, role, context, preferences)
- **Usage:** Injected into JWT → Passed as dependencies → Agent adapts behavior
- **Note:** Admins get same warm tone, just with technical awareness

### 5. Enhanced Memory Manager (v1.1.19+)
Captures deeper insights organically:
- **Identity:** Name, role, background
- **Emotional State:** Mood, urgency, stress levels
- **Preferences:** Communication style, learning preferences
- **Goals:** Short-term needs, long-term objectives
- **Patterns:** Recurring topics, successful approaches

---

## 📁 Critical File Locations

### Backend
```
/home/eenvy/Desktop/cirkelline/
├── my_os.py                    # MAIN BACKEND (2097 lines)
│   ├── Lines 97-172:   Document metadata functions
│   ├── Lines 251-356:  Specialist agents
│   ├── Lines 462-570:  Teams (Research, Law)
│   ├── Lines 659-926:  Cirkelline orchestrator
│   ├── Lines 1006-1144: Custom endpoint with knowledge filtering
│   └── Lines 1699-2044: Auth endpoints (signup, login, memories)
│
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (LOCAL)
├── Dockerfile                  # 🔴 AWS production Docker image (MUST have curl!)
└── aws_deployment/
    └── task-definition.json    # ECS task configuration
```

### Frontend
```
/home/eenvy/Desktop/cirkelline/cirkelline-ui/
├── src/
│   ├── app/
│   │   ├── page.tsx            # Login page
│   │   ├── chat/page.tsx       # Main chat interface
│   │   └── memories/page.tsx   # Memories viewer (v1.1.20)
│   ├── components/chat/
│   │   ├── ChatInput.tsx       # Message input + file upload
│   │   ├── ChatMessages.tsx    # Message display
│   │   └── Sidebar/            # Sessions + memories navigation
│   ├── hooks/
│   │   ├── useAIStreamHandler.tsx  # SSE streaming (467 lines)
│   │   └── useSessionLoader.tsx    # Session management
│   ├── store.ts                # Zustand state (DO NOT persist endpoint!)
│   └── contexts/
│       └── AuthContext.tsx     # JWT auth + anonymous users
└── .env.local                  # Frontend env vars
```

### Database
```
PostgreSQL Database (localhost:5532 or RDS)
├── public schema
│   ├── users               # Auth (⚠️ column: hashed_password)
│   └── admin_profiles      # Admin extended data
└── ai schema
    ├── agno_sessions       # Chat sessions (user_id indexed)
    ├── agno_memories       # User memories (user_id indexed)
    ├── agno_knowledge      # Document metadata (JSONB)
    └── cirkelline_knowledge_vectors  # 768-dim embeddings (HNSW)
```

---

## 🔧 Essential Environment Variables

### Backend (`.env`)
```bash
GOOGLE_API_KEY=AIzaSy...         # Gemini API (Tier 1: 1500 RPM)
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline
JWT_SECRET_KEY=<64-char-hex>     # Generate: python3 -c "import secrets; print(secrets.token_hex(32))"
OPENAI_API_KEY=sk-placeholder    # Not used, but required by AGNO
EXA_API_KEY=<exa-key>            # Web search
TAVILY_API_KEY=<tavily-key>      # Web search
AGNO_MONITOR=true                # Enable monitoring
AGNO_DEBUG=false                 # Disable verbose logs
```

### Frontend (`.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:7777  # Backend URL
```

**🔴 CRITICAL:** Never commit `.env` files! They're in `.gitignore`.

---

## 🛠️ Common Development Workflows

### 1. Add New Agent
```python
# In my_os.py after line 356
new_agent = Agent(
    name="Your Agent Name",
    role="Brief description",
    model=Gemini(id="gemini-2.5-flash"),
    instructions=[...],  # What agent can do
    markdown=True,
    db=db
)

# Add to Cirkelline team (line 660)
cirkelline = Team(
    members=[..., new_agent],
    ...
)

# Register with AgentOS (line 1191)
agent_os = AgentOS(
    agents=[..., new_agent],
    ...
)
```

### 2. Add API Endpoint
```python
# In my_os.py after line 1401
@app.post("/api/your/endpoint")
async def your_endpoint(request: Request):
    # Extract user_id from JWT
    user_id = getattr(request.state, 'user_id', 'anonymous')
    
    # Your logic here
    result = process_data(user_id)
    
    return {"success": True, "data": result}
```

### 3. Query Database
```bash
# Connect to local DB
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline

# List tables
\dt ai.*

# Query sessions
SELECT session_id, user_id, created_at 
FROM ai.agno_sessions 
WHERE user_id = 'your-user-id' 
ORDER BY created_at DESC LIMIT 5;
```

### 4. Deploy to AWS
```bash
# 🔴 ALWAYS check docs/03-AWS-DEPLOYMENT.md FIRST!
# Critical: Docker image MUST have curl for health checks!

cd ~/Desktop/cirkelline

# Build (increment version)
docker build --platform linux/amd64 \
  -f Dockerfile \
  -t 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.1.23 .

# Push to ECR
aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin 710504360116.dkr.ecr.eu-north-1.amazonaws.com
docker push 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.1.23

# Update task definition (edit image version in aws_deployment/task-definition.json)
# Register new task
aws ecs register-task-definition --cli-input-json file://aws_deployment/task-definition.json --region eu-north-1

# Update service
aws ecs update-service \
  --cluster cirkelline-system-cluster \
  --service cirkelline-system-backend-service \
  --task-definition cirkelline-system-backend:27 \
  --force-new-deployment \
  --region eu-north-1
```

---

## ⚠️ Common Pitfalls & Solutions

### 1. Database Column Names
**Problem:** `hashed_password` vs `password_hash`
**Solution:** ALWAYS use [`hashed_password`](./docs/04-DATABASE-REFERENCE.md#publicusers) (not `password_hash`)

### 2. Sessions Not Appearing
**Problem:** AGNO reusing same session
**Solution:** Backend MUST generate UUID when `session_id` is empty (fixed in v1.1.16)

### 3. Login Failures
**Problem:** 401 Unauthorized
**Checks:**
- Backend running? `curl http://localhost:7777/config`
- Database running? `docker ps | grep cirkelline-postgres`
- Correct column name? `docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "\d users"`

### 4. AWS Deployment Failures
**Problem:** Tasks fail health checks
**Cause:** Docker image missing `curl`
**Solution:** Use `/home/eenvy/Desktop/cirkelline/Dockerfile` (has curl on line 12)

### 5. Google API Rate Limit (429)
**Problem:** Too many requests
**Cause:** Using Free tier key (10 RPM) instead of Tier 1 (1,500 RPM)
**Solution:** Update `GOOGLE_API_KEY` to Tier 1: `AIzaSyDd7WG_7VWh9OKB6L-QU5xNEWku8G2qGvk`

---

## 📖 Documentation Guidelines

### When to Update Documentation

**ALWAYS update documentation when:**
- Database schema changes
- New AWS resources created
- API endpoints added/modified
- Common bugs fixed
- Environment variables changed

### How to Update

1. Edit the relevant file in `docs/`
2. Update "Last Updated" date at top
3. Add entry to changelog if major change
4. Test the documented procedure

### Documentation Philosophy

> "Next time we need to fix something, it should be EASY to find the information!"

- **EXACT technical details** (no ambiguity)
- **Copy-paste commands** (tested and working)
- **Real examples** from actual usage
- **Cross-references** between documents

---

## 📚 Documentation Reference

### Must-Read Docs (In Order)
1. **[00-OVERVIEW.md](./docs/00-OVERVIEW.md)** - Complete startup guide (900 lines)
   - Prerequisites, setup, daily workflow
   - All commands you need to copy-paste
   
2. **[01-ARCHITECTURE.md](./docs/01-ARCHITECTURE.md)** - System architecture (913 lines)
   - Multi-agent design, request flow, session management
   
3. **[04-DATABASE-REFERENCE.md](./docs/04-DATABASE-REFERENCE.md)** - Database schema (543 lines)
   - ALL table definitions with EXACT column names
   - Connection strings, common queries

4. **[02-TROUBLESHOOTING.md](./docs/02-TROUBLESHOOTING.md)** - Common issues (732 lines)
   - Exact solutions to known problems
   - Tested and verified fixes

5. **[03-AWS-DEPLOYMENT.md](./docs/03-AWS-DEPLOYMENT.md)** - AWS guide (418 lines)
   - 🔴 Pre-deployment checklist (MANDATORY!)
   - Current infrastructure, deployment procedures

### Additional Docs
- **[05-BACKEND-REFERENCE.md](./docs/05-BACKEND-REFERENCE.md)** - API endpoints (1,341 lines)
- **[06-FRONTEND-REFERENCE.md](./docs/06-FRONTEND-REFERENCE.md)** - Frontend architecture (1,026 lines)
- **[07-DEVELOPMENT-GUIDE.md](./docs/07-DEVELOPMENT-GUIDE.md)** - Developer handbook (912 lines)
- **[08-FEATURES.md](./docs/08-FEATURES.md)** - Feature documentation (1,289 lines)
- **[09-ENVIRONMENT-VARIABLES.md](./docs/09-ENVIRONMENT-VARIABLES.md)** - Config reference (695 lines)
- **[10-CHANGELOG.md](./docs/10-CHANGELOG.md)** - Version history (690 lines)
- **[11-FEEDBACK-SYSTEM.md](./docs/11-FEEDBACK-SYSTEM.md)** - User feedback system (32KB)
  - **Complete feedback implementation** (thumbs up/down, submission, admin dashboard)
  - **Real-time notifications** with badge and preview
  - **Status workflow**: unread → seen → done
  - **Production-ready documentation**
- **[12-USER-MANAGEMENT-SYSTEM.md](./docs/12-USER-MANAGEMENT-SYSTEM.md)** - User management system
  - **Admin user management** (list, search, filter, details)
  - **Online status tracking** (15-minute window)
  - **Activity statistics** per user (sessions, memories, feedback)
  - **Complete API documentation** with examples
- **[15-STREAMING-EVENT-FILTERING.md](./docs/15-STREAMING-EVENT-FILTERING.md)** - 🔴 **CRITICAL** Streaming event filtering guide
  - **How nested teams work** (Cirkelline → Research Team)
  - **Why duplicate content appears** without proper filtering
  - **Exact filtering rules** to prevent duplicates
  - **Testing checklist** for streaming behavior

---

## 🎓 Key Technical Decisions

### Why Teams Over Individual Agents?
- **Specialization:** Each agent has one focused job
- **Better Results:** Experts in their domain
- **Clean UX:** User sees ONE response, not multiple
- **Transparent:** Coordinator explicitly delegates

### Why Session Summaries?
- **Prevents Context Overflow:** Long conversations don't break
- **Maintains Relevance:** Only important context kept
- **AGNO Feature:** `enable_session_summaries=True`

### Why Hybrid Vector Search?
- **Semantic Search:** Vector similarity finds conceptually similar content
- **Keyword Search:** BM25 finds exact matches
- **Combined:** Better retrieval accuracy than either alone

### Why JWT in Middleware?
- **Centralized:** One place handles all auth
- **Automatic:** User isolation applied automatically
- **Dependencies:** Admin profiles injected transparently

---

## 🧪 Testing Checklist

### Local Testing
```bash
# 1. Health checks
curl http://localhost:7777/config        # Backend
curl http://localhost:3000               # Frontend

# 2. Database
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT 1;"

# 3. Auth
curl -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'

# 4. Sessions
# - Click "New Chat", send message
# - Check sidebar updates immediately
# - Verify URL has ?session=<uuid>
```

### AWS Testing
```bash
# 1. Health check
curl https://api.cirkelline.com/config

# 2. Check logs
aws logs tail /ecs/cirkelline-system-backend --since 5m --region eu-north-1

# 3. Service status
aws ecs describe-services \
  --cluster cirkelline-system-cluster \
  --services cirkelline-system-backend-service \
  --region eu-north-1
```

---

## 🚨 Emergency Contacts & Resources

### Important URLs
- **Production:** https://cirkelline.com
- **Backend API:** https://api.cirkelline.com
- **GitHub:** (repository URL)
- **AWS Console:** https://console.aws.amazon.com (eu-north-1)

### Key People
- **Ivo** (CEO & Creator): opnureyes2@gmail.com
- **Rasmus** (CEO & Co-founder): opnureyes2@gmail.com

### Infrastructure Access
- **AWS Account:** 710504360116
- **AWS Region:** eu-north-1 (Stockholm)
- **IAM User:** eenvy
- **Database:** `cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com`

---

## ✅ Quick Health Check

Run this to verify your environment:
```bash
#!/bin/bash
echo "🔍 CIRKELLINE HEALTH CHECK"
echo "=========================="

# Backend
curl -s http://localhost:7777/config > /dev/null && echo "✅ Backend running" || echo "❌ Backend DOWN"

# Database
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT 1;" > /dev/null 2>&1 && echo "✅ Database running" || echo "❌ Database DOWN"

# pgvector
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline -c "\dx vector" 2>&1 | grep -q "0\." && echo "✅ pgvector installed" || echo "❌ pgvector MISSING"

# Frontend
curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend running" || echo "❌ Frontend DOWN"

# API Key
[[ ! -z "$GOOGLE_API_KEY" ]] && echo "✅ Google API key set" || echo "❌ API key MISSING"

echo "=========================="
```

---

## 🤝 Team

### Admins
- **Ivo** (opnureyes2@gmail.com) - CEO & Creator
- **Rasmus** (opnureyes2@gmail.com) - CEO & Creator

### Admin Profiles
Admin users have extended profiles stored in `admin_profiles` table:
- Name, Role
- Personal Context (for AI agents)
- Preferences (communication style)
- Custom Instructions (how agents should respond)

---

## 📈 Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.1.16 | 2025-10-12 | Session fix, API key update, AWS deployment |
| v1.1.15 | 2025-10-11 | Previous version |
| ... | | (See git history) |

---

## 💡 Tips

### For Ivo & Rasmus
- **Before deploying:** Check AWS-DEPLOYMENT.md
- **When debugging:** Check TROUBLESHOOTING.md first
- **Database work:** Always reference DATABASE-REFERENCE.md
- **New features:** Update documentation immediately

### For Claude (AI Assistant)
- **Always check docs first** before making assumptions
- **Use EXACT column/table names** from DATABASE-REFERENCE.md
- **Document new issues** in TROUBLESHOOTING.md
- **Update version numbers** after deployments

---

## 📞 Support

**Documentation Issues:**
- Check `docs` for latest information
- Check `docs(archive)` for historical context

**Technical Issues:**
- Start with TROUBLESHOOTING.md
- Check CloudWatch logs (AWS)
- Check `backend.log` (localhost)

---

**Remember:** When in doubt, read the docs! That's why we created them! 🎉

---

## 🎯 Next Steps

1. **Read [00-OVERVIEW.md](./docs/00-OVERVIEW.md)** - Get the system running locally
2. **Read [01-ARCHITECTURE.md](./docs/01-ARCHITECTURE.md)** - Understand how it works
3. **Explore [`my_os.py`](./my_os.py)** - Main backend logic
4. **Make a small change** - Test the workflow
5. **Read relevant docs** - As needed for your work

**Remember:** When in doubt, check the docs! They have exact solutions to common issues.

---

**Document Status:** ✅ Complete and Ready for New Developers
**Maintained By:** Development Team
**Questions?** Check [docs/](./docs/) or ask Ivo/Rasmus