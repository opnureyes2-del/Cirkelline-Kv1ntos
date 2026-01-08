"""
Cosmic Library Adapter
======================

FASE 6: Multi-Bibliotek Arkitektur

Adapter for integration med Cosmic Library systemet.
Cosmic Library er den centrale AI trænings- og videns-platform.

Features:
    - Knowledge domains (web3, legal, financial, etc.)
    - Agent training data
    - Research findings
    - Cross-disciplinary knowledge
"""

import os
import aiohttp
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


class CosmicLibraryAdapter(BibliotekAdapter):
    """
    Adapter for Cosmic Library integration.

    Cosmic Library er den centrale viden-repository for
    AI agent træning og research i Cirkelline-økosystemet.

    Konfiguration via environment:
        - COSMIC_LIBRARY_URL: Base URL (default: http://localhost:7780)
        - COSMIC_LIBRARY_API_KEY: API nøgle (optional)
    """

    def __init__(self, source: BibliotekSource = BibliotekSource.COSMIC_LIBRARY):
        super().__init__(source)
        self.base_url = os.getenv("COSMIC_LIBRARY_URL", "http://localhost:7780")
        self.api_key = os.getenv("COSMIC_LIBRARY_API_KEY")
        self._session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> bool:
        """Opret forbindelse til Cosmic Library API."""
        try:
            self._session = aiohttp.ClientSession(
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=30)
            )

            # Verificer forbindelse med health check
            async with self._session.get(f"{self.base_url}/health") as resp:
                if resp.status == 200:
                    self._connected = True
                    return True

            self._connected = False
            return False

        except Exception as e:
            print(f"Cosmic Library forbindelsesfejl: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Afbryd forbindelse."""
        if self._session:
            await self._session.close()
            self._session = None
        self._connected = False

    def _get_headers(self) -> Dict[str, str]:
        """Byg HTTP headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def search(self, query: SearchQuery) -> SearchResult:
        """
        Søg i Cosmic Library.

        Understøtter:
            - Full-text søgning
            - Domain filtrering
            - Knowledge type filtrering
        """
        if not self._connected or not self._session:
            return SearchResult(
                items=[],
                total_count=0,
                query=query.query,
                sources_searched=[self.source]
            )

        try:
            # Byg search request
            search_params = {
                "query": query.query,
                "limit": query.limit,
                "offset": query.offset
            }

            if query.domains:
                search_params["domains"] = query.domains

            if query.item_types:
                search_params["types"] = [t.value for t in query.item_types]

            async with self._session.post(
                f"{self.base_url}/api/knowledge/search",
                json=search_params
            ) as resp:
                if resp.status != 200:
                    return SearchResult(
                        items=[],
                        total_count=0,
                        query=query.query,
                        sources_searched=[self.source]
                    )

                data = await resp.json()

            # Konverter til LibraryItems
            items = []
            for item_data in data.get("results", []):
                items.append(self._convert_to_library_item(item_data))

            return SearchResult(
                items=items,
                total_count=data.get("total", len(items)),
                query=query.query,
                sources_searched=[self.source]
            )

        except Exception as e:
            print(f"Cosmic Library søgefejl: {e}")
            return SearchResult(
                items=[],
                total_count=0,
                query=query.query,
                sources_searched=[self.source]
            )

    async def get_item(self, item_id: str) -> Optional[LibraryItem]:
        """Hent specifikt item fra Cosmic Library."""
        if not self._connected or not self._session:
            return None

        try:
            async with self._session.get(
                f"{self.base_url}/api/knowledge/{item_id}"
            ) as resp:
                if resp.status != 200:
                    return None

                data = await resp.json()
                return self._convert_to_library_item(data)

        except Exception as e:
            print(f"Cosmic Library get_item fejl: {e}")
            return None

    async def list_items(
        self,
        domain: Optional[str] = None,
        item_type: Optional[ItemType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[LibraryItem]:
        """List items fra Cosmic Library."""
        query = SearchQuery(
            query="*",
            domains=[domain] if domain else None,
            item_types=[item_type] if item_type else None,
            limit=limit,
            offset=offset
        )
        result = await self.search(query)
        return result.items

    async def save_item(self, item: LibraryItem) -> str:
        """Gem item i Cosmic Library."""
        if not self._connected or not self._session:
            raise ConnectionError("Ikke forbundet til Cosmic Library")

        try:
            async with self._session.post(
                f"{self.base_url}/api/knowledge",
                json={
                    "title": item.title,
                    "content": item.content,
                    "type": item.item_type.value,
                    "domain": item.domain,
                    "tags": item.tags,
                    "metadata": item.metadata
                }
            ) as resp:
                if resp.status not in (200, 201):
                    raise Exception(f"Gem fejl: {resp.status}")

                data = await resp.json()
                return data.get("id", item.id)

        except Exception as e:
            raise Exception(f"Cosmic Library save_item fejl: {e}")

    async def delete_item(self, item_id: str) -> bool:
        """Slet item fra Cosmic Library."""
        if not self._connected or not self._session:
            return False

        try:
            async with self._session.delete(
                f"{self.base_url}/api/knowledge/{item_id}"
            ) as resp:
                return resp.status in (200, 204)

        except Exception:
            return False

    async def sync(self) -> SyncStatus:
        """Synkroniser med Cosmic Library."""
        # Cosmic Library er source-of-truth, så sync er primært pull
        self._last_sync = datetime.utcnow()
        return SyncStatus(
            source=self.source,
            last_sync=self._last_sync,
            status="success"
        )

    async def get_knowledge_domains(self) -> List[Dict[str, Any]]:
        """
        Hent tilgængelige knowledge domains fra Cosmic Library.

        Returns:
            Liste af domain konfigurationer
        """
        if not self._connected or not self._session:
            return []

        try:
            async with self._session.get(
                f"{self.base_url}/api/domains"
            ) as resp:
                if resp.status != 200:
                    return []
                return await resp.json()

        except Exception:
            return []

    def _convert_to_library_item(self, data: Dict[str, Any]) -> LibraryItem:
        """Konverter Cosmic Library data til LibraryItem."""
        # Map Cosmic Library types til ItemType
        type_mapping = {
            "knowledge": ItemType.KNOWLEDGE,
            "document": ItemType.DOCUMENT,
            "research": ItemType.RESEARCH,
            "training": ItemType.TRAINING_DATA,
            "reference": ItemType.REFERENCE,
        }

        cosmic_type = data.get("type", "knowledge")
        item_type = type_mapping.get(cosmic_type, ItemType.KNOWLEDGE)

        return LibraryItem(
            id=data.get("id", ""),
            title=data.get("title", "Untitled"),
            content=data.get("content", ""),
            source=self.source,
            item_type=item_type,
            source_id=data.get("id"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            categories=data.get("categories", []),
            domain=data.get("domain"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
            url=data.get("url"),
            author=data.get("author")
        )

    async def health_check(self) -> Dict[str, Any]:
        """Sundhedstjek for Cosmic Library."""
        base_health = await super().health_check()

        if self._connected and self._session:
            try:
                async with self._session.get(f"{self.base_url}/health") as resp:
                    if resp.status == 200:
                        base_health["api_status"] = "healthy"
                    else:
                        base_health["api_status"] = f"unhealthy ({resp.status})"
            except Exception as e:
                base_health["api_status"] = f"error: {e}"

        base_health["base_url"] = self.base_url
        return base_health
