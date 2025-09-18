"""
Unit tests for CRM integration
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.halcytone_content_generator.services.crm_client_v2 import (
    EnhancedCRMClient,
    EmailRecipient,
    BulkEmailJob,
    EmailStatus,
    RateLimiter
)
from src.halcytone_content_generator.services.email_analytics import (
    EmailAnalyticsService,
    EmailMetrics
)
from src.halcytone_content_generator.core.auth_middleware import (
    APIKeyValidator,
    HMACValidator
)


class TestRateLimiter:
    """Test rate limiting functionality"""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_calls_within_limit(self):
        """Test that rate limiter allows calls within limit"""
        limiter = RateLimiter(max_calls=5, time_window=1)

        # Should allow 5 calls immediately
        for _ in range(5):
            await limiter.acquire()

        # Record time
        assert len(limiter.calls) == 5

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_excess_calls(self):
        """Test that rate limiter blocks calls exceeding limit"""
        limiter = RateLimiter(max_calls=2, time_window=0.1)

        # First two calls should be immediate
        await limiter.acquire()
        await limiter.acquire()

        # Third call should be delayed
        start = asyncio.get_event_loop().time()
        await limiter.acquire()
        elapsed = asyncio.get_event_loop().time() - start

        # Should have waited at least some time
        assert elapsed > 0


class TestEnhancedCRMClient:
    """Test enhanced CRM client functionality"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = Mock()
        settings.CRM_BASE_URL = "http://test-crm.com"
        settings.CRM_API_KEY = "test-key"
        settings.EMAIL_BATCH_SIZE = 10
        settings.EMAIL_RATE_LIMIT = 100
        settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
        settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
        settings.MAX_RETRIES = 3
        settings.RETRY_MAX_WAIT = 60
        return settings

    @pytest.fixture
    def crm_client(self, mock_settings):
        """Create CRM client for testing"""
        return EnhancedCRMClient(mock_settings)

    @pytest.mark.asyncio
    async def test_send_newsletter_bulk_success(self, crm_client):
        """Test successful bulk newsletter sending"""
        # Mock recipients
        recipients = [
            EmailRecipient(email=f"user{i}@test.com", name=f"User {i}")
            for i in range(5)
        ]

        with patch.object(crm_client, '_fetch_recipients', return_value=recipients):
            with patch.object(crm_client, '_send_batch_with_circuit_breaker',
                            return_value={'sent': 5, 'failed': 0, 'errors': []}):

                job = await crm_client.send_newsletter_bulk(
                    subject="Test Newsletter",
                    html="<h1>Test</h1>",
                    text="Test",
                    test_mode=False
                )

                assert job.total_recipients == 5
                assert job.sent_count == 5
                assert job.failed_count == 0
                assert job.status == "completed"

    @pytest.mark.asyncio
    async def test_send_newsletter_test_mode(self, crm_client):
        """Test newsletter sending in test mode"""
        with patch.object(crm_client, '_send_batch_with_circuit_breaker',
                        return_value={'sent': 1, 'failed': 0, 'errors': []}):

            job = await crm_client.send_newsletter_bulk(
                subject="Test Newsletter",
                html="<h1>Test</h1>",
                text="Test",
                test_mode=True
            )

            assert job.total_recipients == 1
            assert job.sent_count == 1

    @pytest.mark.asyncio
    async def test_batch_processing(self, crm_client):
        """Test batch processing of recipients"""
        recipients = [
            EmailRecipient(email=f"user{i}@test.com")
            for i in range(25)  # More than batch size
        ]

        batches_processed = 0
        async def mock_send(batch, *args):
            nonlocal batches_processed
            batches_processed += 1
            return {'sent': len(batch), 'failed': 0, 'errors': []}

        with patch.object(crm_client, '_fetch_recipients', return_value=recipients):
            with patch.object(crm_client, '_send_batch_with_circuit_breaker',
                            side_effect=mock_send):

                job = await crm_client.send_newsletter_bulk(
                    subject="Test",
                    html="<h1>Test</h1>",
                    text="Test"
                )

                # Should process 3 batches (10, 10, 5)
                assert batches_processed == 3
                assert job.sent_count == 25

    def test_job_id_generation(self, crm_client):
        """Test job ID generation"""
        job_id1 = crm_client._generate_job_id("Subject 1")
        job_id2 = crm_client._generate_job_id("Subject 2")

        assert job_id1 != job_id2
        assert len(job_id1) == 16

    def test_merge_vars_generation(self, crm_client):
        """Test merge variables generation"""
        recipient = EmailRecipient(
            email="test@example.com",
            name="Test User",
            user_id="123"
        )

        merge_vars = crm_client._get_merge_vars(recipient)

        assert merge_vars['name'] == "Test User"
        assert merge_vars['email'] == "test@example.com"
        assert "preferences_url" in merge_vars
        assert "unsubscribe_url" in merge_vars


