# BACKUP STRATEGI - CIRKELLINE ECOSYSTEM

**Dato:** 2025-12-17
**Version:** v1.3.5
**Formål:** Komplet backup plan for Cosmic-Library og lib-admin-main
**Agent:** Opus 4.5

---

## EXECUTIVE SUMMARY

### Projekter uden Git (Kræver Manuel Backup)

| Projekt | Total | Kritisk Kode | Regenerérbar | Backup Prioritet |
|---------|-------|--------------|--------------|------------------|
| **Cosmic-Library-main** | 9.3 GB | ~20 MB | 9.28 GB | P1 |
| **lib-admin-main** | 2.5 GB | ~60 MB | 2.44 GB | P1 |
| **TOTAL** | 11.8 GB | ~80 MB | 11.72 GB | |

**Konklusion:** Kun ~80 MB kode behøver backup. Resten kan regenereres.

---

## 1. COSMIC-LIBRARY-MAIN ANALYSE

### 1.1 Størrelse Breakdown

```
TOTAL: 9.3 GB

REGENERÉRBAR (99.8%):
├── backend/venv/           8.7 GB   pip install -r requirements.txt
├── frontend/node_modules/  570 MB   npm install
└── frontend/.next/         ~30 MB   npm run build

KRITISK KODE (0.2% = ~20 MB):
├── backend/agents/         1.6 MB   Agent konfigurationer
├── backend/services/       1.2 MB   Service logik
├── backend/api/            236 KB   API endpoints
├── backend/database/       236 KB   Database schemas
├── backend/training/       96 KB    Training konfiguration
├── backend/config/         144 KB   Konfiguration
├── frontend/app/           596 KB   Next.js pages
├── frontend/components/    16 KB    React components
├── frontend/lib/           24 KB    Utility funktioner
├── docs/                   232 KB   Dokumentation
└── Root MD filer           ~500 KB  Diverse dokumentation
```

### 1.2 .gitignore Status: ✅ KORREKT

```
Ignoreres (korrekt):
- venv/, .venv, env/
- node_modules/
- __pycache__/
- .next/
- *.log
- .env, .env.local
```

### 1.3 Backup Anbefaling

**Metode:** rsync med exclude af regenerérbare mapper

```bash
rsync -av --progress \
  --exclude 'venv/' \
  --exclude 'node_modules/' \
  --exclude '.next/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache/' \
  --exclude 'htmlcov/' \
  --exclude '*.log' \
  Cosmic-Library-main/ \
  /backup/cosmic-library/
```

**Estimeret backup størrelse:** ~20-30 MB

---

## 2. LIB-ADMIN-MAIN ANALYSE

### 2.1 Størrelse Breakdown

```
TOTAL: 2.5 GB

REGENERÉRBAR (97.6%):
├── frontend/node_modules/  981 MB   npm install
├── backend/models/         506 MB   Hugging Face download (langsom!)
├── backend/venv/           324 MB   pip install -r requirements.txt
├── backend/htmlcov/        57 MB    pytest --cov
├── backend/logs/           48 MB    Log rotation
└── frontend/coverage/      7.3 MB   jest --coverage

KRITISK KODE (2.4% = ~60 MB):
├── orchestrator/           37 MB    CKC orchestration kode
├── backend/tests/          12 MB    Test suites
├── backend/agents/         6.6 MB   Agent konfigurationer
├── backend/api/            2.2 MB   API endpoints
├── backend/services/       1.4 MB   Service logik
├── frontend/app/           1 MB     Next.js pages
├── frontend/components/    504 KB   React components
├── frontend/__tests__/     372 KB   Frontend tests
├── backend/database/       472 KB   Database schemas
├── backend/alembic/        288 KB   Migrationer
├── docs/                   176 KB   Dokumentation
└── Root MD filer           ~1 MB    Dokumentation
```

### 2.2 .gitignore Status: ⚠️ MANGLER ENTRY

**Nuværende .gitignore ignorerer:**
- node_modules/, venv/
- __pycache__/, .next/
- htmlcov/, .coverage
- logs/

**MANGLER:**
- `models/` (Hugging Face cache - 506 MB)

### 2.3 .gitignore Opdatering Anbefalet

```bash
# Tilføj til lib-admin-main/.gitignore:
# AI Models (regenerérbar)
backend/models/
```

### 2.4 Backup Anbefaling

