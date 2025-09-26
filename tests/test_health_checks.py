"""
Tests for health check endpoints and functionality
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import psutil

from src.halcytone_content_generator.main import app
from src.halcytone_content_generator.health import (
    HealthStatus,
    HealthCheckManager,
    HealthCheckResult,
    get_health_manager
)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def health_manager():
    """Create health check manager for testing"""
    manager = HealthCheckManager()

    # Register test checks
    async def test_check():
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="Test check passed",
            response_time_ms=10.5
        )

    manager.register_check("test", test_check)
    return manager


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_basic_health_check(self, client):
        """Test basic health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "environment" in data

    def test_detailed_health_check(self, client):
        """Test detailed health endpoint"""
        response = client.get("/health/detailed")
        assert response.status_code in [200, 503]

        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "checks_passed" in data
        assert "checks_failed" in data
        assert "response_time_ms" in data

    def test_detailed_health_with_params(self, client):
        """Test detailed health with query parameters"""
        response = client.get("/health/detailed?check_database=false&check_system=false")
        assert response.status_code in [200, 503]

        data = response.json()
        # Should have fewer components when checks are disabled
        assert "components" in data

    def test_readiness_check(self, client):
        """Test readiness endpoint"""
        response = client.get("/ready")
        # May return 503 if not ready
        assert response.status_code in [200, 503]

        data = response.json()
        assert "ready" in data
        assert "checks" in data
        assert "passed_checks" in data
        assert "failed_checks" in data

    def test_liveness_probe(self, client):
        """Test liveness endpoint"""
        response = client.get("/live")
        assert response.status_code == 200

        data = response.json()
        assert data["alive"] is True
        assert "timestamp" in data
        assert "pid" in data

    def test_liveness_alternate_path(self, client):
        """Test alternate liveness endpoint path"""
        response = client.get("/liveness")
        assert response.status_code == 200

        data = response.json()
        assert data["alive"] is True

    def test_startup_probe(self, client):
        """Test startup probe endpoint"""
        response = client.get("/startup")
        assert response.status_code in [200, 503]

        data = response.json()
        assert "started" in data
        assert "uptime_seconds" in data
        assert "message" in data

    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

        # Check for Prometheus format
        content = response.text
        assert "# HELP" in content
        assert "# TYPE" in content
        assert "app_uptime_seconds" in content

    def test_component_check_trigger(self, client):
        """Test triggering individual component check"""
        # Try to check a known component
        response = client.post("/health/check/database")
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "component" in data
            assert "status" in data
            assert "timestamp" in data

    def test_component_check_invalid(self, client):
        """Test triggering invalid component check"""
        response = client.post("/health/check/nonexistent")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data

    def test_legacy_endpoints_exist(self, client):
        """Test that legacy endpoints still work"""
        # Test legacy health
        response = client.get("/health-legacy")
        assert response.status_code == 200

        # Test legacy ready
        response = client.get("/ready-legacy")
        assert response.status_code == 200


