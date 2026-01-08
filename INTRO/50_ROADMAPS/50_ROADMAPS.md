# ROADMAPS - INDEX
**Dato:** 2025-12-28
**Version:** v2.4.0 - Individuelle mapper

---

## OVERSIGT

| # | Mappe | Projekt | Status |
|---|-------|---------|--------|
| 51 | [51_MASTER_ROADMAP/](./51_MASTER_ROADMAP/51_MASTER_ROADMAP.md) | Master Roadmap | ✅ |
| 52 | [52_FREMTIDSPLAN/](./52_FREMTIDSPLAN/52_FREMTIDSPLAN.md) | Fremtidsplan | ✅ |
| 53 | [53_lib-admin_ROADMAP/](./53_lib-admin_ROADMAP/53_lib-admin_ROADMAP.md) | lib-admin | ✅ |
| 54 | [54_cosmic-library_ROADMAP/](./54_cosmic-library_ROADMAP/54_cosmic-library_ROADMAP.md) | Cosmic Library | ✅ |
| 55 | [55_commando-center_ROADMAP/](./55_commando-center_ROADMAP/55_commando-center_ROADMAP.md) | Commando Center | ✅ |
| 56 | [56_consulting_ROADMAP/](./56_consulting_ROADMAP/56_consulting_ROADMAP.md) | Consulting | ✅ |
| 57 | [57_kommandor_ROADMAP/](./57_kommandor_ROADMAP/57_kommandor_ROADMAP.md) | Kommandør | ✅ |
| 58 | [58_commander_ROADMAP/](./58_commander_ROADMAP/58_commander_ROADMAP.md) | Commander | ✅ |

---

## OVERORDNET ROADMAP

### Q1 2025
1. Fix P0 kritiske problemer
2. Komplet SSO Gateway integration
3. Database migrations verificeret

### Q2 2025
1. Agent deployment pipeline
2. Produktion miljøer opsæt
3. Cross-platform monitoring

### Q3 2025
1. Mobile app lancering
2. Fuld platform integration
3. Performance optimering

---

## FEJLHÅNDTERING

### Problem 1: Roadmap Outdated - Ikke Synced Med Realitet

**Symptom:** Roadmap viser "Q1 2025: Fix P0 problemer" men vi er i 2026 og roadmap aldrig opdateret, eller roadmap siger "Launch feature X i Q2" men feature blev cancelled

**Årsag:**
- Roadmap oprettet men aldrig maintained
- Prioriteter ændrede sig men roadmap ikke revideret
- Projekter delayed/cancelled men roadmap ikke opdateret
- Copy-paste fra gammel roadmap uden dates opdateret

**Diagnosticering:**
```bash
# Check roadmap dates
cat INTRO/50_ROADMAPS/<XX_ROADMAP>/<XX_ROADMAP>.md | grep -i "Q[1-4]\|202[0-9]"

# Check nuværende dato
date "+%Y-%m-%d"

# Sammenlign roadmap claims med faktisk delivery
cat INTRO/50_ROADMAPS/<XX_ROADMAP>/<XX_ROADMAP>.md | grep -A5 "Q1 2025"
# Så check om disse features faktisk blev delivered:
ls -la ~/Desktop/projekts/projects/<projekt>/

# Check CHANGELOG for actual delivery dates
cat INTRO/05_CHANGELOG.md | grep "<feature>"

# Check baseline for current state
cat INTRO/40_BASELINES/<XX_BASELINE>/<XX_BASELINE>.md | grep -i "status\|procent"
```

**Fix:**
1. Identificer hvilket quarter/year vi er i nu
2. Review roadmap fra start til nu:
   - Hvilke Q1/Q2/Q3/Q4 milestones blev delivered?
   - Hvilke blev delayed?
   - Hvilke blev cancelled?
3. Opdater historical quarters med faktiske resultater:
   ```markdown
   ### Q1 2025 (COMPLETED)
   ✅ Fixed 8/12 P0 problemer
   ❌ SSO Gateway delayed til Q2
   ```
4. Revision future quarters baseret på current state:
   - Check baseline procent → realistic next milestones
   - Check P0/P1 priorities → adjust roadmap priorities
   - Update dates if delayed
5. Tilføj ÆNDRINGSLOG entry: "Roadmap updated: Q1-Q2 2025 actual results, Q3-Q4 2026 revised"
6. Git commit med before/after comparison

**Prevention:**
- Quarterly roadmap review (every 3 months)
- Link roadmap update til baseline update workflow
- Automated reminder: if roadmap last updated > 6 months → flag for review
- Roadmap revision i 00_UDVIKLINGSPLAN.md Fase 6

---

### Problem 2: Roadmap Conflicts Med Baseline - Unrealistisk Plan

**Symptom:** Roadmap siger "Q3 2025: Launch mobile app" men baseline viser projekt kun 20% komplet, eller roadmap planlægger "Q2: Production deployment" men kendte P0 bugs ikke fixed

**Årsag:**
- Roadmap lavet uden at check baseline current state
- Optimistisk planlægning ikke baseret på facts
- Roadmap copy-pasted fra andet projekt
- Baseline opdateret men roadmap ikke adjusted