**Metode:** rsync med exclude af regenerérbare mapper

```bash
rsync -av --progress \
  --exclude 'venv/' \
  --exclude 'node_modules/' \
  --exclude '.next/' \
  --exclude '__pycache__/' \
  --exclude 'models/' \
  --exclude 'htmlcov/' \
  --exclude 'coverage/' \
  --exclude 'logs/' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache/' \
  lib-admin-main/ \
  /backup/lib-admin/
```

**Estimeret backup størrelse:** ~60-80 MB

---

## 3. BACKUP STRATEGI

### 3.1 Backup Lokationer

| Niveau | Lokation | Frekvens | Retention |
|--------|----------|----------|-----------|
| **Lokal** | `/home/rasmus/backups/ecosystem/` | Dagligt | 7 dage |
| **Ekstern** | GitHub (hvis git initialiseres) | Ved ændring | Permanent |
| **Cloud** | AWS S3 (fremtid) | Ugentligt | 30 dage |

### 3.2 Backup Script

**Fil:** `scripts/ecosystem-backup.sh`

```bash
#!/bin/bash
# ============================================================
# CIRKELLINE ECOSYSTEM BACKUP SCRIPT
# Version: 1.0.0
# Date: 2025-12-17
# ============================================================

set -e

# Konfiguration
BACKUP_BASE="/home/rasmus/backups/ecosystem"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_BASE}/${TIMESTAMP}"
PROJECTS_DIR="/home/rasmus/Desktop/projekts/projects"

# Farver
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  CIRKELLINE ECOSYSTEM BACKUP           ║${NC}"
echo -e "${GREEN}║  ${TIMESTAMP}                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"

# Opret backup mappe
mkdir -p "${BACKUP_DIR}"

# Fælles exclude patterns
EXCLUDES=(
    --exclude 'venv/'
    --exclude '.venv/'
    --exclude 'node_modules/'
    --exclude '.next/'
    --exclude '__pycache__/'
    --exclude '*.pyc'
    --exclude '.pytest_cache/'
    --exclude 'htmlcov/'
    --exclude 'coverage/'
    --exclude 'logs/'
    --exclude 'models/'
    --exclude '*.log'
    --exclude '.env'
    --exclude '.env.local'
    --exclude '.env.production'
)

# Backup Cosmic-Library
echo -e "\n${YELLOW}[1/2] Backing up Cosmic-Library...${NC}"
rsync -av --progress "${EXCLUDES[@]}" \
    "${PROJECTS_DIR}/Cosmic-Library-main/" \
    "${BACKUP_DIR}/Cosmic-Library-main/"
echo -e "${GREEN}✓ Cosmic-Library backup complete${NC}"

# Backup lib-admin
echo -e "\n${YELLOW}[2/2] Backing up lib-admin...${NC}"
rsync -av --progress "${EXCLUDES[@]}" \
    "${PROJECTS_DIR}/lib-admin-main/" \
    "${BACKUP_DIR}/lib-admin-main/"
echo -e "${GREEN}✓ lib-admin backup complete${NC}"

# Vis backup størrelse
echo -e "\n${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}BACKUP COMPLETE${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo "Location: ${BACKUP_DIR}"
du -sh "${BACKUP_DIR}"/*

# Cleanup gamle backups (behold 7 dage)
echo -e "\n${YELLOW}Cleaning old backups (>7 days)...${NC}"
find "${BACKUP_BASE}" -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
echo -e "${GREEN}✓ Cleanup complete${NC}"

# Optæl aktive backups
BACKUP_COUNT=$(find "${BACKUP_BASE}" -maxdepth 1 -type d | wc -l)
echo -e "\nActive backups: $((BACKUP_COUNT - 1))"
```

### 3.3 Cron Job Setup

```bash
# Daglig backup kl. 04:00
0 4 * * * /home/rasmus/Desktop/projekts/projects/cirkelline-system/scripts/ecosystem-backup.sh >> /var/log/cirkelline-backup.log 2>&1
```

---

## 4. RESTORE PROCEDURE

### 4.1 Cosmic-Library Restore

```bash
# 1. Gendan fra backup
cp -r /home/rasmus/backups/ecosystem/YYYYMMDD_HHMMSS/Cosmic-Library-main/ \
      /home/rasmus/Desktop/projekts/projects/Cosmic-Library-main/

# 2. Regenerer venv
cd Cosmic-Library-main/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Regenerer node_modules
cd ../frontend
npm install

# 4. Rebuild
npm run build
```

