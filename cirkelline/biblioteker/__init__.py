"""
Cirkelline Multi-Bibliotek Arkitektur
=====================================

FASE 6: Central Library Integration

Multi-Bibliotek systemet forener forskellige videns-kilder til
én samlet interface for Kommandanterne.

Kilder:
    - Cosmic Library: AI agent træning og viden
    - Notion: Bruger-definerede databaser
    - Agent Learning DB: Intern agent læring
    - Local Files: Lokale dokumenter (via CLA)

Brug:
    from cirkelline.biblioteker import (
        MultiBibliotek,
        get_bibliotek,
        list_biblioteker
    )

    # Hent samlet bibliotek
    bibliotek = get_bibliotek("web3")

    # Søg på tværs af alle kilder
    results = await bibliotek.search("smart contracts", sources=["cosmic", "notion"])
"""

from .base import (
    BibliotekSource,
    BibliotekAdapter,
    LibraryItem,
    SearchQuery,
    SearchResult,
)

from .multi_bibliotek import (
    MultiBibliotek,
    get_bibliotek,
    list_biblioteker,
    register_adapter,
)

from .adapters import (
    CosmicLibraryAdapter,
    NotionAdapter,
    AgentLearningAdapter,
)

__all__ = [
    # Base
    "BibliotekSource",
    "BibliotekAdapter",
    "LibraryItem",
    "SearchQuery",
    "SearchResult",

    # Multi-Bibliotek
    "MultiBibliotek",
    "get_bibliotek",
    "list_biblioteker",
    "register_adapter",

    # Adapters
    "CosmicLibraryAdapter",
    "NotionAdapter",
    "AgentLearningAdapter",
]

__version__ = "1.0.0"
