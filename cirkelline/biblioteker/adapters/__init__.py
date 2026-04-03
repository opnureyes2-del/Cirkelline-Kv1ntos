"""
Multi-Bibliotek Adapters
========================

FASE 6: Multi-Bibliotek Arkitektur

Konkrete adapters for de forskellige biblioteks-kilder:
    - CosmicLibraryAdapter: Integration med Cosmic Library
    - NotionAdapter: Integration med Notion
    - AgentLearningAdapter: Integration med Agent Learning DB
"""

from .agent_learning_adapter import AgentLearningAdapter
from .cosmic_adapter import CosmicLibraryAdapter
from .notion_adapter import NotionAdapter

__all__ = [
    "CosmicLibraryAdapter",
    "NotionAdapter",
    "AgentLearningAdapter",
]
