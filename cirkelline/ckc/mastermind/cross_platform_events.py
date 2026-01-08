"""
CKC MASTERMIND - Cross Platform Events (DEL AD)
==============================================

Central event distribution system that coordinates events across all platforms.
Aggregates events from Cosmic Library, lib-admin, Frontend SSE, and internal
MASTERMIND components into a unified event stream.

Architecture:
    Platform A ─┐
    Platform B ─┼─> CrossPlatformEventBus ─> Subscribers
    Platform C ─┘         │
                          └─> Event Store (History)

Features:
- Unified event format across all platforms
- Event routing with filters
- Event transformation and enrichment
- Dead letter queue for failed deliveries
- Event replay from history
- Priority-based delivery
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import asyncio
import hashlib
import logging
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class PlatformSource(Enum):
    """Source platforms for events."""
    COSMIC_LIBRARY = "cosmic_library"
    LIB_ADMIN = "lib_admin"
    FRONTEND_SSE = "frontend_sse"
    MASTERMIND = "mastermind"
    THINK_ALOUD = "think_aloud"
    WAVE_DATA = "wave_data"
    RITUAL_SCHEDULER = "ritual_scheduler"
    DECISION_ENGINE = "decision_engine"
    LEARNING_LOOP = "learning_loop"
    EXTERNAL_WEBHOOK = "external_webhook"


class CrossEventType(Enum):
    """Types of cross-platform events."""
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_HEALTH = "system.health"
    SYSTEM_ERROR = "system.error"

    # User events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_ACTION = "user.action"
    USER_PREFERENCE = "user.preference"

    # Content events
    CONTENT_CREATED = "content.created"
    CONTENT_UPDATED = "content.updated"
    CONTENT_DELETED = "content.deleted"
    CONTENT_SYNCED = "content.synced"

    # Agent events
    AGENT_ACTIVATED = "agent.activated"
    AGENT_DEACTIVATED = "agent.deactivated"
    AGENT_TASK_START = "agent.task_start"
    AGENT_TASK_COMPLETE = "agent.task_complete"
    AGENT_THOUGHT = "agent.thought"

    # Decision events
    DECISION_MADE = "decision.made"
    DECISION_ESCALATED = "decision.escalated"
    DECISION_OVERRIDDEN = "decision.overridden"

    # Learning events
    INSIGHT_GENERATED = "insight.generated"
    PATTERN_DETECTED = "pattern.detected"
    KNOWLEDGE_UPDATED = "knowledge.updated"

    # Sync events
    SYNC_STARTED = "sync.started"
    SYNC_COMPLETED = "sync.completed"
    SYNC_FAILED = "sync.failed"

    # Notification events
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_READ = "notification.read"
    ALERT_TRIGGERED = "alert.triggered"

    # Custom events
    CUSTOM = "custom"


class EventPriority(Enum):
    """Priority levels for event delivery."""
    CRITICAL = 0  # Immediate delivery
    HIGH = 1      # Fast delivery
    NORMAL = 2    # Standard delivery
    LOW = 3       # Batch delivery
    BACKGROUND = 4  # When resources available


class DeliveryStatus(Enum):
    """Status of event delivery."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


class SubscriptionFilter(Enum):
    """Filter types for subscriptions."""
    ALL = "all"               # All events
    BY_SOURCE = "by_source"   # Filter by source platform
    BY_TYPE = "by_type"       # Filter by event type
    BY_USER = "by_user"       # Filter by user
    BY_PATTERN = "by_pattern" # Filter by regex pattern
    CUSTOM = "custom"         # Custom filter function


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CrossPlatformEventConfig:
    """Configuration for cross-platform event system."""
    max_history_size: int = 10000
    max_dead_letter_size: int = 1000
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    batch_size: int = 100
    batch_interval_ms: int = 100
    enable_persistence: bool = False
    persistence_path: Optional[str] = None
    enable_compression: bool = True
    max_event_age_hours: int = 24
    cleanup_interval_minutes: int = 30
    enable_metrics: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrossPlatformEvent:
    """A cross-platform event."""
    event_id: str
    event_type: CrossEventType
    source: PlatformSource
    timestamp: datetime
    payload: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ttl_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: CrossEventType,
        source: PlatformSource,
        payload: Dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "CrossPlatformEvent":
        """Create a new cross-platform event."""
        return cls(
            event_id=f"cpe_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            source=source,
            timestamp=datetime.utcnow(),
            payload=payload,
            priority=priority,
            correlation_id=correlation_id,
            user_id=user_id,
            metadata=metadata or {}
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source.value,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ttl_seconds": self.ttl_seconds,
            "metadata": self.metadata
        }

    def get_hash(self) -> str:
        """Get event content hash for deduplication."""
        content = f"{self.event_type.value}:{self.source.value}:{self.payload}"
        return hashlib.md5(content.encode()).hexdigest()[:8]


