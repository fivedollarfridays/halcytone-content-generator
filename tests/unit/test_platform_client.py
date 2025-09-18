"""
Unit tests for platform client service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import httpx
from datetime import datetime

from src.halcytone_content_generator.services.platform_client import PlatformClient


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    settings = MagicMock()
    settings.PLATFORM_BASE_URL = "https://api.platform.test"
    settings.PLATFORM_API_KEY = "test_api_key"
    settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
    settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
    settings.MAX_RETRIES = 3
    settings.RETRY_MAX_WAIT = 30
    return settings


@pytest.fixture
def platform_client(mock_settings):
    """Create a PlatformClient instance for testing"""
    return PlatformClient(mock_settings)


@pytest.fixture
def sample_update_data():
    """Sample update data for testing"""
    return {
        'title': 'Test Update',
        'content': '# Test Update\n\nThis is test content',
        'excerpt': 'This is a test excerpt'
    }


class TestPlatformClientInit:
    """Test PlatformClient initialization"""

    def test_init(self, mock_settings):
        """Test PlatformClient initialization"""
        client = PlatformClient(mock_settings)

        assert client.base_url == "https://api.platform.test"
        assert client.api_key == "test_api_key"
        assert client.breaker is not None
        assert client.retry is not None

    def test_init_with_different_settings(self):
        """Test initialization with different settings"""
        settings = MagicMock()
        settings.PLATFORM_BASE_URL = "https://custom.api.com"
        settings.PLATFORM_API_KEY = "custom_key"
        settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3
        settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 30
        settings.MAX_RETRIES = 5
        settings.RETRY_MAX_WAIT = 60

        client = PlatformClient(settings)

        assert client.base_url == "https://custom.api.com"
        assert client.api_key == "custom_key"


class TestPublishUpdate:
    """Test publish_update method"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_publish_update_success(self, mock_async_client, platform_client, sample_update_data):
        """Test successful update publication"""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'id': 'update_123',
            'url': 'https://platform.test/updates/update_123',
            'published': True,
            'created_at': '2024-03-15T10:30:00Z'
        }

        # Mock client context manager
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Call method
        result = await platform_client.publish_update(
            sample_update_data['title'],
            sample_update_data['content'],
            sample_update_data['excerpt']
        )

        # Verify result
        assert result['id'] == 'update_123'
        assert result['url'] == 'https://platform.test/updates/update_123'
        assert result['published'] is True

        # Verify request was made correctly
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args

        # Check URL
        assert call_args[0][0] == "https://api.platform.test/api/v1/updates"

        # Check request data
        request_data = call_args[1]['json']
        assert request_data['title'] == 'Test Update'
        assert request_data['content'] == '# Test Update\n\nThis is test content'
        assert request_data['excerpt'] == 'This is a test excerpt'
        assert request_data['published'] is True
        assert 'created_at' in request_data

        # Check headers
        headers = call_args[1]['headers']
        assert headers['X-API-Key'] == 'test_api_key'
        assert headers['Content-Type'] == 'application/json'

        # Check timeout
        assert call_args[1]['timeout'] == 15.0

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_publish_update_request_error(self, mock_async_client, platform_client, sample_update_data):
        """Test publish update with request error"""
        # Mock client to raise request error
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.RequestError("Connection failed")
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Call method and expect exception
        with pytest.raises(httpx.RequestError):
            await platform_client.publish_update(
                sample_update_data['title'],
                sample_update_data['content'],
                sample_update_data['excerpt']
            )

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_publish_update_http_status_error(self, mock_async_client, platform_client, sample_update_data):
        """Test publish update with HTTP status error"""
        # Mock response with error status
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "HTTP Error", request=Mock(), response=Mock(status_code=400)
        )
        mock_response.response.status_code = 400

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Call method and expect exception
        with pytest.raises(httpx.HTTPStatusError):
            await platform_client.publish_update(
                sample_update_data['title'],
                sample_update_data['content'],
                sample_update_data['excerpt']
            )

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_publish_update_with_special_characters(self, mock_async_client, platform_client):
        """Test publish update with special characters in content"""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'id': 'test', 'url': 'test', 'published': True}

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Test with special characters
        title = "Update with émojis 🚀 and unicode ñ"
        content = "Content with <html> tags & special chars: 你好"
        excerpt = "Excerpt with quotes \"test\" and apostrophes 'test'"

        result = await platform_client.publish_update(title, content, excerpt)

        # Verify the request was made with special characters
        call_args = mock_client_instance.post.call_args
        request_data = call_args[1]['json']
        assert request_data['title'] == title
        assert request_data['content'] == content
        assert request_data['excerpt'] == excerpt

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_publish_update_empty_content(self, mock_async_client, platform_client):
        """Test publish update with empty content"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'id': 'empty', 'published': True}

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        result = await platform_client.publish_update("", "", "")

        # Should handle empty content gracefully
        call_args = mock_client_instance.post.call_args
        request_data = call_args[1]['json']
        assert request_data['title'] == ""
        assert request_data['content'] == ""
        assert request_data['excerpt'] == ""

    @patch('src.halcytone_content_generator.services.platform_client.datetime')
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_publish_update_datetime_handling(
        self, mock_async_client, mock_datetime, platform_client, sample_update_data
    ):
        """Test that datetime is properly formatted in request"""
        # Mock datetime
        mock_now = datetime(2024, 3, 15, 10, 30, 45, 123456)
        mock_datetime.utcnow.return_value = mock_now

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'id': 'test', 'published': True}

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        await platform_client.publish_update(
            sample_update_data['title'],
            sample_update_data['content'],
            sample_update_data['excerpt']
        )

        # Verify datetime formatting
        call_args = mock_client_instance.post.call_args
        request_data = call_args[1]['json']
        assert request_data['created_at'] == "2024-03-15T10:30:45.123456"


class TestGetRecentUpdates:
    """Test get_recent_updates method"""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_recent_updates_success(self, mock_async_client, platform_client):
        """Test successful retrieval of recent updates"""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {
                'id': 'update1',
                'title': 'First Update',
                'created_at': '2024-03-15T10:00:00Z'
            },
            {
                'id': 'update2',
                'title': 'Second Update',
                'created_at': '2024-03-14T15:30:00Z'
            }
        ]

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Call method
        result = await platform_client.get_recent_updates()

        # Verify result
        assert len(result) == 2
        assert result[0]['id'] == 'update1'
        assert result[1]['id'] == 'update2'

        # Verify request
        mock_client_instance.get.assert_called_once()
        call_args = mock_client_instance.get.call_args

        assert call_args[0][0] == "https://api.platform.test/api/v1/updates"
        assert call_args[1]['params'] == {"limit": 10}
        assert call_args[1]['headers'] == {"X-API-Key": "test_api_key"}
        assert call_args[1]['timeout'] == 10.0

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_recent_updates_with_limit(self, mock_async_client, platform_client):
        """Test get recent updates with custom limit"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Call with custom limit
        result = await platform_client.get_recent_updates(limit=5)

        # Verify request parameters
        call_args = mock_client_instance.get.call_args
        assert call_args[1]['params'] == {"limit": 5}

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_recent_updates_error(self, mock_async_client, platform_client):
        """Test get recent updates with error"""
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = Exception("API Error")
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Should return empty list on error
        result = await platform_client.get_recent_updates()

        assert result == []

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_recent_updates_http_error(self, mock_async_client, platform_client):
        """Test get recent updates with HTTP error"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "HTTP Error", request=Mock(), response=Mock(status_code=404)
        )

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Should return empty list on HTTP error
        result = await platform_client.get_recent_updates()

        assert result == []

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_recent_updates_empty_response(self, mock_async_client, platform_client):
        """Test get recent updates with empty response"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = []

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        result = await platform_client.get_recent_updates()

        assert result == []
        assert isinstance(result, list)


