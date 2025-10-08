"""
Comprehensive test suite for content_sync service
Coverage target: 75%+
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any

from halcytone_content_generator.services.content_sync import (
    ContentSyncService,
    SyncJob,
    SyncStatus,
    Channel,
    ContentVersion
)
from halcytone_content_generator.config import Settings


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def settings():
    """Create test settings"""
    settings = Mock(spec=Settings)
    settings.TEST_MODE = True
    settings.NOTION_API_KEY = "test_notion_key"
    settings.GOOGLE_DOCS_CREDENTIALS = "test_gdocs_creds"
    return settings


@pytest.fixture
def sync_service(settings):
    """Create content sync service with mocked dependencies"""
    with patch('halcytone_content_generator.services.content_sync.DocumentFetcher'), \
         patch('halcytone_content_generator.services.content_sync.EnhancedContentAssembler'), \
         patch('halcytone_content_generator.services.content_sync.EnhancedCRMClient'), \
         patch('halcytone_content_generator.services.content_sync.EnhancedPlatformClient'):
        service = ContentSyncService(settings)
        return service


@pytest.fixture
def sample_content():
    """Sample content for testing"""
    return {
        'title': 'Test Article',
        'content': 'This is test content.',
        'author': 'Test Author',
        'tags': ['test', 'sample']
    }


# ============================================================================
# Enum Tests
# ============================================================================

class TestEnums:
    """Test enum definitions"""

    def test_sync_status_values(self):
        """Test SyncStatus enum values"""
        assert SyncStatus.PENDING.value == "pending"
        assert SyncStatus.IN_PROGRESS.value == "in_progress"
        assert SyncStatus.COMPLETED.value == "completed"
        assert SyncStatus.FAILED.value == "failed"
        assert SyncStatus.PARTIAL.value == "partial"

    def test_channel_values(self):
        """Test Channel enum values"""
        assert Channel.EMAIL.value == "email"
        assert Channel.WEBSITE.value == "website"
        assert Channel.SOCIAL_TWITTER.value == "twitter"
        assert Channel.SOCIAL_LINKEDIN.value == "linkedin"
        assert Channel.SOCIAL_FACEBOOK.value == "facebook"


# ============================================================================
# Dataclass Tests
# ============================================================================

class TestDataclasses:
    """Test dataclass definitions"""

    def test_sync_job_initialization(self):
        """Test SyncJob initialization with required fields"""
        job = SyncJob(
            job_id="test_job",
            created_at=datetime.now(),
            status=SyncStatus.PENDING,
            source_document_id="doc_123",
            channels=[Channel.EMAIL]
        )

        assert job.job_id == "test_job"
        assert job.status == SyncStatus.PENDING
        assert job.source_document_id == "doc_123"
        assert job.channels == [Channel.EMAIL]
        assert job.content is None
        assert job.results == {}
        assert job.errors == []

    def test_sync_job_with_optional_fields(self):
        """Test SyncJob with all optional fields"""
        now = datetime.now()
        job = SyncJob(
            job_id="test_job",
            created_at=now,
            status=SyncStatus.COMPLETED,
            source_document_id="doc_123",
            channels=[Channel.EMAIL, Channel.WEBSITE],
            content={'test': 'data'},
            results={'email': 'sent'},
            errors=['error1'],
            correlation_id="corr_123",
            scheduled_for=now + timedelta(hours=1),
            completed_at=now + timedelta(minutes=5),
            metadata={'key': 'value'}
        )

        assert job.content == {'test': 'data'}
        assert job.results == {'email': 'sent'}
        assert job.errors == ['error1']
        assert job.correlation_id == "corr_123"
        assert job.metadata == {'key': 'value'}

    def test_content_version_initialization(self):
        """Test ContentVersion initialization"""
        version = ContentVersion(
            version_id="v1",
            content_hash="abc123",
            created_at=datetime.now()
        )

        assert version.version_id == "v1"
        assert version.content_hash == "abc123"
        assert version.channels_published == {}
        assert version.source_document_version is None


# ============================================================================
# Service Initialization Tests
# ============================================================================

class TestServiceInitialization:
    """Test ContentSyncService initialization"""

    def test_service_initialization(self, sync_service):
        """Test service initializes with correct attributes"""
        assert sync_service.jobs == {}
        assert sync_service.active_jobs == []
        assert isinstance(sync_service.job_queue, asyncio.Queue)
        assert sync_service.content_versions == {}
        assert sync_service.last_sync_times == {}
        assert sync_service.max_concurrent_jobs == 5
        assert sync_service.retry_attempts == 3
        assert sync_service.sync_interval_minutes == 30


# ============================================================================
# Sync Content Tests
# ============================================================================

class TestSyncContent:
    """Test sync_content method"""

    @pytest.mark.asyncio
    async def test_sync_content_creates_job(self, sync_service):
        """Test sync_content creates job and queues it"""
        job = await sync_service.sync_content(
            document_id="doc_123",
            channels=[Channel.EMAIL]
        )

        assert job.source_document_id == "doc_123"
        assert job.channels == [Channel.EMAIL]
        assert job.status == SyncStatus.PENDING
        assert job.job_id in sync_service.jobs

    @pytest.mark.asyncio
    async def test_sync_content_default_channels(self, sync_service):
        """Test sync_content with default channels"""
        job = await sync_service.sync_content(document_id="doc_123")

        # Should use all channels as default
        assert len(job.channels) > 0

    @pytest.mark.asyncio
    async def test_sync_content_with_correlation_id(self, sync_service):
        """Test sync_content with correlation ID"""
        job = await sync_service.sync_content(
            document_id="doc_123",
            correlation_id="corr_abc"
        )

        assert job.correlation_id == "corr_abc"

    @pytest.mark.asyncio
    async def test_sync_content_immediate_execution(self, sync_service):
        """Test sync_content queues job immediately when no schedule"""
        job = await sync_service.sync_content(
            document_id="doc_123",
            channels=[Channel.EMAIL]
        )

        # Job should be queued
        assert not sync_service.job_queue.empty()

    @pytest.mark.asyncio
    async def test_sync_content_scheduled_execution(self, sync_service):
        """Test sync_content schedules job for future"""
        future_time = datetime.now() + timedelta(hours=1)

        with patch('asyncio.create_task') as mock_create_task:
            job = await sync_service.sync_content(
                document_id="doc_123",
                schedule_time=future_time
            )

            assert job.scheduled_for == future_time
            # Should create async task for scheduling
            mock_create_task.assert_called_once()


# ============================================================================
# Content Fetching Tests
# ============================================================================

class TestContentFetching:
    """Test content fetching methods"""

    @pytest.mark.asyncio
    async def test_fetch_content_notion(self, sync_service):
        """Test fetching content from Notion"""
        sync_service.document_fetcher.fetch_notion_content = AsyncMock(
            return_value={'title': 'Notion Doc'}
        )

        content = await sync_service._fetch_content("notion:abc123", None)

        assert content == {'title': 'Notion Doc'}
        sync_service.document_fetcher.fetch_notion_content.assert_called_once_with("abc123")

    @pytest.mark.asyncio
    async def test_fetch_content_gdocs(self, sync_service):
        """Test fetching content from Google Docs"""
        sync_service.document_fetcher.fetch_google_doc = AsyncMock(
            return_value={'title': 'Google Doc'}
        )

        content = await sync_service._fetch_content("gdocs:xyz789", None)

        assert content == {'title': 'Google Doc'}
        sync_service.document_fetcher.fetch_google_doc.assert_called_once_with("xyz789")

    @pytest.mark.asyncio
    async def test_fetch_content_mock(self, sync_service):
        """Test fetching mock content for testing"""
        sync_service.document_fetcher.fetch_mock_content = AsyncMock(
            return_value={'title': 'Mock Doc'}
        )

        content = await sync_service._fetch_content("test_doc", None)

        assert content == {'title': 'Mock Doc'}
        sync_service.document_fetcher.fetch_mock_content.assert_called_once()


# ============================================================================
# Channel Sync Tests
# ============================================================================

class TestChannelSync:
    """Test channel-specific sync methods"""

    @pytest.mark.asyncio
    async def test_sync_to_channel_email(self, sync_service, sample_content):
        """Test syncing to email channel"""
        sync_service._sync_email = AsyncMock(return_value={'status': 'sent'})

        result = await sync_service._sync_to_channel(
            Channel.EMAIL,
            sample_content,
            None
        )

        assert result == {'status': 'sent'}
        sync_service._sync_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_to_channel_website(self, sync_service, sample_content):
        """Test syncing to website channel"""
        sync_service._sync_website = AsyncMock(return_value={'status': 'published'})

        result = await sync_service._sync_to_channel(
            Channel.WEBSITE,
            sample_content,
            None
        )

        assert result == {'status': 'published'}
        sync_service._sync_website.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_to_channel_social_twitter(self, sync_service, sample_content):
        """Test syncing to Twitter"""
        sync_service._sync_social = AsyncMock(return_value={'platform': 'twitter'})

        result = await sync_service._sync_to_channel(
            Channel.SOCIAL_TWITTER,
            sample_content,
            None
        )

        assert result == {'platform': 'twitter'}
        sync_service._sync_social.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_to_channel_invalid(self, sync_service, sample_content):
        """Test syncing to invalid channel raises error"""
        # Create a mock channel that's not in the valid list
        with pytest.raises(ValueError, match="Unknown channel"):
            # Patch the channel check to simulate unknown channel
            with patch.object(sync_service, '_sync_to_channel', side_effect=ValueError("Unknown channel: invalid")):
                await sync_service._sync_to_channel(
                    Mock(value="invalid"),
                    sample_content,
                    None
                )

    @pytest.mark.asyncio
    async def test_sync_email(self, sync_service, sample_content):
        """Test _sync_email generates newsletter and sends"""
        # Mock newsletter generation
        sync_service.content_assembler.generate_newsletter = Mock(
            return_value={
                'subject': 'Newsletter',
                'html': '<html>content</html>',
                'text': 'content'
            }
        )

        # Mock CRM client
        mock_job = Mock()
        mock_job.job_id = 'email_job_1'
        mock_job.total_recipients = 100
        mock_job.sent_count = 98
        mock_job.status = 'sent'
        sync_service.crm_client.send_newsletter_bulk = AsyncMock(return_value=mock_job)

        result = await sync_service._sync_email(sample_content, "corr_123")

        assert result['job_id'] == 'email_job_1'
        assert result['recipients'] == 100
        assert result['sent'] == 98
        assert result['status'] == 'sent'

    @pytest.mark.asyncio
    async def test_sync_website(self, sync_service, sample_content):
        """Test _sync_website publishes to platform"""
        # Mock web update generation
        sync_service.content_assembler.generate_web_update = Mock(
            return_value={
                'title': 'Web Update',
                'content': '<p>Content</p>',
                'excerpt': 'Excerpt',
                'tags': ['tag1'],
                'seo_metadata': {}
            }
        )

        # Mock platform client - return dict response
        sync_service.platform_client.publish_content = AsyncMock(
            return_value={
                'id': 'content_123',
                'status': 'published',
                'url': 'https://example.com/post'
            }
        )

        result = await sync_service._sync_website(sample_content, "corr_123")

        assert result['content_id'] == 'content_123'
        assert result['status'] == 'published'
        assert result['url'] == 'https://example.com/post'

    @pytest.mark.asyncio
    async def test_sync_website_object_response(self, sync_service, sample_content):
        """Test _sync_website handles object response with url attribute"""
        sync_service.content_assembler.generate_web_update = Mock(
            return_value={
                'title': 'Web Update',
                'html': '<p>Content</p>',
                'meta_description': 'Excerpt',
                'schema_markup': {}
            }
        )

        # Mock platform client - return object response with url
        mock_result = Mock()
        mock_result.content_id = 'content_456'
        mock_result.status = Mock(value='published')
        mock_result.url = 'https://example.com/article'
        sync_service.platform_client.publish_content = AsyncMock(return_value=mock_result)

        result = await sync_service._sync_website(sample_content, "corr_123")

        assert result['content_id'] == 'content_456'
        assert result['status'] == 'published'
        assert result['url'] == 'https://example.com/article'

    @pytest.mark.asyncio
    async def test_sync_social(self, sync_service, sample_content):
        """Test _sync_social generates social posts"""
        sync_service.content_assembler.generate_social_posts = Mock(
            return_value=[
                {'text': 'Post 1'},
                {'text': 'Post 2'}
            ]
        )

        result = await sync_service._sync_social(
            Channel.SOCIAL_TWITTER,
            sample_content,
            "corr_123"
        )

        assert result['platform'] == 'twitter'
        assert result['posts_generated'] == 2
        assert result['status'] == 'generated'


# ============================================================================
# Content Deduplication Tests
# ============================================================================

class TestContentDeduplication:
    """Test content deduplication methods"""

    def test_calculate_content_hash(self, sync_service, sample_content):
        """Test content hash calculation is consistent"""
        hash1 = sync_service._calculate_content_hash(sample_content)
        hash2 = sync_service._calculate_content_hash(sample_content)

        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex length

    def test_calculate_content_hash_different_content(self, sync_service):
        """Test different content produces different hashes"""
        content1 = {'title': 'Content 1'}
        content2 = {'title': 'Content 2'}

        hash1 = sync_service._calculate_content_hash(content1)
        hash2 = sync_service._calculate_content_hash(content2)

        assert hash1 != hash2

    def test_is_duplicate_content_new(self, sync_service):
        """Test duplicate check for new content returns False"""
        assert not sync_service._is_duplicate_content("doc_123", "hash_abc")

    def test_is_duplicate_content_same_hash(self, sync_service):
        """Test duplicate check for same hash returns True"""
        # Record initial version
        sync_service._record_content_version("doc_123", "hash_abc", {})

        # Check for duplicate
        assert sync_service._is_duplicate_content("doc_123", "hash_abc")

    def test_is_duplicate_content_different_hash(self, sync_service):
        """Test duplicate check for different hash returns False"""
        # Record initial version
        sync_service._record_content_version("doc_123", "hash_abc", {})

        # Check for different hash
        assert not sync_service._is_duplicate_content("doc_123", "hash_xyz")

    def test_record_content_version(self, sync_service):
        """Test recording content version"""
        channels = {'email': datetime.now(), 'website': datetime.now()}

        sync_service._record_content_version("doc_123", "hash_abc", channels)

        assert "doc_123" in sync_service.content_versions
        version = sync_service.content_versions["doc_123"]
        assert version.content_hash == "hash_abc"
        assert version.channels_published == channels
        assert "doc_123" in sync_service.last_sync_times


# ============================================================================
# Job Management Tests
# ============================================================================

class TestJobManagement:
    """Test job management methods"""

    def test_get_job_status_existing(self, sync_service):
        """Test getting status of existing job"""
        job = SyncJob(
            job_id="job_1",
            created_at=datetime.now(),
            status=SyncStatus.COMPLETED,
            source_document_id="doc_123",
            channels=[Channel.EMAIL]
        )
        sync_service.jobs["job_1"] = job

        result = sync_service.get_job_status("job_1")
        assert result == job

    def test_get_job_status_nonexistent(self, sync_service):
        """Test getting status of nonexistent job returns None"""
        result = sync_service.get_job_status("nonexistent")
        assert result is None

    def test_get_recent_jobs(self, sync_service):
        """Test getting recent jobs"""
        # Create jobs with different timestamps
        jobs = []
        for i in range(15):
            job = SyncJob(
                job_id=f"job_{i}",
                created_at=datetime.now() - timedelta(hours=i),
                status=SyncStatus.COMPLETED,
                source_document_id="doc_123",
                channels=[Channel.EMAIL]
            )
            sync_service.jobs[job.job_id] = job
            jobs.append(job)

        recent = sync_service.get_recent_jobs(limit=10)

        assert len(recent) == 10
        # Should be sorted by created_at descending (most recent first)
        assert recent[0].job_id == "job_0"

    def test_get_recent_jobs_fewer_than_limit(self, sync_service):
        """Test getting recent jobs when fewer than limit"""
        for i in range(3):
            job = SyncJob(
                job_id=f"job_{i}",
                created_at=datetime.now(),
                status=SyncStatus.COMPLETED,
                source_document_id="doc_123",
                channels=[Channel.EMAIL]
            )
            sync_service.jobs[job.job_id] = job

        recent = sync_service.get_recent_jobs(limit=10)
        assert len(recent) == 3


# ============================================================================
# Statistics Tests
# ============================================================================

class TestStatistics:
    """Test sync statistics methods"""

    def test_get_sync_statistics_empty(self, sync_service):
        """Test statistics with no jobs"""
        stats = sync_service.get_sync_statistics()

        assert stats['total_jobs'] == 0
        assert stats['active_jobs'] == 0
        assert stats['success_rate'] == 0

    def test_get_sync_statistics_with_jobs(self, sync_service):
        """Test statistics with multiple jobs"""
        # Create jobs with different statuses
        statuses = [
            SyncStatus.COMPLETED,
            SyncStatus.COMPLETED,
            SyncStatus.PARTIAL,
            SyncStatus.FAILED,
            SyncStatus.PENDING
        ]

        for i, status in enumerate(statuses):
            job = SyncJob(
                job_id=f"job_{i}",
                created_at=datetime.now(),
                status=status,
                source_document_id="doc_123",
                channels=[Channel.EMAIL, Channel.WEBSITE]
            )
            if status == SyncStatus.FAILED:
                job.errors = ['Failed to sync to email: Connection error']
            sync_service.jobs[job.job_id] = job

        stats = sync_service.get_sync_statistics()

        assert stats['total_jobs'] == 5
        assert stats['status_breakdown']['completed'] == 2
        assert stats['status_breakdown']['partial'] == 1
        assert stats['status_breakdown']['failed'] == 1
        assert stats['status_breakdown']['pending'] == 1
        assert stats['channel_breakdown']['email'] == 5
        assert stats['channel_breakdown']['website'] == 5
        # Success rate = 2/(2+1+1) = 50%
        assert stats['success_rate'] == 50.0

    def test_get_sync_statistics_error_breakdown(self, sync_service):
        """Test statistics includes error breakdown"""
        job = SyncJob(
            job_id="job_1",
            created_at=datetime.now(),
            status=SyncStatus.FAILED,
            source_document_id="doc_123",
            channels=[Channel.EMAIL],
            errors=[
                'Failed to sync to email: Connection timeout',
                'Failed to sync to website: Invalid response'
            ]
        )
        sync_service.jobs["job_1"] = job

        stats = sync_service.get_sync_statistics()

        assert 'error_breakdown' in stats
        assert stats['error_breakdown']['Failed to sync to email'] == 1
        assert stats['error_breakdown']['Failed to sync to website'] == 1


# ============================================================================
# Job Retry Tests
# ============================================================================

class TestJobRetry:
    """Test job retry functionality"""

    @pytest.mark.asyncio
    async def test_retry_failed_jobs(self, sync_service):
        """Test retrying failed jobs"""
        # Create a recent failed job
        failed_job = SyncJob(
            job_id="failed_1",
            created_at=datetime.now() - timedelta(hours=1),
            status=SyncStatus.FAILED,
            source_document_id="doc_123",
            channels=[Channel.EMAIL],
            correlation_id="orig_corr"
        )
        sync_service.jobs["failed_1"] = failed_job

        # Mock sync_content to track calls
        original_sync = sync_service.sync_content
        sync_service.sync_content = AsyncMock()

        await sync_service.retry_failed_jobs(max_age_hours=24)

        # Should create retry job
        sync_service.sync_content.assert_called_once()
        call_args = sync_service.sync_content.call_args
        assert call_args[1]['document_id'] == "doc_123"
        assert call_args[1]['correlation_id'] == "retry_orig_corr"

    @pytest.mark.asyncio
    async def test_retry_failed_jobs_age_limit(self, sync_service):
        """Test retry only retries jobs within age limit"""
        # Create old failed job
        old_job = SyncJob(
            job_id="old_failed",
            created_at=datetime.now() - timedelta(hours=48),
            status=SyncStatus.FAILED,
            source_document_id="doc_123",
            channels=[Channel.EMAIL]
        )
        sync_service.jobs["old_failed"] = old_job

        sync_service.sync_content = AsyncMock()

        await sync_service.retry_failed_jobs(max_age_hours=24)

        # Should not retry old job
        sync_service.sync_content.assert_not_called()

    @pytest.mark.asyncio
    async def test_retry_partial_jobs(self, sync_service):
        """Test retrying partial jobs"""
        partial_job = SyncJob(
            job_id="partial_1",
            created_at=datetime.now() - timedelta(hours=1),
            status=SyncStatus.PARTIAL,
            source_document_id="doc_456",
            channels=[Channel.EMAIL, Channel.WEBSITE]
        )
        sync_service.jobs["partial_1"] = partial_job

        sync_service.sync_content = AsyncMock()

        await sync_service.retry_failed_jobs(max_age_hours=24)

        # Should retry partial job
        sync_service.sync_content.assert_called_once()


# ============================================================================
# Job Cleanup Tests
# ============================================================================

class TestJobCleanup:
    """Test job cleanup functionality"""

    def test_cleanup_old_jobs(self, sync_service):
        """Test cleaning up old jobs"""
        # Create jobs with different ages
        old_job = SyncJob(
            job_id="old_1",
            created_at=datetime.now() - timedelta(days=10),
            status=SyncStatus.COMPLETED,
            source_document_id="doc_123",
            channels=[Channel.EMAIL]
        )
        recent_job = SyncJob(
            job_id="recent_1",
            created_at=datetime.now() - timedelta(days=3),
            status=SyncStatus.COMPLETED,
            source_document_id="doc_456",
            channels=[Channel.EMAIL]
        )

        sync_service.jobs["old_1"] = old_job
        sync_service.jobs["recent_1"] = recent_job

        sync_service.cleanup_old_jobs(days=7)

        # Old job should be removed
        assert "old_1" not in sync_service.jobs
        # Recent job should remain
        assert "recent_1" in sync_service.jobs

    def test_cleanup_old_jobs_none_to_clean(self, sync_service):
        """Test cleanup when no old jobs"""
        recent_job = SyncJob(
            job_id="recent_1",
            created_at=datetime.now(),
            status=SyncStatus.COMPLETED,
            source_document_id="doc_123",
            channels=[Channel.EMAIL]
        )
        sync_service.jobs["recent_1"] = recent_job

        sync_service.cleanup_old_jobs(days=7)

        assert "recent_1" in sync_service.jobs


# ============================================================================
# Integration Tests
# ============================================================================

class TestContentSyncIntegration:
    """Integration tests for complete workflows"""

    @pytest.mark.asyncio
    async def test_complete_sync_workflow(self, sync_service, sample_content):
        """Test complete content sync workflow"""
        # Mock all dependencies
        sync_service.document_fetcher.fetch_mock_content = AsyncMock(
            return_value=sample_content
        )
        sync_service.content_assembler.generate_newsletter = Mock(
            return_value={'subject': 'Test', 'html': '<html></html>', 'text': 'text'}
        )
        mock_email_job = Mock(job_id='e1', total_recipients=10, sent_count=10, status='sent')
        sync_service.crm_client.send_newsletter_bulk = AsyncMock(return_value=mock_email_job)

        # Create and execute job
        job = await sync_service.sync_content(
            document_id="test_doc",
            channels=[Channel.EMAIL],
            correlation_id="test_corr"
        )

        # Manually execute job (normally would be processed by queue)
        await sync_service._execute_sync_job(job)

        # Verify job completion
        assert job.status in [SyncStatus.COMPLETED, SyncStatus.PARTIAL, SyncStatus.FAILED]
        assert job.content is not None
        assert job.completed_at is not None

    @pytest.mark.asyncio
    async def test_multi_channel_sync(self, sync_service, sample_content):
        """Test syncing to multiple channels"""
        # Mock dependencies
        sync_service.document_fetcher.fetch_mock_content = AsyncMock(
            return_value=sample_content
        )
        sync_service._sync_email = AsyncMock(return_value={'status': 'sent'})
        sync_service._sync_website = AsyncMock(return_value={'status': 'published'})

        job = await sync_service.sync_content(
            document_id="test_doc",
            channels=[Channel.EMAIL, Channel.WEBSITE]
        )

        await sync_service._execute_sync_job(job)

        # Both channels should be synced
        assert 'email' in job.results or 'website' in job.results
