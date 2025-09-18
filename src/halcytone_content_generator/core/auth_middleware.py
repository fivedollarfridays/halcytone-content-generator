"""
API key authentication middleware and validation
"""
from fastapi import Request, HTTPException
from fastapi.security import APIKeyHeader, APIKeyQuery
from typing import Optional, Dict, List
import hashlib
import hmac
import time
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class APIKeyValidator:
    """
    Validates API keys and manages authentication
    """

    def __init__(self, valid_keys: Optional[Dict[str, Dict]] = None):
        """
        Initialize API key validator

        Args:
            valid_keys: Dictionary of valid API keys with metadata
        """
        # In production, these would come from a secure store
        self.valid_keys = valid_keys or {
            "test-key-123": {
                "service": "test",
                "permissions": ["read", "write"],
                "rate_limit": 100
            }
        }
        self.request_counts = {}
        self.blocked_keys = set()

    def validate_api_key(self, api_key: str) -> Dict:
        """
        Validate an API key

        Args:
            api_key: API key to validate

        Returns:
            Key metadata if valid

        Raises:
            HTTPException: If key is invalid
        """
        # Check if key is blocked
        if api_key in self.blocked_keys:
            logger.warning(f"Blocked API key attempted: {api_key}")
            raise HTTPException(
                status_code=403,
                detail="API key has been blocked"
            )

        # Check if key exists
        if api_key not in self.valid_keys:
            logger.warning(f"Invalid API key attempted: {api_key}")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )

        # Get key metadata
        key_data = self.valid_keys[api_key]

        # Check rate limit
        if self._check_rate_limit(api_key, key_data.get('rate_limit', 100)):
            logger.warning(f"Rate limit exceeded for key: {api_key}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )

        return key_data

    def _check_rate_limit(self, api_key: str, limit: int) -> bool:
        """
        Check if API key has exceeded rate limit

        Args:
            api_key: API key
            limit: Rate limit per minute

        Returns:
            True if rate limit exceeded
        """
        current_minute = int(time.time() / 60)
        key = f"{api_key}:{current_minute}"

        if key not in self.request_counts:
            self.request_counts[key] = 0

        self.request_counts[key] += 1

        # Clean old entries
        self._cleanup_request_counts(current_minute)

        return self.request_counts[key] > limit

    def _cleanup_request_counts(self, current_minute: int):
        """Clean up old request count entries"""
        keys_to_remove = []
        for key in self.request_counts:
            minute = int(key.split(':')[1])
            if current_minute - minute > 5:  # Keep 5 minutes of history
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.request_counts[key]

    def generate_api_key(self, service_name: str) -> str:
        """
        Generate a new API key for a service

        Args:
            service_name: Name of the service

        Returns:
            Generated API key
        """
        timestamp = str(time.time())
        data = f"{service_name}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def revoke_api_key(self, api_key: str):
        """Revoke an API key"""
        if api_key in self.valid_keys:
            del self.valid_keys[api_key]
            self.blocked_keys.add(api_key)
            logger.info(f"API key revoked: {api_key}")


class HMACValidator:
    """
    Validates HMAC signatures for webhook security
    """

    def __init__(self, secret_key: str):
        """
        Initialize HMAC validator

        Args:
            secret_key: Secret key for HMAC
        """
        self.secret_key = secret_key.encode()

    def generate_signature(self, payload: bytes) -> str:
        """
        Generate HMAC signature for payload

        Args:
            payload: Request payload

        Returns:
            HMAC signature
        """
        signature = hmac.new(
            self.secret_key,
            payload,
            hashlib.sha256
        ).hexdigest()
        return signature

    def validate_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Validate HMAC signature

        Args:
            payload: Request payload
            signature: Signature to validate

        Returns:
            True if signature is valid
        """
        expected_signature = self.generate_signature(payload)
        return hmac.compare_digest(expected_signature, signature)


# FastAPI dependencies
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def get_api_key(
    api_key_header: str = api_key_header,
    api_key_query: str = api_key_query,
) -> str:
    """
    Get API key from header or query parameter

    Args:
        api_key_header: API key from header
        api_key_query: API key from query

    Returns:
        API key

    Raises:
        HTTPException: If no API key provided
    """
    if api_key_header:
        return api_key_header
    elif api_key_query:
        return api_key_query
    else:
        raise HTTPException(
            status_code=401,
            detail="API key required"
        )


# Global validator instance
@lru_cache()
def get_validator() -> APIKeyValidator:
    """Get cached API key validator"""
    # In production, load keys from secure storage
    return APIKeyValidator({
        "content-gen-key-123": {
            "service": "content-generator",
            "permissions": ["read", "write", "admin"],
            "rate_limit": 1000
        },
        "crm-key-456": {
            "service": "crm",
            "permissions": ["read", "write"],
            "rate_limit": 500
        },
        "platform-key-789": {
            "service": "platform",
            "permissions": ["read", "write"],
            "rate_limit": 500
        }
    })


async def validate_api_key_dep(api_key: str = get_api_key) -> Dict:
    """
    Dependency for validating API keys in FastAPI routes

    Args:
        api_key: API key from request

    Returns:
        Key metadata if valid

    Raises:
        HTTPException: If key is invalid
    """
    validator = get_validator()
    return validator.validate_api_key(api_key)


async def require_permission(
    required_permission: str,
    key_data: Dict = validate_api_key_dep
) -> Dict:
    """
    Require specific permission for API key

    Args:
        required_permission: Required permission
        key_data: API key metadata

    Returns:
        Key metadata if permission granted

    Raises:
        HTTPException: If permission denied
    """
    permissions = key_data.get('permissions', [])

    if required_permission not in permissions and 'admin' not in permissions:
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: {required_permission} required"
        )

    return key_data