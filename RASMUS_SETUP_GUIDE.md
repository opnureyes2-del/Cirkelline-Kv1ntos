# 🚀 RASMUS'S LOCAL SETUP GUIDE

**Welcome! This is YOUR local development copy of cirkelline-system.**

This guide explains how to use this local copy safely, how to save your work, and when to ask Ivo for help.

---

## 🎯 UNDERSTAND YOUR SETUP

### What Is This?

This is a **LOCAL DEVELOPMENT COPY** of Cirkelline, Ivo's production AI system.

**Production (Ivo's computer):**
- Running at https://cirkelline.com
- Deployed on AWS
- Used by real users
- **DO NOT TOUCH** - managed by Ivo only

**Your Copy (this computer):**
- Local experiments on localhost:7777
- Learning and testing
- Your KV1NTOS additions (~52,000 lines)
- **SAFE TO EXPERIMENT** - won't affect production

### What You Have

**Your Projects (what you've been building):**
1. **KV1NTOS System** (~52,000 lines) - Agent Factory, ODIN, Knowledge Graph
2. **CKC Admin Hub** (port 7779/3002) - Multi-platform administration
3. **Cosmic Library** (port 7778/3001) - AI training platform
4. **Command Center** (port 8090) - Docker infrastructure

**Ivo's Original System:**
- **Cirkelline System** (port 7777) - Production AI platform
- **Consulting** (port 3000) - Booking website

### What Changed (2025-12-20)

✅ All Ivo's credentials removed (email, passwords, UUID)
✅ Your credentials in place (opnureyes2@gmail.com, new UUID)
✅ Git push blocked (can't accidentally push to production)
✅ API keys left as-is (per Ivo's instruction)

**See SECURITY_CHANGES.md for details**

---

## 🔑 YOUR CREDENTIALS

### Email
```
opnureyes2@gmail.com
```

### Password (LOCAL TESTING ONLY)
```
RASMUS_PASSWORD_HERE
```

**ACTION REQUIRED:** Replace `RASMUS_PASSWORD_HERE` with your actual test password.

**How to set your password:**

1. Choose a password (e.g., `Rasmus2024@test`)
2. Ask Ivo if there's a standard password to use
3. Or create your own for this local copy

**Where to replace it:**
- CLAUDE.md (line 157) - Test login section
- Any other files you use for testing

### User UUID (for API testing)
```
ee461076-8cbb-4626-947b-956f293cf7bf
```

This is YOUR unique user_id. Use it when:
- Testing API endpoints with curl
- Creating database records
- Running load tests

---

## 🛠️ HOW TO USE THIS LOCAL COPY

### Start Development Environment

**Prerequisites:**
- Docker Desktop running
- Python 3.12+ installed
- Node.js 18+ installed
- pnpm installed

**Terminal 1: Start Database**
```bash
docker start cirkelline-postgres
```

**Terminal 2: Start Backend**
```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-system
source .venv/bin/activate
python my_os.py
```
Wait for: `Application startup complete`
Access at: http://localhost:7777

**Terminal 3: Start Frontend (Optional)**
```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-system/cirkelline-ui
pnpm dev
```
Access at: http://localhost:3000

### Test Your Changes

**Method 1: Use the Web Interface**
1. Open http://localhost:3000
2. Login with `opnureyes2@gmail.com` / `YOUR_PASSWORD`
3. Chat with Cirkelline
4. Test your features

**Method 2: Use curl (API Testing)**

```bash
# 1. Get authentication token
curl -s -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"opnureyes2@gmail.com","password":"YOUR_PASSWORD"}' \
  -o /tmp/login.json

# Extract token
TOKEN=$(cat /tmp/login.json | jq -r '.token')

# 2. Test chat endpoint
curl -s -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Hello!" \
  -F "user_id=ee461076-8cbb-4626-947b-956f293cf7bf" \
  -F "stream=false"
```

**Method 3: Run Automated Tests**
```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-system
source .venv/bin/activate
pytest tests/test_cirkelline.py -v
```

---

## 💾 HOW TO SAVE YOUR WORK

### ✅ SAFE: Local Git Commits

```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-system

# 1. Check what changed
git status
git diff

# 2. Add files
git add .

# 3. Commit (stays local - SAFE)
git commit -m "feat: Your feature description"

# 4. View your commits
git log --oneline -10
```

**Commits are LOCAL ONLY** - they NEVER reach production.

### ✅ SAFE: Create Backup Bundle

```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-system

# Create backup file
git bundle create ~/Desktop/cirkelline-backup-2025-12-20.bundle --all

# This creates a complete backup you can restore later
```

### ✅ SAFE: Ask Ivo for Separate Repository

If you want to share your work or have proper git hosting:

**Ask Ivo to create a separate repository for your experiments:**
- Example: `rasmus-dev/cirkelline-experiments`
- You can push there safely
- Won't affect production

### ❌ BLOCKED: Push to Production

```bash
# This will be BLOCKED
git push origin main
# Shows: ❌ BLOCKED: Cannot push to production repository!

# Why? Pre-push hook prevents accidental production pushes
```

**If you need to share work:**
1. Ask Ivo to create separate dev repo
2. Or use `git bundle` to create backup files
3. Or just keep commits local and discuss with Ivo

---

## 📊 YOUR PROJECTS STATUS

Based on Ivo's analysis, here's the real state of what you've built:

### 1. KV1NTOS System (~52,000 lines)
**Status:** ⚠️ NEEDS TESTING
**What it is:** Agent orchestration with Factory, ODIN, Knowledge Graph
**What works:** Code exists, documentation detailed
**What's missing:** Testing, verification it integrates with Cirkelline
**Next steps:** Test if it actually runs, verify integration

### 2. CKC Admin Hub (Port 7779/3002)
**Status:** ⚠️ PARTIALLY WORKING
**What it is:** Multi-platform administration interface
**What works:** Backend API (~60% complete)
**What's missing:** Frontend incomplete (~40% to go), no real integration
**Next steps:** Test backend, complete frontend, build integration

### 3. Cosmic Library (Port 7778/3001)
**Status:** ⚠️ MOSTLY BUILT
**What it is:** AI agent training platform
**What works:** Training rooms, 9-agent research team (~80% done)
**What's missing:** Deployment to Cirkelline system, end-to-end flow
**Next steps:** Build deployment pipeline, test agent training

### 4. Command Center (Port 8090)
**Status:** ⚠️ INFRASTRUCTURE ONLY
**What it is:** Docker orchestration
**What works:** Docker services (PostgreSQL, Redis, Ollama, etc.)
**What's missing:** Application code on top of infrastructure
**Next steps:** Define what apps should run here

### 5. Integration Status
**Claimed (in docs):** All projects connected via SSO Gateway, shared database, webhooks
**Reality:** No actual integration code exists, 5 separate databases, no working SSO

**Ivo's assessment:**
- Can it work? YES, but needs 2-4 weeks of focused integration work
- Should you do it? Depends on goals - production stability vs modular tools
- Recommendation: Test what you built first, then decide on integration

---

## 🎓 ARCHITECTURE NOTES

### Database Reality

**What documentation says:**
- Single shared PostgreSQL on port 5532

**What actually exists:**
- CKC Admin: port 5532, database `cirkelline_admin`
- Cirkelline System: port 5533, database `ckc_brain`
- Cosmic Library: port 5534, database `cosmic_library` (BUT .env says 5532!)
- Command Center: port 5433, database `command_center`
- Consulting: Supabase AWS RDS (separate production)

**This is why integration doesn't work yet** - no shared database.

### Authentication Reality

**What documentation says:**
- SSO Gateway on port 7779 for all platforms

**What actually exists:**
- Every project has its own separate JWT authentication
- No working SSO Gateway
- CKC, Cosmic, Cirkelline, Consulting all use independent auth

**This is another reason integration doesn't work.**

### What Ivo Thinks

From the analysis plan:

**Good things you did:**
- 🎯 Learning AI systems, experimenting with architecture
- 🎯 Built substantial code (~52k lines KV1NTOS)
- 🎯 Explored multi-project orchestration concept

**Problems:**
- ⚠️ Built on production repo without testing first
- ⚠️ No integration code despite integration docs
- ⚠️ Database architecture is broken (5 separate DBs)
- ⚠️ Configuration conflicts everywhere

**His recommendation:**
1. Fix security first (DONE - that's this guide!)
2. Test what you built (does it actually work?)
3. Choose architecture direction (integrate vs keep separate)
4. If integrating, budget 2-4 weeks to build it properly

---

## ❓ WHEN TO ASK IVO

### Always Ask Ivo For:

1. **Production deployment** - Only Ivo deploys to cirkelline.com
2. **Architecture decisions** - Should projects integrate? How?
3. **Database changes** - Unifying databases, schema changes
4. **Creating separate dev repo** - If you want to push to GitHub
5. **API key changes** - If you need your own development keys
6. **Vercel deployment** - Frontend deployment decisions

### You Can Figure Out Yourself:

1. **Local testing** - Run on localhost, test features
2. **Code experiments** - Try new ideas, commit locally
3. **Documentation reading** - CLAUDE.md, docs/ folder
4. **Bug fixes** - Fix issues you find in your local copy
5. **Feature additions** - Add new features to your local copy

### How to Ask Ivo:

**Email:** opnureyes2@gmail.com

**Template:**
```
Subject: Question about [topic]

Hi Ivo,

I'm working on [what you're doing] in my local cirkelline-system copy.

[Your question]

What I've tried:
- [Thing 1]
- [Thing 2]

What happened:
- [Result]

What should I do?

Thanks,
Rasmus
```

---

## 🔍 USEFUL COMMANDS

### Check What's Running

```bash
# Backend health
curl http://localhost:7777/health

# Database health
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT 1;"

# Frontend health (if running)
curl http://localhost:3000
```

### Database Access

```bash
# Connect to local database
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline

# List tables
\dt ai.*
\dt public.*

# Query your sessions
SELECT * FROM ai.agno_sessions WHERE user_id = 'ee461076-8cbb-4626-947b-956f293cf7bf' ORDER BY created_at DESC LIMIT 5;
```

### Git Commands

```bash
# See what you changed
git status
git diff

# See your commits
git log --oneline -20

# Create backup
git bundle create backup.bundle --all

# Commit work
git add .
git commit -m "Your message"
# (Push is blocked automatically)
```

---

## 📚 WHAT TO READ NEXT

### Essential Reading (Start Here)

1. **SECURITY_CHANGES.md** (this folder) - What was changed and why
2. **CLAUDE.md** (this folder) - Main documentation for Cirkelline
3. **docs/00-OVERVIEW.md** - Complete startup guide
4. **docs/01-ARCHITECTURE.md** - System architecture

### When You Need Help

1. **docs/02-TROUBLESHOOTING.md** - Common issues
2. **docs/07-DEVELOPMENT-GUIDE.md** - Development workflows
3. **Plan file** - `/home/rasmus/.claude/plans/clever-inventing-parnas.md` (Complete analysis of everything)

### When You Want to Deploy (Ask Ivo First!)

1. **docs/03-AWS-DEPLOYMENT.md** - AWS procedures
2. **docs/09-ENVIRONMENT-VARIABLES.md** - Environment setup

---

## ✅ CHECKLIST: Your First Day

- [ ] Read SECURITY_CHANGES.md
- [ ] Read this file (RASMUS_SETUP_GUIDE.md)
- [ ] Set your password (replace `RASMUS_PASSWORD_HERE`)
- [ ] Start Docker: `docker start cirkelline-postgres`
- [ ] Start backend: `python my_os.py`
- [ ] Test login at http://localhost:7777
- [ ] Make a small change and commit locally
- [ ] Try to push (verify it blocks)
- [ ] Read CLAUDE.md main documentation
- [ ] Ask Ivo any questions you have

---

## 🎉 YOU'RE READY!

You now have:
- ✅ Secure local development copy
- ✅ Your own credentials
- ✅ Protection from accidental production pushes
- ✅ Understanding of what you've built
- ✅ Knowledge of what works vs what needs work
- ✅ Clear guide on when to ask Ivo for help

**Next steps:**
1. Set your password
2. Test your KV1NTOS system
3. Test your other projects (CKC, Cosmic, Command Center)
4. Figure out what you want to build next
5. Ask Ivo about architecture direction

**Remember:**
- Commit locally (always safe)
- Test on localhost (always safe)
- Ask Ivo before deploying (always required)

**Have fun building! 🚀**

---

**Created:** 2025-12-20
**Maintained by:** Ivo (via Claude)
**For:** Rasmus's local development learning
**Questions:** opnureyes2@gmail.com (Ivo)
