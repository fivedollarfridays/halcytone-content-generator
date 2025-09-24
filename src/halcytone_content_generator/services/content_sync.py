"""
Content synchronization service for multi-channel publishing
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
import json
from collections import defaultdict

from ..services.document_fetcher import DocumentFetcher
from ..services.content_assembler_v2 import EnhancedContentAssembler
from ..services.crm_client_v2 import EnhancedCRMClient
from ..services.platform_client_v2 import EnhancedPlatformClient
from ..services.monitoring import monitoring_service, EventType
from ..config import Settings

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Content synchronization status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Channel(Enum):
    """Content distribution channels"""
    EMAIL = "email"
    WEBSITE = "website"
    SOCIAL_TWITTER = "twitter"
    SOCIAL_LINKEDIN = "linkedin"
    SOCIAL_FACEBOOK = "facebook"


@dataclass
class SyncJob:
    """Content synchronization job"""
    job_id: str
    created_at: datetime
    status: SyncStatus
    source_document_id: str
    channels: List[Channel]
    content: Optional[Dict[str, Any]] = None
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    correlation_id: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentVersion:
    """Track content versions across channels"""
    version_id: str
    content_hash: str
    created_at: datetime
    channels_published: Dict[str, datetime] = field(default_factory=dict)
    source_document_version: Optional[str] = None


class ContentSyncService:
    """
    Orchestrates content synchronization across all channels
    """

    def __init__(self, settings: Settings):
        """
        Initialize content sync service

        Args:
            settings: Application settings
        """
        self.settings = settings

        # Initialize service clients
        self.document_fetcher = DocumentFetcher(settings)
        self.content_assembler = EnhancedContentAssembler()
        self.crm_client = EnhancedCRMClient(settings)
        self.platform_client = EnhancedPlatformClient(settings)

        # Job management
        self.jobs: Dict[str, SyncJob] = {}
        self.active_jobs: List[str] = []
        self.job_queue: asyncio.Queue = asyncio.Queue()

        # Content versioning
        self.content_versions: Dict[str, ContentVersion] = {}
        self.last_sync_times: Dict[str, datetime] = {}

        # Configuration
        self.max_concurrent_jobs = 5
        self.retry_attempts = 3
        self.sync_interval_minutes = 30

    async def sync_content(
        self,
        document_id: str,
        channels: Optional[List[Channel]] = None,
        correlation_id: Optional[str] = None,
        schedule_time: Optional[datetime] = None
    ) -> SyncJob:
        """
        Synchronize content from document to specified channels

        Args:
            document_id: Source document ID
            channels: Target channels (defaults to all)
            correlation_id: Request correlation ID
            schedule_time: Optional scheduled time

        Returns:
            Sync job object
        """
        # Create job
        job_id = f"sync_{datetime.now().strftime('%Y%m%d%H%M%S')}_{document_id[:8]}"
        job = SyncJob(
            job_id=job_id,
            created_at=datetime.now(),
            status=SyncStatus.PENDING,
            source_document_id=document_id,
            channels=channels or list(Channel),
            correlation_id=correlation_id,
            scheduled_for=schedule_time
        )

        self.jobs[job_id] = job

        # Schedule or execute immediately
        if schedule_time and schedule_time > datetime.now():
            asyncio.create_task(self._schedule_job(job))
            logger.info(f"Scheduled job {job_id} for {schedule_time}")
        else:
            await self.job_queue.put(job)
            logger.info(f"Queued job {job_id} for immediate execution")

        return job

    async def _schedule_job(self, job: SyncJob):
        """Schedule a job for future execution"""
        if job.scheduled_for:
            wait_seconds = (job.scheduled_for - datetime.now()).total_seconds()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            await self.job_queue.put(job)

    async def process_sync_queue(self):
        """Process queued sync jobs"""
        while True:
            try:
                # Wait for jobs
                job = await self.job_queue.get()

                # Check concurrent job limit
                while len(self.active_jobs) >= self.max_concurrent_jobs:
                    await asyncio.sleep(1)

                # Process job
                self.active_jobs.append(job.job_id)
                asyncio.create_task(self._execute_sync_job(job))

            except Exception as e:
                logger.error(f"Error processing sync queue: {e}")
                await asyncio.sleep(5)

    async def _execute_sync_job(self, job: SyncJob):
        """
        Execute a content sync job

        Args:
            job: Sync job to execute
        """
        try:
            job.status = SyncStatus.IN_PROGRESS
            start_time = datetime.now()

            with monitoring_service.trace_operation(
                "content_sync",
                correlation_id=job.correlation_id,
                metadata={'job_id': job.job_id, 'channels': [c.value for c in job.channels]}
            ):
                # Step 1: Fetch content from source
                logger.info(f"Fetching content for job {job.job_id}")
                content = await self._fetch_content(job.source_document_id, job.correlation_id)
                job.content = content

                # Step 2: Check for changes
                content_hash = self._calculate_content_hash(content)
                if self._is_duplicate_content(job.source_document_id, content_hash):
                    logger.info(f"No changes detected for job {job.job_id}, skipping")
                    job.status = SyncStatus.COMPLETED
                    job.metadata['skipped'] = True
                    return

                # Step 3: Process each channel
                results = {}
                errors = []

                for channel in job.channels:
                    try:
                        result = await self._sync_to_channel(
                            channel,
                            content,
                            job.correlation_id
                        )
                        results[channel.value] = result
                        logger.info(f"Successfully synced to {channel.value}")

                    except Exception as e:
                        error_msg = f"Failed to sync to {channel.value}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        results[channel.value] = {'error': str(e)}

                # Update job status
                job.results = results
                job.errors = errors

                if errors:
                    job.status = SyncStatus.PARTIAL if len(errors) < len(job.channels) else SyncStatus.FAILED
                else:
                    job.status = SyncStatus.COMPLETED

                # Record content version
                self._record_content_version(
                    job.source_document_id,
                    content_hash,
                    {c: datetime.now() for c in results.keys() if 'error' not in results[c]}
                )

                # Record metrics
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                monitoring_service.record_event(
                    EventType.CONTENT_PUBLISHED,
                    "content_sync_completed",
                    correlation_id=job.correlation_id,
                    duration_ms=duration_ms,
                    metadata={
                        'job_id': job.job_id,
                        'channels_succeeded': len([r for r in results.values() if 'error' not in r]),
                        'channels_failed': len(errors)
                    },
                    success=job.status == SyncStatus.COMPLETED
                )

        except Exception as e:
            logger.error(f"Error executing sync job {job.job_id}: {e}")
            job.status = SyncStatus.FAILED
            job.errors.append(str(e))

        finally:
            job.completed_at = datetime.now()
            if job.job_id in self.active_jobs:
                self.active_jobs.remove(job.job_id)

    async def _fetch_content(self, document_id: str, correlation_id: Optional[str]) -> Dict[str, Any]:
        """
        Fetch content from source document

        Args:
            document_id: Document ID
            correlation_id: Correlation ID

        Returns:
            Parsed content
        """
        # Determine document type from ID format
        if document_id.startswith("notion:"):
            doc_id = document_id.replace("notion:", "")
            return await self.document_fetcher.fetch_notion_content(doc_id)
        elif document_id.startswith("gdocs:"):
            doc_id = document_id.replace("gdocs:", "")
            return await self.document_fetcher.fetch_google_doc(doc_id)
        else:
            # Default to mock content for testing
            return await self.document_fetcher.fetch_mock_content()

    async def _sync_to_channel(
        self,
        channel: Channel,
        content: Dict[str, Any],
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Sync content to a specific channel

        Args:
            channel: Target channel
            content: Content to sync
            correlation_id: Correlation ID

        Returns:
            Sync result
        """
        if channel == Channel.EMAIL:
            return await self._sync_email(content, correlation_id)

        elif channel == Channel.WEBSITE:
            return await self._sync_website(content, correlation_id)

        elif channel in [Channel.SOCIAL_TWITTER, Channel.SOCIAL_LINKEDIN, Channel.SOCIAL_FACEBOOK]:
            return await self._sync_social(channel, content, correlation_id)

        else:
            raise ValueError(f"Unknown channel: {channel}")

    async def _sync_email(self, content: Dict[str, Any], correlation_id: Optional[str]) -> Dict[str, Any]:
        """Sync content as email newsletter"""
        # Generate newsletter
        newsletter = self.content_assembler.generate_newsletter(
            content,
            custom_data={'correlation_id': correlation_id}
        )

        # Send via CRM
        job = await self.crm_client.send_newsletter_bulk(
            subject=newsletter['subject'],
            html=newsletter['html'],
            text=newsletter['text'],
            test_mode=self.settings.get('TEST_MODE', False)
        )

        return {
            'job_id': job.job_id,
            'recipients': job.total_recipients,
            'sent': job.sent_count,
            'status': job.status
        }

    async def _sync_website(self, content: Dict[str, Any], correlation_id: Optional[str]) -> Dict[str, Any]:
        """Sync content to website"""
        # Generate web update
        web_update = self.content_assembler.generate_web_update(
            content,
            seo_optimize=True
        )

        # Publish via Platform API
        result = await self.platform_client.publish_content(
            title=web_update['title'],
            content=web_update['html'],
            author="Content Generator",
            category="updates",
            tags=web_update.get('tags', []),
            seo_metadata=web_update.get('seo_metadata'),
            correlation_id=correlation_id
        )

        return {
            'content_id': result.get('id'),
            'status': result.get('status'),
            'url': result.get('url')
        }

    async def _sync_social(
        self,
        channel: Channel,
        content: Dict[str, Any],
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Sync content to social media"""
        # Map channel to platform
        platform_map = {
            Channel.SOCIAL_TWITTER: 'twitter',
            Channel.SOCIAL_LINKEDIN: 'linkedin',
            Channel.SOCIAL_FACEBOOK: 'facebook'
        }
        platform = platform_map.get(channel)

        # Generate social posts
        posts = self.content_assembler.generate_social_posts(
            content,
            platforms=[platform]
        )

        # For now, return generated posts (manual posting)
        # In production, would integrate with social media APIs
        return {
            'platform': platform,
            'posts_generated': len(posts),
            'posts': posts,
            'status': 'generated',
            'note': 'Manual posting required'
        }

    def _calculate_content_hash(self, content: Dict[str, Any]) -> str:
        """Calculate hash of content for deduplication"""
        import hashlib
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _is_duplicate_content(self, document_id: str, content_hash: str) -> bool:
        """Check if content is duplicate of last sync"""
        if document_id in self.content_versions:
            last_version = self.content_versions[document_id]
            return last_version.content_hash == content_hash
        return False

    def _record_content_version(
        self,
        document_id: str,
        content_hash: str,
        channels_published: Dict[str, datetime]
    ):
        """Record content version for tracking"""
        import uuid
        version = ContentVersion(
            version_id=str(uuid.uuid4()),
            content_hash=content_hash,
            created_at=datetime.now(),
            channels_published=channels_published,
            source_document_version=document_id
        )
        self.content_versions[document_id] = version
        self.last_sync_times[document_id] = datetime.now()

    async def auto_sync_documents(self, document_ids: List[str]):
        """
        Automatically sync documents at regular intervals

        Args:
            document_ids: List of document IDs to sync
        """
        while True:
            try:
                for doc_id in document_ids:
                    # Check if sync needed
                    last_sync = self.last_sync_times.get(doc_id)
                    if last_sync:
                        time_since_sync = datetime.now() - last_sync
                        if time_since_sync.total_seconds() < self.sync_interval_minutes * 60:
                            continue

                    # Create sync job
                    logger.info(f"Auto-syncing document {doc_id}")
                    await self.sync_content(
                        doc_id,
                        channels=[Channel.EMAIL, Channel.WEBSITE],
                        correlation_id=f"auto_sync_{datetime.now().isoformat()}"
                    )

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in auto-sync: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    def get_job_status(self, job_id: str) -> Optional[SyncJob]:
        """
        Get status of a sync job

        Args:
            job_id: Job ID

        Returns:
            Job object or None
        """
        return self.jobs.get(job_id)

    def get_recent_jobs(self, limit: int = 10) -> List[SyncJob]:
        """
        Get recent sync jobs

        Args:
            limit: Maximum number of jobs

        Returns:
            List of recent jobs
        """
        sorted_jobs = sorted(
            self.jobs.values(),
            key=lambda j: j.created_at,
            reverse=True
        )
        return sorted_jobs[:limit]

    def get_sync_statistics(self) -> Dict[str, Any]:
        """
        Get synchronization statistics

        Returns:
            Statistics dictionary
        """
        total_jobs = len(self.jobs)
        status_counts = defaultdict(int)
        channel_counts = defaultdict(int)
        error_counts = defaultdict(int)

        for job in self.jobs.values():
            status_counts[job.status.value] += 1

            for channel in job.channels:
                channel_counts[channel.value] += 1

            for error in job.errors:
                # Extract error type
                error_type = error.split(':')[0] if ':' in error else 'unknown'
                error_counts[error_type] += 1

        # Calculate success rate
        completed = status_counts.get(SyncStatus.COMPLETED.value, 0)
        partial = status_counts.get(SyncStatus.PARTIAL.value, 0)
        failed = status_counts.get(SyncStatus.FAILED.value, 0)
        total_finished = completed + partial + failed

        success_rate = (completed / total_finished * 100) if total_finished > 0 else 0

        return {
            'total_jobs': total_jobs,
            'active_jobs': len(self.active_jobs),
            'status_breakdown': dict(status_counts),
            'channel_breakdown': dict(channel_counts),
            'error_breakdown': dict(error_counts),
            'success_rate': round(success_rate, 2),
            'last_sync_times': {
                doc_id: last_sync.isoformat()
                for doc_id, last_sync in self.last_sync_times.items()
            }
        }

    async def retry_failed_jobs(self, max_age_hours: int = 24):
        """
        Retry failed jobs within specified age

        Args:
            max_age_hours: Maximum age of jobs to retry
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        failed_jobs = [
            job for job in self.jobs.values()
            if job.status in [SyncStatus.FAILED, SyncStatus.PARTIAL]
            and job.created_at > cutoff
        ]

        logger.info(f"Retrying {len(failed_jobs)} failed jobs")

        for job in failed_jobs:
            # Create new job with same parameters
            await self.sync_content(
                document_id=job.source_document_id,
                channels=job.channels,
                correlation_id=f"retry_{job.correlation_id}" if job.correlation_id else None
            )

    def cleanup_old_jobs(self, days: int = 7):
        """
        Clean up old job records

        Args:
            days: Number of days to keep
        """
        cutoff = datetime.now() - timedelta(days=days)
        old_jobs = [
            job_id for job_id, job in self.jobs.items()
            if job.created_at < cutoff
        ]

        for job_id in old_jobs:
            del self.jobs[job_id]

        logger.info(f"Cleaned up {len(old_jobs)} old jobs")