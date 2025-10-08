"""
Cache Management API Endpoints
Sprint 4: Ecosystem Integration - Cache invalidation endpoints with authentication

Provides secure cache invalidation endpoints with API key authentication
and webhook support for automated cache management.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Header, Request, BackgroundTasks
from pydantic import BaseModel, Field, field_validator

from ..services.cache_manager import (
    get_cache_manager,
    CacheManager,
    InvalidationRequest,
    InvalidationResult,
    CacheTarget
)
# from ..core.auth import verify_api_key  # Not available yet
from ..config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["Cache Management"])


class CacheInvalidationRequest(BaseModel):
    """Request model for cache invalidation"""
    targets: List[str] = Field(
        default=["local"],
        description="Cache targets to invalidate: cdn, local, api, redis, memory, database"
    )
    keys: Optional[List[str]] = Field(
        default=None,
        description="Specific cache keys to invalidate"
    )
    patterns: Optional[List[str]] = Field(
        default=None,
        description="Cache key patterns to invalidate (supports * wildcard)"
    )
    force: bool = Field(
        default=False,
        description="Force invalidation of all cache entries"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for cache invalidation"
    )
    webhook_url: Optional[str] = Field(
        default=None,
        description="Optional webhook URL for completion notification"
    )

    @field_validator('targets')
    @classmethod
    def validate_targets(cls, v):
        """Validate cache targets"""
        valid_targets = [target.value for target in CacheTarget]
        for target in v:
            if target not in valid_targets:
                raise ValueError(f"Invalid cache target: {target}. Valid targets: {valid_targets}")
        return v

    @field_validator('patterns')
    @classmethod
    def validate_patterns(cls, v):
        """Validate cache patterns"""
        if v:
            for pattern in v:
                if not isinstance(pattern, str) or len(pattern) == 0:
                    raise ValueError("Cache patterns must be non-empty strings")
        return v


class WebhookInvalidationPayload(BaseModel):
    """Webhook payload for automatic cache invalidation"""
    event: str = Field(
        description="Event that triggered invalidation: content_updated, deployment, manual"
    )
    targets: List[str] = Field(
        default=["local"],
        description="Cache targets to invalidate"
    )
    keys: Optional[List[str]] = Field(
        default=None,
        description="Specific cache keys to invalidate"
    )
    patterns: Optional[List[str]] = Field(
        default=None,
        description="Cache key patterns to invalidate"
    )
    force: bool = Field(
        default=False,
        description="Force complete cache invalidation"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for invalidation"
    )
    webhook_url: Optional[str] = Field(
        default=None,
        description="Callback URL for completion notification"
    )


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics"""
    targets_configured: List[str]
    health_status: Dict[str, bool]
    recent_requests: int
    total_requests: int
    webhook_configured: bool
    api_keys_configured: int


class InvalidationHistoryResponse(BaseModel):
    """Response model for invalidation history"""
    history: List[Dict[str, Any]]
    total_count: int
    limit: int


async def verify_cache_api_key(x_api_key: str = Header(..., description="API key for cache operations")):
    """Verify API key for cache operations"""
    cache_manager = get_cache_manager()

    if not cache_manager.verify_api_key(x_api_key):
        logger.warning(f"Invalid API key for cache operation: {x_api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key for cache operations"
        )
    return x_api_key


@router.post(
    "/invalidate",
    response_model=Dict[str, Any],
    summary="Invalidate Cache",
    description="Invalidate cache across multiple targets with API key authentication"
)
async def invalidate_cache(
    request: CacheInvalidationRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_cache_api_key)
) -> Dict[str, Any]:
    """
    Invalidate cache across specified targets

    Requires API key authentication via X-API-Key header.
    Supports multiple cache targets: CDN, local cache, API cache, Redis, etc.

    Example request:
    ```json
    {
        "targets": ["cdn", "local"],
        "keys": ["user:123", "content:456"],
        "patterns": ["api/v1/*", "images/*"],
        "force": false,
        "reason": "Content update",
        "webhook_url": "https://example.com/webhook"
    }
    ```
    """
    try:
        cache_manager = get_cache_manager()

        # Convert to internal request format
        invalidation_request = InvalidationRequest(
            targets=[CacheTarget(target) for target in request.targets],
            keys=request.keys,
            patterns=request.patterns,
            force=request.force,
            reason=request.reason or "Manual invalidation via API",
            initiated_by=f"api_key:{api_key[:8]}...",
            webhook_url=request.webhook_url
        )

        logger.info(f"Processing cache invalidation request: targets={request.targets}")

        # Execute cache invalidation
        result = await cache_manager.invalidate_cache(invalidation_request)

        return {
            "success": result.status.value in ["success", "partial"],
            "request_id": result.request_id,
            "status": result.status.value,
            "targets_processed": {
                target.value if hasattr(target, 'value') else str(target): success
                for target, success in result.targets_processed.items()
            },
            "keys_invalidated": result.keys_invalidated,
            "duration_ms": result.duration_ms,
            "errors": result.errors,
            "timestamp": result.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache invalidation failed: {str(e)}"
        )


