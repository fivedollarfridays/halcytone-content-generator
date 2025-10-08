"""
Unit tests for Platform API integration
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from halcytone_content_generator.services.platform_client_v2 import (
    EnhancedPlatformClient,
    ContentStatus,
    ContentVersion
)
from halcytone_content_generator.services.monitoring import (
    MonitoringService,
    EventType,
    HealthStatus
)
from halcytone_content_generator.services.content_sync import (
    ContentSyncService,
    SyncJob,
    SyncStatus,
    Channel
)


class TestEnhancedPlatformClient:
    """Test enhanced Platform API client functionality"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = Mock()
        settings.PLATFORM_BASE_URL = "http://test-platform.com"
        settings.PLATFORM_API_KEY = "test-key"
        settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
        settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
        settings.MAX_RETRIES = 3
        settings.RETRY_MAX_WAIT = 60
        return settings

    @pytest.fixture
    def platform_client(self, mock_settings):
        """Create Platform client for testing"""
        return EnhancedPlatformClient(mock_settings)

    @pytest.mark.asyncio
    async def test_publish_content_success(self, platform_client):
        """Test successful content publishing"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                'id': 'content-123',
                'status': 'published',
                'url': '/updates/content-123',
                'version': 1
            }
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await platform_client.publish_content(
                title="Test Update",
                content="<h1>Test Content</h1>",
                author="Test Author",
                category="updates",
                tags=["test", "update"]
            )

            assert result['id'] == 'content-123'
            assert result['status'] == 'published'
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_content_with_scheduling(self, platform_client):
        """Test scheduled content publishing"""
        scheduled_time = datetime.now() + timedelta(hours=1)

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                'id': 'content-123',
                'status': 'scheduled',
                'scheduled_for': scheduled_time.isoformat()
            }
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await platform_client.publish_content(
                title="Scheduled Update",
                content="<h1>Future Content</h1>",
                author="Test Author",
                scheduled_time=scheduled_time
            )

            assert result['status'] == 'scheduled'
            assert 'scheduled_for' in result

    @pytest.mark.asyncio
    async def test_update_content_status(self, platform_client):
        """Test updating content status"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {'status': 'archived'}
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.patch.return_value = mock_response

            result = await platform_client.update_content_status(
                content_id="content-123",
                status=ContentStatus.ARCHIVED
            )

            assert result['status'] == 'archived'

    @pytest.mark.asyncio
    async def test_get_content_metrics(self, platform_client):
        """Test fetching content metrics"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                'views': 1000,
                'engagement_rate': 5.5,
                'average_time_seconds': 45
            }
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            metrics = await platform_client.get_content_metrics("content-123")

            assert metrics['views'] == 1000
            assert metrics['engagement_rate'] == 5.5

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Method not yet implemented in platform client")
    async def test_batch_sync_updates(self, platform_client):
        """Test batch synchronization of updates"""
        updates = [
            {
                "title": "Update 1",
                "content": "Content 1",
                "author": "Author 1",
                "category": "news"
            },
            {
                "title": "Update 2",
                "content": "Content 2",
                "author": "Author 2",
                "category": "blog"
            }
        ]

        with patch.object(platform_client, 'publish_content') as mock_publish:
            mock_publish.side_effect = [
                {'id': 'content-1', 'status': 'published'},
                {'id': 'content-2', 'status': 'published'}
            ]

            results = await platform_client.batch_sync_updates(updates)

            assert len(results['successful']) == 2
            assert len(results['failed']) == 0
            assert mock_publish.call_count == 2

    @pytest.mark.asyncio
    async def test_content_versioning(self, platform_client):
        """Test content versioning functionality"""
        # First publish
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                'id': 'content-123',
                'version': 1
            }
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await platform_client.publish_content(
                title="Versioned Content",
                content="Version 1"
            )

            version_key = f"content-123_v1"
            assert version_key in platform_client.content_versions

    @pytest.mark.asyncio
    async def test_circuit_breaker_activation(self, platform_client):
        """Test circuit breaker activation on failures"""
        # Simulate multiple failures
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("API Error")

            # Should trigger circuit breaker after threshold
            for _ in range(6):  # Threshold is 5
                try:
                    await platform_client.publish_content(
                        title="Test",
                        content="Test"
                    )
                except:
                    pass

            # Circuit should be open
            assert platform_client.circuit_breaker.state == 'open'

    @pytest.mark.asyncio
    async def test_correlation_id_propagation(self, platform_client):
        """Test correlation ID propagation through requests"""
        correlation_id = "test-correlation-123"

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {'id': 'content-123'}
            mock_response.status_code = 200
            mock_post = Mock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await platform_client.publish_content(
                title="Test",
                content="Test",
                correlation_id=correlation_id
            )

            # Check correlation ID was passed in headers
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert 'headers' in call_kwargs
            assert call_kwargs['headers'].get('X-Correlation-ID') == correlation_id

    @pytest.mark.asyncio
    async def test_monitoring_event_recording(self, platform_client):
        """Test monitoring events are recorded"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {'id': 'content-123'}
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            await platform_client.publish_content(
                title="Test",
                content="Test"
            )

            # Check monitoring event was recorded
            assert len(platform_client.monitoring_events) > 0
            event = platform_client.monitoring_events[-1]
            assert event['operation'] == 'publish_content'
            assert event['success'] is True


