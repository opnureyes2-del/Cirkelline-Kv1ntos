# 30_TODOS - OPGAVE & TASK TRACKING SYSTEM

**Version:** v1.0.0
**Dato:** 2026-01-08
**Sidst Opdateret:** 2026-01-08 00:50
**Status:** AKTIV SYSTEM

---

## FORMÅL

**30_TODOS** er det centrale system for opgave tracking, prioritering og progress monitoring på tværs af ALLE projekter og initiativer.

**Hovedfunktioner:**
- Central TODO liste koordinering
- Task prioritering (P0 Kritiske, P1 Vigtige, P2 Normale)
- Progress tracking og metrics
- Dependency mapping
- Master opgave oversigt (DNA KOMPLET TODO)

---

## STRUKTUR OVERSIGT

| Mappe/Fil | Formål | Status |
|-----------|--------|--------|
| **31_MASTER_TODO/** | Master TODO koordinering | ✅ AKTIV |
| **34_TODO_P0_KRITISKE/** | P0 kritiske opgaver | ✅ AKTIV |
| **35_TODO_P1_VIGTIGE/** | P1 vigtige opgaver | ✅ AKTIV |
| **36_TODO_P2_NORMALE/** | P2 normale opgaver | ✅ AKTIV |
| **37_PLAN_TIDSLOG_DATOLOG/** | Tidslog og planlægning | ✅ AKTIV |
| **39_DNA_KOMPLET_TODO/** | Master oversigt (147 tasks) | ✅ AKTIV |
| **40_ELLE_BASELINE_TODO/** | ELLE baseline tasks | ✅ AKTIV |
| 30_INDEX.md | Navigation og links | ✅ KOMPLET |
| 30_FOLDER_TEMPLATE.md | Template documentation | ✅ KOMPLET |
| 38_INTRO_CLEANUP_TODO.md | INTRO cleanup tasks | ✅ KOMPLET |
| 93_ÅBNE_OPGAVER_TRACKING.md | Åbne opgaver tracking | ✅ KOMPLET |
| SYNKRONISERET_TODO_OVERSIGT.md | Synkroniseret oversigt | ✅ KOMPLET |

---

## PRIORITERINGS SYSTEM

### P0 - KRITISKE (Must Have)
**Definition:** Blokerende opgaver der SKAL løses NU.

**Karakteristika:**
- System er brudt uden denne opgave
- Blokerer alt andet arbejde
- Deadline: ASAP (typisk samme dag)
- Review: Dagligt

**Location:** `34_TODO_P0_KRITISKE/`

**Eksempler:**
- Database er nede → fix NU
- Security vulnerability → patch NU
- Production blocker → resolve NU

---

### P1 - VIGTIGE (Should Have)
**Definition:** Kritiske features eller fixes der skal løses denne uge.

**Karakteristika:**
- Høj prioritet men ikke blokerende
- Påvirker produktivitet/brugeroplevelse
- Deadline: Denne uge
- Review: 2x ugentligt

**Location:** `35_TODO_P1_VIGTIGE/`

**Eksempler:**
- SSO Gateway test
- Database migrations
- Agent deployment

---

### P2 - NORMALE (Could Have)
**Definition:** Standard features og forbedringer.

**Karakteristika:**
- Normale prioritet
- Kan vente hvis nødvendigt
- Deadline: Næste 2-4 uger
- Review: Ugentligt

**Location:** `36_TODO_P2_NORMALE/`

**Eksempler:**
- UI polish
- Documentation updates
- Performance optimization

---

## DNA KOMPLET TODO (Master Liste)

**Location:** `39_DNA_KOMPLET_TODO/39_DNA_KOMPLET_TODO.md`

**Statistik:**
- **Total opgaver:** 147
- **Prioritering:**
  - P0: 3 (alle løst ✅)
  - P1: 11 (9 løst, 2 åbne)
  - P2: 13 (1 løst, 12 åbne)
  - Andre: 120+

**Formål:**
Master TODO liste der fungerer som single source of truth for ALT arbejde.

**Sections:**
- ZRAM/Memory optimization
- Database integration
- Agent training system
- API documentation
- Platform integration
- Performance audits

---

## WORKFLOW

### 1. Opgave Oprettelse

**Ny opgave skal:**
1. Tildeles prioritet (P0/P1/P2)
2. Have ejer defineret
3. Have acceptkriterier
4. Have estimat
5. Dokumenteres i korrekt TODO fil

**Template:**
```markdown
### PX-Y: [Opgave titel]
**Status:** ⚪ IKKE STARTET
**Prioritet:** PX
**Estimat:** X timer
**Deadline:** YYYY-MM-DD
**Ejer:** [Person]

**Beskrivelse:**
[Hvad skal gøres]

**Acceptkriterier:**
- [ ] Kriterium 1
- [ ] Kriterium 2
```

### 2. Opgave Tracking

**Status værdier:**
- ⚪ IKKE STARTET - Opgave ikke påbegyndt
- ⏳ IGANGVÆRENDE - Arbejder aktivt på opgaven
- 🔴 BLOKERET - Venter på dependency eller blocker
- ✅ LØST - Komplet og verificeret

**Update frekvens:**
- P0: Dagligt (eller oftere)
- P1: 2x ugentligt
- P2: Ugentligt

### 3. Opgave Completion

**En opgave er LØST når:**
1. ✅ Alle acceptkriterier opfyldt
2. ✅ Tests passed (unit + integration + manual)
3. ✅ Code reviewed (hvis relevant)
4. ✅ Dokumentation opdateret
5. ✅ Deployment verified (hvis relevant)
6. ✅ STATUS opdateret til ✅ LØST

**VIGTIG:** Opdater STATUS.md SAMME DAG opgave løses!

---

## SYNKRONISERING

### Krydsreferencer

TODO systemet synkroniserer med:

| System | Location | Sync Frequency |
|--------|----------|----------------|
| EKSEKVERINGSPLAN | `00_EKSEKVERINGSPLAN.md` | Dagligt |
| BASELINES | `40_BASELINES/` | Ved completion |
| ROADMAPS | `50_ROADMAPS/` | Ugentligt |
| Session Logs | `00_SESSION_LOGS/` | Hver session |

### Automatisk Synkronisering

**Script:** `scripts/sync_todos.py` (planlagt)

**Funktionalitet:**
- Scan alle TODO filer
- Opdater EKSEKVERINGSPLAN metrics
- Check dependencies
- Generate progress reports

---

## METRICS & REPORTING

### Daglig Rapport

**Location:** Genereres automatisk i session logs

**Indeholder:**
- P0 tasks status
- P1 tasks at risk
- Overall progress %
- Blockers identified

### Ugentlig Rapport

**Location:** `37_PLAN_TIDSLOG_DATOLOG/`

**Indeholder:**
- Tasks completed this week
- Tasks planned next week
- Velocity metrics
- Team capacity

---

## BEST PRACTICES

### DO ✅

1. **Opdater STATUS umiddelbart** når opgave status ændres
2. **Link dependencies** eksplicit i opgave beskrivelse
3. **Dokumenter blockers** med konkret årsag
4. **Estimer realistisk** baseret på historisk data
5. **Verificer completion** med fysisk test før marking ✅
6. **Synkroniser dagligt** mellem TODO og EKSEKVERINGSPLAN

### DON'T ❌

1. **Marker LØST uden verification** - Always test first
2. **Spring prioritet** - P0 før P1 før P2
3. **Glem dependencies** - Track hvad blokerer hvad
4. **Lad opgaver hænge** - Update eller delete stale tasks
5. **Duplikere opgaver** - Én master TODO (DNA KOMPLET)
6. **Ignorer blockers** - Adresser blockers eksplicit

---

## SYSTEM DOKUMENTATION

### Formål
**30_TODOS** løser opgave chaos ved at centralisere ALL task tracking på tværs af projekter med klar prioritering (P0/P1/P2) og verification workflows.

**Problemer det løser:**
- Opgaver glemt eller tabt mellem projekter
- Uklare prioriteter ("alt er vigtigt")
- Ingen central overview af hvad der skal laves
- Duplikerede opgaver på tværs af systemer
- Manglende verification før marking complete

### Workflow

**1. Ny Opgave Registrering:**
```bash
# Opret ny opgave i relevant prioritet folder
cd 30_TODOS/34_TODO_P0_KRITISKE  # eller P1/P2
# Opret fil: OPGAVE_BESKRIVELSE.md
# Tilføj til 31_MASTER_TODO liste
```

**2. Daglig Review (P0):**
- Check 34_TODO_P0_KRITISKE folder
- Adresser blokerende opgaver FØRST
- Update status i MASTER_TODO
- Synkroniser med EKSEKVERINGSPLAN

**3. Ugentlig Review (P1/P2):**
- Review 35_TODO_P1_VIGTIGE
- Review 36_TODO_P2_NORMALE
- Re-prioriter hvis nødvendigt
- Archive completede tasks

**4. Opgave Completion:**
```bash
# Step 1: Verify fysisk
[run tests, check files, verify deployment]

# Step 2: Update STATUS.md
echo "STATUS: ✅ LØST" >> STATUS.md

# Step 3: Update MASTER_TODO
# Mark completed i 31_MASTER_TODO

# Step 4: Git commit
git add .
git commit -m "TASK COMPLETE: [beskrivelse] + verification"
git push
```

**5. Synkronisering:**
- 30_TODOS ↔ EKSEKVERINGSPLAN (daily)
- STATUS.md ↔ MASTER_TODO (after each update)
- Local tasks ↔ DNA KOMPLET TODO (weekly)

### Input/Output

**Input:**
- Nye opgaver fra projekter
- Status updates fra udvikling
- Prioritet ændringer fra Rasmus/Ivo
- Dependency information
- Blocker reports

**Output:**
- Prioriterede TODO lister (P0/P1/P2)
- MASTER_TODO koordineret liste
- DNA_KOMPLET_TODO master oversigt (147 tasks)
- Progress metrics og statistics
- STATUS.md verification states

### Validation

**Hvordan verificerer man at TODO systemet virker?**

```bash
# Check P0 opgaver eksisterer og er tracked
ls -la 30_TODOS/34_TODO_P0_KRITISKE/
grep "P0:" 30_TODOS/31_MASTER_TODO/*.md | wc -l

# Check P1 opgaver tracked
ls -la 30_TODOS/35_TODO_P1_VIGTIGE/
grep "P1:" 30_TODOS/31_MASTER_TODO/*.md | wc -l

# Check DNA KOMPLET TODO exists
wc -l 30_TODOS/39_DNA_KOMPLET_TODO/39_DNA_KOMPLET_TODO.md
# Should be ~400+ lines with 147 tasks

# Check MASTER_TODO sync
grep "STATUS:" 30_TODOS/31_MASTER_TODO/*.md

# Verify completed tasks marked correctly
grep "✅ LØST" 30_TODOS/**/*.md | wc -l

