"""
CRM client for email distribution
"""
import httpx
from typing import Dict, Optional
import logging

from ..config import Settings
from ..core.resilience import CircuitBreaker, RetryPolicy
from ..schemas.content import EmailDeliveryResult

logger = logging.getLogger(__name__)


class CRMClient:
    """
    Client for interacting with CRM service for email distribution
    """

    def __init__(self, settings: Settings):
        """
        Initialize CRM client

        Args:
            settings: Application settings
        """
        self.base_url = settings.CRM_BASE_URL
        self.api_key = settings.CRM_API_KEY
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
    async def send_newsletter(
        self,
        subject: str,
        html: str,
        text: str
    ) -> Dict:
        """
        Send newsletter via CRM bulk email endpoint

        Args:
            subject: Email subject
            html: HTML content
            text: Plain text content

        Returns:
            Delivery result dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/notifications/newsletter",
                    json={
                        "subject": subject,
                        "html": html,
                        "text": text
                    },
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    timeout=30.0  # Longer timeout for bulk operations
                )

                response.raise_for_status()
                result = response.json()

                logger.info(f"Newsletter sent successfully: {result}")
                return result

        except httpx.RequestError as e:
            logger.error(f"CRM request failed: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"CRM returned error status: {e.response.status_code}")
            raise

    async def get_subscriber_count(self) -> int:
        """
        Get count of newsletter subscribers

        Returns:
            Number of active subscribers
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/subscribers/count",
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )

                response.raise_for_status()
                data = response.json()
                return data.get("count", 0)

        except Exception as e:
            logger.error(f"Failed to get subscriber count: {e}")
            return 0

    async def test_connection(self) -> bool:
        """
        Test connection to CRM service

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
            logger.error(f"CRM connection test failed: {e}")
            return False