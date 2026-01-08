# 20_PROJEKTER - INDEX
**Sektion:** Projekt Dokumentation
**Sidst Opdateret:** 2025-12-28 22:52
**Version:** v1.2.0

---

## OVERSIGT

Denne sektion indeholder dokumentation for alle 9 projekter i Cirkelline økosystemet.

---

## PROJEKTER

| # | Mappe | Projekt | Port | Status | INTRO % |
|---|-------|---------|------|--------|---------|
| 21 | 21_CONSULTING | Cirkelline Consulting | 3000 | ✅ PRODUCTION | ✅ 100% (6/6) |
| 22 | 22_LIB_ADMIN | lib-admin / CKC | 7779 | ✅ Launch Ready | ✅ 100% (6/6) |
| 23 | 23_COSMIC | Cosmic Library | 7778 | ✅ Fase 3 Komplet | ✅ 100% (6/6) |
| 24 | 24_COMMANDO | Commando Center | 8090 | ✅ Backend Komplet | ✅ 100% (6/6) |
| 25 | 25_AGENTS | cirkelline-agents | N/A | ⚠️ Udokumenteret | 80% (4/5) |
| 26 | 26_KOMMANDOR | Kommandør-og-agenter | N/A | ⚠️ XP Nulstillet | 78% (7/9) |
| 27 | 27_COMMANDER | Commander-and-Agent | N/A | ✅ Dokumentation 100% | 80% (4/5) |
| 28 | 28_KV1NTOS | cirkelline-kv1ntos | 7777 | ⚠️ Eksperimentel | ✅ 100% (6/6) |
| 29 | 29_SYSTEM | Cirkelline System | 7777 | ✅ READ-ONLY | 33% (2/6) |

**INTRO Integration:** Alle 9/9 projekter har INTRO mappe i lokale projekter (verificeret 2025-12-28)

---

## HURTIG NAVIGATION

### Production Ready
- **21_CONSULTING** - Live på Vercel
- **22_LIB_ADMIN** - SSO Gateway komplet

### Backend Komplet
- **23_COSMIC** - Research Team (9 agenter)
- **24_COMMANDO** - CLE Engine

### Dokumentation Only
- **27_COMMANDER** - 25 Commanders dokumenteret

### Eksperimentel
- **28_KV1NTOS** - 52,000+ linjer tilføjet

---

## INDHOLD PER PROJEKT

### I INTRO System (denne mappe)
Hver projektmappe (21-29) indeholder:
- `INDEX.md` - Projekt oversigt
- `CLAUDE.md` - AI instruktioner (kopi)
- Relevante docs fra originalt projekt
- `_TODO_VERIFIKATION/STATUS.md` - Verifikation

### I Lokale Projekter (DEL 12 Integration)
Alle 9 projekter har nu `INTRO/` mappe i deres lokale projekt rod:
- **Sti:** `/home/rasmus/Desktop/projekts/projects/{projekt}/INTRO/`
- **Indhold:** 00_INDEX.md, _TODO_VERIFIKATION/STATUS.md
- **Status:** ✅ 5/9 projekter 100% komplet (lib-admin, cosmic-library, commando-center, consulting, kv1ntos)
- **Reference:** [39_DNA DEL 12](../30_TODOS/39_DNA_KOMPLET_TODO/_TODO_VERIFIKATION/DEL_12_VERIFIKATION_2025-12-28.md)

---

## FEJLHÅNDTERING

### Problem 1: Projekt Dokumentation Ikke Synced Med Faktisk Tilstand

**Symptom:** INTRO docs siger projekt er "Production Ready" men backend fejler ved start, eller STATUS.md viser 100% men features mangler

**Årsag:**
- Dokumentation opdateret uden at verificere faktisk system state
- Changes i lokalt projekt ikke reflekteret i INTRO docs
- Optimistisk status marking uden physical verification
- CLAUDE.md kopieret men ikke opdateret med nye features

**Diagnosticering:**
```bash
# Check faktisk projekt tilstand
cd ~/Desktop/projekts/projects/<projekt>/backend
python -m uvicorn main:app --reload &
curl http://localhost:<port>/health

# Check INTRO docs claims
cat INTRO/20_PROJEKTER/<XX_PROJEKT>/INDEX.md | grep Status

# Check lokal INTRO sync
cd ~/Desktop/projekts/projects/<projekt>
ls -la INTRO/
cat INTRO/00_INDEX.md

# Sammenlign med central INTRO
diff INTRO/00_INDEX.md ~/Desktop/projekts/status\ opdaterings\ rapport/INTRO/20_PROJEKTER/<XX_PROJEKT>/INDEX.md
```

**Fix:**
1. Verificer faktisk projekt state fysisk:
   ```bash
   # Start service
   # Test endpoints
   # Check database
   # Verify all features claimed
   ```
2. Opdater INTRO docs baseret på FACTS:
   - Status: Verificeret tilstand (ikke ønsket tilstand)
   - Features: Kun list hvad der virker
   - Port: Verificer med `lsof`
3. Sync lokal INTRO med central INTRO:
   ```bash
   rsync -av ~/Desktop/projekts/status\ opdaterings\ rapport/INTRO/20_PROJEKTER/<XX_PROJEKT>/ \
             ~/Desktop/projekts/projects/<projekt>/INTRO/
   ```
4. Update CHANGELOG med dato + hvad blev verificeret

**Prevention:**
- Physical verification før status update
- Automated sync script mellem lokal og central INTRO
- Verification checklist in STATUS.md
- Regular audit (weekly) af projekt states

