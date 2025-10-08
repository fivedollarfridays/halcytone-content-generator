"""
Comprehensive test suite for ContentGeneratorClient
Coverage target: 75%+
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import uuid

from halcytone_content_generator.lib.api.content_generator import (
    ContentGeneratorClient
)
from halcytone_content_generator.lib.base_client import APIResponse, APIError


# ============================================================================
# ContentGeneratorClient Initialization Tests
# ============================================================================

class TestContentGeneratorClientInitialization:
    """Test ContentGeneratorClient initialization"""

    def test_client_basic_initialization(self):
        """Test basic client initialization"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        assert client.base_url == "https://api.example.com"
        assert client.api_key is None
        assert client.timeout == 60.0  # Default for content generation
        assert client.max_retries == 3

    def test_client_with_api_key(self):
        """Test client initialization with API key"""
        client = ContentGeneratorClient(
            base_url="https://api.example.com",
            api_key="test_key_123"
        )

        assert client.api_key == "test_key_123"
        assert "Authorization" in client.default_headers

    def test_client_with_custom_timeout(self):
        """Test client with custom timeout"""
        client = ContentGeneratorClient(
            base_url="https://api.example.com",
            timeout=120.0
        )

        assert client.timeout == 120.0

    def test_client_with_custom_retries(self):
        """Test client with custom retries"""
        client = ContentGeneratorClient(
            base_url="https://api.example.com",
            max_retries=5
        )

        assert client.max_retries == 5


# ============================================================================
# Health & Status Methods Tests
# ============================================================================

class TestHealthAndStatusMethods:
    """Test health and status checking methods"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.health_check()

            assert response.status_code == 200
            assert response.data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_readiness_check(self):
        """Test readiness check endpoint"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ready": True}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.readiness_check()

            assert response.status_code == 200
            assert response.data["ready"] is True

    @pytest.mark.asyncio
    async def test_startup_probe(self):
        """Test startup probe endpoint"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"startup": "complete"}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.startup_probe()

            assert response.status_code == 200
            assert response.data["startup"] == "complete"

    @pytest.mark.asyncio
    async def test_metrics(self):
        """Test metrics endpoint"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"requests_total": 100}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.metrics()

            assert response.status_code == 200
            assert response.data["requests_total"] == 100


# ============================================================================
# Content Generation V1 Tests
# ============================================================================

class TestContentGenerationV1:
    """Test V1 content generation methods"""

    @pytest.mark.asyncio
    async def test_generate_content_basic(self):
        """Test basic content generation"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"job_id": "job_123", "status": "queued"}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.generate_content(send_email=True)

            assert response.status_code == 200
            assert response.data["job_id"] == "job_123"

    @pytest.mark.asyncio
    async def test_generate_content_with_all_options(self):
        """Test content generation with all options"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"job_id": "job_456"}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.generate_content(
                send_email=True,
                publish_web=True,
                publish_social=True,
                document_id="gdocs:123",
                dry_run=True
            )

            assert response.status_code == 200
            # Verify request data includes all parameters
            call_kwargs = mock_client.request.call_args[1]
            assert call_kwargs["json"]["send_email"] is True
            assert call_kwargs["json"]["publish_web"] is True
            assert call_kwargs["json"]["publish_social"] is True
            assert call_kwargs["json"]["document_id"] == "gdocs:123"
            assert call_kwargs["json"]["dry_run"] is True

    @pytest.mark.asyncio
    async def test_preview_content(self):
        """Test content preview"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"preview": "Content preview"}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.preview_content(document_id="gdocs:789")

            assert response.status_code == 200
            assert "preview" in response.data


# ============================================================================
# Content Synchronization V2 Tests
# ============================================================================

class TestContentSynchronizationV2:
    """Test V2 content synchronization methods"""

    @pytest.mark.asyncio
    async def test_sync_content_basic(self):
        """Test basic content sync"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"sync_job_id": "sync_123"}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.sync_content(
                document_id="notion:abc123",
                channels=["email", "web"]
            )

            assert response.status_code == 201
            assert response.data["sync_job_id"] == "sync_123"

    @pytest.mark.asyncio
    async def test_sync_content_with_schedule(self):
        """Test content sync with schedule"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"sync_job_id": "sync_456"}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            schedule_time = datetime(2025, 10, 15, 10, 0)
            response = await client.sync_content(
                document_id="gdocs:xyz",
                channels=["social_twitter"],
                schedule_time=schedule_time,
                metadata={"campaign": "launch"}
            )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_sync_job(self):
        """Test get sync job status"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"job_id": "sync_123", "status": "completed"}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.get_sync_job("sync_123")

            assert response.status_code == 200
            assert response.data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_list_sync_jobs(self):
        """Test list sync jobs"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jobs": [], "total": 0}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.list_sync_jobs(status="pending", limit=10)

            assert response.status_code == 200
            assert "jobs" in response.data

    @pytest.mark.asyncio
    async def test_cancel_sync_job(self):
        """Test cancel sync job"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cancelled": True}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.cancel_sync_job("sync_789")

            assert response.status_code == 200
            assert response.data["cancelled"] is True


# ============================================================================
# Content Validation Tests
# ============================================================================