**Diagnosticering:**
```bash
# Check roadmap next milestone
cat INTRO/50_ROADMAPS/<XX_ROADMAP>/<XX_ROADMAP>.md | grep -A10 "Q[1-4] 202[0-9]" | head -20

# Check baseline current completion %
cat INTRO/40_BASELINES/<XX_BASELINE>/<XX_BASELINE>.md | grep -i "procent\|total"
cat INTRO/40_BASELINES/40_BASELINES.md | grep "<projekt>"

# Check kendte problemer i baseline
cat INTRO/40_BASELINES/<XX_BASELINE>/<XX_BASELINE>.md | grep -A10 "Kendte problemer"

# Calculate gap
# If baseline = 20% complete, roadmap should not plan production launch next quarter
# Realistic: 20% → need 3-6 months to reach 80%+
```

**Fix:**
1. Compare roadmap milestones med baseline state:
   ```
   Roadmap says: "Q2 2026: Production launch"
   Baseline shows: 35% complete, 5 P0 bugs, no frontend
   Gap: UNREALISTIC
   ```
2. Identificer dependencies:
   - Hvilke features skal være færdige først?
   - Hvilke P0 bugs skal fixes?
   - Hvad er realistic completion rate per month?
3. Revidér roadmap baseret på baseline facts:
   ```markdown
   ### Q2 2026 (REVISED)
   - Fix 5 P0 bugs → reach 60% complete
   - Build minimal frontend MVP

   ### Q3 2026
   - Integration testing → reach 85% complete

   ### Q4 2026
   - Production launch (if Q2+Q3 milestones met)
   ```
4. Add realistic buffers (multiply estimates by 1.5x)
5. Tilføj ÆNDRINGSLOG: "Roadmap realigned with baseline (was unrealistic)"
6. Git commit med justification

**Prevention:**
- ALWAYS check baseline before writing roadmap
- Roadmap review when baseline % changes significantly
- Conservative estimates (add 50% buffer)
- Dependency tracking: block roadmap milestone until baseline dependencies met

---

### Problem 3: Roadmap Mangler For Projekt

**Symptom:** Projekt findes i `20_PROJEKTER/` og har baseline i `40_BASELINES/` men ingen roadmap i `50_ROADMAPS/`

**Årsag:**
- Projekt fokuseret på nuværende features, glemte fremtidsplan
- Roadmap creation ikke del af project setup workflow
- Eksperimentelt projekt blev permanent men roadmap ikke oprettet
- Copy-paste projekt men roadmap ikke tilpasset

**Diagnosticering:**
```bash
# List alle projekter
cat INTRO/20_PROJEKTER/20_PROJEKTER.md | grep "^|" | grep -v "^| #"

# List alle roadmaps
ls -la INTRO/50_ROADMAPS/ | grep "ROADMAP"

# Find projekter uden roadmap
for proj in lib-admin cosmic-library commando-center consulting kommandor commander; do
    if ! grep -q "$proj" INTRO/50_ROADMAPS/50_ROADMAPS.md; then
        echo "Missing roadmap: $proj"
    fi
done

# Check om projekt har baseline (indikerer det er etableret)
ls -la INTRO/40_BASELINES/ | grep "<projekt>"
```

**Fix:**
1. Verificer projekt er permanent og har fremtid (ikke deprecated)
2. Check baseline for current state:
   ```bash
   cat INTRO/40_BASELINES/<XX_BASELINE>/<XX_BASELINE>.md | grep -i "anbefalet\|næste"
   ```
3. Opret roadmap mappe:
   ```bash
   mkdir -p INTRO/50_ROADMAPS/<XX_PROJEKT_ROADMAP>/
   ```
4. Opret roadmap dokument:
   ```bash
   cp INTRO/06_TEMPLATE_INTRO/ROADMAP_TEMPLATE.md \
      INTRO/50_ROADMAPS/<XX_PROJEKT_ROADMAP>/<XX_PROJEKT_ROADMAP>.md
   ```
5. Udfyld roadmap baseret på baseline "Anbefalet næste skridt":
   - Nuværende quarter: immediate next steps fra baseline
   - Next quarter: features efter current priorities
   - Following quarters: long-term vision
6. Tilføj til 50_ROADMAPS.md oversigt:
   ```markdown
   | XX | <XX_PROJEKT_ROADMAP>/ | <Projekt> | ✅ |
   ```
7. Git commit: "NEW ROADMAP: <projekt> - future planning"

**Prevention:**
- Roadmap creation i project setup checklist
- Automated audit: projects with baseline but no roadmap → flag
- Template i 06_TEMPLATE_INTRO for hurtig roadmap creation
- Link roadmap til baseline "Anbefalet næste skridt" section

---

## ÆNDRINGSLOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2025-12-27 | - | Roadmaps index oprettet | Claude |
| 2025-12-28 | 21:36 | ÆNDRINGSLOG sektion tilføjet | Claude |
| 2026-01-08 | 12:05 | FEJLHÅNDTERING tilføjet (3 problems: outdated roadmap, conflicts with baseline, missing roadmap) | Claude |

---

*50_ROADMAPS.md - Opdateret 2026-01-08 12:05*
