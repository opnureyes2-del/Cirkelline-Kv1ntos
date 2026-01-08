# CKC - Cirkelline Kreativ Koordinator

**Version:** 1.1.0 | **Status:** Operationel | **ISO Compliance:** ISO 27001, ISO 25010

---

## Oversigt

CKC (Cirkelline Kreativ Koordinator) er et multi-agent orkestrationssystem designet til at koordinere
specialiserede AI-agenter gennem læringsrum, sikkerhedsprotokoller og HITL (Human-in-the-Loop) godkendelser.

### Arkitektur

```
┌─────────────────────────────────────────────────────────────┐
│                    CKC ORCHESTRATOR                         │
│                  (Central Koordination)                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Læringsrum  │  │ Læringsrum  │  │ Læringsrum  │  ...    │
│  │     #1      │  │     #2      │  │     #3      │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐         │
│  │   Agenter   │  │   Agenter   │  │   Agenter   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                    SIKKERHEDSLAG                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Security  │  │    ILCP    │  │    EIAP    │            │
│  │  Manager   │  │  Protocol  │  │  Protocol  │            │
│  └────────────┘  └────────────┘  └────────────┘            │
├─────────────────────────────────────────────────────────────┤
│                 KOMMANDANT SYSTEM                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Historiker │  │ Bibliotekar│  │ Dashboard  │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## Moduler

### Core Moduler

| Modul | Fil | Beskrivelse |
|-------|-----|-------------|
| **Orchestrator** | `orchestrator.py` | Central opgavefordeling og agent-koordination |
| **Learning Rooms** | `learning_rooms.py` | Virtuelle læringsrum med status-tracking |
| **Agents** | `agents.py` | Specialiserede AI-agenter (8 typer) |
| **Security** | `security.py` | Input sanitering, korruptionsdetektion |
| **Terminal** | `terminal.py` | Interaktiv kommandør-terminal |

### Avancerede Protokoller

| Protokol | Beskrivelse |
|----------|-------------|
| **5.1 Dynamisk Sikkerhed** | Automatisk sikkerhedsjustering baseret på drift |
| **5.2 ILCP** | Inter-Læringsrum Kommunikation Protocol |
| **5.3 EIAP** | External Implementation Access Protocol |

### Support Moduler

| Modul | Fil | Beskrivelse |
|-------|-----|-------------|
| **Kommandanter** | `kommandanter.py` | Historiker & Bibliotekar kommandanter |
| **Dashboard** | `dashboard.py` | Status-dashboard og monitoring |
| **Audit** | `audit.py` | FASE III audit framework |

---

## Hurtig Start

### Terminal Mode

```bash
# Start interaktiv terminal
python -m cirkelline.ckc.terminal

# Kun vis status
python -m cirkelline.ckc.terminal --status-only
```

### Programmatisk Brug

```python
import asyncio
from cirkelline.ckc.terminal import CKCTerminal

async def main():
    ckc = CKCTerminal(user_id="admin")
    await ckc.initialize()
    await ckc.show_status()

asyncio.run(main())
```

---

## Kommandoer

### Basis Kommandoer

```python
ckc.show_status()           # Vis komplet systemstatus
ckc.help()                  # Vis hjælp
```

### Simulering & Test

```python
await ckc.simulate_learning_room_error(room_id=1)
await ckc.initiate_ilcp_request(1, 2, "Analyser data")
await ckc.request_new_agent_feature(3, "analyzer", "OCR support")
await ckc.trigger_eiap_test("Claude", "LIMITED", {"action": "test"})
```

### HITL (Human-in-the-Loop)

```python
await ckc.show_pending_hitl()
await ckc.approve_hitl("request_id")
await ckc.reject_hitl("request_id", "reason")
```

### Nødstop (Emergency Stop)

```python
# KRITISK: Øjeblikkelig standsning af alle operationer
await ckc.emergency_stop("Sikkerhedsbrud detekteret")

