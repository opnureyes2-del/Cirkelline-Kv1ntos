# CIRKELLINE SYSTEM RUTINER

**Oprettet:** 2025-12-17
**Agent:** Kommandor #4
**Version:** v1.3.5
**Status:** KOMPLET DOKUMENTATION

---

## OVERBLIK

```
CIRKELLINE RUTINER OVERSIGT
===========================================================================

AUTOMATISKE RUTINER (Cron)
--------------------------
[03:33] Sorting Routine          ✅ IMPLEMENTERET  scripts/sorting_0333.py
[09:00] Morning Sync             ✅ IMPLEMENTERET  scripts/morning_sync_0900.py
[21:21] Evening Optimization     ✅ IMPLEMENTERET  scripts/evening_opt_2121.py

DEPLOYMENT RUTINER
------------------
Blue-Green Deploy               ✅ DOKUMENTERET   aws_deployment/deploy_blue_green.sh
Standard Deploy                 ✅ EKSISTERENDE   aws_deployment/deploy.sh
Secret Rotation                 ✅ EKSISTERENDE   aws_deployment/rotate_secrets.sh
DB Backup                       ✅ EKSISTERENDE   aws_deployment/db_backup.sh

MONITORING RUTINER
------------------
CloudWatch Setup                ✅ IMPLEMENTERET  aws_deployment/setup_monitoring.sh
Health Checks                   ✅ EKSISTERENDE   curl localhost:7777/health

TEST RUTINER
------------
Backend (pytest)                ✅ EKSISTERENDE   pytest tests/ -v
Frontend (Vitest)               ✅ IMPLEMENTERET  npm run test
E2E (Playwright)                ✅ IMPLEMENTERET  npm run test:e2e

===========================================================================
```

---

## AUTOMATISKE RUTINER

### 03:33 SORTING ROUTINE

