"""
Multi-Bibliotek Base Classes
============================

FASE 6: Multi-Bibliotek Arkitektur

Base interfaces og dataklasser for Multi-Bibliotek systemet.
Definerer kontrakten som alle bibliotek-adapters skal følge.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid


class BibliotekSource(Enum):
    """
    Tilgængelige biblioteks-kilder.

    Systemet er designet til at kunne udvides med nye kilder
    uden at ændre eksisterende kode.
    """
    COSMIC_LIBRARY = "cosmic"       # Cosmic Library AI training system
    NOTION = "notion"               # Notion databases
    AGENT_LEARNING = "agent"        # Internal agent learning DB
    LOCAL_FILES = "local"           # Local file system (via CLA)
    CUSTOM = "custom"               # User-defined sources


class ItemType(Enum):
    """Typer af biblioteks-items."""
    DOCUMENT = "document"
    KNOWLEDGE = "knowledge"
    TRAINING_DATA = "training_data"
    RESEARCH = "research"
    REFERENCE = "reference"
    NOTE = "note"
    TASK = "task"
    PROJECT = "project"


@dataclass
class LibraryItem:
    """
    Et item fra et bibliotek.

    Repræsenterer en generisk enhed der kan komme fra
    enhver biblioteks-kilde.

    Attributes:
        id: Unik identifikator
        title: Titel på item
        content: Indhold (tekst, markdown, etc.)
        source: Kilde-bibliotek
        item_type: Type af item
        metadata: Kilde-specifik metadata
        created_at: Oprettelsestidspunkt
        updated_at: Sidst opdateret
    """
    title: str
    content: str
    source: BibliotekSource
    item_type: ItemType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: Optional[str] = None  # Original ID i kildesystemet
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    url: Optional[str] = None  # Link til original kilde
    author: Optional[str] = None
    domain: Optional[str] = None  # Videndomæne (web3, legal, etc.)

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": self.source.value,
            "item_type": self.item_type.value,
            "source_id": self.source_id,
            "metadata": self.metadata,
            "tags": self.tags,
            "categories": self.categories,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "url": self.url,
            "author": self.author,
            "domain": self.domain,
        }


@dataclass
class SearchQuery:
    """
    Søgeforespørgsel til biblioteker.

    Attributes:
        query: Søgetekst
        sources: Kilder at søge i (None = alle)
        domains: Videndomæner at filtrere på
        item_types: Typer af items at filtrere på
        tags: Tags at filtrere på
        limit: Max antal resultater
        offset: Start offset for pagination
    """
    query: str
    sources: Optional[List[BibliotekSource]] = None
    domains: Optional[List[str]] = None
    item_types: Optional[List[ItemType]] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 20
    offset: int = 0
    include_content: bool = True  # Inkluder fuldt indhold i resultater


@dataclass
class SearchResult:
    """
    Resultat fra en biblioteks-søgning.

    Attributes:
        items: Liste af fundne items
        total_count: Totalt antal matches (før pagination)
        query: Den originale søgeforespørgsel
        sources_searched: Kilder der blev søgt i
        execution_time_ms: Søgetid i millisekunder
    """
    items: List[LibraryItem]
    total_count: int
    query: str
    sources_searched: List[BibliotekSource]
    execution_time_ms: float = 0.0
    page: int = 1
    page_size: int = 20
    has_more: bool = False
    facets: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    @property
    def item_count(self) -> int:
        return len(self.items)


@dataclass
class SyncStatus:
    """
    Status for synkronisering med en kilde.

    Attributes:
        source: Biblioteks-kilde
        last_sync: Tidspunkt for sidste synk
        items_synced: Antal items synkroniseret
        status: Status (success, failed, in_progress)
        error: Fejlbesked hvis relevant
    """
    source: BibliotekSource
    last_sync: Optional[datetime] = None
    items_synced: int = 0
    status: str = "unknown"  # success, failed, in_progress, unknown
    error: Optional[str] = None
    next_sync: Optional[datetime] = None


class BibliotekAdapter(ABC):
    """
    Abstract base class for biblioteks-adapters.

    Hver kilde (Cosmic Library, Notion, etc.) implementerer
    sin egen adapter der følger denne interface.

    Adapters er ansvarlige for:
    - Forbindelse til kildesystemet
    - Konvertering af data til LibraryItem format
    - Søgning i kildesystemet
    - Synkronisering af data
    """

    def __init__(self, source: BibliotekSource):
        """
        Initialiser adapter.

        Args:
            source: Biblioteks-kilden denne adapter håndterer
        """
        self.source = source
        self._connected = False
        self._last_sync: Optional[datetime] = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    @abstractmethod
    async def connect(self) -> bool:
        """
        Opret forbindelse til kildesystemet.

        Returns:
            True hvis forbindelse lykkedes
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Afbryd forbindelse til kildesystemet."""
        pass

    @abstractmethod
    async def search(self, query: SearchQuery) -> SearchResult:
        """
        Søg i biblioteket.

        Args:
            query: Søgeforespørgsel

        Returns:
            SearchResult med fundne items
        """
        pass

    @abstractmethod
    async def get_item(self, item_id: str) -> Optional[LibraryItem]:
        """
        Hent et specifikt item.

        Args:
            item_id: ID på item (kan være source_id eller intern id)

        Returns:
            LibraryItem eller None
        """
        pass

    @abstractmethod
    async def list_items(
        self,
        domain: Optional[str] = None,
        item_type: Optional[ItemType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[LibraryItem]:
        """
        List items fra biblioteket.

        Args:
            domain: Filtrer på videndomæne
            item_type: Filtrer på type
            limit: Max antal items
            offset: Start offset

        Returns:
            Liste af LibraryItems
        """
        pass

    @abstractmethod
    async def save_item(self, item: LibraryItem) -> str:
        """
        Gem et item i biblioteket.

        Args:
            item: Item at gemme

        Returns:
            ID på det gemte item
        """
        pass

    @abstractmethod
    async def delete_item(self, item_id: str) -> bool:
        """
        Slet et item fra biblioteket.

        Args:
            item_id: ID på item

        Returns:
            True hvis sletning lykkedes
        """
        pass

    async def sync(self) -> SyncStatus:
        """
        Synkroniser med kildesystemet.

        Default implementation - kan overskrives.

        Returns:
            SyncStatus med synkroniseringsresultat
        """
        return SyncStatus(
            source=self.source,
            last_sync=datetime.utcnow(),
            status="not_implemented"
        )

    async def get_sync_status(self) -> SyncStatus:
        """
        Hent synkroniseringsstatus.

        Returns:
            SyncStatus
        """
        return SyncStatus(
            source=self.source,
            last_sync=self._last_sync,
            status="connected" if self._connected else "disconnected"
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Udfør sundhedstjek på adapteren.

        Returns:
            Dict med sundhedsinformation
        """
        return {
            "source": self.source.value,
            "connected": self._connected,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
        }
