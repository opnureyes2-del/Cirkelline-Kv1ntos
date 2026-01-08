# MILJØER - INDEX
**Dato:** 2025-12-28
**Total:** 6 projekter med miljø-konfiguration
**Version:** v2.5.0

---

## OVERSIGT

| Projekt | Port | Database Port | Status | Miljø Fil |
|---------|------|---------------|--------|-----------|
| Consulting | 3000 | 5435 | LIVE (Vercel) | .env.local |
| lib-admin/CKC | 7779 | 5533 | Dev | backend/.env |
| Cosmic Library | 7778 | 5534 | Dev | backend/.env |
| Cirkelline System | 7777 | 5532 | AWS Live | .env |
| Commando Center | 8090 | 5433 | Dev | .env |
| Kommandør | N/A | 5535 | Dev | .env |

---

## UNDERMAPPER

| # | Mappe | Beskrivelse | Status |
|---|-------|-------------|--------|
| A | [15A_REELLE_MILJOER/](./15A_REELLE_MILJOER/15A_REELLE_MILJOER.md) | Reelle miljøvariabler | ⏳ |
| B | [15B_TEMPLATES/](./15B_TEMPLATES/15B_TEMPLATES.md) | .env templates | ⏳ |
| C | [15C_PORT_MAPPING/](./15C_PORT_MAPPING/15C_PORT_MAPPING.md) | Komplet port oversigt | ⏳ |
| D | [15D_UDVIKLINGS_STATUS/](./15D_UDVIKLINGS_STATUS/15D_UDVIKLINGS_STATUS.md) | Udviklingsstatus per projekt | ⏳ |

---

## HURTIG REFERENCE

### Database Porte
| Port | Database | Projekt |
|------|----------|---------|
| 5432 | Standard PostgreSQL | (System default) |
| 5532 | cirkelline | cirkelline-system |
| 5533 | ckc_admin | lib-admin |
| 5534 | cosmic_library | cosmic-library |
| 5435 | consulting | consulting |
| 5535 | kommandor | Kommandør-og-agenter |

### Backend Porte
| Port | Service | Framework |
|------|---------|-----------|
| 7777 | Cirkelline System | FastAPI |
| 7778 | Cosmic Library | FastAPI |
| 7779 | lib-admin (CKC) | FastAPI |
| 8090 | Commando Center | FastAPI + Docker |

### Frontend Porte
| Port | Service | Framework |
|------|---------|-----------|
| 3000 | Consulting | Next.js |
| 3001 | Cosmic Library | React |
| 3002 | lib-admin (CKC) | Next.js |

---

## LÆSERÆKKEFØLGE

1. **For miljøoversigt:** 15A_REELLE_MILJOER.md
2. **For opsætning:** 15B_TEMPLATES.md
3. **For porte:** 15C_PORT_MAPPING.md
4. **For projektstatus:** 15D_UDVIKLINGS_STATUS.md

---

## FEJLHÅNDTERING

### Problem 1: Environment Variable Ikke Sat Eller Forkert Værdi

**Symptom:** Service starter ikke, fejlmeddelelse om missing environment variable, eller service bruger forkert database/port

**Årsag:**
- .env fil mangler required variable
- Variable har forkert værdi (fx forkert database port)
- Environment variable ikke loaded (fx ved manual start uden env fil)

**Diagnosticering:**
```bash
# Check om .env fil findes
ls -la backend/.env

# Check environment variables i runtime
# For Python/FastAPI:
python -c "import os; print(os.getenv('DATABASE_URL'))"

# Check faktisk port i brug
sudo lsof -i :7777  # Check om port er i brug

# Check .env content (uden at vise secrets)
cat backend/.env | grep -v PASSWORD | grep -v SECRET
```

**Fix:**
1. Identificer missing variable fra error message
2. Check 15B_TEMPLATES for korrekt .env template
3. Tilføj missing variable til .env fil:
   ```bash
   echo "DATABASE_PORT=5532" >> backend/.env
   ```
4. Verificer værdi matcher 15C_PORT_MAPPING
5. Restart service med opdateret .env