**Status:** ✅ IMPLEMENTERET
**Script:** `scripts/sorting_0333.py`
**Cron Setup:** `scripts/setup_sorting_cron.sh`

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          03:33 SORTING FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 1: MEMORY AUDIT                                                    │
│  ├── gc.collect() - Force garbage collection                             │
│  ├── Get memory statistics                                               │
│  └── Log memory freed                                                    │
│                                                                          │
│  STEP 2: SYSTEM CLEANUP                                                  │
│  ├── Clean /tmp files (>7 days)                                          │
│  ├── Clean ~/.ckc/cache/* (>24 hours)                                    │
│  └── Remove old session files                                            │
│                                                                          │
│  STEP 3: LOG ROTATION                                                    │
│  ├── Rotate active logs                                                  │
│  ├── Compress to .gz                                                     │
│  └── Delete logs >30 days                                                │
│                                                                          │
│  STEP 4: CACHE INVALIDATION                                              │
│  ├── Redis: Selective FLUSHDB                                            │
│  ├── File cache: Clear expired                                           │
│  └── Memory cache: gc.collect()                                          │
│                                                                          │
│  STEP 5: INDEX OPTIMIZATION                                              │
│  ├── PostgreSQL: VACUUM ANALYZE                                          │
│  ├── pgvector: Check index health                                        │
│  └── Clear query plan cache                                              │
│                                                                          │
│  RAPPORT                                                                 │
│  └── Save to ~/.ckc/sorting-report-YYYY-MM-DD.json                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Kommandoer:**
```bash
# Test (dry-run)
python scripts/sorting_0333.py --dry-run --verbose

# Live execution
python scripts/sorting_0333.py

# Install cron job
bash scripts/setup_sorting_cron.sh

# Se logs
tail -f /var/log/ckc/sorting_0333.log

# Se rapporter
ls -la ~/.ckc/sorting-report-*.json
```

**Cron Entry:**
```cron
33 3 * * * /path/to/python /path/to/scripts/sorting_0333.py >> /var/log/ckc/sorting_0333.log 2>&1
```

**Test Output:**
```
Steps completed: 5/5
Duration: 0.06 seconds
Status: SUCCESS
```

---

### 09:00 MORNING SYNC

**Status:** ✅ IMPLEMENTERET
**Script:** `scripts/morning_sync_0900.py`
**Formål:** Daglig morgensync af team status

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          09:00 MORNING SYNC FLOW                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 1: CHECK SORTING REPORT                                            │
│  ├── Find sorting-report-YYYY-MM-DD.json                                │
│  ├── Verificer success status                                            │
│  └── Log eventuelle fejl                                                 │
│                                                                          │
│  STEP 2: VERIFY SYSTEM HEALTH                                            │
│  ├── Backend health endpoint                                             │
│  ├── Disk space check                                                    │
│  ├── Memory usage check                                                  │
│  └── Docker containers status                                            │
│                                                                          │
│  STEP 3: COLLECT METRICS                                                 │
│  ├── Git status og commits                                               │
│  ├── Test file count                                                     │
│  ├── SYNKRONISERING docs count                                           │
│  └── System uptime                                                       │
│                                                                          │
│  STEP 4: UPDATE SYNC STATUS                                              │
│  └── Save last_morning_sync.json                                         │
│                                                                          │
│  STEP 5: GENERATE REPORT                                                 │
│  └── Save morning-sync-YYYY-MM-DD.json                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Kommandoer:**
```bash
# Test (dry-run)
python3 scripts/morning_sync_0900.py --dry-run --verbose

# Live execution
python3 scripts/morning_sync_0900.py

# Se rapporter
ls -la ~/.ckc/morning-reports/
```

**Test Output:**
```
Steps completed: 5/5
Duration: 0.03 seconds
Status: SUCCESS
```

---

### 21:21 EVENING OPTIMIZATION

**Status:** ✅ IMPLEMENTERET
**Script:** `scripts/evening_opt_2121.py`
**Formål:** Daglig aftenoptimering

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          21:21 EVENING OPT FLOW                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 1: SESSION CLEANUP                                                 │
│  ├── Ryd gamle session filer (>24h)                                      │
│  ├── Clean __pycache__ (>48h)                                            │
│  └── Free disk space                                                     │
│                                                                          │
│  STEP 2: MEMORY PRE-OPTIMIZATION                                         │
│  ├── Force garbage collection                                            │
│  ├── Get memory statistics                                               │
│  └── Log memory freed                                                    │
│                                                                          │
│  STEP 3: METRICS AGGREGATION                                             │
│  ├── Check morning sync status                                           │
│  ├── Check sorting status                                                │
│  ├── Git activity today                                                  │
│  └── Aggregate daily stats                                               │
│                                                                          │
│  STEP 4: PREPARE NEXT DAY                                                │
│  ├── Verify CKC directories                                              │
│  ├── Check disk space                                                    │
│  ├── Verify cron jobs                                                    │
│  └── Save next_day_prep.json                                             │
│                                                                          │
│  STEP 5: GENERATE REPORT                                                 │
│  └── Save evening-opt-YYYY-MM-DD.json                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Kommandoer:**
```bash
# Test (dry-run)
python3 scripts/evening_opt_2121.py --dry-run --verbose

# Live execution
python3 scripts/evening_opt_2121.py

# Se rapporter
ls -la ~/.ckc/evening-reports/
```

**Test Output:**
```
Steps completed: 5/5
Duration: 0.57 seconds
Sessions cleaned: 0
Memory freed: 0.0 MB
Ready for 03:33: Yes
```

---

## DEPLOYMENT RUTINER

### BLUE-GREEN DEPLOYMENT

**Status:** ✅ DOKUMENTERET
**Guide:** `aws_deployment/BLUE-GREEN-DEPLOYMENT-GUIDE.md`
**Script:** `aws_deployment/deploy_blue_green.sh`

```bash
# Standard blue-green deploy
./aws_deployment/deploy_blue_green.sh v1.3.6

# With canary strategy (10% → 100%)
./aws_deployment/deploy_blue_green.sh v1.3.6 --canary

# With linear strategy (10% every minute)
./aws_deployment/deploy_blue_green.sh v1.3.6 --linear

# Monitor deployment
aws ecs describe-services --cluster cirkelline-system-cluster \
  --services cirkelline-system-backend-service --region eu-north-1
```

**Pre-flight checklist:**
- [ ] Alle tests passerer
- [ ] Docker image bygget
- [ ] ECR push komplet
- [ ] Health endpoint verificeret
- [ ] Rollback plan klar

---

### STANDARD DEPLOYMENT

**Status:** ✅ EKSISTERENDE
**Script:** `aws_deployment/deploy.sh`

```bash
# Full deploy
./aws_deployment/deploy.sh

# Deploy specific version
./aws_deployment/deploy.sh v1.3.5
```

---

### SECRET ROTATION

**Status:** ✅ EKSISTERENDE
**Script:** `aws_deployment/rotate_secrets.sh`

```bash
# Rotate all secrets
./aws_deployment/rotate_secrets.sh

# Rotate specific secret
./aws_deployment/rotate_secrets.sh --secret-name cirkelline-jwt-secret
```

---

### DATABASE BACKUP

**Status:** ✅ EKSISTERENDE
**Script:** `aws_deployment/db_backup.sh`

```bash
# Full backup
./aws_deployment/db_backup.sh

# Backup to specific S3 bucket
./aws_deployment/db_backup.sh --bucket cirkelline-backups
```

---

## MONITORING RUTINER

### CLOUDWATCH SETUP

**Status:** ✅ IMPLEMENTERET
**Script:** `aws_deployment/setup_monitoring.sh`

```bash
# Setup alt (SNS + alarms + dashboard)
./aws_deployment/setup_monitoring.sh --all

# Kun alarms
./aws_deployment/setup_monitoring.sh --alarms

# Kun dashboard
./aws_deployment/setup_monitoring.sh --dashboard

# Check status
./aws_deployment/setup_monitoring.sh --status
```

**10 CloudWatch Alarms:**
| Alarm | Trigger | Kategori |
|-------|---------|----------|
| cirkelline-ecs-cpu-high | CPU >80% | ECS |
| cirkelline-ecs-memory-high | Memory >80% | ECS |
| cirkelline-ecs-task-count-low | Tasks <desired | ECS |
| cirkelline-alb-5xx-errors | 5XX >10/5min | ALB |
| cirkelline-alb-latency-high | Latency >2s | ALB |
| cirkelline-alb-unhealthy-hosts | Unhealthy >0 | ALB |
| cirkelline-alb-request-count-anomaly | Requests >10k | ALB |
| cirkelline-rds-cpu-high | CPU >80% | RDS |
| cirkelline-rds-connections-high | Connections >80 | RDS |
| cirkelline-rds-storage-low | Storage <5GB | RDS |

---

### HEALTH CHECK

```bash
# Backend health
curl http://localhost:7777/health

# Config check
curl http://localhost:7777/config

# AWS production
curl https://api.cirkelline.com/health
```

---

## TEST RUTINER

### BACKEND TESTS (pytest)

**Status:** ✅ EKSISTERENDE
**Baseline:** 1,322 tests / 39 filer

```bash
# Alle tests
pytest tests/ -v

# Specifik fil
pytest tests/test_cirkelline.py -v

# Med coverage
pytest tests/ --cov=cirkelline --cov-report=html

# Kun CKC tests
pytest tests/test_ckc_*.py -v
```

---

### FRONTEND TESTS (Vitest)

**Status:** ✅ IMPLEMENTERET
**Tests:** 21 unit tests

```bash
cd cirkelline-ui

# Kør alle unit tests
npm run test

# Watch mode
npm run test:watch

# Med coverage
npm run test:coverage
```

**Test Files:**
- `tests/store.test.ts` - 15 Zustand store tests
- `tests/components/Button.test.tsx` - 6 component tests

---

### E2E TESTS (Playwright)

**Status:** ✅ IMPLEMENTERET
**Tests:** 6 E2E tests

```bash
cd cirkelline-ui

# Kør E2E tests
npm run test:e2e

# Specifik browser
npx playwright test --project=chromium

# Debug mode
npx playwright test --debug

# Med UI
npx playwright test --ui
```

**Browsers Supported:**
- Chromium (Desktop Chrome)
- Firefox
- WebKit (Safari)
- Mobile Chrome (Pixel 5)
- Mobile Safari (iPhone 12)

---

## GIT WORKFLOW RUTINER

### STANDARD COMMIT

```bash
# 1. Check status
git status

# 2. Stage changes
git add <files>

# 3. Commit med besked
git commit -m "feat: Description

Details here.

Co-Authored-By: Claude <noreply@anthropic.com>"

# 4. Push
git push origin main
```

---

### PRE-COMMIT CHECKLIST

- [ ] `git status` - Check ændringer
- [ ] `pytest tests/ -v` - Backend tests passerer
- [ ] `cd cirkelline-ui && npm run test` - Frontend tests passerer
- [ ] `cd cirkelline-ui && npm run build` - Build succeeds
- [ ] Ingen secrets i kode
- [ ] Dokumentation opdateret

---

## SESSION RUTINER

### SESSION START

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SESSION START CHECKLIST                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. [ ] Læs SYNKRONISERING/INDEX.md                                     │
│  2. [ ] Læs MASTER-ROADMAP-2025-12-XX.md                                │
│  3. [ ] Check git status                                                 │
│  4. [ ] docker start cirkelline-postgres                                │
│  5. [ ] python my_os.py (hvis backend needed)                           │
│  6. [ ] Verificer health: curl localhost:7777/health                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### SESSION END

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SESSION END CHECKLIST                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. [ ] Commit alle ændringer                                           │
│  2. [ ] Opdater SYNKRONISERING/INDEX.md                                 │
│  3. [ ] Opdater relevante TODO filer                                    │
│  4. [ ] Opdater MASTER-ROADMAP hvis nødvendigt                          │
│  5. [ ] Notér næste steps                                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## RUTINE IMPLEMENTATION STATUS

| Rutine | Script | Status | Næste Step |
|--------|--------|--------|------------|
| 03:33 Sorting | sorting_0333.py | ✅ IMPLEMENTERET | Monitoring/Alerting |
| 09:00 Morning Sync | morning_sync_0900.py | ✅ IMPLEMENTERET | CI/CD integration |
| 21:21 Evening Opt | evening_opt_2121.py | ✅ IMPLEMENTERET | CI/CD integration |
| Blue-Green Deploy | deploy_blue_green.sh | ✅ DOKUMENTERET | Production test |
| CloudWatch Setup | setup_monitoring.sh | ✅ IMPLEMENTERET | Subscribe emails |
| Frontend Testing | Vitest + Playwright | ✅ IMPLEMENTERET | CI/CD integration |
| All Routines Cron | setup_all_routines_cron.sh | ✅ IMPLEMENTERET | Install on server |

---

## BAKTERIE-PERSPEKTIV

### Hvad Sker Ved Hver Rutine?

```
DAGLIGT FLOW:
=============================================================================

[03:33] ─────────────────────────────────────────────────────────────────────
        │
        ├── sorting_0333.py STARTER
        │   ├── Step 1: Memory gc.collect()
        │   ├── Step 2: Clean /tmp, ~/.ckc/cache
        │   ├── Step 3: Rotate logs, compress, delete >30d
        │   ├── Step 4: Clear Redis, file cache, memory
        │   ├── Step 5: PostgreSQL VACUUM ANALYZE
        │   └── Save report to ~/.ckc/sorting-report-*.json
        │
[09:00] ─────────────────────────────────────────────────────────────────────
        │
        ├── morning_sync_0900.py STARTER (CRON AKTIV)
        │   ├── Step 1: Check sorting rapport
        │   ├── Step 2: Verify system health
        │   ├── Step 3: Collect metrics
        │   ├── Step 4: Update sync status
        │   └── Save report to ~/.ckc/morning-reports/*.json
        │
[WORKDAY] ───────────────────────────────────────────────────────────────────
        │
        ├── Manual operations as needed
        │   ├── pytest tests/ -v
        │   ├── npm run test
        │   ├── git commit
        │   └── ./deploy_blue_green.sh (hvis deploy)
        │
[21:21] ─────────────────────────────────────────────────────────────────────
        │
        ├── evening_opt_2121.py STARTER (CRON AKTIV)
        │   ├── Step 1: Session cleanup
        │   ├── Step 2: Memory pre-optimization
        │   ├── Step 3: Metrics aggregation
        │   ├── Step 4: Prepare next day
        │   └── Save report to ~/.ckc/evening-reports/*.json
        │
=============================================================================
```

---

*Opdateret: 2025-12-17 ~09:15*
*Agent: Kommandor #4*
*Version: v1.3.5*
*Status: ALLE RUTINER IMPLEMENTERET (03:33 + 09:00 + 21:21)*
