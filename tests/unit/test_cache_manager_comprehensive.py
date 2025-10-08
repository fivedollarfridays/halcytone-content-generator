"""
Comprehensive tests for CacheManager (cache_manager.py)
Target: 70%+ coverage

Tests cover:
- Enums and dataclasses
- Cache invalidator implementations (CDN, Local, API)
- CacheManager orchestration
- API key verification
- Webhook signature verification
- Cache invalidation workflows
- History tracking
- Edge cases
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
import hmac
import hashlib
import json

from halcytone_content_generator.services.cache_manager import (
    CacheTarget,
    InvalidationStatus,
    InvalidationRequest,
    InvalidationResult,
    CDNInvalidator,
    LocalCacheInvalidator,
    APICacheInvalidator,
    CacheManager
)


# Test Enums

class TestEnums:
    """Test enum definitions."""

    def test_cache_target_values(self):
        """Test CacheTarget enum values."""
        assert CacheTarget.CDN == "cdn"
        assert CacheTarget.LOCAL == "local"
        assert CacheTarget.API == "api"
        assert CacheTarget.REDIS == "redis"
        assert CacheTarget.MEMORY == "memory"
        assert CacheTarget.DATABASE == "database"

    def test_invalidation_status_values(self):
        """Test InvalidationStatus enum values."""
        assert InvalidationStatus.PENDING == "pending"
        assert InvalidationStatus.IN_PROGRESS == "in_progress"
        assert InvalidationStatus.SUCCESS == "success"
        assert InvalidationStatus.FAILED == "failed"
        assert InvalidationStatus.PARTIAL == "partial"


# Test Dataclasses

class TestInvalidationRequest:
    """Test InvalidationRequest dataclass."""

    def test_basic_creation(self):
        """Test basic InvalidationRequest creation."""
        request = InvalidationRequest(
            targets=[CacheTarget.CDN, CacheTarget.LOCAL],
            keys=["key1", "key2"]
        )

        assert len(request.targets) == 2
        assert CacheTarget.CDN in request.targets
        assert request.keys == ["key1", "key2"]
        assert request.timestamp is not None

    def test_with_patterns(self):
        """Test InvalidationRequest with patterns."""
        request = InvalidationRequest(
            targets=[CacheTarget.API],
            patterns=["*/users/*", "/api/v1/*"]
        )

        assert request.patterns is not None
        assert len(request.patterns) == 2

    def test_with_optional_fields(self):
        """Test InvalidationRequest with all optional fields."""
        request = InvalidationRequest(
            targets=[CacheTarget.CDN],
            keys=["test"],
            force=True,
            reason="Testing",
            initiated_by="test_user",
            webhook_url="https://example.com/webhook"
        )

        assert request.force is True
        assert request.reason == "Testing"
        assert request.initiated_by == "test_user"
        assert request.webhook_url == "https://example.com/webhook"

    def test_to_dict(self):
        """Test InvalidationRequest to_dict conversion."""
        request = InvalidationRequest(
            targets=[CacheTarget.CDN],
            keys=["key1"]
        )

        data = request.to_dict()

        assert isinstance(data, dict)
        assert 'targets' in data
        assert 'keys' in data
        assert 'timestamp' in data


class TestInvalidationResult:
    """Test InvalidationResult dataclass."""

    def test_basic_creation(self):
        """Test basic InvalidationResult creation."""
        result = InvalidationResult(
            request_id="req123",
            status=InvalidationStatus.SUCCESS,
            targets_processed={CacheTarget.CDN: True},
            keys_invalidated=10,
            errors=[],
            duration_ms=150.5
        )

        assert result.request_id == "req123"
        assert result.status == InvalidationStatus.SUCCESS
        assert result.keys_invalidated == 10
        assert result.duration_ms == 150.5
        assert result.timestamp is not None

    def test_with_errors(self):
        """Test InvalidationResult with errors."""
        result = InvalidationResult(
            request_id="req456",
            status=InvalidationStatus.FAILED,
            targets_processed={CacheTarget.API: False},
            keys_invalidated=0,
            errors=["Connection timeout", "API error"],
            duration_ms=5000.0
        )

        assert len(result.errors) == 2
        assert result.status == InvalidationStatus.FAILED

    def test_to_dict(self):
        """Test InvalidationResult to_dict conversion."""
        result = InvalidationResult(
            request_id="req789",
            status=InvalidationStatus.SUCCESS,
            targets_processed={CacheTarget.LOCAL: True},
            keys_invalidated=5,
            errors=[],
            duration_ms=100.0
        )

        data = result.to_dict()

        assert isinstance(data, dict)
        assert 'request_id' in data
        assert 'status' in data
        assert 'targets_processed' in data


# Test LocalCacheInvalidator

class TestLocalCacheInvalidator:
    """Test local cache invalidator."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test LocalCacheInvalidator initialization."""
        invalidator = LocalCacheInvalidator()

        assert invalidator._cache is not None
        assert invalidator._cache == {}
        assert invalidator._patterns is not None

    @pytest.mark.asyncio
    async def test_invalidate_by_keys(self):
        """Test invalidating specific keys."""
        invalidator = LocalCacheInvalidator()
        # Pre-populate cache
        invalidator._cache = {"key1": "value1", "key2": "value2", "key3": "value3"}

        result = await invalidator.invalidate(keys=["key1", "key3"])

        assert result is True  # Returns bool, not dict
        assert "key1" not in invalidator._cache
        assert "key2" in invalidator._cache  # Not invalidated
        assert "key3" not in invalidator._cache

    @pytest.mark.asyncio
    async def test_invalidate_by_pattern(self):
        """Test invalidating by pattern."""
        invalidator = LocalCacheInvalidator()
        invalidator._cache = {
            "user:123": "data1",
            "user:456": "data2",
            "post:789": "data3"
        }

        result = await invalidator.invalidate(patterns=["user:*"])

        assert result is True  # Returns bool
        # Verify user keys were removed
        assert "user:123" not in invalidator._cache
        assert "user:456" not in invalidator._cache
        assert "post:789" in invalidator._cache  # Not matching pattern

    @pytest.mark.asyncio
    async def test_invalidate_empty_cache(self):
        """Test invalidating empty cache."""
        invalidator = LocalCacheInvalidator()

        result = await invalidator.invalidate(keys=["nonexistent"])

        assert result is True  # Operation succeeds even if no keys found

    @pytest.mark.asyncio
    async def test_pattern_matching(self):
        """Test pattern matching logic."""
        invalidator = LocalCacheInvalidator()

        assert invalidator._matches_pattern("user:123", "user:*") is True
        assert invalidator._matches_pattern("post:456", "user:*") is False

    @pytest.mark.asyncio
    async def test_cache_operations(self):
        """Test set, get, size operations."""
        invalidator = LocalCacheInvalidator()

        invalidator.set("key1", "value1")
        assert invalidator.get("key1") == "value1"
        assert invalidator.size() == 1

        invalidator.set("key2", "value2")
        assert invalidator.size() == 2


