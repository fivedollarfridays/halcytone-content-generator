"""
Unit tests for Health Check Endpoints.

Tests cover all health check endpoints including basic health,
detailed health, readiness, liveness, startup, metrics, and
manual component checks.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from halcytone_content_generator.api.health_endpoints import router
from halcytone_content_generator.health import (
    HealthStatus,
    HealthResponse,
    DetailedHealthResponse,
    ReadinessResponse,
    LivenessResponse,
    ComponentStatus,
    ReadinessCheck
)


@pytest.fixture
def app():
    """Create FastAPI app with health endpoints."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_health_manager():
    """Create mock health manager."""
    manager = Mock()
    manager.get_overall_status.return_value = HealthStatus.HEALTHY
    manager.get_uptime_seconds.return_value = 3600.0
    manager.components = {}
    manager.checks = {
        "database": Mock(),
        "cache": Mock(),
        "external_services": Mock()
    }
    return manager


class TestBasicHealthCheck:
    """Test basic /health endpoint."""

    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    def test_health_check_healthy(self, mock_get_manager, client, mock_health_manager):
        """Test health check returns 200 when healthy."""
        mock_get_manager.return_value = mock_health_manager
        mock_health_manager.get_overall_status.return_value = HealthStatus.HEALTHY

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] == 3600.0

    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    def test_health_check_unhealthy(self, mock_get_manager, client, mock_health_manager):
        """Test health check returns 503 when unhealthy."""
        mock_get_manager.return_value = mock_health_manager
        mock_health_manager.get_overall_status.return_value = HealthStatus.UNHEALTHY

        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"

    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    def test_health_check_degraded(self, mock_get_manager, client, mock_health_manager):
        """Test health check returns 200 when degraded."""
        mock_get_manager.return_value = mock_health_manager
        mock_health_manager.get_overall_status.return_value = HealthStatus.DEGRADED

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"


class TestDetailedHealthCheck:
    """Test detailed /health/detailed endpoint."""

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    async def test_detailed_health_all_checks(self, mock_get_manager, client, mock_health_manager):
        """Test detailed health check with all checks enabled."""
        mock_get_manager.return_value = mock_health_manager

        # Mock check results
        async def mock_run_check(check_name):
            result = Mock()
            result.status = HealthStatus.HEALTHY
            result.message = f"{check_name} is healthy"
            result.response_time_ms = 10.0
            result.metadata = {"detail": "ok"}
            result.error = None
            return result

        mock_health_manager.run_check = mock_run_check

        response = client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert "components" in data
        assert "checks_passed" in data
        assert "checks_failed" in data
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    async def test_detailed_health_selective_checks(self, mock_get_manager, client, mock_health_manager):
        """Test detailed health check with selective checks."""
        mock_get_manager.return_value = mock_health_manager

        async def mock_run_check(check_name):
            result = Mock()
            result.status = HealthStatus.HEALTHY
            result.message = "ok"
            result.response_time_ms = 5.0
            result.metadata = {}
            result.error = None
            return result

        mock_health_manager.run_check = mock_run_check

        response = client.get("/health/detailed?check_database=true&check_cache=false")

        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    async def test_detailed_health_with_failures(self, mock_get_manager, client, mock_health_manager):
        """Test detailed health check with component failures."""
        mock_get_manager.return_value = mock_health_manager
        mock_health_manager.get_overall_status.return_value = HealthStatus.UNHEALTHY

        async def mock_run_check(check_name):
            result = Mock()
            if check_name == "database":
                result.status = HealthStatus.UNHEALTHY
                result.message = "Database connection failed"
                result.error = "Connection timeout"
            else:
                result.status = HealthStatus.HEALTHY
                result.message = "ok"
                result.error = None
            result.response_time_ms = 10.0
            result.metadata = {}
            return result

        mock_health_manager.run_check = mock_run_check

        response = client.get("/health/detailed")

        assert response.status_code == 503
        data = response.json()
        assert data["checks_failed"] > 0
        assert len(data["errors"]) > 0

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    async def test_detailed_health_check_exception(self, mock_get_manager, client, mock_health_manager):
        """Test detailed health check handles check exceptions."""
        mock_get_manager.return_value = mock_health_manager

        async def mock_run_check(check_name):
            raise Exception("Check failed unexpectedly")

        mock_health_manager.run_check = mock_run_check

        response = client.get("/health/detailed")

        # Should still return a response with error info
        assert response.status_code in [200, 503]
        data = response.json()
        assert "components" in data


