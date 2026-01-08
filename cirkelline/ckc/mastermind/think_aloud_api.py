"""
CKC MASTERMIND Think Aloud API (DEL U)
======================================

SSE (Server-Sent Events) API for real-time tanke streaming.

Giver klienter adgang til ThinkAloudStream via HTTP SSE endpoints.
Understøtter multiple samtidige klienter med subscription management.

Princip: Transparent adgang - alle kan lytte til tankerne.

Komponenter:
- ClientSubscription: Klient abonnement info
- StreamChannel: Kanal for streaming
- ThinkAloudAPI: Hoved API klasse
- SSEMessage: SSE formateret besked
"""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set

from .think_aloud_stream import (
    ThinkAloudStream,
    ThoughtFragment,
    ReasoningChain,
    ThoughtType,
    ReasoningStyle,
    StreamState,
    get_think_aloud_stream,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class SubscriptionType(Enum):
    """Type af subscription."""
    ALL = "all"                     # Alle tanker
    THINKER = "thinker"             # Tanker fra specifik tænker
    THOUGHT_TYPE = "thought_type"   # Specifik type tanker
    REASONING_CHAIN = "chain"       # Specifik reasoning chain
    SESSION = "session"             # Specifik session


class ConnectionState(Enum):
    """Tilstand af klient forbindelse."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    PAUSED = "paused"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


class EventType(Enum):
    """Type af SSE event."""
    THOUGHT = "thought"             # Ny tanke
    CHAIN_START = "chain_start"     # Reasoning chain starter
    CHAIN_END = "chain_end"         # Reasoning chain slutter
    STATE_CHANGE = "state_change"   # Stream state ændring
    HEARTBEAT = "heartbeat"         # Keep-alive
    ERROR = "error"                 # Fejl
    SUBSCRIPTION = "subscription"   # Subscription update


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SSEMessage:
    """Server-Sent Event formateret besked."""
    event: EventType
    data: Dict[str, Any]
    id: Optional[str] = None
    retry: Optional[int] = None  # Millisekunder til retry

    def format(self) -> str:
        """Formatér til SSE format."""
        lines = []

        if self.id:
            lines.append(f"id: {self.id}")

        if self.retry:
            lines.append(f"retry: {self.retry}")

        lines.append(f"event: {self.event.value}")
        lines.append(f"data: {json.dumps(self.data)}")
        lines.append("")  # Tom linje afslutter event

        return "\n".join(lines) + "\n"


@dataclass
class SubscriptionFilter:
    """Filter for subscription."""
    thinker_ids: Optional[Set[str]] = None
    thought_types: Optional[Set[ThoughtType]] = None
    reasoning_styles: Optional[Set[ReasoningStyle]] = None
    chain_ids: Optional[Set[str]] = None
    min_confidence: float = 0.0
    include_metadata: bool = True

    def matches(self, fragment: ThoughtFragment) -> bool:
        """Tjek om fragment matcher filter."""
        # Thinker filter
        if self.thinker_ids and fragment.thinker_id not in self.thinker_ids:
            return False

        # Thought type filter
        if self.thought_types and fragment.thought_type not in self.thought_types:
            return False

        # Reasoning style filter
        if self.reasoning_styles and fragment.style not in self.reasoning_styles:
            return False

        # Confidence filter
        if fragment.confidence < self.min_confidence:
            return False

        return True


@dataclass
class ClientSubscription:
    """Information om en klient subscription."""
    subscription_id: str
    client_id: str
    subscription_type: SubscriptionType
    filter: SubscriptionFilter = field(default_factory=SubscriptionFilter)

    # Connection state
    state: ConnectionState = ConnectionState.CONNECTING
    connected_at: datetime = field(default_factory=datetime.now)
    last_event_at: Optional[datetime] = None
    last_heartbeat_at: Optional[datetime] = None

    # Statistics
    events_sent: int = 0
    events_filtered: int = 0
    bytes_sent: int = 0
    errors: int = 0

    # Queue for async iteration
    _queue: asyncio.Queue = field(default_factory=asyncio.Queue, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            "client_id": self.client_id,
            "subscription_type": self.subscription_type.value,
            "state": self.state.value,
            "connected_at": self.connected_at.isoformat(),
            "events_sent": self.events_sent,
            "events_filtered": self.events_filtered
        }


@dataclass
class StreamChannel:
    """En kanal for streaming til multiple klienter."""
    channel_id: str
    name: str
    description: str = ""

    subscriptions: Dict[str, ClientSubscription] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    # Statistics
    total_events: int = 0
    total_subscribers: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "name": self.name,
            "description": self.description,
            "active_subscriptions": len(self.subscriptions),
            "total_events": self.total_events,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class APIStats:
    """Statistik for ThinkAloudAPI."""
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    total_events_sent: int = 0
    total_bytes_sent: int = 0
    total_errors: int = 0

    uptime_seconds: float = 0.0
    events_per_second: float = 0.0

    started_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_subscriptions": self.total_subscriptions,
            "active_subscriptions": self.active_subscriptions,
            "total_events_sent": self.total_events_sent,
            "total_bytes_sent": self.total_bytes_sent,
            "total_errors": self.total_errors,
            "uptime_seconds": self.uptime_seconds,
            "events_per_second": self.events_per_second,
            "started_at": self.started_at.isoformat() if self.started_at else None
        }


# =============================================================================
# THINK ALOUD API
# =============================================================================

class ThinkAloudAPI:
    """
    SSE API for real-time tanke streaming.

    Forbinder til ThinkAloudStream og broadcaster tanker
    til tilmeldte klienter via Server-Sent Events.
    """

    def __init__(
        self,
        think_aloud_stream: Optional[ThinkAloudStream] = None,
        heartbeat_interval: float = 30.0,
        max_subscriptions_per_client: int = 10,
        event_buffer_size: int = 1000
    ):
        self._stream = think_aloud_stream
        self._heartbeat_interval = heartbeat_interval
        self._max_subscriptions_per_client = max_subscriptions_per_client
        self._event_buffer_size = event_buffer_size

        # Channels
        self._default_channel = StreamChannel(
            channel_id="default",
            name="Default",
            description="Default streaming channel"
        )
        self._channels: Dict[str, StreamChannel] = {
            "default": self._default_channel
        }

        # All subscriptions (flattened for quick lookup)
        self._subscriptions: Dict[str, ClientSubscription] = {}
        self._client_subscriptions: Dict[str, Set[str]] = {}  # client_id -> subscription_ids

        # State
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = APIStats()

        # Callbacks
        self._on_subscribe_callbacks: List[Callable[[ClientSubscription], None]] = []
        self._on_unsubscribe_callbacks: List[Callable[[str], None]] = []

        logger.info("ThinkAloudAPI initialized")

    # =========================================================================
    # SUBSCRIPTION MANAGEMENT
    # =========================================================================

    async def subscribe(
        self,
        client_id: str,
        subscription_type: SubscriptionType = SubscriptionType.ALL,
        filter: Optional[SubscriptionFilter] = None,
        channel_id: str = "default"
    ) -> ClientSubscription:
        """
        Opret en ny subscription.

        Returns:
            ClientSubscription som kan bruges til at iterere over events.
        """
        # Check client limit
        client_subs = self._client_subscriptions.get(client_id, set())
        if len(client_subs) >= self._max_subscriptions_per_client:
            raise ValueError(
                f"Client {client_id} has reached max subscriptions "
                f"({self._max_subscriptions_per_client})"
            )

        # Get or create channel
        channel = self._channels.get(channel_id)
        if not channel:
            channel = StreamChannel(
                channel_id=channel_id,
                name=channel_id.title(),
            )
            self._channels[channel_id] = channel

        # Create subscription
        subscription = ClientSubscription(
            subscription_id=f"sub_{secrets.token_hex(12)}",
            client_id=client_id,
            subscription_type=subscription_type,
            filter=filter or SubscriptionFilter(),
            state=ConnectionState.CONNECTED
        )

        # Register subscription
        self._subscriptions[subscription.subscription_id] = subscription
        channel.subscriptions[subscription.subscription_id] = subscription
        channel.total_subscribers += 1

        # Track client subscriptions
        if client_id not in self._client_subscriptions:
            self._client_subscriptions[client_id] = set()
        self._client_subscriptions[client_id].add(subscription.subscription_id)

        # Update stats
        self._stats.total_subscriptions += 1
        self._stats.active_subscriptions += 1

        # Notify callbacks
        for callback in self._on_subscribe_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(subscription)
                else:
                    callback(subscription)
            except Exception as e:
                logger.error(f"Subscribe callback error: {e}")

        logger.info(f"New subscription: {subscription.subscription_id} for client {client_id}")

        # Send subscription confirmation
        await self._send_to_subscription(
            subscription,
            SSEMessage(
                event=EventType.SUBSCRIPTION,
                data={
                    "action": "subscribed",
                    "subscription_id": subscription.subscription_id,
                    "type": subscription_type.value,
                    "channel": channel_id
                },
                id=f"sub_{subscription.subscription_id}"
            )
        )

        return subscription

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Afmeld en subscription."""
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return False

        # Mark as disconnecting
        subscription.state = ConnectionState.DISCONNECTING

        # Remove from channel
        for channel in self._channels.values():
            if subscription_id in channel.subscriptions:
                del channel.subscriptions[subscription_id]
                break

        # Remove from tracking
        del self._subscriptions[subscription_id]

        client_subs = self._client_subscriptions.get(subscription.client_id, set())
        client_subs.discard(subscription_id)
        if not client_subs:
            del self._client_subscriptions[subscription.client_id]

        # Update stats
        self._stats.active_subscriptions -= 1

        # Notify callbacks
        for callback in self._on_unsubscribe_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(subscription_id)
                else:
                    callback(subscription_id)
            except Exception as e:
                logger.error(f"Unsubscribe callback error: {e}")

        subscription.state = ConnectionState.DISCONNECTED
        logger.info(f"Unsubscribed: {subscription_id}")

        return True

    def get_subscription(self, subscription_id: str) -> Optional[ClientSubscription]:
        """Hent subscription by ID."""
        return self._subscriptions.get(subscription_id)

    def get_client_subscriptions(self, client_id: str) -> List[ClientSubscription]:
        """Hent alle subscriptions for en klient."""
        sub_ids = self._client_subscriptions.get(client_id, set())
        return [self._subscriptions[sid] for sid in sub_ids if sid in self._subscriptions]

    # =========================================================================
    # STREAMING
    # =========================================================================

    async def stream_events(
        self,
        subscription: ClientSubscription
    ) -> AsyncIterator[str]:
        """
        Async generator der yielder SSE-formaterede events.

        Brug denne til at streame events til en klient.
        """
        subscription.state = ConnectionState.STREAMING

        try:
            while subscription.state == ConnectionState.STREAMING:
                try:
                    # Wait for event with timeout
                    message = await asyncio.wait_for(
                        subscription._queue.get(),
                        timeout=self._heartbeat_interval
                    )

                    # Format and yield
                    formatted = message.format()
                    subscription.events_sent += 1
                    subscription.bytes_sent += len(formatted.encode())
                    subscription.last_event_at = datetime.now()

                    yield formatted

                except asyncio.TimeoutError:
                    # Send heartbeat on timeout
                    heartbeat = SSEMessage(
                        event=EventType.HEARTBEAT,
                        data={
                            "timestamp": datetime.now().isoformat(),
                            "subscription_id": subscription.subscription_id
                        }
                    )
                    subscription.last_heartbeat_at = datetime.now()
                    yield heartbeat.format()

        except asyncio.CancelledError:
            logger.debug(f"Stream cancelled for {subscription.subscription_id}")
        except Exception as e:
            logger.error(f"Stream error for {subscription.subscription_id}: {e}")
            subscription.errors += 1

        finally:
            subscription.state = ConnectionState.DISCONNECTED

    # =========================================================================
    # EVENT DISTRIBUTION
    # =========================================================================

    async def _send_to_subscription(
        self,
        subscription: ClientSubscription,
        message: SSEMessage
    ) -> bool:
        """Send besked til en subscription."""
        if subscription.state not in (ConnectionState.CONNECTED, ConnectionState.STREAMING):
            return False

        try:
            # Non-blocking put with size limit
            if subscription._queue.qsize() < self._event_buffer_size:
                await subscription._queue.put(message)
                return True
            else:
                subscription.events_filtered += 1
                logger.warning(
                    f"Queue full for {subscription.subscription_id}, event dropped"
                )
                return False

        except Exception as e:
            logger.error(f"Error sending to {subscription.subscription_id}: {e}")
            subscription.errors += 1
            return False

    async def broadcast_thought(
        self,
        fragment: ThoughtFragment,
        channel_id: str = "default"
    ) -> int:
        """
        Broadcast en tanke til alle tilmeldte klienter i en kanal.

        Returns:
            Antal klienter der modtog tanken.
        """
        channel = self._channels.get(channel_id)
        if not channel:
            return 0

        message = SSEMessage(
            event=EventType.THOUGHT,
            data={
                "fragment_id": fragment.fragment_id,
                "thinker_id": fragment.thinker_id,
                "thought_type": fragment.thought_type.value,
                "content": fragment.content,
                "confidence": fragment.confidence,
                "style": fragment.style.value,
                "timestamp": fragment.timestamp.isoformat() if hasattr(fragment, 'timestamp') else datetime.now().isoformat()
            },
            id=fragment.fragment_id
        )

        sent_count = 0
        for sub in channel.subscriptions.values():
            # Apply filter
            if sub.filter.matches(fragment):
                if await self._send_to_subscription(sub, message):
                    sent_count += 1
            else:
                sub.events_filtered += 1

        channel.total_events += 1
        self._stats.total_events_sent += sent_count

        return sent_count

    async def broadcast_chain_event(
        self,
        chain: ReasoningChain,
        event_type: EventType,
        channel_id: str = "default"
    ) -> int:
        """Broadcast chain start/end event."""
        channel = self._channels.get(channel_id)
        if not channel:
            return 0

        message = SSEMessage(
            event=event_type,
            data={
                "chain_id": chain.chain_id,
                "thinker_id": chain.thinker_id,
                "topic": chain.topic,
                "fragment_count": len(chain.fragments) if hasattr(chain, 'fragments') else 0,
                "timestamp": datetime.now().isoformat()
            },
            id=f"chain_{chain.chain_id}"
        )

        sent_count = 0
        for sub in channel.subscriptions.values():
            if await self._send_to_subscription(sub, message):
                sent_count += 1

        return sent_count

    async def broadcast_state_change(
        self,
        new_state: StreamState,
        channel_id: str = "default"
    ) -> int:
        """Broadcast state change event."""
        channel = self._channels.get(channel_id)
        if not channel:
            return 0

        message = SSEMessage(
            event=EventType.STATE_CHANGE,
            data={
                "state": new_state.value,
                "timestamp": datetime.now().isoformat()
            }
        )

        sent_count = 0
        for sub in channel.subscriptions.values():
            if await self._send_to_subscription(sub, message):
                sent_count += 1

        return sent_count

    # =========================================================================
    # STREAM LISTENER
    # =========================================================================

    async def _listen_to_stream(self) -> None:
        """Lyt til ThinkAloudStream og broadcast events."""
        if not self._stream:
            logger.warning("No ThinkAloudStream configured, listener not started")
            return

        try:
            # Subscribe to stream events
            async for fragment in self._stream.listen():
                if not self._running:
                    break

                await self.broadcast_thought(fragment)

        except asyncio.CancelledError:
            logger.debug("Stream listener cancelled")
        except Exception as e:
            logger.error(f"Stream listener error: {e}")

    # =========================================================================
    # CHANNEL MANAGEMENT
    # =========================================================================

    def create_channel(
        self,
        channel_id: str,
        name: str,
        description: str = ""
    ) -> StreamChannel:
        """Opret en ny kanal."""
        if channel_id in self._channels:
            raise ValueError(f"Channel {channel_id} already exists")

        channel = StreamChannel(
            channel_id=channel_id,
            name=name,
            description=description
        )
        self._channels[channel_id] = channel

        logger.info(f"Channel created: {channel_id}")
        return channel

    def get_channel(self, channel_id: str) -> Optional[StreamChannel]:
        """Hent en kanal."""
        return self._channels.get(channel_id)

    def list_channels(self) -> List[StreamChannel]:
        """List alle kanaler."""
        return list(self._channels.values())

    def delete_channel(self, channel_id: str) -> bool:
        """Slet en kanal (kan ikke slette default)."""
        if channel_id == "default":
            raise ValueError("Cannot delete default channel")

        channel = self._channels.get(channel_id)
        if not channel:
            return False

        # Unsubscribe all
        for sub_id in list(channel.subscriptions.keys()):
            asyncio.create_task(self.unsubscribe(sub_id))

        del self._channels[channel_id]
        logger.info(f"Channel deleted: {channel_id}")
        return True

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    async def start(self) -> None:
        """Start API."""
        if self._running:
            logger.warning("ThinkAloudAPI already running")
            return

        self._running = True
        self._stats.started_at = datetime.now()

        # Get stream if not set
        if not self._stream:
            self._stream = get_think_aloud_stream()

        # Start listener
        if self._stream:
            self._listener_task = asyncio.create_task(self._listen_to_stream())

        logger.info("ThinkAloudAPI started")

    async def stop(self) -> None:
        """Stop API."""
        if not self._running:
            return

        self._running = False

        # Cancel tasks
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        # Disconnect all subscriptions
        for sub_id in list(self._subscriptions.keys()):
            await self.unsubscribe(sub_id)

        # Update stats
        if self._stats.started_at:
            self._stats.uptime_seconds = (
                datetime.now() - self._stats.started_at
            ).total_seconds()

        logger.info("ThinkAloudAPI stopped")

    # =========================================================================
    # CALLBACKS
    # =========================================================================

    def on_subscribe(self, callback: Callable[[ClientSubscription], None]) -> None:
        """Registrer callback for nye subscriptions."""
        self._on_subscribe_callbacks.append(callback)

    def on_unsubscribe(self, callback: Callable[[str], None]) -> None:
        """Registrer callback for unsubscriptions."""
        self._on_unsubscribe_callbacks.append(callback)

    # =========================================================================
    # STATUS & STATS
    # =========================================================================

    def get_stats(self) -> APIStats:
        """Hent API statistik."""
        if self._stats.started_at and self._running:
            self._stats.uptime_seconds = (
                datetime.now() - self._stats.started_at
            ).total_seconds()

            if self._stats.uptime_seconds > 0:
                self._stats.events_per_second = (
                    self._stats.total_events_sent / self._stats.uptime_seconds
                )

        return self._stats

    @property
    def is_running(self) -> bool:
        """Er API kørende?"""
        return self._running

    @property
    def active_subscriptions(self) -> int:
        """Antal aktive subscriptions."""
        return self._stats.active_subscriptions


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

_api_instance: Optional[ThinkAloudAPI] = None


def create_think_aloud_api(
    think_aloud_stream: Optional[ThinkAloudStream] = None,
    **kwargs
) -> ThinkAloudAPI:
    """Opret ny ThinkAloudAPI instans."""
    return ThinkAloudAPI(think_aloud_stream=think_aloud_stream, **kwargs)


def get_think_aloud_api() -> Optional[ThinkAloudAPI]:
    """Hent global ThinkAloudAPI instans."""
    return _api_instance


def set_think_aloud_api(api: ThinkAloudAPI) -> None:
    """Sæt global ThinkAloudAPI instans."""
    global _api_instance
    _api_instance = api


# =============================================================================
# FASTAPI INTEGRATION HELPERS
# =============================================================================

def create_sse_response_headers() -> Dict[str, str]:
    """Opret headers for SSE response."""
    return {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"  # For nginx
    }


async def sse_event_generator(
    api: ThinkAloudAPI,
    client_id: str,
    subscription_type: SubscriptionType = SubscriptionType.ALL,
    filter: Optional[SubscriptionFilter] = None
) -> AsyncIterator[str]:
    """
    Generator til brug med FastAPI StreamingResponse.

    Eksempel:
        @app.get("/api/think-aloud/stream")
        async def stream_thoughts(request: Request):
            api = get_think_aloud_api()
            client_id = request.client.host

            return StreamingResponse(
                sse_event_generator(api, client_id),
                media_type="text/event-stream",
                headers=create_sse_response_headers()
            )
    """
    subscription = await api.subscribe(
        client_id=client_id,
        subscription_type=subscription_type,
        filter=filter
    )

    try:
        async for event in api.stream_events(subscription):
            yield event
    finally:
        await api.unsubscribe(subscription.subscription_id)
