"""
CKC HTTP Platform Connector
===========================

Connector for HTTP-based platforms (Cosmic Library, lib-admin, CLA API, etc.)
Provides REST API integration with event polling and webhook support.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
import json

import aiohttp

from .base import (
    CKCConnector,
    ConnectorConfig,
    ConnectorCapability,
    ConnectorEvent,
    ConnectorHealthStatus,
    ConnectorStatus,
    ActionResult,
)

logger = logging.getLogger(__name__)


class HTTPConnectorConfig(ConnectorConfig):
    """Extended configuration for HTTP connectors."""

    def __init__(
        self,
        name: str,
        platform_id: str,
        base_url: str,
        api_key: Optional[str] = None,
        auth_token: Optional[str] = None,
        auth_header: str = "Authorization",
        auth_prefix: str = "Bearer",
        headers: Optional[Dict[str, str]] = None,
        poll_interval: int = 10,  # seconds
        enabled: bool = True,
        auto_reconnect: bool = True,
        **kwargs
    ):
        super().__init__(
            name=name,
            platform_id=platform_id,
            enabled=enabled,
            auto_reconnect=auto_reconnect,
            **kwargs
        )
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.auth_token = auth_token
        self.auth_header = auth_header
        self.auth_prefix = auth_prefix
        self.custom_headers = headers or {}
        self.poll_interval = poll_interval


class HTTPConnector(CKCConnector):
    """
    HTTP-based connector for external platforms.

    Supports:
    - REST API calls
    - Event polling
    - Webhook delivery
    - Authentication (API key, Bearer token)
    """

    def __init__(self, config: HTTPConnectorConfig):
        super().__init__(config)
        self.http_config = config

        # Add capabilities
        self.add_capability(ConnectorCapability.READ_EVENTS)
        self.add_capability(ConnectorCapability.WRITE_EVENTS)
        self.add_capability(ConnectorCapability.EXECUTE_ACTIONS)
        self.add_capability(ConnectorCapability.BATCH_OPERATIONS)
        self.add_capability(ConnectorCapability.WEBHOOKS)

        # HTTP client
        self._session: Optional[aiohttp.ClientSession] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._polling_endpoints: Dict[str, Dict[str, Any]] = {}

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CKC-Connector/1.0"
        }

        # Add authentication
        if self.http_config.auth_token:
            headers[self.http_config.auth_header] = (
                f"{self.http_config.auth_prefix} {self.http_config.auth_token}"
            )
        elif self.http_config.api_key:
            headers["X-API-Key"] = self.http_config.api_key

        # Add custom headers
        headers.update(self.http_config.custom_headers)

        return headers

    async def connect(self) -> bool:
        """Establish HTTP connection (create session)."""
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self._get_headers()
            )

            # Verify connection with health check
            async with self._session.get(
                f"{self.http_config.base_url}/health"
            ) as resp:
                if resp.status in (200, 204):
                    logger.info(
                        f"HTTP connector connected to {self.http_config.base_url}"
                    )
                    return True
                else:
                    # Try without /health - some platforms don't have it
                    logger.warning(
                        f"Health endpoint returned {resp.status}, "
                        "trying base URL"
                    )

            # Try base URL
            async with self._session.get(self.http_config.base_url) as resp:
                if resp.status < 500:  # Accept any non-server-error
                    logger.info(
                        f"HTTP connector connected to {self.http_config.base_url} "
                        f"(status {resp.status})"
                    )
                    return True

            return False

        except aiohttp.ClientError as e:
            logger.error(f"HTTP connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting: {e}")
            return False

    async def disconnect(self) -> bool:
        """Close HTTP session."""
        try:
            # Stop polling
            if self._poll_task:
                self._poll_task.cancel()
                try:
                    await self._poll_task
                except asyncio.CancelledError:
                    pass

            # Close session
            if self._session:
                await self._session.close()
                self._session = None

            logger.info(f"HTTP connector disconnected from {self.http_config.base_url}")
            return True

        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False

    async def health_check(self) -> ConnectorHealthStatus:
        """Check platform health via HTTP."""
        start_time = datetime.utcnow()

        try:
            if self._session is None:
                return ConnectorHealthStatus(
                    status=ConnectorStatus.DISCONNECTED,
                    last_check=start_time,
                    error_message="HTTP session not initialized"
                )

            # Try health endpoint
            try:
                async with self._session.get(
                    f"{self.http_config.base_url}/health"
                ) as resp:
                    latency = (datetime.utcnow() - start_time).total_seconds() * 1000

                    if resp.status == 200:
                        data = await resp.json()
                        return ConnectorHealthStatus(
                            status=ConnectorStatus.CONNECTED,
                            last_check=datetime.utcnow(),
                            latency_ms=latency,
                            events_processed=self._events_processed,
                            events_failed=self._events_failed,
                            uptime_seconds=self.get_uptime_seconds(),
                            details=data
                        )
                    else:
                        return ConnectorHealthStatus(
                            status=ConnectorStatus.ERROR,
                            last_check=datetime.utcnow(),
                            latency_ms=latency,
                            error_message=f"Health check returned {resp.status}"
                        )

            except aiohttp.ClientError as e:
                return ConnectorHealthStatus(
                    status=ConnectorStatus.ERROR,
                    last_check=datetime.utcnow(),
                    error_message=f"Connection error: {e}"
                )

        except Exception as e:
            return ConnectorHealthStatus(
                status=ConnectorStatus.ERROR,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )

    async def subscribe_events(
        self,
        event_types: List[str],
        callback: Callable[[ConnectorEvent], None]
    ) -> bool:
        """
        Subscribe to events via polling.

        Event types map to polling endpoints:
        - events: GET /api/events (with ?since=timestamp)
        - notifications: GET /api/notifications
        - tasks: GET /api/tasks/updates
        """
        try:
            for event_type in event_types:
                self.on_event(event_type, callback)

                # Map event type to endpoint
                endpoint = self._map_event_to_endpoint(event_type)
                if endpoint:
                    self._polling_endpoints[event_type] = {
                        "endpoint": endpoint,
                        "last_poll": None,
                        "last_id": None
                    }

            # Start polling if not already running
            if self._polling_endpoints and self._poll_task is None:
                self._poll_task = asyncio.create_task(self._poll_loop())

            logger.info(f"Subscribed to events: {event_types}")
            return True

        except Exception as e:
            logger.error(f"Failed to subscribe to events: {e}")
            return False

    def _map_event_to_endpoint(self, event_type: str) -> Optional[str]:
        """Map event type to API endpoint."""
        mappings = {
            "events": "/api/events",
            "notifications": "/api/notifications",
            "tasks": "/api/tasks/updates",
            "bookings": "/api/bookings",
            "learning_events": "/api/learning/events",
            "agent_status": "/api/agents/status",
            "system_events": "/api/system/events",
        }
        return mappings.get(event_type)

    async def _poll_loop(self) -> None:
        """Poll endpoints for new events."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.http_config.poll_interval)

                if self._shutdown_event.is_set():
                    break

                for event_type, config in self._polling_endpoints.items():
                    await self._poll_endpoint(event_type, config)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Polling error: {e}")

    async def _poll_endpoint(
        self,
        event_type: str,
        config: Dict[str, Any]
    ) -> None:
        """Poll a single endpoint for new events."""
        try:
            endpoint = config["endpoint"]
            params = {}

            # Add pagination/filtering params
            if config.get("last_poll"):
                params["since"] = config["last_poll"].isoformat()
            if config.get("last_id"):
                params["after_id"] = config["last_id"]

            url = f"{self.http_config.base_url}{endpoint}"

            async with self._session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    events = data if isinstance(data, list) else data.get("items", [])

                    for item in events:
                        event = ConnectorEvent(
                            event_id=item.get("id", f"evt_{id(item)}"),
                            event_type=event_type,
                            source=self.config.platform_id,
                            timestamp=datetime.utcnow(),
                            payload=item,
                            metadata={"polled_from": endpoint}
                        )
                        await self._dispatch_event(event)

                        # Update last ID
                        if "id" in item:
                            config["last_id"] = item["id"]

                    config["last_poll"] = datetime.utcnow()

                elif resp.status == 404:
                    # Endpoint not found - remove from polling
                    logger.warning(f"Endpoint {endpoint} not found, removing")
                    del self._polling_endpoints[event_type]

        except Exception as e:
            logger.error(f"Error polling {endpoint}: {e}")

    async def publish_event(self, event: ConnectorEvent) -> bool:
        """Publish event to platform via POST."""
        try:
            if self._session is None:
                return False

            # Determine endpoint based on event type
            endpoint = f"/api/events"
            if event.event_type.startswith("webhook."):
                endpoint = event.metadata.get("webhook_url", "/api/webhooks")

            url = f"{self.http_config.base_url}{endpoint}"

            async with self._session.post(url, json=event.to_dict()) as resp:
                if resp.status in (200, 201, 202):
                    self._events_processed += 1
                    return True
                else:
                    logger.warning(f"Failed to publish event: {resp.status}")
                    self._events_failed += 1
                    return False

        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            self._events_failed += 1
            return False

    async def execute_action(
        self,
        action_type: str,
        action_data: Dict[str, Any]
    ) -> ActionResult:
        """
        Execute HTTP action on platform.

        Actions:
        - get: GET request
        - post: POST request
        - put: PUT request
        - delete: DELETE request
        - patch: PATCH request
        """
        import uuid
        action_id = f"act_{uuid.uuid4().hex[:12]}"
        start_time = datetime.utcnow()

        try:
            if self._session is None:
                return ActionResult(
                    success=False,
                    action_id=action_id,
                    error="HTTP session not initialized"
                )

            method = action_data.get("method", action_type).upper()
            endpoint = action_data.get("endpoint", "/")
            body = action_data.get("body")
            params = action_data.get("params")

            url = f"{self.http_config.base_url}{endpoint}"

            async with self._session.request(
                method=method,
                url=url,
                json=body,
                params=params
            ) as resp:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000

                try:
                    result_data = await resp.json()
                except:
                    result_data = {"text": await resp.text()}

                if resp.status < 400:
                    return ActionResult(
                        success=True,
                        action_id=action_id,
                        result_data=result_data,
                        duration_ms=duration,
                        metadata={"status_code": resp.status}
                    )
                else:
                    return ActionResult(
                        success=False,
                        action_id=action_id,
                        result_data=result_data,
                        error=f"HTTP {resp.status}",
                        duration_ms=duration,
                        metadata={"status_code": resp.status}
                    )

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ActionResult(
                success=False,
                action_id=action_id,
                error=str(e),
                duration_ms=duration
            )

    # Convenience methods
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> ActionResult:
        """Convenience method for GET requests."""
        return await self.execute_action("get", {
            "method": "GET",
            "endpoint": endpoint,
            "params": params
        })

    async def post(
        self,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None
    ) -> ActionResult:
        """Convenience method for POST requests."""
        return await self.execute_action("post", {
            "method": "POST",
            "endpoint": endpoint,
            "body": body
        })

    async def put(
        self,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None
    ) -> ActionResult:
        """Convenience method for PUT requests."""
        return await self.execute_action("put", {
            "method": "PUT",
            "endpoint": endpoint,
            "body": body
        })

    async def delete(self, endpoint: str) -> ActionResult:
        """Convenience method for DELETE requests."""
        return await self.execute_action("delete", {
            "method": "DELETE",
            "endpoint": endpoint
        })


