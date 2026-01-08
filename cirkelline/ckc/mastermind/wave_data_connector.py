"""
CKC MASTERMIND Wave Data Connector (DEL T)
==========================================

Live data stream forbindelse for MASTERMIND.

Forbinder til eksterne datakilder og streamer data ind i
Wave-formatet for WaveCollector.

Komponenter:
- DataSourceType: Type af datakilde
- ConnectionState: Forbindelses-tilstand
- DataSource: Konfiguration af en datakilde
- ConnectionPool: Pool af forbindelser
- StreamBuffer: Buffer for indgående data
- WaveDataConnector: Hoved-connector klasse

Princip: Altid forbundet - altid lyttende.
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set, Type

from .wave_collector import (
    Wave,
    WaveType,
    WaveOrigin,
    WaveIntensity,
    WaveCollector,
    get_wave_collector,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class DataSourceType(Enum):
    """Type af datakilde."""
    DATABASE = "database"           # PostgreSQL, MySQL, etc.
    API = "api"                     # REST API
    WEBSOCKET = "websocket"         # WebSocket stream
    FILE = "file"                   # Fil-baseret (log filer, etc.)
    MESSAGE_QUEUE = "message_queue" # RabbitMQ, Redis, etc.
    WEBHOOK = "webhook"             # Indgående webhooks
    EVENT_STREAM = "event_stream"   # SSE eller lignende
    INTERNAL = "internal"           # Interne system events


class ConnectionState(Enum):
    """Tilstand af forbindelse."""
    DISCONNECTED = "disconnected"   # Ikke forbundet
    CONNECTING = "connecting"       # Forsøger at forbinde
    CONNECTED = "connected"         # Aktivt forbundet
    RECONNECTING = "reconnecting"   # Genforbinder efter fejl
    PAUSED = "paused"               # Midlertidigt pauseret
    FAILED = "failed"               # Permanent fejlet
    CLOSING = "closing"             # Lukker ned


class DataFormat(Enum):
    """Format af indgående data."""
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    BINARY = "binary"
    TEXT = "text"
    MSGPACK = "msgpack"
    PROTOBUF = "protobuf"


class RetryStrategy(Enum):
    """Strategi for genforbindelse."""
    NONE = "none"                   # Ingen retry
    IMMEDIATE = "immediate"         # Øjeblikkelig retry
    LINEAR = "linear"               # Lineær backoff
    EXPONENTIAL = "exponential"     # Eksponentiel backoff
    FIBONACCI = "fibonacci"         # Fibonacci backoff


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DataSource:
    """Konfiguration af en datakilde."""
    source_id: str
    source_type: DataSourceType
    name: str
    description: str = ""

    # Forbindelses-detaljer
    connection_string: str = ""
    host: str = ""
    port: int = 0
    path: str = ""
    credentials: Dict[str, str] = field(default_factory=dict)

    # Stream konfiguration
    data_format: DataFormat = DataFormat.JSON
    batch_size: int = 100
    poll_interval_seconds: float = 1.0

    # Retry konfiguration
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_retries: int = 10
    base_retry_delay_seconds: float = 1.0
    max_retry_delay_seconds: float = 300.0

    # Wave mapping
    default_wave_type: WaveType = WaveType.SIGNAL
    default_wave_origin: WaveOrigin = WaveOrigin.EXTERNAL
    default_intensity: WaveIntensity = WaveIntensity.NORMAL

    # Metadata
    enabled: bool = True
    tags: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "name": self.name,
            "description": self.description,
            "data_format": self.data_format.value,
            "retry_strategy": self.retry_strategy.value,
            "enabled": self.enabled,
            "tags": list(self.tags),
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ConnectionInfo:
    """Information om en aktiv forbindelse."""
    connection_id: str
    source_id: str
    state: ConnectionState = ConnectionState.DISCONNECTED

    # Tidspunkter
    connected_at: Optional[datetime] = None
    last_data_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None

    # Statistik
    total_messages: int = 0
    total_bytes: int = 0
    total_errors: int = 0
    consecutive_errors: int = 0

    # Retry state
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "source_id": self.source_id,
            "state": self.state.value,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "last_data_at": self.last_data_at.isoformat() if self.last_data_at else None,
            "total_messages": self.total_messages,
            "total_errors": self.total_errors
        }


@dataclass
class StreamBuffer:
    """Buffer for indgående data før konvertering til Waves."""
    buffer_id: str
    source_id: str
    max_size: int = 10000

    items: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_flush_at: Optional[datetime] = None

    def add(self, item: Dict[str, Any]) -> bool:
        """Tilføj item til buffer. Returnerer False hvis fuld."""
        if len(self.items) >= self.max_size:
            return False
        self.items.append(item)
        return True

    def flush(self) -> List[Dict[str, Any]]:
        """Tøm buffer og returner alle items."""
        items = self.items.copy()
        self.items = []
        self.last_flush_at = datetime.now()
        return items

    @property
    def size(self) -> int:
        return len(self.items)

    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0

    @property
    def is_full(self) -> bool:
        return len(self.items) >= self.max_size


@dataclass
class DataTransform:
    """Transformation af data før Wave-konvertering."""
    transform_id: str
    name: str
    source_id: str

    # Transform funktion (registreres separat)
    transform_type: str = "identity"  # identity, map, filter, aggregate
    config: Dict[str, Any] = field(default_factory=dict)

    enabled: bool = True
    priority: int = 0  # Lavere = højere prioritet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transform_id": self.transform_id,
            "name": self.name,
            "source_id": self.source_id,
            "transform_type": self.transform_type,
            "enabled": self.enabled,
            "priority": self.priority
        }


@dataclass
class ConnectorStats:
    """Statistik for WaveDataConnector."""
    total_sources: int = 0
    active_connections: int = 0
    total_waves_generated: int = 0
    total_bytes_processed: int = 0
    total_errors: int = 0

    uptime_seconds: float = 0.0
    waves_per_second: float = 0.0
    bytes_per_second: float = 0.0

    started_at: Optional[datetime] = None
    last_wave_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_sources": self.total_sources,
            "active_connections": self.active_connections,
            "total_waves_generated": self.total_waves_generated,
            "total_bytes_processed": self.total_bytes_processed,
            "total_errors": self.total_errors,
            "uptime_seconds": self.uptime_seconds,
            "waves_per_second": self.waves_per_second,
            "started_at": self.started_at.isoformat() if self.started_at else None
        }


# =============================================================================
# ABSTRACT BASE: DATA ADAPTER
# =============================================================================

class DataAdapter(ABC):
    """Abstrakt base klasse for data adaptere."""

    @abstractmethod
    async def connect(self) -> bool:
        """Etabler forbindelse til datakilden."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Afbryd forbindelse."""
        pass

    @abstractmethod
    async def read(self) -> AsyncIterator[Dict[str, Any]]:
        """Læs data fra kilden som async iterator."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Tjek om forbindelsen er sund."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Er adapteren forbundet?"""
        pass


