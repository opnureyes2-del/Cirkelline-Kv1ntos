# BYTEOS ↔ CIRKELLINE CHAT INTEGRATION

**Dato:** 2025-12-18
**Version:** v1.0.0
**System:** Unified Local Ecosystem

---

## OVERBLIK

ByteOS og Cirkelline Chat arbejder sammen som et **unified local system**:

```
┌────────────────────────────────────────────────────────────────────┐
│                    UNIFIED LOCAL ECOSYSTEM                          │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌──────────────┐         ┌──────────────┐                       │
│   │   BYTEOS     │◄───────►│  CIRKELLINE  │                       │
│   │   Agent      │   API   │    Chat      │                       │
│   │  (Terminal)  │         │  (Backend)   │                       │
│   └──────────────┘         └──────────────┘                       │
│          │                        │                                │
│          │                        │                                │
│          ▼                        ▼                                │
│   ┌──────────────┐         ┌──────────────┐                       │
│   │   OLLAMA     │         │   FRONTEND   │                       │
│   │   LLM        │         │   Next.js    │                       │
│   │  :11434      │         │   :3000      │                       │
│   └──────────────┘         └──────────────┘                       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 1. CIRKELLINE CHAT API ENDPOINTS

### 1.1 Basis Information

| Parameter | Værdi |
|-----------|-------|
| **Base URL** | `http://localhost:7777` |
| **Auth** | JWT Bearer Token |
| **Content-Type** | `multipart/form-data` eller `application/json` |
| **Response** | JSON eller SSE stream |

### 1.2 Authentication

**Login endpoint:**
```bash
POST http://localhost:7777/api/auth/login
Content-Type: application/json

{
  "email": "opnureyes2@gmail.com",
  "password": "YOUR_PASSWORD"
}

# Response:
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {...}
}
```

**Token bruges i alle efterfølgende requests:**
```
Authorization: Bearer <token>
```

### 1.3 Chat Endpoint

**Send besked til Cirkelline:**
```bash
POST http://localhost:7777/teams/cirkelline/runs
Authorization: Bearer <token>
Content-Type: multipart/form-data

message=Hej Cirkelline!
user_id=<user-uuid>
session_id=<session-uuid>  # Optional: ny chat hvis tom
stream=true                 # SSE streaming
deep_research=false         # false = hurtig, true = grundig
```

### 1.4 Sessions API

**Hent sessions:**
```bash
GET http://localhost:7777/sessions
Authorization: Bearer <token>
```

**Hent session messages:**
```bash
GET http://localhost:7777/sessions/{session_id}/messages
Authorization: Bearer <token>
```

### 1.5 Health Check

```bash
GET http://localhost:7777/health
# Response: {"status": "healthy", ...}

GET http://localhost:7777/config
# Response: {"agents": [...], "teams": [...]}
```

---

## 2. BYTEOS → CHAT INTEGRATION

### 2.1 Python Client Klasse

```python
# ~/.claude-agent/cirkelline_client.py

import httpx
import json
from typing import Optional, AsyncGenerator

class CirkellineClient:
    """
    Client for ByteOS → Cirkelline Chat integration.
    Kører 100% lokalt på port 7777.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:7777",
        email: str = "opnureyes2@gmail.com",
        password: str = None
    ):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None

    async def login(self) -> bool:
        """Authenticate with Cirkelline backend."""
        if not self.password:
            raise ValueError("Password required for login")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/auth/login",
                json={"email": self.email, "password": self.password}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["token"]
                self.user_id = data.get("user", {}).get("id")
                return True
            return False

    def _headers(self) -> dict:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.token}"}

    async def send_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        deep_research: bool = False,
        stream: bool = False
    ) -> dict:
        """
        Send message to Cirkelline chat.

        Args:
            message: User message
            session_id: Existing session or None for new
            deep_research: True for comprehensive research
            stream: True for SSE streaming

        Returns:
            Response dict with content and metadata
        """
        if not self.token:
            raise RuntimeError("Not authenticated. Call login() first.")

        form_data = {
            "message": message,
            "user_id": self.user_id,
            "stream": str(stream).lower(),
            "deep_research": str(deep_research).lower()
        }

        if session_id:
            form_data["session_id"] = session_id

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/teams/cirkelline/runs",
                headers=self._headers(),
                data=form_data
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise RuntimeError(f"Chat failed: {response.text}")

    async def stream_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        deep_research: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from Cirkelline via SSE.

        Yields:
            Content chunks as they arrive
        """
        if not self.token:
            raise RuntimeError("Not authenticated. Call login() first.")

        form_data = {
            "message": message,
            "user_id": self.user_id,
            "stream": "true",
            "deep_research": str(deep_research).lower()
        }

        if session_id:
            form_data["session_id"] = session_id

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/teams/cirkelline/runs",
                headers=self._headers(),
                data=form_data
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "content" in chunk:
                                yield chunk["content"]
                        except json.JSONDecodeError:
                            pass

    async def get_sessions(self) -> list:
        """Get all user sessions."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/sessions",
                headers=self._headers()
            )
            return response.json() if response.status_code == 200 else []

    async def get_session_messages(self, session_id: str) -> list:
        """Get messages from a specific session."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/sessions/{session_id}/messages",
                headers=self._headers()
            )
            return response.json() if response.status_code == 200 else []

    async def health_check(self) -> bool:
        """Check if Cirkelline backend is running."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False
```

