# 00-OVERVIEW - Complete Startup Guide

**Last Updated:** 2025-11-18
**Purpose:** Complete guide to starting and running Cirkelline locally
**Difficulty:** Beginner-friendly with copy-paste commands

---

## 🚀 QUICK START (TL;DR)

```bash
# Step 1: Start Database
docker start cirkelline-postgres

# Step 2: Start Backend (Terminal 1)
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py

# Step 3: Start Frontend (Terminal 2)
cd ~/Desktop/cirkelline/cirkelline-ui
pnpm dev

# Kill running server
pkill -9 python
pkill -9 node
killall -9 pnpm
fuser -k 3000/tcp

#Clean cache
rm -rf .next

# Access: http://localhost:3000

# Open a separate terminal for monitoring:
tail -f /home/eenvy/Desktop/cirkelline/backend.log | grep -E "Calendar|calendar|event|Google"

```

**That's it!** But read below for troubleshooting and details.

---

## 📋 TABLE OF CONTENTS

1. [Prerequisites](#prerequisites)
2. [First-Time Setup](#first-time-setup)
3. [Daily Development Workflow](#daily-development-workflow)
4. [Verification Steps](#verification-steps)
5. [Common Issues & Solutions](#common-issues--solutions)
6. [Project Structure](#project-structure)
7. [Environment Variables](#environment-variables)
8. [Useful Commands](#useful-commands)

---

## 🔧 PREREQUISITES

### Required Software

| Software | Version | Check Command | Install If Missing |
|----------|---------|---------------|-------------------|
| **Docker** | Latest | `docker --version` | https://docs.docker.com/get-docker/ |
| **Python** | 3.12+ | `python3 --version` | https://www.python.org/downloads/ |
| **pnpm** | 8.0+ | `pnpm --version` | `npm install -g pnpm` |
| **Node.js** | 18+ | `node --version` | https://nodejs.org/ |
| **Git** | Any | `git --version` | https://git-scm.com/ |

### Verify Prerequisites
```bash
# Run this to check everything at once
echo "Docker: $(docker --version)"
echo "Python: $(python3 --version)"
echo "pnpm: $(pnpm --version)"
echo "Node: $(node --version)"
echo "Git: $(git --version)"
```

---

## 🎯 FIRST-TIME SETUP

### Step 1: Clone Repository (If Not Done)
```bash
cd ~/Desktop
git clone <repository-url> cirkelline
cd cirkelline
```

### Step 2: Setup Database Container

**Create and start PostgreSQL with pgvector:**
```bash
# Pull the official pgvector image (PostgreSQL 17)
docker pull pgvector/pgvector:pg17

# Create and start the container
docker run -d \
  --name cirkelline-postgres \
  -e POSTGRES_USER=cirkelline \
  -e POSTGRES_PASSWORD=cirkelline123 \
  -e POSTGRES_DB=cirkelline \
  -p 5532:5432 \
  pgvector/pgvector:pg17

# Verify it's running
docker ps | grep cirkelline-postgres
```

**Expected output:**
```
463f493349ce   pgvector/pgvector:pg17   "docker-entrypoint.s…"   Up X seconds   0.0.0.0:5532->5432/tcp   cirkelline-postgres
```

**Connect to database (optional - for testing):**
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline
# Type \q to exit
```

### Step 3: Setup Backend (Python)

**Create virtual environment and install dependencies:**
```bash
cd ~/Desktop/cirkelline

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Verify installation:**
```bash
# Should show installed packages including:
# - agno
# - fastapi
# - sqlalchemy
# - psycopg
# - google-genai
pip list | grep -E "agno|fastapi|sqlalchemy"
```

### Step 4: Setup Frontend (Next.js)

**Install dependencies:**
```bash
cd ~/Desktop/cirkelline/cirkelline-ui

# Install all npm packages (this may take a few minutes)
pnpm install
```

**Verify installation:**
```bash
# Check if node_modules exists
ls -la node_modules | head

# Verify package.json scripts
pnpm run --help
```

### Step 5: Configure Environment Variables

**Backend `.env` (already exists):**
```bash
cat ~/Desktop/cirkelline/.env
```

Should contain:
```env
GOOGLE_API_KEY=AIzaSyDd7WG_7VWh9OKB6L-QU5xNEWku8G2qGvk
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline
OPENAI_API_KEY=sk-placeholder-for-knowledge-base
EXA_API_KEY=83082804-12e1-4a16-8151-c3c92eef966f
TAVILY_API_KEY=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
JWT_SECRET_KEY=c0f7a7e1773b90b74c3ba6c08f21411afe8cbc5f81ca0c0f1f4a9246b8082b68
AGNO_MONITOR=true
AGNO_DEBUG=false
```

**Frontend `.env` (already exists):**
```bash
cat ~/Desktop/cirkelline/cirkelline-ui/.env
```

Should contain:
```env
DATABASE_URL=postgresql://cirkelline:cirkelline123@localhost:5532/cirkelline
JWT_SECRET=c0f7a7e1773b90b74c3ba6c08f21411afe8cbc5f81ca0c0f1f4a9246b8082b68
NEXT_PUBLIC_API_URL=http://localhost:7777
```

**⚠️ IMPORTANT:** Never commit `.env` files to Git! They're in `.gitignore`.

### Step 6: Initialize Database Schema

**The database schema is auto-created by AgentOS on first run.**

When you first run `python my_os.py`, AgentOS will automatically create all tables:
- `ai.agno_sessions` - Chat sessions
- `ai.agno_knowledge` - Document knowledge base
- `ai.agno_memories` - Agent memories
- `users` - User accounts
- `admin_profiles` - Admin extended profiles

**To verify schema after first run:**
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "\dt ai.*"
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "\dt"
```

---

## 💼 DAILY DEVELOPMENT WORKFLOW

### Starting Everything

**You need 2 terminal windows/tabs:**

#### Terminal 1: Backend
```bash
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py
```

**Expected output:**
```
Starting AgentOS v2.1.1...
Database connected: postgresql+psycopg://cirkelline:***@localhost:5532/cirkelline
Registering agents...
✓ Audio Specialist registered
✓ Video Specialist registered
✓ Image Specialist registered
✓ Document Specialist registered
✓ Research Team registered
✓ Law Team registered
Server running on http://0.0.0.0:7777
```

**Backend will be available at:**
- API: `http://localhost:7777`
- Health check: `http://localhost:7777/health`
- Docs: `http://localhost:7777/docs`

#### Terminal 2: Frontend
```bash
cd ~/Desktop/cirkelline/cirkelline-ui
pnpm dev
```

**Expected output:**
```
> cirkelline-ui@0.1.0 dev
> next dev

  ▲ Next.js 15.0.4
  - Local:        http://localhost:3000
  - Network:      http://192.168.x.x:3000

 ✓ Starting...
 ✓ Ready in 2.5s
```

**Frontend will be available at:**
- App: `http://localhost:3000`

### Stopping Everything

**Stop Backend:**
- Press `Ctrl+C` in Terminal 1

**Stop Frontend:**
- Press `Ctrl+C` in Terminal 2

**Stop Database:**
```bash
# Only if you want to fully stop database
docker stop cirkelline-postgres
```

**⚠️ NOTE:** Usually you keep the database running. Only stop if you need to free up resources.

---

## ✅ VERIFICATION STEPS

### 1. Check Database is Running
```bash
docker ps | grep cirkelline-postgres
```
**Should show:** `Up X minutes` status

### 2. Check Database Connection
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT version();"
```
**Should show:** PostgreSQL version info

### 3. Check Backend is Running
```bash
curl http://localhost:7777/health
```
**Should return:** `{"status":"ok"}` or similar

### 4. Check Frontend is Running
```bash
curl -I http://localhost:3000
```
**Should return:** `HTTP/1.1 200 OK`

### 5. Full System Check
Open browser: `http://localhost:3000`

**You should see:**
- Cirkelline login page
- No console errors (F12 → Console)
- Can login with test credentials

**Test Login:**
- Email: `opnureyes2@gmail.com`
- Password: `cirkelline123`

---

## 🐛 COMMON ISSUES & SOLUTIONS

### Issue 1: Database Container Not Starting

**Symptom:**
```
Error: Cannot start container cirkelline-postgres: No such container
```

**Solution:**
```bash
# Container doesn't exist, create it
docker run -d \
  --name cirkelline-postgres \
  -e POSTGRES_USER=cirkelline \
  -e POSTGRES_PASSWORD=cirkelline123 \
  -e POSTGRES_DB=cirkelline \
  -p 5532:5432 \
  pgvector/pgvector:pg17
```

### Issue 2: Port 5532 Already in Use

**Symptom:**
```
Error: Bind for 0.0.0.0:5532 failed: port is already allocated
```

**Solution:**
```bash
# Find what's using port 5532
sudo lsof -i :5532

# Option 1: Stop the other service
# Option 2: Use different port (update .env files)
docker run -d \
  --name cirkelline-postgres \
  -e POSTGRES_USER=cirkelline \
  -e POSTGRES_PASSWORD=cirkelline123 \
  -e POSTGRES_DB=cirkelline \
  -p 5533:5432 \
  pgvector/pgvector:pg17

# Then update .env to use localhost:5533
```

### Issue 3: Backend - ModuleNotFoundError

**Symptom:**
```
ModuleNotFoundError: No module named 'agno'
```

**Solution:**
```bash
# Activate virtual environment first!
cd ~/Desktop/cirkelline
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify
python -c "import agno; print('Success!')"
```

### Issue 4: Backend - Database Connection Error

**Symptom:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
```bash
# 1. Check database is running
docker ps | grep cirkelline-postgres

# 2. If not running, start it
docker start cirkelline-postgres

# 3. Wait 5 seconds for startup
sleep 5

# 4. Try connecting
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT 1;"
```

### Issue 5: Frontend - pnpm Command Not Found

**Symptom:**
```
bash: pnpm: command not found
```

**Solution:**
```bash
# Install pnpm globally
npm install -g pnpm

# Verify
pnpm --version
```

### Issue 6: Frontend - Port 3000 Already in Use

**Symptom:**
```
Error: listen EADDRINUSE: address already in use :::3000
```

**Solution:**
```bash
# Find process using port 3000
lsof -i :3000

# Kill it (replace PID)
kill -9 <PID>

# Or use different port
pnpm dev --port 3001
```

### Issue 7: Frontend - Module Not Found Errors

**Symptom:**
```
Module not found: Can't resolve '@/components/...'
```

**Solution:**
```bash
cd ~/Desktop/cirkelline/cirkelline-ui

# Remove node_modules and lockfile
rm -rf node_modules pnpm-lock.yaml

# Reinstall
pnpm install

# Restart dev server
pnpm dev
```

### Issue 8: Login Not Working

**Symptom:**
- "Invalid credentials" error
- 401 Unauthorized

**Solutions:**

**A) Check backend is running:**
```bash
curl http://localhost:7777/health
```

**B) Check database column names:**
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "\d users"
```
Should show `hashed_password` (NOT `password_hash`)

**C) Verify user exists:**
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT email, user_type FROM users WHERE email='opnureyes2@gmail.com';"
```

**D) Reset password (if needed):**
```python
# In Python shell with activated venv
import bcrypt
password = "cirkelline123"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"UPDATE users SET hashed_password='{hashed}' WHERE email='opnureyes2@gmail.com';")
```

### Issue 9: Sessions Not Saving

**Symptom:**
- Chat works but sessions don't appear in sidebar
- Sessions lost on refresh

**Solution:**
Already fixed in v1.1.16! If still occurring:

```bash
# Check session table exists
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "\d ai.agno_sessions"

# Check sessions are being saved
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT session_id, user_id, created_at FROM ai.agno_sessions ORDER BY created_at DESC LIMIT 5;"
```

### Issue 10: Documents Not Uploading

**Symptom:**
- Upload button doesn't work
- "Failed to upload" error

**Solutions:**

**A) Check backend logs for errors**

**B) Verify knowledge table exists:**
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "\d ai.agno_knowledge"
```

**C) Check file permissions:**
```bash
# Backend should have write access
ls -la ~/Desktop/cirkelline/
```

---

## 📁 PROJECT STRUCTURE

```
/home/eenvy/Desktop/cirkelline/
├── my_os.py                    # Backend entry point (AgentOS)
├── requirements.txt            # Python dependencies
├── .env                        # Backend environment variables
├── .venv/                      # Python virtual environment
│
├── cirkelline-ui/              # Frontend (Next.js)
│   ├── src/
│   │   ├── app/                # Next.js pages
│   │   │   ├── page.tsx        # Login page
│   │   │   └── chat/           # Chat interface
│   │   ├── components/         # React components
│   │   │   ├── chat/           # Chat-specific components
│   │   │   └── ui/             # Reusable UI components
│   │   ├── hooks/              # Custom React hooks
│   │   │   ├── useDocuments.ts
│   │   │   └── useChatActions.ts
│   │   ├── lib/                # Utility functions
│   │   └── store/              # State management
│   ├── public/                 # Static assets
│   ├── package.json            # npm dependencies
│   ├── .env                    # Frontend environment variables
│   └── node_modules/           # Installed packages
│
├── docs/                       # Documentation
│   ├── MAIN/                   # Current documentation
│   │   ├── 00-OVERVIEW.md      # ← YOU ARE HERE
│   │   ├── 01-DATABASE-REFERENCE.md
│   │   ├── 02-TROUBLESHOOTING.md
│   │   └── 03-AWS-DEPLOYMENT.md
│   └── archive/                # Old documentation (162 files)
│
├── backups/                    # Database backups
├── Dockerfile.prod             # Production Docker image
├── task-definition.json        # AWS ECS configuration
└── README.md                   # Main project README
```

---

## 🔐 ENVIRONMENT VARIABLES

### Backend `.env` Location
`/home/eenvy/Desktop/cirkelline/.env`

### Backend Variables
```env
# Google AI (Gemini)
GOOGLE_API_KEY=AIzaSyDd7WG_7VWh9OKB6L-QU5xNEWku8G2qGvk

# Database
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline

# Placeholder for AgentOS (not actually used)
OPENAI_API_KEY=sk-placeholder-for-knowledge-base

# Search APIs
EXA_API_KEY=83082804-12e1-4a16-8151-c3c92eef966f
TAVILY_API_KEY=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

# Authentication
JWT_SECRET_KEY=c0f7a7e1773b90b74c3ba6c08f21411afe8cbc5f81ca0c0f1f4a9246b8082b68

# Monitoring
AGNO_MONITOR=true
AGNO_DEBUG=false
```

### Frontend `.env` Location
`/home/eenvy/Desktop/cirkelline/cirkelline-ui/.env`

### Frontend Variables
```env
# Database (used for direct queries in some cases)
DATABASE_URL=postgresql://cirkelline:cirkelline123@localhost:5532/cirkelline

# JWT Authentication
JWT_SECRET=c0f7a7e1773b90b74c3ba6c08f21411afe8cbc5f81ca0c0f1f4a9246b8082b68

# Backend API endpoint
NEXT_PUBLIC_API_URL=http://localhost:7777
```

**⚠️ Security Notes:**
- Never commit `.env` files
- Rotate API keys regularly
- Use different secrets for production
- Keep JWT_SECRET_KEY secure

---

## 🛠️ USEFUL COMMANDS

### Database Commands

**Connect to database:**
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline
```

**List all tables:**
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "\dt ai.*"
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "\dt"
```

**Query users:**
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT id, email, user_type FROM users;"
```

**Query sessions:**
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT session_id, user_id, created_at FROM ai.agno_sessions ORDER BY created_at DESC LIMIT 10;"
```

**Query documents:**
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT name, metadata->>'access_level' as access_level, metadata->>'uploaded_by' as uploaded_by FROM ai.agno_knowledge ORDER BY created_at DESC LIMIT 10;"
```

**Backup database:**
```bash
docker exec cirkelline-postgres pg_dump -U cirkelline cirkelline > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Restore database:**
```bash
cat backup_20251017_120000.sql | docker exec -i cirkelline-postgres psql -U cirkelline -d cirkelline
```

### Docker Commands

**Start database:**
```bash
docker start cirkelline-postgres
```

**Stop database:**
```bash
docker stop cirkelline-postgres
```

**Check status:**
```bash
docker ps | grep cirkelline
```

**View logs:**
```bash
docker logs cirkelline-postgres
docker logs -f cirkelline-postgres  # Follow logs
```

**Restart database:**
```bash
docker restart cirkelline-postgres
```

**Remove container (WARNING: deletes data!):**
```bash
docker rm -f cirkelline-postgres
```

### Backend Commands

**Activate virtual environment:**
```bash
cd ~/Desktop/cirkelline
source .venv/bin/activate
```

**Deactivate virtual environment:**
```bash
deactivate
```

**Install/update dependencies:**
```bash
pip install -r requirements.txt
```

**Run backend:**
```bash
python my_os.py
```

**Check backend is running:**
```bash
curl http://localhost:7777/health
```

**View API documentation:**
Open browser: `http://localhost:7777/docs`

### Frontend Commands

**Install dependencies:**
```bash
cd ~/Desktop/cirkelline/cirkelline-ui
pnpm install
```

**Run development server:**
```bash
pnpm dev
```

**Run on different port:**
```bash
pnpm dev --port 3001
```

**Build for production:**
```bash
pnpm build
```

**Run production build:**
```bash
pnpm start
```

**Lint code:**
```bash
pnpm lint
```

**Type check:**
```bash
pnpm type-check
```

### Git Commands

**Check status:**
```bash
git status
```

**Pull latest changes:**
```bash
git pull origin main
```

**Create new branch:**
```bash
git checkout -b feature/my-feature
```

**Commit changes:**
```bash
git add .
git commit -m "Description of changes"
```

**Push to remote:**
```bash
git push origin feature/my-feature
```

---

## 🎓 LEARNING RESOURCES

### AgentOS (Agno)
- Docs: https://docs.agno.com
- GitHub: https://github.com/agnohq/agno

### Next.js
- Docs: https://nextjs.org/docs
- Learn: https://nextjs.org/learn

### FastAPI
- Docs: https://fastapi.tiangolo.com
- Tutorial: https://fastapi.tiangolo.com/tutorial/

### PostgreSQL
- Docs: https://www.postgresql.org/docs/
- pgvector: https://github.com/pgvector/pgvector

---

## 📞 SUPPORT

### Documentation
1. **Start here:** 00-OVERVIEW.md (this file)
2. **Database issues:** 01-DATABASE-REFERENCE.md
3. **Errors/bugs:** 02-TROUBLESHOOTING.md
4. **AWS/deployment:** 03-AWS-DEPLOYMENT.md

### Debugging Steps
1. Check if database is running: `docker ps`
2. Check if backend is running: `curl http://localhost:7777/health`
3. Check if frontend is running: `curl http://localhost:3000`
4. Check browser console for errors (F12)
5. Check backend logs in terminal
6. Check database logs: `docker logs cirkelline-postgres`

### Getting Help
- Check `docs/MAIN/02-TROUBLESHOOTING.md` first
- Check recent git commits for similar issues
- Check `docs/archive/` for historical context

---

## 📚 COMPLETE DOCUMENTATION INDEX

### Core Documentation (Getting Started)

**Start Here:**
- **[00-OVERVIEW.md](./00-OVERVIEW.md)** - This file! Complete startup guide
- **[01-ARCHITECTURE.md](./01-ARCHITECTURE.md)** - System architecture, multi-agent design, request flow
- **[02-TROUBLESHOOTING.md](./02-TROUBLESHOOTING.md)** - Common issues and solutions
- **[07-DEVELOPMENT-GUIDE.md](./07-DEVELOPMENT-GUIDE.md)** - Developer handbook and workflows

### Technical Reference

**Backend & Infrastructure:**
- **[03-AWS-DEPLOYMENT.md](./03-AWS-DEPLOYMENT.md)** - AWS deployment guide and checklist
- **[04-DATABASE-REFERENCE.md](./04-DATABASE-REFERENCE.md)** - Complete database schema with exact column names
- **[05-BACKEND-REFERENCE.md](./05-BACKEND-REFERENCE.md)** - Backend API endpoints and functions
- **[09-ENVIRONMENT-VARIABLES.md](./09-ENVIRONMENT-VARIABLES.md)** - All environment variables explained
- **[11-API-ENDPOINTS.md](./11-API-ENDPOINTS.md)** - API endpoints reference

**Frontend:**
- **[06-FRONTEND-REFERENCE.md](./06-FRONTEND-REFERENCE.md)** - Frontend architecture and components

### Features & Systems

**User Features:**
- **[08-FEATURES.md](./08-FEATURES.md)** - All Cirkelline features documented
- **[12-GOOGLE-SERVICES.md](./12-GOOGLE-SERVICES.md)** - ⭐ **NEW!** Complete Google OAuth, Gmail, Calendar, Sheets integration

**Administration Features (50 Series):**
- **[50-ADMINISTRATION.md](./50-ADMINISTRATION.md)** - Admin dashboard overview (coming soon)
- **[51-FEEDBACK-SYSTEM.md](./51-FEEDBACK-SYSTEM.md)** - User feedback system (thumbs up/down, admin dashboard)
- **[52-USER-MANAGEMENT-SYSTEM.md](./52-USER-MANAGEMENT-SYSTEM.md)** - User management, online status, activity stats
- **[53-REAL-TIME-ACTIVITY-LOGGING.md](./53-REAL-TIME-ACTIVITY-LOGGING.md)** - Activity logging and audit trail
- **[54-KNOWLEDGE-DOCUMENT-SYSTEM.md](./54-KNOWLEDGE-DOCUMENT-SYSTEM.md)** - Document management system

### Project Management

**Version Control & History:**
- **[10-CHANGELOG.md](./10-CHANGELOG.md)** - Version history and changes

**Testing & Quality:**
- **[TESTING-GUIDE.md](./TESTING-GUIDE.md)** - Testing procedures and guidelines
- **[GOOGLE_INTEGRATION_TESTING_GUIDE.md](./GOOGLE_INTEGRATION_TESTING_GUIDE.md)** - Detailed Google Services testing

### Quick Navigation by Task

**"I want to..."**

- **Set up locally** → [00-OVERVIEW.md](./00-OVERVIEW.md) (this file)
- **Understand the system** → [01-ARCHITECTURE.md](./01-ARCHITECTURE.md)
- **Fix an issue** → [02-TROUBLESHOOTING.md](./02-TROUBLESHOOTING.md)
- **Deploy to AWS** → [03-AWS-DEPLOYMENT.md](./03-AWS-DEPLOYMENT.md)
- **Work with database** → [04-DATABASE-REFERENCE.md](./04-DATABASE-REFERENCE.md)
- **Add API endpoint** → [05-BACKEND-REFERENCE.md](./05-BACKEND-REFERENCE.md)
- **Modify frontend** → [06-FRONTEND-REFERENCE.md](./06-FRONTEND-REFERENCE.md)
- **Set up Google integration** → [12-GOOGLE-SERVICES.md](./12-GOOGLE-SERVICES.md) ⭐
- **Configure environment** → [09-ENVIRONMENT-VARIABLES.md](./09-ENVIRONMENT-VARIABLES.md)
- **Manage users** → [52-USER-MANAGEMENT-SYSTEM.md](./52-USER-MANAGEMENT-SYSTEM.md)
- **View activity logs** → [53-REAL-TIME-ACTIVITY-LOGGING.md](./53-REAL-TIME-ACTIVITY-LOGGING.md)
- **Handle user feedback** → [51-FEEDBACK-SYSTEM.md](./51-FEEDBACK-SYSTEM.md)

### Recent Updates (October 2025)

🆕 **NEW: Google Services Integration** (2025-10-26)
- Complete OAuth 2.0 flow with token encryption
- Gmail integration (read, search, send)
- Google Calendar integration (read, create events with timezone awareness)
- Google Sheets integration (read, write, create)
- 24 bugs fixed and documented
- See: [12-GOOGLE-SERVICES.md](./12-GOOGLE-SERVICES.md)

🆕 **Administration Features** (October 2025)
- Feedback system with admin dashboard
- User management with online status tracking
- Real-time activity logging
- Document management system
- See: [50-ADMINISTRATION.md](./50-ADMINISTRATION.md) series

### Historical Documentation

Older implementation details and progress tracking are archived in:
- `docs(archive)/` - Historical Google integration progress, research, bug fixes
- All production-relevant information has been consolidated into current docs

---

## ✅ NEXT STEPS

After completing setup:

1. **Test login** - Try logging in with test credentials
2. **Test chat** - Send a message to Cirkelline
3. **Test documents** - Upload a test document
4. **Explore Google Services** - Connect your Google account ([12-GOOGLE-SERVICES.md](./12-GOOGLE-SERVICES.md))
5. **Read architecture** - Understand the system ([01-ARCHITECTURE.md](./01-ARCHITECTURE.md))
6. **Start coding** - Make your first changes!

---

## 🎯 QUICK REFERENCE CARD

**Copy this and keep it handy:**

```bash
# START EVERYTHING (3 commands)
docker start cirkelline-postgres
cd ~/Desktop/cirkelline && source .venv/bin/activate && python my_os.py  # Terminal 1
cd ~/Desktop/cirkelline/cirkelline-ui && pnpm dev  # Terminal 2

# STOP EVERYTHING
Ctrl+C  # In both terminals
docker stop cirkelline-postgres  # Optional

# CHECK STATUS
docker ps | grep cirkelline-postgres  # Database
curl http://localhost:7777/health     # Backend
curl http://localhost:3000             # Frontend

# CONNECT TO DATABASE
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline

# MOST COMMON ISSUE
# "Backend not connecting to database"
docker start cirkelline-postgres
sleep 5
python my_os.py
```

---

**Remember:** When in doubt, restart everything! 🔄

```bash
docker restart cirkelline-postgres
# Ctrl+C both terminals, then start again
```

---

**End of 00-OVERVIEW.md** 🎉
