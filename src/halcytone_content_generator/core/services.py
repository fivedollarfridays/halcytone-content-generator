"""
Centralized service management and dependency injection
Provides service instances configured for the current environment
"""

import logging
from typing import Optional
from functools import lru_cache

from ..config.enhanced_config import get_production_settings, ProductionSettings
from ..services.service_factory import ServiceFactory, get_service_factory, create_crm_client, create_platform_client
from ..services.crm_client_v2 import EnhancedCRMClient
from ..services.platform_client_v2 import EnhancedPlatformClient
from ..services.publishers.email_publisher import EmailPublisher
from ..services.publishers.web_publisher import WebPublisher
from ..services.publishers.social_publisher import SocialPublisher

logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Container for managing service dependencies with environment-based configuration
    """

    def __init__(self, settings: ProductionSettings):
        """
        Initialize service container

        Args:
            settings: Production settings
        """
        self.settings = settings
        self.service_factory = ServiceFactory(settings)
        self._crm_client: Optional[EnhancedCRMClient] = None
        self._platform_client: Optional[EnhancedPlatformClient] = None
        self._publishers: Optional[dict] = None

    async def get_crm_client(self) -> EnhancedCRMClient:
        """
        Get CRM client instance

        Returns:
            EnhancedCRMClient configured for current environment
        """
        if not self._crm_client:
            self._crm_client = self.service_factory.create_crm_client()
        return self._crm_client

    async def get_platform_client(self) -> EnhancedPlatformClient:
        """
        Get Platform client instance

        Returns:
            EnhancedPlatformClient configured for current environment
        """
        if not self._platform_client:
            self._platform_client = self.service_factory.create_platform_client()
        return self._platform_client

    async def get_publishers(self) -> dict:
        """
        Get all configured publishers

        Returns:
            Dictionary of publisher instances
        """
        if not self._publishers:
            # Get configured service clients
            crm_client = await self.get_crm_client()
            platform_client = await self.get_platform_client()

            # Create legacy configuration for publishers
            config = {
                'crm_base_url': crm_client.base_url,
                'crm_api_key': crm_client.api_key,
                'platform_base_url': platform_client.base_url,
                'platform_api_key': platform_client.api_key,
                'dry_run': self.settings.DRY_RUN_MODE,
                'environment': self.settings.ENVIRONMENT
            }

            self._publishers = {
                'email': EmailPublisher(config),
                'web': WebPublisher(config),
                'social': SocialPublisher(config)
            }

            logger.info(f"Publishers configured for {self.settings.ENVIRONMENT} environment")

        return self._publishers

    async def validate_services(self) -> dict:
        """
        Validate all service connections

        Returns:
            Validation results
        """
        return await self.service_factory.validate_services()

    def get_service_info(self) -> dict:
        """
        Get service configuration information

        Returns:
            Service configuration details
        """
        return self.service_factory.get_service_info()

    def reset_cache(self):
        """Reset all cached service instances"""
        self._crm_client = None
        self._platform_client = None
        self._publishers = None
        self.service_factory.clear_cache()
        logger.info("Service container cache cleared")


# Global service container
_global_container: Optional[ServiceContainer] = None


async def get_service_container(settings: ProductionSettings = None) -> ServiceContainer:
    """
    Get or create global service container

    Args:
        settings: Production settings (optional)

    Returns:
        ServiceContainer instance
    """
    global _global_container

    if settings:
        # Create new container with provided settings
        _global_container = ServiceContainer(settings)
    elif not _global_container:
        # Load settings if no container exists
        settings = await get_production_settings()
        _global_container = ServiceContainer(settings)

    return _global_container


def reset_service_container():
    """Reset global service container (for testing)"""
    global _global_container
    _global_container = None


# FastAPI dependency functions
async def get_crm_client() -> EnhancedCRMClient:
    """
    FastAPI dependency for CRM client

    Returns:
        EnhancedCRMClient instance
    """
    container = await get_service_container()
    return await container.get_crm_client()


async def get_platform_client() -> EnhancedPlatformClient:
    """
    FastAPI dependency for Platform client

    Returns:
        EnhancedPlatformClient instance
    """
    container = await get_service_container()
    return await container.get_platform_client()


async def get_publishers() -> dict:
    """
    FastAPI dependency for publishers

    Returns:
        Dictionary of publisher instances
    """
    container = await get_service_container()
    return await container.get_publishers()


# Compatibility function for existing endpoints
async def get_publishers_legacy(settings) -> dict:
    """
    Legacy publisher creation for backwards compatibility
    This function maintains compatibility with existing endpoints while using the new service factory

    Args:
        settings: Legacy settings object

    Returns:
        Dictionary of publisher instances
    """
    try:
        # Try to get production settings if available
        if hasattr(settings, 'ENVIRONMENT'):
            # This is likely already a production settings object
            container = await get_service_container(settings)
        else:
            # This is a legacy settings object, need to adapt
            # For now, use the global container with default settings
            container = await get_service_container()

        return await container.get_publishers()

    except Exception as e:
        logger.warning(f"Failed to use new service container, falling back to legacy publishers: {e}")

        # Fallback to legacy direct instantiation
        config = {
            'crm_base_url': getattr(settings, 'CRM_BASE_URL', ''),
            'crm_api_key': getattr(settings, 'CRM_API_KEY', ''),
            'platform_base_url': getattr(settings, 'PLATFORM_BASE_URL', ''),
            'platform_api_key': getattr(settings, 'PLATFORM_API_KEY', ''),
            'dry_run': getattr(settings, 'DRY_RUN', False) or getattr(settings, 'DRY_RUN_MODE', False)
        }

        return {
            'email': EmailPublisher(config),
            'web': WebPublisher(config),
            'social': SocialPublisher(config)
        }


# Service validation endpoint helpers
async def validate_all_services() -> dict:
    """
    Validate all service connections

    Returns:
        Validation results for all services
    """
    container = await get_service_container()
    return await container.validate_services()


async def get_service_info() -> dict:
    """
    Get comprehensive service configuration information

    Returns:
        Service configuration details
    """
    container = await get_service_container()
    service_info = container.get_service_info()

    # Add additional container info
    service_info.update({
        'container_initialized': _global_container is not None,
        'settings_environment': container.settings.ENVIRONMENT,
        'dry_run_mode': container.settings.DRY_RUN_MODE,
        'use_mock_services': container.settings.USE_MOCK_SERVICES
    })

    return service_info