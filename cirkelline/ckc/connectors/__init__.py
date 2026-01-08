"""
CKC Connectors
==============

Platform connectors for integrating external systems with CKC.

Connectors provide a standardized interface for:
- Receiving events from platforms
- Sending commands to platforms
- Health monitoring
- Event routing

Available Connectors:
    - InternalConnector: CKC message bus integration
    - HTTPConnector: Generic HTTP/REST platform integration
    - CosmicLibraryConnector: Cosmic Library platform
    - LibAdminConnector: lib-admin platform
    - CLAConnector: Cirkelline Local Agent
    - WebhookConnector: Inbound webhook receiver

Usage:
    from cirkelline.ckc.connectors import (
        ConnectorRegistry,
        get_connector_registry,
        CosmicLibraryConnector
    )

    # Register connector
    registry = await get_connector_registry()
    registry.register(CosmicLibraryConnector())

    # Start all
    await registry.start_all()
"""

from .base import (
    CKCConnector,
    ConnectorConfig,
    ConnectorStatus,
    ConnectorCapability,
    ConnectorEvent,
    ConnectorHealthStatus,
    ActionResult,
)

from .internal_connector import (
    InternalConnector,
    get_internal_connector,
    close_internal_connector,
)

from .http_connector import (
    HTTPConnector,
    HTTPConnectorConfig,
    CosmicLibraryConnector,
    LibAdminConnector,
    CLAConnector,
)

from .webhook_connector import (
    WebhookConnector,
    WebhookConfig,
    WebhookReceiver,
    get_webhook_connector,
    close_webhook_connector,
)

__all__ = [
    # Base classes
    "CKCConnector",
    "ConnectorConfig",
    "ConnectorStatus",
    "ConnectorCapability",
    "ConnectorEvent",
    "ConnectorHealthStatus",
    "ActionResult",
    # Internal
    "InternalConnector",
    "get_internal_connector",
    "close_internal_connector",
    # HTTP
    "HTTPConnector",
    "HTTPConnectorConfig",
    "CosmicLibraryConnector",
    "LibAdminConnector",
    "CLAConnector",
    # Webhook
    "WebhookConnector",
    "WebhookConfig",
    "WebhookReceiver",
    "get_webhook_connector",
    "close_webhook_connector",
]
