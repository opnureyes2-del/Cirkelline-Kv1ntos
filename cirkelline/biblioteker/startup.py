"""
Multi-Bibliotek Startup Configuration
=====================================

FASE 6: Multi-Bibliotek Arkitektur

Registrerer alle biblioteks-adapters ved application startup.
Import dette modul for at initialisere Multi-Bibliotek systemet.

Brug:
    from cirkelline.biblioteker.startup import initialize_biblioteker

    # I FastAPI lifespan
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await initialize_biblioteker()
        yield
"""

from typing import Optional
import os

from .base import BibliotekSource
from .multi_bibliotek import (
    MultiBibliotek,
    register_adapter,
    get_bibliotek,
)
from .adapters import (
    CosmicLibraryAdapter,
    NotionAdapter,
    AgentLearningAdapter,
)

# Global initialization flag
_initialized = False


def register_default_adapters() -> None:
    """
    Registrer alle default biblioteks-adapters.

    Kaldes automatisk ved initialization.
    """
    # Register Cosmic Library adapter
    register_adapter(BibliotekSource.COSMIC_LIBRARY, CosmicLibraryAdapter)

    # Register Notion adapter
    register_adapter(BibliotekSource.NOTION, NotionAdapter)

    # Register Agent Learning adapter
    register_adapter(BibliotekSource.AGENT_LEARNING, AgentLearningAdapter)

    print("✅ Multi-Bibliotek adapters registered")


async def initialize_biblioteker(
    domains: Optional[list] = None
) -> MultiBibliotek:
    """
    Initialiser Multi-Bibliotek systemet.

    Args:
        domains: Liste af domæner at initialisere (None = default)

    Returns:
        Forbundet MultiBibliotek instance
    """
    global _initialized

    if not _initialized:
        register_default_adapters()
        _initialized = True

    # Hent eller opret default bibliotek
    bibliotek = get_bibliotek()

    # Opret og registrer adapters
    # Cosmic Library
    cosmic = CosmicLibraryAdapter()
    bibliotek.register_adapter(
        BibliotekSource.COSMIC_LIBRARY,
        cosmic,
        priority=1,
        enabled=bool(os.getenv("COSMIC_LIBRARY_URL", ""))
    )

    # Agent Learning (altid aktiveret)
    agent_learning = AgentLearningAdapter()
    bibliotek.register_adapter(
        BibliotekSource.AGENT_LEARNING,
        agent_learning,
        priority=2,
        enabled=True
    )

    # Notion (aktiveres hvis OAuth token findes)
    notion = NotionAdapter()
    bibliotek.register_adapter(
        BibliotekSource.NOTION,
        notion,
        priority=3,
        enabled=bool(os.getenv("NOTION_INTEGRATION_TOKEN", ""))
    )

    # Forbind alle
    connection_results = await bibliotek.connect_all()

    print("✅ Multi-Bibliotek connections:")
    for source, connected in connection_results.items():
        status = "✓" if connected else "✗"
        print(f"   {status} {source.value}")

    return bibliotek


async def shutdown_biblioteker() -> None:
    """
    Shutdown Multi-Bibliotek systemet.

    Afbryder alle forbindelser og frigiver resourcer.
    """
    bibliotek = get_bibliotek()
    await bibliotek.disconnect_all()
    print("✅ Multi-Bibliotek connections closed")


# Auto-register adapters on module import
register_default_adapters()
