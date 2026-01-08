"""
CIRKELLINE MASTERMIND - DEL AA: CosmicLibraryBridge
===================================================

Bridge mellem MASTERMIND og Cosmic Library platformen.
Udvider den eksisterende CosmicLibraryConnector med:
- HTTP API kommunikation til ekstern platform
- Realtids event-synkronisering
- MASTERMIND event-integration
- Cross-platform data synkronisering

Forfatter: Cirkelline Team
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class BridgeConnectionState(Enum):
    """Forbindelsestilstand for broen."""

    DISCONNECTED = "disconnected"     # Ikke forbundet
    CONNECTING = "connecting"         # Forbinder
    CONNECTED = "connected"           # Forbundet og aktiv
    RECONNECTING = "reconnecting"     # Genforbinder efter fejl
    ERROR = "error"                   # Fejltilstand


class SyncDirection(Enum):
    """Retning for datasynkronisering."""

    TO_COSMIC = "to_cosmic"           # Fra CKC til Cosmic Library
    FROM_COSMIC = "from_cosmic"       # Fra Cosmic Library til CKC
    BIDIRECTIONAL = "bidirectional"   # Begge retninger


class EventPriority(Enum):
    """Prioritet for platform-events."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AssetSyncStatus(Enum):
    """Status for asset synkronisering."""

    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    CONFLICT = "conflict"
    FAILED = "failed"


class PlatformEventType(Enum):
    """Typer af platform-events."""

    ASSET_CREATED = "asset_created"
    ASSET_UPDATED = "asset_updated"
    ASSET_DELETED = "asset_deleted"
    ASSET_VIEWED = "asset_viewed"
    ASSET_DOWNLOADED = "asset_downloaded"
    SESSION_LINKED = "session_linked"
    SEARCH_PERFORMED = "search_performed"
    COLLECTION_CREATED = "collection_created"
    COLLECTION_UPDATED = "collection_updated"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class BridgeConfig:
    """Konfiguration for Cosmic Library Bridge."""

    # API endpoints
    api_base_url: str = "https://api.cosmic.cirkelline.com"
    api_version: str = "v1"

    # Authentication
    api_key: Optional[str] = None
    jwt_token: Optional[str] = None

    # Connection settings
    connection_timeout_seconds: float = 30.0
    request_timeout_seconds: float = 60.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    # Sync settings
    sync_interval_seconds: float = 30.0
    batch_size: int = 50
    enable_real_time_sync: bool = True

    # Feature flags
    enable_asset_sync: bool = True
    enable_event_streaming: bool = True
    enable_search_integration: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_base_url": self.api_base_url,
            "api_version": self.api_version,
            "has_api_key": self.api_key is not None,
            "has_jwt_token": self.jwt_token is not None,
            "connection_timeout_seconds": self.connection_timeout_seconds,
            "request_timeout_seconds": self.request_timeout_seconds,
            "max_retries": self.max_retries,
            "sync_interval_seconds": self.sync_interval_seconds,
            "batch_size": self.batch_size,
            "enable_real_time_sync": self.enable_real_time_sync,
            "enable_asset_sync": self.enable_asset_sync,
            "enable_event_streaming": self.enable_event_streaming,
            "enable_search_integration": self.enable_search_integration,
        }


@dataclass
class PlatformEvent:
    """En event fra Cosmic Library platformen."""

    event_id: str
    event_type: PlatformEventType
    timestamp: datetime
    priority: EventPriority

    # Event data
    asset_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    source: str = "cosmic_library"
    processed: bool = False
    processing_attempts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "asset_id": self.asset_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "data": self.data,
            "source": self.source,
            "processed": self.processed,
            "processing_attempts": self.processing_attempts,
        }


@dataclass
class SyncTask:
    """En synkroniseringsopgave."""

    task_id: str
    direction: SyncDirection
    asset_ids: List[str]
    status: AssetSyncStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Progress
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0

    # Errors
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "direction": self.direction.value,
            "asset_ids": self.asset_ids,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "failed_items": self.failed_items,
            "errors": self.errors,
        }


