"""
Unit tests for monitoring service
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

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

    def test_event_type_enum(self):
        """Test EventType enum values"""
        assert EventType.REQUEST.value == "request"
        assert EventType.ERROR.value == "error"
        assert EventType.PERFORMANCE.value == "performance"

    def test_health_status_enum(self):
        """Test HealthStatus enum values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_monitoring_event_creation(self):
        """Test MonitoringEvent creation"""
        event = MonitoringEvent(
            event_id="event_123",
            correlation_id="corr_456",
            timestamp=datetime.now(),
            service="content-generator",
            operation="test_operation",
            event_type=EventType.REQUEST,
            metadata={"test": "data"}
        )

        assert event.event_id == "event_123"
        assert event.correlation_id == "corr_456"
        assert event.service == "content-generator"
        assert event.operation == "test_operation"
        assert event.event_type == EventType.REQUEST
        assert event.metadata["test"] == "data"

    def test_record_event(self, monitoring_service):
        """Test recording events"""
        monitoring_service.record_event(
            event_type=EventType.REQUEST,
            operation="test_operation",
            metadata={"endpoint": "/test"}
        )

        # Event should be recorded
        assert len(monitoring_service.events) > 0

    def test_get_health_status(self, monitoring_service):
        """Test getting health status"""
        status = monitoring_service.get_health_status()

        assert status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]

    @patch('src.halcytone_content_generator.services.monitoring.MonitoringService._check_system_health')
    def test_health_check_healthy(self, mock_health_check, monitoring_service):
        """Test health check when system is healthy"""
        mock_health_check.return_value = True

        status = monitoring_service.get_health_status()
        assert status == HealthStatus.HEALTHY

    @patch('src.halcytone_content_generator.services.monitoring.MonitoringService._check_system_health')
    def test_health_check_unhealthy(self, mock_health_check, monitoring_service):
        """Test health check when system is unhealthy"""
        mock_health_check.return_value = False

        status = monitoring_service.get_health_status()
        assert status == HealthStatus.UNHEALTHY

    def test_start_trace(self, monitoring_service):
        """Test starting a trace"""
        trace_id = monitoring_service.start_trace("test_operation")
        assert trace_id is not None

    def test_end_trace(self, monitoring_service):
        """Test ending a trace"""
        trace_id = monitoring_service.start_trace("test_operation")
        monitoring_service.end_trace(trace_id, success=True)

        # Should have recorded the trace
        assert len(monitoring_service.events) > 0

    def test_context_manager_trace(self, monitoring_service):
        """Test tracing with context manager"""
        with monitoring_service.trace("test_operation") as trace_id:
            assert trace_id is not None

        # Should have recorded the trace
        assert len(monitoring_service.events) > 0

    def test_get_metrics_summary(self, monitoring_service):
        """Test getting metrics summary"""
        # Record some events
        monitoring_service.record_event(EventType.REQUEST, "test_op")
        monitoring_service.record_event(EventType.ERROR, "test_op")

        summary = monitoring_service.get_metrics_summary()
        assert "total_events" in summary
        assert summary["total_events"] >= 2

    def test_export_events(self, monitoring_service):
        """Test exporting events"""
        monitoring_service.record_event(EventType.REQUEST, "test_op")

        events = monitoring_service.export_events()
        assert len(events) > 0
        assert events[0]["event_type"] == "request"

    def test_cleanup_old_events(self, monitoring_service):
        """Test cleanup of old events"""
        # Add an event
        monitoring_service.record_event(EventType.REQUEST, "test_op")
        initial_count = len(monitoring_service.events)

        # Cleanup (should not remove recent events)
        monitoring_service.cleanup_old_events(hours=24)
        assert len(monitoring_service.events) == initial_count

    def test_get_error_rate(self, monitoring_service):
        """Test error rate calculation"""
        # Record some events
        for _ in range(8):
            monitoring_service.record_event(EventType.REQUEST, "test_op")
        for _ in range(2):
            monitoring_service.record_event(EventType.ERROR, "test_op")

        error_rate = monitoring_service.get_error_rate()
        assert 0 <= error_rate <= 1

    def test_get_operation_metrics(self, monitoring_service):
        """Test getting metrics for specific operation"""
        monitoring_service.record_event(EventType.REQUEST, "test_op")
        monitoring_service.record_event(EventType.PERFORMANCE, "test_op",
                                       metadata={"duration_ms": 150})

        metrics = monitoring_service.get_operation_metrics("test_op")
        assert "request_count" in metrics

    @patch('logging.Logger.info')
    def test_logging_integration(self, mock_logger, monitoring_service):
        """Test logging integration"""
        monitoring_service.record_event(EventType.REQUEST, "test_op")
        # Should have logged the event
        mock_logger.assert_called()

    def test_correlation_id_tracking(self, monitoring_service):
        """Test correlation ID tracking across events"""
        correlation_id = "test_correlation_123"

        monitoring_service.record_event(
            EventType.REQUEST,
            "test_op",
            correlation_id=correlation_id
        )

        events = monitoring_service.export_events()
        assert events[0]["correlation_id"] == correlation_id