# =============================================================================
# CONCRETE ADAPTERS
# =============================================================================

class InternalEventAdapter(DataAdapter):
    """Adapter for interne system events."""

    def __init__(self, source: DataSource):
        self.source = source
        self._connected = False
        self._event_queue: asyncio.Queue = asyncio.Queue()

    async def connect(self) -> bool:
        self._connected = True
        logger.info(f"InternalEventAdapter connected: {self.source.name}")
        return True

    async def disconnect(self) -> None:
        self._connected = False
        logger.info(f"InternalEventAdapter disconnected: {self.source.name}")

    async def read(self) -> AsyncIterator[Dict[str, Any]]:
        while self._connected:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=self.source.poll_interval_seconds
                )
                yield event
            except asyncio.TimeoutError:
                continue

    async def health_check(self) -> bool:
        return self._connected

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def emit_event(self, event: Dict[str, Any]) -> None:
        """Emit et internt event."""
        if self._connected:
            await self._event_queue.put(event)


class WebhookAdapter(DataAdapter):
    """Adapter for indgående webhooks."""

    def __init__(self, source: DataSource):
        self.source = source
        self._connected = False
        self._webhook_queue: asyncio.Queue = asyncio.Queue()

    async def connect(self) -> bool:
        self._connected = True
        logger.info(f"WebhookAdapter connected: {self.source.name}")
        return True

    async def disconnect(self) -> None:
        self._connected = False
        logger.info(f"WebhookAdapter disconnected: {self.source.name}")

    async def read(self) -> AsyncIterator[Dict[str, Any]]:
        while self._connected:
            try:
                webhook_data = await asyncio.wait_for(
                    self._webhook_queue.get(),
                    timeout=self.source.poll_interval_seconds
                )
                yield webhook_data
            except asyncio.TimeoutError:
                continue

    async def health_check(self) -> bool:
        return self._connected

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def receive_webhook(self, data: Dict[str, Any]) -> None:
        """Modtag webhook data."""
        if self._connected:
            await self._webhook_queue.put(data)


