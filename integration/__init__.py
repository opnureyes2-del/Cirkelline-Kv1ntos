"""
ELLE Unified Integration System
================================

Provides access to:
- Event Bus (RabbitMQ messaging)
- Cache Manager (Memory + Redis)
- Unified Query API (cross-database queries)
- Master Orchestrator (event routing)
- Cross-DB Sync (INTRO ↔ ELLE)
- File Watcher (real-time file monitoring)
"""

from .event_bus import EventBus
from .cache_manager import MultiLayerCache
from .unified_query_api import UnifiedQueryAPI
from .master_orchestrator import MasterOrchestrator
from .cross_db_sync import CrossDatabaseSync
from .file_watcher import FileWatcher

__all__ = [
    'EventBus',
    'MultiLayerCache',
    'UnifiedQueryAPI',
    'MasterOrchestrator',
    'CrossDatabaseSync',
    'FileWatcher'
]

__version__ = '2.0.0'
__author__ = 'ELLE.md System'
