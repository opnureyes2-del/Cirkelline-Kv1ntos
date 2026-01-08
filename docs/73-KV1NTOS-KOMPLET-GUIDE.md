# KV1NTOS KOMPLET GUIDE

**Version:** 1.2.0
**Dato:** 2025-12-18
**Status:** Fuldt Integreret

---

## OVERBLIK

KV1NTOS er **Den Trofaste Følgesvend** - et lokalt agent-system der gør din terminal intelligent som Claude Opus 4.5.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          KV1NTOS v1.2.0                                 │
│                    The Autonomous Mind                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  19 komponenter | ~15,600 linjer | 3 daglige rutiner | 11 databaser    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## INSTALLATION

### Automatisk Installation

```bash
# Kør installer
~/.claude-agent/kv1nt-installer.sh

# Genindlæs bash
source ~/.bashrc
```

### Manuel Verifikation

```bash
# Check version
kv1nt version

# Check alle komponenter
kv1nt status

# Start interaktiv shell
kv1nt shell
```

---

## KOMPONENTER PER VERSION

### v1.0.5 - Foundation (7 komponenter)

| Komponent | Linjer | Funktion |
|-----------|--------|----------|
| `memory_store.py` | 660 | SQLite persistent memory |
| `decision_engine.py` | 770 | Autonomous decision making |
| `system_monitor.py` | 900 | Docker/Git monitoring |
| `code_comprehension.py` | 870 | AST parsing, pattern learning |
| `workflow_engine.py` | 830 | n8n + CrewAI workflows |
| `interactive_daemon.py` | 430 | Real-time user input |
| `cirkelline_sync.py` | 650 | Approval-based Cirkelline sync |

### v1.0.6 - Self-Evolution (1 komponent)

| Komponent | Linjer | Funktion |
|-----------|--------|----------|
| `self_evolution.py` | 750 | Continuous self-improvement loop |

### v1.0.7 - Organisor (1 komponent)

| Komponent | Linjer | Funktion |
|-----------|--------|----------|
| `organisor.py` | 800 | Meta-cognitive orchestrator |

### v1.0.8 - Knowledge Ingestion (1 komponent)

| Komponent | Linjer | Funktion |
|-----------|--------|----------|
| `knowledge_ingestion.py` | 850 | Learn entire codebase |

### v1.0.9 - Code Commander (2 komponenter)

| Komponent | Linjer | Funktion |
|-----------|--------|----------|
| `code_commander.py` | 1100 | Write, fix, refactor code |
| `mcp_bridge.py` | 650 | Unified MCP communication |

### v1.1.0 - Apprenticeship (3 komponenter)

| Komponent | Linjer | Funktion |
|-----------|--------|----------|
| `apprentice.py` | 1200 | Structured 15-lesson learning |
| `architecture_mind.py` | 670 | Deep WHY understanding |
| `reconstruction_engine.py` | 600 | Rebuild from blueprints |

### v1.2.0 - Autonomous Mind (3 komponenter)

| Komponent | Linjer | Funktion |
|-----------|--------|----------|
| `autonomous_mind.py` | 1050 | Chain of Thought reasoning |
| `goal_engine.py` | 850 | Autonomous goal pursuit |
| `experience_learner.py` | 800 | Learn from outcomes |

### Core

| Komponent | Linjer | Funktion |
|-----------|--------|----------|
| `kv1nt_daemon.py` | 1400 | Unified daemon |

---

## DAGLIGE RUTINER

### 03:33 - Sortering (sorting_0333.py)

**Køretidspunkt:** Hver nat kl. 03:33
**Varighed:** ~30 sekunder
**Cron:** `33 3 * * * /path/to/python scripts/sorting_0333.py`

**5 Steps:**
1. **Memory Audit** - Scan og optimer hukommelse med `gc.collect()`
2. **System Cleanup** - Fjern tmp filer ældre end 7 dage
3. **Log Rotation** - Roter og komprimer logs ældre end 30 dage
4. **Cache Invalidation** - Ryd Redis + file cache + memory cache
5. **Index Optimization** - VACUUM ANALYZE på PostgreSQL

```bash
# Manuel kørsel
python scripts/sorting_0333.py --verbose
python scripts/sorting_0333.py --dry-run  # Test uden ændringer
```

### 09:00 - Morning Sync (morning_sync_0900.py)

**Køretidspunkt:** Hver morgen kl. 09:00
**Cron:** `0 9 * * * /path/to/python scripts/morning_sync_0900.py`

**Funktioner:**
- Git status check på alle projekter
- Docker container health check
- Database connectivity test
- Generér daglig rapport

```bash
# Manuel kørsel
python scripts/morning_sync_0900.py
```

