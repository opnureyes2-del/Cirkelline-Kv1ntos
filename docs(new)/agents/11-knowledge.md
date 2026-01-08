# AGNO Knowledge Documentation

> **Source:** https://docs.agno.com/basics/agents/usage/agent-with-knowledge
> **Last Updated:** 2025-11-29

---

## What Is Knowledge?

Knowledge enables agents to access and search through documents, creating Retrieval Augmented Generation (RAG) capabilities. Documents are chunked, embedded, and stored in vector databases for semantic search.

---

## V2 Changes (IMPORTANT)

| Old (V1) | New (V2) |
|----------|----------|
| `AgentKnowledge` | `Knowledge` |
| `add_references` | `add_knowledge_to_context` |
| `retriever` | `knowledge_retriever` |
| Import from various | Import from `agno.knowledge` |

---

## Knowledge Setup

### Basic Configuration

```python
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import PgVector

knowledge = Knowledge(
    vector_db=PgVector(
        table_name="my_knowledge",
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

# Add content
knowledge.add_content(url="https://example.com/document.pdf")
# OR async (recommended for production)
await knowledge.add_content_async(path="data/documents/")
```

### Vector Database Options

| Database | Use Case |
|----------|----------|
| `PgVector` | PostgreSQL with pgvector extension |
| `LanceDb` | Lightweight, file-based |
| `Qdrant` | High-performance vector search |
| `Pinecone` | Managed cloud service |

### Search Types

```python
from agno.vectordb.lancedb import LanceDb, SearchType

vector_db = LanceDb(
    uri="tmp/lancedb",
    table_name="knowledge",
    search_type=SearchType.hybrid,  # Combines vector + keyword
    embedder=OpenAIEmbedder(),
)
```

| Search Type | Description |
|-------------|-------------|
| `vector` | Pure semantic similarity |
| `keyword` | Traditional keyword matching |
| `hybrid` | Combines both (recommended) |

---

## Agent Integration

### Agentic RAG (Agent Searches)

```python
agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,  # Agent gets search tool
)
```

Agent decides when to search and receives a `search_knowledge_base()` tool.

### Traditional RAG (Auto-Include)

```python
agent = Agent(
    knowledge=knowledge,
    add_knowledge_to_context=True,  # Auto-add relevant docs
)
```

Relevant documents automatically added to context for every query.

### Combined Approach

```python
agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,           # Agent can search
    add_knowledge_to_context=True,   # Also auto-include
)
```

---

## Knowledge Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `knowledge` | None | Knowledge instance |
| `search_knowledge` | True (if knowledge set) | Enable search tool |
| `add_knowledge_to_context` | False | Auto-add to context |
| `knowledge_retriever` | None | Custom retrieval function |
| `max_results` | 5 | Number of results to return |

---

## Content Types

| Source | Description |
|--------|-------------|
| `path` | Local files or directories |
| `url` | Direct links to files |
| `text_content` | Raw text content |
| `topic` | Search Arxiv/Wikipedia |
| Remote | S3, Google Cloud Storage |

### Supported Formats
- PDF, DOCX, CSV, JSON, Text
- Websites (URL content)
- Custom readers for other formats

---

## Custom Readers

```python
from agno.knowledge.reader.pdf_reader import PDFReader

reader = PDFReader(
    chunk_size=1000,  # Characters per chunk
    # chunking_strategy=...
)

knowledge.add_content(
    path="data/documents/",
    reader=reader,
)
```

### Reader Parameters

| Parameter | Description |
|-----------|-------------|
| `chunk_size` | Size of each chunk (default varies) |
| `chunking_strategy` | How to split content |
| `overlap` | Overlap between chunks |

---

## Custom Retriever

For complete control over search:

```python
from typing import Optional

def my_retriever(
    query: str,
    agent: Optional[Agent] = None,
    num_documents: int = 5,
    **kwargs
) -> Optional[list[dict]]:
    """Custom retrieval logic."""
    # Your custom search logic here
    return results

agent = Agent(
    knowledge_retriever=my_retriever,
    search_knowledge=True,
)
```

---

## Embedders

| Embedder | Model |
|----------|-------|
| `OpenAIEmbedder` | text-embedding-3-small/large |
| `AzureOpenAIEmbedder` | Azure embeddings |
| `GeminiEmbedder` | Google embeddings |
| Custom | Implement your own |

```python
from agno.knowledge.embedder.openai import OpenAIEmbedder

embedder = OpenAIEmbedder(id="text-embedding-3-large")
```

---

## Adding Content with Metadata

```python
await knowledge.add_content_async(
    name="Employee Handbook",
    path="docs/handbook.pdf",
    metadata={"department": "HR", "year": 2024},
)
```

Metadata enables filtering during retrieval.

---

## Best Practices

### 1. Use Hybrid Search

```python
search_type=SearchType.hybrid
```

Combines semantic understanding with keyword matching for best results.

### 2. Async Loading for Production

```python
# Better performance for large knowledge bases
await knowledge.add_content_async(path="data/")
```

### 3. Appropriate Chunk Sizes

- **Smaller chunks** (500-1000): More precise retrieval
- **Larger chunks** (2000-3000): More context per result

### 4. Include Metadata

```python
metadata={"user_id": "...", "category": "..."}
```

Enables filtering and access control.

### 5. Combine with Instructions

```python
instructions=[
    "Search the knowledge base first for information",
    "Only use web search if knowledge base lacks the answer",
]
```

---

## Complete Example

```python
import asyncio
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import PgVector

# Setup knowledge base
knowledge = Knowledge(
    vector_db=PgVector(
        table_name="company_docs",
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
    max_results=5,
)

# Load documents
asyncio.run(knowledge.add_content_async(
    path="data/company_policies/",
    metadata={"type": "policy"},
))

# Create agent with knowledge
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    knowledge=knowledge,
    search_knowledge=True,
    instructions=[
        "You are a helpful assistant with access to company documents.",
        "Always search the knowledge base before answering policy questions.",
    ],
)

agent.print_response("What is our vacation policy?")
```

---

## Team Knowledge

Teams use the same pattern:

```python
from agno.team import Team

team = Team(
    knowledge=knowledge,
    search_knowledge=True,
    members=[agent1, agent2],
)
```

---

## Summary

| Feature | Parameter | Notes |
|---------|-----------|-------|
| Knowledge base | `knowledge=Knowledge(...)` | Required for RAG |
| Agent search | `search_knowledge=True` | Agent gets search tool |
| Auto-include | `add_knowledge_to_context=True` | Traditional RAG |
| Custom search | `knowledge_retriever=func` | Full control |
| Embedder | Set in vector_db | OpenAI default |
| Search type | `SearchType.hybrid` | Recommended |

**Key Insight:** Use `search_knowledge=True` for agentic RAG where the agent decides when to search, or `add_knowledge_to_context=True` for traditional RAG where relevant docs are auto-included.