# Genoptag operationer (kræver session_id bekræftelse)
await ckc.resume_operations(ckc.session_id)
```

---

## Sikkerhed

### Attack Pattern Defense

CKC inkluderer beskyttelse mod følgende angrebstyper:

| Kategori | Patterns |
|----------|----------|
| **XSS** | Script injection, javascript:, event handlers |
| **SQL Injection** | UNION SELECT, DROP TABLE, OR 1=1 |
| **Command Injection** | Shell metacharacters, backticks |
| **XXE** | DOCTYPE, ENTITY, SYSTEM file:// |
| **SSTI** | Jinja2 `{{}}`, ERB `<%%>`, Razor `@()` |
| **LDAP Injection** | Filter manipulation |
| **NoSQL Injection** | $where, $gt, $ne operators |
| **CRLF** | Header injection via newlines |
| **Path Traversal** | ../ sequences |

### Sikkerhedsniveauer

```
HIGH     → Fuld kontrol, alle handlinger logges
MODERATE → Reduceret kontrol efter 72 timers fejlfri drift
LIGHT    → Minimal kontrol for betroede operationer
```

### Fail-Safe Mekanisme

Ved fejl eller sikkerhedshændelser:
1. Sikkerhed rulles øjeblikkeligt tilbage til HIGH
2. Læringsrum låses til RØD status
3. HITL notification oprettes
4. Alle operationer logges til audit trail

---

## FASE III.2-4 Forbedringer (F-001 til F-006)

### F-001: Emergency Stop med Rollback

Nødstop-funktion med transaction-lignende adfærd:

```python
# Aktivér nødstop
result = await ckc.emergency_stop("Sikkerhedsbrud")

# Ved partial failure udføres automatisk rollback
if result.get("rollback_performed"):
    print(f"Rollback: {result['rollback_result']}")

# Genoptag med constant-time valideret kode
await ckc.resume_operations(ckc.session_id)
```

**Features:**
- Per-room timeout (5 sekunder)
- Automatisk rollback ved partial failure
- Constant-time session validation (timing attack prevention)
- Fuld audit trail

### F-002: Forbedret Attack Pattern Detection

Præcise regex patterns der undgår false positives:

| Pattern Type | Eksempel Match | False Positive Protected |
|-------------|----------------|--------------------------|
| Jinja2 SSTI | `{{ config }}` | JSON `{"k": {"n": 1}}` |
| NoSQL | `"$where": "..."` | Normale MongoDB queries |
| XXE | `<!ENTITY xxe` | Standard XML |

### F-003: Dokumentation (denne sektion)

Komplet dokumentation af alle F-001 til F-006 forbedringer.

### F-004: Capability Mastery Tracking

Agenter tracker deres capability mastery over tid:

```python
# Track brug af en capability
agent.track_capability_use("tool_discovery", success=True)

# Hent mastery-data
mastery = agent.get_capability_mastery()
# {
#   "capabilities": {...},
#   "overall_mastery": 0.78,
#   "strongest_capability": "security_evaluation",
#   "weakest_capability": "tool_integration"
# }

# Få anbefalinger
recommendations = agent.get_capability_recommendations()
```

**Mastery Levels:**
- `novice` (0.0-0.3)
- `beginner` (0.3-0.5)
- `intermediate` (0.5-0.75)
- `advanced` (0.75-0.9)
- `expert` (0.9-0.98)
- `master` (0.98+)

**Persistence (v1.1.1):**
Mastery data gemmes automatisk til disk ved hver opdatering:

```python
# Data gemmes i ~/.ckc/mastery/[agent_id]_mastery.json
# Auto-load ved agent initialisering
# Auto-save ved track_capability_use()

# Manuel save/load
agent._save_mastery_to_disk()  # Returns {"saved": True, "file": "..."}
agent._load_mastery_from_disk()  # Returns {"loaded": True, ...}

# Reset mastery
agent.reset_mastery()  # Nulstil alle
agent.reset_mastery("tool_discovery")  # Nulstil specifik
```

**Thread Safety (v1.1.1):**
Async operationer bruger asyncio.Lock for thread-safety:

```python
# Sync version (ikke thread-safe, til simple scripts)
result = agent.track_capability_use("tool_discovery", True)

# Async version (thread-safe, til concurrent operationer)
result = await agent.track_capability_use_async("tool_discovery", True)
```

### F-005: Feedback Integration med Validation

Agenter kan modtage og lære fra feedback:

```python
# Send feedback til agent
result = await agent.receive_feedback(
    feedback_type="correction",  # correction, praise, suggestion, error
    content={"target": "response_format", "correct_behavior": "..."},
    source="user"  # user, system, peer_agent, self, hitl
)