@router.post(
    "/webhook",
    response_model=Dict[str, Any],
    summary="Webhook Cache Invalidation",
    description="Process cache invalidation triggered by webhook with signature verification"
)
async def webhook_invalidation(
    request: Request,
    payload: WebhookInvalidationPayload,
    x_signature: Optional[str] = Header(None, description="Webhook signature for verification")
):
    """
    Process cache invalidation triggered by webhook

    Supports signature verification for secure webhook processing.
    Common webhook sources: CI/CD pipelines, content management systems, deployment tools.

    Example webhook payload:
    ```json
    {
        "event": "content_updated",
        "targets": ["cdn", "api"],
        "patterns": ["api/v1/content/*"],
        "reason": "Content management system update"
    }
    ```
    """
    try:
        cache_manager = get_cache_manager()

        # Get raw body for signature verification
        body = await request.body()

        # Verify webhook signature if provided
        if x_signature:
            if not cache_manager.verify_webhook_signature(body, x_signature):
                logger.warning("Invalid webhook signature")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid webhook signature"
                )

        logger.info(f"Processing webhook cache invalidation: event={payload.event}")

        # Process webhook invalidation
        result = await cache_manager.process_webhook_invalidation(payload.dict())

        return {
            "success": result.status.value in ["success", "partial"],
            "request_id": result.request_id,
            "status": result.status.value,
            "targets_processed": result.targets_processed,
            "keys_invalidated": result.keys_invalidated,
            "duration_ms": result.duration_ms,
            "webhook_event": payload.event,
            "timestamp": result.timestamp.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook cache invalidation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Cache Health Check",
    description="Check health status of all configured cache targets"
)
async def cache_health_check(
    api_key: str = Depends(verify_cache_api_key)
) -> Dict[str, Any]:
    """
    Check health status of all cache targets

    Returns health status for each configured cache target:
    - CDN (CloudFlare, AWS CloudFront)
    - Local cache (in-memory)
    - API cache
    - Redis cache
    - Database cache
    """
    try:
        cache_manager = get_cache_manager()
        health_status = await cache_manager.health_check()

        return {
            "overall_health": "healthy" if all(health_status.values()) else "degraded",
            "targets": {
                target.value if hasattr(target, 'value') else str(target): {
                    "healthy": healthy,
                    "status": "operational" if healthy else "unavailable"
                }
                for target, healthy in health_status.items()
            },
            "timestamp": datetime.utcnow().isoformat(),
            "total_targets": len(health_status)
        }

    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=CacheStatsResponse,
    summary="Cache Statistics",
    description="Get comprehensive cache system statistics"
)
async def cache_statistics(
    api_key: str = Depends(verify_cache_api_key)
) -> CacheStatsResponse:
    """
    Get comprehensive cache system statistics

    Includes:
    - Configured cache targets
    - Health status of each target
    - Request statistics
    - Configuration status
    """
    try:
        cache_manager = get_cache_manager()
        stats = await cache_manager.get_cache_stats()

        return CacheStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Cache statistics retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Statistics retrieval failed: {str(e)}"
        )


@router.get(
    "/history",
    response_model=InvalidationHistoryResponse,
    summary="Invalidation History",
    description="Get recent cache invalidation history"
)
async def invalidation_history(
    limit: int = 50,
    api_key: str = Depends(verify_cache_api_key)
) -> InvalidationHistoryResponse:
    """
    Get recent cache invalidation history

    Parameters:
    - limit: Maximum number of recent invalidations to return (default: 50, max: 200)

    Returns chronological list of invalidation operations with:
    - Request ID and status
    - Targets processed
    - Keys invalidated
    - Duration and errors
    """
    try:
        if limit > 200:
            limit = 200

        cache_manager = get_cache_manager()
        history = cache_manager.get_invalidation_history(limit)

        return InvalidationHistoryResponse(
            history=history,
            total_count=len(cache_manager.request_history),
            limit=limit
        )

    except Exception as e:
        logger.error(f"Invalidation history retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"History retrieval failed: {str(e)}"
        )


@router.delete(
    "/clear-all",
    response_model=Dict[str, Any],
    summary="Clear All Caches",
    description="Force clear all cache targets (USE WITH CAUTION)"
)
async def clear_all_caches(
    confirm: bool = False,
    api_key: str = Depends(verify_cache_api_key)
) -> Dict[str, Any]:
    """
    Force clear all configured cache targets

    **WARNING: This will clear ALL cache data across all targets.**

    Parameters:
    - confirm: Must be true to execute the operation

    This operation:
    - Clears CDN cache completely
    - Purges local cache
    - Invalidates all API cache entries
    - Resets Redis cache (if configured)
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to clear all caches"
        )

    try:
        cache_manager = get_cache_manager()

        # Get all configured targets
        all_targets = list(cache_manager.invalidators.keys())

        invalidation_request = InvalidationRequest(
            targets=all_targets,
            force=True,
            reason="Force clear all caches via API",
            initiated_by=f"api_key:{api_key[:8]}..."
        )

        logger.warning(f"CLEARING ALL CACHES - initiated by API key {api_key[:8]}...")

        result = await cache_manager.invalidate_cache(invalidation_request)

        return {
            "success": result.status.value in ["success", "partial"],
            "request_id": result.request_id,
            "status": result.status.value,
            "targets_cleared": list(result.targets_processed.keys()),
            "duration_ms": result.duration_ms,
            "warning": "All cache data has been cleared",
            "timestamp": result.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Clear all caches failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Clear all caches failed: {str(e)}"
        )


# Utility endpoint for testing webhook signatures
@router.post(
    "/webhook/test",
    response_model=Dict[str, Any],
    summary="Test Webhook Signature",
    description="Test webhook signature verification (for development/testing)"
)
async def test_webhook_signature(
    request: Request,
    x_signature: str = Header(..., description="Test signature")
):
    """
    Test webhook signature verification

    Useful for development and testing webhook integrations.
    Validates signature without processing invalidation.
    """
    try:
        cache_manager = get_cache_manager()
        body = await request.body()

        is_valid = cache_manager.verify_webhook_signature(body, x_signature)

        return {
            "signature_valid": is_valid,
            "signature_provided": x_signature,
            "body_length": len(body),
            "webhook_secret_configured": bool(cache_manager.webhook_secret),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Webhook signature test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Signature test failed: {str(e)}"
        )