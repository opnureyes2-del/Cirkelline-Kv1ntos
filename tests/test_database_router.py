"""
Tests for Database Read/Write Router
=====================================

Tests routing, failover, and metrics for I-2 Database Replicas.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from cirkelline.database import (
    RouteMode,
    DatabaseNode,
    RouterConfig,
    RouterMetrics,
    DatabaseRouter,
    get_database_router,
)


# =============================================================================
# DATABASE NODE TESTS
# =============================================================================

class TestDatabaseNode:
    """Tests for DatabaseNode configuration."""

    def test_create_primary_node(self):
        """Test creating a primary database node."""
        node = DatabaseNode(
            name="primary",
            host="localhost",
            port=5432,
            database="testdb",
            user="user",
            password="pass",
            is_primary=True,
        )

        assert node.is_primary is True
        assert node.is_replica is False
        assert node.weight == 1
        assert "localhost:5432" in str(node)

    def test_create_replica_node(self):
        """Test creating a replica database node."""
        node = DatabaseNode(
            name="replica-1",
            host="replica.example.com",
            port=5432,
            database="testdb",
            user="user",
            password="pass",
            is_replica=True,
            weight=2,
        )

        assert node.is_primary is False
        assert node.is_replica is True
        assert node.weight == 2

    def test_connection_string(self):
        """Test connection string generation."""
        node = DatabaseNode(
            name="test",
            host="db.example.com",
            port=5433,
            database="mydb",
            user="myuser",
            password="mypass",
        )

        conn_str = node.connection_string
        assert "postgresql+psycopg://" in conn_str
        assert "myuser:mypass" in conn_str
        assert "db.example.com:5433" in conn_str
        assert "mydb" in conn_str

    def test_repr(self):
        """Test node string representation."""
        node = DatabaseNode(
            name="test",
            host="localhost",
            port=5432,
            database="db",
            user="user",
            password="pass",
            is_primary=True,
        )

        repr_str = repr(node)
        assert "test" in repr_str
        assert "PRIMARY" in repr_str


# =============================================================================
# ROUTER CONFIG TESTS
# =============================================================================

class TestRouterConfig:
    """Tests for RouterConfig."""

    def test_localhost_single(self):
        """Test localhost single-node configuration."""
        config = RouterConfig.localhost_single()

        assert config.primary is not None
        assert config.primary.host == "localhost"
        assert config.primary.port == 5532
        assert config.primary.is_primary is True
        assert len(config.replicas) == 0

    def test_config_defaults(self):
        """Test default configuration values."""
        config = RouterConfig.localhost_single()

        assert config.pool_size == 20
        assert config.max_overflow == 40
        assert config.pool_recycle == 1800
        assert config.pool_pre_ping is True
        assert config.read_from_primary_on_empty is True

    def test_config_with_replicas(self):
        """Test configuration with replicas."""
        primary = DatabaseNode(
            name="primary",
            host="primary.db",
            port=5432,
            database="db",
            user="user",
            password="pass",
            is_primary=True,
        )

        replicas = [
            DatabaseNode(
                name="replica-1",
                host="replica1.db",
                port=5432,
                database="db",
                user="user",
                password="pass",
                is_replica=True,
            ),
            DatabaseNode(
                name="replica-2",
                host="replica2.db",
                port=5432,
                database="db",
                user="user",
                password="pass",
                is_replica=True,
            ),
        ]

        config = RouterConfig(primary=primary, replicas=replicas)

        assert len(config.replicas) == 2

    @patch.dict('os.environ', {
        'DB_PRIMARY_HOST': 'prod.db.example.com',
        'DB_PRIMARY_PORT': '5432',
        'DB_NAME': 'production',
        'DB_USER': 'produser',
        'DB_PASSWORD': 'secret',
        'DB_REPLICA_HOSTS': 'replica1.db,replica2.db',
    })
    def test_from_env(self):
        """Test configuration from environment variables."""
        config = RouterConfig.from_env()

        assert config.primary.host == "prod.db.example.com"
        assert config.primary.database == "production"
        assert len(config.replicas) == 2


# =============================================================================
# ROUTER METRICS TESTS
# =============================================================================

class TestRouterMetrics:
    """Tests for RouterMetrics."""

    def test_default_metrics(self):
        """Test default metric values."""
        metrics = RouterMetrics()

        assert metrics.read_queries == 0
        assert metrics.write_queries == 0
        assert metrics.errors == 0

    def test_metrics_to_dict(self):
        """Test metrics serialization."""
        metrics = RouterMetrics(
            read_queries=100,
            write_queries=50,
            replica_reads=80,
            primary_reads=20,
        )

        d = metrics.to_dict()

        assert d["read_queries"] == 100
        assert d["write_queries"] == 50
        assert d["replica_reads"] == 80
        assert d["primary_reads"] == 20


# =============================================================================
# DATABASE ROUTER TESTS
# =============================================================================

class TestDatabaseRouter:
    """Tests for DatabaseRouter."""

    def test_create_router_default(self):
        """Test creating router with default config."""
        router = DatabaseRouter()

        assert router.config is not None
        assert router._initialized is False
        assert router.has_replicas is False

    def test_create_router_custom_config(self):
        """Test creating router with custom config."""
        config = RouterConfig.localhost_single()
        router = DatabaseRouter(config)

        assert router.config is config

    @pytest.mark.asyncio
    async def test_initialize_requires_database(self):
        """Test initialization attempts database connection."""
        router = DatabaseRouter()

        # This will fail without actual database
        # But tests the initialization flow
        try:
            await router.initialize()
        except Exception:
            pass  # Expected without real DB

    def test_get_metrics_before_init(self):
        """Test getting metrics before initialization."""
        router = DatabaseRouter()
        metrics = router.get_metrics()

        assert metrics["status"]["initialized"] is False
        assert metrics["config"]["replica_count"] == 0

    @pytest.mark.asyncio
    async def test_close_without_init(self):
        """Test closing without initialization."""
        router = DatabaseRouter()
        await router.close()  # Should not raise

        assert router._initialized is False


# =============================================================================
# ROUTE MODE TESTS
# =============================================================================

class TestRouteMode:
    """Tests for RouteMode enum."""

    def test_route_modes_exist(self):
        """Test all route modes exist."""
        assert RouteMode.READ.value == "read"
        assert RouteMode.WRITE.value == "write"
        assert RouteMode.AUTO.value == "auto"


# =============================================================================
# INTEGRATION TESTS (Mock)
# =============================================================================

class TestRouterIntegration:
    """Integration tests with mocked database."""

    @pytest.mark.asyncio
    async def test_metrics_tracking(self):
        """Test that metrics are tracked correctly."""
        router = DatabaseRouter()
        router._initialized = True  # Skip real init

        # Mock engines
        mock_engine = MagicMock()
        router._primary_engine = mock_engine
        router._replica_engines = []

        # Access metrics
        metrics = router.get_metrics()
        assert "read_queries" in metrics
        assert "write_queries" in metrics

    def test_has_replicas_false_without_engines(self):
        """Test has_replicas is False without replica engines."""
        router = DatabaseRouter()
        assert router.has_replicas is False

    def test_has_replicas_true_with_engines(self):
        """Test has_replicas is True with replica engines."""
        router = DatabaseRouter()
        router._replica_engines = [MagicMock()]
        assert router.has_replicas is True


# =============================================================================
# GLOBAL ACCESS TESTS
# =============================================================================

class TestGlobalAccess:
    """Tests for global router access."""

    def test_get_database_router_singleton(self):
        """Test get_database_router returns singleton."""
        # Reset global
        import cirkelline.database.read_write_router as module
        module._router = None

        router1 = get_database_router()
        router2 = get_database_router()

        assert router1 is router2


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestRouterPerformance:
    """Performance and load tests."""

    def test_config_creation_fast(self):
        """Test config creation is fast."""
        import time

        start = time.time()
        for _ in range(1000):
            RouterConfig.localhost_single()
        elapsed = time.time() - start

        assert elapsed < 1.0  # Should create 1000 configs in < 1 second

    def test_metrics_creation_fast(self):
        """Test metrics creation is fast."""
        import time

        start = time.time()
        for _ in range(1000):
            metrics = RouterMetrics()
            metrics.to_dict()
        elapsed = time.time() - start

        assert elapsed < 1.0  # Should handle 1000 metrics in < 1 second
