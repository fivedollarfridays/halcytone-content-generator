"""
Comprehensive test suite for base_client infrastructure module
Coverage target: 75%+
"""

import pytest
import httpx
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from halcytone_content_generator.lib.base_client import (
    APIResponse,
    APIError,
    APIClient
)


# ============================================================================
# APIResponse Tests
# ============================================================================

class TestAPIResponse:
    """Test APIResponse dataclass"""

    def test_api_response_initialization(self):
        """Test APIResponse initialization"""
        headers = {"Content-Type": "application/json"}
        response = APIResponse(
            status_code=200,
            data={"result": "success"},
            headers=headers,
            success=True
        )

        assert response.status_code == 200
        assert response.data == {"result": "success"}
        assert response.headers == headers
        assert response.success is True
        assert response.error is None
        assert response.timestamp is not None

    def test_api_response_with_error(self):
        """Test APIResponse with error"""
        response = APIResponse(
            status_code=400,
            data={"detail": "Bad request"},
            headers={},
            success=False,
            error="Validation error"
        )

        assert response.status_code == 400
        assert response.success is False
        assert response.error == "Validation error"

    def test_api_response_timestamp_auto_set(self):
        """Test timestamp is automatically set"""
        response = APIResponse(
            status_code=200,
            data={},
            headers={},
            success=True
        )

        assert response.timestamp is not None
        assert isinstance(response.timestamp, datetime)

    def test_api_response_json_method(self):
        """Test json() method returns data"""
        data = {"key": "value", "count": 42}
        response = APIResponse(
            status_code=200,
            data=data,
            headers={},
            success=True
        )

        assert response.json() == data

    def test_api_response_is_success_200(self):
        """Test is_success() for 200 status"""
        response = APIResponse(
            status_code=200,
            data={},
            headers={},
            success=True
        )

        assert response.is_success() is True

    def test_api_response_is_success_204(self):
        """Test is_success() for 204 status"""
        response = APIResponse(
            status_code=204,
            data={},
            headers={},
            success=True
        )

        assert response.is_success() is True

    def test_api_response_is_success_false_400(self):
        """Test is_success() returns False for 400"""
        response = APIResponse(
            status_code=400,
            data={},
            headers={},
            success=False
        )

        assert response.is_success() is False

    def test_api_response_is_success_false_500(self):
        """Test is_success() returns False for 500"""
        response = APIResponse(
            status_code=500,
            data={},
            headers={},
            success=False
        )

        assert response.is_success() is False


# ============================================================================
# APIError Tests
# ============================================================================

class TestAPIError:
    """Test APIError exception"""

    def test_api_error_initialization(self):
        """Test APIError initialization"""
        error = APIError("Test error")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code is None
        assert error.response is None

    def test_api_error_with_status_code(self):
        """Test APIError with status code"""
        error = APIError("Not found", status_code=404)

        assert error.message == "Not found"
        assert error.status_code == 404

    def test_api_error_with_response(self):
        """Test APIError with response data"""
        response_data = {"detail": "Validation failed", "errors": ["field required"]}
        error = APIError("Validation error", status_code=422, response=response_data)

        assert error.message == "Validation error"
        assert error.status_code == 422
        assert error.response == response_data

    def test_api_error_can_be_raised(self):
        """Test APIError can be raised"""
        with pytest.raises(APIError) as exc_info:
            raise APIError("Test error", status_code=500)

        assert exc_info.value.message == "Test error"
        assert exc_info.value.status_code == 500


# ============================================================================
# APIClient Initialization Tests
# ============================================================================

class TestAPIClientInitialization:
    """Test APIClient initialization"""

    def test_client_basic_initialization(self):
        """Test basic client initialization"""
        client = APIClient(base_url="https://api.example.com")

        assert client.base_url == "https://api.example.com"
        assert client.api_key is None
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client.default_headers == {}

    def test_client_initialization_with_api_key(self):
        """Test client initialization with API key"""
        client = APIClient(
            base_url="https://api.example.com",
            api_key="test_api_key_123"
        )

        assert client.api_key == "test_api_key_123"
        assert "Authorization" in client.default_headers
        assert client.default_headers["Authorization"] == "Bearer test_api_key_123"

    def test_client_initialization_with_custom_timeout(self):
        """Test client with custom timeout"""
        client = APIClient(
            base_url="https://api.example.com",
            timeout=60.0
        )

        assert client.timeout == 60.0

    def test_client_initialization_with_custom_retries(self):
        """Test client with custom max retries"""
        client = APIClient(
            base_url="https://api.example.com",
            max_retries=5
        )

        assert client.max_retries == 5

    def test_client_initialization_with_custom_headers(self):
        """Test client with custom headers"""
        headers = {"X-Custom-Header": "value"}
        client = APIClient(
            base_url="https://api.example.com",
            headers=headers
        )

        assert "X-Custom-Header" in client.default_headers
        assert client.default_headers["X-Custom-Header"] == "value"

    def test_client_strips_trailing_slash(self):
        """Test base URL trailing slash is stripped"""
        client = APIClient(base_url="https://api.example.com/")

        assert client.base_url == "https://api.example.com"