# Check for stale tasks (older than 2 weeks without update)
find 30_TODOS -name "*.md" -mtime +14

# Verification output:
# ✅ P0: X tasks (should be 0-3, low means good prioritization)
# ✅ P1: Y tasks (should be 5-15)
# ✅ P2: Z tasks (backlog can be larger)
# ✅ Completed: N tasks marked LØST
# ✅ DNA KOMPLET: 147 tasks tracked
```

### Integration

**30_TODOS forbinder med:**

1. **00_EKSEKVERINGSPLAN.md:**
   - TODO systemet synkroniseres med execution plan daily
   - P0 tasks fra TODO → prioriteres i execution plan
   - Completed tasks → fjernes fra execution plan

2. **39_DNA_KOMPLET_TODO:**
   - Master liste af ALLE 147 tasks
   - Synkroniseres med sub-TODO lists (P0/P1/P2)
   - Single source of truth for total scope

3. **31_MASTER_TODO:**
   - Central koordinering mellem priority levels
   - Cross-references mellem P0/P1/P2 folders
   - Dependency tracking

4. **STATUS.md Files (Alle Projekter):**
   - Hver projekt STATUS.md → feeds tasks til 30_TODOS
   - 30_TODOS status → updates sent til projekt STATUS
   - Two-way sync maintained

5. **INTRO/00_SESSION_LOGS:**
   - TODO decisions dokumenteret i session logs
   - Priority changes logged
   - Archive af completed task reports

**Data flow:**
```
Project STATUS.md
    ↓
