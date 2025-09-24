"""
Enhanced CRM client with advanced features for reliable email distribution
"""
import httpx
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import json
from enum import Enum
import hashlib
import time

from ..config import Settings
from ..core.resilience import CircuitBreaker, RetryPolicy, TimeoutHandler
from ..schemas.content import EmailDeliveryResult

logger = logging.getLogger(__name__)


class EmailStatus(Enum):
    """Email delivery status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"
    UNSUBSCRIBED = "unsubscribed"


@dataclass
class EmailRecipient:
    """Email recipient data"""
    email: str
    name: Optional[str] = None
    user_id: Optional[str] = None
    preferences: Dict[str, Any] = None
    tags: List[str] = None


@dataclass
class BulkEmailJob:
    """Bulk email job tracking"""
    job_id: str
    total_recipients: int
    sent_count: int = 0
    failed_count: int = 0
    status: str = "pending"
    started_at: datetime = None
    completed_at: datetime = None
    errors: List[str] = None


class RateLimiter:
    """Rate limiter for API calls"""

    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter

        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        now = time.time()

        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls
                     if now - call_time < self.time_window]

        # If we've hit the limit, wait
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                return await self.acquire()

        # Record this call
        self.calls.append(now)


class EnhancedCRMClient:
    """
    Enhanced CRM client with advanced reliability and monitoring features
    """

    def __init__(self, settings: Settings):
        """
        Initialize enhanced CRM client

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.dry_run_mode = settings.DRY_RUN_MODE or settings.DRY_RUN
        self.use_mock_services = settings.USE_MOCK_SERVICES

        # Use mock service URL if in dry run mode
        if self.dry_run_mode and self.use_mock_services:
            self.base_url = "http://localhost:8001"  # Mock CRM service
            self.api_key = "mock-crm-api-key"
            logger.info("CRM Client: Using mock service for dry run mode")
        else:
            self.base_url = settings.CRM_BASE_URL
            self.api_key = settings.CRM_API_KEY

        self.batch_size = settings.EMAIL_BATCH_SIZE
        self.rate_limit = settings.EMAIL_RATE_LIMIT

        # Initialize circuit breaker
        self.breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            expected_exception=httpx.RequestError
        )

        # Initialize retry policy
        self.retry_policy = RetryPolicy(
            max_retries=settings.MAX_RETRIES,
            base_delay=1.0,
            max_delay=settings.RETRY_MAX_WAIT
        )

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            max_calls=self.rate_limit,
            time_window=1  # per second
        )

        # Track active jobs
        self.active_jobs: Dict[str, BulkEmailJob] = {}

    async def send_newsletter_bulk(
        self,
        subject: str,
        html: str,
        text: str,
        recipient_filter: Optional[Dict] = None,
        test_mode: bool = False
    ) -> BulkEmailJob:
        """
        Send newsletter to multiple recipients with advanced handling

        Args:
            subject: Email subject
            html: HTML content
            text: Plain text content
            recipient_filter: Optional filter for recipients
            test_mode: If true, only send to test recipients

        Returns:
            BulkEmailJob with results
        """
        # Create job ID
        job_id = self._generate_job_id(subject)

        # Get recipients
        recipients = await self._fetch_recipients(recipient_filter, test_mode)

        if not recipients:
            logger.warning("No recipients found for newsletter")
            return BulkEmailJob(
                job_id=job_id,
                total_recipients=0,
                status="completed",
                errors=["No recipients found"]
            )

        # Create and track job
        job = BulkEmailJob(
            job_id=job_id,
            total_recipients=len(recipients),
            started_at=datetime.now(),
            errors=[]
        )
        self.active_jobs[job_id] = job

        # Process recipients in batches
        try:
            if self.dry_run_mode and self.use_mock_services:
                # Use mock service API directly
                result = await self._send_via_mock_service(subject, html, text, recipients)
                job.sent_count = result.get('recipients_count', len(recipients))
                job.failed_count = 0
            else:
                # Use original batch processing
                async for batch_result in self._process_batches(
                    recipients, subject, html, text
                ):
                    job.sent_count += batch_result['sent']
                    job.failed_count += batch_result['failed']

                    if batch_result.get('errors'):
                        job.errors.extend(batch_result['errors'])

            job.status = "completed"
            job.completed_at = datetime.now()

        except Exception as e:
            logger.error(f"Bulk email job {job_id} failed: {e}")
            job.status = "failed"
            job.errors.append(str(e))

        return job

    async def _process_batches(
        self,
        recipients: List[EmailRecipient],
        subject: str,
        html: str,
        text: str
    ) -> AsyncGenerator[Dict, None]:
        """
        Process recipients in batches with rate limiting

        Args:
            recipients: List of recipients
            subject: Email subject
            html: HTML content
            text: Plain text content

        Yields:
            Batch results
        """
        for i in range(0, len(recipients), self.batch_size):
            batch = recipients[i:i + self.batch_size]

            # Apply rate limiting
            await self.rate_limiter.acquire()

            # Send batch with circuit breaker protection
            result = await self._send_batch_with_circuit_breaker(
                batch, subject, html, text
            )

            yield result

    @CircuitBreaker(failure_threshold=5, recovery_timeout=60)
    @RetryPolicy(max_retries=3, base_delay=2.0)
    async def _send_batch_with_circuit_breaker(
        self,
        batch: List[EmailRecipient],
        subject: str,
        html: str,
        text: str
    ) -> Dict:
        """
        Send a batch of emails with circuit breaker protection

        Args:
            batch: Batch of recipients
            subject: Email subject
            html: HTML content
            text: Plain text content

        Returns:
            Batch result
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/email/batch",
                    json={
                        "recipients": [
                            {
                                "email": r.email,
                                "name": r.name,
                                "user_id": r.user_id,
                                "merge_vars": self._get_merge_vars(r)
                            }
                            for r in batch
                        ],
                        "subject": subject,
                        "html": html,
                        "text": text,
                        "tracking": {
                            "opens": True,
                            "clicks": True,
                            "unsubscribes": True
                        }
                    },
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json",
                        "X-Request-ID": self._generate_request_id()
                    },
                    timeout=30.0
                )

                response.raise_for_status()
                data = response.json()

                return {
                    'sent': data.get('successful', 0),
                    'failed': data.get('failed', 0),
                    'errors': data.get('errors', [])
                }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limited
                logger.warning("CRM rate limit hit, backing off")
                await asyncio.sleep(10)  # Back off for 10 seconds
                return await self._send_batch_with_circuit_breaker(
                    batch, subject, html, text
                )
            raise

        except Exception as e:
            logger.error(f"Batch send failed: {e}")
            return {
                'sent': 0,
                'failed': len(batch),
                'errors': [str(e)]
            }

    async def _fetch_recipients(
        self,
        filter_criteria: Optional[Dict] = None,
        test_mode: bool = False
    ) -> List[EmailRecipient]:
        """
        Fetch email recipients from CRM

        Args:
            filter_criteria: Optional filtering criteria
            test_mode: If true, only return test recipients

        Returns:
            List of email recipients
        """
        try:
            if test_mode:
                # Return test recipients only
                return [
                    EmailRecipient(
                        email="test@halcytone.com",
                        name="Test User",
                        user_id="test-001"
                    )
                ]

            async with httpx.AsyncClient() as client:
                params = {
                    "newsletter_opt_in": True,
                    "status": "active"
                }

                if filter_criteria:
                    params.update(filter_criteria)

                response = await client.get(
                    f"{self.base_url}/api/v1/users/subscribers",
                    params=params,
                    headers={"X-API-Key": self.api_key},
                    timeout=15.0
                )

                response.raise_for_status()
                data = response.json()

                return [
                    EmailRecipient(
                        email=user['email'],
                        name=user.get('name'),
                        user_id=user.get('id'),
                        preferences=user.get('preferences', {}),
                        tags=user.get('tags', [])
                    )
                    for user in data.get('users', [])
                ]

        except Exception as e:
            logger.error(f"Failed to fetch recipients: {e}")
            return []

    async def track_email_event(
        self,
        event_type: EmailStatus,
        email: str,
        campaign_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Track email events (opens, clicks, etc.)

        Args:
            event_type: Type of email event
            email: Recipient email
            campaign_id: Campaign/job ID
            metadata: Additional event metadata

        Returns:
            Success status
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/email/track",
                    json={
                        "event": event_type.value,
                        "email": email,
                        "campaign_id": campaign_id,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": metadata or {}
                    },
                    headers={"X-API-Key": self.api_key},
                    timeout=5.0
                )

                return response.status_code == 200

        except Exception as e:
            logger.error(f"Failed to track email event: {e}")
            return False

    async def get_email_analytics(
        self,
        campaign_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get email campaign analytics

        Args:
            campaign_id: Optional campaign ID
            start_date: Start date for analytics
            end_date: End date for analytics

        Returns:
            Analytics data
        """
        try:
            params = {}
            if campaign_id:
                params['campaign_id'] = campaign_id
            if start_date:
                params['start_date'] = start_date.isoformat()
            if end_date:
                params['end_date'] = end_date.isoformat()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/email/analytics",
                    params=params,
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )

                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to fetch analytics: {e}")
            return {
                'error': str(e),
                'total_sent': 0,
                'open_rate': 0,
                'click_rate': 0
            }

    async def manage_subscription(
        self,
        email: str,
        action: str,
        preferences: Optional[Dict] = None
    ) -> bool:
        """
        Manage email subscription preferences

        Args:
            email: User email
            action: subscribe, unsubscribe, or update
            preferences: Optional preference updates

        Returns:
            Success status
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/subscriptions/{action}",
                    json={
                        "email": email,
                        "preferences": preferences or {},
                        "timestamp": datetime.now().isoformat()
                    },
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )

                return response.status_code in [200, 201]

        except Exception as e:
            logger.error(f"Failed to manage subscription: {e}")
            return False

    async def validate_email_list(
        self,
        emails: List[str]
    ) -> Dict[str, List[str]]:
        """
        Validate a list of email addresses

        Args:
            emails: List of email addresses to validate

        Returns:
            Dictionary with valid and invalid emails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/email/validate",
                    json={"emails": emails},
                    headers={"X-API-Key": self.api_key},
                    timeout=15.0
                )

                response.raise_for_status()
                data = response.json()

                return {
                    'valid': data.get('valid', []),
                    'invalid': data.get('invalid', []),
                    'disposable': data.get('disposable', []),
                    'role_based': data.get('role_based', [])
                }

        except Exception as e:
            logger.error(f"Email validation failed: {e}")
            # Return all as valid in case of error (fail open)
            return {
                'valid': emails,
                'invalid': [],
                'disposable': [],
                'role_based': []
            }

    async def get_job_status(self, job_id: str) -> Optional[BulkEmailJob]:
        """
        Get status of a bulk email job

        Args:
            job_id: Job ID

        Returns:
            BulkEmailJob or None if not found
        """
        # Check local cache first
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]

        # Query CRM for job status
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/email/jobs/{job_id}",
                    headers={"X-API-Key": self.api_key},
                    timeout=5.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return BulkEmailJob(
                        job_id=job_id,
                        total_recipients=data.get('total_recipients', 0),
                        sent_count=data.get('sent_count', 0),
                        failed_count=data.get('failed_count', 0),
                        status=data.get('status', 'unknown'),
                        started_at=datetime.fromisoformat(data['started_at'])
                        if data.get('started_at') else None,
                        completed_at=datetime.fromisoformat(data['completed_at'])
                        if data.get('completed_at') else None,
                        errors=data.get('errors', [])
                    )

        except Exception as e:
            logger.error(f"Failed to get job status: {e}")

        return None

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test CRM connection and return service info

        Returns:
            Connection status and service information
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers={"X-API-Key": self.api_key},
                    timeout=5.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        'connected': True,
                        'service': data.get('service', 'CRM'),
                        'version': data.get('version', 'unknown'),
                        'features': data.get('features', [])
                    }
                else:
                    return {
                        'connected': False,
                        'error': f"HTTP {response.status_code}"
                    }

        except Exception as e:
            logger.error(f"CRM connection test failed: {e}")
            return {
                'connected': False,
                'error': str(e)
            }

    def _generate_job_id(self, subject: str) -> str:
        """Generate unique job ID"""
        timestamp = datetime.now().isoformat()
        hash_input = f"{subject}{timestamp}{self.api_key}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracking"""
        return hashlib.sha256(
            f"{time.time()}{self.api_key}".encode()
        ).hexdigest()[:16]

    def _get_merge_vars(self, recipient: EmailRecipient) -> Dict:
        """Get merge variables for email personalization"""
        return {
            'name': recipient.name or 'Subscriber',
            'email': recipient.email,
            'preferences_url': f"https://halcytone.com/preferences?u={recipient.user_id}",
            'unsubscribe_url': f"https://halcytone.com/unsubscribe?u={recipient.user_id}"
        }

    async def _send_via_mock_service(self, subject: str, html: str, text: str, recipients: List[EmailRecipient]) -> Dict:
        """Send email via mock CRM service for dry run testing"""

        try:
            # Prepare recipient list
            recipient_emails = [r.email for r in recipients]

            # Prepare request payload for mock API
            payload = {
                "subject": subject,
                "html_content": html,
                "text_content": text or "",
                "recipients": recipient_emails,
                "campaign_id": f"dry-run-{self._generate_job_id(subject)}"
            }

            logger.info(f"Sending email via mock CRM service: {subject} to {len(recipient_emails)} recipients")

            # Send to mock service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/email/send",
                    json=payload,
                    headers={
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )

                response.raise_for_status()
                result = response.json()

                logger.info(f"Mock CRM response: {result}")

                return {
                    'message_id': result.get('message_id'),
                    'status': result.get('status', 'sent'),
                    'recipients_count': result.get('recipients_count', len(recipient_emails)),
                    'timestamp': result.get('timestamp')
                }

        except Exception as e:
            logger.error(f"Mock CRM service error: {e}")
            # Return mock success for dry run resilience
            return {
                'message_id': f"mock-{self._generate_job_id(subject)}",
                'status': 'sent',
                'recipients_count': len(recipients),
                'timestamp': datetime.utcnow().isoformat()
            }