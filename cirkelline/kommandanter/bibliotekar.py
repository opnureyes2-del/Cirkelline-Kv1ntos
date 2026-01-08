"""
Bibliotekar-Kommandant Interface
================================

FASE 6: Multi-Bibliotek Arkitektur

Bibliotekar-Kommandanten er ansvarlig for organisering,
klassifikation og soging af viden inden for en given domane.

Ansvar:
    - Organiserer viden i logiske kategorier
    - Vedligeholder taxonomier og ontologier
    - Faciliterer effektiv soging
    - Forbinder relateret viden

Hver videndomane har sin egen Bibliotekar der specialiserer
sig i domanens unikke organisations-behov.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Set
from enum import Enum
import uuid


class ContentType(Enum):
    """Typer af indhold"""
    RESEARCH_FINDING = "research_finding"
    DOCUMENT = "document"
    ANALYSIS = "analysis"
    REPORT = "report"
    NOTE = "note"
    REFERENCE = "reference"
    EXTERNAL_LINK = "external_link"


class RelevanceLevel(Enum):
    """Relevansniveau for sogeresultater"""
    EXACT_MATCH = "exact_match"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TANGENTIAL = "tangential"


@dataclass
class Content:
    """
    Indhold der skal klassificeres og indekseres.

    Attributes:
        id: Unik identifikator
        title: Titel
        body: Hovedindhold
        content_type: Type af indhold
        source: Kilde
        created_at: Oprettelsestidspunkt
        metadata: Yderligere metadata
    """
    title: str
    body: str
    content_type: ContentType
    source: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Classification:
    """
    Klassifikation af indhold.

    Attributes:
        content_id: ID pa det klassificerede indhold
        domain: Videndomane
        primary_category: Primar kategori
        secondary_categories: Sekundare kategorier
        tags: Tags
        confidence: Confidence score for klassifikationen
    """
    content_id: str
    domain: str
    primary_category: str
    secondary_categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    confidence: float = 1.0
    classified_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IndexEntry:
    """
    Index entry for indhold.

    Attributes:
        content_id: ID pa indholdet
        domain: Videndomane
        terms: Sogebare termer
        embedding_id: ID pa embedding vector (hvis relevant)
        indexed_at: Tidspunkt for indeksering
    """
    content_id: str
    domain: str
    terms: List[str]
    embedding_id: Optional[str] = None
    indexed_at: datetime = field(default_factory=datetime.utcnow)
    weight_boost: float = 1.0


@dataclass
class SearchFilters:
    """
    Filtre til soging.

    Attributes:
        categories: Filtrer pa kategorier
        tags: Filtrer pa tags
        content_types: Filtrer pa indholdstyper
        date_from: Fra dato
        date_to: Til dato
        min_relevance: Minimum relevansscore
    """
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    content_types: Optional[List[ContentType]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_relevance: float = 0.0
    sources: Optional[List[str]] = None


@dataclass
class SearchResult:
    """Enkelt sogeresultat"""
    content_id: str
    title: str
    snippet: str
    relevance: RelevanceLevel
    score: float
    category: str
    matched_terms: List[str] = field(default_factory=list)


@dataclass
class SearchResults:
    """
    Sogeresultater.

    Attributes:
        query: Den originale sogeforesporgsel
        total_count: Totalt antal resultater
        results: Liste af resultater
        facets: Facetter for filtrering
        execution_time_ms: Eksekveringstid
    """
    query: str
    total_count: int
    results: List[SearchResult]
    facets: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    page: int = 1
    page_size: int = 10


@dataclass
class RelatedContent:
    """
    Relateret indhold.

    Attributes:
        content_id: ID pa det relaterede indhold
        title: Titel
        relationship_type: Type af relation
        strength: Styrke af relationen (0.0 - 1.0)
    """
    content_id: str
    title: str
    relationship_type: str
    strength: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaxonomyNode:
    """En node i taxonomien"""
    id: str
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    children: List["TaxonomyNode"] = field(default_factory=list)
    item_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Taxonomy:
    """
    Taxonomi for en domane.

    Attributes:
        domain: Videndomane
        root_nodes: Rod-noder i taxonomien
        total_categories: Totalt antal kategorier
        max_depth: Maksimal dybde
    """
    domain: str
    root_nodes: List[TaxonomyNode]
    total_categories: int = 0
    max_depth: int = 0
    version: str = "1.0"
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def get_all_categories(self) -> List[str]:
        """Hent alle kategorinavne flat."""
        categories = []

        def collect(node: TaxonomyNode):
            categories.append(node.name)
            for child in node.children:
                collect(child)

        for root in self.root_nodes:
            collect(root)

        return categories


class BibliotekarKommandant(ABC):
    """
    Abstract base class for Bibliotekar-Kommandant.

    Hver videndomane har sin egen Bibliotekar der:
    - Organiserer viden i logiske kategorier
    - Vedligeholder taxonomier og ontologier
    - Faciliterer effektiv soging
    - Forbinder relateret viden

    Subclasses skal implementere alle abstracte metoder.
    """

    def __init__(self, domain: str):
        """
        Initialiser Bibliotekar for en specifik domane.

        Args:
            domain: Videndomane (fx 'web3', 'legal')
        """
        self.domain = domain
        self._initialized = False
        self._taxonomy: Optional[Taxonomy] = None

    async def initialize(self) -> None:
        """Initialiser Bibliotekaren med nødvendige ressourcer."""
        self._initialized = True

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @abstractmethod
    async def classify(self, content: Content) -> Classification:
        """
        Klassificer indhold i domane-specifikke kategorier.

        Args:
            content: Indholdet der skal klassificeres

        Returns:
            Classification objekt med kategorier og tags
        """
        pass

    @abstractmethod
    async def index(self, content: Content) -> IndexEntry:
        """
        Indekser indhold for effektiv soging.

        Args:
            content: Indholdet der skal indekseres

        Returns:
            IndexEntry med sogebare termer
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None
    ) -> SearchResults:
        """
        Sog i biblioteket med optional filtre.

        Args:
            query: Sogeforesporgsel
            filters: Optional filtre

        Returns:
            SearchResults med matchende indhold
        """
        pass

    @abstractmethod
    async def find_related(
        self,
        content_id: str,
        depth: int = 1
    ) -> List[RelatedContent]:
        """
        Find relateret indhold.

        Args:
            content_id: ID pa indholdet at finde relateret til
            depth: Dybde af relationer (1 = direkte, 2+ = transitive)

        Returns:
            Liste af relateret indhold
        """
        pass

    @abstractmethod
    async def get_taxonomy(self) -> Taxonomy:
        """
        Hent domanens taxonomi.

        Returns:
            Taxonomy objekt med kategori-hierarki
        """
        pass

    async def add_to_taxonomy(
        self,
        category_name: str,
        parent_category: Optional[str] = None,
        description: Optional[str] = None
    ) -> TaxonomyNode:
        """
        Tilføj en kategori til taxonomien.

        Args:
            category_name: Navn pa kategorien
            parent_category: Foraeldre-kategori (None = rod)
            description: Beskrivelse

        Returns:
            Den nye TaxonomyNode
        """
        node = TaxonomyNode(
            id=str(uuid.uuid4()),
            name=category_name,
            description=description,
            parent_id=parent_category
        )
        # Implementation would add to actual taxonomy storage
        return node

    async def get_category_contents(
        self,
        category: str,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResults:
        """
        Hent alt indhold i en kategori.

        Args:
            category: Kategorinavn
            page: Sidetal
            page_size: Antal pr. side

        Returns:
            SearchResults med indhold i kategorien
        """
        filters = SearchFilters(categories=[category])
        return await self.search("*", filters)

    async def suggest_categories(
        self,
        content: Content
    ) -> List[str]:
        """
        Foreslå kategorier for indhold.

        Args:
            content: Indholdet at foreslå kategorier for

        Returns:
            Liste af foreslåede kategori-navne
        """
        classification = await self.classify(content)
        suggestions = [classification.primary_category]
        suggestions.extend(classification.secondary_categories)
        return suggestions


# Registry for bibliotekar instances
_bibliotekar_registry: Dict[str, BibliotekarKommandant] = {}


def register_bibliotekar(domain: str, bibliotekar: BibliotekarKommandant) -> None:
    """Registrer en Bibliotekar for en domane."""
    _bibliotekar_registry[domain] = bibliotekar


def get_bibliotekar(domain: str) -> Optional[BibliotekarKommandant]:
    """
    Fa Bibliotekar for en domane.

    Args:
        domain: Videndomane

    Returns:
        BibliotekarKommandant instance eller None
    """
    return _bibliotekar_registry.get(domain)


def list_registered_bibliotekarer() -> List[str]:
    """List alle registrerede Bibliotekar domaner."""
    return list(_bibliotekar_registry.keys())