@dataclass
class RemoteAsset:
    """Reference til et asset på Cosmic Library platformen."""

    remote_id: str
    local_id: Optional[str]
    remote_url: str
    asset_type: str

    # Metadata
    title: str
    description: str = ""
    tags: List[str] = field(default_factory=list)

    # Sync info
    sync_status: AssetSyncStatus = AssetSyncStatus.PENDING
    last_synced_at: Optional[datetime] = None
    remote_version: int = 1
    local_version: int = 0
    content_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "remote_id": self.remote_id,
            "local_id": self.local_id,
            "remote_url": self.remote_url,
            "asset_type": self.asset_type,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "sync_status": self.sync_status.value,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "remote_version": self.remote_version,
            "local_version": self.local_version,
            "content_hash": self.content_hash,
        }


@dataclass
class SearchRequest:
    """En søgeforespørgsel til Cosmic Library."""

    query: str
    asset_types: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    owner_id: Optional[str] = None
    session_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = "relevance"
    sort_order: str = "desc"
    limit: int = 50
    offset: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "asset_types": self.asset_types,
            "tags": self.tags,
            "owner_id": self.owner_id,
            "session_id": self.session_id,
            "date_from": self.date_from.isoformat() if self.date_from else None,
            "date_to": self.date_to.isoformat() if self.date_to else None,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "limit": self.limit,
            "offset": self.offset,
        }


@dataclass
class SearchResult:
    """Resultat af en søgning i Cosmic Library."""

    request_id: str
    query: str
    total_results: int
    returned_results: int
    assets: List[RemoteAsset]
    search_time_ms: float
    facets: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "query": self.query,
            "total_results": self.total_results,
            "returned_results": self.returned_results,
            "assets": [a.to_dict() for a in self.assets],
            "search_time_ms": self.search_time_ms,
            "facets": self.facets,
        }


@dataclass
class BridgeStats:
    """Statistikker for broen."""

    # Connection
    connection_state: BridgeConnectionState = BridgeConnectionState.DISCONNECTED
    connected_since: Optional[datetime] = None
    total_connections: int = 0
    failed_connections: int = 0

    # Events
    events_received: int = 0
    events_processed: int = 0
    events_failed: int = 0

    # Sync
    sync_tasks_completed: int = 0
    sync_tasks_failed: int = 0
    assets_synced_to_cosmic: int = 0
    assets_synced_from_cosmic: int = 0

    # API calls
    api_calls_total: int = 0
    api_calls_success: int = 0
    api_calls_failed: int = 0
    average_response_time_ms: float = 0.0

    # Search
    searches_performed: int = 0
    average_search_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connection_state": self.connection_state.value,
            "connected_since": self.connected_since.isoformat() if self.connected_since else None,
            "total_connections": self.total_connections,
            "failed_connections": self.failed_connections,
            "events_received": self.events_received,
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "sync_tasks_completed": self.sync_tasks_completed,
            "sync_tasks_failed": self.sync_tasks_failed,
            "assets_synced_to_cosmic": self.assets_synced_to_cosmic,
            "assets_synced_from_cosmic": self.assets_synced_from_cosmic,
            "api_calls_total": self.api_calls_total,
            "api_calls_success": self.api_calls_success,
            "api_calls_failed": self.api_calls_failed,
            "average_response_time_ms": self.average_response_time_ms,
            "searches_performed": self.searches_performed,
            "average_search_time_ms": self.average_search_time_ms,
        }


# ============================================================================
# HTTP CLIENT (Simulated for now)
# ============================================================================

