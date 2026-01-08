"""
Comprehensive Test Suite for Cirkelline AgentOS
Tests all endpoints, concurrent requests, database connections, and system health
"""

import pytest
from fastapi.testclient import TestClient
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# Add parent directory to path to import my_os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from my_os import app, db, vector_db, agent_os

# Create test client
client = TestClient(app)


class TestBasicEndpoints:
    """Test all basic API endpoints"""

    def test_health_endpoint(self):
        """Test /health endpoint returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_metrics_endpoint(self):
        """Test /metrics endpoint returns system metrics"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data or "metrics" in data

    def test_health_detailed_endpoint(self):
        """Test /health endpoint returns component health"""
        response = client.get("/health")
        assert response.status_code in [200, 503]  # 503 if unhealthy is ok
        data = response.json()
        assert "status" in data

    def test_config_endpoint(self):
        """Test /config endpoint returns configuration"""
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "service" in data

    def test_agents_list_endpoint(self):
        """Test /agents endpoint returns agent list"""
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)

    def test_teams_list_endpoint(self):
        """Test /teams endpoint returns team list"""
        response = client.get("/teams")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)


class TestConcurrency:
    """Test system handles concurrent requests"""

    def test_10_concurrent_health_checks(self):
        """Test 10 concurrent health check requests"""
        def make_request():
            response = client.get("/health")
            return response.status_code == 200

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]

        # All requests should succeed
        assert all(results), "Some concurrent requests failed"

    def test_50_concurrent_requests(self):
        """Test 50 concurrent requests to stress test connection pool"""
        def make_request():
            response = client.get("/health")
            return response.status_code in [200, 503]

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in as_completed(futures)]
        duration = time.time() - start_time

        # All requests should complete
        assert all(results), "Some requests failed"
        # Should complete reasonably fast (under 10 seconds)
        assert duration < 10, f"50 requests took too long: {duration}s"

    def test_mixed_endpoint_concurrent_requests(self):
        """Test concurrent requests to different endpoints"""
        endpoints = ["/health", "/metrics", "/config", "/agents", "/teams"]

        def make_request(endpoint):
            response = client.get(endpoint)
            return response.status_code in [200, 503]

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, endpoints[i % len(endpoints)])
                      for i in range(30)]
            results = [future.result() for future in as_completed(futures)]

        # At least 90% should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.9, f"Success rate too low: {success_rate:.2%}"


class TestPerformance:
    """Test response time performance"""

    def test_health_response_time(self):
        """Test /health responds quickly"""
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        # Should respond in under 100ms
        assert duration < 0.1, f"Response too slow: {duration:.3f}s"

    def test_metrics_response_time(self):
        """Test /metrics responds quickly"""
        start = time.time()
        response = client.get("/metrics")
        duration = time.time() - start

        assert response.status_code == 200
        # Should respond in under 200ms
        assert duration < 0.2, f"Response too slow: {duration:.3f}s"

    def test_average_response_time(self):
        """Test average response time over 10 requests"""
        times = []
        for _ in range(10):
            start = time.time()
            response = client.get("/health")
            duration = time.time() - start
            times.append(duration)
            assert response.status_code == 200

        avg_time = sum(times) / len(times)
        # Average should be under 50ms
        assert avg_time < 0.05, f"Average response time too slow: {avg_time:.3f}s"


class TestSystemConfiguration:
    """Test system is configured correctly"""

    def test_agentos_has_agents(self):
        """Test AgentOS has agents configured"""
        assert len(agent_os.agents) > 0, "No agents configured"
        assert len(agent_os.agents) >= 4, f"Expected at least 4 agents, got {len(agent_os.agents)}"

    def test_agentos_has_teams(self):
        """Test AgentOS has teams configured"""
        assert len(agent_os.teams) > 0, "No teams configured"
        assert len(agent_os.teams) >= 3, f"Expected at least 3 teams, got {len(agent_os.teams)}"

    def test_database_configured(self):
        """Test database is configured"""
        assert db is not None, "Database not configured"
        assert db.db_url is not None, "Database URL not set"

    def test_vector_db_configured(self):
        """Test vector database is configured"""
        assert vector_db is not None, "Vector database not configured"


class TestErrorHandling:
    """Test error handling"""

    def test_404_on_invalid_endpoint(self):
        """Test 404 returned for invalid endpoints"""
        response = client.get("/this-endpoint-does-not-exist")
        assert response.status_code == 404

    def test_404_on_invalid_agent(self):
        """Test 404 for non-existent agent"""
        response = client.get("/agents/nonexistent-agent-id")
        assert response.status_code == 404

    def test_404_on_invalid_team(self):
        """Test 404 for non-existent team"""
        response = client.get("/teams/nonexistent-team-id")
        assert response.status_code == 404


class TestStressTest:
    """Stress tests for production readiness"""

    def test_sustained_load(self):
        """Test system handles sustained load (100 requests)"""
        success_count = 0
        start_time = time.time()

        for _ in range(100):
            response = client.get("/health")
            if response.status_code == 200:
                success_count += 1

        duration = time.time() - start_time
        success_rate = success_count / 100

        # At least 95% success rate
        assert success_rate >= 0.95, f"Success rate too low: {success_rate:.2%}"
        # Should complete in reasonable time (under 30 seconds)
        assert duration < 30, f"100 requests took too long: {duration:.2f}s"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "stress: marks tests as stress tests")


# Mark slow tests
pytest.mark.slow(TestStressTest.test_sustained_load)