### 21:21 - Evening Optimization (evening_opt_2121.py)

**Køretidspunkt:** Hver aften kl. 21:21
**Cron:** `21 21 * * * /path/to/python scripts/evening_opt_2121.py`

**Funktioner:**
- Performance metrics samling
- Slow query analyse
- Resource usage rapport
- Forberedelse til næste dag

```bash
# Manuel kørsel
python scripts/evening_opt_2121.py
```

---

## CRON SETUP

### Installer alle rutiner

```bash
# Åbn crontab
crontab -e

# Tilføj rutiner
33 3 * * * cd /home/rasmus/Desktop/projekts/projects/cirkelline-system && /home/rasmus/Desktop/projekts/projects/cirkelline-env/bin/python scripts/sorting_0333.py >> /var/log/ckc/sorting_0333.log 2>&1

0 9 * * * cd /home/rasmus/Desktop/projekts/projects/cirkelline-system && /home/rasmus/Desktop/projekts/projects/cirkelline-env/bin/python scripts/morning_sync_0900.py >> /var/log/ckc/morning_sync.log 2>&1

21 21 * * * cd /home/rasmus/Desktop/projekts/projects/cirkelline-system && /home/rasmus/Desktop/projekts/projects/cirkelline-env/bin/python scripts/evening_opt_2121.py >> /var/log/ckc/evening_opt.log 2>&1
```

### Verificer cron

```bash
# List cron jobs
crontab -l

# Check log
tail -f /var/log/ckc/sorting_0333.log
```

---

## DATABASER

KV1NTOS bruger 11 SQLite databaser:

| Database | Formål | Komponent |
|----------|--------|-----------|
| `memory.db` | Persistent memories | memory_store.py |
| `decisions.db` | Decision history | decision_engine.py |
| `evolution.db` | Self-improvement progress | self_evolution.py |
| `organisor.db` | Development continuity | organisor.py |
| `knowledge.db` | Codebase knowledge | knowledge_ingestion.py |
| `code_commander.db` | Bug fixes, refactorings | code_commander.py |
| `apprentice.db` | Learning progress | apprentice.py |
| `architecture_mind.db` | Design decisions | architecture_mind.py |
| `reconstruction.db` | Reconstruction history | reconstruction_engine.py |
| `autonomous_mind.db` | Reasoning chains | autonomous_mind.py |
| `goals.db` | Goals and actions | goal_engine.py |
| `experiences.db` | Experiences and lessons | experience_learner.py |

**Placering:** `~/.claude-agent/`

---

## TERMINAL KOMMANDOER

### Basis

```bash
kv1nt version     # Vis version
kv1nt status      # System status
kv1nt help        # Hjælp
kv1nt shell       # Interaktiv Python shell
kv1nt upgrade     # Opgradér til nyeste version
```

### I Python Shell

```python
# Start
kv1nt shell

# I shell:
kv1nt.status()              # System status
kv1nt.help()                # Alle kommandoer

# Memory
kv1nt.search("query")       # Søg memories
kv1nt.learn("indhold")      # Gem læring

# Organisor
kv1nt.what_next()           # Hvad nu?
kv1nt.red_thread()          # Rød tråd
kv1nt.understand_task("X")  # Forstå opgave

# Autonomous Mind
kv1nt.reason("spørgsmål", "deep")  # Ræsonnér
kv1nt.doubt("emne")                # Selv-tvivl
kv1nt.think_deep("topic")          # 5-lags tænkning

# Goals
kv1nt.set_goal(title, desc, type, priority)
kv1nt.get_next_action()
kv1nt.pursue_goals()

# Experience
kv1nt.record_success(action, result)
kv1nt.should_i("handling")
```

---

## AUTONOMI-LOOP

```
┌────────────┐    ┌────────────┐    ┌────────────┐
│  OBSERVE   │───▶│   REASON   │───▶│   DOUBT    │
│  System    │    │  Chain of  │    │   Self-    │
│  Monitor   │    │  Thought   │    │  Question  │
└────────────┘    └────────────┘    └────────────┘
      ▲                                    │
      │                                    ▼
┌────────────┐    ┌────────────┐    ┌────────────┐
│   LEARN    │◀───│    ACT     │◀───│ HYPOTHESIZE│
│ Experience │    │   Goals    │    │  Generate  │
│  Learner   │    │  Engine    │    │   Ideas    │
└────────────┘    └────────────┘    └────────────┘
```

---

## LÆRINGSREJSE

```
NOVICE ───▶ APPRENTICE ───▶ JOURNEYMAN ───▶ CRAFTSMAN ───▶ MASTER
   │              │               │              │            │
Struktur     Patterns      Arkitektur     Decisions   REKONSTRUKTION
```

