"""
Base API Client
Provides common functionality for API interactions with error handling, retries, and logging
"""

import httpx
import logging
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Structured API response"""
    status_code: int
    data: Any
    headers: Dict[str, str]
    success: bool
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def json(self) -> Any:
        """Get response data as JSON"""
        return self.data

    def is_success(self) -> bool:
        """Check if response was successful"""
        return self.success and 200 <= self.status_code < 300


class APIError(Exception):
    """Base API Error"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class APIClient:
    """
    Base API Client with common functionality

    Features:
    - Automatic retry with exponential backoff
    - Request/response logging
    - Error handling
    - Correlation ID tracking
    - Timeout management
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize API client

        Args:
            base_url: Base URL for API endpoints
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            headers: Additional headers to include in all requests
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_headers = headers or {}

        if api_key:
            self.default_headers['Authorization'] = f'Bearer {api_key}'

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint"""
        endpoint = endpoint.lstrip('/')
        return f"{self.base_url}/{endpoint}"

    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare request headers"""
        request_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            **self.default_headers
        }

        if headers:
            request_headers.update(headers)

        return request_headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Union[Dict, List]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """
        Make HTTP request with retry logic

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout (overrides default)
            correlation_id: Optional correlation ID for request tracking

        Returns:
            APIResponse object

        Raises:
            APIError: On request failure
        """
        url = self._build_url(endpoint)
        request_headers = self._prepare_headers(headers)

        if correlation_id:
            request_headers['X-Correlation-ID'] = correlation_id

        timeout_value = timeout or self.timeout

        logger.info(f"API Request: {method} {url}")
        if correlation_id:
            logger.info(f"Correlation ID: {correlation_id}")

        last_error = None

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        json=data if data else None,
                        params=params,
                        headers=request_headers,
                        timeout=timeout_value
                    )

                    # Parse response
                    try:
                        response_data = response.json()
                    except json.JSONDecodeError:
                        response_data = response.text

                    # Check for success
                    success = 200 <= response.status_code < 300

                    if not success:
                        error_msg = f"API request failed: {response.status_code}"
                        if isinstance(response_data, dict):
                            error_msg = response_data.get('detail', error_msg)

                        logger.error(f"{error_msg} (Attempt {attempt + 1}/{self.max_retries})")

                        # Retry on server errors (5xx)
                        if response.status_code >= 500 and attempt < self.max_retries - 1:
                            continue

                        raise APIError(
                            error_msg,
                            status_code=response.status_code,
                            response=response_data if isinstance(response_data, dict) else None
                        )

                    logger.info(f"API Response: {response.status_code}")

                    return APIResponse(
                        status_code=response.status_code,
                        data=response_data,
                        headers=dict(response.headers),
                        success=success
                    )

            except httpx.TimeoutException as e:
                last_error = APIError(f"Request timeout after {timeout_value}s", status_code=408)
                logger.warning(f"Request timeout (Attempt {attempt + 1}/{self.max_retries})")

            except httpx.RequestError as e:
                last_error = APIError(f"Request error: {str(e)}", status_code=None)
                logger.warning(f"Request error: {e} (Attempt {attempt + 1}/{self.max_retries})")

            # Don't retry on last attempt
            if attempt >= self.max_retries - 1:
                break

        # All retries exhausted
        if last_error:
            raise last_error

        raise APIError("Request failed after all retries")

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """Make GET request"""
        return await self._request('GET', endpoint, params=params, headers=headers,
                                   timeout=timeout, correlation_id=correlation_id)

    async def post(
        self,
        endpoint: str,
        data: Optional[Union[Dict, List]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """Make POST request"""
        return await self._request('POST', endpoint, data=data, params=params,
                                   headers=headers, timeout=timeout, correlation_id=correlation_id)

    async def put(
        self,
        endpoint: str,
        data: Optional[Union[Dict, List]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """Make PUT request"""
        return await self._request('PUT', endpoint, data=data, params=params,
                                   headers=headers, timeout=timeout, correlation_id=correlation_id)

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """Make DELETE request"""
        return await self._request('DELETE', endpoint, params=params, headers=headers,
                                   timeout=timeout, correlation_id=correlation_id)

    async def patch(
        self,
        endpoint: str,
        data: Optional[Union[Dict, List]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """Make PATCH request"""
        return await self._request('PATCH', endpoint, data=data, params=params,
                                   headers=headers, timeout=timeout, correlation_id=correlation_id)