### 2.2 ByteOS Integration

```python
# Tilføj til ~/.claude-agent/byteos-agent.py

from cirkelline_client import CirkellineClient

class ByteOS:
    def __init__(self):
        # ... existing init ...

        # Cirkelline Chat integration
        self.cirkelline = CirkellineClient(
            email="opnureyes2@gmail.com",
            password=os.getenv("CIRKELLINE_PASSWORD")
        )
        self._chat_authenticated = False

    async def ensure_chat_connected(self):
        """Ensure connection to Cirkelline Chat."""
        if not self._chat_authenticated:
            if await self.cirkelline.health_check():
                if await self.cirkelline.login():
                    self._chat_authenticated = True
                    print("✓ Connected to Cirkelline Chat")
                else:
                    print("✗ Chat login failed")
            else:
                print("✗ Cirkelline backend not running")
        return self._chat_authenticated

    async def delegate_to_cirkelline(
        self,
        task: str,
        use_deep_research: bool = False
    ) -> str:
        """
        Delegate a task to Cirkelline Chat system.

        Use this when:
        - Task requires multi-agent orchestration
        - Task needs specialist agents (Audio, Video, Legal, Research)
        - Task benefits from Cirkelline's full capabilities
        """
        if not await self.ensure_chat_connected():
            return "ERROR: Cannot connect to Cirkelline Chat"

        print(f"🔄 Delegating to Cirkelline: {task[:50]}...")

        try:
            response = await self.cirkelline.send_message(
                message=task,
                deep_research=use_deep_research
            )

            content = response.get("content", "No response")

            # Log delegation
            self._save_learning(
                f"[DELEGATION: cirkelline: {task[:100]}]"
            )

            return content

        except Exception as e:
            return f"ERROR delegating to Cirkelline: {e}"

    async def research_via_cirkelline(self, query: str) -> str:
        """
        Use Cirkelline's Research Team for comprehensive research.
        FREE: Uses DuckDuckGo via Research Team.
        """
        return await self.delegate_to_cirkelline(
            task=f"Research: {query}",
            use_deep_research=True
        )
```

---

## 3. TERMINAL KOMMANDOER

### 3.1 ByteOS Chat Commands

```bash
# I ByteOS interaktiv mode

rasmus@byteos:~$ /chat Hvad er status på mit system?
🔄 Delegating to Cirkelline...
📨 Cirkelline: [response from chat system]

rasmus@byteos:~$ /research Hvad er de seneste AI trends?
🔬 Research mode (DuckDuckGo)...
📊 Results: [research findings]

rasmus@byteos:~$ /sessions
📋 Your chat sessions:
1. [2025-12-18] "System status check"
2. [2025-12-17] "Backup strategi"
...
```

### 3.2 Implementering i byteos-agent.py

```python
# Tilføj til chat() metoden

async def handle_command(self, command: str) -> str:
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/chat":
        return await self.delegate_to_cirkelline(arg)

    elif cmd == "/research":
        return await self.research_via_cirkelline(arg)

    elif cmd == "/sessions":
        sessions = await self.cirkelline.get_sessions()
        return self._format_sessions(sessions)

    elif cmd == "/sync":
        # Sync ByteOS knowledge with Cirkelline
        return await self._sync_with_cirkelline()

    # ... other commands ...
```

---

## 4. SYNKRONISERING

### 4.1 ByteOS → Cirkelline Sync

ByteOS kan dele sine learnings med Cirkelline:

```python
async def _sync_with_cirkelline(self) -> str:
    """Sync ByteOS learnings to Cirkelline memory."""

    # Read ByteOS learnings
    learnings = self._load_recent_learnings()

    if not learnings:
        return "No new learnings to sync"

    # Send to Cirkelline via memories endpoint
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.cirkelline.base_url}/memories",
            headers=self.cirkelline._headers(),
            json={
                "content": f"ByteOS Sync: {learnings}",
                "source": "byteos_agent"
            }
        )

    if response.status_code == 200:
        return f"✓ Synced {len(learnings)} learnings to Cirkelline"
    return "✗ Sync failed"
```

