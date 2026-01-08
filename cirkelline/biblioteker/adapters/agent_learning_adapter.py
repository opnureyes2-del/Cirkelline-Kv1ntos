"""
Agent Learning Database Adapter
===============================

FASE 6: Multi-Bibliotek Arkitektur

Adapter for integration med Agent Learning databasen.
Bruger den interne agent.learning_* tabeller.

Features:
    - Kommandant learning data
    - Knowledge events og patterns
    - Domain-specifik viden
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from ..base import (
    BibliotekSource,
    BibliotekAdapter,
    LibraryItem,
    SearchQuery,
    SearchResult,
    SyncStatus,
    ItemType,
)
from ...kommandanter.database import AgentLearningDB, get_agent_learning_db


class AgentLearningAdapter(BibliotekAdapter):
    """
    Adapter for Agent Learning Database.

    Integrerer med den interne database for agent læring,
    som bruges af Historiker og Bibliotekar Kommandanterne.

    Tabeller:
        - agent.learning_content
        - agent.learning_events
        - agent.learning_patterns
        - agent.learning_taxonomy
    """

    def __init__(self, source: BibliotekSource = BibliotekSource.AGENT_LEARNING):
        super().__init__(source)
        self._db: Optional[AgentLearningDB] = None
        self._domain: Optional[str] = None

    def set_domain(self, domain: str) -> None:
        """
        Sæt aktiv videndomæne.

        Args:
            domain: Domæne-identifikator (web3, legal, etc.)
        """
        self._domain = domain

    async def connect(self) -> bool:
        """Opret forbindelse til Agent Learning database."""
        try:
            self._db = get_agent_learning_db()
            await self._db.connect()
            self._connected = True
            return True

        except Exception as e:
            print(f"Agent Learning DB forbindelsesfejl: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Afbryd forbindelse."""
        if self._db:
            await self._db.disconnect()
        self._connected = False

    async def search(self, query: SearchQuery) -> SearchResult:
        """
        Søg i Agent Learning content.

        Bruger full-text søgning i learning_content tabellen.
        """
        if not self._connected or not self._db:
            return SearchResult(
                items=[],
                total_count=0,
                query=query.query,
                sources_searched=[self.source]
            )

        try:
            # Bestem domain filter
            domain = None
            if query.domains:
                domain = query.domains[0]  # Brug første domain
            elif self._domain:
                domain = self._domain

            if not domain:
                # Uden domain, søg i alle
                domain = "web3"  # Default domain

            # Map ItemType til content_type
            content_types = None
            if query.item_types:
                type_map = {
                    ItemType.DOCUMENT: "document",
                    ItemType.KNOWLEDGE: "research_finding",
                    ItemType.RESEARCH: "analysis",
                    ItemType.NOTE: "note",
                    ItemType.REFERENCE: "reference",
                }
                content_types = [
                    type_map.get(t, "document") for t in query.item_types
                ]

            # Søg i database
            results = await self._db.search_content(
                domain=domain,
                query=query.query,
                categories=query.categories,
                tags=query.tags,
                content_types=content_types,
                limit=query.limit,
                offset=query.offset
            )

            # Konverter til LibraryItems
            items = [
                self._convert_content_to_library_item(row)
                for row in results
            ]

            return SearchResult(
                items=items,
                total_count=len(items),  # TODO: Få total count fra DB
                query=query.query,
                sources_searched=[self.source]
            )

        except Exception as e:
            print(f"Agent Learning søgefejl: {e}")
            return SearchResult(
                items=[],
                total_count=0,
                query=query.query,
                sources_searched=[self.source]
            )

    async def get_item(self, item_id: str) -> Optional[LibraryItem]:
        """Hent specifikt item."""
        if not self._connected or not self._db:
            return None

        try:
            content = await self._db.get_content(item_id)
            if content:
                return self._convert_content_to_library_item(content)
            return None

        except Exception as e:
            print(f"Agent Learning get_item fejl: {e}")
            return None

    async def list_items(
        self,
        domain: Optional[str] = None,
        item_type: Optional[ItemType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[LibraryItem]:
        """List items fra Agent Learning."""
        query = SearchQuery(
            query="*",
            domains=[domain] if domain else ([self._domain] if self._domain else None),
            item_types=[item_type] if item_type else None,
            limit=limit,
            offset=offset
        )
        result = await self.search(query)
        return result.items

    async def save_item(self, item: LibraryItem) -> str:
        """Gem item i Agent Learning database."""
        if not self._connected or not self._db:
            raise ConnectionError("Ikke forbundet til Agent Learning DB")

        try:
            # Map ItemType til content_type
            type_map = {
                ItemType.DOCUMENT: "document",
                ItemType.KNOWLEDGE: "research_finding",
                ItemType.RESEARCH: "analysis",
                ItemType.TRAINING_DATA: "research_finding",
                ItemType.NOTE: "note",
                ItemType.REFERENCE: "reference",
            }

            content_id = await self._db.save_content(
                domain=item.domain or self._domain or "default",
                title=item.title,
                body=item.content,
                content_type=type_map.get(item.item_type, "document"),
                source=f"{self.source.value}:{item.source_id}" if item.source_id else None,
                primary_category=item.categories[0] if item.categories else None,
                secondary_categories=item.categories[1:] if len(item.categories) > 1 else None,
                tags=item.tags,
                metadata=item.metadata
            )

            return content_id

        except Exception as e:
            raise Exception(f"Agent Learning save_item fejl: {e}")

    async def delete_item(self, item_id: str) -> bool:
        """Slet item fra Agent Learning (ikke implementeret)."""
        # Vi sletter normalt ikke fra learning data
        # Det arkiveres i stedet
        return False

    async def sync(self) -> SyncStatus:
        """Synkronisering er ikke nødvendig for lokal DB."""
        self._last_sync = datetime.utcnow()
        return SyncStatus(
            source=self.source,
            last_sync=self._last_sync,
            status="success"
        )

    async def get_learning_events(
        self,
        domain: Optional[str] = None,
        topic: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Hent knowledge events fra Historiker.

        Args:
            domain: Filtrer på domæne
            topic: Filtrer på emne
            limit: Max antal

        Returns:
            Liste af events
        """
        if not self._connected or not self._db:
            return []

        try:
            return await self._db.get_events(
                domain=domain or self._domain or "web3",
                topic=topic,
                limit=limit
            )
        except Exception:
            return []

    async def get_patterns(
        self,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Hent identificerede patterns.

        Args:
            domain: Filtrer på domæne

        Returns:
            Liste af patterns
        """
        if not self._connected or not self._db:
            return []

        try:
            return await self._db.get_patterns(
                domain=domain or self._domain or "web3"
            )
        except Exception:
            return []

    async def get_taxonomy(
        self,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Hent taxonomi for domæne.

        Args:
            domain: Domæne

        Returns:
            Liste af taxonomy nodes
        """
        if not self._connected or not self._db:
            return []

        try:
            return await self._db.get_taxonomy(
                domain=domain or self._domain or "web3"
            )
        except Exception:
            return []

    def _convert_content_to_library_item(
        self,
        content: Dict[str, Any]
    ) -> LibraryItem:
        """Konverter database content til LibraryItem."""
        # Map content_type til ItemType
        type_map = {
            "document": ItemType.DOCUMENT,
            "research_finding": ItemType.RESEARCH,
            "analysis": ItemType.RESEARCH,
            "report": ItemType.DOCUMENT,
            "note": ItemType.NOTE,
            "reference": ItemType.REFERENCE,
            "external_link": ItemType.REFERENCE,
        }

        content_type = content.get("content_type", "document")
        item_type = type_map.get(content_type, ItemType.DOCUMENT)

        # Parse JSON fields
        import json
        tags = content.get("tags", [])
        if isinstance(tags, str):
            tags = json.loads(tags)

        secondary_cats = content.get("secondary_categories", [])
        if isinstance(secondary_cats, str):
            secondary_cats = json.loads(secondary_cats)

        categories = []
        if content.get("primary_category"):
            categories.append(content["primary_category"])
        categories.extend(secondary_cats)

        metadata = content.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        return LibraryItem(
            id=str(content.get("id", "")),
            title=content.get("title", "Untitled"),
            content=content.get("body", ""),
            source=self.source,
            item_type=item_type,
            source_id=str(content.get("id", "")),
            metadata=metadata,
            tags=tags,
            categories=categories,
            domain=content.get("domain"),
            created_at=content.get("created_at", datetime.utcnow()),
            updated_at=content.get("updated_at", datetime.utcnow()),
        )

    async def health_check(self) -> Dict[str, Any]:
        """Sundhedstjek for Agent Learning DB."""
        base_health = await super().health_check()
        base_health["domain"] = self._domain

        if self._connected and self._db:
            try:
                # Simpelt tjek - hent domains
                domains = await self._db.list_domains()
                base_health["available_domains"] = [d["domain_name"] for d in domains]
                base_health["db_status"] = "healthy"
            except Exception as e:
                base_health["db_status"] = f"error: {e}"

        return base_health
