# Setup Guide - cirkelline-kv1ntos

**Project:** cirkelline-kv1ntos
**Version:** 3.0.0
**Estimated Setup Time:** 30-45 minutes
**Last Updated:** 2026-01-01

---

## Prerequisites

### System Requirements
- **OS:** macOS, Linux, or Windows (WSL2)
- **RAM:** 8GB minimum (16GB recommended)
- **Disk:** 10GB free space
- **CPU:** Quad-core or better

### Required Software

Check these are installed:
```bash
# Python 3.12+
python3 --version
# Expected: Python 3.12.x or higher

# Node.js 18+
node --version
# Expected: v18.x or higher

# pnpm (npm alternative, faster)
pnpm --version
# Expected: 7.x or higher

# Docker Desktop
docker --version
# Expected: Docker 20.10+

# Git (for cloning, optional for this project)
git --version
```

**Installation Links:**
- Python: https://python.org/downloads
- Node.js: https://nodejs.org
- Docker: https://docker.com/products/docker-desktop
- pnpm: `npm install -g pnpm`

---

## Step 1: Navigate to Project (2 min)

```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos
ls -la
# Should show: my_os.py, cirkelline-ui/, requirements.txt, etc.
```

---

## Step 2: Setup Python Environment (5 min)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate
# On Windows: .venv\Scripts\activate
# On macOS: source .venv/bin/activate

# Verify activation (should show (.venv) in terminal)
which python
# Should show path to .venv/bin/python
```

---

## Step 3: Install Python Dependencies (10 min)

```bash
# Ensure pip is latest
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
# or (if using pyproject.toml):
pip install -e .

# Verify installation
pip list | grep -E "fastapi|agno|sqlalchemy"
# Should show installed packages
```

**Expected Packages:**
- agno >= 2.3.4
- fastapi >= 0.109.0
- google-genai >= 1.52.0
- sqlalchemy >= 2.0
- pgvector
- pyjwt
- bcrypt

---

## Step 4: Create Environment File (3 min)

Create `.env` file in project root:

```bash
cat > /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/.env << 'EOF'
# Google Gemini API
GOOGLE_API_KEY=AIzaSy...

# Database
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline

# JWT Secret (generate: python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=your_generated_64_char_hex_here

# Optional APIs
EXA_API_KEY=optional
TAVILY_API_KEY=optional

# Configuration
AGNO_MONITOR=true
AGNO_DEBUG=false
ENVIRONMENT=development
LOG_LEVEL=INFO
EOF

chmod 600 .env  # Secure permissions
```

**Getting API Keys:**
- **GOOGLE_API_KEY:** https://aistudio.google.com/apikey
- **EXA_API_KEY:** https://exa.ai
- **TAVILY_API_KEY:** https://tavily.com

---

## Step 5: Generate JWT Secret (2 min)

```bash
# Generate secure JWT secret
python3 -c "import secrets; print(secrets.token_hex(32))"
# Output: abc123def456...

# Edit .env and replace JWT_SECRET_KEY value with output
```

---

## Step 6: Start Docker Services (5 min)

```bash
# Navigate to project root if not already there
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos

# Start all services in background
docker-compose up -d

# Verify all services started
docker-compose ps

# Expected output:
# NAME                   STATUS
# cirkelline-postgres    Up (healthy)
# cirkelline-redis       Up (healthy)
# cirkelline-rabbitmq    Up (healthy)
```

### Troubleshooting Docker Start
```bash
# If services fail to start, check logs
docker-compose logs cirkelline-postgres

# If ports already in use, stop existing containers
docker-compose down

# Clean and restart
docker-compose down -v
docker-compose pull
docker-compose up -d
```

---

## Step 7: Verify Database (3 min)

```bash
# Connect to PostgreSQL
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline

# Inside psql prompt:
\dt ai.*          # List ai schema tables
\dt public.*      # List public schema tables
\dx vector        # Check pgvector installed
SELECT 1;         # Test connection
\q               # Exit
```

**Expected Output:**
```
List of relations
 Schema |                Name                 | Type  | Owner
--------+-------------------------------------+-------+----------
 ai     | agno_sessions                       | table | cirkelline
 ai     | agno_memories                       | table | cirkelline
 ai     | agno_knowledge                      | table | cirkelline
 ai     | cirkelline_knowledge_vectors        | table | cirkelline
 ai     | workflow_runs                       | table | cirkelline
 public | users                               | table | cirkelline
 public | admin_profiles                      | table | cirkelline

 vector | 0.6.0 | INSTALLED
```

---

## Step 8: Start Backend Server (2 min)

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Start FastAPI server
python my_os.py

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:7777
# ✅ Stage 1: FastAPI app created at module level
# ✅ Database migrations completed (v1.3.0 workflow tables)
# INFO:     Application startup complete

# Test health endpoint (in another terminal)
curl http://localhost:7777/health
# Expected: {"status": "ok"}
```

**If Server Won't Start:**
```bash
# Check port 7777 is free
lsof -i :7777

# Check database connection
curl http://localhost:7777/config  # Should return config

# Check environment variables
echo $DATABASE_URL
echo $GOOGLE_API_KEY
```

---

## Step 9: Install Frontend Dependencies (5 min)

**Open new terminal window/tab:**

