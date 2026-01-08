# 60_CLAUDE_MD - AI Context & Documentation

**Purpose:** Claude-specific context files, AI collaboration documentation
**Template for:** AI context across all projects

---

## WHAT GOES HERE

### Documents
- **60_CLAUDE_MD.md** - Claude context overview
- **61_PROJECT_CLAUDE.md** - Per-project Claude context
- **62_CODEBASE_CONTEXT.md** - Codebase structure for AI
- **63_PATTERNS.md** - Code patterns and conventions
- **64_PREFERENCES.md** - Development preferences

### Why Claude Context Matters
Claude needs context to:
- Understand project structure
- Follow your coding patterns
- Remember decisions made
- Avoid repeating mistakes
- Work efficiently

---

## CLAUDE.md TEMPLATE

```markdown
# [PROJECT] - Claude Context

**Last Updated:** 2026-01-01
**Primary Language:** [TypeScript/Python/etc]
**Framework:** [Next.js/FastAPI/etc]

## Project Overview
[Brief description of what this project does]

## Tech Stack
- **Frontend:** [Framework, version]
- **Backend:** [Framework, version]
- **Database:** [Database, version]
- **Infrastructure:** [Docker/Cloud/etc]

## Directory Structure
```
project/
├── src/           # Source code
├── tests/         # Tests
├── docs/          # Documentation
└── scripts/       # Utility scripts
```

## Key Files
- `src/main.py` - Entry point
- `config/settings.py` - Configuration
- `tests/test_main.py` - Main tests

## Coding Patterns
- Use TypeScript strict mode
- All functions have JSDoc comments
- Tests in `__tests__` folders
- Follow Airbnb style guide

## Common Tasks
### Run Development Server
```bash
npm run dev
```

### Run Tests
```bash
npm test
```

### Build for Production
```bash
npm run build
```

## Integration Points
- Connects to cirkelline-system via REST API
- Shares authentication with main platform
- Uses shared PostgreSQL database

## Current Work
[What we're currently building]

## Important Context
- [Any gotchas or important things to know]
- [Decisions made and why]
- [Things to avoid]
```

---

## RELATED SECTIONS

- **20_PROJEKTER:** Project documentation
- **70_GUIDES:** Development guides
- **10_ARKITEKTUR:** Architecture context

---

## CHANGELOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2026-01-01 | 03:35 | Template sektion oprettet | Kv1nt |
