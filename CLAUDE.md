# CIRKELLINE KV1NTOS (Experimental Version)

**Version:** KV1NTOS v3.0.0 (based on Cirkelline v1.3.8)
**Status:** ⏳ EXPERIMENTAL - Needs Testing
**Last Updated:** 2025-12-20
**Owner:** Rasmus (experimental work from Dec 16-19, 2025)

---

## 🌍 OVERALL ECOSYSTEM CONTEXT

### The Situation
You are working in Rasmus's localhost development environment. This is the **experimental version** where Rasmus added extensive KV1NTOS features.

### Background
1. **Rasmus** started with clean Cirkelline v1.3.8 from production
2. **December 16-19, 2025:** Added ~52,000 lines of KV1NTOS code (79 commits)
3. **December 20, 2025:** Ivo took over and reorganized folders
4. **Result:** This experimental version preserved separately from clean reference

### This Specific Folder
**Location:** `/home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/`
**Purpose:** Rasmus's experimental KV1NTOS work (SAFE TO EDIT)
**Status:** Untested - functionality unknown
**Git:** NO GIT (completely disconnected, local only)

### The Complete Ecosystem (6 Projects)
```
/home/rasmus/Desktop/projekts/projects/
├── cirkelline-system/              ← Clean v1.3.8 (DO NOT EDIT)
├── cirkelline-kv1ntos/             ← YOU ARE HERE (experimental, NO GIT)
├── cosmic-library/                 ← AI Training Academy (Port 7778)
├── lib-admin/                      ← CKC Admin Hub (Port 7779)
├── commando-center/                ← Docker Infrastructure (Port 8090)
├── cirkelline-consulting/          ← Booking Platform (Port 3000)
└── docs/                           ← Central documentation
```

### Critical Notes
⚠️ **ALL DATABASES ARE DIFFERENT AND NOTHING TALKS TO ANYTHING!**
- Each project has isolated database
- No shared authentication
- Integration is a FUTURE goal

---

## 🎯 PROJECT PURPOSE

### What This Project Is
This is Rasmus's **experimental enhancement** of the Cirkelline System, adding a sophisticated multi-layered AI orchestration framework called **KV1NTOS** (Knowledge + Autonomous Orchestration).

### Rasmus's Vision
Build an advanced AI orchestration system with:
- **Agent Factory** - Dynamically create and manage AI agents
- **ODIN Orchestrator** - Master orchestrator coordinating all agents
- **Flock Management** - Organize agents into collaborative flocks
- **Learning Rooms** - Virtual training environments
- **NL Terminal** - Natural language interface for system control
- **Admiral** - Strategic governance layer
- **Code Guardian** - Autonomous code quality monitoring

### Comparison with Clean Version (Verificeret 2026-01-03)
| Feature | Clean v1.3.8 | KV1NTOS v3.0.0 (Verified) |
|---------|--------------|---------------------------|
| Docs | 54 files | 130+ files |
| Python Files | ~200 files | **19,533 files** (verificeret) |
| Total Size | ~100MB | **~5GB** (verificeret) |
| Main Entry | main.py | my_os.py (1,152 linjer) |
| Frontend | cirkelline-ui | cirkelline-ui (2.2GB) |
| Desktop App | N/A | cla/ (1.9GB CLA Desktop) |
| Ecosystems | N/A | ecosystems/ (449MB) |
| Agents | 9 specialists | 9 + dynamic creation |
| Orchestration | Cirkelline only | Multi-layer (ODIN, Admiral, Flock) |
| Status | Production | ⚠️ UNTESTED (5GB experimental code) |

---

## 🏗️ TECHNICAL ARCHITECTURE

### Technology Stack (Same as Clean Version)
- **Backend:** FastAPI (Python 3.12+)
- **Frontend:** Next.js 15 + TypeScript
- **Database:** PostgreSQL 17 + pgvector (768-dim embeddings)
- **AI Framework:** AGNO v2.3.4
- **LLM:** Google Gemini 2.5 Flash
- **Infrastructure:** AWS ECS Fargate + RDS + ALB (for deployment)

### Ports Used (Same as Production)
| Service | Port | Type | Status |
|---------|------|------|--------|
| Backend API | 7777 | FastAPI | ⏳ Needs testing |
| Frontend | 3000 | Next.js | ⏳ Needs testing |
| PostgreSQL | 5532 | Database | ✅ Configured |
| Redis | 6381 | Cache | ✅ Configured |
| RabbitMQ | 5672 | Message Queue | ✅ Configured |