# Pre-configured platform connectors
class CosmicLibraryConnector(HTTPConnector):
    """Connector for Cosmic Library platform."""

    def __init__(
        self,
        base_url: str = "http://localhost:7780",
        auth_token: Optional[str] = None
    ):
        config = HTTPConnectorConfig(
            name="Cosmic Library",
            platform_id="cosmic_library",
            base_url=base_url,
            auth_token=auth_token,
            poll_interval=5
        )
        super().__init__(config)


class LibAdminConnector(HTTPConnector):
    """Connector for lib-admin platform."""

    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        auth_token: Optional[str] = None
    ):
        config = HTTPConnectorConfig(
            name="Lib Admin",
            platform_id="lib_admin",
            base_url=base_url,
            auth_token=auth_token,
            poll_interval=10
        )
        super().__init__(config)


class CLAConnector(HTTPConnector):
    """Connector for Cirkelline Local Agent (CLA) API."""

    def __init__(
        self,
        base_url: str = "http://localhost:7781",
        api_key: Optional[str] = None
    ):
        config = HTTPConnectorConfig(
            name="CLA",
            platform_id="cla",
            base_url=base_url,
            api_key=api_key,
            poll_interval=15
        )
        super().__init__(config)
        self.add_capability(ConnectorCapability.STREAM_DATA)
