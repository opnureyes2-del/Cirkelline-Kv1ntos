# 70_GUIDES - INDEKS
**Version:** v1.1.0
**Dato:** 2025-12-28
**Indhold:** Alle guides og vejledninger

---

## STRUKTUR

```
70_GUIDES/
├── 70_INDEX.md                 ← DENNE FIL
├── 71_SETUP/                   (11 filer)
│   ├── 71_INDEX.md
│   ├── agents_EXPO_QUICK_SETUP.md
│   ├── consulting_*.md (7 filer)
│   ├── cosmic_QUICK_START.md
│   ├── kommandor_QUICK_START.md
│   └── lib-admin_QUICKSTART.md
├── 72_TESTING/                 (4 filer)
│   ├── 72_INDEX.md
│   ├── consulting_ADMIN_AUTH_TESTING.md
│   ├── consulting_QUICK_START_TESTING.md
│   └── GULDGULD_TESTING_GUIDE.md
├── 73_TROUBLESHOOTING/         (4 filer)
│   ├── 73_INDEX.md
│   ├── BUG_FIX_KATALOG.md
│   ├── ERRORS_AND_ISSUES.md
│   └── GULDGULD_TROUBLESHOOTING.md
├── 74_INTEGRATION/             (5 filer)
│   ├── 74_INDEX.md
│   ├── CKC_INTEGRATION_GUIDE.md
│   ├── PLATFORM_INTEGRATION_ANALYSIS.md
│   ├── PLATFORM_INTEGRATION_FLOW.md
│   └── TEST_ALL_INTEGRATIONS.md
├── 75_INTRO_ARBEJDSPROCEDURE/  ✨ NYE (2 filer)
│   ├── 75_INTRO_ARBEJDSPROCEDURE.md  ← KOMPLET TODO 39 PROCEDURE GUIDE
│   └── _TODO_VERIFIKATION/STATUS.md
└── _SKRALDESPAND/
```

---

## TOTAL: 31 filer (+2 nye)

---

## FEJLHÅNDTERING

### Problem 1: Guide Outdated - Steps Don't Work Anymore

**Symptom:** Følger guide step-by-step men får fejl ved step 3, eller guide siger "click Admin tab" men UI ændret og Admin tab findes ikke længere

**Årsag:**
- Guide skrevet for gammel version af projekt
- UI/UX refactored men guide ikke opdateret
- Dependencies opdateret (npm packages, Python versions) men guide har gamle kommandoer
- Guide copy-pasted fra andet projekt og ikke tilpasset

**Diagnosticering:**
```bash
# Check guide last updated
cat INTRO/70_GUIDES/<7X_TYPE>/<GUIDE_NAME>.md | grep -i "dato\|updated\|version"

# Check git history for changes i projekt siden guide update
cd ~/Desktop/projekts/projects/<projekt>
GUIDE_DATE="2025-12-15"  # fra guide metadata
git log --since="$GUIDE_DATE" --oneline | wc -l

# Check for breaking changes
git log --since="$GUIDE_DATE" --grep="BREAKING\|refactor\|update" --oneline

# Test guide step-by-step (actual physical test)
# Step 1: [test]
# Step 2: [test]
# Step 3: [fails here] ← document where guide breaks

# Check om dependencies changed
cat ~/Desktop/projekts/projects/<projekt>/backend/requirements.txt
cat ~/Desktop/projekts/projects/<projekt>/frontend/package.json
# Compare med guide's listed dependencies
```

**Fix:**
1. Follow guide exactly, note hvor det fejler:
   ```
   Step 1: ✅ Works
   Step 2: ✅ Works
   Step 3: ❌ Fails - command "npm install" should be "pnpm install"
   Step 4: ❌ UI changed - "Admin" tab now called "Settings"
   ```
2. Test opdaterede steps fysisk:
   ```bash
   # Test new command works
   pnpm install
   # Test new UI path exists
   ```
3. Opdater guide med working steps:
   ```markdown
   ## Step 3: Install Dependencies (UPDATED 2026-01-08)
   ```bash
   pnpm install  # Changed from npm install
   ```
   **Note:** Frontend switched to pnpm in v2.0.0
   ```
4. Add version/date metadata i guide header:
   ```markdown
   **Version:** 2.1.0
   **Last Tested:** 2026-01-08
   **Tested With:** lib-admin v3.2.0, Node 20.x
   ```
5. Tilføj screenshots hvis UI changed (optional but helpful)
6. Git commit: "GUIDE UPDATED: <guide_name> - fixed steps 3-4, tested with current version"

**Prevention:**
- Version metadata i ALL guides (last tested date + project version)
- Quarterly guide testing: follow each guide step-by-step
- Link guide updates til CLAUDE.md updates (same trigger)
- Automated reminder: if project has >100 commits since guide update → flag for review

---

### Problem 2: Guide Mangler For Common Task

**Symptom:** Rasmus eller udvikler spørger gentagne gange "hvordan deployer jeg til production?" eller "hvordan kører jeg migrations?" men ingen guide eksisterer

**Årsag:**
- Task er ny (deployment setup for første gang)
- Task antaget "obvious" men faktisk ikke dokumenteret
- Tribal knowledge - kun Ivo ved hvordan, aldrig skrevet ned
- Guide planlagt men aldrig skrevet

**Diagnosticering:**
```bash
# Search eksisterende guides for keyword
grep -r "deployment\|deploy" INTRO/70_GUIDES/

# Check session logs for gentagne spørgsmål
grep -r "hvordan\|how do I" INTRO/00_SESSION_LOGS/ | grep -i "<keyword>"

# List current guides
find INTRO/70_GUIDES/ -name "*.md" -type f | grep -v INDEX | grep -v STATUS

# Identificer gap:
# Common tasks: setup, testing, deployment, troubleshooting, integration
# Mangler: <task_name>
```