### Database Details
- **Type:** PostgreSQL 17 with pgvector
- **Name:** cirkelline
- **Port:** 5532
- **Container:** cirkelline-postgres
- **Connection:** \`postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline\`

**CRITICAL:** This database is SEPARATE from other projects!

---

## 📊 CURRENT STATUS

### Implementation Status: ⏳ UNKNOWN (Needs Testing)

### What Rasmus Added (79 Commits) ✅
**KV1NTOS Features (v2.0.0 → v3.0.0):**
1. Agent Factory (v2.4.0) - Dynamic agent creation
2. Flock Orchestrator (v2.5.0) - Collaborative agent groups + Learning Rooms
3. Folder Activator & Codeword Manager (v2.6.0)
4. Continuous Optimization (v2.7.0)
5. Predictive Optimization (v2.8.0)
6. Cross-Agent Learning (v2.9.0)
7. LLM Foundation (v2.10.0)
8. Knowledge Graph (v2.11.0)
9. OPUS-NIVEAU Complete (v3.0.0)

**Plus:** Admiral v2.1.0, Code Guardian v2.1.0, NL Terminal v2.3.0

**Documentation:** 76 new docs (130 total)

### What's Unknown/Untested ⏳
- Does it run?
- Do all features work?
- Database migrations needed?
- Integration with AGNO v2.3.4?
- Performance impact?

### Known Issues ❌
- **Untested** - No verification
- **API Keys Missing** - EXA_API_KEY, TAVILY_API_KEY (same as clean)
- **Integration Unknown** - May conflict with base Cirkelline

---

## 🚀 QUICK START

### Start Backend
```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos
source .venv/bin/activate
python my_os.py
# Expected: Port 7777
# Reality: UNKNOWN - needs testing!
```

### Start Frontend
```bash
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos/cirkelline-ui
pnpm install
pnpm dev
# Expected: Port 3000
```

### Test
\`\`\`bash
curl http://localhost:7777/health
curl http://localhost:7777/config
\`\`\`

---

## ⚠️ CRITICAL NOTES

1. **EXPERIMENTAL** - This code is untested
2. **NO GIT** - This folder has no git, changes are local only
3. **Compare with clean** at ../cirkelline-system/
4. **Test before using** - may crash
5. **Document results** - update this file

### Testing Checklist (TODO)
- [ ] Does backend start?
- [ ] Do agents load?
- [ ] Does Agent Factory work?
- [ ] Does ODIN function?
- [ ] Any critical bugs?

**Created:** 2025-12-20
**Last Updated:** 2025-12-23
**Maintained by:** Ivo (eenvywithin@gmail.com)
**Original Author:** Rasmus (opnureyes2@gmail.com)

---

## INTRO DOCUMENTATION STANDARD

This project follows the INTRO documentation standard:
- [06_TEMPLATE_INTRO](/home/rasmus/Desktop/status opdaterings rapport/INTRO/06_TEMPLATE_INTRO/06_TEMPLATE_INTRO.md) - Master template for all documentation
- [39_DNA_KOMPLET_TODO](/home/rasmus/Desktop/status opdaterings rapport/INTRO/30_TODOS/39_DNA_KOMPLET_TODO/39_DNA_KOMPLET_TODO.md) - Master task list (270 points)

**Local INTRO folder:** `./INTRO/`
- `00_INDEX.md` - Project navigation and links to central bible
- `_TODO_VERIFIKATION/STATUS.md` - Integration status

**Central INTRO Bible:** `/home/rasmus/Desktop/status opdaterings rapport/INTRO/`
- [00_START_HER.md](../../../status%20opdaterings%20rapport/INTRO/00_START_HER.md) - Starting point
- [46_cirkelline-kv1ntos_BASELINE](../../../status%20opdaterings%20rapport/INTRO/40_BASELINES/46_cirkelline-kv1ntos_BASELINE/) - Project baseline
- [57_kv1ntos_ROADMAP](../../../status%20opdaterings%20rapport/INTRO/50_ROADMAPS/57_kv1ntos_ROADMAP/) - Project roadmap
- [66_cirkelline-kv1ntos_CLAUDE](../../../status%20opdaterings%20rapport/INTRO/60_CLAUDE_MD/66_cirkelline-kv1ntos_CLAUDE/) - This file (copy)

---

## ÆNDRINGSLOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2025-12-20 | - | Initial CLAUDE.md created | Ivo |
| 2025-12-29 | 04:20 | INTRO DOCUMENTATION STANDARD tilføjet (DEL 18 KRYDS-3) | Claude |
| 2025-12-29 | 04:20 | Reference til 06_TEMPLATE_INTRO og 39_DNA tilføjet | Claude |
| 2026-01-03 | 02:35 | P1-9: Fysisk verificeret projekt størrelse (5GB, 19.5k Python filer) | Claude |
| 2026-01-03 | 02:35 | Opdateret sammenligning med FAKTA: 19,533 filer, 2.2GB UI, 1.9GB CLA | Claude |

---

**INTRO Integration:** Se `INTRO/_TODO_VERIFIKATION/STATUS.md` for detaljer
