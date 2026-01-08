# GULDGULD FILER - INDEX
**Dato:** 2025-12-28
**Total:** 10 guldværdige dokumenter
**Version:** v2.4.0 - Individuelle mapper

---

## HVAD ER GULDGULD?

"GULDGULD" (Guld-Guld) er de mest værdifulde dokumenter i systemet.
Disse filer indeholder kerneinformation der skal bevares.

---

## OVERSIGT

| # | Mappe | Beskrivelse | Status |
|---|-------|-------------|--------|
| 81 | [81_DNA_LINEAGE_SYSTEM/](./81_DNA_LINEAGE_SYSTEM/81_DNA_LINEAGE_SYSTEM.md) | Agent arv og DNA | ✅ |
| 82 | [82_BASELINE_KOMPLET_2025_12_12/](./82_BASELINE_KOMPLET_2025_12_12/82_BASELINE_KOMPLET_2025_12_12.md) | Komplet baseline | ✅ |
| 83 | [83_SETUP_GUIDE/](./83_SETUP_GUIDE/83_SETUP_GUIDE.md) | Setup guide | ✅ |
| 84 | [84_TESTING_GUIDE/](./84_TESTING_GUIDE/84_TESTING_GUIDE.md) | Testing manual | ✅ |
| 85 | [85_TROUBLESHOOTING/](./85_TROUBLESHOOTING/85_TROUBLESHOOTING.md) | Fejlfinding | ✅ |
| 86 | [86_QUICK_REFERENCE/](./86_QUICK_REFERENCE/86_QUICK_REFERENCE.md) | Hurtig reference | ✅ |
| 87 | [87_AGENT_UDDANNELSE_MANUAL/](./87_AGENT_UDDANNELSE_MANUAL/87_AGENT_UDDANNELSE_MANUAL.md) | Uddannelse | ✅ |
| 88 | [88_AGENT_DNA_OVERBLIK/](./88_AGENT_DNA_OVERBLIK/88_AGENT_DNA_OVERBLIK.md) | DNA overblik | ✅ |
| 89 | [89_ECOSYSTEM_COMPLETE_GUIDE/](./89_ECOSYSTEM_COMPLETE_GUIDE/89_ECOSYSTEM_COMPLETE_GUIDE.md) | Økosystem guide | ✅ |
| 89B | [89B_CIRKELLINE_SYSTEM_ARCHITECTURE/](./89B_CIRKELLINE_SYSTEM_ARCHITECTURE/89B_CIRKELLINE_SYSTEM_ARCHITECTURE.md) | System arkitektur | ✅ |

---

## LÆSERÆKKEFØLGE

### For Overblik
1. `09_ECOSYSTEM_COMPLETE_GUIDE.md` - Samlet overblik
2. `10_CIRKELLINE_SYSTEM_ARCHITECTURE.md` - Teknisk arkitektur

### For Setup
1. `03_SETUP_GUIDE.md` - Installation
2. `06_QUICK_REFERENCE.md` - Hurtig reference

### For Agenter
1. `01_DNA_LINEAGE_SYSTEM.md` - Agent arv system
2. `07_AGENT_UDDANNELSE_MANUAL.md` - Uddannelse
3. `08_AGENT_DNA_OVERBLIK.md` - DNA detaljer

### For Problemer
1. `04_TESTING_GUIDE.md` - Test først
2. `05_TROUBLESHOOTING.md` - Løs problemer

---

## OPRINDELSE

Disse filer stammer fra `GULDGULD_FILER/` mappen i status rapport,
som samler de mest værdifulde dokumenter fra hele økosystemet.

---

## FEJLHÅNDTERING

### Problem 1: GULDGULD Outdated - Ancient Information

**Symptom:** GULDGULD dokument siger "Cirkelline har 9 agenter" men faktisk 21 agenter nu, eller architecture diagram viser gammelt system fra 2023

**Årsag:**
- GULDGULD oprettet i early days, aldrig opdateret
- "GULDGULD" betyder "værdifuld så rør den ikke" misfortolket som "freeze forever"
- Focus på nye features, glemte at opdatere legacy docs
- GULDGULD ikke del af regular review cycle

**Diagnosticering:**
```bash
# Check GULDGULD last updated
cat INTRO/80_GULDGULD/<8X_GULDGULD>/<FILE>.md | grep -i "dato\|updated\|version"

# Compare claims med current reality
cat INTRO/80_GULDGULD/88_AGENT_DNA_OVERBLIK/88_AGENT_DNA_OVERBLIK.md | grep -i "antal\|9\|21"

# Check faktisk agent count
ls -la ~/Desktop/projekts/projects/Kommandør-og-agenter/src/agent*/ | wc -l
cat INTRO/20_PROJEKTER/25_AGENTS/INDEX.md | grep "Total"

# Check architecture diagram vs reality
# GULDGULD shows: cirkelline-system → lib-admin → cosmic
# Reality check:
cat INTRO/10_ARKITEKTUR/10A_SYSTEM_ARCHITECTURE/10A_SYSTEM_ARCHITECTURE.md
```