class TestContentValidation:
    """Test content validation methods"""

    @pytest.mark.asyncio
    async def test_validate_content_basic(self):
        """Test basic content validation"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"is_valid": True, "issues": []}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            content = {"title": "Test", "body": "Content"}
            response = await client.validate_content(content)

            assert response.status_code == 200
            assert response.data["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_content_with_type(self):
        """Test content validation with specific type"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"is_valid": True}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            content = {"title": "Blog Post"}
            response = await client.validate_content(
                content,
                content_type="blog",
                strict=False
            )

            assert response.status_code == 200


# ============================================================================
# Cache Management Tests
# ============================================================================

class TestCacheManagement:
    """Test cache management methods"""

    @pytest.mark.asyncio
    async def test_invalidate_cache_by_keys(self):
        """Test cache invalidation by keys"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalidated": 3}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.invalidate_cache(
                cache_keys=["key1", "key2", "key3"]
            )

            assert response.status_code == 200
            assert response.data["invalidated"] == 3

    @pytest.mark.asyncio
    async def test_invalidate_cache_by_pattern(self):
        """Test cache invalidation by pattern"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalidated": 10}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.invalidate_cache(pattern="content:*")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_cache_stats(self):
        """Test get cache statistics"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"hits": 100, "misses": 10}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.get_cache_stats()

            assert response.status_code == 200
            assert response.data["hits"] == 100

    @pytest.mark.asyncio
    async def test_clear_all_caches(self):
        """Test clear all caches"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cleared": True}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.clear_all_caches()

            assert response.status_code == 200
            assert response.data["cleared"] is True


# ============================================================================
# Batch Operations Tests
# ============================================================================

class TestBatchOperations:
    """Test batch operation methods"""

    @pytest.mark.asyncio
    async def test_batch_generate(self):
        """Test batch content generation"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"batch_id": "batch_123", "results": []}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            requests = [
                {"document_id": "doc1", "channels": ["email"]},
                {"document_id": "doc2", "channels": ["web"]}
            ]
            response = await client.batch_generate(
                requests=requests,
                parallel=True,
                fail_fast=False
            )

            assert response.status_code == 200
            assert "batch_id" in response.data


# ============================================================================
# Analytics & Reporting Tests
# ============================================================================

class TestAnalyticsAndReporting:
    """Test analytics and reporting methods"""

    @pytest.mark.asyncio
    async def test_get_content_analytics(self):
        """Test get content analytics"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"views": 1000, "clicks": 50}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.get_content_analytics(
                content_id="content_123",
                channels=["email", "web"]
            )

            assert response.status_code == 200
            assert response.data["views"] == 1000

    @pytest.mark.asyncio
    async def test_get_content_analytics_with_dates(self):
        """Test get content analytics with date range"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"analytics": {}}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            start = datetime(2025, 10, 1)
            end = datetime(2025, 10, 7)
            response = await client.get_content_analytics(
                start_date=start,
                end_date=end
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_email_analytics(self):
        """Test get email analytics"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"opens": 500, "clicks": 100}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.get_email_analytics(campaign_id="campaign_789")

            assert response.status_code == 200
            assert response.data["opens"] == 500


# ============================================================================
# Configuration Tests
# ============================================================================

class TestConfiguration:
    """Test configuration methods"""

    @pytest.mark.asyncio
    async def test_get_config(self):
        """Test get configuration"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"debug": False, "timeout": 60}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            response = await client.get_config()

            assert response.status_code == 200
            assert "debug" in response.data

    @pytest.mark.asyncio
    async def test_update_config(self):
        """Test update configuration"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

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

            config_updates = {"debug": True, "log_level": "DEBUG"}
            response = await client.update_config(config_updates)

            assert response.status_code == 200
            assert response.data["updated"] is True


# ============================================================================
# Helper Methods Tests
# ============================================================================

class TestHelperMethods:
    """Test helper utility methods"""

    def test_generate_correlation_id(self):
        """Test correlation ID generation"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        corr_id = client.generate_correlation_id()

        assert isinstance(corr_id, str)
        assert len(corr_id) == 36  # UUID format
        # Verify it's a valid UUID
        uuid.UUID(corr_id)

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test connection test when successful"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await client.test_connection()

            assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test connection test when failed"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Server error"}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await client.test_connection()

            assert result is False


# ============================================================================
# Integration Tests
# ============================================================================

class TestContentGeneratorClientIntegration:
    """Test integrated workflows"""

    @pytest.mark.asyncio
    async def test_full_content_workflow(self):
        """Test complete content generation workflow"""
        client = ContentGeneratorClient(
            base_url="https://api.example.com",
            api_key="test_key"
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # Step 1: Test connection
            connected = await client.test_connection()
            assert connected is True

            # Step 2: Generate content
            gen_response = await client.generate_content(send_email=True)
            assert gen_response.is_success()

            # Step 3: Check metrics
            metrics_response = await client.metrics()
            assert metrics_response.is_success()

    @pytest.mark.asyncio
    async def test_correlation_id_propagation(self):
        """Test correlation ID is properly propagated"""
        client = ContentGeneratorClient(base_url="https://api.example.com")

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

            corr_id = "test-correlation-123"
            await client.health_check(correlation_id=corr_id)

            # Verify correlation ID was passed in headers
            call_kwargs = mock_client.request.call_args[1]
            assert call_kwargs["headers"]["X-Correlation-ID"] == corr_id