class TestEmailAnalytics:
    """Test email analytics functionality"""

    @pytest.fixture
    def analytics(self):
        """Create analytics service for testing"""
        return EmailAnalyticsService()

    def test_track_send(self, analytics):
        """Test tracking email sends"""
        analytics.track_send("campaign-1", ["user1@test.com", "user2@test.com"])

        metrics = analytics.get_campaign_metrics("campaign-1")
        assert metrics['total_sent'] == 2
        assert len(analytics.recipients) == 2

    def test_track_open(self, analytics):
        """Test tracking email opens"""
        analytics.track_send("campaign-1", ["user1@test.com"])
        analytics.track_delivery("campaign-1", "user1@test.com")
        analytics.track_open("campaign-1", "user1@test.com")

        metrics = analytics.get_campaign_metrics("campaign-1")
        assert metrics['total_opened'] == 1
        assert metrics['unique_opens'] == 1

        # Track another open from same user
        analytics.track_open("campaign-1", "user1@test.com")
        metrics = analytics.get_campaign_metrics("campaign-1")
        assert metrics['total_opened'] == 2
        assert metrics['unique_opens'] == 1  # Still 1 unique

    def test_track_click(self, analytics):
        """Test tracking link clicks"""
        analytics.track_send("campaign-1", ["user1@test.com"])
        analytics.track_delivery("campaign-1", "user1@test.com")
        analytics.track_open("campaign-1", "user1@test.com")
        analytics.track_click("campaign-1", "user1@test.com", "https://example.com")

        metrics = analytics.get_campaign_metrics("campaign-1")
        assert metrics['total_clicked'] == 1
        assert metrics['unique_clicks'] == 1
        assert metrics['popular_links'][0][0] == "https://example.com"

    def test_engagement_score_calculation(self, analytics):
        """Test recipient engagement score calculation"""
        # Simulate engaged recipient
        analytics.track_send("campaign-1", ["user1@test.com"])
        analytics.track_open("campaign-1", "user1@test.com")
        analytics.track_click("campaign-1", "user1@test.com", "https://example.com")

        engagement = analytics.get_recipient_engagement("user1@test.com")
        assert engagement['campaigns_received'] == 1
        assert engagement['campaigns_opened'] == 1
        assert engagement['campaigns_clicked'] == 1
        assert engagement['engagement_score'] > 0

    def test_bounce_tracking(self, analytics):
        """Test bounce tracking"""
        analytics.track_send("campaign-1", ["user1@test.com"])
        analytics.track_bounce("campaign-1", "user1@test.com", "hard")

        metrics = analytics.get_campaign_metrics("campaign-1")
        assert metrics['total_bounced'] == 1

        engagement = analytics.get_recipient_engagement("user1@test.com")
        assert engagement['status'] == "bounced"

    def test_aggregate_metrics(self, analytics):
        """Test aggregate metrics calculation"""
        # Simulate multiple campaigns
        analytics.track_send("campaign-1", ["user1@test.com", "user2@test.com"])
        analytics.track_send("campaign-2", ["user1@test.com", "user3@test.com"])

        aggregate = analytics.get_aggregate_metrics()
        assert aggregate['total_campaigns'] == 2
        assert aggregate['total_sent'] == 4

    def test_time_based_metrics(self, analytics):
        """Test time-based metrics"""
        analytics.track_send("campaign-1", ["user1@test.com"])
        analytics.track_open("campaign-1", "user1@test.com")
        analytics.track_click("campaign-1", "user1@test.com", "https://example.com")

        time_metrics = analytics.get_time_based_metrics("campaign-1", "hourly")
        assert len(time_metrics) > 0
        assert 'opens' in time_metrics[0]
        assert 'clicks' in time_metrics[0]


class TestAPIKeyAuthentication:
    """Test API key authentication"""

    def test_api_key_validation_success(self):
        """Test successful API key validation"""
        validator = APIKeyValidator({
            "test-key": {
                "service": "test",
                "permissions": ["read", "write"],
                "rate_limit": 100
            }
        })

        key_data = validator.validate_api_key("test-key")
        assert key_data['service'] == "test"
        assert "read" in key_data['permissions']

    def test_api_key_validation_failure(self):
        """Test API key validation failure"""
        validator = APIKeyValidator()

        with pytest.raises(Exception):  # HTTPException
            validator.validate_api_key("invalid-key")

    def test_rate_limit_checking(self):
        """Test API key rate limit checking"""
        validator = APIKeyValidator({
            "test-key": {
                "service": "test",
                "permissions": ["read"],
                "rate_limit": 2
            }
        })

        # First two calls should succeed
        validator.validate_api_key("test-key")
        validator.validate_api_key("test-key")

        # Third call should fail due to rate limit
        with pytest.raises(Exception):  # HTTPException with 429
            validator.validate_api_key("test-key")

    def test_api_key_generation(self):
        """Test API key generation"""
        validator = APIKeyValidator()
        key1 = validator.generate_api_key("service1")
        key2 = validator.generate_api_key("service2")

        assert key1 != key2
        assert len(key1) == 32

    def test_api_key_revocation(self):
        """Test API key revocation"""
        validator = APIKeyValidator({
            "test-key": {
                "service": "test",
                "permissions": ["read"]
            }
        })

        # Key should work initially
        validator.validate_api_key("test-key")

        # Revoke key
        validator.revoke_api_key("test-key")

        # Key should now be blocked
        with pytest.raises(Exception):  # HTTPException with 403
            validator.validate_api_key("test-key")


class TestHMACValidation:
    """Test HMAC signature validation"""

    def test_signature_generation(self):
        """Test HMAC signature generation"""
        validator = HMACValidator("secret-key")
        payload = b"test payload"
        signature = validator.generate_signature(payload)

        assert len(signature) == 64  # SHA256 hex digest

    def test_signature_validation_success(self):
        """Test successful signature validation"""
        validator = HMACValidator("secret-key")
        payload = b"test payload"
        signature = validator.generate_signature(payload)

        assert validator.validate_signature(payload, signature) is True

    def test_signature_validation_failure(self):
        """Test signature validation failure"""
        validator = HMACValidator("secret-key")
        payload = b"test payload"

        assert validator.validate_signature(payload, "invalid-signature") is False

    def test_signature_tampering_detection(self):
        """Test detection of tampered payload"""
        validator = HMACValidator("secret-key")
        payload = b"original payload"
        signature = validator.generate_signature(payload)

        tampered_payload = b"tampered payload"
        assert validator.validate_signature(tampered_payload, signature) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])