"""
Semantic Search
===============
Vector-based knowledge retrieval and similarity matching.

Responsibilities:
- Index documents for semantic search
- Find similar content using embeddings
- Support hybrid search (semantic + keyword)
- Cache embeddings for performance
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib

from cirkelline.headquarters.knowledge_graph import (
    KnowledgeGraph,
    GraphNode,
    NodeType,
    get_knowledge_graph,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class SearchMode(Enum):
    """Search modes available."""
    SEMANTIC = "semantic"  # Vector similarity
    KEYWORD = "keyword"  # Traditional text match
    HYBRID = "hybrid"  # Combination of both


@dataclass
class SearchResult:
    """A single search result."""
    doc_id: str
    content: str
    score: float  # Similarity score (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)
    source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
            "highlights": self.highlights,
            "source": self.source,
        }


@dataclass
class Document:
    """A document for indexing."""
    doc_id: str
    content: str
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "title": self.title,
            "metadata": self.metadata,
            "has_embedding": self.embedding is not None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# EMBEDDING PROVIDER
# ═══════════════════════════════════════════════════════════════════════════════

class EmbeddingProvider:
    """Base class for embedding providers."""

    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        raise NotImplementedError

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed(t) for t in texts]


class SimpleEmbeddingProvider(EmbeddingProvider):
    """
    Simple embedding provider using character-level features.

    Note: This is a placeholder. In production, use a real
    embedding model like Sentence Transformers or OpenAI.
    """

    def __init__(self, dimensions: int = 128):
        self.dimensions = dimensions

    def embed(self, text: str) -> List[float]:
        """Generate a simple feature-based embedding."""
        if not text:
            return [0.0] * self.dimensions

        # Character frequency as features
        text_lower = text.lower()
        features = []

        # Character frequencies (a-z)
        for char in 'abcdefghijklmnopqrstuvwxyz':
            freq = text_lower.count(char) / max(len(text), 1)
            features.append(freq)

        # Word-level features
        words = text.split()
        features.append(len(words) / 100)  # Word count normalized
        features.append(sum(len(w) for w in words) / max(len(words), 1) / 10)  # Avg word length

        # Pad or truncate to dimensions
        while len(features) < self.dimensions:
            features.append(0.0)
        features = features[:self.dimensions]

        # Normalize
        magnitude = sum(f * f for f in features) ** 0.5
        if magnitude > 0:
            features = [f / magnitude for f in features]

        return features


# ═══════════════════════════════════════════════════════════════════════════════
# SIMILARITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0

    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = sum(x * x for x in a) ** 0.5
    magnitude_b = sum(x * x for x in b) ** 0.5

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def jaccard_similarity(a: str, b: str) -> float:
    """Calculate Jaccard similarity between two strings."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())

    if not words_a and not words_b:
        return 0.0

    intersection = len(words_a & words_b)
    union = len(words_a | words_b)

    return intersection / union if union > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# SEMANTIC SEARCH ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class SemanticSearch:
    """
    Vector-based semantic search engine.

    Indexes documents with embeddings and provides similarity
    search across the knowledge base.
    """

    def __init__(self, embedding_provider: Optional[EmbeddingProvider] = None):
        self._graph: Optional[KnowledgeGraph] = None
        self._embedding_provider = embedding_provider or SimpleEmbeddingProvider()

        # Document store
        self._documents: Dict[str, Document] = {}

        # Embedding cache
        self._embedding_cache: Dict[str, List[float]] = {}

    async def initialize(self) -> bool:
        """Initialize connections."""
        try:
            self._graph = get_knowledge_graph()
            logger.info("SemanticSearch initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SemanticSearch: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # DOCUMENT INDEXING
    # ═══════════════════════════════════════════════════════════════════════════

    def index_document(
        self,
        content: str,
        doc_id: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """
        Index a document for semantic search.

        Args:
            content: Document content
            doc_id: Optional document ID (generated if not provided)
            title: Optional document title
            metadata: Optional metadata

        Returns:
            Indexed Document
        """
        # Generate ID if not provided
        if not doc_id:
            content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
            doc_id = f"doc-{content_hash}"

        # Generate embedding
        embedding = self._get_embedding(content)

        # Create document
        doc = Document(
            doc_id=doc_id,
            content=content,
            title=title,
            metadata=metadata or {},
            embedding=embedding,
        )

        # Store
        self._documents[doc_id] = doc

        # Also add to knowledge graph
        if self._graph:
            self._graph.add_node(GraphNode(
                node_id=doc_id,
                node_type=NodeType.DOCUMENT,
                name=title or doc_id,
                properties={
                    "content_preview": content[:200],
                    **doc.metadata,
                },
            ))

        logger.debug(f"Indexed document {doc_id}")
        return doc

    def index_batch(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[Document]:
        """Index multiple documents."""
        results = []
        for doc_data in documents:
            doc = self.index_document(
                content=doc_data.get("content", ""),
                doc_id=doc_data.get("doc_id"),
                title=doc_data.get("title"),
                metadata=doc_data.get("metadata"),
            )
            results.append(doc)
        return results

    def update_document(
        self,
        doc_id: str,
        content: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Document]:
        """Update an existing document."""
        if doc_id not in self._documents:
            return None

        doc = self._documents[doc_id]

        if content is not None:
            doc.content = content
            doc.embedding = self._get_embedding(content)
            # Clear cache
            cache_key = self._cache_key(content)
            self._embedding_cache.pop(cache_key, None)

        if title is not None:
            doc.title = title

        if metadata is not None:
            doc.metadata.update(metadata)

        doc.updated_at = datetime.utcnow().isoformat()

        return doc

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index."""
        if doc_id in self._documents:
            del self._documents[doc_id]
            return True
        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # SEARCH
    # ═══════════════════════════════════════════════════════════════════════════

    def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        top_k: int = 10,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search for documents matching a query.

        Args:
            query: Search query
            mode: Search mode (semantic, keyword, hybrid)
            top_k: Number of results to return
            min_score: Minimum score threshold
            filters: Optional metadata filters

        Returns:
            List of SearchResults sorted by relevance
        """
        if not query or not self._documents:
            return []

        results = []

        # Get query embedding for semantic search
        query_embedding = self._get_embedding(query) if mode != SearchMode.KEYWORD else None

        for doc_id, doc in self._documents.items():
            # Apply filters
            if filters and not self._matches_filters(doc, filters):
                continue

            # Calculate score based on mode
            if mode == SearchMode.SEMANTIC:
                score = self._semantic_score(query_embedding, doc)
            elif mode == SearchMode.KEYWORD:
                score = self._keyword_score(query, doc)
            else:  # HYBRID
                semantic = self._semantic_score(query_embedding, doc)
                keyword = self._keyword_score(query, doc)
                # Weighted combination
                score = 0.7 * semantic + 0.3 * keyword

            if score >= min_score:
                # Extract highlights
                highlights = self._extract_highlights(query, doc.content)

                results.append(SearchResult(
                    doc_id=doc_id,
                    content=doc.content[:500],  # Preview
                    score=score,
                    metadata=doc.metadata,
                    highlights=highlights,
                    source=doc.title,
                ))

        # Sort by score and limit
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def find_similar(
        self,
        doc_id: str,
        top_k: int = 5,
        exclude_self: bool = True,
    ) -> List[SearchResult]:
        """Find documents similar to a given document."""
        if doc_id not in self._documents:
            return []

        source_doc = self._documents[doc_id]
        if not source_doc.embedding:
            return []

        results = []

        for other_id, other_doc in self._documents.items():
            if exclude_self and other_id == doc_id:
                continue

            if not other_doc.embedding:
                continue

            score = cosine_similarity(source_doc.embedding, other_doc.embedding)
            results.append(SearchResult(
                doc_id=other_id,
                content=other_doc.content[:500],
                score=score,
                metadata=other_doc.metadata,
                source=other_doc.title,
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def _semantic_score(
        self,
        query_embedding: List[float],
        doc: Document,
    ) -> float:
        """Calculate semantic similarity score."""
        if not query_embedding or not doc.embedding:
            return 0.0
        return cosine_similarity(query_embedding, doc.embedding)

    def _keyword_score(
        self,
        query: str,
        doc: Document,
    ) -> float:
        """Calculate keyword-based score."""
        return jaccard_similarity(query, doc.content)

    def _matches_filters(
        self,
        doc: Document,
        filters: Dict[str, Any],
    ) -> bool:
        """Check if document matches filters."""
        for key, value in filters.items():
            doc_value = doc.metadata.get(key)
            if doc_value != value:
                return False
        return True

    def _extract_highlights(
        self,
        query: str,
        content: str,
        max_highlights: int = 3,
    ) -> List[str]:
        """Extract relevant snippets from content."""
        query_words = set(query.lower().split())
        sentences = content.replace('\n', '. ').split('. ')

        # Score sentences by query word overlap
        scored = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            words = set(sentence.lower().split())
            overlap = len(words & query_words)
            if overlap > 0:
                scored.append((overlap, sentence[:200]))

        scored.sort(reverse=True)
        return [s for _, s in scored[:max_highlights]]

    # ═══════════════════════════════════════════════════════════════════════════
    # EMBEDDING MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding with caching."""
        cache_key = self._cache_key(text)

        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        embedding = self._embedding_provider.embed(text)
        self._embedding_cache[cache_key] = embedding

        return embedding

    def _cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()

    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self._embedding_cache.clear()

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        docs_with_embeddings = sum(
            1 for d in self._documents.values() if d.embedding
        )

        return {
            "total_documents": len(self._documents),
            "documents_with_embeddings": docs_with_embeddings,
            "embedding_cache_size": len(self._embedding_cache),
            "embedding_dimensions": self._embedding_provider.dimensions if hasattr(self._embedding_provider, 'dimensions') else "unknown",
        }

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID."""
        return self._documents.get(doc_id)

    def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Document]:
        """List all documents."""
        docs = list(self._documents.values())
        return docs[offset:offset + limit]


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_search_instance: Optional[SemanticSearch] = None


def get_semantic_search() -> SemanticSearch:
    """Get the singleton SemanticSearch instance."""
    global _search_instance

    if _search_instance is None:
        _search_instance = SemanticSearch()

    return _search_instance


async def init_semantic_search() -> SemanticSearch:
    """Initialize and return the semantic search engine."""
    search = get_semantic_search()
    await search.initialize()
    return search