# Hent feedback statistik
stats = agent.get_feedback_statistics()
# {
#   "total_feedback": 42,
#   "by_type": {"correction": 10, "praise": 25, ...},
#   "learning_rate": 0.12,
#   "avg_performance": 0.87
# }
```

**Features:**
- Input validation (type, source, size)
- Bounded growth (max 1000 entries, auto-prune)
- Adaptive learning rate

### F-006: Dashboard & Orchestrator Integration

```python
# Sæt component status
await dashboard.set_component_status(
    "system_emergency",
    StatusLevel.RED,
    "NØDSTOP aktiv"
)

# Cancel alle tasks ved nødstop
cancelled = await orchestrator.cancel_all_tasks("Emergency stop")
```

---

## Agent Typer

| Agent | Kapabiliteter | Beskrivelse |
|-------|---------------|-------------|
| **Analyst** | analysis, reasoning | Dyb analyse og logisk ræsonnering |
| **Researcher** | research, search | Web-søgning og informationsindsamling |
| **Writer** | writing, content | Tekstgenerering og redigering |
| **Coder** | coding, debugging | Kodning og fejlfinding |
| **Reviewer** | review, quality | Kvalitetssikring og gennemgang |
| **Translator** | translation, language | Oversættelse og sprogbehandling |
| **Summarizer** | summarization | Opsummering af indhold |
| **Assistant** | general, support | Generel assistance |

---

## Læringsrum Status

| Farve | Status | Betydning |
|-------|--------|-----------|
| **BLÅ** | IDLE | Klar til opgaver |
| **GRØN** | ACTIVE | Aktiv behandling |
| **GUL** | WARNING | Advarsler/problemer |
| **RØD** | ERROR/LOCKED | Fejl eller låst |

---

## Audit & Compliance

### FASE III Audit

CKC inkluderer omfattende audit framework:

- **FASE III.1**: Basal systemverifikation (26 tests)
- **FASE III.2**: Robustgørelse & stresstest (16 tests)
- **FASE III.3**: Dokumentationsaudit (9 tests)
- **FASE III.4**: Kontinuerlig læring (12 tests)

### ISO Compliance

- **ISO 27001**: Information Security Management
- **ISO 25010**: Software Quality Model

### Kørselshistorik

Alle handlinger logges med:
- Tidsstempel
- Bruger/agent ID
- Handlingstype
- Resultat
- Vigtighed (1-5 skala)

---

## Konfiguration

### Miljøvariabler

```bash
CKC_LOG_LEVEL=INFO
CKC_SECURITY_DEFAULT=HIGH
CKC_HITL_TIMEOUT=300
CKC_MAX_AGENTS_PER_ROOM=10
```

### Standardindstillinger

```python
DEFAULT_SECURITY_LEVEL = SecurityLevel.HIGH
FAIL_SAFE_THRESHOLD = 3  # Fejl før rollback
ILCP_MESSAGE_TTL = 3600  # Sekunder
EIAP_SANDBOX_REQUIRED = True
```

---

## Fejlfinding

### Almindelige Problemer

| Problem | Løsning |
|---------|---------|
| Terminal starter ikke | Check Python 3.9+ og dependencies |
| HITL timeout | Øg CKC_HITL_TIMEOUT eller godkend request |
| Læringsrum låst | Brug `resume_operations()` med korrekt kode |
| Sikkerhed rullet tilbage | Normal adfærd ved fejl - check logs |

### Debug Mode

```bash
python -m cirkelline.ckc.terminal --debug
```

---

## Versionhistorik

| Version | Dato | Ændringer |
|---------|------|-----------|
| 1.1.1 | 2025-12 | F-004 persistence (disk) + Thread safety (asyncio.Lock) |
| 1.1.0 | 2025-12 | FASE III.2-4: F-001 rollback, F-002 patterns, F-004 mastery, F-005 validation |
| 1.0.0 | 2024-12 | Initial release med FASE III compliance |
| 0.9.0 | 2024-11 | Beta med alle protokoller |
| 0.8.0 | 2024-10 | Alpha med basis funktionalitet |

---

## Kontakt

- **Repository**: cirkelline-system
- **Maintainer**: Rasmus
- **Dokumentation**: `/docs/` mappen

---

*CKC - Sikker, Intelligent, Menneske-i-Loopet*
