# CKC API ENDPOINTS DOKUMENTATION

**Dato:** 2025-12-17 (Opdateret ~14:15)
**Version:** v1.3.5
**Agent:** Agent 2 (CKC) / Kommandør #4
**Base URL:** `/api/ckc`

---

## OVERSIGT

CKC API giver **36 endpoints** til administration af:
- System overblik
- Task monitoring
- Agent status
- Learning rooms
- HITL (Human-in-the-Loop) godkendelser
- Real-time event streaming

---

## ENDPOINTS

### System Overview

| Method | Endpoint | Beskrivelse |
|--------|----------|-------------|
| GET | `/overview` | Komplet system overblik |

**Response Model:** `SystemOverview`
```json
{
  "status": "operational",
  "version": "1.0.0",
  "uptime_seconds": 3600.0,
  "active_tasks": 5,
  "active_agents": 3,
  "active_rooms": 4,
  "pending_hitl": 2,
  "database_status": "connected",
  "message_bus_status": "connected",
  "last_updated": "2025-12-16T23:45:00"
}
```

---

### Tasks

| Method | Endpoint | Beskrivelse | Query Params |
|--------|----------|-------------|--------------|
| GET | `/tasks` | Liste alle tasks | `status`, `agent`, `limit` |
| GET | `/tasks/{task_id}` | Task detaljer | - |
| POST | `/tasks/{task_id}/pause` | Pause en task | - |
| POST | `/tasks/{task_id}/resume` | Genoptag en task | - |
| POST | `/tasks/{task_id}/cancel` | Annuller en task | - |
| GET | `/tasks/{task_id}/checkpoints` | Task checkpoints | `limit` |

**Task Status Values:**
- `pending` - Afventer start
- `running` - Kører
- `completed` - Færdig
- `failed` - Fejlet
- `paused` - Pauset

---

### Agents

| Method | Endpoint | Beskrivelse | Query Params |
|--------|----------|-------------|--------------|
| GET | `/agents` | Liste alle agenter | `status` |
| GET | `/agents/{agent_id}` | Agent detaljer | - |
| GET | `/agents/{agent_id}/metrics` | Agent performance | - |

**Agent Status Values:**
- `idle` - Ledig
- `busy` - Optaget
- `error` - Fejl
- `offline` - Offline

**Demo Agenter (5):**
1. `tool_explorer` - Analyserer værktøjer
2. `creative_synthesizer` - Kreativ problemløsning
3. `knowledge_architect` - Strukturerer viden
4. `virtual_world_builder` - Bygger virtuelle verdener
5. `quality_assurance` - Sikrer kvalitet

---

### Learning Rooms

| Method | Endpoint | Beskrivelse | Query Params |
|--------|----------|-------------|--------------|
| GET | `/rooms` | Liste alle rum | `status` |
| GET | `/rooms/{room_id}` | Rum detaljer | - |

**Demo Rooms (4):**
1. `Projektledelse` (management)
2. `Kreativ Zone` (creative)
3. `Teknisk Lab` (technical)
4. `Kvalitetskontrol` (qa)

---

### HITL (Human-in-the-Loop)

| Method | Endpoint | Beskrivelse |
|--------|----------|-------------|
| GET | `/hitl/pending` | Afventende godkendelser |
| GET | `/hitl/{request_id}` | Anmodning detaljer |
| POST | `/hitl/{request_id}/approve` | Godkend anmodning |
| POST | `/hitl/{request_id}/reject` | Afvis anmodning |

**HITL Status Values:**
- `pending` - Afventer
- `approved` - Godkendt
- `rejected` - Afvist
- `expired` - Udløbet

**Decision Body:**
```json
{
  "approved": true,
  "reason": "Godkendt af admin",
  "modifications": {}
}
```

---

### Infrastructure

| Method | Endpoint | Beskrivelse |
|--------|----------|-------------|
| GET | `/infrastructure/status` | Infrastruktur status |
| GET | `/infrastructure/connectors` | Liste connectors |
| GET | `/knowledge/status` | Viden sync status |

---

### State Management

