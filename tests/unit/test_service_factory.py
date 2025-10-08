"""
Comprehensive tests for ServiceFactory - Environment-based service client creation
Tests cover: ServiceEnvironment, ServiceRegistry, ServiceFactory, and global functions
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any

from halcytone_content_generator.services.service_factory import (
    ServiceEnvironment,
    ServiceRegistry,
    ServiceFactory,
    ServiceClient,
    get_service_factory,
    reset_service_factory,
    create_crm_client,
    create_platform_client,
    validate_all_services,
    _service_registry,
    _global_service_factory
)


# ========== ServiceEnvironment Enum Tests ==========

class TestServiceEnvironment:
    """Test ServiceEnvironment enum"""

    def test_development_environment(self):
        """Test DEVELOPMENT environment value"""
        assert ServiceEnvironment.DEVELOPMENT.value == "development"

    def test_staging_environment(self):
        """Test STAGING environment value"""
        assert ServiceEnvironment.STAGING.value == "staging"

    def test_production_environment(self):
        """Test PRODUCTION environment value"""
        assert ServiceEnvironment.PRODUCTION.value == "production"

    def test_testing_environment(self):
        """Test TESTING environment value"""
        assert ServiceEnvironment.TESTING.value == "testing"

    def test_environment_from_string(self):
        """Test creating environment from string"""
        env = ServiceEnvironment("development")
        assert env == ServiceEnvironment.DEVELOPMENT

    def test_all_environments_unique(self):
        """Test all environment values are unique"""
        environments = [e.value for e in ServiceEnvironment]
        assert len(environments) == len(set(environments))


# ========== ServiceRegistry Tests ==========

class TestServiceRegistry:
    """Test ServiceRegistry class"""

    @pytest.fixture
    def registry(self):
        """Create fresh ServiceRegistry for each test"""
        return ServiceRegistry()

    def test_registry_initialization(self, registry):
        """Test registry initializes with empty dictionaries"""
        assert registry._crm_clients == {}
        assert registry._platform_clients == {}
        assert registry._initialized is False

    def test_register_crm_client(self, registry):
        """Test registering CRM client"""
        mock_client = Mock()
        registry.register_crm_client(ServiceEnvironment.PRODUCTION, mock_client)

        assert ServiceEnvironment.PRODUCTION in registry._crm_clients
        assert registry._crm_clients[ServiceEnvironment.PRODUCTION] == mock_client

    def test_register_platform_client(self, registry):
        """Test registering Platform client"""
        mock_client = Mock()
        registry.register_platform_client(ServiceEnvironment.STAGING, mock_client)

        assert ServiceEnvironment.STAGING in registry._platform_clients
        assert registry._platform_clients[ServiceEnvironment.STAGING] == mock_client

    def test_get_crm_client_class_exists(self, registry):
        """Test getting registered CRM client class"""
        mock_client = Mock()
        registry.register_crm_client(ServiceEnvironment.DEVELOPMENT, mock_client)

        result = registry.get_crm_client_class(ServiceEnvironment.DEVELOPMENT)
        assert result == mock_client

    def test_get_crm_client_class_not_registered(self, registry):
        """Test getting unregistered CRM client returns None"""
        result = registry.get_crm_client_class(ServiceEnvironment.PRODUCTION)
        assert result is None

    def test_get_platform_client_class_exists(self, registry):
        """Test getting registered Platform client class"""
        mock_client = Mock()
        registry.register_platform_client(ServiceEnvironment.TESTING, mock_client)

        result = registry.get_platform_client_class(ServiceEnvironment.TESTING)
        assert result == mock_client

    def test_get_platform_client_class_not_registered(self, registry):
        """Test getting unregistered Platform client returns None"""
        result = registry.get_platform_client_class(ServiceEnvironment.STAGING)
        assert result is None

    def test_list_available_services_empty(self, registry):
        """Test listing services when registry is empty"""
        services = registry.list_available_services()

        assert 'crm_clients' in services
        assert 'platform_clients' in services
        assert services['crm_clients'] == []
        assert services['platform_clients'] == []

    def test_list_available_services_populated(self, registry):
        """Test listing services after registration"""
        mock_crm = Mock()
        mock_platform = Mock()

        registry.register_crm_client(ServiceEnvironment.PRODUCTION, mock_crm)
        registry.register_crm_client(ServiceEnvironment.STAGING, mock_crm)
        registry.register_platform_client(ServiceEnvironment.DEVELOPMENT, mock_platform)

        services = registry.list_available_services()
        assert len(services['crm_clients']) == 2
        assert len(services['platform_clients']) == 1

    def test_register_multiple_environments(self, registry):
        """Test registering clients for all environments"""
        mock_crm = Mock()
        mock_platform = Mock()

        for env in ServiceEnvironment:
            registry.register_crm_client(env, mock_crm)
            registry.register_platform_client(env, mock_platform)

        services = registry.list_available_services()
        assert len(services['crm_clients']) == 4
        assert len(services['platform_clients']) == 4


# ========== ServiceFactory Tests ==========

class TestServiceFactory:
    """Test ServiceFactory class"""

    @pytest.fixture
    def mock_settings(self):
        """Create mock ProductionSettings"""
        settings = Mock()
        settings.ENVIRONMENT = "development"
        settings.DEBUG = True
        settings.DRY_RUN_MODE = True
        settings.USE_MOCK_SERVICES = True
        settings.SERVICE_NAME = "test-service"

        # External services mock
        settings.external_services = Mock()
        settings.external_services.CRM_BASE_URL = "https://crm.test.com"
        settings.external_services.CRM_API_KEY = "test_crm_key_12345"
        settings.external_services.CRM_TIMEOUT = 30
        settings.external_services.CRM_MAX_RETRIES = 3
        settings.external_services.PLATFORM_BASE_URL = "https://platform.test.com"
        settings.external_services.PLATFORM_API_KEY = "test_platform_key_12345"
        settings.external_services.PLATFORM_TIMEOUT = 30
        settings.external_services.PLATFORM_MAX_RETRIES = 3

        # Monitoring mock
        settings.monitoring = Mock()
        settings.monitoring.ENABLE_METRICS = True

        return settings

    @pytest.fixture
    def service_factory(self, mock_settings):
        """Create ServiceFactory instance"""
        # Reset global registry before each test
        _service_registry._initialized = False
        _service_registry._crm_clients.clear()
        _service_registry._platform_clients.clear()

        return ServiceFactory(mock_settings)

    def test_factory_initialization(self, service_factory, mock_settings):
        """Test ServiceFactory initialization"""
        assert service_factory.settings == mock_settings
        assert service_factory.environment == ServiceEnvironment.DEVELOPMENT
        assert isinstance(service_factory._service_cache, dict)

    def test_factory_initializes_registry(self, service_factory):
        """Test that factory initializes global registry"""
        assert _service_registry._initialized is True

        # Check all environments are registered
        services = _service_registry.list_available_services()
        assert len(services['crm_clients']) == 4
        assert len(services['platform_clients']) == 4

    def test_factory_environment_parsing(self, mock_settings):
        """Test parsing different environment strings"""
        mock_settings.ENVIRONMENT = "production"
        factory = ServiceFactory(mock_settings)
        assert factory.environment == ServiceEnvironment.PRODUCTION

        mock_settings.ENVIRONMENT = "staging"
        factory = ServiceFactory(mock_settings)
        assert factory.environment == ServiceEnvironment.STAGING

    def test_create_crm_client(self, service_factory):
        """Test creating CRM client"""
        client = service_factory.create_crm_client()

        assert client is not None
        # Verify it's cached
        cache_key = "crm_development"
        assert cache_key in service_factory._service_cache

    def test_create_crm_client_caching(self, service_factory):
        """Test CRM client is cached"""
        client1 = service_factory.create_crm_client()
        client2 = service_factory.create_crm_client()

        assert client1 is client2  # Same instance from cache

    def test_create_crm_client_force_recreate(self, service_factory):
        """Test force recreating CRM client"""
        client1 = service_factory.create_crm_client()
        client2 = service_factory.create_crm_client(force_recreate=True)

        # Should be different instances
        assert client1 is not client2

    def test_create_platform_client(self, service_factory):
        """Test creating Platform client"""
        client = service_factory.create_platform_client()

        assert client is not None
        # Verify it's cached
        cache_key = "platform_development"
        assert cache_key in service_factory._service_cache

    def test_create_platform_client_caching(self, service_factory):
        """Test Platform client is cached"""
        client1 = service_factory.create_platform_client()
        client2 = service_factory.create_platform_client()

        assert client1 is client2  # Same instance from cache

    def test_legacy_settings_adapter_basic_fields(self, service_factory):
        """Test legacy settings adapter creates correct basic fields"""
        adapter = service_factory._create_legacy_settings_adapter()

        assert adapter.ENVIRONMENT == "development"
        assert adapter.DEBUG is True
        assert adapter.DRY_RUN_MODE is True
        assert adapter.DRY_RUN is True  # Alias
        assert adapter.USE_MOCK_SERVICES is True

    def test_legacy_settings_adapter_crm_fields(self, service_factory):
        """Test legacy settings adapter includes CRM fields"""
        adapter = service_factory._create_legacy_settings_adapter()

        assert adapter.CRM_BASE_URL == "https://crm.test.com"
        assert adapter.CRM_API_KEY == "test_crm_key_12345"
        assert adapter.CRM_TIMEOUT == 30
        assert adapter.CRM_MAX_RETRIES == 3

    def test_legacy_settings_adapter_platform_fields(self, service_factory):
        """Test legacy settings adapter includes Platform fields"""
        adapter = service_factory._create_legacy_settings_adapter()

        assert adapter.PLATFORM_BASE_URL == "https://platform.test.com"
        assert adapter.PLATFORM_API_KEY == "test_platform_key_12345"
        assert adapter.PLATFORM_TIMEOUT == 30
        assert adapter.PLATFORM_MAX_RETRIES == 3

    def test_legacy_settings_adapter_monitoring_fields(self, service_factory):
        """Test legacy settings adapter includes monitoring fields"""
        adapter = service_factory._create_legacy_settings_adapter()

        assert adapter.ENABLE_METRICS is True

    @patch('halcytone_content_generator.services.service_factory.logger')
    def test_configure_crm_client_development(self, mock_logger, service_factory):
        """Test configuring CRM client for development"""
        mock_client = Mock()
        mock_client.base_url = "http://localhost:8000"
        mock_client.api_key = "dev_key"

        service_factory._configure_crm_client(mock_client)

        # Should log development configuration
        assert any('development' in str(call) for call in mock_logger.info.call_args_list)

    @patch('halcytone_content_generator.services.service_factory.logger')
    def test_configure_crm_client_production_https(self, mock_logger, mock_settings):
        """Test production CRM client requires HTTPS"""
        mock_settings.ENVIRONMENT = "production"
        factory = ServiceFactory(mock_settings)

        mock_client = Mock()
        mock_client.base_url = "http://crm.prod.com"  # HTTP, not HTTPS
        mock_client.api_key = "prod_key_12345678"

        factory._configure_crm_client(mock_client)

        # Should log error about HTTP
        assert any('HTTPS' in str(call) for call in mock_logger.error.call_args_list)

    @patch('halcytone_content_generator.services.service_factory.logger')
    def test_configure_crm_client_production_short_key(self, mock_logger, mock_settings):
        """Test production CRM client warns about short API key"""
        mock_settings.ENVIRONMENT = "production"
        mock_settings.USE_MOCK_SERVICES = False
        factory = ServiceFactory(mock_settings)

        mock_client = Mock()
        mock_client.base_url = "https://crm.prod.com"
        mock_client.api_key = "short"  # Too short

        factory._configure_crm_client(mock_client)

        # Should warn about short key
        assert any('too short' in str(call) for call in mock_logger.warning.call_args_list)

    @patch('halcytone_content_generator.services.service_factory.logger')
    def test_configure_platform_client_staging(self, mock_logger, mock_settings):
        """Test configuring Platform client for staging"""
        mock_settings.ENVIRONMENT = "staging"
        factory = ServiceFactory(mock_settings)

        mock_client = Mock()
        mock_client.base_url = "https://staging.platform.com"
        mock_client.api_key = "staging_key_12345"

        factory._configure_platform_client(mock_client)

        # Should log staging configuration
        assert any('staging' in str(call) for call in mock_logger.info.call_args_list)

    @pytest.mark.asyncio
    async def test_validate_services_success(self, service_factory):
        """Test validating services - basic validation"""
        results = await service_factory.validate_services()

        assert 'crm' in results
        assert 'platform' in results
        # CRM may fail connection but structure should be there
        assert 'environment' in results['crm']
        assert results['platform']['status'] == 'configured'

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.services.service_factory.EnhancedCRMClient')
    async def test_validate_services_crm_failure(self, mock_crm_class, service_factory):
        """Test validating services - CRM connection fails"""
        mock_crm_instance = AsyncMock()
        mock_crm_instance.base_url = "https://crm.test.com"
        mock_crm_instance.test_connection = AsyncMock(return_value={'connected': False})
        mock_crm_class.return_value = mock_crm_instance

        with patch('halcytone_content_generator.services.service_factory.EnhancedPlatformClient'):
            results = await service_factory.validate_services()

            assert results['crm']['status'] == 'failed'

    @pytest.mark.asyncio
    async def test_validate_services_platform_error(self, service_factory):
        """Test validating services - handles errors gracefully"""
        # Corrupt the cache to force an error
        service_factory._service_cache['platform_test'] = None

        results = await service_factory.validate_services()

        # Should still return results dict with error status
        assert 'crm' in results or 'platform' in results

    def test_get_service_info(self, service_factory):
        """Test getting service configuration info"""
        info = service_factory.get_service_info()

        assert info['environment'] == 'development'
        assert info['dry_run_mode'] is True
        assert info['use_mock_services'] is True
        assert 'available_services' in info
        assert 'cached_clients' in info

    @patch('halcytone_content_generator.services.service_factory.EnhancedCRMClient')
    def test_get_service_info_with_cached_clients(self, mock_crm_class, service_factory):
        """Test service info includes cached client keys"""
        mock_crm_class.return_value = Mock(base_url="test", api_key="test_key_1234567890")

        # Create some clients to populate cache
        service_factory.create_crm_client()

        info = service_factory.get_service_info()
        assert len(info['cached_clients']) > 0

    def test_clear_cache(self, service_factory):
        """Test clearing service cache"""
        service_factory._service_cache['test_key'] = Mock()

        assert len(service_factory._service_cache) > 0

        service_factory.clear_cache()

        assert len(service_factory._service_cache) == 0


# ========== Global Functions Tests ==========

class TestGlobalFunctions:
    """Test global service factory functions"""

    @pytest.fixture(autouse=True)
    def reset_globals(self):
        """Reset global factory before each test"""
        reset_service_factory()
        yield
        reset_service_factory()

    @pytest.fixture
    def mock_settings(self):
        """Create mock ProductionSettings"""
        settings = Mock()
        settings.ENVIRONMENT = "testing"
        settings.DEBUG = True
        settings.DRY_RUN_MODE = True
        settings.USE_MOCK_SERVICES = True
        settings.SERVICE_NAME = "test-service"

        settings.external_services = Mock()
        settings.external_services.CRM_BASE_URL = "https://crm.test.com"
        settings.external_services.CRM_API_KEY = "test_crm_key_12345"
        settings.external_services.CRM_TIMEOUT = 30
        settings.external_services.CRM_MAX_RETRIES = 3
        settings.external_services.PLATFORM_BASE_URL = "https://platform.test.com"
        settings.external_services.PLATFORM_API_KEY = "test_platform_key_12345"
        settings.external_services.PLATFORM_TIMEOUT = 30
        settings.external_services.PLATFORM_MAX_RETRIES = 3

        settings.monitoring = Mock()
        settings.monitoring.ENABLE_METRICS = True

        return settings

    @pytest.mark.asyncio
    async def test_get_service_factory_with_settings(self, mock_settings):
        """Test getting global factory with settings"""
        factory = await get_service_factory(mock_settings)

        assert factory is not None
        assert factory.environment == ServiceEnvironment.TESTING

    @pytest.mark.asyncio
    async def test_get_service_factory_no_settings_raises(self):
        """Test getting factory without settings raises error"""
        with pytest.raises(ValueError, match="ServiceFactory requires ProductionSettings"):
            await get_service_factory()

    @pytest.mark.asyncio
    async def test_get_service_factory_singleton(self, mock_settings):
        """Test global factory is a singleton"""
        factory1 = await get_service_factory(mock_settings)
        factory2 = await get_service_factory()  # No settings, should return existing

        assert factory1 is factory2

    def test_reset_service_factory(self, mock_settings):
        """Test resetting global factory"""
        import asyncio
        asyncio.run(get_service_factory(mock_settings))

        reset_service_factory()

        # Should raise error because factory was reset
        with pytest.raises(ValueError):
            asyncio.run(get_service_factory())

    @pytest.mark.asyncio
    async def test_create_crm_client_convenience(self, mock_settings):
        """Test convenience function for creating CRM client"""
        client = await create_crm_client(mock_settings)

        assert client is not None

    @pytest.mark.asyncio
    async def test_create_platform_client_convenience(self, mock_settings):
        """Test convenience function for creating Platform client"""
        client = await create_platform_client(mock_settings)

        assert client is not None

    @pytest.mark.asyncio
    async def test_validate_all_services_convenience(self, mock_settings):
        """Test convenience function for validating all services"""
        results = await validate_all_services(mock_settings)

        assert 'crm' in results
        assert 'platform' in results


# ========== Additional Coverage Tests ==========

class TestEdgeCases:
    """Test edge cases and error paths for full coverage"""

    @pytest.fixture
    def mock_settings(self):
        """Create mock ProductionSettings"""
        settings = Mock()
        settings.ENVIRONMENT = "production"
        settings.DEBUG = False
        settings.DRY_RUN_MODE = False
        settings.USE_MOCK_SERVICES = False
        settings.SERVICE_NAME = "prod-service"

        settings.external_services = Mock()
        settings.external_services.CRM_BASE_URL = "http://crm.prod.com"  # HTTP not HTTPS
        settings.external_services.CRM_API_KEY = "short"  # Too short
        settings.external_services.CRM_TIMEOUT = 30
        settings.external_services.CRM_MAX_RETRIES = 3
        settings.external_services.PLATFORM_BASE_URL = "http://platform.prod.com"
        settings.external_services.PLATFORM_API_KEY = "tiny"
        settings.external_services.PLATFORM_TIMEOUT = 30
        settings.external_services.PLATFORM_MAX_RETRIES = 3

        settings.monitoring = Mock()
        settings.monitoring.ENABLE_METRICS = True

        return settings

    @pytest.fixture
    def service_factory(self, mock_settings):
        """Create ServiceFactory instance"""
        _service_registry._initialized = False
        _service_registry._crm_clients.clear()
        _service_registry._platform_clients.clear()
        return ServiceFactory(mock_settings)

    def test_production_crm_validation_errors(self, service_factory):
        """Test production CRM client validation raises errors for invalid config"""
        # HTTP instead of HTTPS and short API key should raise ValueError
        with pytest.raises(ValueError, match="Critical CRM configuration errors"):
            service_factory.create_crm_client()

    def test_production_platform_validation_errors(self, service_factory):
        """Test production Platform client validation raises errors for invalid config"""
        # HTTP instead of HTTPS and short API key should raise ValueError
        with pytest.raises(ValueError, match="Critical Platform configuration errors"):
            service_factory.create_platform_client()

    def test_create_client_with_unregistered_environment(self, mock_settings):
        """Test creating client when no class registered raises ValueError"""
        # Clear registry
        _service_registry._initialized = False
        _service_registry._crm_clients.clear()
        _service_registry._platform_clients.clear()

        # Create factory but don't initialize registry
        mock_settings.ENVIRONMENT = "custom_env"
        factory = ServiceFactory.__new__(ServiceFactory)
        factory.settings = mock_settings
        factory.environment = ServiceEnvironment.DEVELOPMENT
        factory._service_cache = {}
        factory._initialize_registry()

        # Now clear one environment's registration
        del _service_registry._crm_clients[ServiceEnvironment.DEVELOPMENT]

        # Should raise ValueError
        with pytest.raises(ValueError, match="No CRM client registered"):
            factory.create_crm_client()

    def test_get_service_info_structure(self, service_factory):
        """Test service info contains all expected fields"""
        info = service_factory.get_service_info()

        assert 'environment' in info
        assert 'dry_run_mode' in info
        assert 'use_mock_services' in info
        assert 'available_services' in info
        assert 'cached_clients' in info

        # Check available_services structure
        assert 'crm_clients' in info['available_services']
        assert 'platform_clients' in info['available_services']

    def test_clear_cache_multiple_times(self, service_factory):
        """Test clearing cache multiple times is safe"""
        service_factory._service_cache['test1'] = Mock()
        service_factory._service_cache['test2'] = Mock()

        service_factory.clear_cache()
        assert len(service_factory._service_cache) == 0

        # Should be safe to clear again
        service_factory.clear_cache()
        assert len(service_factory._service_cache) == 0
