# KV1NTOS v2.11.0 - Knowledge Graph

**Version:** 2.11.0
**Date:** 2025-12-19
**Location:** `~/.claude-agent/`
**Components:** 47 total (~48,000 lines)

---

## OVERVIEW

v2.11.0 introduces the **Knowledge Graph** - semantic understanding of the codebase through vector embeddings and relationship mapping.

### Core Principle

> **SEMANTIC CODE UNDERSTANDING** - The Knowledge Graph enables intelligent navigation and context-aware operations by understanding code at a semantic level.

### New Component

| Component | Lines | Purpose |
|-----------|-------|---------|
| `knowledge_graph.py` | ~970 | 768-dim embeddings, semantic search, relationships |

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE GRAPH v2.11.0                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Local     │    │  Knowledge  │    │   Graph     │         │
│  │  Embedder   │    │   Graph     │    │  Database   │         │
│  │ (768-dim)   │    │   (Core)    │    │  (SQLite)   │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                            ▼                                    │
│              ┌─────────────────────────┐                       │
│              │    Semantic Search      │                       │
│              │  - find similar code    │                       │
│              │  - get dependencies     │                       │
│              │  - class hierarchy      │                       │
│              └─────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## NODE TYPES

```python
class NodeType(Enum):
    FILE = "file"           # Source file
    CLASS = "class"         # Class definition
    FUNCTION = "function"   # Function definition
    METHOD = "method"       # Class method
    VARIABLE = "variable"   # Global variable
    IMPORT = "import"       # Import statement
    CONCEPT = "concept"     # Abstract concept
    PATTERN = "pattern"     # Code pattern
    MODULE = "module"       # Python module
```

---

## EDGE TYPES

```python
class EdgeType(Enum):
    CONTAINS = "contains"         # File contains class
    CALLS = "calls"               # Function calls function
    IMPORTS = "imports"           # File imports module
    INHERITS = "inherits"         # Class inherits class
    IMPLEMENTS = "implements"     # Class implements interface
    USES = "uses"                 # Function uses variable
    RELATED = "related"           # Semantically related
    SIMILAR = "similar"           # Similar code pattern
    DEPENDS_ON = "depends_on"     # Dependency relationship
```

---

## EMBEDDING SYSTEM

### Local Embedder (768-dim)

```python
class LocalEmbedder:
    """TF-IDF-like embedding generation."""

    def embed(text: str) -> List[float]:
        """Generate 768-dimensional embedding from text."""
        # Tokenize
        tokens = self._tokenize(text)

        # Hash each token to a dimension
        for token in tokens:
            dim = self._hash_token(token) % 768
            embedding[dim] += tf_idf_weight

        # Normalize
        return normalize(embedding)
```

### Embedding Providers

```python
class EmbeddingProvider(Enum):
    LOCAL = "local"                   # Built-in TF-IDF (default)
    OLLAMA = "ollama"                 # Ollama embeddings
    SENTENCE_TRANSFORMER = "sentence_transformer"
```

---

## USAGE

### Semantic Search

```python
from knowledge_graph import get_knowledge_graph

kg = get_knowledge_graph()

# Search codebase semantically
results = kg.semantic_search(
    query="authentication handling",
    top_k=10,
    node_types=[NodeType.FUNCTION, NodeType.CLASS],
    threshold=0.7
)

for result in results:
    print(f"{result.node.name}: {result.similarity:.2f}")
```

### Find Similar Code

```python
# Find similar patterns
similar = kg.find_similar_code(
    code="def validate_user(token): ...",
    top_k=5,
    exclude_file="auth.py"
)

for match in similar:
    print(f"{match.node.file_path}: {match.similarity:.2f}")
```

### Add Files to Graph

```python
# Index a file
kg.add_file("/path/to/module.py", content=source_code)

# Extract functions/classes automatically
kg.add_function("validate", file_path, content, 10, 25)
kg.add_class("UserManager", file_path, content, 30, 100)
```

