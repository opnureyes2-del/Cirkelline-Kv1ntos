"""
Kommandant Implementations
==========================

Konkrete implementationer af Historiker og Bibliotekar
Kommandanter for specifikke videndomaner.

Tilgangelige domaner:
    - web3: Web3/Blockchain research domain
    - legal: Juridisk/Legal domain

Opdateret: 2025-12-12 - Legal Kommandanter tilfojet
"""

# Import implementations when available
try:
    from .web3_kommandanter import (
        Web3HistorikerKommandant,
        Web3BibliotekarKommandant,
    )
    __all__ = [
        "Web3HistorikerKommandant",
        "Web3BibliotekarKommandant",
    ]
except ImportError:
    __all__ = []

try:
    from .legal_kommandanter import (
        LegalHistorikerKommandant,
        LegalBibliotekarKommandant,
    )
    __all__.extend([
        "LegalHistorikerKommandant",
        "LegalBibliotekarKommandant",
    ])
except ImportError:
    pass  # Legal domain implementations not available