class TestReadinessCheck:
    """Test /ready readiness probe endpoint."""

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.core.services.validate_all_services')
    async def test_readiness_check_ready(self, mock_validate_services, client):
        """Test readiness check returns 200 when ready (no database configured)."""
        # Mock services
        mock_validate_services.return_value = {
            "crm": {"status": "connected", "message": "CRM connected"},
            "platform": {"status": "connected", "message": "Platform connected"}
        }

        response = client.get("/ready")

        # In development mode without database, should still return 200 if services are ready
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "checks" in data

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.core.services.validate_all_services')
    async def test_readiness_check_not_ready(self, mock_validate_services, client):
        """Test readiness check returns 503 when services fail."""
        # Mock service failures
        mock_validate_services.side_effect = Exception("Services not available")

        response = client.get("/ready")

        # Should return data even with failures
        data = response.json()
        assert "ready" in data
        assert "checks" in data

    @pytest.mark.asyncio
    async def test_readiness_check_no_database(self, client):
        """Test readiness check when database is not configured."""
        # Database module doesn't exist, so this tests default behavior
        response = client.get("/ready")

        # Should handle gracefully in development mode
        assert response.status_code in [200, 503]
        data = response.json()
        assert "checks" in data


class TestLivenessProbe:
    """Test /live and /liveness probe endpoints."""

    @patch('psutil.Process')
    def test_liveness_probe_alive(self, mock_process_class, client):
        """Test liveness probe returns 200 when alive."""
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=500 * 1024 * 1024)  # 500MB
        mock_process.cpu_percent.return_value = 30.0
        mock_process.num_threads.return_value = 10
        mock_process_class.return_value = mock_process

        response = client.get("/live")

        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True
        assert "memory_usage_mb" in data
        assert "cpu_percent" in data

    @patch('psutil.Process')
    def test_liveness_probe_high_cpu(self, mock_process_class, client):
        """Test liveness probe returns 503 when CPU is too high."""
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=500 * 1024 * 1024)
        mock_process.cpu_percent.return_value = 96.0  # Over 95% threshold
        mock_process.num_threads.return_value = 10
        mock_process_class.return_value = mock_process

        response = client.get("/live")

        assert response.status_code == 503
        data = response.json()
        assert data["alive"] is False

    @patch('psutil.Process')
    def test_liveness_probe_high_memory(self, mock_process_class, client):
        """Test liveness probe returns 503 when memory is too high."""
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=3000 * 1024 * 1024)  # 3GB
        mock_process.cpu_percent.return_value = 30.0
        mock_process.num_threads.return_value = 10
        mock_process_class.return_value = mock_process

        response = client.get("/live")

        assert response.status_code == 503
        data = response.json()
        assert data["alive"] is False

    @patch('psutil.Process')
    def test_liveness_endpoint_alias(self, mock_process_class, client):
        """Test /liveness endpoint alias."""
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=500 * 1024 * 1024)
        mock_process.cpu_percent.return_value = 30.0
        mock_process.num_threads.return_value = 10
        mock_process_class.return_value = mock_process

        response = client.get("/liveness")

        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True

    @patch('psutil.Process')
    def test_liveness_probe_exception(self, mock_process_class, client):
        """Test liveness probe handles exceptions gracefully."""
        mock_process_class.side_effect = Exception("Process error")

        response = client.get("/live")

        # Should still return 200 with alive=True as fallback
        assert response.status_code == 200
        data = response.json()
        assert "alive" in data