30_TODOS (central)
    ↓
Prioritized (P0/P1/P2)
    ↓
MASTER_TODO (coordination)
    ↓
DNA_KOMPLET_TODO (147 tasks master list)
    ↓
EKSEKVERINGSPLAN (execution)
    ↓
Session Logs (archive)
```

---

## FEJLHÅNDTERING

### Problem 1: Opgave Markeret som LØST Men Ikke Verificeret

**Symptom:** Opgave har status ✅ LØST men tests fejler, dokumentation mangler, eller deployment ikke verificeret

**Årsag:**
- Markeret complete før verification
- Antagelse om success uden physical check
- Glemt verification step

**Diagnosticering:**
```bash
# Check om opgave er markeret som LØST
$ grep "✅ LØST" 39_DNA_KOMPLET_TODO/39_DNA_KOMPLET_TODO.md

# Verificer at filen/feature faktisk eksisterer
$ ls -la [fil som skulle være oprettet]

# Check git commits for opgaven
$ git log --grep="[opgave ID]" --oneline
```

**Fix:**
1. Identificer hvad der ikke er verificeret (tests? docs? deployment?)
2. Marker opgave tilbage til ⏳ IGANGVÆRENDE
3. Tilføj blocker note med specifik årsag:
   ```markdown
   **Blocker:** Tests not run, deployment not verified
   ```
4. Udfør manglende verification
5. Opdater STATUS.md samme dag med korrekt status
6. Kun marker ✅ LØST når ALT er verificeret

**Prevention:**
- Brug ALTID verification checklist før marking LØST
- Kør physical checks (tests, ls, curl, etc.)
- Opdater EKSEKVERINGSPLAN samme dag
- Commit bevis (git hash) sammen med completion

---

### Problem 2: Opgave Blokeret i Flere Uger

**Symptom:** Opgave har status 🔴 BLOKERET og har ikke bevæget sig i 2+ uger

**Årsag:**
- Dependency ikke løst
- Ressourcer ikke tilgængelige
- Vent på ekstern part
- Glemt eller nedprioriteret

**Diagnosticering:**
```bash
# Find alle blokerede opgaver
$ grep "🔴 BLOKERET" 39_DNA_KOMPLET_TODO/39_DNA_KOMPLET_TODO.md

