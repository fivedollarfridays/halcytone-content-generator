"""
Platform API client for website content publishing
"""
import httpx
from datetime import datetime
from typing import Dict, Optional
import logging

from ..config import Settings
from ..core.resilience import CircuitBreaker, RetryPolicy
from ..schemas.content import WebPublishResult

logger = logging.getLogger(__name__)


class PlatformClient:
    """
    Client for interacting with Platform API for content publishing
    """

    def __init__(self, settings: Settings):
        """
        Initialize Platform client

        Args:
            settings: Application settings
        """
        self.base_url = settings.PLATFORM_BASE_URL
        self.api_key = settings.PLATFORM_API_KEY
        self.breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        )
        self.retry = RetryPolicy(
            max_retries=settings.MAX_RETRIES,
            base_delay=1.0,
            max_delay=settings.RETRY_MAX_WAIT
        )

    @RetryPolicy(max_retries=3)
    async def publish_update(
        self,
        title: str,
        content: str,
        excerpt: str
    ) -> Dict:
        """
        Publish content update to website

        Args:
            title: Update title
            content: Update content (markdown)
            excerpt: Brief excerpt

        Returns:
            Publication result dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/updates",
                    json={
                        "title": title,
                        "content": content,
                        "excerpt": excerpt,
                        "published": True,
                        "created_at": datetime.utcnow().isoformat()
                    },
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    timeout=15.0
                )

                response.raise_for_status()
                result = response.json()

                logger.info(f"Web update published successfully: {result.get('id')}")
                return result

        except httpx.RequestError as e:
            logger.error(f"Platform API request failed: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Platform API returned error status: {e.response.status_code}")
            raise

    async def get_recent_updates(self, limit: int = 10) -> list:
        """
        Get recent published updates

        Args:
            limit: Number of updates to retrieve

        Returns:
            List of recent updates
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/updates",
                    params={"limit": limit},
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )

                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to get recent updates: {e}")
            return []

    async def test_connection(self) -> bool:
        """
        Test connection to Platform API

        Returns:
            True if connection successful
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Platform API connection test failed: {e}")
            return False