class PollingAdapter(DataAdapter):
    """Generic polling adapter for APIs og databases."""

    def __init__(
        self,
        source: DataSource,
        poll_function: Optional[Callable[[], Any]] = None
    ):
        self.source = source
        self._connected = False
        self._poll_function = poll_function or self._default_poll

    async def _default_poll(self) -> List[Dict[str, Any]]:
        """Default poll funktion - returnerer tom liste."""
        return []

    async def connect(self) -> bool:
        self._connected = True
        logger.info(f"PollingAdapter connected: {self.source.name}")
        return True

    async def disconnect(self) -> None:
        self._connected = False
        logger.info(f"PollingAdapter disconnected: {self.source.name}")

    async def read(self) -> AsyncIterator[Dict[str, Any]]:
        while self._connected:
            try:
                if asyncio.iscoroutinefunction(self._poll_function):
                    results = await self._poll_function()
                else:
                    results = self._poll_function()

                if results:
                    for item in results:
                        yield item

                await asyncio.sleep(self.source.poll_interval_seconds)
            except Exception as e:
                logger.error(f"Poll error for {self.source.name}: {e}")
                await asyncio.sleep(self.source.poll_interval_seconds)

    async def health_check(self) -> bool:
        return self._connected

    @property
    def is_connected(self) -> bool:
        return self._connected


# =============================================================================
# WAVE DATA CONNECTOR
# =============================================================================