### Analyze Dependencies

```python
# Get file dependencies
deps = kg.get_file_dependencies("/path/to/main.py")
for dep in deps:
    print(f"Imports: {dep}")

# Get function call graph
calls = kg.get_function_calls("process_request", "/path/to/api.py")
print(f"Calls: {calls}")

# Get class hierarchy
hierarchy = kg.get_class_hierarchy("AdminUser", "/path/to/models.py")
print(f"Parents: {hierarchy['parents']}")
```

---

## DAEMON INTEGRATION

### New Properties

```python
kv1nt.knowledge_graph   # KnowledgeGraph instance
```

### New Methods

```python
# Semantic search
kv1nt.semantic_search(query, top_k, node_types, threshold)

# Find similar code
kv1nt.find_similar_code(code, top_k, exclude_file)

# Add files
kv1nt.add_code_file(file_path, content)

# Analysis
kv1nt.get_file_dependencies(file_path)
kv1nt.get_function_calls(function_name)
kv1nt.get_class_hierarchy(class_name)

# Status
kv1nt.knowledge_graph_status()
kv1nt.knowledge_graph_status_formatted()
```

---

## DATABASE SCHEMA

### SQLite: `knowledge_graph.db`

**nodes table:**
```sql
CREATE TABLE nodes (
    node_id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    name TEXT NOT NULL,
    content TEXT,
    file_path TEXT,
    line_start INTEGER,
    line_end INTEGER,
    embedding BLOB,
    metadata TEXT,
    created_at TIMESTAMP
);
```

**edges table:**
```sql
CREATE TABLE edges (
    edge_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    metadata TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES nodes(node_id),
    FOREIGN KEY (target_id) REFERENCES nodes(node_id)
);
```

**concepts table:**
```sql
CREATE TABLE concepts (
    concept_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    keywords TEXT,
    related_nodes TEXT,
    embedding BLOB,
    created_at TIMESTAMP
);
```

---

## DATACLASSES

### GraphNode

```python
@dataclass
class GraphNode:
    node_id: str
    node_type: NodeType
    name: str
    content: str
    file_path: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
```

### GraphEdge

```python
@dataclass
class GraphEdge:
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
```

### SearchResult

```python
@dataclass
class SearchResult:
    node: GraphNode
    similarity: float
    context: str = ""
```

---

## COMPONENT STATISTICS

### v2.11.0 Summary

| Metric | Value |
|--------|-------|
| Total Components | 47 |
| Total Lines | ~48,000 |
| New Components | 1 |
| New Methods | 8 |
| New Enums | 3 |
| New Dataclasses | 5 |

### Progression

```
v2.10.0  →  v2.11.0
  46         47
 components  components
```

---

## NEXT STEPS (v2.12.0)

With Knowledge Graph in place, the next iteration adds:

1. **Prompt Composer** (`prompt_composer.py`)
   - Specialized prompt templates
   - Context injection
   - Task-specific prompting

2. **Code Synthesizer** (`code_synthesizer.py`)
   - Multi-language code generation
   - Template + LLM hybrid generation
   - Syntax validation

---

## CHANGELOG

### v2.11.0 (2025-12-19)

**Added:**
- `knowledge_graph.py` (~970 lines)
  - LocalEmbedder class (768-dim TF-IDF)
  - KnowledgeGraphDatabase class
  - KnowledgeGraph main class
  - GraphNode, GraphEdge, SearchResult dataclasses
  - NodeType enum (9 types)
  - EdgeType enum (9 types)
  - EmbeddingProvider enum (3 providers)
- 8 new daemon methods
- `knowledge_graph.db` SQLite database

**Updated:**
- kv1nt_daemon.py to v2.11.0
- VERSION file to 2.11.0
- Component count: 46 → 47

---

*Documentation Version: 1.0*
*Created: 2025-12-19*
*Author: Claude Opus 4.5*
