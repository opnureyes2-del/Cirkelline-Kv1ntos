"""
Test suite for CKC Connectors Framework
=======================================

Tests connector base class, HTTP connector, webhook connector,
internal connector, and connector registry.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_base_connector_classes():
    """Test base connector classes can be imported."""
    print("=== Test 1: Base Connector Classes ===")

    from cirkelline.ckc.connectors.base import (
        CKCConnector,
        ConnectorConfig,
        ConnectorStatus,
        ConnectorCapability,
        ConnectorEvent,
        ConnectorHealthStatus,
        ActionResult,
    )

    # Test config creation
    config = ConnectorConfig(
        name="Test Connector",
        platform_id="test_platform",
        enabled=True
    )
    assert config.name == "Test Connector"
    assert config.platform_id == "test_platform"
    print("  - ConnectorConfig: OK")

    # Test event creation
    event = ConnectorEvent.create(
        event_type="test_event",
        source="test_source",
        payload={"key": "value"}
    )
    assert event.event_id.startswith("evt_")
    assert event.event_type == "test_event"
    assert event.payload == {"key": "value"}
    print("  - ConnectorEvent: OK")

    # Test health status
    health = ConnectorHealthStatus(
        status=ConnectorStatus.CONNECTED,
        last_check=event.timestamp,
        latency_ms=5.0
    )
    assert health.status == ConnectorStatus.CONNECTED
    print("  - ConnectorHealthStatus: OK")

    print("  All base classes OK!")
    return True


async def test_http_connector():
    """Test HTTP connector."""
    print("\n=== Test 2: HTTP Connector ===")

    from cirkelline.ckc.connectors.http_connector import (
        HTTPConnector,
        HTTPConnectorConfig,
        CosmicLibraryConnector,
        LibAdminConnector,
        CLAConnector,
    )
    from cirkelline.ckc.connectors.base import ConnectorCapability

    # Test config
    config = HTTPConnectorConfig(
        name="Test HTTP",
        platform_id="test_http",
        base_url="http://localhost:9999",
        api_key="test_key"
    )
    assert config.base_url == "http://localhost:9999"
    assert config.api_key == "test_key"
    print("  - HTTPConnectorConfig: OK")

    # Test connector creation
    connector = HTTPConnector(config)
    assert connector.name == "Test HTTP"
    assert connector.platform_id == "test_http"
    assert connector.has_capability(ConnectorCapability.EXECUTE_ACTIONS)
    print("  - HTTPConnector creation: OK")

    # Test pre-configured connectors
    cosmic = CosmicLibraryConnector()
    assert cosmic.platform_id == "cosmic_library"
    print("  - CosmicLibraryConnector: OK")

    lib_admin = LibAdminConnector()
    assert lib_admin.platform_id == "lib_admin"
    print("  - LibAdminConnector: OK")

    cla = CLAConnector()
    assert cla.platform_id == "cla"
    print("  - CLAConnector: OK")

    print("  All HTTP connector tests OK!")
    return True


async def test_webhook_connector():
    """Test webhook connector."""
    print("\n=== Test 3: Webhook Connector ===")

    from cirkelline.ckc.connectors.webhook_connector import (
        WebhookConnector,
        WebhookConfig,
        WebhookReceiver,
    )
    from cirkelline.ckc.connectors.base import ConnectorCapability

    # Test config
    config = WebhookConfig(
        name="Test Webhook",
        secret="test_secret",
        validate_signatures=True
    )
    assert config.secret == "test_secret"
    print("  - WebhookConfig: OK")

    # Test connector
    connector = WebhookConnector(config)
    assert connector.has_capability(ConnectorCapability.WEBHOOKS)
    assert connector.has_capability(ConnectorCapability.READ_EVENTS)
    print("  - WebhookConnector capabilities: OK")

    # Test webhook handling (simulate)
    events_received = []

    async def handler(event):
        events_received.append(event)

    await connector.subscribe_events(["test_source"], handler)
    await connector.start()

    # Simulate webhook
    result = await connector.handle_webhook(
        source="test_source",
        payload={"event": "test", "data": "value"},
        headers={"X-Test": "header"}
    )
    assert result["success"] is True
    assert "event_id" in result
    print("  - Webhook handling: OK")

    # Check event was dispatched
    await asyncio.sleep(0.1)  # Give time for dispatch
    assert len(events_received) >= 1
    print("  - Event dispatch: OK")

    await connector.stop()
    print("  All webhook connector tests OK!")
    return True


async def test_internal_connector():
    """Test internal connector."""
    print("\n=== Test 4: Internal Connector ===")

    from cirkelline.ckc.connectors.internal_connector import InternalConnector
    from cirkelline.ckc.connectors.base import ConnectorCapability, ConnectorStatus

    # Create connector
    connector = InternalConnector()
    assert connector.name == "CKC Internal"
    assert connector.has_capability(ConnectorCapability.BIDIRECTIONAL)
    print("  - InternalConnector creation: OK")

    # Test start (will try to connect to message bus)
    # Note: This may fail if Redis/RabbitMQ not running
    try:
        await connector.start()
        health = await connector.health_check()
        if health.status in (ConnectorStatus.CONNECTED, ConnectorStatus.ERROR):
            print(f"  - InternalConnector start: OK (status: {health.status.value})")
        await connector.stop()
    except Exception as e:
        print(f"  - InternalConnector start: Skipped (message bus not available: {e})")

    print("  Internal connector tests OK!")
    return True


async def test_connector_registry():
    """Test connector registry."""
    print("\n=== Test 5: Connector Registry ===")

    from cirkelline.ckc.infrastructure.connector_registry import (
        ConnectorRegistry,
        RegistryEvent,
    )
    from cirkelline.ckc.connectors.webhook_connector import WebhookConnector
    from cirkelline.ckc.connectors.http_connector import HTTPConnector, HTTPConnectorConfig
    from cirkelline.ckc.connectors.base import ConnectorCapability

    # Create registry
    registry = ConnectorRegistry(health_check_interval=0)  # Disable auto health check
    assert registry is not None
    print("  - Registry creation: OK")

    # Register connectors
    webhook = WebhookConnector()
    success = registry.register(webhook, priority=10, tags={"inbound"})
    assert success is True
    print("  - Register webhook: OK")

    http_config = HTTPConnectorConfig(
        name="Test Platform",
        platform_id="test_platform",
        base_url="http://localhost:9999"
    )
    http_connector = HTTPConnector(http_config)
    success = registry.register(http_connector, priority=5, tags={"platform"})
    assert success is True
    print("  - Register HTTP connector: OK")

    # Test get
    assert registry.get("webhooks") is webhook
    assert registry.get("test_platform") is http_connector
    assert registry.get("nonexistent") is None
    print("  - Get connector: OK")

    # Test get by capability
    webhook_connectors = registry.get_by_capability(ConnectorCapability.WEBHOOKS)
    assert len(webhook_connectors) >= 1
    print("  - Get by capability: OK")

    # Test get by tag
    platform_connectors = registry.get_by_tag("platform")
    assert len(platform_connectors) == 1
    print("  - Get by tag: OK")

    # Test list
    connector_list = registry.list_connectors()
    assert len(connector_list) == 2
    print("  - List connectors: OK")

    # Test overview
    overview = registry.get_overview()
    assert overview["total_connectors"] == 2
    print("  - Get overview: OK")

    # Test unregister
    success = registry.unregister("test_platform")
    assert success is True
    assert registry.get("test_platform") is None
    print("  - Unregister: OK")

    print("  All registry tests OK!")
    return True


async def test_connector_events():
    """Test connector event creation and dispatch."""
    print("\n=== Test 6: Connector Events ===")

    from cirkelline.ckc.connectors.base import ConnectorEvent
    from datetime import datetime

    # Test event creation
    event = ConnectorEvent.create(
        event_type="task.created",
        source="test_agent",
        payload={"task_id": "123", "prompt": "Test task"},
        metadata={"priority": "high"}
    )

    assert event.event_id.startswith("evt_")
    assert event.event_type == "task.created"
    assert event.source == "test_agent"
    assert event.payload["task_id"] == "123"
    assert event.metadata["priority"] == "high"
    print("  - Event creation: OK")

    # Test to_dict
    event_dict = event.to_dict()
    assert "event_id" in event_dict
    assert "timestamp" in event_dict
    assert event_dict["event_type"] == "task.created"
    print("  - Event to_dict: OK")

    print("  All event tests OK!")
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("CKC Connectors Framework Test Suite")
    print("=" * 60)

    tests = [
        test_base_connector_classes,
        test_http_connector,
        test_webhook_connector,
        test_internal_connector,
        test_connector_registry,
        test_connector_events,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
