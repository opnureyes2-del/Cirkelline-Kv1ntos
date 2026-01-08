# CKC FOLDER SWITCHER - SUPER ADMIN GUIDE

**Version:** v1.3.5
**Dato:** 2025-12-17
**Status:** KOMPLET

---

## OVERBLIK

CKC Folder Switcher giver Super Admin mulighed for at navigere mellem alle CKC mapper i systemet via:

1. **API Endpoints** - REST API til programmatisk adgang
2. **Terminal Commands** - KV1NT terminal kommandoer
3. **Dashboard** - UI integration (fremtid)

### Folder Kategorier

| Kategori | Antal | Status | Beskrivelse |
|----------|-------|--------|-------------|
| **CKC-COMPONENTS** | 6 | Frozen | Låste komponenter med version |
| **cirkelline/ckc** | 9 | Active | Aktive udviklings-moduler |
| **Custom** | 0+ | Active | Brugerdefinerede mapper |

---

## CKC FOLDERS (15 Total)

### CKC-COMPONENTS (6 Frozen)

Disse mapper er låst og kan ikke ændres:

| ID | Display Name | Kategori | Beskrivelse |
|----|--------------|----------|-------------|
| `ckc-legal-kommandant` | Legal Kommandant | kommandanter | Juridisk specialist |
| `ckc-web3-kommandant` | Web3 Kommandant | kommandanter | Web3/Blockchain specialist |
| `ckc-research-team` | Research Team | teams | Research og analyse |
| `ckc-law-team` | Law Team | teams | Juridisk team |
| `ckc-mastermind` | Mastermind | systems | Strategisk system |
| `ckc-kv1nt` | KV1NT | systems | Terminal partner |

**Lokation:** `CKC-COMPONENTS/{category}/{folder-name}/`

### cirkelline/ckc (9 Active)

Disse mapper er aktive og kan udvikles:

| ID | Display Name | Python Files | Beskrivelse |
|----|--------------|--------------|-------------|
| `mastermind` | Mastermind | 77 | Orchestration og kontrol |
| `tegne_enhed` | Tegne Enhed | 11 | Visuel output generation |
| `kommandant` | Kommandant | 9 | Kommandant base system |
| `infrastructure` | Infrastructure | 17 | Infrastruktur komponenter |
| `integrations` | Integrations | 7 | Eksterne integrationer |
| `web3` | Web3 | 9 | Web3/Blockchain moduler |
| `connectors` | Connectors | 11 | System connectors |
| `api` | API | 7 | API endpoints og routes |
| `aws` | AWS | 5 | AWS cloud integration |

**Lokation:** `cirkelline/ckc/{folder-name}/`

---

## API ENDPOINTS

### Base URL
```
/api/ckc/folders
```

### Endpoints (11 total)

| Method | Endpoint | Beskrivelse |
|--------|----------|-------------|
| GET | `/api/ckc/folders` | List alle folders |
| GET | `/api/ckc/folders/current` | Hent nuværende context |
| POST | `/api/ckc/folders/switch` | Skift aktiv folder |
| GET | `/api/ckc/folders/{id}` | Hent folder detaljer |
| GET | `/api/ckc/folders/{id}/contents` | Hent folder indhold |
| POST | `/api/ckc/folders/custom` | Tilføj custom folder |
| DELETE | `/api/ckc/folders/custom/{id}` | Fjern custom folder |
| GET | `/api/ckc/folders/favorites` | List favoritter |
| POST | `/api/ckc/folders/favorites/{id}` | Toggle favorit |
| GET | `/api/ckc/folders/recent` | List recent folders |
| GET | `/api/ckc/folders/status` | Switcher status |

### Eksempler

#### List Alle Folders
```bash
curl http://localhost:7777/api/ckc/folders
```

**Response:**
```json
{
  "folders": [
    {
      "folder_id": "mastermind",
      "display_name": "Mastermind",
      "category": "cirkelline_ckc",
      "status": "active",
      "frozen": false,
      "files_count": 153,
      "python_files_count": 77
    },
    ...
  ],
  "total": 15,
  "by_category": {
    "ckc_components": 6,
    "cirkelline_ckc": 9,
    "custom": 0
  }
}
```

#### Skift Folder
```bash
curl -X POST http://localhost:7777/api/ckc/folders/switch \
  -H "Content-Type: application/json" \
  -d '{"folder_id": "mastermind", "method": "api"}'
```

**Response:**
```json
{
  "success": true,
  "event_id": "abc123...",
  "from_folder": null,
  "to_folder": "mastermind",
  "message": "Switched to Mastermind"
}
```

#### Tilføj Custom Folder
```bash
curl -X POST http://localhost:7777/api/ckc/folders/custom \
  -H "Content-Type: application/json" \
  -d '{"path": "/home/rasmus/my-project", "name": "My Project"}'
```

---

## TERMINAL KOMMANDOER

Via KV1NT terminal kan Super Admin bruge følgende kommandoer:

### Kommando Reference

