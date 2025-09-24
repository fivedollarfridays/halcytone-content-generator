"""
Integration Tests for Cache Invalidation System
Sprint 4: Ecosystem Integration - End-to-end cache invalidation testing

Tests the complete cache invalidation workflow including API endpoints,
webhook processing, and multi-target cache management.
"""
import pytest
import json
import hmac
import hashlib
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.halcytone_content_generator.services.cache_manager import (
    CacheManager,
    initialize_cache_manager,
    CacheTarget,
    InvalidationStatus
)
from src.halcytone_content_generator.api.cache_endpoints import router as cache_router


class TestCacheInvalidationAPI:
    """Integration tests for cache invalidation API endpoints"""

    @pytest.fixture
    def cache_config(self):
        """Configuration for test cache manager"""
        return {
            "api_keys": ["test_api_key_123", "admin_key_456"],
            "webhook_secret": "test_webhook_secret_789",
            "max_history": 50,
            "local": {"enabled": True},
            "api": {"enabled": True},
            "cdn": {
                "type": "cloudflare",
                "api_key": "cf_test_key",
                "zone_id": "cf_test_zone"
            }
        }

    @pytest.fixture
    def app(self, cache_config):
        """FastAPI test application with cache endpoints"""
        app = FastAPI()
        app.include_router(cache_router)

        # Initialize cache manager
        initialize_cache_manager(cache_config)

        return app

    @pytest.fixture
    def client(self, app):
        """Test client for API requests"""
        return TestClient(app)

    def test_cache_invalidation_endpoint_success(self, client):
        """Test successful cache invalidation via API"""
        # Mock successful invalidation
        with patch('src.halcytone_content_generator.services.cache_manager.get_cache_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.verify_api_key.return_value = True
            mock_manager.invalidate_cache = AsyncMock()

            # Mock successful result
            from src.halcytone_content_generator.services.cache_manager import InvalidationResult, InvalidationStatus
            mock_result = InvalidationResult(
                request_id="test_123",
                status=InvalidationStatus.SUCCESS,
                targets_processed={CacheTarget.LOCAL: True, CacheTarget.CDN: True},
                keys_invalidated=5,
                errors=[],
                duration_ms=150.5
            )
            mock_manager.invalidate_cache.return_value = mock_result
            mock_get_manager.return_value = mock_manager

            response = client.post(
                "/cache/invalidate",
                headers={"X-API-Key": "test_api_key_123"},
                json={
                    "targets": ["local", "cdn"],
                    "keys": ["test_key_1", "test_key_2"],
                    "patterns": ["api/v1/*"],
                    "reason": "Integration test"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["request_id"] == "test_123"
            assert data["status"] == "success"
            assert data["keys_invalidated"] == 5
            assert "local" in data["targets_processed"]
            assert "cdn" in data["targets_processed"]

    def test_cache_invalidation_unauthorized(self, client):
        """Test cache invalidation with invalid API key"""
        response = client.post(
            "/cache/invalidate",
            headers={"X-API-Key": "invalid_key"},
            json={"targets": ["local"]}
        )

        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_cache_invalidation_missing_api_key(self, client):
        """Test cache invalidation without API key header"""
        response = client.post(
            "/cache/invalidate",
            json={"targets": ["local"]}
        )

        assert response.status_code == 422  # FastAPI validation error for missing header

    def test_cache_invalidation_invalid_targets(self, client):
        """Test cache invalidation with invalid targets"""
        with patch('src.halcytone_content_generator.services.cache_manager.get_cache_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.verify_api_key.return_value = True
            mock_get_manager.return_value = mock_manager

            response = client.post(
                "/cache/invalidate",
                headers={"X-API-Key": "test_api_key_123"},
                json={"targets": ["invalid_target"]}
            )

            assert response.status_code == 422  # Pydantic validation error

    def test_webhook_invalidation_endpoint_success(self, client):
        """Test successful webhook cache invalidation"""
        with patch('src.halcytone_content_generator.services.cache_manager.get_cache_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.verify_webhook_signature.return_value = True
            mock_manager.process_webhook_invalidation = AsyncMock()

            from src.halcytone_content_generator.services.cache_manager import InvalidationResult, InvalidationStatus
            mock_result = InvalidationResult(
                request_id="webhook_123",
                status=InvalidationStatus.SUCCESS,
                targets_processed={CacheTarget.LOCAL: True},
                keys_invalidated=3,
                errors=[],
                duration_ms=85.2
            )
            mock_manager.process_webhook_invalidation.return_value = mock_result
            mock_get_manager.return_value = mock_manager

            payload = {
                "event": "content_updated",
                "targets": ["local"],
                "keys": ["updated_content"],
                "reason": "CMS update"
            }

            # Generate signature
            webhook_secret = "test_webhook_secret_789"
            body = json.dumps(payload).encode()
            signature = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()

            response = client.post(
                "/cache/webhook",
                headers={"X-Signature": f"sha256={signature}"},
                json=payload
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["request_id"] == "webhook_123"
            assert data["webhook_event"] == "content_updated"
            assert data["keys_invalidated"] == 3

    def test_webhook_invalidation_invalid_signature(self, client):
        """Test webhook invalidation with invalid signature"""
        with patch('src.halcytone_content_generator.services.cache_manager.get_cache_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.verify_webhook_signature.return_value = False
            mock_get_manager.return_value = mock_manager

            response = client.post(
                "/cache/webhook",
                headers={"X-Signature": "invalid_signature"},
                json={
                    "event": "test",
                    "targets": ["local"]
                }
            )

            assert response.status_code == 401
            assert "Invalid webhook signature" in response.json()["detail"]

    def test_cache_health_check_endpoint(self, client):
        """Test cache health check endpoint"""
        with patch('src.halcytone_content_generator.services.cache_manager.get_cache_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.verify_api_key.return_value = True
            mock_manager.health_check = AsyncMock()
            mock_manager.health_check.return_value = {
                CacheTarget.LOCAL: True,
                CacheTarget.CDN: False,
                CacheTarget.API: True
            }
            mock_get_manager.return_value = mock_manager

            response = client.get(
                "/cache/health",
                headers={"X-API-Key": "test_api_key_123"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["overall_health"] == "degraded"  # CDN is unhealthy
            assert data["targets"]["local"]["healthy"] is True
            assert data["targets"]["cdn"]["healthy"] is False
            assert data["targets"]["api"]["healthy"] is True
            assert data["total_targets"] == 3

    def test_cache_statistics_endpoint(self, client):
        """Test cache statistics endpoint"""
        with patch('src.halcytone_content_generator.services.cache_manager.get_cache_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.verify_api_key.return_value = True
            mock_manager.get_cache_stats = AsyncMock()
            mock_manager.get_cache_stats.return_value = {
                "targets_configured": ["local", "cdn", "api"],
                "health_status": {"local": True, "cdn": True, "api": True},
                "recent_requests": 10,
                "total_requests": 50,
                "webhook_configured": True,
                "api_keys_configured": 2
            }
            mock_get_manager.return_value = mock_manager

            response = client.get(
                "/cache/stats",
                headers={"X-API-Key": "test_api_key_123"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["targets_configured"] == ["local", "cdn", "api"]
            assert data["recent_requests"] == 10
            assert data["total_requests"] == 50
            assert data["webhook_configured"] is True

    def test_invalidation_history_endpoint(self, client):
        """Test invalidation history endpoint"""
        with patch('src.halcytone_content_generator.services.cache_manager.get_cache_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.verify_api_key.return_value = True
            mock_manager.get_invalidation_history.return_value = [
                {
                    "request_id": "req_1",
                    "status": "success",
                    "targets_processed": {"local": True},
                    "keys_invalidated": 5,
                    "duration_ms": 120.5,
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                {
                    "request_id": "req_2",
                    "status": "partial",
                    "targets_processed": {"local": True, "cdn": False},
                    "keys_invalidated": 2,
                    "duration_ms": 250.8,
                    "timestamp": "2024-01-15T10:25:00Z"
                }
            ]
            mock_manager.request_history = ["mock"] * 25  # Mock total count
            mock_get_manager.return_value = mock_manager

            response = client.get(
                "/cache/history?limit=10",
                headers={"X-API-Key": "test_api_key_123"}
            )

            assert response.status_code == 200
            data = response.json()

            assert len(data["history"]) == 2
            assert data["total_count"] == 25
            assert data["limit"] == 10
            assert data["history"][0]["request_id"] == "req_1"

    def test_clear_all_caches_endpoint_success(self, client):
        """Test clear all caches endpoint"""
        with patch('src.halcytone_content_generator.services.cache_manager.get_cache_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.verify_api_key.return_value = True
            mock_manager.invalidators = {CacheTarget.LOCAL: MagicMock(), CacheTarget.CDN: MagicMock()}
            mock_manager.invalidate_cache = AsyncMock()

            from src.halcytone_content_generator.services.cache_manager import InvalidationResult, InvalidationStatus
            mock_result = InvalidationResult(
                request_id="clear_all_123",
                status=InvalidationStatus.SUCCESS,
                targets_processed={CacheTarget.LOCAL: True, CacheTarget.CDN: True},
                keys_invalidated=100,
                errors=[],
                duration_ms=300.0
            )
            mock_manager.invalidate_cache.return_value = mock_result
            mock_get_manager.return_value = mock_manager

            response = client.delete(
                "/cache/clear-all?confirm=true",
                headers={"X-API-Key": "test_api_key_123"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["request_id"] == "clear_all_123"
            assert "All cache data has been cleared" in data["warning"]

    def test_clear_all_caches_without_confirmation(self, client):
        """Test clear all caches endpoint without confirmation"""
        with patch('src.halcytone_content_generator.services.cache_manager.get_cache_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.verify_api_key.return_value = True
            mock_get_manager.return_value = mock_manager

            response = client.delete(
                "/cache/clear-all?confirm=false",
                headers={"X-API-Key": "test_api_key_123"}
            )

            assert response.status_code == 400
            assert "Must set confirm=true" in response.json()["detail"]

    def test_webhook_signature_test_endpoint(self, client):
        """Test webhook signature testing endpoint"""
        with patch('src.halcytone_content_generator.services.cache_manager.get_cache_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.verify_webhook_signature.return_value = True
            mock_manager.webhook_secret = "test_secret"
            mock_get_manager.return_value = mock_manager

            test_payload = {"test": "data"}
            body = json.dumps(test_payload).encode()

            response = client.post(
                "/cache/webhook/test",
                headers={"X-Signature": "test_signature"},
                json=test_payload
            )

            assert response.status_code == 200
            data = response.json()

            assert data["signature_valid"] is True
            assert data["signature_provided"] == "test_signature"
            assert data["webhook_secret_configured"] is True


class TestCacheInvalidationWorkflow:
    """Integration tests for complete cache invalidation workflows"""

    @pytest.fixture
    def cache_manager(self):
        """Cache manager with real invalidators for testing"""
        config = {
            "api_keys": ["workflow_test_key"],
            "webhook_secret": "workflow_webhook_secret",
            "local": {},
            "api": {}
        }
        return CacheManager(config)

    @pytest.mark.asyncio
    async def test_end_to_end_invalidation_workflow(self, cache_manager):
        """Test complete invalidation workflow from request to completion"""
        # Step 1: Set up test data in local cache
        local_invalidator = cache_manager.invalidators[CacheTarget.LOCAL]
        local_invalidator.set("test_user:123", {"name": "John"})
        local_invalidator.set("test_product:456", {"title": "Widget"})
        local_invalidator.set("test_category:789", {"name": "Electronics"})

        assert local_invalidator.size() == 3

        # Step 2: Create invalidation request
        from src.halcytone_content_generator.services.cache_manager import InvalidationRequest
        request = InvalidationRequest(
            targets=[CacheTarget.LOCAL, CacheTarget.API],
            patterns=["test_user:*", "test_product:*"],
            reason="End-to-end test",
            initiated_by="integration_test"
        )

        # Step 3: Execute invalidation
        result = await cache_manager.invalidate_cache(request)

        # Step 4: Verify results
        assert result.status == InvalidationStatus.SUCCESS
        assert result.targets_processed[CacheTarget.LOCAL] is True
        assert result.targets_processed[CacheTarget.API] is True
        assert result.duration_ms > 0

        # Step 5: Verify cache state
        assert local_invalidator.get("test_user:123") is None
        assert local_invalidator.get("test_product:456") is None
        assert local_invalidator.get("test_category:789") == {"name": "Electronics"}  # Should remain

        # Step 6: Verify history
        assert len(cache_manager.request_history) == 1
        history_item = cache_manager.request_history[0]
        assert history_item.status == InvalidationStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_webhook_triggered_invalidation_workflow(self, cache_manager):
        """Test webhook-triggered invalidation workflow"""
        # Step 1: Set up cache data
        local_invalidator = cache_manager.invalidators[CacheTarget.LOCAL]
        local_invalidator.set("content:article:123", {"title": "Old Article"})
        local_invalidator.set("content:page:456", {"title": "Old Page"})

        # Step 2: Process webhook payload
        webhook_payload = {
            "event": "content_updated",
            "targets": ["local"],
            "patterns": ["content:*"],
            "reason": "CMS content update"
        }

        result = await cache_manager.process_webhook_invalidation(webhook_payload)

        # Step 3: Verify invalidation result
        assert result.status == InvalidationStatus.SUCCESS
        assert result.reason == "Webhook: content_updated"

        # Step 4: Verify cache state
        assert local_invalidator.get("content:article:123") is None
        assert local_invalidator.get("content:page:456") is None

    @pytest.mark.asyncio
    async def test_multi_target_invalidation_with_failure(self, cache_manager):
        """Test multi-target invalidation with one target failing"""
        # Mock CDN invalidator failure
        cdn_invalidator = MagicMock()
        cdn_invalidator.invalidate = AsyncMock(return_value=False)
        cache_manager.invalidators[CacheTarget.CDN] = cdn_invalidator

        from src.halcytone_content_generator.services.cache_manager import InvalidationRequest
        request = InvalidationRequest(
            targets=[CacheTarget.LOCAL, CacheTarget.CDN, CacheTarget.API],
            force=True,
            reason="Multi-target test with failure"
        )

        result = await cache_manager.invalidate_cache(request)

        # Should be partial success (local and API succeed, CDN fails)
        assert result.status == InvalidationStatus.PARTIAL
        assert result.targets_processed[CacheTarget.LOCAL] is True
        assert result.targets_processed[CacheTarget.CDN] is False
        assert result.targets_processed[CacheTarget.API] is True

    @pytest.mark.asyncio
    async def test_concurrent_invalidation_requests(self, cache_manager):
        """Test handling of concurrent invalidation requests"""
        from src.halcytone_content_generator.services.cache_manager import InvalidationRequest

        # Create multiple concurrent requests
        requests = []
        for i in range(5):
            request = InvalidationRequest(
                targets=[CacheTarget.LOCAL],
                keys=[f"concurrent_test:{i}"],
                reason=f"Concurrent test {i}"
            )
            requests.append(request)

        # Execute all requests concurrently
        results = await asyncio.gather(*[
            cache_manager.invalidate_cache(request) for request in requests
        ])

        # Verify all completed successfully
        for result in results:
            assert result.status == InvalidationStatus.SUCCESS

        # Verify history contains all requests
        assert len(cache_manager.request_history) == 5

    @pytest.mark.asyncio
    async def test_invalidation_with_webhook_notification(self, cache_manager):
        """Test invalidation with webhook notification callback"""
        webhook_url = "https://example.com/cache-webhook-callback"

        # Mock webhook notification
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            from src.halcytone_content_generator.services.cache_manager import InvalidationRequest
            request = InvalidationRequest(
                targets=[CacheTarget.LOCAL],
                keys=["webhook_test"],
                webhook_url=webhook_url,
                reason="Webhook notification test"
            )

            result = await cache_manager.invalidate_cache(request)

            # Verify invalidation succeeded
            assert result.status == InvalidationStatus.SUCCESS

            # Verify webhook was called
            mock_client.return_value.__aenter__.return_value.post.assert_called_once()
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args

            # Verify webhook URL
            assert call_args[0][0] == webhook_url

            # Verify webhook payload
            webhook_payload = call_args[1]["json"]
            assert webhook_payload["event"] == "cache_invalidation_completed"
            assert webhook_payload["result"]["request_id"] == result.request_id


class TestCacheInvalidationErrorHandling:
    """Integration tests for error handling and edge cases"""

    @pytest.fixture
    def cache_manager_with_failing_invalidator(self):
        """Cache manager with a failing invalidator for error testing"""
        config = {"api_keys": ["error_test_key"]}
        manager = CacheManager(config)

        # Add a failing invalidator
        failing_invalidator = MagicMock()
        failing_invalidator.invalidate = AsyncMock(side_effect=Exception("Invalidator failure"))
        failing_invalidator.health_check = AsyncMock(side_effect=Exception("Health check failure"))
        manager.invalidators[CacheTarget.REDIS] = failing_invalidator

        return manager

    @pytest.mark.asyncio
    async def test_invalidator_exception_handling(self, cache_manager_with_failing_invalidator):
        """Test handling of exceptions thrown by invalidators"""
        from src.halcytone_content_generator.services.cache_manager import InvalidationRequest

        request = InvalidationRequest(
            targets=[CacheTarget.REDIS],  # This will throw an exception
            keys=["error_test"],
            reason="Error handling test"
        )

        result = await cache_manager_with_failing_invalidator.invalidate_cache(request)

        # Should handle exception gracefully
        assert result.status == InvalidationStatus.FAILED
        assert len(result.errors) > 0
        assert "Invalidator failure" in result.errors[0]

    @pytest.mark.asyncio
    async def test_health_check_exception_handling(self, cache_manager_with_failing_invalidator):
        """Test handling of exceptions during health checks"""
        health_status = await cache_manager_with_failing_invalidator.health_check()

        # Failing invalidator should be marked as unhealthy
        assert health_status[CacheTarget.REDIS] is False
        # Other invalidators should still work
        assert health_status[CacheTarget.LOCAL] is True

    @pytest.mark.asyncio
    async def test_webhook_notification_failure(self):
        """Test handling of webhook notification failures"""
        config = {"webhook_secret": "test_secret"}
        manager = CacheManager(config)

        from src.halcytone_content_generator.services.cache_manager import InvalidationResult, InvalidationStatus

        result = InvalidationResult(
            request_id="webhook_fail_test",
            status=InvalidationStatus.SUCCESS,
            targets_processed={CacheTarget.LOCAL: True},
            keys_invalidated=1,
            errors=[],
            duration_ms=50.0
        )

        # Mock failing webhook request
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Network error")
            )

            # Should not raise exception, just log error
            await manager._send_webhook_notification("https://failing-webhook.com", result)

            # Verify webhook was attempted
            mock_client.return_value.__aenter__.return_value.post.assert_called_once()

    def test_invalid_webhook_payload_handling(self):
        """Test handling of invalid webhook payloads"""
        config = {"api_keys": ["test_key"]}
        manager = CacheManager(config)

        # Test with invalid payload structure
        invalid_payload = {
            "event": "test",
            "targets": ["invalid_target"],  # Invalid target
            "keys": None
        }

        # Should raise HTTPException for invalid payload
        with pytest.raises(Exception):  # Could be HTTPException or ValueError
            asyncio.run(manager.process_webhook_invalidation(invalid_payload))


class TestCacheInvalidationPerformance:
    """Performance and load testing for cache invalidation"""

    @pytest.fixture
    def performance_cache_manager(self):
        """Cache manager optimized for performance testing"""
        config = {
            "api_keys": ["perf_test_key"],
            "max_history": 1000,
            "local": {}
        }
        return CacheManager(config)

    @pytest.mark.asyncio
    async def test_large_batch_invalidation_performance(self, performance_cache_manager):
        """Test performance with large batch invalidation"""
        # Set up large number of cache entries
        local_invalidator = performance_cache_manager.invalidators[CacheTarget.LOCAL]
        for i in range(1000):
            local_invalidator.set(f"perf_test:{i}", f"data_{i}")

        assert local_invalidator.size() == 1000

        from src.halcytone_content_generator.services.cache_manager import InvalidationRequest
        import time

        # Measure invalidation performance
        start_time = time.time()

        request = InvalidationRequest(
            targets=[CacheTarget.LOCAL],
            patterns=["perf_test:*"],
            reason="Performance test"
        )

        result = await performance_cache_manager.invalidate_cache(request)

        end_time = time.time()
        duration_seconds = end_time - start_time

        # Verify successful invalidation
        assert result.status == InvalidationStatus.SUCCESS
        assert local_invalidator.size() == 0

        # Performance assertion - should complete within reasonable time
        assert duration_seconds < 1.0  # Should complete within 1 second

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, performance_cache_manager):
        """Test performance with concurrent invalidation requests"""
        from src.halcytone_content_generator.services.cache_manager import InvalidationRequest
        import time

        start_time = time.time()

        # Create 20 concurrent requests
        requests = []
        for i in range(20):
            request = InvalidationRequest(
                targets=[CacheTarget.LOCAL],
                keys=[f"concurrent_perf:{i}"],
                reason=f"Concurrent performance test {i}"
            )
            requests.append(request)

        # Execute all concurrently
        results = await asyncio.gather(*[
            performance_cache_manager.invalidate_cache(request) for request in requests
        ])

        end_time = time.time()
        duration_seconds = end_time - start_time

        # Verify all completed successfully
        assert len(results) == 20
        assert all(result.status == InvalidationStatus.SUCCESS for result in results)

        # Performance assertion
        assert duration_seconds < 2.0  # Should handle 20 concurrent requests within 2 seconds

        # Verify all requests are in history
        assert len(performance_cache_manager.request_history) == 20