# Test APICacheInvalidator

class TestAPICacheInvalidator:
    """Test API cache invalidator."""

    def test_initialization(self):
        """Test APICacheInvalidator initialization."""
        config = {
            "base_url": "https://api.example.com",
            "timeout": 30
        }
        invalidator = APICacheInvalidator(config)

        # Check that invalidator was created
        assert invalidator is not None

    @pytest.mark.asyncio
    async def test_invalidate_endpoints(self):
        """Test invalidating API endpoints."""
        config = {"base_url": "https://api.example.com"}
        invalidator = APICacheInvalidator(config)

        result = await invalidator.invalidate(keys=["/api/users", "/api/posts"])

        assert isinstance(result, bool)  # Returns bool like other invalidators

    @pytest.mark.asyncio
    async def test_api_pattern_matching(self):
        """Test API pattern matching."""
        config = {"base_url": "https://api.example.com"}
        invalidator = APICacheInvalidator(config)

        assert invalidator._matches_api_pattern("/api/users/123", "/api/users/*") is True
        assert invalidator._matches_api_pattern("/api/posts/456", "/api/users/*") is False

    @pytest.mark.asyncio
    async def test_is_invalidated(self):
        """Test checking if endpoint is invalidated."""
        config = {"base_url": "https://api.example.com"}
        invalidator = APICacheInvalidator(config)

        # Invalidate an endpoint
        await invalidator.invalidate(keys=["/api/test"])

        # Should be marked as invalidated
        assert invalidator.is_invalidated("/api/test") is True
        assert invalidator.is_invalidated("/api/other") is False


# Test CDNInvalidator

class TestCDNInvalidator:
    """Test CDN invalidator."""

    def test_initialization(self):
        """Test CDNInvalidator initialization."""
        config = {
            "provider": "cloudflare",
            "api_key": "test_key",
            "zone_id": "zone123"
        }
        invalidator = CDNInvalidator(config)

        # Check that invalidator was created
        assert invalidator is not None

    @pytest.mark.asyncio
    async def test_invalidate_paths(self):
        """Test invalidating CDN paths."""
        config = {
            "provider": "cloudflare",
            "api_key": "test_key",
            "zone_id": "zone123"
        }
        invalidator = CDNInvalidator(config)

        with patch.object(invalidator, '_invalidate_cloudflare', new_callable=AsyncMock) as mock_cf:
            mock_cf.return_value = {'invalidated': 5}

            result = await invalidator.invalidate(keys=["/static/css/*", "/static/js/*"])

            assert mock_cf.called
            assert isinstance(result, dict)