class CosmicAPIClient:
    """
    HTTP client til Cosmic Library API.

    NOTE: Dette er en simuleret implementation.
    I produktion skal denne bruge httpx eller aiohttp.
    """

    def __init__(self, config: BridgeConfig):
        self.config = config
        self._response_times: List[float] = []

    def _get_headers(self) -> Dict[str, str]:
        """Generer HTTP headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CKC-MASTERMIND/1.0",
        }

        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        if self.config.jwt_token:
            headers["Authorization"] = f"Bearer {self.config.jwt_token}"

        return headers

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Simuleret GET request."""
        import time
        start = time.time()

        # Simuler API latency
        await asyncio.sleep(0.05)

        response_time = (time.time() - start) * 1000
        self._response_times.append(response_time)

        # Simuleret response
        return {
            "success": True,
            "data": {},
            "meta": {"response_time_ms": response_time},
        }

    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Simuleret POST request."""
        import time
        start = time.time()

        # Simuler API latency
        await asyncio.sleep(0.1)

        response_time = (time.time() - start) * 1000
        self._response_times.append(response_time)

        # Simuleret response
        return {
            "success": True,
            "data": {"id": f"remote_{uuid4().hex[:12]}"},
            "meta": {"response_time_ms": response_time},
        }

    async def put(
        self,
        endpoint: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Simuleret PUT request."""
        import time
        start = time.time()

        await asyncio.sleep(0.08)

        response_time = (time.time() - start) * 1000
        self._response_times.append(response_time)

        return {
            "success": True,
            "data": data,
            "meta": {"response_time_ms": response_time},
        }

    async def delete(
        self,
        endpoint: str,
    ) -> Dict[str, Any]:
        """Simuleret DELETE request."""
        await asyncio.sleep(0.05)

        return {
            "success": True,
            "data": {},
        }

    def get_average_response_time(self) -> float:
        """Hent gennemsnitlig response tid."""
        if not self._response_times:
            return 0.0
        return sum(self._response_times) / len(self._response_times)


# ============================================================================
# COSMIC LIBRARY BRIDGE
# ============================================================================