# Check hvor længe opgaven har været blokeret
$ git log -p --grep="BLOKERET" -- 39_DNA_KOMPLET_TODO/39_DNA_KOMPLET_TODO.md

# Check om blocker stadig eksisterer
$ [command til at verificere blocker - fx curl, ls, etc]
```

**Fix:**
1. **Dokumenter blocker eksplicit:**
   ```markdown
   **Blocker:** Venter på database migration (P1-2)
   **Ejer af blocker:** [Person]
   **Forventet løst:** [Dato]
   ```
2. **Vurder om opgave skal re-prioriteres:**
   - Hvis blocker ikke løses snart: Nedpriorité til P2
   - Hvis blocker kritisk: Eskalér blocker til P0
3. **Find alternativ løsning:**
   - Kan opgaven deles op?
   - Kan workaround implementeres?
4. **Opdater deadline realistisk:**
   - Beregn ny deadline baseret på blocker status
5. **Track blocker aktivt:**
   - Tilføj til ugentlig review
   - Ping blocker ejer hver uge

**Prevention:**
- Review blokerede opgaver hver uge (ikke lad dem ligge)
- Dokumentér blocker ejer og expected resolution date
- Eskalér hvis blocker ikke løses inden 2 uger
- Tilføj blocker til priority meetings

---

### Problem 3: Duplikerede Opgaver På Tværs af TODO Lister

**Symptom:** Samme opgave findes i både P1 liste og DNA KOMPLET TODO, eller i projekt TODO og master TODO

**Årsag:**
- Manglende synkronisering mellem lister
- Forskellige personer opretter samme opgave
- Copy/paste fejl
- Manglende central tracking

**Diagnosticering:**
```bash
# Søg efter duplicates med nøgleord
$ grep -r "SSO Gateway" 30_TODOS/

