# CKC FOLDER SWITCHER - DESIGN NOTES

**Created:** 2025-12-17 00:30
**Agent:** Kommandør #4
**Version:** v1.3.5

---

## DESIGN DECISIONS

### 1. File-based State Persistence
**Valg:** JSON fil i `~/.ckc/folder_preferences.json`

**Begrundelse:**
- Simpel implementation (ingen database dependency)
- Let at debugge og inspicere
- God nok for single-user (Super Admin)
- Kan nemt migreres til database senere

### 2. Folder ID Naming Convention
**Valg:** Prefix-baseret naming

| Kategori | Prefix | Eksempel |
|----------|--------|----------|
| CKC-COMPONENTS | `ckc-` | `ckc-mastermind` |
| cirkelline/ckc | Ingen | `mastermind` |
| Custom | `custom-` | `custom-my-folder` |

**Begrundelse:**
- Undgår ID konflikt mellem CKC-COMPONENTS og cirkelline/ckc `mastermind`
- Let at identificere folder type fra ID
- Custom prefix gør det nemt at validere sletning

### 3. Three Interface Approach
**Valg:** Dropdown + Sidebar + Terminal (alle tre)

**Begrundelse:**
- Dropdown: Hurtig switching for daglig brug
- Sidebar: Visual navigation for overblik
- Terminal: Power user features og scripting

### 4. Singleton Pattern for Switcher
**Valg:** `get_folder_switcher()` singleton

**Begrundelse:**
- Konsistent state på tværs af API, Terminal og SuperAdmin
- Undgår multiple instances der scanner samme folders
- Event handlers kan registreres globalt

---

## INTEGRATION POINTS

```
┌─────────────────────────────────────────────────────────────┐
│                    USER (Super Admin)                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Dropdown   │  │   Sidebar    │  │   Terminal   │       │
│  │   (Future)   │  │   (Future)   │  │  (KV1NT)     │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │                │
│         └────────────────┬┴─────────────────┘                │
│                          ↓                                   │
│                ┌─────────────────────┐                       │
│                │ REST API Endpoints  │ ← 11 endpoints        │
│                │ /api/ckc/folders/*  │                       │
│                └─────────┬───────────┘                       │
│                          ↓                                   │
│                ┌─────────────────────┐                       │
│                │ CKCFolderSwitcher   │ ← Core logic          │
│                │ (singleton)         │                       │
│                └─────────┬───────────┘                       │
│                          ↓                                   │
│  ┌───────────────────────┴────────────────────────┐         │
│  │                                                 │         │
│  ↓                                                 ↓         │
│ ┌─────────────────────┐          ┌─────────────────────┐    │
│ │ SuperAdminControl   │          │ ~/.ckc/preferences  │    │
│ │ System              │          │ (state persistence) │    │
│ │ - folder_context    │          └─────────────────────┘    │
│ │ - dashboard zone    │                                     │
│ └─────────────────────┘                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## EVENT BROADCASTING

| Event Type | Trigger | Payload |
|------------|---------|---------|
| `folder.switched` | switch_folder() | event + folder_info |
| `folder.switch_failed` | switch_folder() fejl | event med error |
| `folder.custom_added` | add_custom_folder() | folder_info |
| `folder.custom_removed` | remove_custom_folder() | folder_id |
| `folder.favorite_toggled` | toggle_favorite() | folder_id, is_favorite |

---

## KNOWN LIMITATIONS

1. **Concurrent Access:** Simpel fil-baseret state understøtter ikke concurrent access fra multiple sessions
2. **No Real-time Sync:** Folder changes scanner ikke automatisk (kræver re-init)
3. **No Frontend:** Dropdown og Sidebar er fremtidigt arbejde (kun API ready)

---

## FREMTIDIGT ARBEJDE

1. [ ] Frontend dropdown component (React/Next.js)
2. [ ] Sidebar tree view component
3. [ ] WebSocket integration for live folder updates
4. [ ] Database-backed state for multi-session support
5. [ ] File watcher for auto-reload ved folder ændringer

---

## TEST KOMMANDOER

```bash
# Test API
curl http://localhost:7777/api/ckc/folders | jq
curl http://localhost:7777/api/ckc/folders/current | jq
curl -X POST http://localhost:7777/api/ckc/folders/switch \
  -H "Content-Type: application/json" \
  -d '{"folder_id": "mastermind", "method": "api"}' | jq

# Test Terminal
python -m cirkelline.ckc.terminal
> await ckc.list_folders()
> await ckc.switch_folder("mastermind")
```

---

*Agent 4/4 (Kommandør)*
*2025-12-17 00:30*