class TestTestConnection:
    """Test test_connection method"""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_connection_success(self, mock_async_client, platform_client):
        """Test successful connection test"""
        mock_response = Mock()
        mock_response.status_code = 200

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        result = await platform_client.test_connection()

        assert result is True

        # Verify request
        mock_client_instance.get.assert_called_once()
        call_args = mock_client_instance.get.call_args
        assert call_args[0][0] == "https://api.platform.test/health"
        assert call_args[1]['timeout'] == 5.0

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_connection_failure_status(self, mock_async_client, platform_client):
        """Test connection test with non-200 status"""
        mock_response = Mock()
        mock_response.status_code = 500

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        result = await platform_client.test_connection()

        assert result is False

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_connection_failure_exception(self, mock_async_client, platform_client):
        """Test connection test with exception"""
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = Exception("Connection failed")
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        result = await platform_client.test_connection()

        assert result is False

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_connection_failure_timeout(self, mock_async_client, platform_client):
        """Test connection test with timeout"""
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        result = await platform_client.test_connection()

        assert result is False

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_connection_different_status_codes(self, mock_async_client, platform_client):
        """Test connection test with various status codes"""
        status_codes = [200, 201, 204, 302, 400, 401, 403, 404, 500, 502, 503]
        expected_results = [True, False, False, False, False, False, False, False, False, False, False]

        for status_code, expected in zip(status_codes, expected_results):
            mock_response = Mock()
            mock_response.status_code = status_code

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance

            result = await platform_client.test_connection()

            assert result is expected, f"Status code {status_code} should return {expected}"