# Check om opgave ID duplikeret
$ grep -r "P1-5" 30_TODOS/ 39_DNA_KOMPLET_TODO/

# Find filer sidst modificeret (mulig duplicate oprettelse)
$ find 30_TODOS/ -name "*.md" -mtime -7 -exec grep -l "opgave navn" {} \;
```

**Fix:**
1. **Identificer master opgave:**
   - DNA KOMPLET TODO er single source of truth
   - Andre lister linker TIL DNA KOMPLET, ikke duplikerer
2. **Slet duplikater:**
   ```bash
   # Backup før sletning
   $ cp 35_TODO_P1_VIGTIGE/35_TODO_P1_VIGTIGE.md{,.backup}

   # Slet duplicate entry manuelt eller via script
   ```
3. **Opret link i stedet:**
   ```markdown
   ### P1-5: SSO Gateway Test
   **Reference:** Se DNA KOMPLET TODO P1-5 (linje 234)
   **Link:** [39_DNA_KOMPLET_TODO.md](../39_DNA_KOMPLET_TODO/39_DNA_KOMPLET_TODO.md)
   ```
4. **Synkroniser status:**
   - Opdater master TODO
   - Links reflekterer automatisk opdateringer
5. **Verificer ingen flere duplicates:**
   ```bash
   $ grep -r "[opgave navn]" 30_TODOS/ | wc -l
   # Skal være 1 (kun i DNA KOMPLET TODO)
   ```

**Prevention:**
- DNA KOMPLET TODO = single source of truth
- Andre lister linker til DNA KOMPLET, duplikerer IKKE
- Run duplicate check script ugentligt
- Code review for nye opgaver (check for duplicates)

---

### Problem 4: STATUS.md Ikke Synkroniseret Med Faktisk Progress

**Symptom:** STATUS.md viser "10/10 complete" men physical verification finder manglende filer eller fejl

**Årsag:**
- STATUS opdateret uden verification
- Optimistisk marking without checks
- Glemt at opdatere efter ændringer
- Ingen automated validation

**Diagnosticering:**
```bash
# Check STATUS claims
$ grep "Komplet" 30_TODOS/_TODO_VERIFIKATION/STATUS.md

# Verificer physically om det passer
$ ls 30_TODOS/39_DNA_KOMPLET_TODO/39_DNA_KOMPLET_TODO.md
$ wc -l 30_TODOS/39_DNA_KOMPLET_TODO/39_DNA_KOMPLET_TODO.md

# Check for empty files (false positives)
$ find 30_TODOS/ -name "*.md" -size 0

# Check for recent modifications (mulig incomplete work)
$ find 30_TODOS/ -name "*.md" -mtime -1
```

**Fix:**
1. **Run physical verification:**
   ```bash
   # Create verification script
   $ cat > /tmp/verify_todos.sh << 'EOF'
   #!/bin/bash
   for file in 31_MASTER_TODO 34_TODO_P0_KRITISKE 35_TODO_P1_VIGTIGE 36_TODO_P2_NORMALE 39_DNA_KOMPLET_TODO 40_ELLE_BASELINE_TODO; do
       main="${file}/${file}.md"
       if [ -f "30_TODOS/$main" ] && [ $(wc -l < "30_TODOS/$main") -gt 10 ]; then
           echo "✅ $file"
       else
           echo "❌ $file - MISSING or INCOMPLETE"
       fi
   done
   EOF

   $ bash /tmp/verify_todos.sh
   ```
2. **Opdater STATUS.md baseret på facts:**
   - Marker incomplete items som ❌
   - Tilføj notes om hvad der mangler
   - Opdater completion percentage realistisk
3. **Fix faktiske mangler først, derefter opdater STATUS:**
   - Ikke omvendt!
4. **Add timestamp til hver STATUS update:**
   ```markdown
   | 2026-01-08 | 01:30 | Physical verification run - 9/10 complete | Elle |
   ```

**Prevention:**
- Run physical verification BEFORE opdatering af STATUS
- Never assume completion - always verify
- Automated validation script run dagligt
- STATUS.md last modified date skal matche verification date

---

### Problem 5: P0 Opgave Ikke Løst Inden Deadline

**Symptom:** P0 (kritisk) opgave stadig åben efter deadline passeret, system muligvis brudt

**Årsag:**
- Underestimeret kompleksitet
- Uventede blockers
- Ressource mangel
- Tekniske problemer
- Manglende escalation

**Diagnosticering:**
```bash
# Find alle P0 opgaver
$ grep -A 5 "P0-" 34_TODO_P0_KRITISKE/34_TODO_P0_KRITISKE.md

