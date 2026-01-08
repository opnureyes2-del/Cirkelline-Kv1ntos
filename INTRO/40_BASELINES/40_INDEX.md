# 40_BASELINES - Working Baselines & Snapshots

**Purpose:** Documented working states, baseline commits, known-good configurations
**Template for:** Baseline documentation across all projects

---

## WHAT GOES HERE

### Documents
- **40_BASELINES.md** - Baseline overview
- **41_PROJECT_BASELINE.md** - Per-project baseline state
- **42_SYSTEM_BASELINE.md** - System-wide baseline
- **43_DATABASE_BASELINE.md** - Database schema baseline
- **44_CONFIGURATION_BASELINE.md** - Working configuration baseline

### Purpose of Baselines
A baseline is a **known-good state** you can always return to:
- All tests passing ✅
- Features working as expected ✅
- Configuration documented ✅
- Git commit tagged ✅

---

## BASELINE TEMPLATE

```markdown
# [PROJECT] Baseline - [Date]

**Git Commit:** `abc123def456`
**Branch:** main
**Date:** 2026-01-01
**Status:** ✅ VERIFIED WORKING

## What Works
- Feature X functional
- Tests passing (127/127)
- Database migrations applied
- API endpoints responding

## Configuration
- Node: v18.17.0
- Python: 3.12.3
- PostgreSQL: 16.11

## Environment Variables Required
```bash
DATABASE_URL=postgresql://...
API_KEY=...
```

## How to Restore This Baseline
```bash
git checkout abc123def456
npm install
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm run migrate
npm test  # Should pass 127/127
```

## Verification
- [ ] Tests pass
- [ ] Server starts
- [ ] Database connects
- [ ] API responds
```

---

## WHY BASELINES MATTER

Before adding ANY new feature:
1. **Establish baseline** - document current working state
2. **Build feature** - on top of baseline
3. **Test thoroughly** - verify nothing broke
4. **Create new baseline** - if all works

This prevents "it was working yesterday" situations.

---

## RELATED SECTIONS

- **20_PROJEKTER:** Project-specific baselines
- **50_ROADMAPS:** Baseline requirements before roadmap execution
- **30_TODOS:** Baseline verification todos

---

## CHANGELOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2026-01-01 | 03:35 | Template sektion oprettet med baseline format | Kv1nt |