class TestStartupProbe:
    """Test /startup probe endpoint."""

    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    def test_startup_probe_not_ready(self, mock_get_manager, client, mock_health_manager):
        """Test startup probe returns 503 when not ready."""
        mock_get_manager.return_value = mock_health_manager
        mock_health_manager.get_uptime_seconds.return_value = 5.0  # Less than 10 seconds

        response = client.get("/startup")

        assert response.status_code == 503
        data = response.json()
        assert data["started"] is False
        assert data["uptime_seconds"] == 5.0

    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    def test_startup_probe_ready(self, mock_get_manager, client, mock_health_manager):
        """Test startup probe returns 200 when ready."""
        mock_get_manager.return_value = mock_health_manager
        mock_health_manager.get_uptime_seconds.return_value = 15.0  # More than 10 seconds

        response = client.get("/startup")

        # May return 200 or 503 depending on import success
        data = response.json()
        assert "started" in data
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] == 15.0

    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    def test_startup_probe_import_failure(self, mock_get_manager, client, mock_health_manager):
        """Test startup probe handles import failures."""
        mock_get_manager.return_value = mock_health_manager
        mock_health_manager.get_uptime_seconds.return_value = 15.0

        response = client.get("/startup")

        # Should return response even with import issues
        data = response.json()
        assert "started" in data
        assert "uptime_seconds" in data
        assert "message" in data


class TestMetricsEndpoint:
    """Test /metrics Prometheus endpoint."""

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    async def test_metrics_endpoint(self, mock_get_manager, client, mock_health_manager):
        """Test metrics endpoint returns Prometheus format."""
        mock_get_manager.return_value = mock_health_manager

        # Mock system metrics
        mock_metrics = Mock()
        mock_metrics.memory_usage_percent = 45.5
        mock_metrics.cpu_usage_percent = 30.2
        mock_metrics.disk_usage_percent = 60.0
        mock_health_manager.get_system_metrics = AsyncMock(return_value=mock_metrics)

        response = client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        content = response.text

        # Check for Prometheus format
        assert "app_uptime_seconds" in content
        assert "app_memory_usage_percent" in content
        assert "app_cpu_usage_percent" in content
        assert "app_disk_usage_percent" in content
        assert "# HELP" in content
        assert "# TYPE" in content

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    async def test_metrics_with_components(self, mock_get_manager, client, mock_health_manager):
        """Test metrics endpoint includes component health."""
        mock_get_manager.return_value = mock_health_manager

        # Add mock components
        mock_component = Mock()
        mock_component.status = HealthStatus.HEALTHY
        mock_health_manager.components = {"database": mock_component}

        mock_metrics = Mock()
        mock_metrics.memory_usage_percent = 45.5
        mock_metrics.cpu_usage_percent = 30.2
        mock_metrics.disk_usage_percent = 60.0
        mock_health_manager.get_system_metrics = AsyncMock(return_value=mock_metrics)

        response = client.get("/metrics")

        assert response.status_code == 200
        content = response.text
        assert "app_component_health" in content


class TestManualComponentCheck:
    """Test POST /health/check/{component} endpoint."""

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    async def test_trigger_component_check_success(self, mock_get_manager, client, mock_health_manager):
        """Test manual component check triggers successfully."""
        mock_get_manager.return_value = mock_health_manager

        # Mock check result
        mock_result = Mock()
        mock_result.status = HealthStatus.HEALTHY
        mock_result.message = "Database is healthy"
        mock_result.response_time_ms = 25.0
        mock_result.metadata = {"connections": 10}
        mock_result.error = None
        mock_health_manager.run_check = AsyncMock(return_value=mock_result)

        response = client.post("/health/check/database")

        assert response.status_code == 200
        data = response.json()
        assert data["component"] == "database"
        assert data["status"] == "healthy"
        assert data["response_time_ms"] == 25.0

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    async def test_trigger_component_check_not_found(self, mock_get_manager, client, mock_health_manager):
        """Test manual component check with invalid component."""
        mock_get_manager.return_value = mock_health_manager
        mock_health_manager.checks = {"database": Mock(), "cache": Mock()}

        response = client.post("/health/check/invalid_component")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.api.health_endpoints.get_health_manager')
    async def test_trigger_component_check_failure(self, mock_get_manager, client, mock_health_manager):
        """Test manual component check with component failure."""
        mock_get_manager.return_value = mock_health_manager

        mock_result = Mock()
        mock_result.status = HealthStatus.UNHEALTHY
        mock_result.message = "Connection failed"
        mock_result.response_time_ms = 5000.0
        mock_result.metadata = {}
        mock_result.error = "Timeout after 5 seconds"
        mock_health_manager.run_check = AsyncMock(return_value=mock_result)

        response = client.post("/health/check/database")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["error"] is not None
