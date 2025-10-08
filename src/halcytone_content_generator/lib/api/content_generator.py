"""
Content Generator API Client
Specialized client for Content Generator API endpoints
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from ..base_client import APIClient, APIResponse, APIError

logger = logging.getLogger(__name__)


class ContentGeneratorClient(APIClient):
    """
    Content Generator API Client

    Provides convenient methods for interacting with Content Generator API endpoints
    including content generation, validation, synchronization, and health checks.

    Example:
        ```python
        client = ContentGeneratorClient(
            base_url="https://api.example.com",
            api_key="your-api-key"
        )

        # Generate content
        response = await client.generate_content(
            document_id="gdocs:123",
            channels=["email", "web"],
            send_email=True
        )

        # Check health
        health = await client.health_check()
        print(health.data)
        ```
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 60.0,  # Longer timeout for content generation
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize Content Generator client

        Args:
            base_url: Base URL for Content Generator API
            api_key: API key for authentication
            timeout: Request timeout in seconds (default 60s for generation)
            max_retries: Maximum retry attempts
            headers: Additional headers
        """
        super().__init__(base_url, api_key, timeout, max_retries, headers)
        logger.info(f"Initialized ContentGeneratorClient for {base_url}")

    # ========== Health & Status ==========

    async def health_check(self, correlation_id: Optional[str] = None) -> APIResponse:
        """
        Check API health status

        Returns:
            APIResponse with health status data
        """
        return await self.get('/health', correlation_id=correlation_id)

    async def readiness_check(self, correlation_id: Optional[str] = None) -> APIResponse:
        """
        Check if API is ready to serve requests

        Returns:
            APIResponse with readiness status
        """
        return await self.get('/ready', correlation_id=correlation_id)

    async def startup_probe(self, correlation_id: Optional[str] = None) -> APIResponse:
        """
        Check if API has started successfully

        Returns:
            APIResponse with startup status
        """
        return await self.get('/startup', correlation_id=correlation_id)

    async def metrics(self, correlation_id: Optional[str] = None) -> APIResponse:
        """
        Get API metrics

        Returns:
            APIResponse with metrics data
        """
        return await self.get('/metrics', correlation_id=correlation_id)

    # ========== Content Generation (V1) ==========

    async def generate_content(
        self,
        send_email: bool = False,
        publish_web: bool = False,
        publish_social: bool = False,
        document_id: Optional[str] = None,
        dry_run: bool = False,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        Generate content from living document (V1 API)

        Args:
            send_email: Whether to send email newsletter
            publish_web: Whether to publish to website
            publish_social: Whether to publish to social media
            document_id: Optional document ID to fetch from
            dry_run: If True, simulate without actually sending
            correlation_id: Optional correlation ID

        Returns:
            APIResponse with generation results
        """
        data = {
            "send_email": send_email,
            "publish_web": publish_web,
            "publish_social": publish_social,
            "dry_run": dry_run
        }

        if document_id:
            data["document_id"] = document_id

        return await self.post('/api/v1/generate-content', data=data, correlation_id=correlation_id)

    async def preview_content(
        self,
        document_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        Preview content without sending

        Args:
            document_id: Optional document ID
            correlation_id: Optional correlation ID

        Returns:
            APIResponse with preview data
        """
        params = {}
        if document_id:
            params["document_id"] = document_id

        return await self.get('/api/v1/preview', params=params, correlation_id=correlation_id)

    # ========== Content Synchronization (V2) ==========

    async def sync_content(
        self,
        document_id: str,
        channels: List[str],
        schedule_time: Optional[datetime] = None,
        dry_run: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        Synchronize content across channels (V2 API)

        Args:
            document_id: Document identifier (e.g., "gdocs:123", "notion:abc")
            channels: List of channels (email, website, social_twitter, social_linkedin, etc.)
            schedule_time: Optional datetime to schedule for future
            dry_run: If True, simulate without actually publishing
            metadata: Optional metadata to attach
            correlation_id: Optional correlation ID

        Returns:
            APIResponse with sync job information
        """
        data = {
            "document_id": document_id,
            "channels": channels,
            "dry_run": dry_run
        }

        if schedule_time:
            data["schedule_time"] = schedule_time.isoformat()

        if metadata:
            data["metadata"] = metadata

        return await self.post('/api/v2/content/sync', data=data,
                              correlation_id=correlation_id or str(uuid.uuid4()))

    async def get_sync_job(
        self,
        job_id: str,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        Get sync job status

        Args:
            job_id: Job identifier
            correlation_id: Optional correlation ID

        Returns:
            APIResponse with job status
        """
        return await self.get(f'/api/v2/content/sync/{job_id}', correlation_id=correlation_id)

    async def list_sync_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        List sync jobs

        Args:
            status: Optional status filter (pending, in_progress, completed, failed)
            limit: Maximum number of results
            offset: Result offset for pagination
            correlation_id: Optional correlation ID

        Returns:
            APIResponse with list of jobs
        """
        params = {
            "limit": limit,
            "offset": offset
        }

        if status:
            params["status"] = status

        return await self.get('/api/v2/content/sync', params=params, correlation_id=correlation_id)

    async def cancel_sync_job(
        self,
        job_id: str,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        Cancel a pending sync job

        Args:
            job_id: Job identifier
            correlation_id: Optional correlation ID

        Returns:
            APIResponse confirming cancellation
        """
        return await self.delete(f'/api/v2/content/sync/{job_id}', correlation_id=correlation_id)

    # ========== Content Validation ==========

    async def validate_content(
        self,
        content: Dict[str, Any],
        content_type: Optional[str] = None,
        strict: bool = True,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        Validate content structure and data

        Args:
            content: Content data to validate
            content_type: Content type (update, blog, announcement, etc.)
            strict: Whether to use strict validation
            correlation_id: Optional correlation ID

        Returns:
            APIResponse with validation results
        """
        data = {
            "content": content,
            "strict": strict
        }

        if content_type:
            data["content_type"] = content_type

        return await self.post('/api/v2/content/validate', data=data, correlation_id=correlation_id)

    # ========== Cache Management ==========

    async def invalidate_cache(
        self,
        cache_keys: Optional[List[str]] = None,
        pattern: Optional[str] = None,
        tags: Optional[List[str]] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        Invalidate cache entries

        Args:
            cache_keys: Specific cache keys to invalidate
            pattern: Pattern to match cache keys (e.g., "content:*")
            tags: Tags to match for invalidation
            correlation_id: Optional correlation ID

        Returns:
            APIResponse with invalidation results
        """
        data = {}

        if cache_keys:
            data["cache_keys"] = cache_keys

        if pattern:
            data["pattern"] = pattern

        if tags:
            data["tags"] = tags

        return await self.post('/api/v2/cache/invalidate', data=data, correlation_id=correlation_id)

    async def get_cache_stats(self, correlation_id: Optional[str] = None) -> APIResponse:
        """
        Get cache statistics

        Returns:
            APIResponse with cache statistics
        """
        return await self.get('/api/v2/cache/stats', correlation_id=correlation_id)

    async def clear_all_caches(self, correlation_id: Optional[str] = None) -> APIResponse:
        """
        Clear all caches (use with caution!)

        Returns:
            APIResponse confirming cache clear
        """
        return await self.post('/api/v2/cache/clear', correlation_id=correlation_id)

    # ========== Batch Operations ==========

    async def batch_generate(
        self,
        requests: List[Dict[str, Any]],
        parallel: bool = True,
        fail_fast: bool = False,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        Batch generate multiple content items

        Args:
            requests: List of generation requests
            parallel: Whether to process in parallel
            fail_fast: Whether to stop on first failure
            correlation_id: Optional correlation ID

        Returns:
            APIResponse with batch results
        """
        data = {
            "requests": requests,
            "parallel": parallel,
            "fail_fast": fail_fast
        }

        return await self.post('/api/v2/batch/generate', data=data,
                              timeout=120.0,  # Longer timeout for batch
                              correlation_id=correlation_id)

    # ========== Analytics & Reporting ==========

    async def get_content_analytics(
        self,
        content_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        channels: Optional[List[str]] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        Get content analytics

        Args:
            content_id: Optional specific content ID
            start_date: Optional start date for analytics
            end_date: Optional end date for analytics
            channels: Optional channel filter
            correlation_id: Optional correlation ID

        Returns:
            APIResponse with analytics data
        """
        params = {}

        if content_id:
            params["content_id"] = content_id

        if start_date:
            params["start_date"] = start_date.isoformat()

        if end_date:
            params["end_date"] = end_date.isoformat()

        if channels:
            params["channels"] = ",".join(channels)

        return await self.get('/api/v2/analytics/content', params=params, correlation_id=correlation_id)

    async def get_email_analytics(
        self,
        campaign_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        Get email campaign analytics

        Args:
            campaign_id: Optional campaign ID
            correlation_id: Optional correlation ID

        Returns:
            APIResponse with email analytics
        """
        params = {}
        if campaign_id:
            params["campaign_id"] = campaign_id

        return await self.get('/api/v2/analytics/email', params=params, correlation_id=correlation_id)

    # ========== Configuration ==========

    async def get_config(self, correlation_id: Optional[str] = None) -> APIResponse:
        """
        Get current configuration

        Returns:
            APIResponse with configuration data
        """
        return await self.get('/api/v2/config', correlation_id=correlation_id)

    async def update_config(
        self,
        config_updates: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        Update configuration

        Args:
            config_updates: Configuration updates
            correlation_id: Optional correlation ID

        Returns:
            APIResponse confirming update
        """
        return await self.patch('/api/v2/config', data=config_updates, correlation_id=correlation_id)

    # ========== Helpers ==========

    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID"""
        return str(uuid.uuid4())

    async def test_connection(self) -> bool:
        """
        Test if connection to API is working

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = await self.health_check()
            return response.is_success()
        except APIError as e:
            logger.error(f"Connection test failed: {e}")
            return False
