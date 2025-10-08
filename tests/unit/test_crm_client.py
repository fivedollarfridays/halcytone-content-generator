"""
Unit tests for CRM client
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from halcytone_content_generator.services.crm_client import CRMClient
from halcytone_content_generator.config import Settings


class TestCRMClient:
    """Test CRM client functionality"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = Mock(spec=Settings)
        settings.CRM_BASE_URL = "https://api.crm.test"
        settings.CRM_API_KEY = "test_api_key"
        settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
        settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
        settings.MAX_RETRIES = 3
        settings.RETRY_MAX_WAIT = 30
        return settings

    @pytest.fixture
    def crm_client(self, mock_settings):
        """Create CRM client instance for testing"""
        return CRMClient(mock_settings)

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_send_newsletter_success(self, mock_client, crm_client):
        """Test successful newsletter sending"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"sent": 100, "failed": 0, "id": "newsletter_123"}
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Test newsletter sending
        result = await crm_client.send_newsletter(
            subject="Test Newsletter",
            html="<h1>Test</h1>",
            text="Test"
        )

        assert result["sent"] == 100
        assert result["failed"] == 0
        assert result["id"] == "newsletter_123"

        # Verify correct API call
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert call_args[0][0] == "https://api.crm.test/api/v1/notifications/newsletter"
        assert call_args[1]["json"]["subject"] == "Test Newsletter"
        assert call_args[1]["headers"]["X-API-Key"] == "test_api_key"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_send_newsletter_http_error(self, mock_client, crm_client):
        """Test newsletter sending with HTTP error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response
        )

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        with pytest.raises(httpx.HTTPStatusError):
            await crm_client.send_newsletter("Test", "<h1>Test</h1>", "Test")

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_send_newsletter_request_error(self, mock_client, crm_client):
        """Test newsletter sending with request error"""
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.RequestError("Connection failed")
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        with pytest.raises(httpx.RequestError):
            await crm_client.send_newsletter("Test", "<h1>Test</h1>", "Test")

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_subscriber_count_success(self, mock_client, crm_client):
        """Test successful subscriber count retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"count": 1500}
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await crm_client.get_subscriber_count()

        assert result == 1500
        mock_client_instance.get.assert_called_once_with(
            "https://api.crm.test/api/v1/users/subscribers/count",
            headers={"X-API-Key": "test_api_key"},
            timeout=10.0
        )

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_subscriber_count_error(self, mock_client, crm_client):
        """Test subscriber count retrieval with error"""
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = Exception("API Error")
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await crm_client.get_subscriber_count()

        assert result == 0  # Should return 0 on error

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_subscriber_count_missing_count(self, mock_client, crm_client):
        """Test subscriber count with missing count in response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No count field
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await crm_client.get_subscriber_count()

        assert result == 0  # Should return 0 when count is missing

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_test_connection_success(self, mock_client, crm_client):
        """Test successful connection test"""
        mock_response = Mock()
        mock_response.status_code = 200

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await crm_client.test_connection()

        assert result is True
        mock_client_instance.get.assert_called_once_with(
            "https://api.crm.test/health",
            timeout=5.0
        )

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_test_connection_failure(self, mock_client, crm_client):
        """Test connection test failure"""
        mock_response = Mock()
        mock_response.status_code = 500

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await crm_client.test_connection()

        assert result is False

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_test_connection_exception(self, mock_client, crm_client):
        """Test connection test with exception"""
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = Exception("Connection failed")
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await crm_client.test_connection()

        assert result is False

    def test_client_initialization(self, mock_settings):
        """Test client initialization with settings"""
        client = CRMClient(mock_settings)

        assert client.base_url == "https://api.crm.test"
        assert client.api_key == "test_api_key"
        assert client.breaker is not None
        assert client.retry is not None