# 3:33 SORTERING RUTINE

**Oprettet:** 2025-12-17
**Agent:** Kommandor #4
**Version:** v1.3.5
**Status:** ✅ AKTIV + CRON INSTALLERET

---

## FORMÅL

Daglig automatisk sortering og optimering af systemet kl. 03:33.

---

## TIDSPLAN

| Tid | Handling | Type |
|-----|----------|------|
| 03:33 | Morning Memory Audit | Auto |
| 03:33 | System Cleanup | Auto |
| 03:33 | Log Rotation | Auto |
| 03:33 | Cache Invalidation | Auto |
| 03:33 | Index Optimization | Auto |

---

## HANDLINGER

### 1. Morning Memory Audit
```
Lokation: Memory Evolution Room
Handling: Audit og optimering af hukommelse
Frekvens: Dagligt kl. 03:33
```

### 2. System Cleanup
```
Handling: Fjern midlertidige filer
Targets:
  - /tmp/*.log (ældre end 7 dage)
  - ~/.ckc/cache/* (ældre end 24 timer)
  - logs/*.log (rotation)
```

### 3. Log Rotation
```
Handling: Roter og komprimér logs
Targets:
  - Backend logs
  - CKC logs
  - Agent logs
Retention: 30 dage
```

### 4. Cache Invalidation
```
Handling: Ryd forældede cache entries
Targets:
  - Redis cache
  - File cache
  - Memory cache
```

### 5. Index Optimization
```
Handling: Optimér database indekser
Targets:
  - PostgreSQL VACUUM
  - pgvector index rebuild
  - Query plan cache clear
```

---

## MONITORING

### Success Criteria
- Memory audit komplet
- Logs roteret korrekt
- Cache cleared
- Indekser optimeret
- Ingen fejl i execution

### Failure Handling
- Alert til admin hvis fejl
- Retry efter 15 minutter
- Eskalér efter 3 forsøg

---

## INTEGRATION

### Med Eksisterende Rutiner

| Tid | Rutine | Relation |
|-----|--------|----------|
| 03:33 | **SORTERING** | Primær |
| 09:00 | Morning Sync | Efter sortering |
| 21:21 | Evening Optimization | Komplement |

### Koordination

```
03:33 SORTERING → Cleanup + Audit
     ↓
09:00 MORNING SYNC → Fresh start
     ↓
21:21 EVENING OPT → Daglig afslutning
```

---

## BAKTERIE-PERSPEKTIV

### Hvad Sker Ved 03:33?

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          03:33 SORTERING                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 1: MEMORY AUDIT                                                    │
│  ├── Scan alle memory entries                                            │
│  ├── Identificer duplicates                                              │
│  ├── Merge lignende entries                                              │
│  └── Opdater memory index                                                │
│                                                                          │
│  STEP 2: LOG ROTATION                                                    │
│  ├── Roter aktive log filer                                              │
│  ├── Komprimér gamle logs (.gz)                                          │
│  ├── Flyt til archive/                                                   │
│  └── Slet logs ældre end 30 dage                                         │
│                                                                          │
│  STEP 3: CACHE CLEAR                                                     │
│  ├── Redis: FLUSHDB (selektiv)                                           │
│  ├── File: rm -rf /tmp/cache/*                                           │
│  └── Memory: gc.collect()                                                │
│                                                                          │
│  STEP 4: INDEX OPTIMIZATION                                              │
│  ├── VACUUM ANALYZE (PostgreSQL)                                         │
│  ├── REINDEX (pgvector)                                                  │
│  └── Clear query cache                                                   │
│                                                                          │
│  STEP 5: RAPPORT                                                         │
│  ├── Generer audit rapport                                               │
│  ├── Log til SYNKRONISERING/                                             │
│  └── Notificer om anomalier                                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## IMPLEMENTATION NOTES

### Nuværende Status
- [x] Automatisering: KOMPLET (cron job + script)
- [x] Dokumentation: KOMPLET
- [x] Script: KOMPLET (sorting_0333.py)
- [x] Cron Job: INSTALLERET (33 3 * * *)
- [x] Logging: KOMPLET (/var/log/ckc/sorting_0333.log)
- [ ] Monitoring: CloudWatch integration (PENDING)
- [ ] Alerting: SNS notifications (PENDING)

### Implementerede Filer
```
scripts/sorting_0333.py       ← Main sorting script (~400 linjer)
scripts/setup_sorting_cron.sh ← Cron job installer
```

### Kommandoer
```bash
# Test (dry-run)
python scripts/sorting_0333.py --dry-run --verbose

# Live execution
python scripts/sorting_0333.py

# Install cron job
bash scripts/setup_sorting_cron.sh

# Se logs
tail -f /var/log/ckc/sorting_0333.log
```

### Test Output (2025-12-17)
```
Steps completed: 5/5
Duration: 0.06 seconds
Status: SUCCESS
```

### Næste Steps
1. ~~Opret cron job til 03:33~~ ✅ INSTALLERET
2. ~~Implementer cleanup script~~ ✅ sorting_0333.py
3. ~~Test fuld cycle~~ ✅ 5/5 steps SUCCESS
4. ~~Cron installation~~ ✅ Via setup_all_routines_cron.sh
5. Konfigurer CloudWatch alerting (FASE 4)
6. SNS email notifications (FASE 4)

### Relaterede Rutiner
- **09:00 Morning Sync** - Checker sorting rapport
- **21:21 Evening Opt** - Forbereder næste dags sorting

---

*Opdateret: 2025-12-17 10:00*
*Agent: Kommandør #4*
*Status: AKTIV + CRON INSTALLERET*
*Cron: 33 3 * * * (dagligt kl. 03:33)*
*Log: /var/log/ckc/sorting_0333.log*