class TestMonitoringService:
    """Test monitoring and telemetry functionality"""

    @pytest.fixture
    def monitoring(self):
        """Create monitoring service for testing"""
        return MonitoringService("test-service")

    def test_record_event(self, monitoring):
        """Test recording monitoring events"""
        monitoring.record_event(
            EventType.API_REQUEST,
            "test_operation",
            correlation_id="test-123",
            duration_ms=100,
            metadata={'key': 'value'}
        )

        assert len(monitoring.events) == 1
        event = monitoring.events[0]
        assert event.operation == "test_operation"
        assert event.duration_ms == 100
        assert event.correlation_id == "test-123"

    def test_trace_operation_success(self, monitoring):
        """Test tracing successful operations"""
        with monitoring.trace_operation("test_op", "correlation-123"):
            # Simulate operation
            pass

        assert len(monitoring.events) == 1
        assert monitoring.events[0].success is True

    def test_trace_operation_failure(self, monitoring):
        """Test tracing failed operations"""
        with pytest.raises(ValueError):
            with monitoring.trace_operation("test_op", "correlation-123"):
                raise ValueError("Test error")

        assert len(monitoring.events) == 1
        assert monitoring.events[0].success is False
        assert "Test error" in monitoring.events[0].error

    def test_get_metrics(self, monitoring):
        """Test metrics calculation"""
        # Record some events
        monitoring.record_event(EventType.API_REQUEST, "op1", duration_ms=100)
        monitoring.record_event(EventType.API_REQUEST, "op1", duration_ms=200)
        monitoring.record_event(EventType.ERROR, "op1", success=False)

        metrics = monitoring.get_metrics("op1")

        assert metrics['total_calls'] == 3
        assert metrics['error_count'] == 1
        assert metrics['error_rate'] == pytest.approx(33.33, 0.1)
        assert metrics['avg_duration_ms'] == 150

    @pytest.mark.asyncio
    async def test_health_status(self, monitoring):
        """Test health status calculation"""
        # Register health check
        async def check_database():
            return {'status': 'healthy', 'latency_ms': 10}

        monitoring.register_health_check("database", check_database)

        health = await monitoring.get_health_status()

        assert health.service == "test-service"
        assert health.status == "healthy"
        assert 'database' in health.metadata['health_checks']

    def test_prometheus_export(self, monitoring):
        """Test Prometheus metrics export"""
        monitoring.record_event(EventType.API_REQUEST, "test_op", duration_ms=100)

        prometheus_output = monitoring.export_metrics_prometheus()

        assert "content_generator_total_calls 1" in prometheus_output
        assert "content_generator_error_rate 0" in prometheus_output

    def test_event_cleanup(self, monitoring):
        """Test old event cleanup"""
        # Add old event
        old_event = monitoring.events[0] if monitoring.events else None
        monitoring.record_event(EventType.API_REQUEST, "test_op")

        # Set timestamp to old date
        if monitoring.events:
            monitoring.events[0].timestamp = datetime.now() - timedelta(days=8)

        monitoring.clear_old_events(days=7)

        # Old event should be removed
        assert all(
            e.timestamp > datetime.now() - timedelta(days=7)
            for e in monitoring.events
        )


