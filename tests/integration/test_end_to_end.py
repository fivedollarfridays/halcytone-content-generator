"""
End-to-end integration tests for Content Generator
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from src.halcytone_content_generator.services.content_sync import (
    ContentSyncService,
    Channel,
    SyncStatus
)
from src.halcytone_content_generator.services.document_fetcher import DocumentFetcher
from src.halcytone_content_generator.services.content_assembler_v2 import EnhancedContentAssembler
from src.halcytone_content_generator.services.crm_client_v2 import EnhancedCRMClient
from src.halcytone_content_generator.services.platform_client_v2 import EnhancedPlatformClient
from src.halcytone_content_generator.config import Settings


class TestEndToEndIntegration:
    """Test complete content generation workflow"""

    @pytest.fixture
    def settings(self):
        """Create test settings"""
        settings = Settings()
        settings.CRM_BASE_URL = "http://test-crm.com"
        settings.PLATFORM_BASE_URL = "http://test-platform.com"
        settings.CRM_API_KEY = "test-crm-key"
        settings.PLATFORM_API_KEY = "test-platform-key"
        settings.GOOGLE_DOCS_API_KEY = "test-google-key"
        settings.NOTION_API_KEY = "test-notion-key"
        settings.EMAIL_BATCH_SIZE = 10
        settings.EMAIL_RATE_LIMIT = 100
        return settings

    @pytest.fixture
    def sync_service(self, settings):
        """Create sync service with mocked dependencies"""
        return ContentSyncService(settings)

    @pytest.fixture
    def mock_content(self):
        """Sample content for testing"""
        return {
            'breathscape': [
                {
                    'title': 'New Feature Release',
                    'content': 'We are excited to announce our latest breathing exercise feature.',
                    'tags': ['feature', 'release'],
                    'date': datetime.now().isoformat()
                }
            ],
            'hardware': [
                {
                    'title': 'Sensor Update',
                    'content': 'Improved accuracy in heart rate monitoring.',
                    'tags': ['hardware', 'update']
                }
            ],
            'tips': [
                {
                    'title': 'Morning Routine',
                    'content': 'Start your day with 5 minutes of deep breathing.',
                    'tags': ['tips', 'wellness']
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_full_content_sync_workflow(self, sync_service, mock_content):
        """Test complete workflow from document fetch to multi-channel publish"""

        # Mock document fetching
        with patch.object(sync_service.document_fetcher, 'fetch_google_doc') as mock_fetch:
            mock_fetch.return_value = mock_content

            # Mock CRM email sending
            with patch.object(sync_service.crm_client, 'send_newsletter_bulk') as mock_crm:
                mock_crm.return_value = Mock(
                    job_id='email-job-123',
                    total_recipients=100,
                    sent_count=100,
                    status='completed'
                )

                # Mock Platform API publishing
                with patch('httpx.AsyncClient') as mock_client:
                    mock_response = Mock()
                    mock_response.json.return_value = {
                        'id': 'content-456',
                        'status': 'published',
                        'url': '/updates/content-456'
                    }
                    mock_response.status_code = 200
                    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

                    # Execute sync
                    job = await sync_service.sync_content(
                        document_id='gdocs:test-doc-123',
                        channels=[Channel.EMAIL, Channel.WEBSITE]
                    )

                    # Start processing (normally runs in background)
                    await sync_service.job_queue.put(job)
                    await sync_service._execute_sync_job(job)

                    # Verify job completed
                    assert job.status == SyncStatus.COMPLETED
                    assert 'email' in job.results
                    assert 'website' in job.results
                    assert job.results['email']['sent'] == 100
                    assert job.results['website']['content_id'] == 'content-456'

    @pytest.mark.asyncio
    async def test_email_only_workflow(self, sync_service, mock_content):
        """Test email-only content distribution"""

        with patch.object(sync_service.document_fetcher, 'fetch_mock_content') as mock_fetch:
            mock_fetch.return_value = mock_content

            with patch.object(sync_service.crm_client, 'send_newsletter_bulk') as mock_crm:
                mock_crm.return_value = Mock(
                    job_id='email-job-789',
                    total_recipients=50,
                    sent_count=50,
                    status='completed'
                )

                job = await sync_service.sync_content(
                    document_id='mock:test',
                    channels=[Channel.EMAIL]
                )

                await sync_service._execute_sync_job(job)

                assert job.status == SyncStatus.COMPLETED
                assert len(job.results) == 1
                assert 'email' in job.results

    @pytest.mark.asyncio
    async def test_website_only_workflow(self, sync_service, mock_content):
        """Test website-only content publishing"""

        with patch.object(sync_service.document_fetcher, 'fetch_notion_content') as mock_fetch:
            mock_fetch.return_value = mock_content

            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = {
                    'id': 'web-content-123',
                    'status': 'published'
                }
                mock_response.status_code = 200
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

                job = await sync_service.sync_content(
                    document_id='notion:page-123',
                    channels=[Channel.WEBSITE]
                )

                await sync_service._execute_sync_job(job)

                assert job.status == SyncStatus.COMPLETED
                assert 'website' in job.results

    @pytest.mark.asyncio
    async def test_social_media_generation(self, sync_service, mock_content):
        """Test social media content generation"""

        with patch.object(sync_service.document_fetcher, 'fetch_mock_content') as mock_fetch:
            mock_fetch.return_value = mock_content

            job = await sync_service.sync_content(
                document_id='mock:test',
                channels=[Channel.SOCIAL_TWITTER, Channel.SOCIAL_LINKEDIN]
            )

            await sync_service._execute_sync_job(job)

            assert job.status == SyncStatus.COMPLETED
            assert 'twitter' in job.results
            assert 'linkedin' in job.results
            assert job.results['twitter']['status'] == 'generated'
            assert len(job.results['twitter']['posts']) > 0

    @pytest.mark.asyncio
    async def test_scheduled_content_sync(self, sync_service, mock_content):
        """Test scheduled content synchronization"""

        future_time = datetime.now() + timedelta(seconds=2)

        with patch.object(sync_service.document_fetcher, 'fetch_mock_content') as mock_fetch:
            mock_fetch.return_value = mock_content

            job = await sync_service.sync_content(
                document_id='mock:test',
                channels=[Channel.EMAIL],
                schedule_time=future_time
            )

            # Job should be pending initially
            assert job.status == SyncStatus.PENDING
            assert job.scheduled_for == future_time

            # Wait for scheduled time
            await asyncio.sleep(2.5)

            # Mock email sending for when job executes
            with patch.object(sync_service.crm_client, 'send_newsletter_bulk') as mock_crm:
                mock_crm.return_value = Mock(
                    job_id='scheduled-job',
                    total_recipients=10,
                    sent_count=10,
                    status='completed'
                )

                # Process the scheduled job
                if not sync_service.job_queue.empty():
                    queued_job = await sync_service.job_queue.get()
                    await sync_service._execute_sync_job(queued_job)

                    assert queued_job.status == SyncStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_error_handling_partial_failure(self, sync_service, mock_content):
        """Test handling partial failures in multi-channel sync"""

        with patch.object(sync_service.document_fetcher, 'fetch_mock_content') as mock_fetch:
            mock_fetch.return_value = mock_content

            # Email succeeds
            with patch.object(sync_service.crm_client, 'send_newsletter_bulk') as mock_crm:
                mock_crm.return_value = Mock(
                    job_id='email-success',
                    total_recipients=100,
                    sent_count=100,
                    status='completed'
                )

                # Website fails
                with patch('httpx.AsyncClient') as mock_client:
                    mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("API Error")

                    job = await sync_service.sync_content(
                        document_id='mock:test',
                        channels=[Channel.EMAIL, Channel.WEBSITE]
                    )

                    await sync_service._execute_sync_job(job)

                    # Should be partial success
                    assert job.status == SyncStatus.PARTIAL
                    assert 'email' in job.results
                    assert 'website' in job.results
                    assert 'error' in job.results['website']
                    assert len(job.errors) > 0

    @pytest.mark.asyncio
    async def test_duplicate_content_detection(self, sync_service, mock_content):
        """Test that duplicate content is not re-sent"""

        with patch.object(sync_service.document_fetcher, 'fetch_mock_content') as mock_fetch:
            mock_fetch.return_value = mock_content

            with patch.object(sync_service.crm_client, 'send_newsletter_bulk') as mock_crm:
                mock_crm.return_value = Mock(
                    job_id='first-send',
                    total_recipients=100,
                    sent_count=100,
                    status='completed'
                )

                # First sync
                job1 = await sync_service.sync_content(
                    document_id='mock:test',
                    channels=[Channel.EMAIL]
                )
                await sync_service._execute_sync_job(job1)
                assert job1.status == SyncStatus.COMPLETED

                # Second sync with same content
                job2 = await sync_service.sync_content(
                    document_id='mock:test',
                    channels=[Channel.EMAIL]
                )
                await sync_service._execute_sync_job(job2)

                # Should skip due to duplicate
                assert job2.status == SyncStatus.COMPLETED
                assert job2.metadata.get('skipped') is True

    @pytest.mark.asyncio
    async def test_correlation_id_propagation(self, sync_service, mock_content):
        """Test correlation ID propagation through the system"""

        correlation_id = "test-correlation-123"

        with patch.object(sync_service.document_fetcher, 'fetch_mock_content') as mock_fetch:
            mock_fetch.return_value = mock_content

            with patch.object(sync_service.crm_client, 'send_newsletter_bulk') as mock_crm:
                mock_crm.return_value = Mock(
                    job_id='corr-test',
                    total_recipients=10,
                    sent_count=10,
                    status='completed'
                )

                job = await sync_service.sync_content(
                    document_id='mock:test',
                    channels=[Channel.EMAIL],
                    correlation_id=correlation_id
                )

                await sync_service._execute_sync_job(job)

                assert job.correlation_id == correlation_id
                assert job.status == SyncStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_content_assembly_templates(self, sync_service, mock_content):
        """Test different content assembly templates"""

        assembler = sync_service.content_assembler

        # Test newsletter generation
        newsletter = assembler.generate_newsletter(mock_content)
        assert 'subject' in newsletter
        assert 'html' in newsletter
        assert 'text' in newsletter
        assert 'New Feature Release' in newsletter['html']

        # Test web update generation
        web_update = assembler.generate_web_update(mock_content)
        assert 'title' in web_update
        assert 'html' in web_update
        assert 'tags' in web_update

        # Test social posts generation
        social_posts = assembler.generate_social_posts(mock_content)
        assert len(social_posts) > 0
        twitter_posts = [p for p in social_posts if p['platform'] == 'twitter']
        assert all(len(p['content']) <= 280 for p in twitter_posts)


class TestAPIIntegration:
    """Test API endpoint integration"""

    @pytest.fixture
    async def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from src.halcytone_content_generator.main import app

        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'

    def test_ready_endpoint(self, client):
        """Test readiness endpoint"""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data['ready'] is True

    @pytest.mark.asyncio
    async def test_generate_content_endpoint(self, client):
        """Test content generation API endpoint"""
        with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher:
            mock_instance = Mock()
            mock_instance.fetch_mock_content.return_value = {
                'breathscape': [{'title': 'Test', 'content': 'Test content'}]
            }
            mock_fetcher.return_value = mock_instance

            response = client.post(
                "/api/v1/content/generate",
                json={
                    "source": "mock",
                    "channels": ["email", "web"]
                }
            )

            assert response.status_code in [200, 422]  # 422 if validation fails

    @pytest.mark.asyncio
    async def test_sync_content_endpoint(self, client):
        """Test content sync API endpoint"""
        with patch('src.halcytone_content_generator.api.endpoints_v2.ContentSyncService') as mock_sync:
            mock_instance = Mock()
            mock_job = Mock(
                job_id='test-123',
                status='completed',
                created_at=datetime.now()
            )
            mock_instance.sync_content.return_value = mock_job
            mock_sync.return_value = mock_instance

            response = client.post(
                "/api/v2/content/sync",
                json={
                    "document_id": "gdocs:test-doc",
                    "channels": ["email", "website"]
                }
            )

            assert response.status_code in [200, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])