class WaveDataConnector:
    """
    Central connector til live data streams.

    Forbinder til multiple datakilder og transformerer data til Waves
    for WaveCollector.
    """

    def __init__(
        self,
        wave_collector: Optional[WaveCollector] = None,
        auto_connect: bool = True,
        buffer_size: int = 10000
    ):
        self._wave_collector = wave_collector
        self._auto_connect = auto_connect
        self._buffer_size = buffer_size

        # Sources og connections
        self._sources: Dict[str, DataSource] = {}
        self._adapters: Dict[str, DataAdapter] = {}
        self._connections: Dict[str, ConnectionInfo] = {}
        self._buffers: Dict[str, StreamBuffer] = {}
        self._transforms: Dict[str, List[DataTransform]] = {}

        # State
        self._running = False
        self._connector_task: Optional[asyncio.Task] = None
        self._source_tasks: Dict[str, asyncio.Task] = {}

        # Statistik
        self._stats = ConnectorStats()

        # Callbacks
        self._on_wave_callbacks: List[Callable[[Wave], None]] = []
        self._on_error_callbacks: List[Callable[[str, Exception], None]] = []

        logger.info("WaveDataConnector initialized")

    # =========================================================================
    # SOURCE MANAGEMENT
    # =========================================================================

    def register_source(
        self,
        source: DataSource,
        adapter: Optional[DataAdapter] = None
    ) -> str:
        """Registrer en datakilde."""
        self._sources[source.source_id] = source

        # Opret adapter hvis ikke givet
        if adapter:
            self._adapters[source.source_id] = adapter
        else:
            self._adapters[source.source_id] = self._create_default_adapter(source)

        # Opret buffer
        self._buffers[source.source_id] = StreamBuffer(
            buffer_id=f"buf_{secrets.token_hex(8)}",
            source_id=source.source_id,
            max_size=self._buffer_size
        )

        # Opret connection info
        self._connections[source.source_id] = ConnectionInfo(
            connection_id=f"conn_{secrets.token_hex(8)}",
            source_id=source.source_id
        )

        # Initialiser transforms liste
        self._transforms[source.source_id] = []

        # Opdater stats
        self._stats.total_sources += 1

        logger.info(f"Source registered: {source.name} ({source.source_id})")

        # Auto-connect hvis kørende
        if self._running and source.enabled and self._auto_connect:
            asyncio.create_task(self._connect_source(source.source_id))

        return source.source_id

    def _create_default_adapter(self, source: DataSource) -> DataAdapter:
        """Opret default adapter baseret på source type."""
        if source.source_type == DataSourceType.INTERNAL:
            return InternalEventAdapter(source)
        elif source.source_type == DataSourceType.WEBHOOK:
            return WebhookAdapter(source)
        else:
            return PollingAdapter(source)

    def unregister_source(self, source_id: str) -> bool:
        """Fjern en datakilde."""
        if source_id not in self._sources:
            return False

        # Stop source task hvis kørende
        if source_id in self._source_tasks:
            self._source_tasks[source_id].cancel()
            del self._source_tasks[source_id]

        # Cleanup
        del self._sources[source_id]
        del self._adapters[source_id]
        del self._connections[source_id]
        del self._buffers[source_id]
        if source_id in self._transforms:
            del self._transforms[source_id]

        self._stats.total_sources -= 1

        logger.info(f"Source unregistered: {source_id}")
        return True

    def get_source(self, source_id: str) -> Optional[DataSource]:
        """Hent en datakilde."""
        return self._sources.get(source_id)

    def list_sources(self) -> List[DataSource]:
        """List alle datakilder."""
        return list(self._sources.values())

    # =========================================================================
    # CONNECTION MANAGEMENT
    # =========================================================================

    async def _connect_source(self, source_id: str) -> bool:
        """Forbind til en specifik kilde."""
        if source_id not in self._sources:
            return False

        source = self._sources[source_id]
        adapter = self._adapters[source_id]
        conn_info = self._connections[source_id]

        conn_info.state = ConnectionState.CONNECTING

        try:
            success = await adapter.connect()
            if success:
                conn_info.state = ConnectionState.CONNECTED
                conn_info.connected_at = datetime.now()
                conn_info.consecutive_errors = 0
                self._stats.active_connections += 1

                # Start source processing task
                self._source_tasks[source_id] = asyncio.create_task(
                    self._process_source(source_id)
                )

                logger.info(f"Connected to source: {source.name}")
                return True
            else:
                conn_info.state = ConnectionState.FAILED
                return False

        except Exception as e:
            logger.error(f"Connection failed for {source.name}: {e}")
            conn_info.state = ConnectionState.FAILED
            conn_info.last_error_at = datetime.now()
            conn_info.total_errors += 1
            await self._handle_connection_error(source_id, e)
            return False

    async def _disconnect_source(self, source_id: str) -> None:
        """Afbryd forbindelse til en kilde."""
        if source_id not in self._adapters:
            return

        # Cancel source task
        if source_id in self._source_tasks:
            self._source_tasks[source_id].cancel()
            try:
                await self._source_tasks[source_id]
            except asyncio.CancelledError:
                pass
            del self._source_tasks[source_id]

        # Disconnect adapter
        adapter = self._adapters[source_id]
        await adapter.disconnect()

        # Update connection info
        conn_info = self._connections[source_id]
        conn_info.state = ConnectionState.DISCONNECTED
        self._stats.active_connections = max(0, self._stats.active_connections - 1)

        logger.info(f"Disconnected from source: {source_id}")

    async def _handle_connection_error(
        self,
        source_id: str,
        error: Exception
    ) -> None:
        """Håndter forbindelsesfejl med retry."""
        source = self._sources.get(source_id)
        conn_info = self._connections.get(source_id)

        if not source or not conn_info:
            return

        conn_info.consecutive_errors += 1
        conn_info.total_errors += 1
        self._stats.total_errors += 1

        # Notify callbacks
        for callback in self._on_error_callbacks:
            try:
                callback(source_id, error)
            except Exception as e:
                logger.error(f"Error callback failed: {e}")

        # Check retry
        if source.retry_strategy == RetryStrategy.NONE:
            conn_info.state = ConnectionState.FAILED
            return

        if conn_info.retry_count >= source.max_retries:
            conn_info.state = ConnectionState.FAILED
            logger.error(f"Max retries exceeded for {source.name}")
            return

        # Calculate retry delay
        delay = self._calculate_retry_delay(source, conn_info.retry_count)
        conn_info.retry_count += 1
        conn_info.next_retry_at = datetime.now() + timedelta(seconds=delay)
        conn_info.state = ConnectionState.RECONNECTING

        logger.info(f"Retrying {source.name} in {delay:.1f}s (attempt {conn_info.retry_count})")

        # Schedule retry
        await asyncio.sleep(delay)
        if self._running and conn_info.state == ConnectionState.RECONNECTING:
            await self._connect_source(source_id)

    def _calculate_retry_delay(self, source: DataSource, retry_count: int) -> float:
        """Beregn retry delay baseret på strategi."""
        base = source.base_retry_delay_seconds
        max_delay = source.max_retry_delay_seconds

        if source.retry_strategy == RetryStrategy.IMMEDIATE:
            return 0.0
        elif source.retry_strategy == RetryStrategy.LINEAR:
            delay = base * (retry_count + 1)
        elif source.retry_strategy == RetryStrategy.EXPONENTIAL:
            delay = base * (2 ** retry_count)
        elif source.retry_strategy == RetryStrategy.FIBONACCI:
            # Fibonacci sequence
            a, b = base, base
            for _ in range(retry_count):
                a, b = b, a + b
            delay = b
        else:
            delay = base

        return min(delay, max_delay)

    # =========================================================================
    # DATA PROCESSING
    # =========================================================================

    async def _process_source(self, source_id: str) -> None:
        """Process data fra en kilde."""
        source = self._sources[source_id]
        adapter = self._adapters[source_id]
        conn_info = self._connections[source_id]
        buffer = self._buffers[source_id]

        try:
            async for data in adapter.read():
                if not self._running:
                    break

                # Update stats
                conn_info.last_data_at = datetime.now()
                conn_info.total_messages += 1

                # Transform data
                transformed = await self._apply_transforms(source_id, data)
                if transformed is None:
                    continue

                # Convert to Wave
                wave = self._data_to_wave(source, transformed)

                # Send to collector
                await self._emit_wave(wave)

        except asyncio.CancelledError:
            logger.debug(f"Source processing cancelled: {source_id}")
        except Exception as e:
            logger.error(f"Source processing error for {source_id}: {e}")
            conn_info.last_error_at = datetime.now()
            await self._handle_connection_error(source_id, e)

    async def _apply_transforms(
        self,
        source_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Anvend transforms på data."""
        transforms = self._transforms.get(source_id, [])
        result = data

        for transform in sorted(transforms, key=lambda t: t.priority):
            if not transform.enabled:
                continue

            if transform.transform_type == "filter":
                # Filter: returner None hvis filtreret ud
                filter_field = transform.config.get("field")
                filter_value = transform.config.get("value")
                if filter_field and result.get(filter_field) != filter_value:
                    return None

            elif transform.transform_type == "map":
                # Map: omdøb felter
                mappings = transform.config.get("mappings", {})
                for old_key, new_key in mappings.items():
                    if old_key in result:
                        result[new_key] = result.pop(old_key)

        return result

    def _data_to_wave(self, source: DataSource, data: Dict[str, Any]) -> Wave:
        """Konverter data til Wave."""
        # Extract wave type fra data eller brug default
        wave_type = WaveType(data.get("wave_type", source.default_wave_type.value))
        origin = WaveOrigin(data.get("origin", source.default_wave_origin.value))
        intensity = WaveIntensity(data.get("intensity", source.default_intensity.value))

        return Wave(
            wave_id=f"wave_{secrets.token_hex(12)}",
            wave_type=wave_type,
            origin=origin,
            source_id=source.source_id,
            content=data.get("content", data),
            intensity=intensity,
            context=data.get("context", {}),
            tags=set(data.get("tags", [])) | source.tags
        )

    async def _emit_wave(self, wave: Wave) -> None:
        """Send wave til collector og callbacks."""
        # Send til WaveCollector
        if self._wave_collector:
            await self._wave_collector.collect(wave)

        # Update stats
        self._stats.total_waves_generated += 1
        self._stats.last_wave_at = datetime.now()

        # Notify callbacks
        for callback in self._on_wave_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(wave)
                else:
                    callback(wave)
            except Exception as e:
                logger.error(f"Wave callback error: {e}")

    # =========================================================================
    # TRANSFORM MANAGEMENT
    # =========================================================================

    def add_transform(self, transform: DataTransform) -> str:
        """Tilføj en transform til en kilde."""
        source_id = transform.source_id
        if source_id not in self._transforms:
            self._transforms[source_id] = []

        self._transforms[source_id].append(transform)
        logger.debug(f"Transform added: {transform.name} for {source_id}")
        return transform.transform_id

    def remove_transform(self, source_id: str, transform_id: str) -> bool:
        """Fjern en transform."""
        if source_id not in self._transforms:
            return False

        transforms = self._transforms[source_id]
        for i, t in enumerate(transforms):
            if t.transform_id == transform_id:
                del transforms[i]
                return True
        return False

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    async def start(self) -> None:
        """Start connector og alle forbindelser."""
        if self._running:
            logger.warning("WaveDataConnector already running")
            return

        self._running = True
        self._stats.started_at = datetime.now()

        # Get wave collector hvis ikke sat
        if not self._wave_collector:
            self._wave_collector = get_wave_collector()

        # Connect til alle enabled sources
        for source_id, source in self._sources.items():
            if source.enabled:
                await self._connect_source(source_id)

        logger.info("WaveDataConnector started")

    async def stop(self) -> None:
        """Stop connector og alle forbindelser."""
        if not self._running:
            return

        self._running = False

        # Disconnect alle sources
        for source_id in list(self._source_tasks.keys()):
            await self._disconnect_source(source_id)

        # Update stats
        if self._stats.started_at:
            self._stats.uptime_seconds = (
                datetime.now() - self._stats.started_at
            ).total_seconds()

        logger.info("WaveDataConnector stopped")

    # =========================================================================
    # CALLBACKS
    # =========================================================================

    def on_wave(self, callback: Callable[[Wave], None]) -> None:
        """Registrer callback for nye waves."""
        self._on_wave_callbacks.append(callback)

    def on_error(self, callback: Callable[[str, Exception], None]) -> None:
        """Registrer callback for fejl."""
        self._on_error_callbacks.append(callback)

    # =========================================================================
    # STATUS & STATS
    # =========================================================================

    def get_stats(self) -> ConnectorStats:
        """Hent connector statistik."""
        # Update uptime
        if self._stats.started_at and self._running:
            self._stats.uptime_seconds = (
                datetime.now() - self._stats.started_at
            ).total_seconds()

            if self._stats.uptime_seconds > 0:
                self._stats.waves_per_second = (
                    self._stats.total_waves_generated / self._stats.uptime_seconds
                )

        return self._stats

    def get_connection_status(self, source_id: str) -> Optional[ConnectionInfo]:
        """Hent forbindelsesstatus for en kilde."""
        return self._connections.get(source_id)

    def get_all_connection_status(self) -> Dict[str, ConnectionInfo]:
        """Hent forbindelsesstatus for alle kilder."""
        return self._connections.copy()

    @property
    def is_running(self) -> bool:
        """Er connector kørende?"""
        return self._running

    @property
    def active_connections(self) -> int:
        """Antal aktive forbindelser."""
        return self._stats.active_connections


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

_connector_instance: Optional[WaveDataConnector] = None


def create_wave_data_connector(
    wave_collector: Optional[WaveCollector] = None,
    **kwargs
) -> WaveDataConnector:
    """Opret ny WaveDataConnector instans."""
    return WaveDataConnector(wave_collector=wave_collector, **kwargs)


def get_wave_data_connector() -> Optional[WaveDataConnector]:
    """Hent global WaveDataConnector instans."""
    return _connector_instance


def set_wave_data_connector(connector: WaveDataConnector) -> None:
    """Sæt global WaveDataConnector instans."""
    global _connector_instance
    _connector_instance = connector


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_internal_source(
    name: str,
    description: str = "",
    tags: Optional[Set[str]] = None
) -> DataSource:
    """Opret en intern event source."""
    return DataSource(
        source_id=f"internal_{secrets.token_hex(8)}",
        source_type=DataSourceType.INTERNAL,
        name=name,
        description=description,
        default_wave_type=WaveType.SIGNAL,
        default_wave_origin=WaveOrigin.SYSTEM,
        tags=tags or set()
    )


def create_webhook_source(
    name: str,
    path: str,
    description: str = "",
    tags: Optional[Set[str]] = None
) -> DataSource:
    """Opret en webhook source."""
    return DataSource(
        source_id=f"webhook_{secrets.token_hex(8)}",
        source_type=DataSourceType.WEBHOOK,
        name=name,
        path=path,
        description=description,
        default_wave_type=WaveType.SIGNAL,
        default_wave_origin=WaveOrigin.EXTERNAL,
        tags=tags or set()
    )


def create_api_source(
    name: str,
    host: str,
    path: str,
    poll_interval: float = 60.0,
    description: str = "",
    tags: Optional[Set[str]] = None
) -> DataSource:
    """Opret en API polling source."""
    return DataSource(
        source_id=f"api_{secrets.token_hex(8)}",
        source_type=DataSourceType.API,
        name=name,
        host=host,
        path=path,
        poll_interval_seconds=poll_interval,
        description=description,
        default_wave_type=WaveType.OBSERVATION,
        default_wave_origin=WaveOrigin.EXTERNAL,
        tags=tags or set()
    )