@dataclass
class EventDelivery:
    """Record of event delivery attempt."""
    delivery_id: str
    event_id: str
    subscriber_id: str
    status: DeliveryStatus
    attempt: int
    timestamp: datetime
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class EventSubscription:
    """A subscription to cross-platform events."""
    subscription_id: str
    subscriber_name: str
    filter_type: SubscriptionFilter
    filter_value: Any  # Depends on filter type
    callback: Callable[[CrossPlatformEvent], Any]
    priority: EventPriority = EventPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True
    events_received: int = 0
    last_event_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches(self, event: CrossPlatformEvent) -> bool:
        """Check if event matches this subscription's filter."""
        if self.filter_type == SubscriptionFilter.ALL:
            return True
        elif self.filter_type == SubscriptionFilter.BY_SOURCE:
            return event.source == self.filter_value
        elif self.filter_type == SubscriptionFilter.BY_TYPE:
            if isinstance(self.filter_value, list):
                return event.event_type in self.filter_value
            return event.event_type == self.filter_value
        elif self.filter_type == SubscriptionFilter.BY_USER:
            return event.user_id == self.filter_value
        elif self.filter_type == SubscriptionFilter.CUSTOM:
            if callable(self.filter_value):
                return self.filter_value(event)
        return False


@dataclass
class EventRoute:
    """A route for transforming and forwarding events."""
    route_id: str
    name: str
    source_filter: SubscriptionFilter
    source_value: Any
    target_platform: PlatformSource
    transformer: Optional[Callable[[CrossPlatformEvent], CrossPlatformEvent]] = None
    enabled: bool = True
    events_routed: int = 0


@dataclass
class EventMetrics:
    """Metrics for cross-platform events."""
    total_events: int = 0
    events_by_source: Dict[str, int] = field(default_factory=dict)
    events_by_type: Dict[str, int] = field(default_factory=dict)
    deliveries_success: int = 0
    deliveries_failed: int = 0
    dead_letter_count: int = 0
    avg_delivery_time_ms: float = 0.0
    active_subscriptions: int = 0
    last_event_at: Optional[datetime] = None
    uptime_seconds: float = 0.0


# =============================================================================
# MAIN CLASS: CrossPlatformEventBus
# =============================================================================