**Fix:**
1. Identificer outdated information i GULDGULD:
   ```
   Claim: "9 agenter i systemet"
   Reality: 21 agenter (check 25_AGENTS)
   GAP: +12 agenter not documented

   Claim: "Database: cirkelline_db"
   Reality: Multiple databases (ckc_admin, cosmic_library, cirkelline)
   GAP: Architecture expanded
   ```
2. For each outdated claim:
   - Verificer current reality (check projekter, baselines, CLAUDE.md)
   - Update GULDGULD med facts
   - Add "UPDATED YYYY-MM-DD" note ved changed sections
3. Opdater GULDGULD metadata:
   ```markdown
   **Version:** 3.0.0 (was 1.0.0)
   **Last Updated:** 2026-01-08
   **Major Changes:**
   - Agent count: 9→21
   - Architecture: added 5 new projects
   - DNA system: 3 new DNA components
   ```
4. If major changes, consider deprecating old GULDGULD:
   ```bash
   # Hvis >50% af content outdated → deprecate
   mv INTRO/80_GULDGULD/<8X_OLD>/ INTRO/80_GULDGULD/_ARCHIVED_<8X_OLD>/
   # Create new updated version
   ```
5. Cross-reference med current docs:
   ```markdown
   **Note:** For current agent list, see `20_PROJEKTER/25_AGENTS/INDEX.md`
   **Note:** For current architecture, see `10_ARKITEKTUR/10A_SYSTEM_ARCHITECTURE`
   ```
6. Git commit: "GULDGULD UPDATED: <file> - refreshed to 2026 reality (9→21 agents, architecture expanded)"

**Prevention:**
- GULDGULD not sacred (kan opdateres som andre docs)
- Annual GULDGULD review: verify claims vs current system
- Link GULDGULD til canonical sources (baselines, projekter) for facts
- Version metadata required i all GULDGULD files

---

### Problem 2: GULDGULD Conflicts Med Current Docs

**Symptom:** GULDGULD says "lib-admin port 7777" men 15_MILJOER says port 7779, eller GULDGULD architecture diagram shows old structure men 10_ARKITEKTUR shows new structure

**Årsag:**
- GULDGULD written early, never synchronized med nye docs
- Multiple sources of truth ikke aligned
- GULDGULD assumed authoritative men actually outdated
- Infrastructure changes ikke reflected i GULDGULD

**Diagnosticering:**
```bash
# Extract facts fra GULDGULD
cat INTRO/80_GULDGULD/<8X>/<FILE>.md | grep -i "port\|database\|projekt"

# Compare med canonical sources
# For ports:
cat INTRO/15_MILJOER/15C_PORT_MAPPING/15C_PORT_MAPPING.md | grep "lib-admin"

# For architecture:
cat INTRO/10_ARKITEKTUR/10A_SYSTEM_ARCHITECTURE/10A_SYSTEM_ARCHITECTURE.md

# For projekter:
cat INTRO/20_PROJEKTER/20_PROJEKTER.md

# For baselines:
cat INTRO/40_BASELINES/<XX_BASELINE>/<XX_BASELINE>.md

# Identify conflicts
diff <(grep "port" INTRO/80_GULDGULD/<8X>/<FILE>.md) \
     <(grep "port" INTRO/15_MILJOER/15_MILJOER.md)
```

**Fix:**
1. Establish canonical source of truth for each topic:
   - Ports/Environment: `15_MILJOER/` (AUTHORITATIVE)
   - Architecture: `10_ARKITEKTUR/` (AUTHORITATIVE)
   - Projekter: `20_PROJEKTER/` (AUTHORITATIVE)
   - Baselines: `40_BASELINES/` (AUTHORITATIVE)
   - GULDGULD: High-level summaries (NOT source of truth)
2. Reposition GULDGULD as **summaries** not **canonical sources**:
   ```markdown
   # Agent DNA Overblik (SUMMARY)

   **For complete details, see:**
   - Agent list: `20_PROJEKTER/25_AGENTS/`
   - DNA specifications: `10_ARKITEKTUR/10B_DNA_SYSTEM/`

   ## Quick Summary (as of 2026-01-08)
   - Total agenter: 21 (verified with 25_AGENTS)
   - Primary DNA components: [list]
   ```
3. Update GULDGULD med cross-references:
   ```markdown
   **Port Configuration** (see `15_MILJOER/15C_PORT_MAPPING` for complete details)
   - lib-admin: 7779
   - cosmic-library: 7778
   - commando-center: 8090
   ```
4. Remove conflicting details from GULDGULD:
   - Keep high-level concepts
   - Remove specific ports/databases/counts
   - Link til canonical sources for specifics