**Fix:**
1. Verificer task er gentagende (ikke one-time):
   - Skal andre kunne gøre det?
   - Sker det regelmæssigt (weekly/monthly)?
   - Kræver det >5 steps?
2. Identificer rigtig guide kategori:
   - Setup (71_SETUP) - initial project setup
   - Testing (72_TESTING) - how to test features
   - Troubleshooting (73_TROUBLESHOOTING) - fixing problems
   - Integration (74_INTEGRATION) - connecting systems
   - Arbejdsprocedure (75_) - workflows og procedures
3. Opret guide:
   ```bash
   # Eksempel: deployment guide
   touch INTRO/70_GUIDES/71_SETUP/<projekt>_DEPLOYMENT_GUIDE.md
   ```
4. Skriv guide med structure:
   ```markdown
   # <Projekt> Deployment Guide
   **Version:** 1.0.0
   **Last Tested:** 2026-01-08
   **Tested With:** <projekt> v2.0.0

   ## Prerequisites
   - [list requirements]

   ## Step 1: [Name]
   ```bash
   [command]
   ```
   **Expected output:** [what user should see]

   ## Step 2: [Name]
   ...

   ## Troubleshooting
   - **Problem:** [common issue]
   - **Solution:** [how to fix]
   ```
5. Test guide fysisk (follow it yourself)
6. Tilføj til 70_GUIDES.md index og relevant 7X_INDEX.md
7. Git commit: "NEW GUIDE: <guide_name> - <purpose>"

**Prevention:**
- Gap analysis: compare common questions vs existing guides (monthly)
- Guide creation i 00_UDVIKLINGSPLAN.md Fase 6 for new features
- Session log review: if same question asked 3+ times → create guide
- Template i 06_TEMPLATE_INTRO for quick guide creation

---

### Problem 3: Guide Conflicts Med Andre Dokumenter

**Symptom:** Setup guide siger "backend kører på port 7777" men 15_MILJOER siger port 7779, eller guide siger "database: ckc_db" men CLAUDE.md siger "database: ckc_admin"

**Årsag:**
- Guide copy-pasted fra andet projekt uden tilpasning
- Multiple sources of truth ikke synced
- Guide skrevet før environment standardisering
- Guide opdateret men cross-references ikke checked

**Diagnosticering:**
```bash
# Extract facts fra guide
cat INTRO/70_GUIDES/<7X>/<GUIDE>.md | grep -i "port\|database\|endpoint"

# Compare med 15_MILJOER
cat INTRO/15_MILJOER/15_MILJOER.md | grep "<projekt>"
cat INTRO/15_MILJOER/15C_PORT_MAPPING/15C_PORT_MAPPING.md | grep "<projekt>"

# Compare med CLAUDE.md
cat INTRO/60_CLAUDE_MD/<XX_CLAUDE>/CLAUDE.md | grep -i "port\|database"

# Compare med baseline
cat INTRO/40_BASELINES/<XX_BASELINE>/<XX_BASELINE>.md | grep -i "port\|database"

# Test faktisk system (source of truth)
cat ~/Desktop/projekts/projects/<projekt>/backend/.env | grep "PORT\|DATABASE"
sudo lsof -i :<port_from_guide>
```

**Fix:**
1. Identificer all conflicts:
   ```
   Guide says: Port 7777
   15_MILJOER says: Port 7779
   CLAUDE.md says: Port 7779
   Actual (.env): PORT=7779
   CONFLICT: Guide is wrong
   ```
2. Establish source of truth (in priority order):
   - Actual running system (.env, lsof) = HIGHEST AUTHORITY
   - 15_MILJOER (environment standards)
   - CLAUDE.md (project instructions)
   - Guide (should match above)
3. Opdater guide til match source of truth:
   ```markdown
   ## Environment Setup
   **Backend Port:** 7779 (verified with 15_MILJOER)
   **Database:** ckc_admin (verified with .env)

   ```bash
   # Start backend
   cd backend
   uvicorn main:app --port 7779
   ```
   ```
4. Cross-reference i guide:
   ```markdown
   **Note:** See `15_MILJOER/15C_PORT_MAPPING` for complete port allocation
   ```
5. Validation checklist før guide publish:
   - ✅ Ports match 15_MILJOER?
   - ✅ Database names match CLAUDE.md?
   - ✅ Endpoints match baseline docs?
   - ✅ Tested with actual .env file?
6. Git commit: "GUIDE CORRECTED: <guide> - aligned with 15_MILJOER and CLAUDE.md"

**Prevention:**
- ALWAYS cross-check guide med 15_MILJOER, CLAUDE.md, baseline
- Guide template includes "Cross-Reference Validation" section
- Pre-commit hook: scan guides for common conflicts (ports, databases)
- Quarterly audit: validate all guides against canonical sources

---

## ÆNDRINGSLOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2025-12-28 | - | 70_GUIDES index oprettet | Claude |
| 2025-12-28 | 21:51 | ÆNDRINGSLOG sektion tilføjet | Claude |
| 2025-12-28 | 23:13 | 75_INTRO_ARBEJDSPROCEDURE tilføjet (+2 filer) | Claude |
| 2025-12-28 | 23:13 | v1.1.0 - Komplet TODO 39 procedure guide | Claude |
| 2026-01-08 | 12:15 | FEJLHÅNDTERING tilføjet (3 problems: outdated guide, missing guide, conflicts with other docs) | Claude |

---

*70_GUIDES.md - Opdateret 2026-01-08 12:15*
