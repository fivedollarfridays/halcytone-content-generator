"""
API Client Library
Provides reusable API clients and helpers for interacting with Content Generator services
"""

from .base_client import APIClient, APIError, APIResponse

# Import ContentGeneratorClient separately to avoid circular imports
# Use: from halcytone_content_generator.lib.api.content_generator import ContentGeneratorClient

__all__ = [
    'APIClient',
    'APIError',
    'APIResponse',
]
