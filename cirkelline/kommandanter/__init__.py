"""
Cirkelline Kommandanter Module
==============================

FASE 6: Multi-Bibliotek Arkitektur

Dette modul definerer Historiker og Bibliotekar Kommandanter
som er ansvarlige for videns-bevaring og organisering pa tvaers
af Cirkellines multi-bibliotek arkitektur.

Komponenter:
    - HistorikerKommandant: Historisk bevaring og kontekstualisering
    - BibliotekarKommandant: Organisering, klassifikation og soging
    - DomainKommandantFactory: Factory til at oprette domane-specifikke kommandanter

Domaner:
    - web3: Web3 Research Domain
    - legal: Legal/Juridisk Domain
    - custom: Bruger-definerede domaner

Eksempel:
    from cirkelline.kommandanter import (
        get_historiker,
        get_bibliotekar,
        create_domain_kommandanter
    )

    # Fa Web3 domane kommandanter
    web3_historiker = get_historiker("web3")
    web3_bibliotekar = get_bibliotekar("web3")

    # Opret ny domane med begge kommandanter
    kommandanter = create_domain_kommandanter("custom_domain")
"""

from .historiker import (
    HistorikerKommandant,
    KnowledgeEvent,
    Timeline,
    EvolutionReport,
    Pattern,
    get_historiker,
)

from .bibliotekar import (
    BibliotekarKommandant,
    Classification,
    IndexEntry,
    SearchResults,
    SearchFilters,
    RelatedContent,
    Taxonomy,
    get_bibliotekar,
)

from .factory import (
    DomainKommandantFactory,
    create_domain_kommandanter,
    get_available_domains,
)

from .database import (
    AgentLearningDB,
    get_agent_learning_db,
    initialize_agent_learning_db,
)

__all__ = [
    # Historiker
    "HistorikerKommandant",
    "KnowledgeEvent",
    "Timeline",
    "EvolutionReport",
    "Pattern",
    "get_historiker",

    # Bibliotekar
    "BibliotekarKommandant",
    "Classification",
    "IndexEntry",
    "SearchResults",
    "SearchFilters",
    "RelatedContent",
    "Taxonomy",
    "get_bibliotekar",

    # Factory
    "DomainKommandantFactory",
    "create_domain_kommandanter",
    "get_available_domains",

    # Database
    "AgentLearningDB",
    "get_agent_learning_db",
    "initialize_agent_learning_db",
]

__version__ = "1.0.0"