### 4.2 lib-admin Restore

```bash
# 1. Gendan fra backup
cp -r /home/rasmus/backups/ecosystem/YYYYMMDD_HHMMSS/lib-admin-main/ \
      /home/rasmus/Desktop/projekts/projects/lib-admin-main/

# 2. Regenerer backend
cd lib-admin-main/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Regenerer Hugging Face models (LANGSOMT - ~30 min)
python -c "from transformers import pipeline; pipeline('text-classification')"

# 4. Regenerer frontend
cd ../frontend
npm install

# 5. Rebuild
npm run build
```

---

## 5. GIT INITIALISERING (ANBEFALET)

### 5.1 Cosmic-Library

```bash
cd /home/rasmus/Desktop/projekts/projects/Cosmic-Library-main

# Verificer .gitignore er korrekt
cat .gitignore

# Initialiser git
git init
git add .
git commit -m "Initial commit: Cosmic-Library codebase"

# Tilføj remote (valgfrit)
git remote add origin git@github.com:eenvywithin/Cosmic-Library.git
git push -u origin main
```

### 5.2 lib-admin

```bash
cd /home/rasmus/Desktop/projekts/projects/lib-admin-main

# Opdater .gitignore først
echo -e "\n# AI Models (regenerable)\nbackend/models/" >> .gitignore

# Initialiser git
git init
git add .
git commit -m "Initial commit: lib-admin codebase"

# Tilføj remote (valgfrit)
git remote add origin git@github.com:eenvywithin/lib-admin.git
git push -u origin main
```

---

## 6. VERIFIKATION

### 6.1 Backup Tjekliste

| Check | Cosmic-Library | lib-admin |
|-------|----------------|-----------|
| Kode inkluderet | ✅ | ✅ |
| venv ekskluderet | ✅ | ✅ |
| node_modules ekskluderet | ✅ | ✅ |
| models/ ekskluderet | N/A | ✅ |
| logs/ ekskluderet | ✅ | ✅ |
| .env ekskluderet | ✅ | ✅ |
| Dokumentation inkluderet | ✅ | ✅ |

### 6.2 Restore Test

```bash
# Test restore procedure kvartalsvis
# 1. Lav backup
# 2. Slet original (eller brug testmappe)
# 3. Restore fra backup
# 4. Regenerer dependencies
# 5. Kør tests
# 6. Verificer funktionalitet
```

---

## 7. INTEGRATION MED RØD TRÅD

### 7.1 Backup som del af Ecosystem

```
CIRKELLINE ECOSYSTEM BACKUP STRUKTUR
═══════════════════════════════════════════════════════════════

  GIT-TRACKEDE PROJEKTER (automatisk backup via GitHub):
  ─────────────────────────────────────────────────────
  ✅ cirkelline-system         → github.com/eenvywithin/...
  ✅ Cirkelline-Consulting-main → github.com/cirkelline/...
  ✅ cirkelline-system-BACKUP   → github.com/eenvywithin/...

  MANUEL BACKUP PÅKRÆVET:
  ─────────────────────────────────────────────────────
  📦 Cosmic-Library-main       → /backups/ecosystem/
  📦 lib-admin-main            → /backups/ecosystem/

  DOCKER INFRASTRUKTUR (data volumes):
  ─────────────────────────────────────────────────────
  🐳 Commando-Center-main      → Docker volumes (separat)

═══════════════════════════════════════════════════════════════
```

---

## 8. NÆSTE SKRIDT

| # | Handling | Status | Ansvarlig |
|---|----------|--------|-----------|
| 1 | Opret backup mappe struktur | ⏳ | Script |
| 2 | Implementer backup script | ⏳ | Script |
| 3 | Test backup procedure | ⏳ | Manual |
| 4 | Setup cron job | ⏳ | Manual |
| 5 | (Valgfrit) Git init projekter | ⏳ | Manual |
| 6 | Opdater RØD-TRÅD | ⏳ | Dokumentation |
| 7 | Opdater MASTER-ROADMAP | ⏳ | Dokumentation |

---

*Dokumentation oprettet: 2025-12-17*
*System: Cirkelline v1.3.5*
*Agent: Opus 4.5*
