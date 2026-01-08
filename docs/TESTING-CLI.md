# CLI Testing Guide

**Version:** 1.2.34
**File:** `test_cli.py`

---

## What is CLI Testing?

CLI testing lets you talk to Cirkelline directly from your terminal, bypassing the web UI and API layer. This is useful for:

- **Quick testing** - No need to start frontend
- **Debugging** - See exactly what the AI is doing
- **Isolation** - Test AI logic without HTTP/UI complexity
- **Development** - Faster iteration when working on agents

---

## How It Works

### Normal Flow (Web UI)

```
Browser → Frontend → HTTP → Backend → Cirkelline Team → Response → HTTP → Frontend → Browser
```

### CLI Flow

```
Terminal → Cirkelline Team → Response → Terminal
```

**Key difference:** No web server, no frontend, no HTTP. Just Python talking directly to the AGNO Team.

---

## Prerequisites

1. **PostgreSQL database running:**
   ```bash
   docker start cirkelline-postgres
   ```

2. **Virtual environment activated:**
   ```bash
   cd ~/Desktop/cirkelline
   source .venv/bin/activate
   ```

3. **Environment variables loaded** (automatic via `.venv/bin/activate`)

---

## Usage

### Basic Usage (Quick Search Mode)

```bash
python test_cli.py
```

### Deep Research Mode

```bash
python test_cli.py --deep-research
```

### With Debug Output

```bash
python test_cli.py --debug
```

### Continue a Previous Session

```bash
python test_cli.py --session-id "your-session-id-here"
```

### Custom User ID

```bash
python test_cli.py --user-id "another-user-uuid"
```

### All Options

```bash
python test_cli.py --help
```

Output:
```
usage: test_cli.py [-h] [--deep-research] [--debug] [--user-id USER_ID]
                   [--session-id SESSION_ID]

Cirkelline CLI Testing Tool

options:
  -h, --help            show this help message and exit
  --deep-research       Enable Deep Research mode
  --debug               Enable debug output
  --user-id USER_ID     User ID for knowledge filtering (default: Ivo's ID)
  --session-id SESSION_ID
                        Session ID to continue a previous conversation
```

---

## What Works in CLI Mode

| Feature | Works? | Notes |
|---------|--------|-------|
| Streaming responses | Yes | Real-time output |
| Tool calls | Yes | Search, reasoning, etc. |
| Session persistence | Yes | Stored in database |
| User memories | Yes | Loaded from database |
| Knowledge base search | Yes | Filtered by user_id |
| Deep Research mode | Yes | Use `--deep-research` flag |
| Debug output | Yes | Use `--debug` flag |

---

## What Does NOT Work in CLI Mode

| Feature | Why |
|---------|-----|
| File uploads | No file picker in terminal |
| Google integration | Requires OAuth browser flow |
| Web UI sidebar | No UI |
| Real-time UI updates | No frontend |
| Multiple concurrent users | Single terminal session |

---

## Example Session

```
============================================================
CIRKELLINE CLI TEST MODE
============================================================

Mode: Quick Search
User ID: 62563835-4e00-43b6-b...
Debug: Disabled

Type your messages and press Enter.
Type 'exit', 'quit', or 'bye' to stop.

============================================================

🧪 Tester: Hello!

🤖 Cirkelline: Hey there! How can I help you today?

🧪 Tester: What's the latest AI news?

🤖 Cirkelline: [Uses DuckDuckGo to search for news]

Here's what I found about AI news today:
- OpenAI announced...
- Google released...
[continues with news]

🧪 Tester: exit

Goodbye!
```

---

## Testing Specific Features

### Test Knowledge Base

```
🧪 Tester: What documents have I uploaded?
🧪 Tester: Search my knowledge base for "contract"
```

### Test Research Team (Deep Research Mode)

```bash
python test_cli.py --deep-research
```

```
🧪 Tester: Research the best CRM platforms for small businesses
```

### Test Memories

```
🧪 Tester: Remember that my favorite color is blue
🧪 Tester: What's my favorite color?
```

### Test Search Tool Selection

```
🧪 Tester: What's today's news?  (should use DuckDuckGo)
🧪 Tester: How do AI agents work?  (should use Exa)
🧪 Tester: Compare React vs Vue in detail  (should use Tavily)
```

---

## Debug Mode

Enable debug mode to see:
- System prompts
- Tool calls with arguments
- Member agent responses
- Internal decision making

```bash
python test_cli.py --debug
```

This is equivalent to setting:
```python
cirkelline.debug_mode = True
cirkelline.show_members_responses = True
```

---

## Technical Details

### Session State

The CLI sets up the same `session_state` as the API endpoint:

```python
session_state = {
    "current_user_id": user_id,
    "current_user_type": "Admin",
    "current_user_name": "CLI Tester",
    "current_tier_slug": "elite",
    "current_tier_level": 5,
    "deep_research": deep_research_flag,
    "current_user_timezone": "UTC",
    "current_user_datetime": "...",
}
```

This ensures:
- Knowledge base filtering works (uses `current_user_id`)
- Callable instructions work (reads `deep_research` flag)
- User personalization works (reads user context)

### AGNO Workaround

The CLI applies the same workaround as the API endpoint:

```python
cirkelline.session_state = session_state
```

This is required because AGNO doesn't automatically set `agent.session_state` during `run()`. Callable instructions access it via `agent.session_state`, so we must set it manually.

### Deep Research Mode

When `--deep-research` is enabled, the CLI:

1. Removes `ExaTools` and `TavilyTools` from Cirkelline's tools
2. Sets `deep_research: True` in session_state
3. Callable instructions return different prompts (without search tool mentions)
4. Cirkelline delegates to Research Team instead of searching directly

---

## Troubleshooting

### "Database connection error"

Make sure PostgreSQL is running:
```bash
docker start cirkelline-postgres
```

### "Module not found"

Make sure virtual environment is activated:
```bash
source .venv/bin/activate
```

### "API key error"

Check that your `.venv/bin/activate` exports `GOOGLE_API_KEY`:
```bash
echo $GOOGLE_API_KEY
```

### "Rate limit exceeded"

The CLI doesn't have retry logic like the API endpoint. Wait a moment and try again.

---

## Comparison: CLI vs Web UI vs API Testing

| Aspect | CLI (`test_cli.py`) | Web UI | API (`curl`) |
|--------|---------------------|--------|--------------|
| Setup | Just run Python | Start both frontend + backend | Start backend |
| Auth | Bypass (hardcoded user_id) | Full login flow | JWT token |
| Debug | Built-in `--debug` flag | Browser console | Backend logs |
| Speed | Fastest | Slowest | Medium |
| Isolation | Tests AI only | Tests everything | Tests API + AI |
| File uploads | No | Yes | Yes |
| Google integration | No | Yes | Yes |

---

## When to Use CLI Testing

**Use CLI when:**
- Developing/debugging agent logic
- Testing tool selection
- Testing Deep Research mode
- Quick smoke tests
- Exploring memories/knowledge base

**Use Web UI when:**
- Testing full user flow
- Testing Google integrations
- Testing file uploads
- User acceptance testing

**Use API testing when:**
- Testing authentication
- Testing streaming
- Testing error handling
- Integration testing

---

## Related Documentation

- `docs/TESTING.md` - Full testing guide
- `docs(new)/teams/06-run-as-cli.md` - AGNO cli_app() reference
- `cirkelline/endpoints/custom_cirkelline.py` - API endpoint implementation
