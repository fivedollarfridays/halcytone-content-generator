"""
Service Factory for Environment-Based Client Selection
Provides centralized service instantiation with environment-specific configuration
"""

import logging
from typing import Dict, Any, Protocol, runtime_checkable
from enum import Enum

from ..config.enhanced_config import ProductionSettings
from ..config import Settings  # Legacy settings for compatibility
from .crm_client_v2 import EnhancedCRMClient
from .platform_client_v2 import EnhancedPlatformClient

logger = logging.getLogger(__name__)


class ServiceEnvironment(Enum):
    """Service environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@runtime_checkable
class ServiceClient(Protocol):
    """Protocol for service clients"""

    async def test_connection(self) -> Dict[str, Any]:
        """Test service connection"""
        ...


class ServiceRegistry:
    """Registry of available service implementations"""

    def __init__(self):
        self._crm_clients = {}
        self._platform_clients = {}
        self._initialized = False

    def register_crm_client(self, environment: ServiceEnvironment, client_class):
        """Register CRM client for environment"""
        self._crm_clients[environment] = client_class
        logger.debug(f"Registered CRM client for {environment.value}")

    def register_platform_client(self, environment: ServiceEnvironment, client_class):
        """Register Platform client for environment"""
        self._platform_clients[environment] = client_class
        logger.debug(f"Registered Platform client for {environment.value}")

    def get_crm_client_class(self, environment: ServiceEnvironment):
        """Get CRM client class for environment"""
        return self._crm_clients.get(environment)

    def get_platform_client_class(self, environment: ServiceEnvironment):
        """Get Platform client class for environment"""
        return self._platform_clients.get(environment)

    def list_available_services(self) -> Dict[str, list]:
        """List all registered services"""
        return {
            "crm_clients": list(self._crm_clients.keys()),
            "platform_clients": list(self._platform_clients.keys())
        }


# Global service registry
_service_registry = ServiceRegistry()


class ServiceFactory:
    """
    Factory for creating environment-appropriate service clients
    """

    def __init__(self, settings: ProductionSettings):
        """
        Initialize service factory

        Args:
            settings: Production settings with environment configuration
        """
        self.settings = settings
        self.environment = ServiceEnvironment(settings.ENVIRONMENT)
        self._service_cache: Dict[str, ServiceClient] = {}

        # Initialize registry if not done
        if not _service_registry._initialized:
            self._initialize_registry()

    def _initialize_registry(self):
        """Initialize service registry with default implementations"""
        # Register CRM clients
        _service_registry.register_crm_client(ServiceEnvironment.DEVELOPMENT, EnhancedCRMClient)
        _service_registry.register_crm_client(ServiceEnvironment.STAGING, EnhancedCRMClient)
        _service_registry.register_crm_client(ServiceEnvironment.PRODUCTION, EnhancedCRMClient)
        _service_registry.register_crm_client(ServiceEnvironment.TESTING, EnhancedCRMClient)

        # Register Platform clients
        _service_registry.register_platform_client(ServiceEnvironment.DEVELOPMENT, EnhancedPlatformClient)
        _service_registry.register_platform_client(ServiceEnvironment.STAGING, EnhancedPlatformClient)
        _service_registry.register_platform_client(ServiceEnvironment.PRODUCTION, EnhancedPlatformClient)
        _service_registry.register_platform_client(ServiceEnvironment.TESTING, EnhancedPlatformClient)

        _service_registry._initialized = True
        logger.info("Service registry initialized")

    def create_crm_client(self, force_recreate: bool = False) -> EnhancedCRMClient:
        """
        Create CRM client for current environment

        Args:
            force_recreate: Force creation of new client instance

        Returns:
            EnhancedCRMClient instance
        """
        cache_key = f"crm_{self.environment.value}"

        if not force_recreate and cache_key in self._service_cache:
            return self._service_cache[cache_key]

        # Get client class from registry
        client_class = _service_registry.get_crm_client_class(self.environment)
        if not client_class:
            raise ValueError(f"No CRM client registered for environment: {self.environment.value}")

        # Create legacy settings adapter for existing client
        legacy_settings = self._create_legacy_settings_adapter()

        # Create client with environment-specific configuration
        client = client_class(legacy_settings)

        # Configure client for environment
        self._configure_crm_client(client)

        # Cache the client
        self._service_cache[cache_key] = client

        logger.info(f"Created CRM client for {self.environment.value} environment")
        return client

    def create_platform_client(self, force_recreate: bool = False) -> EnhancedPlatformClient:
        """
        Create Platform client for current environment

        Args:
            force_recreate: Force creation of new client instance

        Returns:
            EnhancedPlatformClient instance
        """
        cache_key = f"platform_{self.environment.value}"

        if not force_recreate and cache_key in self._service_cache:
            return self._service_cache[cache_key]

        # Get client class from registry
        client_class = _service_registry.get_platform_client_class(self.environment)
        if not client_class:
            raise ValueError(f"No Platform client registered for environment: {self.environment.value}")

        # Create legacy settings adapter for existing client
        legacy_settings = self._create_legacy_settings_adapter()

        # Create client with environment-specific configuration
        client = client_class(legacy_settings)

        # Configure client for environment
        self._configure_platform_client(client)

        # Cache the client
        self._service_cache[cache_key] = client

        logger.info(f"Created Platform client for {self.environment.value} environment")
        return client

    def _create_legacy_settings_adapter(self) -> Settings:
        """
        Create legacy Settings object from ProductionSettings for compatibility

        Returns:
            Settings object compatible with existing clients
        """
        # Create a settings-like object that existing clients expect
        class LegacySettingsAdapter:
            def __init__(self, prod_settings: ProductionSettings):
                # Basic settings
                self.ENVIRONMENT = prod_settings.ENVIRONMENT
                self.DEBUG = prod_settings.DEBUG
                self.DRY_RUN_MODE = prod_settings.DRY_RUN_MODE
                self.DRY_RUN = prod_settings.DRY_RUN_MODE  # Alias
                self.USE_MOCK_SERVICES = prod_settings.USE_MOCK_SERVICES
                self.SERVICE_NAME = prod_settings.SERVICE_NAME

                # CRM settings from external services config
                self.CRM_BASE_URL = prod_settings.external_services.CRM_BASE_URL
                self.CRM_API_KEY = prod_settings.external_services.CRM_API_KEY
                self.CRM_TIMEOUT = prod_settings.external_services.CRM_TIMEOUT
                self.CRM_MAX_RETRIES = prod_settings.external_services.CRM_MAX_RETRIES

                # Platform settings from external services config
                self.PLATFORM_BASE_URL = prod_settings.external_services.PLATFORM_BASE_URL
                self.PLATFORM_API_KEY = prod_settings.external_services.PLATFORM_API_KEY
                self.PLATFORM_TIMEOUT = prod_settings.external_services.PLATFORM_TIMEOUT
                self.PLATFORM_MAX_RETRIES = prod_settings.external_services.PLATFORM_MAX_RETRIES

                # Email settings (with defaults for existing clients)
                self.EMAIL_BATCH_SIZE = getattr(prod_settings, 'EMAIL_BATCH_SIZE', 50)
                self.EMAIL_RATE_LIMIT = getattr(prod_settings, 'EMAIL_RATE_LIMIT', 100)

                # Circuit breaker settings (with defaults)
                self.CIRCUIT_BREAKER_FAILURE_THRESHOLD = getattr(prod_settings, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 5)
                self.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = getattr(prod_settings, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60)

                # Retry settings (with defaults)
                self.MAX_RETRIES = getattr(prod_settings, 'MAX_RETRIES', 3)
                self.RETRY_MAX_WAIT = getattr(prod_settings, 'RETRY_MAX_WAIT', 60)

                # Monitoring settings
                self.ENABLE_METRICS = prod_settings.monitoring.ENABLE_METRICS

        return LegacySettingsAdapter(self.settings)

    def _configure_crm_client(self, client: EnhancedCRMClient):
        """
        Apply environment-specific configuration to CRM client

        Args:
            client: CRM client to configure
        """
        if self.environment == ServiceEnvironment.PRODUCTION:
            # Production-specific CRM configuration
            if self.settings.USE_MOCK_SERVICES:
                logger.warning("Mock services enabled in production CRM client")

            # Validate production endpoints
            if not client.base_url.startswith('https://'):
                logger.error(f"Production CRM URL must use HTTPS: {client.base_url}")

            # Ensure strong API key
            if len(client.api_key) < 16:
                logger.warning("CRM API key may be too short for production")

        elif self.environment == ServiceEnvironment.DEVELOPMENT:
            # Development-specific configuration
            logger.info("CRM client configured for development environment")

        elif self.environment == ServiceEnvironment.STAGING:
            # Staging-specific configuration
            logger.info("CRM client configured for staging environment")

        logger.debug(f"CRM client configured: {client.base_url}")

    def _configure_platform_client(self, client: EnhancedPlatformClient):
        """
        Apply environment-specific configuration to Platform client

        Args:
            client: Platform client to configure
        """
        if self.environment == ServiceEnvironment.PRODUCTION:
            # Production-specific Platform configuration
            if self.settings.USE_MOCK_SERVICES:
                logger.warning("Mock services enabled in production Platform client")

            # Validate production endpoints
            if not client.base_url.startswith('https://'):
                logger.error(f"Production Platform URL must use HTTPS: {client.base_url}")

            # Ensure strong API key
            if len(client.api_key) < 16:
                logger.warning("Platform API key may be too short for production")

        elif self.environment == ServiceEnvironment.DEVELOPMENT:
            # Development-specific configuration
            logger.info("Platform client configured for development environment")

        elif self.environment == ServiceEnvironment.STAGING:
            # Staging-specific configuration
            logger.info("Platform client configured for staging environment")

        logger.debug(f"Platform client configured: {client.base_url}")

    async def validate_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Validate all service connections

        Returns:
            Validation results for all services
        """
        results = {}

        try:
            # Test CRM client
            crm_client = self.create_crm_client()
            crm_result = await crm_client.test_connection()
            results['crm'] = {
                'status': 'connected' if crm_result.get('connected', False) else 'failed',
                'environment': self.environment.value,
                'base_url': crm_client.base_url,
                'details': crm_result
            }
        except Exception as e:
            results['crm'] = {
                'status': 'error',
                'environment': self.environment.value,
                'error': str(e)
            }

        try:
            # Test Platform client
            platform_client = self.create_platform_client()
            # Platform client doesn't have test_connection, so check basic attributes
            results['platform'] = {
                'status': 'configured',
                'environment': self.environment.value,
                'base_url': platform_client.base_url,
                'dry_run_mode': platform_client.dry_run_mode,
                'use_mock_services': platform_client.use_mock_services
            }
        except Exception as e:
            results['platform'] = {
                'status': 'error',
                'environment': self.environment.value,
                'error': str(e)
            }

        return results

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about current service configuration

        Returns:
            Service configuration information
        """
        return {
            'environment': self.environment.value,
            'dry_run_mode': self.settings.DRY_RUN_MODE,
            'use_mock_services': self.settings.USE_MOCK_SERVICES,
            'available_services': _service_registry.list_available_services(),
            'cached_clients': list(self._service_cache.keys())
        }

    def clear_cache(self):
        """Clear service client cache"""
        self._service_cache.clear()
        logger.info("Service factory cache cleared")


# Global service factory instance
_global_service_factory = None


async def get_service_factory(settings: ProductionSettings = None) -> ServiceFactory:
    """
    Get global service factory instance

    Args:
        settings: Production settings (creates new factory if provided)

    Returns:
        ServiceFactory instance
    """
    global _global_service_factory

    if settings:
        _global_service_factory = ServiceFactory(settings)
    elif not _global_service_factory:
        # If no settings provided and no factory exists, we need settings
        raise ValueError("ServiceFactory requires ProductionSettings to be initialized")

    return _global_service_factory


def reset_service_factory():
    """Reset global service factory (for testing)"""
    global _global_service_factory
    _global_service_factory = None


# Convenience functions for service creation
async def create_crm_client(settings: ProductionSettings = None, force_recreate: bool = False) -> EnhancedCRMClient:
    """
    Create CRM client with current environment configuration

    Args:
        settings: Production settings (optional)
        force_recreate: Force creation of new client

    Returns:
        EnhancedCRMClient instance
    """
    factory = await get_service_factory(settings)
    return factory.create_crm_client(force_recreate)


async def create_platform_client(settings: ProductionSettings = None, force_recreate: bool = False) -> EnhancedPlatformClient:
    """
    Create Platform client with current environment configuration

    Args:
        settings: Production settings (optional)
        force_recreate: Force creation of new client

    Returns:
        EnhancedPlatformClient instance
    """
    factory = await get_service_factory(settings)
    return factory.create_platform_client(force_recreate)


async def validate_all_services(settings: ProductionSettings = None) -> Dict[str, Dict[str, Any]]:
    """
    Validate all service connections

    Args:
        settings: Production settings (optional)

    Returns:
        Validation results for all services
    """
    factory = await get_service_factory(settings)
    return await factory.validate_services()