# Best Practices - cirkelline-kv1ntos

**Version:** 3.0.0
**Context:** Development, Testing, Deployment
**Last Updated:** 2026-01-01

---

## Development Best Practices

### 1. Code Organization

#### Backend (Python)
```
cirkelline/
├── agents/              # Agent definitions
│   ├── specialists.py   # Audio, Video, Image, Document agents
│   ├── research_team.py # Research team
│   └── law_team.py      # Law team
├── orchestrator/        # Orchestration logic
│   └── cirkelline_team.py # Main orchestrator
├── tools/               # Custom tools
│   ├── media.py         # Media processing
│   └── search.py        # Search integration
├── routers/             # API endpoints
│   ├── auth.py          # Authentication
│   ├── chat.py          # Chat endpoints
│   ├── knowledge.py      # Knowledge management
│   └── memories.py      # Memory management
├── middleware/          # Middleware
│   └── middleware.py    # JWT, user isolation
├── database/            # Database layer
│   └── db.py            # Database connections
└── models/              # Pydantic models
    └── schemas.py       # Request/response schemas
```

#### Frontend (Next.js)
```
cirkelline-ui/src/
├── app/                 # Pages
│   ├── page.tsx        # Login
│   ├── chat/page.tsx   # Chat page
│   └── memories/page.tsx # Memories
├── components/          # Reusable components
│   ├── ChatInput.tsx    # Message input
│   ├── ChatMessages.tsx # Message display
│   └── Sidebar/         # Navigation
├── hooks/               # Custom hooks
│   ├── useAIStreamHandler.tsx  # SSE streaming
│   └── useSessionLoader.tsx    # Session loading
├── contexts/            # React contexts
│   └── AuthContext.tsx  # Auth + user state
├── store.ts             # Zustand state
├── types/               # TypeScript types
└── utils/               # Utility functions
```

### 2. Naming Conventions

#### Python
```python
# Classes: PascalCase
class AudioAgent:
    pass

class DocumentProcessor:
    pass

# Functions/Methods: snake_case
def process_document():
    pass

def extract_embeddings():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 10_000_000
EMBEDDING_DIMENSION = 768

# Private (single underscore prefix)
def _internal_helper():
    pass

# Global module level
from cirkelline.agents.specialists import audio_agent
```

#### TypeScript/JavaScript
```typescript
// Types/Interfaces: PascalCase
interface UserSession {
  id: string;
  userId: string;
}

type Message = {
  content: string;
  timestamp: Date;
};

// Variables/Functions: camelCase
const userEmail = "test@test.com";

function handleChatMessage() {
  // ...
}

// Components: PascalCase
export function ChatInput() {
  // ...
}

// Constants: UPPER_SNAKE_CASE
const API_BASE_URL = "http://localhost:7777";
const MAX_UPLOAD_SIZE = 10_000_000;
```

#### Database
```
Tables: lowercase_snake_case
  ✓ agno_sessions
  ✓ agno_memories
  ✗ agnoSessions

Columns: lowercase_snake_case
  ✓ user_id, created_at
  ✗ userId, createdAt

Indexes: idx_<table>_<column>
  ✓ idx_agno_sessions_user_id
  ✓ idx_agno_memories_created_at
```

### 3. Code Style

#### Python (Black formatter)
```python
# Line length: 100 characters
# Use black for automatic formatting
black cirkelline/

# Type hints (recommended)
def process_document(
    file_path: str,
    user_id: str,
) -> dict[str, Any]:
    pass

# Docstrings
def search_knowledge(query: str) -> list[dict]:
    """
    Search knowledge base using semantic and keyword search.

    Args:
        query: User's search query

    Returns:
        List of matching documents with scores
    """
    pass
```

#### TypeScript (Prettier)
```typescript
// Format with prettier
pnpm run format

// Type hints (required)
const handleMessage = async (
  message: string,
  sessionId: string | null
): Promise<void> => {
  // implementation
};

// Exports
export type UserSession = {
  id: string;
  userId: string;
};

export const DEFAULT_TIMEOUT = 5000;
```

### 4. Version Control Practices

#### Commit Messages
```
Format: <type>: <subject>

Types:
  feat:    New feature
  fix:     Bug fix
  refactor: Code refactoring
  test:    Tests only
  docs:    Documentation
  perf:    Performance improvement

Examples:
  feat: Add Agent Factory dynamic creation
  fix: Resolve JWT token expiration issue
  refactor: Extract vector search logic
  docs: Update database schema documentation
```