class CosmicLibraryBridge:
    """
    Bridge mellem MASTERMIND og Cosmic Library.

    Håndterer:
    - Platform-forbindelse og authentication
    - Asset synkronisering (bidirektionel)
    - Event streaming og processing
    - Søgning i Cosmic Library
    - MASTERMIND session linking
    """

    def __init__(
        self,
        bridge_id: Optional[str] = None,
        config: Optional[BridgeConfig] = None,
    ):
        self.bridge_id = bridge_id or f"bridge_{uuid4().hex[:12]}"
        self.config = config or BridgeConfig()

        # HTTP client
        self._client = CosmicAPIClient(self.config)

        # State
        self._state = BridgeConnectionState.DISCONNECTED
        self._stats = BridgeStats()

        # Event handling
        self._event_queue: asyncio.Queue[PlatformEvent] = asyncio.Queue()
        self._event_listeners: Dict[PlatformEventType, List[Callable]] = {}
        self._global_event_listeners: List[Callable[[PlatformEvent], None]] = []

        # Sync tracking
        self._sync_tasks: Dict[str, SyncTask] = {}
        self._remote_assets: Dict[str, RemoteAsset] = {}
        self._local_to_remote_map: Dict[str, str] = {}  # local_id -> remote_id

        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._is_running = False
        self._lock = asyncio.Lock()

        logger.info(f"CosmicLibraryBridge oprettet: {self.bridge_id}")

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    async def connect(self) -> bool:
        """
        Opret forbindelse til Cosmic Library platformen.

        Returns:
            True hvis forbindelse lykkedes
        """
        if self._state == BridgeConnectionState.CONNECTED:
            return True

        self._state = BridgeConnectionState.CONNECTING
        logger.info("Forbinder til Cosmic Library...")

        try:
            # Simuler authentication og forbindelse
            response = await self._client.get("/health")

            if response.get("success"):
                self._state = BridgeConnectionState.CONNECTED
                self._stats.connection_state = BridgeConnectionState.CONNECTED
                self._stats.connected_since = datetime.now()
                self._stats.total_connections += 1

                self._is_running = True

                # Start background tasks
                if self.config.enable_event_streaming:
                    self._background_tasks.append(
                        asyncio.create_task(self._event_processing_loop())
                    )

                if self.config.enable_real_time_sync:
                    self._background_tasks.append(
                        asyncio.create_task(self._sync_loop())
                    )

                logger.info("Forbundet til Cosmic Library")
                return True

            else:
                self._state = BridgeConnectionState.ERROR
                self._stats.failed_connections += 1
                return False

        except Exception as e:
            logger.error(f"Forbindelsesfejl: {e}")
            self._state = BridgeConnectionState.ERROR
            self._stats.failed_connections += 1
            return False

    async def disconnect(self) -> None:
        """Afbryd forbindelse til Cosmic Library."""
        self._is_running = False

        # Stop background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._background_tasks.clear()
        self._state = BridgeConnectionState.DISCONNECTED
        self._stats.connection_state = BridgeConnectionState.DISCONNECTED

        logger.info("Afbrudt fra Cosmic Library")

    async def _event_processing_loop(self) -> None:
        """Baggrunds-loop til event processing."""
        while self._is_running:
            try:
                # Vent på event med timeout
                try:
                    event = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                await self._process_event(event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Fejl i event processing loop: {e}")

    async def _sync_loop(self) -> None:
        """Baggrunds-loop til periodisk synkronisering."""
        while self._is_running:
            try:
                await asyncio.sleep(self.config.sync_interval_seconds)
                await self._perform_periodic_sync()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Fejl i sync loop: {e}")

    async def _perform_periodic_sync(self) -> None:
        """Udfør periodisk synkronisering."""
        # Implementér periodisk check af ændrede assets
        pass

    # ========================================================================
    # ASSET OPERATIONS
    # ========================================================================

    async def push_asset(
        self,
        local_asset_id: str,
        asset_data: Dict[str, Any],
        file_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Push et lokalt asset til Cosmic Library.

        Args:
            local_asset_id: Lokalt asset ID
            asset_data: Asset metadata
            file_path: Sti til asset fil (optional)

        Returns:
            Remote asset ID hvis succes
        """
        if self._state != BridgeConnectionState.CONNECTED:
            logger.warning("Ikke forbundet - kan ikke pushe asset")
            return None

        try:
            self._stats.api_calls_total += 1

            # Opret på remote
            response = await self._client.post(
                "/api/assets",
                data={
                    "local_id": local_asset_id,
                    "metadata": asset_data,
                    "has_file": file_path is not None,
                }
            )

            if response.get("success"):
                remote_id = response["data"].get("id")

                if remote_id:
                    # Opret remote asset reference
                    remote_asset = RemoteAsset(
                        remote_id=remote_id,
                        local_id=local_asset_id,
                        remote_url=f"{self.config.api_base_url}/assets/{remote_id}",
                        asset_type=asset_data.get("asset_type", "unknown"),
                        title=asset_data.get("title", ""),
                        description=asset_data.get("description", ""),
                        tags=asset_data.get("tags", []),
                        sync_status=AssetSyncStatus.SYNCED,
                        last_synced_at=datetime.now(),
                    )

                    async with self._lock:
                        self._remote_assets[remote_id] = remote_asset
                        self._local_to_remote_map[local_asset_id] = remote_id

                    self._stats.assets_synced_to_cosmic += 1
                    self._stats.api_calls_success += 1

                    # Emit event
                    await self._emit_event(
                        PlatformEventType.ASSET_CREATED,
                        asset_id=remote_id,
                        data={"local_id": local_asset_id},
                    )

                    logger.info(f"Asset pushed: {local_asset_id} -> {remote_id}")
                    return remote_id

            self._stats.api_calls_failed += 1
            return None

        except Exception as e:
            logger.error(f"Fejl ved push af asset: {e}")
            self._stats.api_calls_failed += 1
            return None

    async def pull_asset(
        self,
        remote_asset_id: str,
    ) -> Optional[RemoteAsset]:
        """
        Hent et asset fra Cosmic Library.

        Args:
            remote_asset_id: Remote asset ID

        Returns:
            RemoteAsset hvis fundet
        """
        if self._state != BridgeConnectionState.CONNECTED:
            return None

        try:
            self._stats.api_calls_total += 1

            response = await self._client.get(f"/api/assets/{remote_asset_id}")

            if response.get("success"):
                data = response.get("data", {})

                remote_asset = RemoteAsset(
                    remote_id=remote_asset_id,
                    local_id=data.get("local_id"),
                    remote_url=f"{self.config.api_base_url}/assets/{remote_asset_id}",
                    asset_type=data.get("asset_type", "unknown"),
                    title=data.get("title", ""),
                    description=data.get("description", ""),
                    tags=data.get("tags", []),
                    sync_status=AssetSyncStatus.SYNCED,
                    last_synced_at=datetime.now(),
                    remote_version=data.get("version", 1),
                )

                async with self._lock:
                    self._remote_assets[remote_asset_id] = remote_asset

                self._stats.assets_synced_from_cosmic += 1
                self._stats.api_calls_success += 1

                return remote_asset

            self._stats.api_calls_failed += 1
            return None

        except Exception as e:
            logger.error(f"Fejl ved pull af asset: {e}")
            self._stats.api_calls_failed += 1
            return None

    async def sync_asset(
        self,
        local_asset_id: str,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
    ) -> AssetSyncStatus:
        """
        Synkroniser et specifikt asset.

        Args:
            local_asset_id: Lokalt asset ID
            direction: Synkroniseringsretning

        Returns:
            Sync status efter operation
        """
        remote_id = self._local_to_remote_map.get(local_asset_id)

        if not remote_id and direction in [SyncDirection.BIDIRECTIONAL, SyncDirection.TO_COSMIC]:
            # Asset eksisterer ikke remote - push det
            # Her ville vi hente local asset data og pushe
            logger.info(f"Asset {local_asset_id} findes ikke remote")
            return AssetSyncStatus.PENDING

        if remote_id:
            # Sammenlign versioner og synkroniser
            remote_asset = self._remote_assets.get(remote_id)
            if remote_asset:
                remote_asset.sync_status = AssetSyncStatus.SYNCED
                remote_asset.last_synced_at = datetime.now()
                return AssetSyncStatus.SYNCED

        return AssetSyncStatus.FAILED

    async def create_sync_task(
        self,
        asset_ids: List[str],
        direction: SyncDirection,
    ) -> SyncTask:
        """
        Opret en synkroniseringsopgave for multiple assets.

        Args:
            asset_ids: Liste af asset IDs
            direction: Synkroniseringsretning

        Returns:
            SyncTask
        """
        task = SyncTask(
            task_id=f"sync_{uuid4().hex[:12]}",
            direction=direction,
            asset_ids=asset_ids,
            status=AssetSyncStatus.PENDING,
            created_at=datetime.now(),
            total_items=len(asset_ids),
        )

        async with self._lock:
            self._sync_tasks[task.task_id] = task

        # Start async processing
        asyncio.create_task(self._execute_sync_task(task.task_id))

        return task

    async def _execute_sync_task(self, task_id: str) -> None:
        """Eksekver en sync task."""
        task = self._sync_tasks.get(task_id)
        if not task:
            return

        task.status = AssetSyncStatus.SYNCING
        task.started_at = datetime.now()

        for asset_id in task.asset_ids:
            try:
                status = await self.sync_asset(asset_id, task.direction)
                if status == AssetSyncStatus.SYNCED:
                    task.processed_items += 1
                else:
                    task.failed_items += 1
                    task.errors.append(f"Failed to sync {asset_id}")

            except Exception as e:
                task.failed_items += 1
                task.errors.append(f"Error syncing {asset_id}: {e}")

        task.completed_at = datetime.now()
        task.status = AssetSyncStatus.SYNCED if task.failed_items == 0 else AssetSyncStatus.FAILED

        if task.status == AssetSyncStatus.SYNCED:
            self._stats.sync_tasks_completed += 1
        else:
            self._stats.sync_tasks_failed += 1

    # ========================================================================
    # SEARCH
    # ========================================================================

    async def search(
        self,
        query: str,
        asset_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        limit: int = 50,
    ) -> SearchResult:
        """
        Søg i Cosmic Library.

        Args:
            query: Søgeforespørgsel
            asset_types: Filter på asset typer
            tags: Filter på tags
            session_id: Filter på MASTERMIND session
            limit: Max antal resultater

        Returns:
            SearchResult
        """
        import time
        start_time = time.time()

        request = SearchRequest(
            query=query,
            asset_types=asset_types or [],
            tags=tags or [],
            session_id=session_id,
            limit=limit,
        )

        self._stats.api_calls_total += 1

        try:
            response = await self._client.post(
                "/api/search",
                data=request.to_dict()
            )

            search_time = (time.time() - start_time) * 1000

            if response.get("success"):
                self._stats.api_calls_success += 1
                self._stats.searches_performed += 1

                # Opdater gennemsnitlig søgetid
                n = self._stats.searches_performed
                self._stats.average_search_time_ms = (
                    (self._stats.average_search_time_ms * (n - 1) + search_time) / n
                )

                # Parse resultater (simuleret)
                assets = []
                for i in range(min(5, limit)):  # Simuler 5 resultater
                    assets.append(RemoteAsset(
                        remote_id=f"remote_{uuid4().hex[:8]}",
                        local_id=None,
                        remote_url=f"{self.config.api_base_url}/assets/{i}",
                        asset_type="image",
                        title=f"Resultat for '{query}' #{i+1}",
                        description=f"Fundet via søgning",
                        tags=tags or [],
                    ))

                return SearchResult(
                    request_id=f"search_{uuid4().hex[:8]}",
                    query=query,
                    total_results=5,
                    returned_results=len(assets),
                    assets=assets,
                    search_time_ms=search_time,
                    facets={
                        "asset_types": {"image": 3, "animation": 2},
                        "tags": {t: 1 for t in (tags or [])},
                    },
                )

            self._stats.api_calls_failed += 1

        except Exception as e:
            logger.error(f"Søgefejl: {e}")
            self._stats.api_calls_failed += 1

        # Return empty result on error
        return SearchResult(
            request_id=f"search_{uuid4().hex[:8]}",
            query=query,
            total_results=0,
            returned_results=0,
            assets=[],
            search_time_ms=(time.time() - start_time) * 1000,
        )

    async def search_by_session(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[RemoteAsset]:
        """
        Hent alle assets tilknyttet en MASTERMIND session.

        Args:
            session_id: MASTERMIND session ID
            limit: Max antal resultater

        Returns:
            Liste af RemoteAsset
        """
        result = await self.search(
            query="",
            session_id=session_id,
            limit=limit,
        )
        return result.assets

    # ========================================================================
    # EVENTS
    # ========================================================================

    async def _emit_event(
        self,
        event_type: PlatformEventType,
        asset_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """Emit en platform event."""
        event = PlatformEvent(
            event_id=f"evt_{uuid4().hex[:12]}",
            event_type=event_type,
            timestamp=datetime.now(),
            priority=priority,
            asset_id=asset_id,
            user_id=user_id,
            session_id=session_id,
            data=data or {},
        )

        await self._event_queue.put(event)
        self._stats.events_received += 1

    async def _process_event(self, event: PlatformEvent) -> None:
        """Process en platform event."""
        event.processing_attempts += 1

        try:
            # Call type-specific listeners
            listeners = self._event_listeners.get(event.event_type, [])
            for listener in listeners:
                try:
                    result = listener(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Listener fejl for {event.event_type}: {e}")

            # Call global listeners
            for listener in self._global_event_listeners:
                try:
                    result = listener(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Global listener fejl: {e}")

            event.processed = True
            self._stats.events_processed += 1

        except Exception as e:
            logger.error(f"Event processing fejl: {e}")
            self._stats.events_failed += 1

    def add_event_listener(
        self,
        event_type: PlatformEventType,
        listener: Callable[[PlatformEvent], None],
    ) -> None:
        """Tilføj listener for specifik event type."""
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(listener)

    def add_global_event_listener(
        self,
        listener: Callable[[PlatformEvent], None],
    ) -> None:
        """Tilføj global event listener."""
        self._global_event_listeners.append(listener)

    def remove_event_listener(
        self,
        event_type: PlatformEventType,
        listener: Callable[[PlatformEvent], None],
    ) -> bool:
        """Fjern event listener."""
        if event_type in self._event_listeners:
            try:
                self._event_listeners[event_type].remove(listener)
                return True
            except ValueError:
                pass
        return False

    # ========================================================================
    # SESSION LINKING
    # ========================================================================

    async def link_session(
        self,
        mastermind_session_id: str,
        cosmic_collection_id: Optional[str] = None,
    ) -> bool:
        """
        Link en MASTERMIND session til Cosmic Library.

        Args:
            mastermind_session_id: MASTERMIND session ID
            cosmic_collection_id: Cosmic Library collection ID (opretter ny hvis None)

        Returns:
            True hvis linking lykkedes
        """
        self._stats.api_calls_total += 1

        try:
            response = await self._client.post(
                "/api/sessions/link",
                data={
                    "mastermind_session_id": mastermind_session_id,
                    "collection_id": cosmic_collection_id,
                }
            )

            if response.get("success"):
                self._stats.api_calls_success += 1

                await self._emit_event(
                    PlatformEventType.SESSION_LINKED,
                    session_id=mastermind_session_id,
                    data={"collection_id": cosmic_collection_id},
                )

                logger.info(f"Session linked: {mastermind_session_id}")
                return True

            self._stats.api_calls_failed += 1
            return False

        except Exception as e:
            logger.error(f"Session link fejl: {e}")
            self._stats.api_calls_failed += 1
            return False

    # ========================================================================
    # STATS & STATUS
    # ========================================================================

    async def get_stats(self) -> BridgeStats:
        """Hent bridge statistikker."""
        # Opdater API response time
        self._stats.average_response_time_ms = self._client.get_average_response_time()
        return self._stats

    async def get_status(self) -> Dict[str, Any]:
        """Hent komplet bridge status."""
        stats = await self.get_stats()

        return {
            "bridge_id": self.bridge_id,
            "connection_state": self._state.value,
            "is_running": self._is_running,
            "config": self.config.to_dict(),
            "remote_assets_count": len(self._remote_assets),
            "pending_sync_tasks": sum(
                1 for t in self._sync_tasks.values()
                if t.status == AssetSyncStatus.PENDING
            ),
            "event_queue_size": self._event_queue.qsize(),
            "stats": stats.to_dict(),
        }

    def get_remote_asset(self, remote_id: str) -> Optional[RemoteAsset]:
        """Hent remote asset reference."""
        return self._remote_assets.get(remote_id)

    def get_remote_id_for_local(self, local_id: str) -> Optional[str]:
        """Hent remote ID for et lokalt asset."""
        return self._local_to_remote_map.get(local_id)


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

# Global instance
_bridge_instance: Optional[CosmicLibraryBridge] = None


def create_cosmic_library_bridge(
    bridge_id: Optional[str] = None,
    config: Optional[BridgeConfig] = None,
) -> CosmicLibraryBridge:
    """
    Opret en ny CosmicLibraryBridge.

    Args:
        bridge_id: Unikt ID for broen
        config: Bridge konfiguration

    Returns:
        Ny CosmicLibraryBridge instance
    """
    return CosmicLibraryBridge(
        bridge_id=bridge_id,
        config=config,
    )


def get_cosmic_library_bridge() -> Optional[CosmicLibraryBridge]:
    """Hent global CosmicLibraryBridge instance."""
    return _bridge_instance


def set_cosmic_library_bridge(bridge: CosmicLibraryBridge) -> None:
    """Sæt global CosmicLibraryBridge instance."""
    global _bridge_instance
    _bridge_instance = bridge


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def push_to_cosmic(
    local_asset_id: str,
    asset_data: Dict[str, Any],
) -> Optional[str]:
    """Convenience: Push asset til Cosmic Library via global bridge."""
    bridge = get_cosmic_library_bridge()
    if bridge:
        return await bridge.push_asset(local_asset_id, asset_data)
    return None


async def search_cosmic(
    query: str,
    limit: int = 50,
) -> SearchResult:
    """Convenience: Søg i Cosmic Library via global bridge."""
    bridge = get_cosmic_library_bridge()
    if bridge:
        return await bridge.search(query, limit=limit)

    return SearchResult(
        request_id=f"search_{uuid4().hex[:8]}",
        query=query,
        total_results=0,
        returned_results=0,
        assets=[],
        search_time_ms=0,
    )


# ============================================================================
# MASTERMIND INTEGRATION
# ============================================================================

async def create_mastermind_cosmic_bridge(
    api_key: Optional[str] = None,
    enable_real_time: bool = True,
) -> CosmicLibraryBridge:
    """
    Opret CosmicLibraryBridge konfigureret til MASTERMIND.

    Args:
        api_key: API nøgle til Cosmic Library
        enable_real_time: Aktiver real-time synkronisering

    Returns:
        CosmicLibraryBridge klar til MASTERMIND brug
    """
    config = BridgeConfig(
        api_key=api_key,
        enable_real_time_sync=enable_real_time,
        enable_event_streaming=True,
        sync_interval_seconds=30.0,
    )

    bridge = create_cosmic_library_bridge(
        bridge_id="mastermind_cosmic_bridge",
        config=config,
    )

    set_cosmic_library_bridge(bridge)

    # Connect
    await bridge.connect()

    logger.info("MASTERMIND CosmicLibraryBridge initialiseret")

    return bridge