**Prevention:**
- Brug .env.example template fra 15B_TEMPLATES
- Dokumenter alle required variables i template
- Validation script der checker required vars før start
- Environment variable checklist i startup workflow

---

### Problem 2: Port Conflict - Service Kan Ikke Starte

**Symptom:** Service fejler ved startup med "Address already in use" eller "Port 7777 is already allocated"

**Årsag:**
- Anden service allerede kører på samme port
- Gammel service ikke lukket korrekt (zombie process)
- Port mapping conflict i docker-compose
- To projekter konfigureret til samme port

**Diagnosticering:**
```bash
# Find hvad der bruger porten
sudo lsof -i :7777
sudo netstat -tulpn | grep 7777

# Check docker container ports
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Check hvilke porte der er i brug
ss -tulpn | grep LISTEN

# Check 15C_PORT_MAPPING for port allocation
grep "7777" INTRO/15_MILJOER/15C_PORT_MAPPING/15C_PORT_MAPPING.md
```

**Fix:**
1. Identificer proces på porten:
   ```bash
   sudo lsof -i :7777
   # Noter PID
   ```
2. Stop proces:
   ```bash
   kill <PID>
   # Eller hvis docker:
   docker stop <container_name>
   ```
3. Verificer port er fri:
   ```bash
   sudo lsof -i :7777  # Skal returnere intet
   ```
4. Start din service igen
5. Hvis port skal ændres permanent:
   - Opdater .env: `PORT=7780`
   - Opdater 15C_PORT_MAPPING dokumentation
   - Opdater denne fil (15_MILJOER.md) oversigt

**Prevention:**
- Brug 15C_PORT_MAPPING som single source of truth
- Tjek port availability før service start
- Graceful shutdown script der frigiver porte
- Docker compose healthcheck før port binding

---

### Problem 3: Database Connection Fejler - Forkert Miljø Config

**Symptom:** Service starter men kan ikke connecte til database: "Connection refused", "Unknown database", "Access denied"

**Årsag:**
- DATABASE_URL peger på forkert port (fx 5432 standard i stedet for projekt-specifik 5533)
- Database name forkert i .env
- Database credentials ikke matcher
- Database container ikke startet før service

**Diagnosticering:**
```bash
# Check database container kører
docker ps | grep postgres

# Check database port fra .env
cat backend/.env | grep DATABASE

# Test connection direkte
psql postgresql://user:pass@localhost:5533/ckc_admin

# Check om database findes
docker exec -it <postgres_container> psql -U postgres -l

# Check 15A_REELLE_MILJOER for korrekt config
cat INTRO/15_MILJOER/15A_REELLE_MILJOER/15A_REELLE_MILJOER.md | grep -A5 "<project_name>"
```

**Fix:**
1. Verificer database container kører:
   ```bash
   docker ps | grep postgres
   # Hvis ikke: docker start <postgres_container>
   ```
2. Verificer korrekt port fra 15C_PORT_MAPPING:
   - lib-admin bruger 5533
   - cosmic-library bruger 5534
   - cirkelline-system bruger 5532
3. Opdater .env DATABASE_URL:
   ```bash
   # Eksempel for lib-admin:
   DATABASE_URL=postgresql://username:password@localhost:5533/ckc_admin
   ```
4. Test connection:
   ```bash
   psql $DATABASE_URL -c "SELECT 1"
   ```
5. Restart service

**Prevention:**
- Environment-specific .env filer (.env.development, .env.production)
- Database startup verification i service healthcheck
- Connection pool med retry logic
- Dokumenter database config i 15A_REELLE_MILJOER per projekt

---

## ÆNDRINGSLOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2026-01-08 | 11:50 | FEJLHÅNDTERING tilføjet (3 problems: env vars, port conflicts, database connection) | Claude |
| 2025-12-28 | 21:40 | ÆNDRINGSLOG sektion tilføjet | Claude |
| 2025-12-28 | - | Miljøer index oprettet v2.5.0 | Claude |

---

*15_MILJOER.md - Opdateret 2026-01-08 11:50*
