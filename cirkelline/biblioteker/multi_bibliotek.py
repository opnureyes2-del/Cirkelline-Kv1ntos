"""
Multi-Bibliotek Orchestrator
============================

FASE 6: Multi-Bibliotek Arkitektur

Den centrale orchestrator der forener alle biblioteks-kilder
til én samlet interface.

Funktioner:
    - Søgning på tværs af alle kilder
    - Intelligent routing til relevante kilder
    - Caching og optimering
    - Synkronisering mellem kilder
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass, field

from .base import (
    BibliotekSource,
    BibliotekAdapter,
    LibraryItem,
    SearchQuery,
    SearchResult,
    SyncStatus,
    ItemType,
)


@dataclass
class BibliotekConfig:
    """Konfiguration for et enkelt bibliotek."""
    source: BibliotekSource
    adapter_class: Type[BibliotekAdapter]
    enabled: bool = True
    priority: int = 1  # Lavere = højere prioritet
    config: Dict[str, Any] = field(default_factory=dict)


class MultiBibliotek:
    """
    Central orchestrator for Multi-Bibliotek systemet.

    Forener flere biblioteks-kilder til én samlet interface.
    Håndterer søgning, routing og synkronisering.

    Eksempel:
        bibliotek = MultiBibliotek()
        await bibliotek.connect_all()

        # Søg på tværs af alle kilder
        results = await bibliotek.search("smart contracts")

        # Søg kun i specifikke kilder
        results = await bibliotek.search(
            "legal compliance",
            sources=[BibliotekSource.NOTION, BibliotekSource.AGENT_LEARNING]
        )
    """

    def __init__(self):
        self._adapters: Dict[BibliotekSource, BibliotekAdapter] = {}
        self._configs: Dict[BibliotekSource, BibliotekConfig] = {}
        self._initialized = False
        self._domain: Optional[str] = None

    def register_adapter(
        self,
        source: BibliotekSource,
        adapter: BibliotekAdapter,
        priority: int = 1,
        enabled: bool = True
    ) -> None:
        """
        Registrer en biblioteks-adapter.

        Args:
            source: Biblioteks-kilde
            adapter: Adapter instance
            priority: Søge-prioritet (lavere = først)
            enabled: Om adapteren er aktiveret
        """
        self._adapters[source] = adapter
        self._configs[source] = BibliotekConfig(
            source=source,
            adapter_class=type(adapter),
            enabled=enabled,
            priority=priority
        )

    def get_adapter(self, source: BibliotekSource) -> Optional[BibliotekAdapter]:
        """Hent adapter for en kilde."""
        config = self._configs.get(source)
        if config and config.enabled:
            return self._adapters.get(source)
        return None

    def list_sources(self) -> List[BibliotekSource]:
        """List alle registrerede kilder."""
        return [
            source for source, config in self._configs.items()
            if config.enabled
        ]

    async def connect_all(self) -> Dict[BibliotekSource, bool]:
        """
        Opret forbindelse til alle adapters.

        Returns:
            Dict med status for hver kilde
        """
        results = {}
        for source, adapter in self._adapters.items():
            config = self._configs.get(source)
            if config and config.enabled:
                try:
                    results[source] = await adapter.connect()
                except Exception as e:
                    print(f"Fejl ved forbindelse til {source.value}: {e}")
                    results[source] = False
        self._initialized = True
        return results

    async def disconnect_all(self) -> None:
        """Afbryd forbindelse til alle adapters."""
        for adapter in self._adapters.values():
            try:
                await adapter.disconnect()
            except Exception:
                pass
        self._initialized = False

    async def search(
        self,
        query: str,
        sources: Optional[List[BibliotekSource]] = None,
        domains: Optional[List[str]] = None,
        item_types: Optional[List[ItemType]] = None,
        limit: int = 20,
        offset: int = 0,
        parallel: bool = True
    ) -> SearchResult:
        """
        Søg på tværs af biblioteker.

        Args:
            query: Søgetekst
            sources: Kilder at søge i (None = alle)
            domains: Domæner at filtrere på
            item_types: Typer at filtrere på
            limit: Max resultater per kilde
            offset: Start offset
            parallel: Søg parallelt (hurtigere men bruger mere resourcer)

        Returns:
            Samlet SearchResult fra alle kilder
        """
        start_time = time.time()

        # Byg søgeforespørgsel
        search_query = SearchQuery(
            query=query,
            sources=sources,
            domains=domains,
            item_types=item_types,
            limit=limit,
            offset=offset
        )

        # Bestem hvilke kilder at søge i
        target_sources = sources or self.list_sources()
        active_adapters = [
            (source, self._adapters[source])
            for source in target_sources
            if source in self._adapters and self._configs.get(source, BibliotekConfig(source, BibliotekAdapter)).enabled
        ]

        # Sortér efter prioritet
        active_adapters.sort(key=lambda x: self._configs[x[0]].priority)

        # Udfør søgning
        all_items: List[LibraryItem] = []
        total_count = 0
        sources_searched: List[BibliotekSource] = []

        if parallel and len(active_adapters) > 1:
            # Parallel søgning
            tasks = [
                adapter.search(search_query)
                for _, adapter in active_adapters
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for (source, _), result in zip(active_adapters, results):
                if isinstance(result, SearchResult):
                    all_items.extend(result.items)
                    total_count += result.total_count
                    sources_searched.append(source)
                elif isinstance(result, Exception):
                    print(f"Søgefejl i {source.value}: {result}")
        else:
            # Sekventiel søgning
            for source, adapter in active_adapters:
                try:
                    result = await adapter.search(search_query)
                    all_items.extend(result.items)
                    total_count += result.total_count
                    sources_searched.append(source)
                except Exception as e:
                    print(f"Søgefejl i {source.value}: {e}")

        # Sortér resultater (nyeste først som default)
        all_items.sort(key=lambda x: x.updated_at, reverse=True)

        # Anvend global limit
        paginated_items = all_items[offset:offset + limit]

        execution_time = (time.time() - start_time) * 1000

        return SearchResult(
            items=paginated_items,
            total_count=total_count,
            query=query,
            sources_searched=sources_searched,
            execution_time_ms=execution_time,
            page=(offset // limit) + 1 if limit > 0 else 1,
            page_size=limit,
            has_more=len(all_items) > offset + limit
        )

    async def get_item(
        self,
        item_id: str,
        source: Optional[BibliotekSource] = None
    ) -> Optional[LibraryItem]:
        """
        Hent et specifikt item.

        Args:
            item_id: Item ID
            source: Kilde at søge i (None = søg alle)

        Returns:
            LibraryItem eller None
        """
        if source:
            adapter = self.get_adapter(source)
            if adapter:
                return await adapter.get_item(item_id)
            return None

        # Søg i alle kilder
        for src, adapter in self._adapters.items():
            if self._configs.get(src, BibliotekConfig(src, BibliotekAdapter)).enabled:
                try:
                    item = await adapter.get_item(item_id)
                    if item:
                        return item
                except Exception:
                    continue
        return None

    async def save_item(
        self,
        item: LibraryItem,
        source: Optional[BibliotekSource] = None
    ) -> str:
        """
        Gem et item.

        Args:
            item: Item at gemme
            source: Kilde at gemme i (None = brug item.source)

        Returns:
            ID på gemt item

        Raises:
            ValueError: Hvis ingen valid kilde
        """
        target_source = source or item.source
        adapter = self.get_adapter(target_source)

        if not adapter:
            raise ValueError(f"Ingen adapter for {target_source.value}")

        return await adapter.save_item(item)

    async def sync_all(self) -> Dict[BibliotekSource, SyncStatus]:
        """
        Synkroniser alle kilder.

        Returns:
            Dict med SyncStatus for hver kilde
        """
        results = {}
        for source, adapter in self._adapters.items():
            config = self._configs.get(source)
            if config and config.enabled:
                try:
                    results[source] = await adapter.sync()
                except Exception as e:
                    results[source] = SyncStatus(
                        source=source,
                        status="failed",
                        error=str(e)
                    )
        return results

    async def health_check(self) -> Dict[str, Any]:
        """
        Udfør sundhedstjek på hele systemet.

        Returns:
            Dict med sundhedsinformation
        """
        adapter_health = {}
        for source, adapter in self._adapters.items():
            try:
                adapter_health[source.value] = await adapter.health_check()
            except Exception as e:
                adapter_health[source.value] = {"error": str(e)}

        return {
            "initialized": self._initialized,
            "domain": self._domain,
            "adapters": adapter_health,
            "active_sources": [s.value for s in self.list_sources()],
            "timestamp": datetime.utcnow().isoformat()
        }


# ============================================
# REGISTRY & FACTORY
# ============================================

_bibliotek_registry: Dict[str, MultiBibliotek] = {}
_adapter_registry: Dict[BibliotekSource, Type[BibliotekAdapter]] = {}


def register_adapter(
    source: BibliotekSource,
    adapter_class: Type[BibliotekAdapter]
) -> None:
    """
    Registrer en adapter-klasse globalt.

    Args:
        source: Biblioteks-kilde
        adapter_class: Adapter klasse
    """
    _adapter_registry[source] = adapter_class


def get_bibliotek(
    domain: Optional[str] = None,
    sources: Optional[List[BibliotekSource]] = None
) -> MultiBibliotek:
    """
    Hent eller opret en MultiBibliotek instance.

    Args:
        domain: Videndomæne (bruges som cache-nøgle)
        sources: Kilder at inkludere (None = alle)

    Returns:
        MultiBibliotek instance
    """
    cache_key = domain or "default"

    if cache_key in _bibliotek_registry:
        return _bibliotek_registry[cache_key]

    # Opret nyt bibliotek
    bibliotek = MultiBibliotek()
    bibliotek._domain = domain

    # Registrer alle tilgængelige adapters
    for source, adapter_class in _adapter_registry.items():
        if sources is None or source in sources:
            try:
                adapter = adapter_class(source)
                bibliotek.register_adapter(source, adapter)
            except Exception as e:
                print(f"Kunne ikke oprette adapter for {source.value}: {e}")

    _bibliotek_registry[cache_key] = bibliotek
    return bibliotek


def list_biblioteker() -> List[str]:
    """
    List alle aktive biblioteker.

    Returns:
        Liste af bibliotek-domæner/nøgler
    """
    return list(_bibliotek_registry.keys())


async def initialize_default_bibliotek() -> MultiBibliotek:
    """
    Initialiser og forbind default bibliotek.

    Returns:
        Forbundet MultiBibliotek
    """
    bibliotek = get_bibliotek()
    await bibliotek.connect_all()
    return bibliotek