```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/cirkelline-ui

# Install dependencies with pnpm
pnpm install

# Expected output:
# Packages in global cache were used, linking them to node_modules
# ...
# Dependencies resolved in 15.23 seconds
# Done in 15.34 seconds
```

---

## Step 10: Create Frontend Environment File (1 min)

```bash
cat > /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/cirkelline-ui/.env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:7777
EOF
```

---

## Step 11: Start Frontend Development Server (2 min)

```bash
# In the cirkelline-ui directory
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/cirkelline-ui

# Start Next.js dev server
pnpm dev

# Expected output:
# ▲ Next.js 15.1.0
# - Local:        http://localhost:3000
# - Environments: .env.local
#
# Ready in 2.5s
```

---

## Step 12: Verify Frontend (1 min)

Open browser and navigate to:
```
http://localhost:3000
```

**Expected:** Login page with email/password fields

---

## Complete Setup Verification

All systems ready when all pass:

```bash
# Terminal 1 - Backend should show:
✅ FastAPI on http://localhost:7777
✅ Uvicorn running
✅ Migrations completed

# Terminal 2 - Frontend should show:
✅ Next.js on http://localhost:3000
✅ Ready in X seconds

# Terminal 3 - Verify all endpoints:
curl http://localhost:7777/health          # {"status": "ok"}
curl http://localhost:7777/config          # Configuration JSON
curl http://localhost:3000                 # HTML response (login page)

# Terminal 4 - Check Docker:
docker-compose ps                          # All containers Up
```

---

## Quick Test

### Create Test User
```bash
curl -X POST http://localhost:7777/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@test.com",
    "password":"test123"
  }'
# Expected: {"success": true, "user_id": "..."}
```

### Login
```bash
curl -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@test.com",
    "password":"test123"
  }'
# Expected: {"access_token": "...", "token_type": "bearer"}
```

### Send Chat Message
```bash
# Replace TOKEN with JWT from login
TOKEN="your_jwt_token_here"

curl -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message":"Hello Cirkelline",
    "session_id":null
  }'
# Expected: SSE stream with response
```

---

## Daily Startup Routine

After initial setup, daily startup is simple:

```bash
# Terminal 1: Docker services (run once or when needed)
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos
docker-compose up -d

# Terminal 2: Backend
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos
source .venv/bin/activate
python my_os.py

# Terminal 3: Frontend
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/cirkelline-ui
pnpm dev

# Terminal 4: Access application
open http://localhost:3000
```

---

## Useful Commands

### Check Status
```bash
# Docker containers
docker-compose ps

# Backend process
curl http://localhost:7777/health

# Frontend
curl http://localhost:3000 --silent | head -20
```

### View Logs
```bash
# Backend logs (from running terminal)
# Already showing in terminal running `python my_os.py`

# Frontend logs (from running terminal)
# Already showing in terminal running `pnpm dev`

# Docker logs
docker-compose logs postgres
docker-compose logs redis
docker-compose logs rabbitmq

# Follow logs (live)
docker-compose logs -f postgres
```

### Stop Services
```bash
# Stop frontend (Ctrl+C in pnpm dev terminal)

# Stop backend (Ctrl+C in python terminal)

# Stop Docker services
docker-compose down

# Keep Docker data
docker-compose down    # Data persists in volumes
```

### Reset Everything (Dangerous!)
```bash
# Stop all services
docker-compose down -v  # -v removes volumes (DELETES DATA!)

# Remove virtual environment
rm -rf .venv

# Start fresh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker-compose up -d
python my_os.py
```

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :7777    # Backend
lsof -i :3000    # Frontend
lsof -i :5532    # PostgreSQL

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Database Connection Error
```bash
# Verify Docker container is running
docker ps | grep postgres

# Check connection credentials
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline

# Check DATABASE_URL in .env
echo $DATABASE_URL
```

### Frontend Won't Load
```bash
# Clear node modules
cd cirkelline-ui
rm -rf node_modules pnpm-lock.yaml
pnpm install
pnpm dev
```

### API Key Issues
```bash
# Verify API key is set
echo $GOOGLE_API_KEY

# Check key in .env file
cat .env | grep GOOGLE

# Get new key from https://aistudio.google.com/apikey
```

---

## What to Do Next

After successful setup:

1. **Read Documentation:**
   - Read `CLAUDE.md` for project context
   - Read `10_ARKITEKTUR/10_SYSTEM_ARCHITECTURE.md` for design

2. **Test Basic Features:**
   - Create user account in web UI
   - Send test message to Cirkelline
   - Upload test document
   - Search documents

3. **Review Code:**
   - Study `my_os.py` (main backend)
   - Review agent definitions in `cirkelline/agents/`
   - Check API routes in `cirkelline/routers/`

4. **Run Tests:**
   - Follow test plan in `30_ACTIVE_TASKS.md`
   - Document any issues found
   - Report results to Rasmus/Ivo

---

## CHANGELOG

| Date | Time | Description | Author |
|------|------|-------------|--------|
| 2026-01-01 | 23:50 | Initial SETUP_GUIDE.md created with MEDIUM detail | Kv1nt |

---

**Last Updated:** 2026-01-01
**Status:** MEDIUM Detail Level Complete
**Document Type:** INTRO Documentation