#### Branch Naming
```
Format: <type>/<description>

Types: feature, bugfix, hotfix, refactor, docs

Examples:
  feature/agent-factory
  bugfix/jwt-token-issue
  refactor/vector-search
```

---

## Testing Best Practices

### 1. Unit Tests

```python
# Location: tests/test_<module>.py
import pytest
from cirkelline.agents.specialists import audio_agent

def test_audio_agent_initialization():
    """Test audio agent initializes correctly."""
    assert audio_agent is not None
    assert audio_agent.name == "Audio Specialist"

def test_document_processing():
    """Test document processing with sample file."""
    result = process_document("test.pdf", "user-123")
    assert result["success"] is True
    assert len(result["chunks"]) > 0
```

### 2. Integration Tests

```python
# Test API endpoints
@pytest.mark.asyncio
async def test_chat_endpoint():
    """Test chat endpoint with real database."""
    response = await client.post(
        "/teams/cirkelline/runs",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Hello", "session_id": None}
    )
    assert response.status_code == 200
```

### 3. Test Coverage

```bash
# Run tests with coverage
pytest --cov=cirkelline tests/

# Target: >80% coverage for critical code
# Exclude: migrations, type stubs, test files

# Critical paths (100% coverage):
- User isolation filters
- Authentication middleware
- Knowledge access control
```

### 4. Frontend Testing

```typescript
// Use Vitest + React Testing Library
import { render, screen } from '@testing-library/react';
import { ChatInput } from '@/components/ChatInput';

describe('ChatInput', () => {
  it('renders input field', () => {
    render(<ChatInput />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('sends message on submit', async () => {
    const { getByRole } = render(<ChatInput />);
    const input = getByRole('textbox');
    // Test logic
  });
});
```

---

## Database Best Practices

### 1. Queries

#### Always Filter by user_id
```python
# ✓ CORRECT - Filtered
sessions = db.query("""
    SELECT * FROM ai.agno_sessions
    WHERE user_id = %s
""", user_id)

# ✗ WRONG - No filter (data leak!)
sessions = db.query("SELECT * FROM ai.agno_sessions")
```

#### Use Parameterized Queries
```python
# ✓ CORRECT - Parameterized (SQL injection safe)
result = db.query(
    "SELECT * FROM users WHERE email = %s",
    email
)

# ✗ WRONG - String formatting (unsafe)
result = db.query(f"SELECT * FROM users WHERE email = '{email}'")
```

#### Index for Common Filters
```python
# ✓ CORRECT - Queries use indexed columns
SELECT * FROM ai.agno_sessions WHERE user_id = 'user-123'  # indexed

# ✗ SLOW - Non-indexed column
SELECT * FROM ai.agno_sessions WHERE name LIKE '%test%'  # not indexed
```

### 2. Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check status
alembic current
```

### 3. Performance

```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
)

# Batch inserts
db.bulk_insert_mappings(User, [user1, user2, user3])

# Use indexes
CREATE INDEX idx_fast_query ON table (column1, column2)

# Analyze query plans
EXPLAIN ANALYZE SELECT ...
```

---

## Security Best Practices

### 1. Authentication

```python
# ✓ Correct: Use JWT middleware
@app.middleware("http")
async def jwt_middleware(request, call_next):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        request.state.user_id = payload["user_id"]
    except:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    return await call_next(request)

# ✗ Wrong: No authentication
@app.get("/sensitive-endpoint")
async def endpoint():
    # Anyone can access!
    pass
```

### 2. Input Validation

```python
from pydantic import BaseModel, EmailStr

# ✓ Correct: Validated input
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/login")
async def login(request: LoginRequest):
    # Email validated, password type-checked
    pass

# ✗ Wrong: No validation
@app.post("/login")
async def login(data: dict):
    # Anyone can send anything
    pass
```

### 3. Environment Variables

```python
# ✓ Correct: Secure secrets
from dotenv import load_dotenv
load_dotenv()  # Load from .env

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# ✗ Wrong: Hardcoded secrets
DATABASE_URL = "postgresql://user:password@localhost/db"
JWT_SECRET_KEY = "my-super-secret-key"
```

### 4. CORS

```python
# ✓ Correct: Specific origins
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://cirkelline.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# ✗ Wrong: Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Security risk!
)
```

---

## API Best Practices

### 1. Endpoint Design

```python
# ✓ RESTful
POST   /api/documents           # Create
GET    /api/documents           # List
GET    /api/documents/{id}      # Get one
PUT    /api/documents/{id}      # Update
DELETE /api/documents/{id}      # Delete