### 4.2 Cirkelline → ByteOS Sync

Cirkelline kan dele viden tilbage:

```python
async def _fetch_cirkelline_context(self) -> dict:
    """Fetch relevant context from Cirkelline."""

    # Get recent sessions
    sessions = await self.cirkelline.get_sessions()

    # Get Cirkelline system status
    async with httpx.AsyncClient() as client:
        config = await client.get(
            f"{self.cirkelline.base_url}/config"
        )

    return {
        "recent_sessions": sessions[:5],
        "available_agents": config.json().get("agents", []),
        "available_teams": config.json().get("teams", [])
    }
```

---

## 5. EVENT FLOW

### 5.1 User → ByteOS → Cirkelline

```
1. User types in terminal: "Research AI trends 2025"

2. ByteOS receives command
   ├── Parses as research request
   └── Decides: "This needs Research Team"

3. ByteOS → Cirkelline API
   ├── POST /teams/cirkelline/runs
   ├── message="Research AI trends 2025"
   └── deep_research=true

4. Cirkelline Orchestrator
   ├── Analyzes request
   ├── Delegates to Research Team
   │   └── DuckDuckGo Researcher → News search
   └── Synthesizes response

5. Response → ByteOS
   ├── Displays to user
   ├── Extracts learnings
   └── Saves to memory

6. ByteOS updates memory:
   [LEARNING: research: AI trends 2025 include...]
```

### 5.2 Cirkelline → ByteOS Callback (Future)

```
1. Cirkelline detects system issue

2. Cirkelline → ByteOS webhook
   POST http://localhost:8765/webhook
   {"event": "system_alert", "data": {...}}

3. ByteOS handles alert
   ├── Checks system status
   ├── Takes corrective action
   └── Reports back to Cirkelline
```

---

## 6. SIKKERHED

### 6.1 Lokal-Only Mode

```python
# Sikrer at al trafik forbliver lokal

class CirkellineClient:
    ALLOWED_HOSTS = [
        "localhost",
        "127.0.0.1"
    ]

    def __init__(self, base_url: str):
        from urllib.parse import urlparse
        host = urlparse(base_url).hostname

        if host not in self.ALLOWED_HOSTS:
            raise ValueError(
                f"Only local connections allowed. Got: {host}"
            )

        self.base_url = base_url
```

### 6.2 Password Management

```bash
# Gem password sikkert (IKKE i koden!)

# Option 1: Environment variable
export CIRKELLINE_PASSWORD="your-password"

# Option 2: Secure file
echo "your-password" > ~/.cirkelline_password
chmod 600 ~/.cirkelline_password

# Option 3: Keyring (recommended)
python -c "import keyring; keyring.set_password('cirkelline', 'rasmus', 'password')"
```

---

## 7. FEJLFINDING

| Problem | Årsag | Løsning |
|---------|-------|---------|
| `Connection refused` | Backend ikke startet | `python my_os.py` |
| `401 Unauthorized` | Token udløbet | Kald `login()` igen |
| `Timeout` | Deep research tager tid | Øg timeout til 120s |
| `No content` | SSE parsing fejl | Check stream format |

### Debug Mode

```python
# Aktiver debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test connection
client = CirkellineClient()
print(await client.health_check())  # True/False
```

---

## 8. KOMPLET INTEGRATION TEST

```python
#!/usr/bin/env python3
"""Test ByteOS ↔ Cirkelline integration."""

import asyncio
import os
from cirkelline_client import CirkellineClient

async def test_integration():
    print("=== BYTEOS ↔ CIRKELLINE TEST ===\n")

    # 1. Health check
    client = CirkellineClient()
    print("1. Health check...")
    if await client.health_check():
        print("   ✓ Cirkelline backend running")
    else:
        print("   ✗ Backend not running!")
        return

    # 2. Authentication
    print("\n2. Authentication...")
    client.password = os.getenv("CIRKELLINE_PASSWORD")
    if await client.login():
        print(f"   ✓ Logged in as {client.email}")
        print(f"   ✓ User ID: {client.user_id}")
    else:
        print("   ✗ Login failed!")
        return

    # 3. Send test message
    print("\n3. Sending test message...")
    response = await client.send_message(
        message="Hej! Hvad er dit navn?",
        stream=False
    )
    print(f"   ✓ Response: {response.get('content', '')[:100]}...")

    # 4. Get sessions
    print("\n4. Fetching sessions...")
    sessions = await client.get_sessions()
    print(f"   ✓ Found {len(sessions)} sessions")

    print("\n=== ALL TESTS PASSED ===")

if __name__ == "__main__":
    asyncio.run(test_integration())
```

---

*Dokumentation oprettet: 2025-12-18*
*System: Cirkelline v1.3.5 + ByteOS v1.0.0*
