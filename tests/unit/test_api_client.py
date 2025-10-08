"""
Unit tests for API Client library
Tests base API client and Content Generator client
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from halcytone_content_generator.lib import APIClient, APIError, APIResponse
from halcytone_content_generator.lib.api.content_generator import ContentGeneratorClient


class TestAPIResponse:
    """Test APIResponse dataclass"""

    def test_api_response_creation(self):
        """Test creating APIResponse"""
        response = APIResponse(
            status_code=200,
            data={"message": "success"},
            headers={"Content-Type": "application/json"},
            success=True
        )

        assert response.status_code == 200
        assert response.data == {"message": "success"}
        assert response.success is True
        assert response.is_success() is True

    def test_api_response_json(self):
        """Test json() method returns data"""
        response = APIResponse(
            status_code=200,
            data={"test": "data"},
            headers={},
            success=True
        )

        assert response.json() == {"test": "data"}

    def test_api_response_is_success_false(self):
        """Test is_success() returns False for error codes"""
        response = APIResponse(
            status_code=404,
            data={"error": "not found"},
            headers={},
            success=False
        )

        assert response.is_success() is False


class TestAPIError:
    """Test APIError exception"""

    def test_api_error_creation(self):
        """Test creating APIError"""
        error = APIError(
            message="Test error",
            status_code=400,
            response={"detail": "Bad request"}
        )

        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.response == {"detail": "Bad request"}
        assert str(error) == "Test error"


class TestAPIClient:
    """Test base APIClient"""

    @pytest.fixture
    def client(self):
        """Create test API client"""
        return APIClient(
            base_url="https://api.test.com",
            api_key="test-key",
            timeout=10.0,
            max_retries=2
        )

    def test_client_initialization(self, client):
        """Test client initialization"""
        assert client.base_url == "https://api.test.com"
        assert client.api_key == "test-key"
        assert client.timeout == 10.0
        assert client.max_retries == 2
        assert "Authorization" in client.default_headers

    def test_build_url(self, client):
        """Test URL building"""
        url = client._build_url("/api/v1/endpoint")
        assert url == "https://api.test.com/api/v1/endpoint"

        url = client._build_url("api/v1/endpoint")
        assert url == "https://api.test.com/api/v1/endpoint"

    def test_prepare_headers(self, client):
        """Test header preparation"""
        headers = client._prepare_headers()

        assert "Content-Type" in headers
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-key"

    def test_prepare_headers_with_additional(self, client):
        """Test adding additional headers"""
        headers = client._prepare_headers({"X-Custom": "value"})

        assert headers["X-Custom"] == "value"
        assert "Authorization" in headers

    @pytest.mark.asyncio
    async def test_successful_get_request(self, client):
        """Test successful GET request"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": "test"}
            mock_response.headers = {"Content-Type": "application/json"}

            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            response = await client.get("/test")

            assert response.status_code == 200
            assert response.data == {"data": "test"}
            assert response.is_success()

    @pytest.mark.asyncio
    async def test_failed_request_raises_error(self, client):
        """Test failed request raises APIError"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"detail": "Not found"}
            mock_response.headers = {}

            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(APIError) as exc_info:
                await client.get("/missing")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_post_request(self, client):
        """Test POST request"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "123"}
            mock_response.headers = {}

            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            response = await client.post("/create", data={"name": "test"})

            assert response.status_code == 201
            assert response.data["id"] == "123"


class TestContentGeneratorClient:
    """Test ContentGeneratorClient"""

    @pytest.fixture
    def client(self):
        """Create test Content Generator client"""
        return ContentGeneratorClient(
            base_url="https://api.test.com",
            api_key="test-key"
        )

    def test_client_initialization(self, client):
        """Test Content Generator client initialization"""
        assert client.base_url == "https://api.test.com"
        assert client.timeout == 60.0  # Default longer timeout

    def test_generate_correlation_id(self, client):
        """Test correlation ID generation"""
        corr_id = client.generate_correlation_id()

        assert isinstance(corr_id, str)
        assert len(corr_id) > 0

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_response.headers = {}

            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            response = await client.health_check()

            assert response.status_code == 200
            assert response.data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_generate_content(self, client):
        """Test content generation"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"job_id": "123", "status": "completed"}
            mock_response.headers = {}

            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            response = await client.generate_content(
                send_email=True,
                publish_web=True,
                document_id="gdocs:test"
            )

            assert response.status_code == 200
            assert response.data["job_id"] == "123"

    @pytest.mark.asyncio
    async def test_sync_content(self, client):
        """Test content sync"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "job_id": "sync-123",
                "status": "pending",
                "channels": ["email", "website"]
            }
            mock_response.headers = {}

            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            response = await client.sync_content(
                document_id="gdocs:doc123",
                channels=["email", "website"]
            )

            assert response.status_code == 201
            assert response.data["job_id"] == "sync-123"
            assert len(response.data["channels"]) == 2

    @pytest.mark.asyncio
    async def test_sync_content_scheduled(self, client):
        """Test scheduled content sync"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"job_id": "scheduled-123"}
            mock_response.headers = {}

            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            future_time = datetime.now() + timedelta(hours=24)
            response = await client.sync_content(
                document_id="gdocs:doc123",
                channels=["email"],
                schedule_time=future_time
            )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_validate_content(self, client):
        """Test content validation"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "is_valid": True,
                "issues": [],
                "warnings": []
            }
            mock_response.headers = {}

            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            content_data = {
                "type": "update",
                "title": "Test Update",
                "content": "Test content"
            }

            response = await client.validate_content(
                content=content_data,
                strict=True
            )

            assert response.status_code == 200
            assert response.data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_invalidate_cache(self, client):
        """Test cache invalidation"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"invalidated": 5}
            mock_response.headers = {}

            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            response = await client.invalidate_cache(
                cache_keys=["key1", "key2"]
            )

            assert response.status_code == 200
            assert response.data["invalidated"] == 5

    @pytest.mark.asyncio
    async def test_batch_generate(self, client):
        """Test batch generation"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": {
                    "successful": 2,
                    "failed": 1,
                    "total": 3
                }
            }
            mock_response.headers = {}

            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            requests = [
                {"document_id": "gdocs:1", "channels": ["email"]},
                {"document_id": "gdocs:2", "channels": ["website"]},
                {"document_id": "gdocs:3", "channels": ["email", "website"]}
            ]

            response = await client.batch_generate(
                requests=requests,
                parallel=True
            )

            assert response.status_code == 200
            assert response.data["results"]["total"] == 3

    @pytest.mark.asyncio
    async def test_connection_test_success(self, client):
        """Test successful connection test"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_response.headers = {}

            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            result = await client.test_connection()

            assert result is True

    @pytest.mark.asyncio
    async def test_connection_test_failure(self, client):
        """Test failed connection test"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.json.return_value = {"error": "Internal error"}
            mock_response.headers = {}

            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )

            result = await client.test_connection()

            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