# Test CacheManager

class TestCacheManager:
    """Test CacheManager orchestration."""

    def test_initialization(self):
        """Test CacheManager initialization."""
        config = {
            "api_keys": ["test_api_key"],  # Uses api_keys list
            "webhook_secret": "test_secret",
            "cdn": {"provider": "cloudflare"},
            "max_history": 100
        }
        manager = CacheManager(config)

        assert "test_api_key" in manager.api_keys
        assert manager.webhook_secret == "test_secret"
        assert manager.request_history == []  # Uses request_history not invalidation_history

    def test_api_key_verification(self):
        """Test API key verification."""
        config = {"api_keys": ["correct_key"]}  # Pass as list
        manager = CacheManager(config)

        assert manager.verify_api_key("correct_key") is True
        assert manager.verify_api_key("wrong_key") is False

    def test_webhook_signature_verification(self):
        """Test webhook signature verification."""
        config = {"webhook_secret": "test_secret"}
        manager = CacheManager(config)

        payload = b'{"test": "data"}'
        signature = hmac.new(
            b"test_secret",
            payload,
            hashlib.sha256
        ).hexdigest()

        assert manager.verify_webhook_signature(payload, signature) is True
        assert manager.verify_webhook_signature(payload, "wrong_signature") is False

    @pytest.mark.asyncio
    async def test_invalidate_cache_single_target(self):
        """Test invalidating single cache target."""
        config = {
            "api_keys": ["test_key"],
            "max_history": 10
        }
        manager = CacheManager(config)

        request = InvalidationRequest(
            targets=[CacheTarget.LOCAL],
            keys=["test_key"]
        )

        result = await manager.invalidate_cache(request)

        assert result is not None
        assert result.status in [InvalidationStatus.SUCCESS, InvalidationStatus.PARTIAL]

    @pytest.mark.asyncio
    async def test_invalidate_cache_multiple_targets(self):
        """Test invalidating multiple cache targets."""
        config = {
            "api_keys": ["test_key"],
            "cdn": {"provider": "cloudflare"}
        }
        manager = CacheManager(config)

        request = InvalidationRequest(
            targets=[CacheTarget.LOCAL, CacheTarget.API],
            keys=["key1", "key2"]
        )

        result = await manager.invalidate_cache(request)

        assert result is not None
        assert len(result.targets_processed) > 0

    def test_generate_request_id(self):
        """Test request ID generation."""
        config = {"api_keys": ["test"]}
        manager = CacheManager(config)

        request = InvalidationRequest(
            targets=[CacheTarget.LOCAL],
            keys=["test"]
        )

        request_id = manager._generate_request_id(request)

        assert isinstance(request_id, str)
        assert len(request_id) > 0

    def test_add_to_history(self):
        """Test adding results to history."""
        config = {"api_keys": ["test"], "max_history": 5}
        manager = CacheManager(config)

        result = InvalidationResult(
            request_id="req1",
            status=InvalidationStatus.SUCCESS,
            targets_processed={CacheTarget.LOCAL: True},
            keys_invalidated=10,
            errors=[],
            duration_ms=100.0
        )

        manager._add_to_history(result)

        assert len(manager.request_history) == 1  # Uses request_history

    def test_history_limit(self):
        """Test history size limit enforcement."""
        config = {"api_keys": ["test"], "max_history": 3}
        manager = CacheManager(config)

        # Add more than max_history
        for i in range(5):
            result = InvalidationResult(
                request_id=f"req{i}",
                status=InvalidationStatus.SUCCESS,
                targets_processed={CacheTarget.LOCAL: True},
                keys_invalidated=1,
                errors=[],
                duration_ms=100.0
            )
            manager._add_to_history(result)

        # Should only keep max_history items
        assert len(manager.request_history) == 3

    def test_get_invalidation_history(self):
        """Test getting invalidation history."""
        config = {"api_keys": ["test"]}
        manager = CacheManager(config)

        # Add some history
        for i in range(3):
            result = InvalidationResult(
                request_id=f"req{i}",
                status=InvalidationStatus.SUCCESS,
                targets_processed={CacheTarget.LOCAL: True},
                keys_invalidated=i,
                errors=[],
                duration_ms=100.0
            )
            manager._add_to_history(result)

        history = manager.get_invalidation_history(limit=2)

        assert len(history) == 2
        assert all(isinstance(item, dict) for item in history)

    @pytest.mark.asyncio
    async def test_invalidate_with_force_flag(self):
        """Test invalidation with force flag."""
        config = {"api_keys": ["test"]}
        manager = CacheManager(config)

        request = InvalidationRequest(
            targets=[CacheTarget.LOCAL],
            keys=["test"],
            force=True
        )

        result = await manager.invalidate_cache(request)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_cache_stats(self):
        """Test getting cache statistics."""
        config = {"api_keys": ["test"]}
        manager = CacheManager(config)

        # Add some history
        result = InvalidationResult(
            request_id="req1",
            status=InvalidationStatus.SUCCESS,
            targets_processed={CacheTarget.LOCAL: True},
            keys_invalidated=10,
            errors=[],
            duration_ms=150.0
        )
        manager._add_to_history(result)

        stats = await manager.get_cache_stats()

        assert isinstance(stats, dict)
        assert 'total_requests' in stats
        assert 'recent_requests' in stats
        assert 'targets_configured' in stats
        assert 'health_status' in stats
        assert stats['total_requests'] == 1  # We added one result
        assert stats['recent_requests'] == 1