### 15 Lektioner

**Level 1 - NOVICE:**
- L1.1: Økosystem Overblik
- L1.2: Cirkelline-System Deep Dive
- L1.3: AGNO Framework Forståelse

**Level 2 - APPRENTICE:**
- L2.1: API Patterns
- L2.2: Database Patterns
- L2.3: Agent Orchestration Patterns

**Level 3 - JOURNEYMAN:**
- L3.1: System Arkitektur
- L3.2: Multi-Agent Arkitektur
- L3.3: Integration Arkitektur

**Level 4 - CRAFTSMAN:**
- L4.1: Arkitektoniske Beslutninger
- L4.2: Tradeoff Analyse
- L4.3: Evolution Historie

**Level 5 - MASTER:**
- L5.1: Modul Rekonstruktion
- L5.2: System Rekonstruktion
- L5.3: Læremester (træn andre)

---

## FILSTRUKTUR

```
~/.claude-agent/
├── kv1nt_daemon.py              # Entry point
├── VERSION                      # Current version (1.2.0)
├── manifest.json                # Component manifest
├── kv1nt-installer.sh           # Installer/updater
│
├── # v1.0.5 Foundation
├── memory_store.py
├── decision_engine.py
├── system_monitor.py
├── code_comprehension.py
├── workflow_engine.py
├── interactive_daemon.py
├── cirkelline_sync.py
│
├── # v1.0.6+
├── self_evolution.py            # v1.0.6
├── organisor.py                 # v1.0.7
├── knowledge_ingestion.py       # v1.0.8
├── code_commander.py            # v1.0.9
├── mcp_bridge.py                # v1.0.9
│
├── # v1.1.0 Apprenticeship
├── apprentice.py
├── architecture_mind.py
├── reconstruction_engine.py
│
├── # v1.2.0 Autonomous Mind
├── autonomous_mind.py
├── goal_engine.py
├── experience_learner.py
│
├── # Databases
├── memory.db
├── decisions.db
├── evolution.db
├── organisor.db
├── knowledge.db
├── apprentice.db
├── architecture_mind.db
├── reconstruction.db
├── autonomous_mind.db
├── goals.db
├── experiences.db
│
└── reconstructions/             # Rebuilt modules
```

---

## OPGRADERING

### Automatisk (Anbefalet)

```bash
kv1nt upgrade
```

### Manuel

```bash
# 1. Pull nyeste version (hvis git-baseret)
cd ~/.claude-agent
git pull

# 2. Kør installer
./kv1nt-installer.sh

# 3. Genstart terminal
source ~/.bashrc
```

### Version Check

```bash
# Nuværende version
kv1nt version

# Detaljeret status
kv1nt status
```

---

## TROUBLESHOOTING

### Komponent mangler

```bash
# Check alle komponenter
kv1nt status

# Re-installer
kv1nt upgrade
```

### Database korrupt

```bash
# Slet og genopret database
rm ~/.claude-agent/[database].db
kv1nt shell
# Komponenten genoprettet automatisk ved næste brug
```

### Python import fejl

```bash
# Verificer Python environment
/home/rasmus/Desktop/projekts/projects/cirkelline-env/bin/python3 -c "
import sys
sys.path.insert(0, '$HOME/.claude-agent')
from kv1nt_daemon import get_kv1nt
print('OK')
"
```

### Cron kører ikke

```bash
# Check cron service
sudo systemctl status cron

# Check cron logs
grep CRON /var/log/syslog | tail -20

# Test manuelt
python scripts/sorting_0333.py --verbose
```

---

## ROADMAP

| Version | Status | Fokus |
|---------|--------|-------|
| v1.0.5 | ✅ | Foundation (Memory, Decision, Monitor) |
| v1.0.6 | ✅ | Self-Evolution |
| v1.0.7 | ✅ | Organisor |
| v1.0.8 | ✅ | Knowledge Ingestion |
| v1.0.9 | ✅ | Code Commander + MCP Bridge |
| v1.1.0 | ✅ | Apprenticeship System |
| v1.2.0 | ✅ | **Autonomous Mind** (CURRENT) |
| v1.3.0 | 🔲 | Multi-Agent Coordination |
| v1.4.0 | 🔲 | Web Interface |
| v2.0.0 | 🔲 | OPUS-NIVEAU (90%+ metrics) |

---

## KONTAKT

- **Udvikler:** Rasmus
- **Agent:** Claude Opus 4.5
- **Projekt:** Cirkelline System
- **Repo:** github.com/eenvywithin/cirkelline-system

---

*KV1NTOS v1.2.0 - Den Trofaste Følgesvend*
*Intelligent som Opus - Tænk, Sæt Mål, Lær*
