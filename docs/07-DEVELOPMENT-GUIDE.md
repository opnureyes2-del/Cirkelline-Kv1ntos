# DEVELOPMENT GUIDE

**Last Updated:** 2025-11-18
**Current Version:** v1.2.31

---

## Table of Contents
- [Local Environment Setup](#local-environment-setup)
- [Running the Project](#running-the-project)
- [Adding New Agents](#adding-new-agents)
  - [Adding ReasoningTools](#step-6-adding-reasoningtools-optional)
- [Adding API Endpoints](#adding-api-endpoints)
- [Adding Frontend Components](#adding-frontend-components)
- [Testing Procedures](#testing-procedures)
- [Git Workflow](#git-workflow)
- [Quick Reference](#quick-reference)

---

## Local Environment Setup

### Prerequisites

```bash
# Required Software
- Python 3.10+
- Node.js 18+
- Docker Desktop
- PostgreSQL client (psql)
- Git
```

### Backend Setup

#### 1. Clone Repository

```bash
cd ~/Desktop
git clone <repository-url> cirkelline
cd cirkelline
```

#### 2. Create Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate  # Windows
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
agno
fastapi
uvicorn
python-dotenv
google-genai
sqlalchemy
pgvector
psycopg[binary]
pypdf
python-docx
beautifulsoup4
markdown
duckduckgo-search
ddgs
exa_py
tavily-python
psutil
pyjwt
bcrypt
pytest
pytest-asyncio
pytest-cov
httpx
```

#### 4. Setup Database

```bash
# Start PostgreSQL with pgvector
docker run -d \
    --name cirkelline-postgres \
    -e POSTGRES_USER=cirkelline \
    -e POSTGRES_PASSWORD=cirkelline123 \
    -e POSTGRES_DB=cirkelline \
    -p 5532:5432 \
    pgvector/pgvector:pg17

# Wait 5 seconds for container to start
sleep 5

# Enable vector extension
docker exec cirkelline-postgres \
    psql -U cirkelline -d cirkelline \
    -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify
docker exec cirkelline-postgres \
    psql -U cirkelline -d cirkelline \
    -c "\dx vector"
# Should show: vector | 0.7.0 or 0.8.0
```

#### 5. Create .env File

```bash
cat > .env << 'EOF'
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline
OPENAI_API_KEY=sk-placeholder-for-knowledge-base
EXA_API_KEY=your_exa_api_key
TAVILY_API_KEY=your_tavily_api_key
JWT_SECRET_KEY=generate_64_char_hex_here
AGNO_MONITOR=true
AGNO_DEBUG=false
EOF
```

**Generate JWT Secret:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

#### 6. Initialize Database Schema

**AGNO creates tables automatically on first run**, but you need to create the users table manually:

```bash
docker exec -i cirkelline-postgres psql -U cirkelline -d cirkelline << 'EOF'
-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create admin_profiles table
CREATE TABLE IF NOT EXISTS admin_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    personal_context TEXT,
    preferences TEXT,
    custom_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create ai schema for AGNO tables
CREATE SCHEMA IF NOT EXISTS ai;
EOF
```

### Frontend Setup

#### 1. Navigate to Frontend Directory

```bash
cd ~/Desktop/cirkelline/cirkelline-ui
```

#### 2. Install Dependencies

```bash
npm install
```

#### 3. Create .env.local

```bash
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:7777
EOF
```

---

## Running the Project

### Start Backend

```bash
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:7777 (Press CTRL+C to quit)
```

**Health Check:**
```bash
curl http://localhost:7777/config
# Should return: {"status":"healthy","service":"cirkelline-system-backend","version":"1.1.6"}
```

### Start Frontend

```bash
cd ~/Desktop/cirkelline/cirkelline-ui
npm run dev
```

**Expected Output:**
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

### Access Application

Open browser: http://localhost:3000

**Test Flow:**
1. Click "Sign Up"
2. Create account
3. Send message: "Hello!"
4. Verify response appears
5. Click "New Chat"
6. Send another message
7. Verify new session appears in sidebar

---

## Adding New Agents

### Step 1: Create Agent Definition File

**Location:** Create new file in `/home/eenvy/Desktop/cirkelline/cirkelline/agents/`

**Example:** `cirkelline/agents/your_agent.py`

```python
from agno import Agent, Model
from agno.models.gemini import Gemini

def create_your_agent(knowledge, db):
    """
    Create your new specialist agent.

    Args:
        knowledge: Knowledge base instance
        db: Database connection

    Returns:
        Agent: Configured agent instance
    """
    return Agent(
        name="Your Agent Name",
        role="Brief description of role",
        model=Gemini(id="gemini-2.5-flash"),
        tools=[
            # Add tools if needed
            # ExampleTool(),
        ],
        knowledge=knowledge,  # Include if agent needs knowledge access
        search_knowledge=True,  # Enable knowledge search
        instructions=[
            "You are a [role] specialist.",
            "",
            "CAPABILITIES:",
            "• List what this agent can do",
            "• Be specific",
            "",
            "WHEN USER ASKS FOR [task]:",
            "• Step-by-step what agent should do",
            "• Include format requirements",
            "",
            "OUTPUT FORMAT:",
            "• How to structure responses",
            "• Be clear and consistent",
        ],
        markdown=True,
        db=db,
    )
```

### Step 2: Import and Initialize in my_os.py

**Location:** `/home/eenvy/Desktop/cirkelline/my_os.py` (imports section)

```python
# Add to imports (around line 20)
from cirkelline.agents.your_agent import create_your_agent

# Add to agent initialization section (around line 100)
your_new_agent = create_your_agent(knowledge, db)
```

### Step 3: Add to Cirkelline Team

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline/orchestrator/cirkelline_team.py`

```python
def create_cirkelline_team(..., your_new_agent):  # ← Add parameter
    cirkelline = Team(
        members=[
            audio_agent,
            video_agent,
            image_agent,
            document_agent,
            research_team,
            law_team,
            your_new_agent,  # ← Add here
        ],
        # ... rest of configuration
    )
```

### Step 4: Update Cirkelline Instructions

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline/orchestrator/instructions.py`

```python
def get_cirkelline_instructions(dependencies: dict) -> list:
    """Returns Cirkelline's base instructions."""
    return [
        # ... existing instructions ...

        "WHAT YOU CAN HELP WITH",
        "• Images: Describe, analyze, extract text",
        "• Audio: Transcribe speech, identify sounds",
        "• Video: Describe and analyze content",
        "• Documents: Read, summarize, analyze PDFs",
        "• Research: Find current information on any topic",
        "• Legal: Help with legal questions and research",
        "• [Your New Feature]: [Brief description]",  # ← Add here

        # ... rest of instructions ...

        "TECHNICAL ROUTING (invisible to user)",
        "• Images → Image Specialist",
        "• Audio → Audio Specialist",
        "• Video → Video Specialist",
        "• Documents/PDFs → Document Specialist",
        "• Web research → Research Team",
        "• Legal questions → Law Team",
        "• [Your trigger] → Your New Agent",  # ← Add here
    ]
```

### Step 5: Register with AgentOS

**Location:** `/home/eenvy/Desktop/cirkelline/my_os.py` (AgentOS initialization)

```python
agent_os = AgentOS(
    id="cirkelline-v1",
    description="Cirkelline Multi-Agent System",
    agents=[
        audio_agent,
        video_agent,
        image_agent,
        document_agent,
        your_new_agent,  # ← Add here
    ],
    teams=[
        cirkelline,
        research_team,
        law_team,
    ],
    base_app=app,
    on_route_conflict="preserve_base_app",
)
```

### Step 5: Test

```bash
# Restart backend
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py

# Test in chat
# Send message that triggers your agent
```

### Example: Code Review Agent

```python
code_review_agent = Agent(
    name="Code Review Specialist",
    role="Code analysis and review expert",
    model=Gemini(id="gemini-2.5-flash"),
    instructions=[
        "You are a code review specialist.",
        "",
        "WHEN CODE IS PROVIDED:",
        "• Analyze for bugs and issues",
        "• Check best practices",
        "• Suggest improvements",
        "• Review security concerns",
        "",
        "OUTPUT FORMAT:",
        "• Start with overall assessment",
        "• List issues by severity (Critical, Major, Minor)",
        "• Provide specific line references",
        "• Include code examples for fixes",
    ],
    markdown=True,
    db=db,
)
```

### Step 6: Adding ReasoningTools (Optional)

**Purpose:** Enable agents to show their thinking process in the "Behind the Scenes" panel.

**When to use:**
- Complex analysis tasks (optimization, logic puzzles)
- Multi-step problem solving
- Tasks where showing reasoning improves transparency

**Implementation:**

```python
from agno.tools.reasoning import ReasoningTools

your_agent = Agent(
    name="Analysis Specialist",
    role="Complex problem solver",
    model=Gemini(id="gemini-2.5-flash"),
    tools=[
        ReasoningTools(add_instructions=True),  # ← Add this
        # ... other tools
    ],
    tool_choice="auto",  # ← CRITICAL: Agents decide when to use reasoning
    instructions=[
        "You are an analysis specialist.",
        "",
        "🧠 REASONING:",
        "For complex tasks that require careful analysis, use the think() tool BEFORE taking action:",
        "",
        "**When to use think():**",
        "• Logic puzzles or multi-step problems",
        "• Questions requiring deep analysis",
        "• Tasks with multiple possible approaches",
        "• Complex decision-making scenarios",
        "• Planning complicated workflows",
        "",
        "**How to use think():**",
        "```python",
        "think(",
        "    title='Understanding the problem',",
        "    thought='The user is asking about... I need to consider...',",
        "    confidence=0.9",
        ")",
        "```",
        "",
        "# ... rest of your instructions
    ],
    markdown=True,
    db=db,
)
```

**Configuration Requirements:**

1. **Add ReasoningTools to tools list:**
   ```python
   tools=[ReasoningTools(add_instructions=True)]
   ```

2. **Set tool_choice to "auto":**
   ```python
   tool_choice="auto"  # Agents decide when reasoning is helpful
   ```

3. **Include reasoning instructions:**
   - When to use think()
   - How to use think()
   - Examples of complex tasks

**How It Works:**

```
User asks complex question
    ↓
Agent evaluates: "Is reasoning needed?"
    ↓
If YES: Calls think() tool
    ↓
AGNO emits ReasoningStep event
    ↓
Backend logs: "🧠 REASONING EVENT DETECTED"
    ↓
Frontend displays in Behind the Scenes panel
    ↓
User sees step-by-step thinking
```

**Example Reasoning Session:**

```
User: "I have 100 meters of fence. What dimensions maximize area?"

Behind the Scenes:
┌─────────────────────────────────────────┐
│ Analysis Specialist: Planning response  │
│                                         │
│ This is an optimization problem.        │
│ Given: Perimeter = 100m                 │
│ Find: Dimensions that maximize area     │
│                                         │
│ For a rectangle with fixed perimeter,   │
│ the square maximizes area.              │
│ Therefore: 25m × 25m = 625m²            │
└─────────────────────────────────────────┘

Visible Response:
"To maximize area, use a square: 25m × 25m (625m²)"
```

**Testing Reasoning:**

```bash
# Test query (forces reasoning)
"Think step-by-step: What is 15% of $250?"

# Check backend logs
tail -f backend.log | grep "🧠 REASONING"

# Expected output:
# 🧠 REASONING EVENT DETECTED: ReasoningStep
#    Agent/Team: Analysis Specialist
#    Title: Calculating percentage
#    Reasoning: To calculate 15% of $250...
```

**Debugging:**

1. **Reasoning not appearing?**
   - Check backend logs for `🧠 REASONING EVENT DETECTED`
   - If YES → Frontend issue (check useAIStreamHandler.tsx:277-291)
   - If NO → Agent chose not to use reasoning (try explicit prompt)

2. **Force reasoning for testing:**
   ```
   "Think step-by-step: [your question]"
   ```

3. **Verify configuration:**
   ```python
   # Must have all three:
   tools=[ReasoningTools(add_instructions=True)]  # ✓
   tool_choice="auto"                              # ✓
   instructions=["When to use think()..."]         # ✓
   ```

**See Also:**
- [08-FEATURES.md - AI Reasoning Display](./08-FEATURES.md#ai-reasoning-display) - Full feature documentation
- [14-BEHIND-THE-SCENES-DESIGN.md](./14-BEHIND-THE-SCENES-DESIGN.md) - UI design specifications

---

## Adding API Endpoints

### Step 1: Create Endpoint File

**Location:** Create new file in `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/`

**Example:** `cirkelline/endpoints/your_feature.py`

```python
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Define Pydantic Models
class YourRequestModel(BaseModel):
    field1: str
    field2: int
    optional_field: Optional[str] = None

class YourResponseModel(BaseModel):
    success: bool
    data: dict

# Create Endpoints
@router.post("/api/your/endpoint", response_model=YourResponseModel)
async def your_endpoint(
    request: Request,
    data: YourRequestModel
):
    """
    Your endpoint description.

    Requires JWT authentication (handled by middleware).
    """
    try:
        # 1. Get user_id from middleware (request.state.user_id)
        user_id = getattr(request.state, 'user_id', 'anonymous')

        if user_id == 'anonymous':
            raise HTTPException(status_code=401, detail="Authentication required")

        # 2. Your logic here
        result = process_data(data, user_id)

        # 3. Return response
        return YourResponseModel(
            success=True,
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in your_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 2: Register Router in my_os.py

**Location:** `/home/eenvy/Desktop/cirkelline/my_os.py` (router registration section)

```python
# Add to imports (around line 40)
from cirkelline.endpoints.your_feature import router as your_feature_router

# Register router (around line 950)
app.include_router(your_feature_router)
```

### Step 3: Test Endpoint

```bash
# Test with curl
curl -X POST http://localhost:7777/api/your/endpoint \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{"field1":"value","field2":123}'
```

### Example: Get User Stats

**File:** `cirkelline/endpoints/user_stats.py`

```python
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/user/stats")
async def get_user_stats(request: Request):
    """Get user statistics"""
    try:
        # Extract user_id from middleware
        user_id = getattr(request.state, 'user_id', 'anonymous')

        if user_id == 'anonymous':
            raise HTTPException(status_code=401, detail="Authentication required")

        # Query database
        from cirkelline.shared.database import db
        db_url = db.db_url
        engine = create_engine(db_url)

        with Session(engine) as session:
            # Count sessions
            session_count = session.execute(
                text("SELECT COUNT(*) FROM ai.agno_sessions WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).scalar()

            # Count documents
            doc_count = session.execute(
                text("SELECT COUNT(*) FROM ai.agno_knowledge WHERE metadata->>'user_id' = :user_id"),
                {"user_id": user_id}
            ).scalar()

        return {
            "sessions": session_count,
            "documents": doc_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_user_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Adding Frontend Components

### Step 1: Create Component File

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/components/YourComponent.tsx`

```typescript
'use client'

import React from 'react'

interface YourComponentProps {
  prop1: string
  prop2?: number
  onAction?: () => void
}

export default function YourComponent({
  prop1,
  prop2,
  onAction
}: YourComponentProps) {
  return (
    <div className="your-component">
      <h2>{prop1}</h2>
      {prop2 && <p>Value: {prop2}</p>}
      {onAction && (
        <button onClick={onAction}>
          Click Me
        </button>
      )}
    </div>
  )
}
```

### Step 2: Add Styling (TailwindCSS)

```typescript
export default function YourComponent({ prop1 }: YourComponentProps) {
  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">
        {prop1}
      </h2>
      <button className="mt-4 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded">
        Click Me
      </button>
    </div>
  )
}
```

### Step 3: Use in Page

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/app/page.tsx`

```typescript
import YourComponent from '@/components/YourComponent'

export default function Page() {
  return (
    <div>
      <YourComponent
        prop1="Hello"
        prop2={42}
        onAction={() => console.log('Clicked!')}
      />
    </div>
  )
}
```

### Step 4: Add to Zustand Store (if needed)

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/store.ts`

```typescript
interface Store {
  // ... existing state ...

  yourNewState: string
  setYourNewState: (value: string) => void
}

export const useStore = create<Store>()(
  persist(
    (set) => ({
      // ... existing state ...

      yourNewState: '',
      setYourNewState: (value) => set({ yourNewState: value }),
    }),
    // ... persistence config ...
  )
)
```

---

## Testing Procedures

### Manual Testing

#### 1. Authentication Flow

```bash
# Test signup
curl -X POST http://localhost:7777/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.com",
    "password": "testpass123",
    "display_name": "Test User"
  }'

# Test login
curl -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.com",
    "password": "testpass123"
  }'

# Save token from response
TOKEN="eyJhbGciOiJIUzI1NiIs..."

# Test authenticated endpoint
curl http://localhost:7777/teams/cirkelline/sessions \
  -H "Authorization: Bearer $TOKEN"
```

#### 2. Message Flow

```bash
# Send message
curl -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Hello!" \
  -F "stream=false" \
  -F "session_id="

# Response should include session_id
```

#### 3. File Upload

```bash
# Upload file
curl -X POST http://localhost:7777/api/knowledge/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf"

# Should return success
```

### Automated Testing

#### Backend Tests

**Location:** `/home/eenvy/Desktop/cirkelline/test_auth.py`

```python
import pytest
from fastapi.testclient import TestClient
from my_os import app

client = TestClient(app)

def test_signup():
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "test@example.com",
            "password": "password123",
            "display_name": "Test User"
        }
    )
    assert response.status_code == 200
    assert "token" in response.json()

def test_login():
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "token" in response.json()

def test_protected_endpoint():
    # Login first
    login_response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    token = login_response.json()["token"]

    # Access protected endpoint
    response = client.get(
        "/teams/cirkelline/sessions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

**Run Tests:**
```bash
cd ~/Desktop/cirkelline
source .venv/bin/activate
pytest test_auth.py -v
```

#### Frontend Tests

**Create test file:**
```typescript
// cirkelline-ui/__tests__/AuthContext.test.tsx
import { render, screen } from '@testing-library/react'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'

describe('AuthContext', () => {
  it('initializes with anonymous user', () => {
    const TestComponent = () => {
      const { user } = useAuth()
      return <div>{user?.isAnonymous ? 'Anonymous' : 'Authenticated'}</div>
    }

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    expect(screen.getByText('Anonymous')).toBeInTheDocument()
  })
})
```

**Run Tests:**
```bash
cd ~/Desktop/cirkelline/cirkelline-ui
npm test
```

---

## Git Workflow

### Branching Strategy

```bash
main            # Production-ready code
  └── develop   # Development branch (optional)
      └── feature/your-feature  # Feature branches
```

### Making Changes

#### 1. Create Feature Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/add-code-review-agent
```

#### 2. Make Changes

```bash
# Edit files
# Test changes
```

#### 3. Commit Changes

```bash
git add .
git commit -m "Add code review agent with syntax highlighting"
```

**Commit Message Format:**
```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```bash
git commit -m "feat: add code review agent"
git commit -m "fix: session sidebar not updating"
git commit -m "docs: update API reference"
```

#### 4. Push Changes

```bash
git push origin feature/add-code-review-agent
```

#### 5. Create Pull Request

```bash
# Using GitHub CLI
gh pr create --title "Add code review agent" --body "Adds new agent for code review"

# Or via GitHub web interface
```

### Syncing with Main

```bash
# Update your branch with latest main
git checkout main
git pull origin main
git checkout feature/your-feature
git merge main

# Resolve conflicts if any
git add .
git commit -m "Merge main into feature"
git push
```

---

## Quick Reference

### Common Commands

```bash
# Backend
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py

# Frontend
cd ~/Desktop/cirkelline/cirkelline-ui
npm run dev

# Database
docker start cirkelline-postgres
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline

# Tests
pytest test_auth.py -v
npm test

# Git
git status
git add .
git commit -m "message"
git push
```

### File Locations

```bash
# Backend
my_os.py                        # Main backend
.env                            # Environment variables
requirements.txt                # Python dependencies

# Frontend
cirkelline-ui/src/app/page.tsx  # Main page
cirkelline-ui/src/store.ts      # State management
cirkelline-ui/src/contexts/     # React contexts
cirkelline-ui/src/hooks/        # Custom hooks

# Database
# Docker container: cirkelline-postgres
# Connection: localhost:5532
```

### Environment Variables

```bash
# Backend (.env)
GOOGLE_API_KEY=
DATABASE_URL=
JWT_SECRET_KEY=
AGNO_MONITOR=true

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:7777
```

---

**See Also:**
- [01-ARCHITECTURE.md](./01-ARCHITECTURE.md) - System architecture
- [05-BACKEND-REFERENCE.md](./05-BACKEND-REFERENCE.md) - Backend reference
- [06-FRONTEND-REFERENCE.md](./06-FRONTEND-REFERENCE.md) - Frontend reference
- [02-TROUBLESHOOTING.md](./02-TROUBLESHOOTING.md) - Common issues