class CrossPlatformEventBus:
    """
    Central event bus for cross-platform event distribution.

    Aggregates events from all platforms and distributes them
    to subscribers based on filters and priorities.
    """

    def __init__(self, config: Optional[CrossPlatformEventConfig] = None):
        self.config = config or CrossPlatformEventConfig()

        # Event storage
        self._events: List[CrossPlatformEvent] = []
        self._dead_letter: List[Tuple[CrossPlatformEvent, str]] = []

        # Subscriptions
        self._subscriptions: Dict[str, EventSubscription] = {}

        # Routes
        self._routes: Dict[str, EventRoute] = {}

        # Delivery tracking
        self._deliveries: List[EventDelivery] = []

        # Metrics
        self._metrics = EventMetrics()
        self._start_time = datetime.utcnow()

        # Background tasks
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        self._batch_task: Optional[asyncio.Task] = None

        # Event batch queue
        self._batch_queue: List[CrossPlatformEvent] = []
        self._batch_lock = asyncio.Lock()

        # Platform adapters
        self._platform_adapters: Dict[PlatformSource, Callable] = {}

        logger.info("CrossPlatformEventBus initialized")

    async def start(self) -> None:
        """Start the event bus."""
        self._running = True
        self._start_time = datetime.utcnow()

        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._batch_task = asyncio.create_task(self._batch_processor())

        logger.info("CrossPlatformEventBus started")

    async def stop(self) -> None:
        """Stop the event bus."""
        self._running = False

        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass

        # Process remaining batch
        if self._batch_queue:
            await self._flush_batch()

        logger.info("CrossPlatformEventBus stopped")

    # ========== Event Publishing ==========

    async def publish(
        self,
        event: CrossPlatformEvent,
        immediate: bool = False
    ) -> bool:
        """
        Publish an event to the bus.

        Args:
            event: Event to publish
            immediate: If True, deliver immediately (skip batch)

        Returns:
            True if published successfully
        """
        try:
            # Store event
            self._events.append(event)
            self._trim_history()

            # Update metrics
            self._metrics.total_events += 1
            source_key = event.source.value
            self._metrics.events_by_source[source_key] = \
                self._metrics.events_by_source.get(source_key, 0) + 1
            type_key = event.event_type.value
            self._metrics.events_by_type[type_key] = \
                self._metrics.events_by_type.get(type_key, 0) + 1
            self._metrics.last_event_at = event.timestamp

            # Deliver
            if immediate or event.priority in [EventPriority.CRITICAL, EventPriority.HIGH]:
                await self._deliver_event(event)
            else:
                async with self._batch_lock:
                    self._batch_queue.append(event)

            return True

        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            return False

    async def publish_many(
        self,
        events: List[CrossPlatformEvent]
    ) -> int:
        """
        Publish multiple events.

        Returns:
            Number of events published successfully
        """
        success_count = 0
        for event in events:
            if await self.publish(event):
                success_count += 1
        return success_count

    # ========== Subscriptions ==========

    def subscribe(
        self,
        subscriber_name: str,
        callback: Callable[[CrossPlatformEvent], Any],
        filter_type: SubscriptionFilter = SubscriptionFilter.ALL,
        filter_value: Any = None,
        priority: EventPriority = EventPriority.NORMAL
    ) -> str:
        """
        Subscribe to events.

        Args:
            subscriber_name: Name of the subscriber
            callback: Function to call when event matches
            filter_type: Type of filter to apply
            filter_value: Value for the filter
            priority: Delivery priority

        Returns:
            Subscription ID
        """
        subscription_id = f"sub_{uuid.uuid4().hex[:8]}"

        subscription = EventSubscription(
            subscription_id=subscription_id,
            subscriber_name=subscriber_name,
            filter_type=filter_type,
            filter_value=filter_value,
            callback=callback,
            priority=priority
        )

        self._subscriptions[subscription_id] = subscription
        self._metrics.active_subscriptions = len(self._subscriptions)

        logger.info(f"New subscription: {subscriber_name} ({subscription_id})")
        return subscription_id

    def subscribe_to_source(
        self,
        subscriber_name: str,
        source: PlatformSource,
        callback: Callable[[CrossPlatformEvent], Any]
    ) -> str:
        """Subscribe to events from a specific source."""
        return self.subscribe(
            subscriber_name=subscriber_name,
            callback=callback,
            filter_type=SubscriptionFilter.BY_SOURCE,
            filter_value=source
        )

    def subscribe_to_types(
        self,
        subscriber_name: str,
        event_types: List[CrossEventType],
        callback: Callable[[CrossPlatformEvent], Any]
    ) -> str:
        """Subscribe to specific event types."""
        return self.subscribe(
            subscriber_name=subscriber_name,
            callback=callback,
            filter_type=SubscriptionFilter.BY_TYPE,
            filter_value=event_types
        )

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            self._metrics.active_subscriptions = len(self._subscriptions)
            logger.info(f"Unsubscribed: {subscription_id}")
            return True
        return False

    # ========== Routes ==========

    def add_route(
        self,
        name: str,
        source_filter: SubscriptionFilter,
        source_value: Any,
        target_platform: PlatformSource,
        transformer: Optional[Callable] = None
    ) -> str:
        """
        Add a route for event forwarding.

        Routes automatically forward matching events to target platforms.
        """
        route_id = f"route_{uuid.uuid4().hex[:8]}"

        route = EventRoute(
            route_id=route_id,
            name=name,
            source_filter=source_filter,
            source_value=source_value,
            target_platform=target_platform,
            transformer=transformer
        )

        self._routes[route_id] = route
        logger.info(f"Route added: {name} -> {target_platform.value}")
        return route_id

    def remove_route(self, route_id: str) -> bool:
        """Remove a route."""
        if route_id in self._routes:
            del self._routes[route_id]
            return True
        return False

    # ========== Platform Adapters ==========

    def register_platform_adapter(
        self,
        platform: PlatformSource,
        adapter: Callable[[CrossPlatformEvent], Any]
    ) -> None:
        """
        Register an adapter for a platform.

        Adapters are called when events are routed to a platform.
        """
        self._platform_adapters[platform] = adapter
        logger.info(f"Platform adapter registered: {platform.value}")

    # ========== Event Delivery ==========

    async def _deliver_event(self, event: CrossPlatformEvent) -> None:
        """Deliver event to all matching subscribers."""
        for subscription in self._subscriptions.values():
            if not subscription.active:
                continue

            if not subscription.matches(event):
                continue

            delivery = await self._deliver_to_subscriber(event, subscription)
            self._deliveries.append(delivery)

    async def _deliver_to_subscriber(
        self,
        event: CrossPlatformEvent,
        subscription: EventSubscription
    ) -> EventDelivery:
        """Deliver event to a single subscriber with retry."""
        delivery_id = f"del_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()

        for attempt in range(self.config.retry_attempts):
            try:
                callback = subscription.callback
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)

                # Success
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                subscription.events_received += 1
                subscription.last_event_at = datetime.utcnow()
                self._metrics.deliveries_success += 1

                # Update average delivery time
                total = self._metrics.deliveries_success + self._metrics.deliveries_failed
                self._metrics.avg_delivery_time_ms = (
                    (self._metrics.avg_delivery_time_ms * (total - 1) + duration) / total
                )

                return EventDelivery(
                    delivery_id=delivery_id,
                    event_id=event.event_id,
                    subscriber_id=subscription.subscription_id,
                    status=DeliveryStatus.DELIVERED,
                    attempt=attempt + 1,
                    timestamp=datetime.utcnow(),
                    duration_ms=duration
                )

            except Exception as e:
                logger.warning(
                    f"Delivery failed (attempt {attempt + 1}): "
                    f"{event.event_id} -> {subscription.subscriber_name}: {e}"
                )

                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(
                        self.config.retry_delay_seconds * (attempt + 1)
                    )

        # All attempts failed
        self._metrics.deliveries_failed += 1
        self._add_to_dead_letter(event, f"Delivery failed after {self.config.retry_attempts} attempts")

        return EventDelivery(
            delivery_id=delivery_id,
            event_id=event.event_id,
            subscriber_id=subscription.subscription_id,
            status=DeliveryStatus.DEAD_LETTER,
            attempt=self.config.retry_attempts,
            timestamp=datetime.utcnow(),
            error="Max retries exceeded"
        )

    def _add_to_dead_letter(self, event: CrossPlatformEvent, reason: str) -> None:
        """Add event to dead letter queue."""
        self._dead_letter.append((event, reason))
        self._metrics.dead_letter_count = len(self._dead_letter)

        # Trim dead letter queue
        while len(self._dead_letter) > self.config.max_dead_letter_size:
            self._dead_letter.pop(0)

    # ========== Batch Processing ==========

    async def _batch_processor(self) -> None:
        """Process batched events."""
        while self._running:
            try:
                await asyncio.sleep(self.config.batch_interval_ms / 1000)
                await self._flush_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Batch processor error: {e}")

    async def _flush_batch(self) -> None:
        """Flush the batch queue."""
        async with self._batch_lock:
            if not self._batch_queue:
                return

            batch = self._batch_queue[:self.config.batch_size]
            self._batch_queue = self._batch_queue[self.config.batch_size:]

        for event in batch:
            await self._deliver_event(event)

    # ========== History & Replay ==========

    def get_events(
        self,
        source: Optional[PlatformSource] = None,
        event_type: Optional[CrossEventType] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[CrossPlatformEvent]:
        """Get events from history with optional filters."""
        events = self._events

        if source:
            events = [e for e in events if e.source == source]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if since:
            events = [e for e in events if e.timestamp >= since]

        return events[-limit:]

    async def replay_events(
        self,
        events: List[CrossPlatformEvent],
        target_subscription: str
    ) -> int:
        """
        Replay events to a specific subscriber.

        Returns:
            Number of events replayed
        """
        if target_subscription not in self._subscriptions:
            return 0

        subscription = self._subscriptions[target_subscription]
        count = 0

        for event in events:
            try:
                callback = subscription.callback
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
                count += 1
            except Exception as e:
                logger.error(f"Replay error for {event.event_id}: {e}")

        return count

    # ========== Cleanup ==========

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of old events."""
        while self._running:
            try:
                await asyncio.sleep(self.config.cleanup_interval_minutes * 60)
                self._cleanup_old_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    def _cleanup_old_events(self) -> None:
        """Remove events older than max age."""
        cutoff = datetime.utcnow() - timedelta(
            hours=self.config.max_event_age_hours
        )

        original_count = len(self._events)
        self._events = [e for e in self._events if e.timestamp >= cutoff]
        removed = original_count - len(self._events)

        if removed > 0:
            logger.info(f"Cleaned up {removed} old events")

    def _trim_history(self) -> None:
        """Trim event history to max size."""
        while len(self._events) > self.config.max_history_size:
            self._events.pop(0)

    # ========== Metrics ==========

    def get_metrics(self) -> EventMetrics:
        """Get current metrics."""
        self._metrics.uptime_seconds = (
            datetime.utcnow() - self._start_time
        ).total_seconds()
        return self._metrics

    def get_dead_letter_queue(self) -> List[Tuple[CrossPlatformEvent, str]]:
        """Get dead letter queue contents."""
        return list(self._dead_letter)

    async def retry_dead_letter(self) -> int:
        """
        Retry all events in dead letter queue.

        Returns:
            Number of events successfully delivered
        """
        if not self._dead_letter:
            return 0

        success_count = 0
        retry_list = list(self._dead_letter)
        self._dead_letter.clear()
        self._metrics.dead_letter_count = 0

        for event, _ in retry_list:
            if await self.publish(event, immediate=True):
                success_count += 1

        return success_count

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        metrics = self.get_metrics()
        return {
            "total_events": metrics.total_events,
            "events_by_source": metrics.events_by_source,
            "events_by_type": metrics.events_by_type,
            "deliveries": {
                "success": metrics.deliveries_success,
                "failed": metrics.deliveries_failed,
                "avg_time_ms": metrics.avg_delivery_time_ms
            },
            "subscriptions": metrics.active_subscriptions,
            "dead_letter_count": metrics.dead_letter_count,
            "history_size": len(self._events),
            "routes": len(self._routes),
            "uptime_seconds": metrics.uptime_seconds,
            "last_event": metrics.last_event_at.isoformat() if metrics.last_event_at else None
        }


# =============================================================================
# EVENT AGGREGATOR
# =============================================================================

class EventAggregator:
    """
    Aggregates events from multiple sources into summary events.

    Useful for reducing event volume and creating meaningful summaries.
    """

    def __init__(
        self,
        window_seconds: int = 60,
        min_events: int = 5
    ):
        self.window_seconds = window_seconds
        self.min_events = min_events
        self._buffers: Dict[str, List[CrossPlatformEvent]] = {}
        self._last_flush: Dict[str, datetime] = {}

    def add_event(self, event: CrossPlatformEvent) -> Optional[CrossPlatformEvent]:
        """
        Add event to aggregation buffer.

        Returns:
            Aggregated event if threshold reached, None otherwise
        """
        key = f"{event.source.value}:{event.event_type.value}"

        if key not in self._buffers:
            self._buffers[key] = []
            self._last_flush[key] = datetime.utcnow()

        self._buffers[key].append(event)

        # Check if we should flush
        window_elapsed = (
            datetime.utcnow() - self._last_flush[key]
        ).total_seconds() >= self.window_seconds

        if len(self._buffers[key]) >= self.min_events or window_elapsed:
            return self._flush_buffer(key)

        return None

    def _flush_buffer(self, key: str) -> Optional[CrossPlatformEvent]:
        """Flush buffer and create aggregated event."""
        if key not in self._buffers or not self._buffers[key]:
            return None

        events = self._buffers[key]
        self._buffers[key] = []
        self._last_flush[key] = datetime.utcnow()

        # Create aggregated event
        first_event = events[0]
        return CrossPlatformEvent.create(
            event_type=first_event.event_type,
            source=first_event.source,
            payload={
                "aggregated": True,
                "event_count": len(events),
                "time_range_seconds": (
                    events[-1].timestamp - events[0].timestamp
                ).total_seconds(),
                "sample_payloads": [e.payload for e in events[:3]]
            },
            metadata={"aggregation_key": key}
        )


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

_cross_platform_bus: Optional[CrossPlatformEventBus] = None


def create_cross_platform_bus(
    config: Optional[CrossPlatformEventConfig] = None
) -> CrossPlatformEventBus:
    """Create a new cross-platform event bus."""
    return CrossPlatformEventBus(config)


def get_cross_platform_bus() -> Optional[CrossPlatformEventBus]:
    """Get the global cross-platform event bus."""
    return _cross_platform_bus


def set_cross_platform_bus(bus: CrossPlatformEventBus) -> None:
    """Set the global cross-platform event bus."""
    global _cross_platform_bus
    _cross_platform_bus = bus


async def emit_cross_platform_event(
    event_type: CrossEventType,
    source: PlatformSource,
    payload: Dict[str, Any],
    priority: EventPriority = EventPriority.NORMAL,
    user_id: Optional[str] = None
) -> bool:
    """Convenience function to emit a cross-platform event."""
    bus = get_cross_platform_bus()
    if not bus:
        logger.warning("No cross-platform bus configured")
        return False

    event = CrossPlatformEvent.create(
        event_type=event_type,
        source=source,
        payload=payload,
        priority=priority,
        user_id=user_id
    )

    return await bus.publish(event)


def subscribe_to_all_events(
    name: str,
    callback: Callable[[CrossPlatformEvent], Any]
) -> Optional[str]:
    """Convenience function to subscribe to all events."""
    bus = get_cross_platform_bus()
    if not bus:
        return None
    return bus.subscribe(name, callback)


async def create_mastermind_cross_platform_bus() -> CrossPlatformEventBus:
    """
    Create and configure cross-platform bus for MASTERMIND.

    Sets up default subscriptions and routes.
    """
    config = CrossPlatformEventConfig(
        max_history_size=50000,
        max_dead_letter_size=5000,
        retry_attempts=5,
        enable_metrics=True,
        max_event_age_hours=48
    )

    bus = create_cross_platform_bus(config)
    set_cross_platform_bus(bus)

    # Start the bus
    await bus.start()

    logger.info("MASTERMIND cross-platform event bus created and started")
    return bus


__all__ = [
    # Enums
    "PlatformSource",
    "CrossEventType",
    "EventPriority",
    "DeliveryStatus",
    "SubscriptionFilter",

    # Data classes
    "CrossPlatformEventConfig",
    "CrossPlatformEvent",
    "EventDelivery",
    "EventSubscription",
    "EventRoute",
    "EventMetrics",

    # Classes
    "CrossPlatformEventBus",
    "EventAggregator",

    # Factory functions
    "create_cross_platform_bus",
    "get_cross_platform_bus",
    "set_cross_platform_bus",
    "emit_cross_platform_event",
    "subscribe_to_all_events",
    "create_mastermind_cross_platform_bus",
]
