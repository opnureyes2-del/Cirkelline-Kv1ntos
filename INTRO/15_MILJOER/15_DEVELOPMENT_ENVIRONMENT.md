# Development Environment - cirkelline-kv1ntos

**Project:** cirkelline-kv1ntos
**Setup Date:** 2025-12-20
**Tested On:** Ubuntu 20.04 LTS
**Status:** Ready for local development

---

## System Requirements

### Hardware
- **RAM:** 8GB minimum (16GB recommended)
- **Disk:** 10GB free space
- **CPU:** Quad-core or better
- **OS:** macOS, Linux, or Windows (WSL2)

### Software Prerequisites
```
✅ Required:
   - Docker Desktop 20.10+
   - Python 3.12+
   - Node.js 18+
   - pnpm 7.0+
   - Git (for version control)

✅ Optional:
   - VS Code (editor)
   - Postgres client (psql)
   - Redis CLI
   - Postman (API testing)
```

---

## Installation & Setup

### 1. Prerequisites Check

```bash
# Check Python
python3 --version
# Output: Python 3.12.x or higher

# Check Node.js
node --version
# Output: v18.x or higher

# Check pnpm
pnpm --version
# Output: 7.x or higher

# Check Docker
docker --version
# Output: Docker 20.10+

# Verify Docker is running
docker ps
# Should list running containers (may be empty)
```

### 2. Clone/Setup Project

```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
# On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# or
pip install -e .
# or
pip install agno>=2.3.4 fastapi uvicorn google-genai ...
```

### 3. Environment Configuration

**Backend (.env file):**
```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos

# Create .env file
cat > .env << 'EOF'
# Google API
GOOGLE_API_KEY=AIzaSy...

# Database
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline

# JWT Secret (generate with: python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=<your-64-char-hex-here>

# Search APIs (optional)
EXA_API_KEY=optional
TAVILY_API_KEY=optional

# Configuration
AGNO_MONITOR=true
AGNO_DEBUG=false
ENVIRONMENT=development
EOF

chmod 600 .env  # Secure file permissions
```

**Frontend (.env.local file):**
```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/cirkelline-ui

cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:7777
EOF
```

### 4. Start Docker Services

```bash
# From project root
docker-compose up -d

# Verify services
docker ps

# Check database connection
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT 1;"
# Output: 1

# Verify pgvector installed
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "\dx vector"
# Output: pgvector extension
```

### 5. Start Backend

```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos
source .venv/bin/activate

# Run main server
python my_os.py
# Expected output:
#   INFO:     Uvicorn running on http://0.0.0.0:7777
#   ✅ Stage 1: FastAPI app created
#   ✅ Database migrations completed
```

### 6. Start Frontend

```bash
# Open new terminal window
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/cirkelline-ui

pnpm install
pnpm dev
# Expected output:
#   ▲ Next.js 15.1.0
#   - Local:        http://localhost:3000
```

### 7. Verify Installation

```bash
# Backend health check
curl http://localhost:7777/health
# Expected: {"status": "ok"}

# Backend config
curl http://localhost:7777/config
# Expected: System configuration JSON

# Frontend
curl http://localhost:3000
# Expected: HTML response

# Login test
curl -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'
```

---

## Database Setup

### Initial Database Creation

```bash
# Connect to database
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline

# Inside psql prompt, verify tables exist
\dt ai.*
\dt public.*

# Check pgvector status
\dx vector

# Check indexes
\di ai.*
```

### Migrations

```bash
# Migrations run automatically on startup
# But can manually run if needed:

cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos
alembic upgrade head
```

### Test Database Queries

```bash
# Connect
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline

# Create test user
INSERT INTO public.users (email, hashed_password)
VALUES ('test@test.com', '$2b$12$...');

# Create test session
INSERT INTO ai.agno_sessions (session_id, user_id, created_at)
VALUES (uuid_generate_v4(), 'test-user-1', NOW());

# List sessions
SELECT * FROM ai.agno_sessions LIMIT 5;

# Exit
\q
```

---

## Project Structure