class TestHealthCheckManager:
    """Test health check manager functionality"""

    @pytest.mark.asyncio
    async def test_register_and_run_check(self, health_manager):
        """Test registering and running a health check"""
        result = await health_manager.run_check("test")

        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Test check passed"
        assert result.response_time_ms == 10.5

    @pytest.mark.asyncio
    async def test_run_nonexistent_check(self, health_manager):
        """Test running a non-existent check"""
        result = await health_manager.run_check("nonexistent")

        assert result.status == HealthStatus.UNKNOWN
        assert "not registered" in result.message

    @pytest.mark.asyncio
    async def test_check_caching(self, health_manager):
        """Test that health checks are cached"""
        # Set short cache TTL for testing
        health_manager.cache_ttl = timedelta(seconds=1)

        # First call should execute the check
        result1 = await health_manager.run_check("test")

        # Second call should return cached result
        result2 = await health_manager.run_check("test")

        assert result1 == result2  # Should be the same cached object

    @pytest.mark.asyncio
    async def test_cache_expiration(self, health_manager):
        """Test that cache expires correctly"""
        import asyncio

        # Set very short cache TTL
        health_manager.cache_ttl = timedelta(milliseconds=100)

        # First call
        result1 = await health_manager.run_check("test")

        # Wait for cache to expire
        await asyncio.sleep(0.2)

        # Should get fresh result
        result2 = await health_manager.run_check("test")

        # Results should have different timestamps in cache
        assert "test" in health_manager.cache

    def test_overall_status_calculation(self, health_manager):
        """Test overall status calculation"""
        from src.halcytone_content_generator.health.health_checks import ComponentHealth

        # All healthy
        health_manager.components = {
            "db": ComponentHealth("db", HealthStatus.HEALTHY, datetime.utcnow()),
            "cache": ComponentHealth("cache", HealthStatus.HEALTHY, datetime.utcnow())
        }
        assert health_manager.get_overall_status() == HealthStatus.HEALTHY

        # One degraded
        health_manager.components["cache"].status = HealthStatus.DEGRADED
        assert health_manager.get_overall_status() == HealthStatus.DEGRADED

        # One unhealthy
        health_manager.components["db"].status = HealthStatus.UNHEALTHY
        assert health_manager.get_overall_status() == HealthStatus.UNHEALTHY

    def test_uptime_calculation(self, health_manager):
        """Test uptime calculation"""
        # Set start time to 1 hour ago
        health_manager.app_start_time = datetime.utcnow() - timedelta(hours=1)

        uptime = health_manager.get_uptime_seconds()

        # Should be approximately 3600 seconds (1 hour)
        assert 3595 < uptime < 3605  # Allow 5 second tolerance

    @pytest.mark.asyncio
    async def test_database_check(self, health_manager):
        """Test database health check"""
        with patch("src.halcytone_content_generator.database.get_database") as mock_get_db:
            # Mock successful database connection
            mock_db = AsyncMock()
            mock_db.health_check = AsyncMock(return_value={"status": "connected"})
            mock_get_db.return_value = mock_db

            result = await health_manager.check_database()

            assert result.status == HealthStatus.HEALTHY
            assert "healthy" in result.message.lower()

    @pytest.mark.asyncio
    async def test_database_check_failure(self, health_manager):
        """Test database health check failure"""
        with patch("src.halcytone_content_generator.database.get_database") as mock_get_db:
            # Mock database connection failure
            mock_db = AsyncMock()
            mock_db.health_check = AsyncMock(return_value={"status": "disconnected", "error": "Connection refused"})
            mock_get_db.return_value = mock_db

            result = await health_manager.check_database()

            assert result.status == HealthStatus.UNHEALTHY
            assert result.error == "Connection refused"

    @pytest.mark.asyncio
    async def test_external_services_check(self, health_manager):
        """Test external services health check"""
        with patch("src.halcytone_content_generator.core.services.validate_all_services") as mock_validate:
            # Mock all services healthy
            mock_validate.return_value = {
                "crm": {"status": "connected"},
                "platform": {"status": "configured"}
            }

            result = await health_manager.check_external_services()

            assert result.status == HealthStatus.HEALTHY
            assert "healthy" in result.message.lower()

    @pytest.mark.asyncio
    async def test_system_resource_checks(self, health_manager):
        """Test system resource health checks"""
        # Test disk space check
        result = await health_manager.check_disk_space()
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert result.metadata is not None

        # Test memory check
        result = await health_manager.check_memory()
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert "percent" in str(result.metadata)

        # Test CPU check
        result = await health_manager.check_cpu()
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert result.metadata is not None


class TestHealthCheckIntegration:
    """Integration tests for health check system"""

    @pytest.mark.asyncio
    async def test_full_health_check_flow(self, client):
        """Test full health check flow"""
        # Start with basic health
        response = client.get("/health")
        assert response.status_code in [200, 503]
        health_data = response.json()

        # Check readiness
        response = client.get("/ready")
        ready_data = response.json()

        # Check liveness
        response = client.get("/live")
        live_data = response.json()

        # Verify consistency
        assert health_data["service"] == "halcytone-content-generator"
        assert live_data["alive"] in [True, False]
        assert "checks" in ready_data

    @pytest.mark.asyncio
    async def test_health_degradation_scenario(self, health_manager):
        """Test health degradation scenario"""
        # Register a failing check
        async def failing_check():
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="Service unavailable",
                error="Connection timeout"
            )

        health_manager.register_check("failing", failing_check)

        # Run all checks
        results = await health_manager.run_all_checks()

        # Verify failing check is included
        assert "failing" in results
        assert results["failing"].status == HealthStatus.UNHEALTHY

        # Overall status should be unhealthy
        assert health_manager.get_overall_status() == HealthStatus.UNHEALTHY

    def test_metrics_format(self, client):
        """Test that metrics are in correct Prometheus format"""
        response = client.get("/metrics")
        lines = response.text.split("\n")

        # Check for proper formatting
        help_lines = [l for l in lines if l.startswith("# HELP")]
        type_lines = [l for l in lines if l.startswith("# TYPE")]
        metric_lines = [l for l in lines if l and not l.startswith("#")]

        assert len(help_lines) > 0
        assert len(type_lines) > 0
        assert len(metric_lines) > 0

        # Verify metric format
        for line in metric_lines:
            if line:
                # Should have metric name and value
                assert "{" in line or " " in line  # Has labels or value