---

### Problem 2: INTRO Folder Mangler Eller Incomplete I Lokalt Projekt

**Symptom:** Projekt findes men `/home/rasmus/Desktop/projekts/projects/<projekt>/INTRO/` mangler eller kun har template files

**Årsag:**
- DEL 12 integration ikke kørt for dette projekt
- INTRO folder oprettet men ikke fyldt med content
- Git pull overskrev lokal INTRO
- Projekt nyoprettet, INTRO ikke initialiseret

**Diagnosticering:**
```bash
# Check om INTRO findes
ls -la ~/Desktop/projekts/projects/<projekt>/INTRO/

# Check INTRO completeness (skal have 6/6 files for 100%)
find ~/Desktop/projekts/projects/<projekt>/INTRO/ -name "*.md" | wc -l

# Check denne overview for projekt status
grep "<projekt>" INTRO/20_PROJEKTER/20_PROJEKTER.md

# Check DEL 12 verifikation status
cat INTRO/30_TODOS/39_DNA_KOMPLET_TODO/_TODO_VERIFIKATION/DEL_12_VERIFIKATION*.md | grep "<projekt>"
```

**Fix:**
1. Check om central INTRO docs findes:
   ```bash
   ls -la ~/Desktop/projekts/status\ opdaterings\ rapport/INTRO/20_PROJEKTER/<XX_PROJEKT>/
   ```
2. Copy fra central til lokal:
   ```bash
   mkdir -p ~/Desktop/projekts/projects/<projekt>/INTRO
   cp -r ~/Desktop/projekts/status\ opdaterings\ rapport/INTRO/20_PROJEKTER/<XX_PROJEKT>/* \
         ~/Desktop/projekts/projects/<projekt>/INTRO/
   ```
3. Verificer completeness:
   ```bash
   # Should have:
   # - 00_INDEX.md
   # - CLAUDE.md
   # - STATUS.md
   # - _TODO_VERIFIKATION/STATUS.md
   ls -la ~/Desktop/projekts/projects/<projekt>/INTRO/
   ```
4. Update 20_PROJEKTER.md INTRO % kolonne
5. Git commit både lokalt og i central INTRO

**Prevention:**
- INTRO initialization som del af project creation
- Verification script: `scripts/verify_intro_sync.sh`
- Git hooks der checker INTRO completeness før commit
- Documentation in 00_UDVIKLINGSPLAN.md for new projects

---

### Problem 3: Projekt Status Uklar - Production vs Development

**Symptom:** Usikkerhed om hvilket projekt er live, hvilket er safe at ændre, hvor production data ligger

**Årsag:**
- Status markers ikke consistent (✅ betyder både "done" og "production")
- Ingen klar markering af READ-ONLY projekter
- Production URL ikke dokumenteret
- Development vs staging vs production ikke skelnet

**Diagnosticering:**
```bash
# Check denne overview
cat INTRO/20_PROJEKTER/20_PROJEKTER.md

# Check projekt specifik status
cat INTRO/20_PROJEKTER/<XX_PROJEKT>/INDEX.md | grep -i status

# Check production deployments
cat INTRO/20_PROJEKTER/21_CONSULTING/INDEX.md | grep -i vercel
cat INTRO/20_PROJEKTER/22_LIB_ADMIN/INDEX.md | grep -i production

# Check miljø configs
cat INTRO/15_MILJOER/15A_REELLE_MILJOER/15A_REELLE_MILJOER.md | grep "<projekt>"
```

**Fix:**
1. Definer clear status levels:
   - 🟢 PRODUCTION (live with users)
   - 🟡 STAGING (ready for testing)
   - 🔵 DEVELOPMENT (active development)
   - ⚪ EXPERIMENTAL (proof of concept)
   - 🔒 READ-ONLY (do not modify)
2. Opdater 20_PROJEKTER.md med clear statuses:
   ```markdown
   | 21 | CONSULTING | 🟢 PRODUCTION | Vercel: consulting.cirkelline.dk |
   | 29 | SYSTEM | 🔒 READ-ONLY | DO NOT MODIFY - Ivo's baseline |
   ```
3. Document production URLs:
   - Where is it deployed?
   - How to access?
   - Who has admin access?
4. Mark dangerous operations clearly in each projekt's INTRO docs

**Prevention:**
- Status taxonomy documented in 00_UDVIKLINGSPLAN.md
- Production projects have explicit warning banners
- Deployment tracking in 15_MILJOER
- Regular status audit (monthly)

---

## ÆNDRINGSLOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2025-12-28 | 07:12 | Initial INDEX oprettet | Claude |
| 2025-12-28 | 22:20 | INTRO % kolonne tilføjet (DEL 12 data) | Claude |
| 2025-12-28 | 22:20 | DEL 12 Integration sektion tilføjet | Claude |
| 2025-12-28 | 22:20 | Link til DEL_12_VERIFIKATION rapport | Claude |
| 2025-12-28 | 22:52 | ✅ 5 projekter opdateret til 100% (DEL 12 komplet) | Claude |
| 2025-12-28 | 22:52 | v1.2.0 - INTRO integration færdig for 5/9 projekter | Claude |
| 2026-01-08 | 11:55 | FEJLHÅNDTERING tilføjet (3 problems: doc sync, INTRO missing, status taxonomy) | Claude |

---

*20_PROJEKTER.md - Opdateret 2026-01-08 11:55*
