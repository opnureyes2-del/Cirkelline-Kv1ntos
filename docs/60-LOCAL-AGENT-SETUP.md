# LOCAL AGENT SETUP GUIDE

**Version:** v1.0.0
**Dato:** 2025-12-17
**Status:** KOMPLET

---

## OVERBLIK

Denne guide beskriver hvordan du sætter en lokal lærende agent op til Cirkelline udvikling.

### Komponenter

| Komponent | Lokation | Formål |
|-----------|----------|--------|
| **Custom Commands** | `.claude/commands/` | Slash commands til Claude Code |
| **Persistent Agent** | `~/.claude-agent/` | Python agent med memory |
| **Memory System** | `~/.claude-agent/memories/` | Persistent læring |

---

## TIER 1: CUSTOM COMMANDS

### Installation

Opret `.claude/commands/` i dit projekt:

```bash
mkdir -p .claude/commands
```

### Tilgængelige Commands

| Command | Beskrivelse |
|---------|-------------|
| `/learn <path>` | Analyser kode og gem læring |
| `/review <path>` | Review med lært kontekst |
| `/pattern <path>` | Find og gem patterns |
| `/assistant <spørgsmål>` | Mini-assistent med kontekst |

### learn.md

```markdown
# Lær fra Kodebasen

Analyser den angivne kode eller mappe og gem læring til memory.

## Instruktioner

1. **Scan koden** for:
   - Arkitektoniske mønstre
   - Navngivningskonventioner
   - Import struktur

2. **Gem læring til**:
   ~/.claude-agent/memories/

$ARGUMENTS
```

### review.md

```markdown
# Review med Lært Kontekst

Reviewer kode ved at bruge tidligere lært kontekst fra memory.

## Instruktioner

1. **Load Memory først**
2. **Analyser koden mod** tidligere lærte mønstre
3. **Output** konsistens score og anbefalinger

$ARGUMENTS
```

---

## TIER 2: PERSISTENT AGENT

### Installation

```bash
# 1. Opret agent mappe
mkdir -p ~/.claude-agent/memories/patterns ~/.claude-agent/logs

# 2. Kopier agent script
# (Se persistent-agent.py nedenfor)

# 3. Opret wrapper
cat > ~/.local/bin/cirkelline-agent << 'EOF'
#!/bin/bash
cd ~/.claude-agent
python3 persistent-agent.py "$@"
EOF
chmod +x ~/.local/bin/cirkelline-agent

# 4. Tilføj til PATH (hvis nødvendigt)
export PATH="$HOME/.local/bin:$PATH"
```

### persistent-agent.py

Fuld implementation i `~/.claude-agent/persistent-agent.py`:

```python
#!/usr/bin/env python3
"""
Cirkelline Persistent Learning Agent
"""

from anthropic import Anthropic
from pathlib import Path
from datetime import datetime
import json
import re

MEMORY_DIR = Path.home() / ".claude-agent" / "memories"

class CirkellineAgent:
    def __init__(self):
        self.client = Anthropic()
        self.memory = MemorySystem()
        self.conversation_history = []

    def chat(self, message: str) -> str:
        """Send besked med memory kontekst."""
        system_prompt = self._build_system_prompt()

        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=self.conversation_history
        )

        assistant_message = response.content[0].text
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Auto-save learnings
        self._save_learnings(assistant_message)

        return assistant_message

# Full implementation: ~/.claude-agent/persistent-agent.py
```

### Brug

```bash
# Start interaktiv agent
cirkelline-agent

# Kommandoer i agent:
/analyze cirkelline/ckc/folder_switcher.py  # Analyser fil
/learn                                        # Vis læringer
/memory                                       # Vis loaded memory
/deep                                         # Brug Opus model
/fast                                         # Brug Sonnet model
/quit                                         # Afslut
```

---

## MEMORY SYSTEM

### Struktur

```
~/.claude-agent/
├── persistent-agent.py     # Hovedagent
├── memories/
│   ├── cirkelline_patterns.md  # Lærte mønstre
│   ├── conventions.md          # Konventioner
│   ├── architecture.md         # Arkitektur
│   └── patterns/
│       ├── agno.md             # AGNO patterns
│       ├── api.md              # API patterns
│       └── ckc.md              # CKC patterns
└── logs/
    └── interactions_YYYY-MM-DD.jsonl
```

### Memory Format

Memory filer er Markdown med timestampede entries:

```markdown
# Cirkelline Patterns Memory

## 2025-12-17 22:00
Folder Switcher bruger singleton pattern via `get_folder_switcher()`.

## 2025-12-17 22:15
AGNO agents defineres med `@agent` decorator og `Team` for multi-agent.
```

### Auto-Learning

Agenten gemmer automatisk læringer når den ser:

```
[LEARNING: patterns: Beskrivelse af mønster]
[LEARNING: conventions: Beskrivelse af konvention]
[LEARNING: architecture: Arkitektur indsigt]
```

---

## INTEGRATION MED CLAUDE CODE

### Workflow

1. **Start session**: Brug `/assistant` for hurtig hjælp
2. **Dyb analyse**: Brug `/learn` til at lære fra kode
3. **Review**: Brug `/review` til kontekst-bevidst review
4. **Persistent agent**: Start `cirkelline-agent` for længere sessioner

### Eksempel Session

```bash
# I Claude Code
/learn cirkelline/orchestrator/
# → Agenten analyserer og gemmer mønstre

/review cirkelline/agents/new_agent.py
# → Review med reference til lærte mønstre

# I terminal (for længere arbejde)
cirkelline-agent
Du: Hjælp mig oprette en ny AGNO agent
# → Agenten bruger memory til at give kontekst-bevidst hjælp
```

---

## TROUBLESHOOTING

| Problem | Løsning |
|---------|---------|
| Commands ikke fundet | Check `.claude/commands/` eksisterer |
| Agent import fejl | `pip install anthropic` |
| Memory ikke loaded | Check `~/.claude-agent/memories/` |
| API key mangler | `export ANTHROPIC_API_KEY=...` |

---

## NÆSTE SKRIDT

1. [ ] Tilføj MCP server integration
2. [ ] WebSocket live updates
3. [ ] Database-backed memory
4. [ ] Team-based agents

---

*Dokumentation oprettet: 2025-12-17*
*System: Cirkelline v1.3.5*