5. Add disclaimer at top of GULDGULD files:
   ```markdown
   > **Note:** This is a high-level summary. For current details, see linked sections.
   > **Last Verified:** 2026-01-08
   ```
6. Git commit: "GULDGULD REALIGNED: <file> - cross-referenced with canonical sources, removed conflicts"

**Prevention:**
- GULDGULD = summaries only, NOT source of truth
- All specific facts link til canonical sources (15_MILJOER, 20_PROJEKTER, etc.)
- GULDGULD review includes cross-reference validation
- Template: "For details, see X" pattern

---

### Problem 3: GULDGULD Duplicates Other Docs - Maintenance Burden

**Symptom:** Same information exists in both GULDGULD and BASELINES, or GULDGULD/GUIDES/CLAUDE.md all have setup instructions, causing confusion about which is correct

**Årsag:**
- GULDGULD created early as "all-in-one" doc
- Later, more organized system created (BASELINES, GUIDES, etc.)
- Old GULDGULD ikke cleaned up efter new structure
- Multiple maintainers ikke aware of duplication

**Diagnosticering:**
```bash
# Find duplicate content
# Example: Setup instructions
grep -r "npm install" INTRO/80_GULDGULD/
grep -r "npm install" INTRO/70_GUIDES/
grep -r "npm install" INTRO/60_CLAUDE_MD/

# Compare baseline info
diff <(cat INTRO/80_GULDGULD/82_BASELINE_KOMPLET_2025_12_12/*.md | head -50) \
     <(cat INTRO/40_BASELINES/<XX_BASELINE>/<XX_BASELINE>.md | head -50)

# Find similar headings (indicates duplication)
grep -r "^## Setup" INTRO/80_GULDGULD/
grep -r "^## Setup" INTRO/70_GUIDES/

# Check file sizes (large GULDGULD may contain duplicates)
find INTRO/80_GULDGULD/ -name "*.md" -exec wc -l {} \; | sort -rn
```

**Fix:**
1. Audit GULDGULD for duplicate content:
   ```
   GULDGULD has:
   - Setup instructions (also in 70_GUIDES/71_SETUP)
   - Baseline data (also in 40_BASELINES)
   - Testing guide (also in 70_GUIDES/72_TESTING)
   - Architecture (also in 10_ARKITEKTUR)
   ```
2. Decide role for each section:
   - **GULDGULD:** High-level overview + historical context
   - **GUIDES:** Step-by-step instructions
   - **BASELINES:** Current project state
   - **ARKITEKTUR:** System design
3. Remove duplicate details fra GULDGULD, replace med links:
   ```markdown
   ## Setup (MOVED)
   Setup instructions have moved to `70_GUIDES/71_SETUP/`.
   For quick start, see `70_GUIDES/71_SETUP/lib-admin_QUICKSTART.md`.

   ### Historical Context
   [Keep unique historical info that doesn't exist elsewhere]
   ```
4. Update GULDGULD to focus på:
   - Historical evolution (hvordan kom vi hertil)
   - High-level concepts (DNA system philosophy)
   - Cross-project patterns (hvordan alle projekter hænger sammen)
   - Strategic vision (hvor skal vi hen)
5. Archive deprecated GULDGULD:
   ```bash
   # If GULDGULD content 100% duplicated elsewhere
   mv INTRO/80_GULDGULD/<8X_DUPLICATE>/ \
      INTRO/80_GULDGULD/_ARCHIVED_<8X_DUPLICATE>/
   # Add README: "Content moved to XX_FOLDER - see links"
   ```
6. Update 80_GULDGULD.md index with clear purpose:
   ```markdown
   ## HVAD ER GULDGULD?
   **Purpose:** Historical context, high-level concepts, strategic vision
   **NOT for:** Current details (see BASELINES), step-by-step (see GUIDES), specific configs (see MILJOER)
   ```
7. Git commit: "GULDGULD DEDUPLICATED: removed duplicates, focused on high-level + historical"

**Prevention:**
- Clear separation of concerns: GULDGULD = concepts, other folders = specifics
- Before adding to GULDGULD: check if info already in other folders
- GULDGULD creation guideline: "Does this exist elsewhere? If yes, link instead"
- Quarterly deduplication review

---

## ÆNDRINGSLOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2025-12-27 | - | GULDGULD index oprettet | Claude |
| 2025-12-28 | 21:38 | ÆNDRINGSLOG sektion tilføjet | Claude |
| 2025-12-28 | 22:15 | Filnavne standardiseret (bindestreger → underscore) | Claude |
| 2025-12-28 | 22:15 | 5 mapper + filer renamed til XX_NAVN format | Claude |
| 2026-01-08 | 12:20 | FEJLHÅNDTERING tilføjet (3 problems: outdated GULDGULD, conflicts with current docs, duplicates) | Claude |

---

*80_GULDGULD.md - Opdateret 2026-01-08 12:20*