# ✗ Non-RESTful
GET    /api/create-document
GET    /api/update-document
GET    /api/delete-document
```

### 2. Response Format

```python
# ✓ Consistent format
{
  "success": true,
  "data": {...},
  "error": null
}

{
  "success": false,
  "data": null,
  "error": "Document not found"
}

# ✗ Inconsistent
{
  "result": {...}  # No error field
}

{
  "error": "Not found"  # No success field
}
```

### 3. Error Handling

```python
# ✓ Specific errors
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )

@app.get("/documents/{id}")
async def get_document(id: int):
    doc = db.query(Document).get(id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return doc

# ✗ Generic errors
try:
    result = dangerous_operation()
    return result
except Exception as e:
    return {"error": "Something went wrong"}
```

---

## Performance Best Practices

### 1. Caching

```python
# Use Redis for caching
from redis import Redis

redis_client = Redis(host="localhost", port=6381)

# Cache expensive operations
def get_user_memories(user_id: str):
    cache_key = f"memories:{user_id}"

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Query database
    memories = db.query(...).filter(user_id=user_id).all()

    # Store in cache (5 minute TTL)
    redis_client.setex(cache_key, 300, json.dumps(memories))

    return memories
```

### 2. Database Queries

```python
# ✓ Efficient: Single query with joins
sessions = db.query(Session).filter(
    Session.user_id == user_id
).options(
    joinedload(Session.messages)
).all()

# ✗ Inefficient: N+1 problem
sessions = db.query(Session).filter(user_id=user_id).all()
for session in sessions:
    messages = db.query(Message).filter(...).all()  # Extra query!
```

### 3. Pagination

```python
# Always paginate large result sets
@app.get("/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 50,
):
    if limit > 100:
        limit = 100  # Cap at 100

    documents = db.query(Document).offset(skip).limit(limit).all()
    return {"documents": documents, "skip": skip, "limit": limit}
```

### 4. Lazy Loading

```python
# Load related data only when needed
from sqlalchemy.orm import selectinload

# Good: Load related data in one query
sessions = db.query(Session).options(
    selectinload(Session.messages)
).all()

# Avoid: Lazy load (triggers extra queries)
sessions = db.query(Session).all()
for session in sessions:
    messages = session.messages  # Triggers query for each session!
```

---

## Documentation Best Practices

### 1. Docstrings

```python
def search_knowledge(query: str, user_id: str) -> list[dict]:
    """
    Search user's knowledge base using hybrid search.

    Combines semantic search (vector similarity) and keyword search
    (BM25) to find relevant documents.

    Args:
        query: User's search query
        user_id: User ID for filtering

    Returns:
        List of dicts with structure:
        {
            "chunk_text": str,
            "similarity": float (0-1),
            "document_id": int,
            "page": int
        }

    Raises:
        ValueError: If query is empty
        PermissionError: If user_id not authenticated

    Example:
        >>> results = search_knowledge("agent framework", "user-123")
        >>> print(results[0]["similarity"])
        0.92
    """
    pass
```

### 2. Comments

```python
# ✓ Explain WHY, not WHAT
# User isolation is critical for privacy - always filter by user_id
# even if it seems redundant
sessions = db.query(Session).filter(user_id=user_id).all()

# ✗ Obvious comments
# Get all sessions
sessions = db.query(Session).all()

# Get session by ID
session = db.get(Session, session_id)
```

### 3. Type Hints

```python
# ✓ Complete type hints
from typing import Optional, list

def process_document(
    file_path: str,
    user_id: str,
    extract_text: bool = True,
) -> Optional[dict[str, Any]]:
    """Process a document and return metadata."""
    pass

# ✗ Missing types
def process_document(file_path, user_id, extract_text=True):
    pass
```

---

## CHANGELOG

| Date | Time | Description | Author |
|------|------|-------------|--------|
| 2026-01-01 | 23:50 | Initial BEST_PRACTICES.md created with MEDIUM detail | Kv1nt |

---

**Last Updated:** 2026-01-01
**Status:** MEDIUM Detail Level Complete
**Document Type:** INTRO Documentation