class TestContentSyncService:
    """Test content synchronization service"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = Mock()
        settings.CRM_BASE_URL = "http://test-crm.com"
        settings.PLATFORM_BASE_URL = "http://test-platform.com"
        settings.CRM_API_KEY = "crm-key"
        settings.PLATFORM_API_KEY = "platform-key"
        settings.EMAIL_BATCH_SIZE = 10
        settings.EMAIL_RATE_LIMIT = 100
        settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
        settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
        settings.MAX_RETRIES = 3
        settings.RETRY_MAX_WAIT = 60
        return settings

    @pytest.fixture
    def sync_service(self, mock_settings):
        """Create sync service for testing"""
        return ContentSyncService(mock_settings)

    @pytest.mark.asyncio
    async def test_sync_content_all_channels(self, sync_service):
        """Test syncing content to all channels"""
        with patch.object(sync_service, '_fetch_content') as mock_fetch:
            mock_fetch.return_value = {
                'breathscape': [{'title': 'Test', 'content': 'Test content'}]
            }

            with patch.object(sync_service, '_sync_email') as mock_email:
                mock_email.return_value = {'status': 'sent'}

                with patch.object(sync_service, '_sync_website') as mock_web:
                    mock_web.return_value = {'status': 'published'}

                    with patch.object(sync_service, '_sync_social') as mock_social:
                        mock_social.return_value = {'status': 'generated'}

                        job = await sync_service.sync_content(
                            document_id="test-doc",
                            channels=[Channel.EMAIL, Channel.WEBSITE]
                        )

                        assert job.status == SyncStatus.PENDING
                        assert len(job.channels) == 2

    @pytest.mark.asyncio
    async def test_sync_job_execution(self, sync_service):
        """Test sync job execution"""
        job = SyncJob(
            job_id="test-job",
            created_at=datetime.now(),
            status=SyncStatus.PENDING,
            source_document_id="test-doc",
            channels=[Channel.EMAIL]
        )

        with patch.object(sync_service, '_fetch_content') as mock_fetch:
            mock_fetch.return_value = {'test': 'content'}

            with patch.object(sync_service, '_sync_to_channel') as mock_sync:
                mock_sync.return_value = {'status': 'success'}

                await sync_service._execute_sync_job(job)

                assert job.status == SyncStatus.COMPLETED
                assert 'email' in job.results

    @pytest.mark.asyncio
    async def test_duplicate_content_detection(self, sync_service):
        """Test duplicate content is not re-synced"""
        content = {'test': 'content'}
        content_hash = sync_service._calculate_content_hash(content)

        # Record initial version
        sync_service._record_content_version(
            "test-doc",
            content_hash,
            {'email': datetime.now()}
        )

        # Check duplicate detection
        is_duplicate = sync_service._is_duplicate_content("test-doc", content_hash)
        assert is_duplicate is True

        # Different content should not be duplicate
        different_content = {'test': 'different'}
        different_hash = sync_service._calculate_content_hash(different_content)
        is_duplicate = sync_service._is_duplicate_content("test-doc", different_hash)
        assert is_duplicate is False

    @pytest.mark.asyncio
    async def test_scheduled_sync(self, sync_service):
        """Test scheduled content synchronization"""
        future_time = datetime.now() + timedelta(seconds=1)

        job = await sync_service.sync_content(
            document_id="test-doc",
            channels=[Channel.EMAIL],
            schedule_time=future_time
        )

        assert job.scheduled_for == future_time
        assert job.status == SyncStatus.PENDING

    def test_sync_statistics(self, sync_service):
        """Test sync statistics calculation"""
        # Add some test jobs
        for i in range(5):
            job = SyncJob(
                job_id=f"job-{i}",
                created_at=datetime.now(),
                status=SyncStatus.COMPLETED if i < 3 else SyncStatus.FAILED,
                source_document_id=f"doc-{i}",
                channels=[Channel.EMAIL, Channel.WEBSITE]
            )
            sync_service.jobs[job.job_id] = job

        stats = sync_service.get_sync_statistics()

        assert stats['total_jobs'] == 5
        assert stats['status_breakdown']['completed'] == 3
        assert stats['status_breakdown']['failed'] == 2
        assert stats['success_rate'] == 60.0

    @pytest.mark.asyncio
    async def test_retry_failed_jobs(self, sync_service):
        """Test retrying failed jobs"""
        # Add failed job
        failed_job = SyncJob(
            job_id="failed-job",
            created_at=datetime.now(),
            status=SyncStatus.FAILED,
            source_document_id="test-doc",
            channels=[Channel.EMAIL]
        )
        sync_service.jobs["failed-job"] = failed_job

        with patch.object(sync_service, 'sync_content') as mock_sync:
            mock_sync.return_value = SyncJob(
                job_id="retry-job",
                created_at=datetime.now(),
                status=SyncStatus.PENDING,
                source_document_id="test-doc",
                channels=[Channel.EMAIL]
            )

            await sync_service.retry_failed_jobs(max_age_hours=24)

            mock_sync.assert_called_once()
            assert mock_sync.call_args[1]['document_id'] == "test-doc"

    def test_job_cleanup(self, sync_service):
        """Test cleaning up old jobs"""
        # Add old job
        old_job = SyncJob(
            job_id="old-job",
            created_at=datetime.now() - timedelta(days=8),
            status=SyncStatus.COMPLETED,
            source_document_id="test-doc",
            channels=[Channel.EMAIL]
        )
        sync_service.jobs["old-job"] = old_job

        # Add recent job
        recent_job = SyncJob(
            job_id="recent-job",
            created_at=datetime.now(),
            status=SyncStatus.COMPLETED,
            source_document_id="test-doc",
            channels=[Channel.EMAIL]
        )
        sync_service.jobs["recent-job"] = recent_job

        sync_service.cleanup_old_jobs(days=7)

        assert "old-job" not in sync_service.jobs
        assert "recent-job" in sync_service.jobs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])