"""
Unit tests for monitoring service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from src.halcytone_content_generator.services.monitoring import (
    MonitoringService, HealthStatus, EventType, MonitoringEvent
)
from src.halcytone_content_generator.config import Settings


class TestMonitoringService:
    """Test monitoring service functionality"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = Mock(spec=Settings)
        settings.SERVICE_NAME = "content-generator"
        settings.ENVIRONMENT = "test"
        settings.MONITORING_ENABLED = True
        return settings

    @pytest.fixture
    def monitoring_service(self, mock_settings):
        """Create monitoring service instance"""
        return MonitoringService(mock_settings)

    def test_service_initialization(self, mock_settings):
        """Test monitoring service initialization"""
        service = MonitoringService(mock_settings)

        assert service.service_name == "content-generator"
        assert service.environment == "test"
        assert service.enabled is True
        assert service.metrics is not None

    def test_health_status_enum(self):
        """Test HealthStatus enum values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_record_metric(self, monitoring_service):
        """Test recording metrics"""
        monitoring_service.record_metric("requests_total", 1, {"endpoint": "/test"})

        # Verify metric was recorded
        assert len(monitoring_service.metrics) > 0

    def test_record_performance_metric(self, monitoring_service):
        """Test recording performance metrics"""
        monitoring_service.record_performance_metric(
            operation="content_generation",
            duration_ms=150.5,
            success=True
        )

        # Should be recorded in metrics
        assert len(monitoring_service.metrics) > 0

    def test_get_health_status_healthy(self, monitoring_service):
        """Test health status when system is healthy"""
        status = monitoring_service.get_health_status()

        assert status.status == HealthStatus.HEALTHY
        assert status.timestamp is not None
        assert status.service_name == "content-generator"

    def test_get_health_status_with_dependencies(self, monitoring_service):
        """Test health status with dependency checks"""
        # Mock healthy dependencies
        with patch.object(monitoring_service, '_check_crm_health', return_value=True), \
             patch.object(monitoring_service, '_check_platform_health', return_value=True), \
             patch.object(monitoring_service, '_check_database_health', return_value=True):

            status = monitoring_service.get_health_status()

            assert status.status == HealthStatus.HEALTHY
            assert "crm" in status.dependencies
            assert "platform" in status.dependencies
            assert "database" in status.dependencies

    def test_get_health_status_degraded(self, monitoring_service):
        """Test health status when system is degraded"""
        # Mock one failing dependency
        with patch.object(monitoring_service, '_check_crm_health', return_value=False), \
             patch.object(monitoring_service, '_check_platform_health', return_value=True), \
             patch.object(monitoring_service, '_check_database_health', return_value=True):

            status = monitoring_service.get_health_status()

            assert status.status == HealthStatus.DEGRADED
            assert not status.dependencies["crm"]

    def test_get_health_status_unhealthy(self, monitoring_service):
        """Test health status when system is unhealthy"""
        # Mock multiple failing dependencies
        with patch.object(monitoring_service, '_check_crm_health', return_value=False), \
             patch.object(monitoring_service, '_check_platform_health', return_value=False), \
             patch.object(monitoring_service, '_check_database_health', return_value=True):

            status = monitoring_service.get_health_status()

            assert status.status == HealthStatus.UNHEALTHY

    def test_get_system_metrics(self, monitoring_service):
        """Test getting system metrics"""
        # Record some metrics first
        monitoring_service.record_metric("requests_total", 10)
        monitoring_service.record_metric("errors_total", 2)

        metrics = monitoring_service.get_system_metrics()

        assert metrics.timestamp is not None
        assert metrics.service_name == "content-generator"
        assert len(metrics.metrics) > 0

    def test_get_performance_summary(self, monitoring_service):
        """Test getting performance summary"""
        # Record some performance metrics
        monitoring_service.record_performance_metric("test_op", 100, True)
        monitoring_service.record_performance_metric("test_op", 200, True)
        monitoring_service.record_performance_metric("test_op", 150, False)

        summary = monitoring_service.get_performance_summary("test_op")

        assert summary["operation"] == "test_op"
        assert summary["total_requests"] == 3
        assert summary["success_count"] == 2
        assert summary["failure_count"] == 1
        assert summary["avg_duration_ms"] > 0

    def test_cleanup_old_metrics(self, monitoring_service):
        """Test cleanup of old metrics"""
        # Add some old metrics
        old_time = datetime.now() - timedelta(hours=25)  # Older than 24 hours
        monitoring_service.metrics.append({
            "timestamp": old_time,
            "name": "old_metric",
            "value": 1
        })

        monitoring_service.cleanup_old_metrics()

        # Old metrics should be removed
        assert len([m for m in monitoring_service.metrics if m["name"] == "old_metric"]) == 0

    def test_alert_on_threshold(self, monitoring_service):
        """Test alerting when threshold is exceeded"""
        with patch.object(monitoring_service, '_send_alert') as mock_alert:
            # Set error rate threshold
            monitoring_service.alert_thresholds["error_rate"] = 0.1  # 10%

            # Record metrics that exceed threshold
            for _ in range(9):
                monitoring_service.record_performance_metric("test", 100, True)
            for _ in range(2):
                monitoring_service.record_performance_metric("test", 100, False)

            monitoring_service._check_alert_thresholds()

            # Should have triggered an alert
            mock_alert.assert_called()

    def test_export_metrics_json(self, monitoring_service):
        """Test exporting metrics to JSON"""
        monitoring_service.record_metric("test_metric", 42)

        json_data = monitoring_service.export_metrics(format="json")

        assert json_data is not None
        data = json.loads(json_data)
        assert "metrics" in data
        assert "timestamp" in data

    def test_export_metrics_prometheus(self, monitoring_service):
        """Test exporting metrics to Prometheus format"""
        monitoring_service.record_metric("test_metric", 42, {"label": "value"})

        prometheus_data = monitoring_service.export_metrics(format="prometheus")

        assert prometheus_data is not None
        assert "test_metric" in prometheus_data

    @pytest.mark.asyncio
    async def test_async_health_check(self, monitoring_service):
        """Test async health check"""
        with patch.object(monitoring_service, '_async_check_dependencies') as mock_check:
            mock_check.return_value = {"crm": True, "platform": True}

            status = await monitoring_service.async_health_check()

            assert status.status == HealthStatus.HEALTHY
            mock_check.assert_called_once()

    def test_track_request_duration(self, monitoring_service):
        """Test request duration tracking"""
        with monitoring_service.track_request_duration("test_endpoint"):
            # Simulate some work
            import time
            time.sleep(0.01)

        # Should have recorded the duration
        assert len(monitoring_service.metrics) > 0

    def test_disabled_monitoring(self, mock_settings):
        """Test monitoring when disabled"""
        mock_settings.MONITORING_ENABLED = False
        service = MonitoringService(mock_settings)

        service.record_metric("test", 1)

        # No metrics should be recorded when disabled
        assert len(service.metrics) == 0


class TestPerformanceTracker:
    """Test performance tracker functionality"""

    def test_track_operation(self):
        """Test tracking operation performance"""
        tracker = PerformanceTracker()

        with tracker.track("test_operation"):
            import time
            time.sleep(0.01)

        metrics = tracker.get_metrics("test_operation")
        assert metrics["count"] == 1
        assert metrics["avg_duration"] > 0

    def test_track_multiple_operations(self):
        """Test tracking multiple operations"""
        tracker = PerformanceTracker()

        # Track same operation multiple times
        for _ in range(3):
            with tracker.track("test_op"):
                pass

        metrics = tracker.get_metrics("test_op")
        assert metrics["count"] == 3

    def test_track_failed_operation(self):
        """Test tracking failed operations"""
        tracker = PerformanceTracker()

        try:
            with tracker.track("test_op"):
                raise ValueError("Test error")
        except ValueError:
            pass

        metrics = tracker.get_metrics("test_op")
        assert metrics["count"] == 1
        assert metrics["failure_count"] == 1

    def test_get_all_metrics(self):
        """Test getting all tracked metrics"""
        tracker = PerformanceTracker()

        with tracker.track("op1"):
            pass
        with tracker.track("op2"):
            pass

        all_metrics = tracker.get_all_metrics()
        assert "op1" in all_metrics
        assert "op2" in all_metrics

    def test_reset_metrics(self):
        """Test resetting tracker metrics"""
        tracker = PerformanceTracker()

        with tracker.track("test"):
            pass

        tracker.reset()

        all_metrics = tracker.get_all_metrics()
        assert len(all_metrics) == 0


class TestSystemMetrics:
    """Test system metrics data structure"""

    def test_system_metrics_creation(self):
        """Test creating SystemMetrics instance"""
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            service_name="test-service",
            environment="test",
            metrics={"requests": 100, "errors": 5},
            performance_data={"avg_response_time": 150}
        )

        assert metrics.service_name == "test-service"
        assert metrics.environment == "test"
        assert metrics.metrics["requests"] == 100
        assert metrics.performance_data["avg_response_time"] == 150

    def test_calculate_error_rate(self):
        """Test error rate calculation"""
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            service_name="test",
            environment="test",
            metrics={"requests_total": 100, "errors_total": 5},
            performance_data={}
        )

        error_rate = metrics.calculate_error_rate()
        assert error_rate == 0.05  # 5%

    def test_calculate_error_rate_no_requests(self):
        """Test error rate calculation with no requests"""
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            service_name="test",
            environment="test",
            metrics={"requests_total": 0, "errors_total": 0},
            performance_data={}
        )

        error_rate = metrics.calculate_error_rate()
        assert error_rate == 0.0

    def test_is_healthy_check(self):
        """Test health check based on metrics"""
        # Healthy metrics
        healthy_metrics = SystemMetrics(
            timestamp=datetime.now(),
            service_name="test",
            environment="test",
            metrics={"requests_total": 100, "errors_total": 2},
            performance_data={"avg_response_time": 100}
        )

        assert healthy_metrics.is_healthy() is True

        # Unhealthy metrics (high error rate)
        unhealthy_metrics = SystemMetrics(
            timestamp=datetime.now(),
            service_name="test",
            environment="test",
            metrics={"requests_total": 100, "errors_total": 50},
            performance_data={"avg_response_time": 100}
        )

        assert unhealthy_metrics.is_healthy() is False