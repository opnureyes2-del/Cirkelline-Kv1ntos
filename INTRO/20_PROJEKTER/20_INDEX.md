# 20_PROJEKTER - Projects & Integration

**Purpose:** Project-specific documentation, integration guides, connections
**Template for:** All project documentation in ecosystem

---

## WHAT GOES HERE

### Per-Project Subdirectories
```
20_PROJEKTER/
├── 21_PROJECT_NAME/
│   ├── PROJECT_NAME_CLAUDE.md     # Claude context for project
│   ├── PROJECT_NAME_OVERVIEW.md   # Project overview
│   ├── PROJECT_NAME_SETUP.md      # Setup guide
│   └── _TODO_VERIFIKATION/        # Project todos
```

### Example Projects
- **21_CONSULTING/** - cirkelline-consulting docs
- **22_LIBRARY/** - cosmic-library docs
- **23_COMMANDO/** - commando-center docs
- **24_KV1NTOS/** - cirkelline-kv1ntos docs
- **25_AGENTS/** - agent systems docs

### Standard Files Per Project
- **XX_CLAUDE.md** - Claude context (CRITICAL for AI work)
- **XX_OVERVIEW.md** - Project purpose and goals
- **XX_SETUP.md** - How to set up locally
- **XX_INTEGRATION.md** - How it connects to other projects
- **STATUS.md** - Current project status

---

## TEMPLATE: CLAUDE.md

```markdown
# [PROJECT_NAME] - Claude Context

**Repository:** git@github.com:org/repo.git
**Local Path:** ~/Desktop/projects/[project-name]/
**Status:** [Active/Paused/Complete]

## What This Project Is
[Brief description]

## Tech Stack
- Frontend: [Tech]
- Backend: [Tech]
- Database: [Tech]

## Key Files
- `/src/main.py` - Entry point
- `/config/settings.py` - Configuration

## Integration Points
- Connects to cirkelline-system via [how]
- Uses shared database: [which]

## Current Work
[What we're working on]

## Next Steps
[What comes next]
```

---

## RELATED SECTIONS

- **10_ARKITEKTUR:** How projects fit in overall architecture
- **40_BASELINES:** Project baselines and working states
- **70_GUIDES:** Cross-project integration guides

---

## CHANGELOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2026-01-01 | 03:30 | Template sektion oprettet | Kv1nt |