# ============================================================================
# APIClient Helper Methods Tests
# ============================================================================

class TestAPIClientHelperMethods:
    """Test APIClient helper methods"""

    def test_build_url(self):
        """Test _build_url method"""
        client = APIClient(base_url="https://api.example.com")

        url = client._build_url("users")
        assert url == "https://api.example.com/users"

    def test_build_url_strips_leading_slash(self):
        """Test _build_url strips leading slash from endpoint"""
        client = APIClient(base_url="https://api.example.com")

        url = client._build_url("/users")
        assert url == "https://api.example.com/users"

    def test_build_url_with_path(self):
        """Test _build_url with path"""
        client = APIClient(base_url="https://api.example.com")

        url = client._build_url("users/123/profile")
        assert url == "https://api.example.com/users/123/profile"

    def test_prepare_headers_default(self):
        """Test _prepare_headers with defaults"""
        client = APIClient(base_url="https://api.example.com")

        headers = client._prepare_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"

    def test_prepare_headers_with_api_key(self):
        """Test _prepare_headers includes API key"""
        client = APIClient(
            base_url="https://api.example.com",
            api_key="test_key"
        )

        headers = client._prepare_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_key"

    def test_prepare_headers_merge_custom(self):
        """Test _prepare_headers merges custom headers"""
        client = APIClient(base_url="https://api.example.com")

        custom_headers = {"X-Custom": "value"}
        headers = client._prepare_headers(custom_headers)

        assert headers["X-Custom"] == "value"
        assert headers["Content-Type"] == "application/json"


# ============================================================================
# APIClient HTTP Methods Tests
# ============================================================================

class TestAPIClientHTTPMethods:
    """Test APIClient HTTP methods"""

    @pytest.mark.asyncio
    async def test_get_request_success(self):
        """Test successful GET request"""
        client = APIClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {"Content-Type": "application/json"}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.get("users")

            assert response.status_code == 200
            assert response.data == {"data": "test"}
            assert response.is_success() is True

    @pytest.mark.asyncio
    async def test_post_request_with_data(self):
        """Test POST request with data"""
        client = APIClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 123}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            data = {"name": "Test User"}
            response = await client.post("users", data=data)

            assert response.status_code == 201
            assert response.data == {"id": 123}

    @pytest.mark.asyncio
    async def test_put_request(self):
        """Test PUT request"""
        client = APIClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"updated": True}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.put("users/123", data={"name": "Updated"})

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_request(self):
        """Test DELETE request"""
        import json as json_module
        client = APIClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.text = ""
        mock_response.json.side_effect = json_module.JSONDecodeError("No JSON", "", 0)
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.delete("users/123")

            assert response.status_code == 204
            assert response.data == ""  # Falls back to response.text

    @pytest.mark.asyncio
    async def test_patch_request(self):
        """Test PATCH request"""
        client = APIClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"patched": True}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.patch("users/123", data={"status": "active"})

            assert response.status_code == 200


# ============================================================================
# APIClient Error Handling Tests
# ============================================================================

class TestAPIClientErrorHandling:
    """Test APIClient error handling"""

    @pytest.mark.asyncio
    async def test_request_404_error(self):
        """Test 404 error handling"""
        client = APIClient(base_url="https://api.example.com", max_retries=1)

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(APIError) as exc_info:
                await client.get("users/999")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_request_500_error_with_retry(self):
        """Test 500 error triggers retry"""
        client = APIClient(base_url="https://api.example.com", max_retries=2)

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal error"}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(APIError) as exc_info:
                await client.get("users")

            assert exc_info.value.status_code == 500
            # Should have retried
            assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test timeout error handling"""
        client = APIClient(base_url="https://api.example.com", max_retries=1)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client_class.return_value = mock_client

            with pytest.raises(APIError) as exc_info:
                await client.get("users")

            assert exc_info.value.status_code == 408
            assert "timeout" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test connection error handling"""
        client = APIClient(base_url="https://api.example.com", max_retries=1)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
            mock_client_class.return_value = mock_client

            with pytest.raises(APIError) as exc_info:
                await client.get("users")

            assert "Request error" in exc_info.value.message


# ============================================================================
# APIClient Correlation ID Tests
# ============================================================================

class TestAPIClientCorrelationID:
    """Test correlation ID tracking"""

    @pytest.mark.asyncio
    async def test_correlation_id_in_headers(self):
        """Test correlation ID is added to headers"""
        client = APIClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await client.get("users", correlation_id="test-corr-123")

            # Check that correlation ID was passed in headers
            call_kwargs = mock_client.request.call_args[1]
            assert "X-Correlation-ID" in call_kwargs["headers"]
            assert call_kwargs["headers"]["X-Correlation-ID"] == "test-corr-123"
