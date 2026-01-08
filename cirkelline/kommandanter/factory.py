"""
Domain Kommandant Factory
=========================

FASE 6: Multi-Bibliotek Arkitektur

Factory til at oprette og administrere domane-specifikke
Historiker og Bibliotekar Kommandanter.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List, Type
from .historiker import HistorikerKommandant, register_historiker
from .bibliotekar import BibliotekarKommandant, register_bibliotekar


@dataclass
class DomainKommandanter:
    """
    Container for en domanes Kommandanter.

    Attributes:
        domain: Videndomane
        historiker: Historiker-Kommandant instance
        bibliotekar: Bibliotekar-Kommandant instance
    """
    domain: str
    historiker: HistorikerKommandant
    bibliotekar: BibliotekarKommandant


class DomainKommandantFactory:
    """
    Factory til at oprette domane-specifikke Kommandanter.

    Denne factory holder styr pa registrerede domaner
    og deres tilhorende Historiker/Bibliotekar klasser.
    """

    # Registry of domain implementations
    _domain_classes: Dict[str, Tuple[Type[HistorikerKommandant], Type[BibliotekarKommandant]]] = {}

    # Active instances
    _instances: Dict[str, DomainKommandanter] = {}

    @classmethod
    def register_domain(
        cls,
        domain: str,
        historiker_class: Type[HistorikerKommandant],
        bibliotekar_class: Type[BibliotekarKommandant]
    ) -> None:
        """
        Registrer en domane med dens Kommandant klasser.

        Args:
            domain: Unik domane-identifikator
            historiker_class: Historiker klasse for domanen
            bibliotekar_class: Bibliotekar klasse for domanen
        """
        cls._domain_classes[domain] = (historiker_class, bibliotekar_class)

    @classmethod
    def create(cls, domain: str) -> DomainKommandanter:
        """
        Opret Kommandanter for en domane.

        Args:
            domain: Domane-identifikator

        Returns:
            DomainKommandanter med begge instances

        Raises:
            ValueError: Hvis domanen ikke er registreret
        """
        if domain not in cls._domain_classes:
            raise ValueError(
                f"Domain '{domain}' is not registered. "
                f"Available domains: {list(cls._domain_classes.keys())}"
            )

        # Return existing instance if available
        if domain in cls._instances:
            return cls._instances[domain]

        # Create new instances
        historiker_class, bibliotekar_class = cls._domain_classes[domain]

        historiker = historiker_class(domain)
        bibliotekar = bibliotekar_class(domain)

        # Register with global registries
        register_historiker(domain, historiker)
        register_bibliotekar(domain, bibliotekar)

        # Store and return
        kommandanter = DomainKommandanter(
            domain=domain,
            historiker=historiker,
            bibliotekar=bibliotekar
        )
        cls._instances[domain] = kommandanter

        return kommandanter

    @classmethod
    def get(cls, domain: str) -> Optional[DomainKommandanter]:
        """
        Fa eksisterende Kommandanter for en domane.

        Args:
            domain: Domane-identifikator

        Returns:
            DomainKommandanter eller None
        """
        return cls._instances.get(domain)

    @classmethod
    def get_available_domains(cls) -> List[str]:
        """
        List alle registrerede domaner.

        Returns:
            Liste af domane-navne
        """
        return list(cls._domain_classes.keys())

    @classmethod
    def get_active_domains(cls) -> List[str]:
        """
        List alle aktive domaner (med oprettede instances).

        Returns:
            Liste af aktive domane-navne
        """
        return list(cls._instances.keys())

    @classmethod
    async def initialize_domain(cls, domain: str) -> DomainKommandanter:
        """
        Opret og initialiser Kommandanter for en domane.

        Args:
            domain: Domane-identifikator

        Returns:
            Initialiserede DomainKommandanter
        """
        kommandanter = cls.create(domain)
        await kommandanter.historiker.initialize()
        await kommandanter.bibliotekar.initialize()
        return kommandanter


# Convenience functions
def create_domain_kommandanter(domain: str) -> DomainKommandanter:
    """
    Opret Kommandanter for en domane.

    Args:
        domain: Domane-identifikator

    Returns:
        DomainKommandanter
    """
    return DomainKommandantFactory.create(domain)


def get_available_domains() -> List[str]:
    """
    List alle tilgangelige domaner.

    Returns:
        Liste af domane-navne
    """
    return DomainKommandantFactory.get_available_domains()


# Import og registrer built-in domaner
def _register_builtin_domains():
    """Registrer de indbyggede domaner."""
    try:
        from .implementations.web3_kommandanter import (
            Web3HistorikerKommandant,
            Web3BibliotekarKommandant
        )
        DomainKommandantFactory.register_domain(
            "web3",
            Web3HistorikerKommandant,
            Web3BibliotekarKommandant
        )
    except ImportError:
        pass  # Web3 domain not available yet

    try:
        from .implementations.legal_kommandanter import (
            LegalHistorikerKommandant,
            LegalBibliotekarKommandant
        )
        DomainKommandantFactory.register_domain(
            "legal",
            LegalHistorikerKommandant,
            LegalBibliotekarKommandant
        )
    except ImportError:
        pass  # Legal domain not available yet


# Register built-in domains on module load
_register_builtin_domains()
