# DAGLIG RUTINE - CIRKELLINE SYSTEM v1.3.5

**Oprettet:** 2025-12-16
**Version:** v1.3.5
**Ansvarlig:** Memory Evolution Room + Manuel

---

## AUTOMATISKE RUTINER

### Memory Evolution Room (Kører i baggrunden)

```
┌────────────────────────────────────────────────────────┐
│              AUTOMATISK SCHEDULE                        │
├────────────────────────────────────────────────────────┤
│  03:33  │  Morning Test    │  full_memory_audit        │
│  09:00  │  Morning Sync    │  Sync til SYNKRONISERING  │
│  21:21  │  Evening Test    │  optimization_check       │
│  21:21  │  Evening Sync    │  Sync til SYNKRONISERING  │
└────────────────────────────────────────────────────────┘
```

### Start Memory Evolution Room

```python
# I Python/Backend
from cirkelline.ckc.monitors import start_memory_evolution_room

# Start (kører i baggrunden)
room = await start_memory_evolution_room()

# Check status
status = room.get_status()
print(status)
```

---

## MANUELLE RUTINER

### Morgen Rutine (Start af dag)

```bash
# 1. Start Docker services (hvis ikke kører)
docker ps  # Check status
# Hvis nødvendigt:
cd ~/Desktop/projekts/projects/cirkelline-system
docker-compose up -d

# 2. Aktivér venv og start backend
source .venv/bin/activate
python my_os.py  # Port 7777

# 3. Verificer health
curl http://localhost:7777/health
```

### Test Rutine (Før commit)

```bash
# 1. Kør pytest suite
cd ~/Desktop/projekts/projects/cirkelline-system
source .venv/bin/activate
pytest tests/test_cirkelline.py -v

# 2. Check Memory Evolution Room status
python -c "
from cirkelline.ckc.monitors import get_memory_evolution_room
room = get_memory_evolution_room()
print(room.get_status())
"

# 3. Verificer CKC modules
python -c "
from cirkelline.ckc import __version__
print(f'CKC Version: {__version__}')
"
```

### Aften Rutine (21:21)

```bash
# 1. Check at Memory Evolution Room har kørt
ls -la ~/Desktop/projekts/projects/cirkelline-system/my_admin_workspace/SYNKRONISERING/

# 2. Check snapshots
ls -la ~/Desktop/projekts/projects/cirkelline-system/my_admin_workspace/SYNKRONISERING/snapshots/

# 3. Review dagens ændringer
git status
git diff --stat
```

### Ugentlig Rutine (Mandag)

```bash
# 1. Fuld test audit på alle projekter
cd ~/Desktop/projekts/projects

# cirkelline-system
cd cirkelline-system && source .venv/bin/activate && pytest -v && cd ..

# lib-admin-main
cd lib-admin-main/backend && source venv/bin/activate && pytest -v && cd ../..

# Commando-Center
cd Commando-Center-main && pytest -v && cd ..

# 2. Check for dependency updates
pip list --outdated

# 3. Opdater roadmap med status
```

---

## TJEKLISTE

### Daglig

- [ ] Docker services kører (10 containers)
- [ ] Backend kører på port 7777
- [ ] Memory Evolution Room aktiv
- [ ] Ingen kritiske fejl i logs

### Før Commit

- [ ] `pytest -v` passed
- [ ] Ingen linting fejl
- [ ] Version nummer opdateret hvis relevant
- [ ] Dokumentation opdateret

### Ugentlig

- [ ] Fuld test audit (alle projekter)
- [ ] Dependency check
- [ ] Roadmap opdateret
- [ ] Backup verificeret

---

## KOMMANDO REFERENCE

### Docker

```bash
# Start alle services
docker-compose up -d

# Check status
docker ps

# Stop alle
docker-compose down

# Logs
docker-compose logs -f [service-name]
```

### Backend

```bash
# Start
python my_os.py

# Health check
curl http://localhost:7777/health
curl http://localhost:7777/config
```

### Tests

```bash
# Alle tests
pytest -v

# Specifik test
pytest tests/test_cirkelline.py::TestBasicEndpoints -v

# Med coverage
pytest --cov=cirkelline tests/
```

### Git

```bash
# Status
git status

# Add og commit
git add .
git commit -m "beskrivelse"

# Push
git push origin main
```

---

## FEJLFINDING

### Backend starter ikke

```bash
# Check port
lsof -i :7777

# Kill process hvis optaget
kill -9 $(lsof -t -i :7777)

# Restart
python my_os.py
```

### Docker services fejler

```bash
# Check logs
docker-compose logs [service]

# Restart specifik service
docker-compose restart [service]

# Rebuild
docker-compose up -d --build
```

### Tests fejler

```bash
# Verbose output
pytest -v --tb=long

# Specifik test
pytest tests/test_file.py::test_name -v

# Check imports
python -c "from cirkelline.ckc import *"
```

---

## KONTAKT PUNKTER

| System | Port | Health |
|--------|------|--------|
| Cirkelline Backend | 7777 | `/health` |
| CLE (Commando-Center) | 8000 | `/health` |
| PostgreSQL (main) | 5532 | - |
| PostgreSQL (CKC) | 5533 | - |
| Redis | 6379 | - |
| ChromaDB | 8001 | - |
| MinIO | 9100 | - |
| Portainer | 9000 | Web UI |

---

*Oprettet: 2025-12-16*
*Version: v1.3.5*