class TestRetryDecorator:
    """Test retry functionality"""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_retry_on_failure(self, mock_async_client, platform_client, sample_update_data):
        """Test that retries work on failures"""
        # Mock client to fail twice then succeed
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = [
            httpx.RequestError("First failure"),
            httpx.RequestError("Second failure"),
            Mock(raise_for_status=Mock(), json=Mock(return_value={'id': 'success'}))
        ]
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Should eventually succeed after retries
        result = await platform_client.publish_update(
            sample_update_data['title'],
            sample_update_data['content'],
            sample_update_data['excerpt']
        )

        # Verify it was called 3 times (initial + 2 retries)
        assert mock_client_instance.post.call_count == 3
        assert result['id'] == 'success'

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_max_retries_exceeded(self, mock_async_client, platform_client, sample_update_data):
        """Test behavior when max retries are exceeded"""
        # Mock client to always fail
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.RequestError("Always fails")
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Should raise exception after max retries
        with pytest.raises(httpx.RequestError):
            await platform_client.publish_update(
                sample_update_data['title'],
                sample_update_data['content'],
                sample_update_data['excerpt']
            )

        # Should have tried initial call + 3 retries = 4 total
        assert mock_client_instance.post.call_count == 4


class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    def test_circuit_breaker_initialization(self, platform_client):
        """Test that circuit breaker is properly initialized"""
        assert platform_client.breaker is not None
        # Circuit breaker attributes would be tested if we had access to the implementation

    def test_retry_policy_initialization(self, platform_client):
        """Test that retry policy is properly initialized"""
        assert platform_client.retry is not None
        # Retry policy attributes would be tested if we had access to the implementation


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_publish_update_json_decode_error(self, mock_async_client, platform_client, sample_update_data):
        """Test handling of JSON decode errors"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Should raise the JSON decode error
        with pytest.raises(ValueError):
            await platform_client.publish_update(
                sample_update_data['title'],
                sample_update_data['content'],
                sample_update_data['excerpt']
            )

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_recent_updates_json_decode_error(self, mock_async_client, platform_client):
        """Test handling of JSON decode errors in get_recent_updates"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Should return empty list on JSON error
        result = await platform_client.get_recent_updates()

        assert result == []

    def test_platform_client_with_none_settings(self):
        """Test PlatformClient behavior with None values in settings"""
        settings = MagicMock()
        settings.PLATFORM_BASE_URL = None
        settings.PLATFORM_API_KEY = None
        settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
        settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
        settings.MAX_RETRIES = 3
        settings.RETRY_MAX_WAIT = 30

        client = PlatformClient(settings)

        assert client.base_url is None
        assert client.api_key is None

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_publish_update_very_large_content(self, mock_async_client, platform_client):
        """Test publish update with very large content"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'id': 'large_content', 'published': True}

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Create large content (1MB)
        large_content = "x" * (1024 * 1024)

        result = await platform_client.publish_update(
            "Large Content Test",
            large_content,
            "Large content excerpt"
        )

        # Should handle large content without issues
        assert result['id'] == 'large_content'

        # Verify the large content was passed correctly
        call_args = mock_client_instance.post.call_args
        request_data = call_args[1]['json']
        assert len(request_data['content']) == 1024 * 1024