```
cirkelline-kv1ntos/
├── my_os.py                     # Main backend server
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project metadata
├── .env                        # Environment variables (local)
├── .gitignore
├── docker-compose.yml          # Docker services
├── Dockerfile                  # Backend image
│
├── cirkelline/                 # Python package
│   ├── __init__.py
│   ├── agents/                 # Agent definitions
│   │   ├── specialists.py
│   │   ├── research_team.py
│   │   └── law_team.py
│   ├── orchestrator/
│   ├── tools/
│   ├── database/
│   ├── middleware/
│   └── routers/
│
├── cirkelline-ui/              # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx       # Login
│   │   │   ├── chat/page.tsx  # Chat interface
│   │   │   └── memories/      # Memory pages
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── contexts/
│   │   └── store.ts
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── .env.local
│
├── alembic/                    # Database migrations
│   ├── env.py
│   ├── script.py_mako
│   └── versions/
│
├── agents/                     # Agent configuration
├── config/                     # Configuration files
├── INTRO/                      # Documentation (this folder)
└── CLAUDE.md                   # Project instructions
```

---

## Development Workflow

### Daily Startup

```bash
# Terminal 1: Backend
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos
source .venv/bin/activate
python my_os.py

# Terminal 2: Frontend
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/cirkelline-ui
pnpm dev

# Terminal 3: Utilities (optional)
# For database work
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline

# For logs
docker logs -f cirkelline-postgres
```

### Common Development Tasks

#### Add a Python dependency
```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos
source .venv/bin/activate
pip install <package-name>
pip freeze > requirements.txt  # Update requirements
```

#### Add a Node dependency
```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/cirkelline-ui
pnpm add <package-name>
```

#### Run tests
```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos
source .venv/bin/activate
pytest tests/
```

#### Check code quality
```bash
source .venv/bin/activate
black cirkelline/          # Format
ruff check cirkelline/     # Lint
mypy cirkelline/           # Type check
```

#### Database backup
```bash
# Backup
docker exec cirkelline-postgres pg_dump -U cirkelline cirkelline > cirkelline_backup.sql

# Restore
docker exec -i cirkelline-postgres psql -U cirkelline cirkelline < cirkelline_backup.sql
```

---

## Troubleshooting

### Backend Won't Start

```bash
# Check port 7777 is free
lsof -i :7777
# If occupied, kill the process:
kill -9 <PID>

# Check database connection
curl http://localhost:7777/config
# Should return system config

# Check environment variables
source .env
echo $DATABASE_URL
echo $GOOGLE_API_KEY
```

### Database Connection Issues

```bash
# Test connection
psql -h localhost -p 5532 -U cirkelline -d cirkelline -c "SELECT 1;"

# If fails, restart Docker
docker-compose restart cirkelline-postgres

# Check credentials
docker exec cirkelline-postgres env | grep POSTGRES
```

### Frontend Won't Start

```bash
# Clear node_modules and reinstall
cd cirkelline-ui
rm -rf node_modules pnpm-lock.yaml
pnpm install
pnpm dev

# Check port 3000 is free
lsof -i :3000
```

### Vector Search Not Working

```bash
# Check pgvector extension
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "\dx vector"

# If not installed, install it
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

## Performance Optimization

### Development Mode
- Hot reload enabled for both frontend and backend
- Logging set to INFO level
- Database query logging disabled by default
- No caching (always fresh data)

### Production Preparation
```bash
# Frontend build
cd cirkelline-ui
pnpm build
pnpm start

# Backend (with gunicorn for production)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker my_os:app
```

---

## VSCode Settings (Recommended)

**.vscode/settings.json:**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.python"
  },
  "[typescript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/node_modules": true,
    ".venv": true
  }
}
```

---

## CHANGELOG

| Date | Time | Description | Author |
|------|------|-------------|--------|
| 2026-01-01 | 23:50 | Initial DEVELOPMENT_ENVIRONMENT.md created with MEDIUM detail | Kv1nt |

---

**Last Updated:** 2026-01-01
**Status:** MEDIUM Detail Level Complete
**Document Type:** INTRO Documentation