| Method | Endpoint | Beskrivelse | Query Params |
|--------|----------|-------------|--------------|
| GET | `/state/stats` | State manager statistik | - |
| GET | `/state/active-tasks` | Aktive persisterede tasks | `kommandant_id` |
| POST | `/state/recover/{kommandant_id}` | Gendan tasks | - |

---

### Specialists

| Method | Endpoint | Beskrivelse | Query Params |
|--------|----------|-------------|--------------|
| GET | `/specialists/metrics` | Top specialists | `limit` |
| GET | `/specialists/{specialist_id}/metrics` | Specialist metrics | - |

---

### WebSocket Streaming

| Protocol | Endpoint | Beskrivelse |
|----------|----------|-------------|
| WS | `/stream` | Real-time event stream |

**Event Types:**
- `connection.established` - Forbindelse oprettet
- `heartbeat` - Keepalive
- `task.created`, `task.updated`, `task.paused`, `task.resumed`, `task.cancelled`
- `agent.status_changed`
- `hitl.requested`, `hitl.approved`, `hitl.rejected`
- `room.activity`

---

## TEST KOMMANDOER

```bash
# System overview
curl http://localhost:7777/api/ckc/overview

# Liste tasks
curl http://localhost:7777/api/ckc/tasks

# Liste agenter
curl http://localhost:7777/api/ckc/agents

# Liste rum
curl http://localhost:7777/api/ckc/rooms

# Afventende HITL
curl http://localhost:7777/api/ckc/hitl/pending

# Infrastructure status
curl http://localhost:7777/api/ckc/infrastructure/status
```

---

## FOLDER SWITCHER (11 NYE ENDPOINTS)

**Ny i v1.3.5** - Super Admin folder navigation

| Method | Endpoint | Beskrivelse |
|--------|----------|-------------|
| GET | `/folders` | List alle folders (15 total) |
| GET | `/folders/current` | Nuværende folder kontekst |
| POST | `/folders/switch` | Skift til folder |
| GET | `/folders/{id}` | Folder detaljer |
| GET | `/folders/{id}/contents` | Folder filindhold |
| POST | `/folders/custom` | Tilføj custom folder |
| DELETE | `/folders/custom/{id}` | Fjern custom folder |
| GET | `/folders/favorites` | List favorites |
| POST | `/folders/favorites/{id}` | Toggle favorite |
| GET | `/folders/recent` | Seneste 5 folders |
| GET | `/folders/status` | Switcher status |

**Switch Request Body:**
```json
{
  "folder_id": "mastermind",
  "method": "dropdown"  // dropdown, sidebar, terminal
}
```

**Folders:**
- 6 frozen (CKC-COMPONENTS)
- 9 active (cirkelline/ckc)
- + custom user folders

---

## FIL PLACERING

| Fil | Beskrivelse |
|-----|-------------|
| `cirkelline/ckc/api/control_panel.py` | 834 linjer - Control Panel |
| `cirkelline/ckc/api/folder_switcher.py` | ~350 linjer - Folder Switcher |
| `cirkelline/ckc/folder_context.py` | ~300 linjer - Data models |
| `cirkelline/ckc/folder_switcher.py` | ~500 linjer - Core logic |
| `cirkelline/ckc/api/__init__.py` | Router registration |
| `my_os.py:230` | Router mount: `prefix="/api/ckc"` |
| `tests/test_ckc_control_panel.py` | 509 linjer - Test suite |

---

## PYDANTIC MODELS

| Model | Formål |
|-------|--------|
| `TaskSummary` | Task info |
| `AgentSummary` | Agent info |
| `RoomSummary` | Rum info |
| `HITLRequest` | HITL anmodning |
| `HITLDecision` | HITL beslutning |
| `SystemOverview` | System status |
| `FolderSwitchRequest` | Folder switch request |
| `FolderListResponse` | Folder liste response |
| `FolderSwitchResponse` | Switch operation response |

---

*Dokumentation opdateret: 2025-12-17 ~14:15*
*Af: Kommandør #4*
*Version: v1.3.5*
*Endpoints: 36 total (25 Control Panel + 11 Folder Switcher)*