# Test Edge Cases

class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_invalidate_with_no_targets(self):
        """Test invalidation with empty targets list."""
        config = {"api_keys": ["test"]}
        manager = CacheManager(config)

        request = InvalidationRequest(
            targets=[],
            keys=["test"]
        )

        result = await manager.invalidate_cache(request)

        assert result.status in [InvalidationStatus.FAILED, InvalidationStatus.SUCCESS]

    @pytest.mark.asyncio
    async def test_invalidate_with_no_keys_or_patterns(self):
        """Test invalidation with no keys or patterns."""
        config = {"api_keys": ["test"]}
        manager = CacheManager(config)

        request = InvalidationRequest(
            targets=[CacheTarget.LOCAL]
        )

        result = await manager.invalidate_cache(request)

        # Should handle gracefully
        assert result is not None

    def test_invalid_webhook_signature_format(self):
        """Test webhook verification with invalid signature format."""
        config = {"webhook_secret": "test"}
        manager = CacheManager(config)

        # Invalid signature format
        assert manager.verify_webhook_signature(b"payload", "not_hex") is False

    @pytest.mark.asyncio
    async def test_local_cache_invalidate_nonexistent_keys(self):
        """Test local cache invalidation of non-existent keys."""
        invalidator = LocalCacheInvalidator()

        result = await invalidator.invalidate(keys=["key1", "key2", "key3"])

        # Invalidating non-existent keys should succeed (return True)
        assert result is True

    def test_request_to_dict_with_string_targets(self):
        """Test InvalidationRequest to_dict with string targets."""
        request = InvalidationRequest(
            targets=["cdn", "local"]  # Strings instead of enums
        )

        data = request.to_dict()

        assert 'targets' in data
        assert isinstance(data['targets'], list)

    def test_result_to_dict_with_string_targets(self):
        """Test InvalidationResult to_dict with mixed target types."""
        result = InvalidationResult(
            request_id="test",
            status=InvalidationStatus.SUCCESS,
            targets_processed={"cdn": True},  # String key
            keys_invalidated=1,
            errors=[],
            duration_ms=100.0
        )

        data = result.to_dict()

        assert 'targets_processed' in data

    @pytest.mark.asyncio
    async def test_cdn_invalidator_unknown_provider(self):
        """Test CDN invalidator with unknown provider."""
        config = {
            "provider": "unknown_provider",
            "api_key": "test"
        }
        invalidator = CDNInvalidator(config)

        result = await invalidator.invalidate(keys=["/test"])

        # Should handle unknown provider gracefully - returns False for invalid config
        assert result is False

    @pytest.mark.asyncio
    async def test_manager_initialize_invalidators(self):
        """Test manager initializing invalidators."""
        config = {
            "api_keys": ["test"],
            "cdn": {"provider": "cloudflare", "api_key": "test"},
            "api": {"base_url": "https://api.test.com"}
        }
        manager = CacheManager(config)

        # Check invalidators were initialized
        assert CacheTarget.LOCAL in manager.invalidators
        assert isinstance(manager.invalidators[CacheTarget.LOCAL], LocalCacheInvalidator)

    def test_history_get_with_limit_larger_than_size(self):
        """Test getting history with limit larger than history size."""
        config = {"api_keys": ["test"]}
        manager = CacheManager(config)

        # Add 2 items
        for i in range(2):
            result = InvalidationResult(
                request_id=f"req{i}",
                status=InvalidationStatus.SUCCESS,
                targets_processed={CacheTarget.LOCAL: True},
                keys_invalidated=1,
                errors=[],
                duration_ms=100.0
            )
            manager._add_to_history(result)

        # Request 10 items
        history = manager.get_invalidation_history(limit=10)

        # Should only return 2
        assert len(history) == 2