```python
# List alle folders
await ckc.list_folders()
await ckc.list_folders("ckc_components")    # Filter

# Skift folder
await ckc.switch_folder("mastermind")
await ckc.switch_folder("ckc-legal-kommandant")

# Folder info
await ckc.folder_info("mastermind")
await ckc.folder_contents("mastermind")

# Custom folders
await ckc.add_custom_folder("/path/to/folder", "Display Name")
await ckc.remove_custom_folder("custom-folder-name")

# Favoritter
await ckc.toggle_favorite("mastermind")
await ckc.favorite_folders()

# Recent
await ckc.recent_folders()
```

### Eksempel Output

```
CKC FOLDERS
═══════════════════════════════════════════════════════════

  CKC_COMPONENTS (Frozen):
    🔒 ckc-legal-kommandant - Legal Kommandant
    🔒 ckc-web3-kommandant - Web3 Kommandant
    🔒 ckc-research-team - Research Team
    🔒 ckc-law-team - Law Team
    🔒 ckc-mastermind - Mastermind
    🔒 ckc-kv1nt - KV1NT

  CIRKELLINE_CKC (Active):
  → 📂 mastermind - Mastermind (77 files)
    📂 tegne_enhed - Tegne Enhed (11 files)
    📂 kommandant - Kommandant (9 files)
    📂 infrastructure - Infrastructure (17 files)
    📂 integrations - Integrations (7 files)
    📂 web3 - Web3 (9 files)
    📂 connectors - Connectors (11 files)
    📂 api - API (7 files)
    📂 aws - AWS (5 files)

═══════════════════════════════════════════════════════════
→ indicates current folder
```

---

## STATE PERSISTENCE

Folder switcher gemmer tilstand til:

```
~/.ckc/folder_preferences.json
```

### Format

```json
{
  "user_id": "rasmus_super_admin",
  "current_folder_id": "mastermind",
  "recent_folders": [
    "mastermind",
    "tegne_enhed",
    "api"
  ],
  "favorite_folders": [
    "mastermind",
    "ckc-kv1nt"
  ],
  "custom_folders": [
    "/home/rasmus/my-custom-project"
  ],
  "last_switch": "2025-12-17T22:00:00Z",
  "switch_count": 15
}
```

---

## ARKITEKTUR

### Filer

| Fil | Linjer | Beskrivelse |
|-----|--------|-------------|
| `cirkelline/ckc/folder_context.py` | 389 | Data models, enums, constants |
| `cirkelline/ckc/folder_switcher.py` | 772 | Core switching logic |
| `cirkelline/ckc/api/folder_switcher.py` | 350 | REST API endpoints |
| `tests/test_folder_switcher.py` | 350 | Unit tests (26 tests) |

### Integration Points

```
SuperAdminControlSystem
    └── folder_switcher: CKCFolderSwitcher
            ├── _folders: Dict[str, CKCFolderInfo]
            ├── _state: FolderContextState
            └── _event_handlers: List[Callable]

CKCTerminal
    └── folder_switcher: CKCFolderSwitcher
            └── (same instance via singleton)

API Router (/api/ckc/folders)
    └── get_folder_switcher()
            └── (singleton pattern)
```

### DashboardZone

Folder Switcher er integreret i SuperAdmin Dashboard som:

```python
class DashboardZone(Enum):
    ...
    CKC_FOLDERS = "ckc_folders"  # v1.3.5
```

---

## TEST DÆKNING

### Unit Tests

```
tests/test_folder_switcher.py

Test Classes:
- TestFolderEnums (3 tests)
- TestCKCFolderInfo (3 tests)
- TestFolderSwitchEvent (3 tests)
- TestFolderContextState (5 tests)
- TestFolderConstants (6 tests)
- TestCKCFolderSwitcher (4 tests)
- TestSingleton (1 test)
- TestAsyncFolderSwitcher (7 async tests)

Total: 33 tests (26 sync, 7 async)
```

### Kør Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_folder_switcher.py -v
```

---

## EVENTS

Folder Switcher broadcaster følgende events:

| Event Type | Trigger | Payload |
|------------|---------|---------|
| `folder.switched` | Efter folder skift | folder_id, method, user_id |
| `folder.switch_failed` | Ved fejlet skift | error_message |
| `folder.custom_added` | Custom folder tilføjet | folder info |
| `folder.custom_removed` | Custom folder fjernet | folder_id |
| `folder.favorite_toggled` | Favorite ændret | folder_id, is_favorite |

---

## BEST PRACTICES

1. **Brug terminal til hurtig navigation**
   ```python
   await ckc.switch_folder("mastermind")
   ```

2. **Marker ofte brugte som favoritter**
   ```python
   await ckc.toggle_favorite("mastermind")
   ```

3. **Custom folders til projekt-specifik kontekst**
   ```python
   await ckc.add_custom_folder("/project/path", "Project Name")
   ```

4. **Check recent for hurtig tilbage-navigation**
   ```python
   await ckc.recent_folders()  # Sidste 5 besøgte
   ```

---

## FREMTIDIGE UDVIDELSER

- [ ] Dashboard UI dropdown
- [ ] Sidebar træ-visning
- [ ] WebSocket live updates
- [ ] Folder tagging system
- [ ] Search across folders

---

*Dokumentation oprettet: 2025-12-17*
*System: Cirkelline v1.3.5*
*Agent: Opus 4.5*
