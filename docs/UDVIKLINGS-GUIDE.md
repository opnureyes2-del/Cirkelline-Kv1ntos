# UDVIKLINGS-GUIDE
**Cirkelline Ecosystem | Version 1.0**

---

## 1. GRUNDREGLER (ALTID FØLG DISSE)

### 1.1 Mandatory Workflow
```
1. EXPLORE - Læs filer, research docs. Stop og vent.
2. PLAN - Foreslå specifik plan. Spørg "Skal jeg fortsætte?"
3. IMPLEMENT - Udfør ÉT skridt. Vis resultat. Vent.
4. VERIFY - Kør tests. Vis faktisk output som bevis.
```

### 1.2 Aldrig Antag
- Læs altid koden før du ændrer
- Spørg hvis noget er uklart
- Vis testoutput som bevis

---

## 2. PROJEKT STRUKTUR

### 2.1 Placering
```
/home/rasmus/Desktop/projects/
├── cirkelline-system/          # Hovedplatform
│   ├── cirkelline/             # Backend moduler
│   ├── cirkelline-ui/          # Frontend (Next.js)
│   ├── cla/                    # Desktop app (Tauri)
│   ├── ecosystems/
│   │   └── ckc-core/           # CKC moduler
│   ├── my_os.py                # Entry point (port 7777)
│   └── docs/                   # Dokumentation
├── lib-admin-main/             # CKC Admin Hub
│   ├── backend/                # FastAPI (port 7779)
│   └── frontend/               # Next.js (port 3002)
├── Cosmic-Library-main/        # Training Academy
├── Commando-Center-main/       # Meta-cognitive brain
└── Cirkelline-Consulting-main/ # Consulting website
```

### 2.2 Environment Mapper
```
/home/rasmus/Desktop/projects/
├── cirkelline-env/             # For cirkelline-system
└── ckc-core-env/               # For lib-admin
```

---

## 3. OPSTART AF SERVICES

### 3.1 Database (altid først)
```bash
docker start cirkelline-postgres
# Verificer: docker ps | grep postgres
```

### 3.2 cirkelline-system (port 7777)
```bash
cd ~/Desktop/projects/cirkelline-system
source ~/Desktop/projects/cirkelline-env/bin/activate
python my_os.py
```

### 3.3 lib-admin (port 7779)
```bash
cd ~/Desktop/projects/lib-admin-main/backend
source venv/bin/activate
python main.py
```

### 3.4 Frontend (port 3000)
```bash
cd ~/Desktop/projects/cirkelline-system/cirkelline-ui
pnpm dev
```

---

## 4. KØRSEL AF TESTS

### 4.1 lib-admin Tests
```bash
cd ~/Desktop/projects/lib-admin-main/backend
source venv/bin/activate
TESTING=true ENVIRONMENT=testing python -m pytest tests/ -v
```

### 4.2 cirkelline-system Tests
```bash
cd ~/Desktop/projects/cirkelline-system
source ~/Desktop/projects/cirkelline-env/bin/activate
pytest tests/test_cirkelline.py -v
```

### 4.3 CLA (Rust) Tests
```bash
cd ~/Desktop/projects/cirkelline-system/cla/src-tauri
cargo test
```

---

## 5. TILFØJ NY AGENT

### 5.1 I cirkelline-system
```python
# 1. Opret fil: cirkelline/agents/din_agent.py
from agno import Agent, Gemini
from cirkelline.database import db

din_agent = Agent(
    name="Din Agent",
    role="Hvad den gør",
    model=Gemini(id="gemini-2.5-flash"),
    instructions=[...],
    markdown=True,
    db=db
)

# 2. Tilføj til team: cirkelline/orchestrator/cirkelline_team.py
from cirkelline.agents.din_agent import din_agent
# Tilføj til members list

# 3. Registrer med AgentOS: my_os.py
from cirkelline.agents.din_agent import din_agent
# Tilføj til agents list i AgentOS()
```

### 5.2 I lib-admin
```python
# 1. Opret mappe: agents/din_agent/
# 2. Opret routes.py med FastAPI router
# 3. Registrer i main.py
```

---

## 6. TILFØJ NY ENDPOINT

### 6.1 cirkelline-system
```python
# 1. Opret router: cirkelline/endpoints/din_feature.py
from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/api/din/endpoint")
async def din_endpoint(request: Request):
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401)
    return {"success": True}

# 2. Registrer i my_os.py
from cirkelline.endpoints.din_feature import router as din_router
app.include_router(din_router)
```

---

## 7. DATABASE ÆNDRINGER

### 7.1 cirkelline-system
```bash
# Migrations er i migrations/ mappen
# Kør manuelt via psql eller migration tool
```

### 7.2 lib-admin
```bash
# Brug Alembic
cd ~/Desktop/projects/lib-admin-main/backend
alembic revision --autogenerate -m "beskrivelse"
alembic upgrade head
```

---

## 8. DEPLOYMENT

### 8.1 Build Docker Image
```bash
cd ~/Desktop/projects/cirkelline-system

# Build (husk at opdatere version)
docker build --platform linux/amd64 -f Dockerfile \
  -t 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.X.X .
```

### 8.2 Push til ECR
```bash
aws ecr get-login-password --region eu-north-1 | \
  docker login --username AWS --password-stdin 710504360116.dkr.ecr.eu-north-1.amazonaws.com

docker push 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.X.X
```

### 8.3 Deploy til ECS
```bash
# Opdater task-definition.json med ny version
aws ecs register-task-definition \
  --cli-input-json file://aws_deployment/task-definition.json \
  --region eu-north-1

aws ecs update-service \
  --cluster cirkelline-system-cluster \
  --service cirkelline-system-backend-service \
  --task-definition cirkelline-system-backend:XX \
  --force-new-deployment \
  --region eu-north-1
```

---

## 9. DEBUGGING

### 9.1 Check logs
```bash
# Docker containers
docker logs cirkelline-postgres

# AWS logs
aws logs tail /ecs/cirkelline-system-backend --since 5m --region eu-north-1
```

### 9.2 Database inspektion
```bash
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline
\dt ai.*           # List AI tables
\dt public.*       # List public tables
```

### 9.3 API Test
```bash
# Health check
curl http://localhost:7777/health

# Login og få token
curl -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password"}'
```

---

## 10. GIT WORKFLOW

### 10.1 Commit Message Format
```
<type>: <beskrivelse>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### 10.2 Branch Navngivning
```
feature/din-feature
fix/bug-beskrivelse
docs/dokumentation-opdatering
```

---

## 11. VIGTIGE FILER

| Fil | Formål |
|-----|--------|
| `my_os.py` | cirkelline-system entry point |
| `main.py` | lib-admin entry point |
| `CLAUDE.md` | AI instruktioner |
| `requirements.txt` | Python dependencies |
| `package.json` | Node dependencies |
| `.env` | Environment variables |

---

## 12. KONTAKTER

| Rolle | Email |
|-------|-------|
| Ivo (CEO) | opnureyes2@gmail.com |
| Rasmus (CEO) | opnureyes2@gmail.com |

---

*Se også: BASELINE-2025-12-12.md, ROADMAP-2025-12-12.md, SYSTEM-MANUAL.md*