# Check deadline
$ grep "Deadline:" 34_TODO_P0_KRITISKE/34_TODO_P0_KRITISKE.md

# Sammenlign med dagens dato
$ date +%Y-%m-%d

# Check om system faktisk er brudt
$ curl -f http://localhost:[port] || echo "❌ SYSTEM DOWN"
$ docker ps | grep [service] || echo "❌ SERVICE DOWN"
```

**Fix:**

**IMMEDIATE (< 1 time):**
1. **Triage:**
   - Er systemet FAKTISK brudt? (curl, ps, logs)
   - Hvor mange brugere påvirket?
   - Findes workaround?
2. **Eskalér STRAKS:**
   - Notify team lead
   - Update task status med criticality note
   - Block all other work until resolved
3. **Kommunikér:**
   ```markdown
   **CRITICAL:** P0-3 missed deadline, system degraded
   **Impact:** [antal brugere/services påvirket]
   **ETA:** [realistisk estimate]
   **Workaround:** [hvis findes]
   ```

**SHORT TERM (samme dag):**
4. **Root cause analysis:**
   - Hvorfor blev deadline missed?
   - Var estimat realistisk?
   - Var der blockers?
5. **Implementer quick fix eller workaround**
6. **Opdater deadline realistisk:**
   - Baseret på actual remaining work
   - Add buffer for unexpected issues
7. **Daily status updates:**
   - Update STATUS.md 2x per dag minimum
   - Notify stakeholders hver morgen/aften

**LONG TERM (denne uge):**
8. **Prevent recurrence:**
   - Add buffer til P0 estimates (2x original)
   - Daily standup for P0 tasks
   - Early warning system (50% complete by 50% time)
   - Automated monitoring + alerts

**Prevention:**
- P0 tasks review DAGLIGT (ikke ugen tly)
- 50% checkpoint: If not 50% complete by 50% time → eskalér
- Always have plan B (workaround/rollback)
- Daily standup for active P0 tasks
- Automated monitoring for P0 task deadlines
- Block calendar for P0 work (no distractions)

---

## RELATEREDE DOKUMENTER

- [00_EKSEKVERINGSPLAN.md](../00_EKSEKVERINGSPLAN.md) - Execution order
- [39_DNA_KOMPLET_TODO](./39_DNA_KOMPLET_TODO/39_DNA_KOMPLET_TODO.md) - Master TODO
- [40_BASELINES](../40_BASELINES/40_INDEX.md) - Current state
- [50_ROADMAPS](../50_ROADMAPS/50_INDEX.md) - Future plans
- [06_TEMPLATE_INTRO](../06_TEMPLATE_INTRO/06_TEMPLATE_INTRO.md) - Template standard

---

## ÆNDRINGSLOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2026-01-08 | 01:35 | FEJLHÅNDTERING sektion tilføjet (5 common problems + fixes) | Elle |
| 2026-01-08 | 00:50 | 30_TODOS.md oprettet - komplet hovedfil | Elle |
| 2026-01-07 | 22:24 | 30_FOLDER_TEMPLATE.md oprettet | Elle |
| 2026-01-07 | 22:42 | 30_INDEX.md opdateret | Elle |

---

*30_TODOS.md - Opdateret 2026-01-08 01:35*
