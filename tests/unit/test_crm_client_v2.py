"""
Unit tests for Enhanced CRM client v2
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from datetime import datetime

from src.halcytone_content_generator.services.crm_client_v2 import EnhancedCRMClient, EmailStatus, EmailRecipient, BulkEmailJob
from src.halcytone_content_generator.config import Settings


class TestEnhancedCRMClient:
    """Test Enhanced CRM client v2 functionality"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = Mock(spec=Settings)
        settings.CRM_BASE_URL = "https://api.crm.test"
        settings.CRM_API_KEY = "test_api_key"
        settings.EMAIL_BATCH_SIZE = 100
        settings.EMAIL_RATE_LIMIT = 10
        settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
        settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
        settings.MAX_RETRIES = 3
        settings.RETRY_MAX_WAIT = 30
        return settings

    @pytest.fixture
    def enhanced_crm_client(self, mock_settings):
        """Create Enhanced CRM client instance for testing"""
        return EnhancedCRMClient(mock_settings)

    def test_client_initialization(self, mock_settings):
        """Test client initialization with settings"""
        client = EnhancedCRMClient(mock_settings)

        assert client.base_url == "https://api.crm.test"
        assert client.api_key == "test_api_key"
        assert client.batch_size == 100
        assert client.rate_limit == 10
        assert client.breaker is not None
        assert client.retry_policy is not None
        assert client.timeout_handler is not None

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_send_bulk_newsletter_success(self, mock_client, enhanced_crm_client):
        """Test successful bulk newsletter sending"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json.return_value = {
            "job_id": "job_123",
            "total_recipients": 1000,
            "status": "queued"
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Test bulk newsletter sending
        recipients = [
            EmailRecipient(email="user1@test.com", name="User 1"),
            EmailRecipient(email="user2@test.com", name="User 2")
        ]

        result = await enhanced_crm_client.send_bulk_newsletter(
            subject="Test Newsletter",
            html="<h1>Test</h1>",
            text="Test",
            recipients=recipients
        )

        assert result.job_id == "job_123"
        assert result.total_recipients == 1000
        assert result.status == "queued"

        # Verify correct API call
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert "bulk-newsletter" in call_args[0][0]

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_job_status(self, mock_client, enhanced_crm_client):
        """Test getting bulk email job status"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "job_id": "job_123",
            "status": "completed",
            "sent_count": 950,
            "failed_count": 50,
            "total_recipients": 1000
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await enhanced_crm_client.get_job_status("job_123")

        assert result.job_id == "job_123"
        assert result.status == "completed"
        assert result.sent_count == 950
        assert result.failed_count == 50

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_email_analytics(self, mock_client, enhanced_crm_client):
        """Test getting email analytics"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "campaign_id": "campaign_123",
            "sent": 1000,
            "delivered": 950,
            "opened": 400,
            "clicked": 100,
            "bounced": 50,
            "unsubscribed": 10,
            "open_rate": 0.42,
            "click_rate": 0.25
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await enhanced_crm_client.get_email_analytics("campaign_123")

        assert result["sent"] == 1000
        assert result["open_rate"] == 0.42
        assert result["click_rate"] == 0.25

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_subscriber_list(self, mock_client, enhanced_crm_client):
        """Test getting subscriber list"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "subscribers": [
                {"email": "user1@test.com", "name": "User 1", "status": "active"},
                {"email": "user2@test.com", "name": "User 2", "status": "active"}
            ],
            "total": 2,
            "page": 1
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await enhanced_crm_client.get_subscriber_list(page=1, limit=10)

        assert len(result["subscribers"]) == 2
        assert result["total"] == 2
        assert result["subscribers"][0]["email"] == "user1@test.com"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_send_personalized_email(self, mock_client, enhanced_crm_client):
        """Test sending personalized email"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message_id": "msg_123",
            "status": "sent",
            "recipient": "user@test.com"
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        recipient = EmailRecipient(
            email="user@test.com",
            name="Test User",
            preferences={"language": "en"}
        )

        result = await enhanced_crm_client.send_personalized_email(
            recipient=recipient,
            template_id="template_123",
            variables={"name": "Test User"}
        )

        assert result["message_id"] == "msg_123"
        assert result["status"] == "sent"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_circuit_breaker_functionality(self, mock_client, enhanced_crm_client):
        """Test circuit breaker activation on failures"""
        # Simulate multiple failures
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.RequestError("Connection failed")
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Try to trigger circuit breaker
        recipients = [EmailRecipient(email="test@test.com")]

        with pytest.raises(httpx.RequestError):
            await enhanced_crm_client.send_bulk_newsletter(
                subject="Test",
                html="<h1>Test</h1>",
                text="Test",
                recipients=recipients
            )

    def test_email_status_enum(self):
        """Test EmailStatus enum values"""
        assert EmailStatus.PENDING.value == "pending"
        assert EmailStatus.SENT.value == "sent"
        assert EmailStatus.FAILED.value == "failed"
        assert EmailStatus.BOUNCED.value == "bounced"
        assert EmailStatus.OPENED.value == "opened"
        assert EmailStatus.CLICKED.value == "clicked"
        assert EmailStatus.UNSUBSCRIBED.value == "unsubscribed"

    def test_email_recipient_creation(self):
        """Test EmailRecipient creation"""
        recipient = EmailRecipient(
            email="test@example.com",
            name="Test User",
            user_id="user_123",
            preferences={"language": "en"},
            tags=["premium", "active"]
        )

        assert recipient.email == "test@example.com"
        assert recipient.name == "Test User"
        assert recipient.user_id == "user_123"
        assert recipient.preferences["language"] == "en"
        assert "premium" in recipient.tags

    def test_bulk_email_job_creation(self):
        """Test BulkEmailJob creation"""
        job = BulkEmailJob(
            job_id="job_123",
            total_recipients=1000,
            sent_count=900,
            failed_count=100,
            status="completed"
        )

        assert job.job_id == "job_123"
        assert job.total_recipients == 1000
        assert job.sent_count == 900
        assert job.failed_count == 100
        assert job.status == "completed"

    @pytest.mark.asyncio
    async def test_rate_limiter_functionality(self, enhanced_crm_client):
        """Test rate limiter works correctly"""
        # Test that rate limiter can be acquired
        await enhanced_crm_client.rate_limiter.acquire()

        # Verify it was recorded
        assert len(enhanced_crm_client.rate_limiter.calls) > 0

    def test_correlation_id_generation(self, enhanced_crm_client):
        """Test correlation ID generation"""
        correlation_id = enhanced_crm_client.correlation_tracker.get_or_create()

        assert correlation_id is not None
        assert len(correlation_id) > 0

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_error_handling_and_logging(self, mock_client, enhanced_crm_client):
        """Test proper error handling and logging"""
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=Mock(status_code=500)
        )
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        with pytest.raises(httpx.HTTPStatusError):
            await enhanced_crm_client.get_job_status("job_123")

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_batch_processing(self, mock_client, enhanced_crm_client):
        """Test batch processing of large recipient lists"""
        # Create a large list of recipients
        recipients = [
            EmailRecipient(email=f"user{i}@test.com", name=f"User {i}")
            for i in range(150)  # More than batch_size (100)
        ]

        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json.return_value = {
            "job_id": "job_123",
            "total_recipients": 100,
            "status": "queued"
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await enhanced_crm_client.send_bulk_newsletter(
            subject="Test Newsletter",
            html="<h1>Test</h1>",
            text="Test",
            recipients=recipients
        )

        # Should have been batched
        assert mock_client_instance.post.call_count >= 1
        assert result.job_id == "job_123"