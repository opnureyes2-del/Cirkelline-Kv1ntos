"""
CKC Webhook Connector
=====================

Connector for receiving webhooks from external platforms.
Provides a webhook receiver that can be integrated with FastAPI.
"""

import asyncio
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import json

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


class WebhookConfig(ConnectorConfig):
    """Configuration for webhook connector."""

    def __init__(
        self,
        name: str = "Webhook Receiver",
        platform_id: str = "webhooks",
        secret: Optional[str] = None,
        signature_header: str = "X-Webhook-Signature",
        signature_algorithm: str = "sha256",
        allowed_ips: Optional[List[str]] = None,
        validate_signatures: bool = True,
        enabled: bool = True,
        **kwargs
    ):
        super().__init__(
            name=name,
            platform_id=platform_id,
            enabled=enabled,
            **kwargs
        )
        self.secret = secret
        self.signature_header = signature_header
        self.signature_algorithm = signature_algorithm
        self.allowed_ips = allowed_ips or []
        self.validate_signatures = validate_signatures


class WebhookReceiver:
    """
    Webhook receiver for handling incoming webhooks.

    This class can be integrated with FastAPI:

    ```python
    from fastapi import FastAPI, Request
    from cirkelline.ckc.connectors.webhook_connector import WebhookConnector

    app = FastAPI()
    webhook = WebhookConnector()

    @app.post("/webhooks/{source}")
    async def handle_webhook(source: str, request: Request):
        return await webhook.handle_request(source, request)
    ```
    """

    def __init__(self, config: WebhookConfig):
        self.config = config
        self._handlers: Dict[str, List[Callable]] = {}
        self._events_received = 0
        self._events_failed = 0

    def on(
        self,
        source: str,
        handler: Callable[[ConnectorEvent], None]
    ) -> None:
        """Register a handler for webhooks from a source."""
        if source not in self._handlers:
            self._handlers[source] = []
        self._handlers[source].append(handler)

    def validate_signature(
        self,
        payload: bytes,
        signature: str,
        secret: Optional[str] = None
    ) -> bool:
        """Validate webhook signature."""
        if not self.config.validate_signatures:
            return True

        secret = secret or self.config.secret
        if not secret:
            logger.warning("No secret configured, skipping signature validation")
            return True

        # Calculate expected signature
        if self.config.signature_algorithm == "sha256":
            expected = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
        elif self.config.signature_algorithm == "sha1":
            expected = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha1
            ).hexdigest()
        else:
            logger.error(f"Unknown signature algorithm: {self.config.signature_algorithm}")
            return False

        # Compare (handle different signature formats)
        signature = signature.replace(f"{self.config.signature_algorithm}=", "")
        return hmac.compare_digest(expected.lower(), signature.lower())

    def validate_ip(self, ip: str) -> bool:
        """Validate source IP address."""
        if not self.config.allowed_ips:
            return True
        return ip in self.config.allowed_ips

    async def process_webhook(
        self,
        source: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConnectorEvent:
        """Process a webhook payload and dispatch to handlers."""
        import uuid

        event = ConnectorEvent(
            event_id=f"wh_{uuid.uuid4().hex[:12]}",
            event_type=payload.get("event", payload.get("type", "webhook")),
            source=source,
            timestamp=datetime.utcnow(),
            payload=payload,
            metadata={
                **(metadata or {}),
                "headers": headers or {},
                "webhook_source": source
            }
        )

        # Dispatch to handlers
        handlers = self._handlers.get(source, [])
        handlers.extend(self._handlers.get("*", []))  # Wildcard handlers

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                self._events_received += 1
            except Exception as e:
                logger.error(f"Error in webhook handler: {e}")
                self._events_failed += 1

        return event


class WebhookConnector(CKCConnector):
    """
    Connector for receiving webhooks from external platforms.

    Provides:
    - Webhook signature validation
    - IP whitelisting
    - Event routing based on source
    - FastAPI integration helpers
    """

    def __init__(self, config: Optional[WebhookConfig] = None):
        config = config or WebhookConfig()
        super().__init__(config)
        self.webhook_config = config

        # Add capabilities
        self.add_capability(ConnectorCapability.READ_EVENTS)
        self.add_capability(ConnectorCapability.WEBHOOKS)

        # Webhook receiver
        self._receiver = WebhookReceiver(config)
        self._registered_sources: Dict[str, Dict[str, Any]] = {}

    async def connect(self) -> bool:
        """Webhook connector is always 'connected' - just needs to be started."""
        logger.info("Webhook connector ready to receive webhooks")
        return True

    async def disconnect(self) -> bool:
        """Stop receiving webhooks."""
        self._registered_sources.clear()
        logger.info("Webhook connector stopped")
        return True

    async def health_check(self) -> ConnectorHealthStatus:
        """Return health status."""
        return ConnectorHealthStatus(
            status=ConnectorStatus.CONNECTED,
            last_check=datetime.utcnow(),
            events_processed=self._receiver._events_received,
            events_failed=self._receiver._events_failed,
            uptime_seconds=self.get_uptime_seconds(),
            details={
                "registered_sources": list(self._registered_sources.keys()),
                "handler_count": sum(len(h) for h in self._receiver._handlers.values())
            }
        )

    async def subscribe_events(
        self,
        event_types: List[str],
        callback: Callable[[ConnectorEvent], None]
    ) -> bool:
        """
        Subscribe to webhook events.

        Event types are treated as webhook sources.
        Use "*" to subscribe to all webhooks.
        """
        for event_type in event_types:
            self._receiver.on(event_type, callback)
            self.on_event(event_type, callback)

        logger.info(f"Subscribed to webhook sources: {event_types}")
        return True

    async def publish_event(self, event: ConnectorEvent) -> bool:
        """
        Webhooks are receive-only by nature.
        This method is not applicable for webhook connector.
        """
        logger.warning("Webhook connector cannot publish events")
        return False

    async def execute_action(
        self,
        action_type: str,
        action_data: Dict[str, Any]
    ) -> ActionResult:
        """
        Execute webhook-related actions.

        Actions:
        - register_source: Register a new webhook source
        - unregister_source: Remove a webhook source
        - get_sources: List registered sources
        - validate_payload: Validate a webhook payload
        """
        import uuid
        action_id = f"act_{uuid.uuid4().hex[:12]}"

        try:
            if action_type == "register_source":
                source = action_data.get("source")
                secret = action_data.get("secret")
                allowed_ips = action_data.get("allowed_ips")

                self._registered_sources[source] = {
                    "secret": secret,
                    "allowed_ips": allowed_ips,
                    "registered_at": datetime.utcnow().isoformat()
                }

                return ActionResult(
                    success=True,
                    action_id=action_id,
                    result_data={"source": source, "registered": True}
                )

            elif action_type == "unregister_source":
                source = action_data.get("source")
                if source in self._registered_sources:
                    del self._registered_sources[source]
                    return ActionResult(
                        success=True,
                        action_id=action_id,
                        result_data={"source": source, "unregistered": True}
                    )
                else:
                    return ActionResult(
                        success=False,
                        action_id=action_id,
                        error=f"Source not found: {source}"
                    )

            elif action_type == "get_sources":
                return ActionResult(
                    success=True,
                    action_id=action_id,
                    result_data={"sources": list(self._registered_sources.keys())}
                )

            elif action_type == "validate_payload":
                payload = action_data.get("payload", b"")
                signature = action_data.get("signature", "")
                source = action_data.get("source")

                secret = None
                if source in self._registered_sources:
                    secret = self._registered_sources[source].get("secret")

                valid = self._receiver.validate_signature(
                    payload if isinstance(payload, bytes) else payload.encode(),
                    signature,
                    secret
                )

                return ActionResult(
                    success=True,
                    action_id=action_id,
                    result_data={"valid": valid}
                )

            else:
                return ActionResult(
                    success=False,
                    action_id=action_id,
                    error=f"Unknown action: {action_type}"
                )

        except Exception as e:
            return ActionResult(
                success=False,
                action_id=action_id,
                error=str(e)
            )

    async def handle_webhook(
        self,
        source: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        client_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle an incoming webhook.

        This is the main entry point for processing webhooks.
        Can be called from a FastAPI endpoint.
        """
        try:
            # Validate IP if source is registered
            if source in self._registered_sources:
                allowed_ips = self._registered_sources[source].get("allowed_ips")
                if allowed_ips and client_ip and client_ip not in allowed_ips:
                    return {
                        "success": False,
                        "error": "IP not allowed",
                        "status_code": 403
                    }

            # Process webhook
            event = await self._receiver.process_webhook(
                source=source,
                payload=payload,
                headers=headers,
                metadata={"client_ip": client_ip}
            )

            # Dispatch to our event handlers
            await self._dispatch_event(event)

            return {
                "success": True,
                "event_id": event.event_id,
                "status_code": 200
            }

        except Exception as e:
            logger.error(f"Error handling webhook from {source}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": 500
            }

    def register_source(
        self,
        source: str,
        secret: Optional[str] = None,
        allowed_ips: Optional[List[str]] = None
    ) -> None:
        """Convenience method to register a webhook source."""
        self._registered_sources[source] = {
            "secret": secret,
            "allowed_ips": allowed_ips,
            "registered_at": datetime.utcnow().isoformat()
        }

    def create_fastapi_router(self):
        """
        Create a FastAPI router for webhook endpoints.

        Usage:
            webhook = WebhookConnector()
            app.include_router(webhook.create_fastapi_router())
        """
        try:
            from fastapi import APIRouter, Request, HTTPException

            router = APIRouter(prefix="/webhooks", tags=["webhooks"])

            @router.post("/{source}")
            async def receive_webhook(source: str, request: Request):
                """Receive webhook from external platform."""
                try:
                    payload = await request.json()
                except:
                    payload = {"raw": await request.body()}

                headers = dict(request.headers)
                client_ip = request.client.host if request.client else None

                result = await self.handle_webhook(
                    source=source,
                    payload=payload,
                    headers=headers,
                    client_ip=client_ip
                )

                if not result.get("success"):
                    raise HTTPException(
                        status_code=result.get("status_code", 400),
                        detail=result.get("error")
                    )

                return {"received": True, "event_id": result.get("event_id")}

            @router.get("/sources")
            async def list_sources():
                """List registered webhook sources."""
                return {"sources": list(self._registered_sources.keys())}

            return router

        except ImportError:
            logger.warning("FastAPI not installed, cannot create router")
            return None


# Singleton instance
_webhook_connector: Optional[WebhookConnector] = None


async def get_webhook_connector() -> WebhookConnector:
    """Get or create singleton webhook connector."""
    global _webhook_connector
    if _webhook_connector is None:
        _webhook_connector = WebhookConnector()
        await _webhook_connector.start()
    return _webhook_connector


async def close_webhook_connector() -> None:
    """Close singleton webhook connector."""
    global _webhook_connector
    if _webhook_connector is not None:
        await _webhook_connector.stop()
        _webhook_connector = None
