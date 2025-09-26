"""
Test Service Switching Functionality
Validates that services correctly switch between mock and production endpoints based on environment
"""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import patch, MagicMock

from src.halcytone_content_generator.config.enhanced_config import ProductionSettings, ConfigurationManager
from src.halcytone_content_generator.services.service_factory import ServiceFactory, ServiceEnvironment
from src.halcytone_content_generator.core.services import ServiceContainer, get_service_container, reset_service_container


class TestServiceSwitching:
    """Test service switching between environments"""

    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Setup and cleanup for each test"""
        # Reset service container before each test
        reset_service_container()
        yield
        # Cleanup after each test
        reset_service_container()

    def create_test_settings(self, environment: str, use_mock_services: bool = False) -> ProductionSettings:
        """Create test production settings"""
        # Create security config
        from src.halcytone_content_generator.config.enhanced_config import SecurityConfig
        security_config = SecurityConfig(
            API_KEY_ENCRYPTION_KEY="test-encryption-key-32-chars-long-1234",
            JWT_SECRET_KEY="test-jwt-secret-key-32-chars-long-abcd",
            API_KEY="test-api-key-16-chars"
        )

        # Create external services config
        from src.halcytone_content_generator.config.enhanced_config import ExternalServicesConfig
        if environment == 'production':
            external_services_config = ExternalServicesConfig(
                CRM_BASE_URL="https://production-crm.halcytone.com",
                CRM_API_KEY="prod-crm-api-key-12345",
                PLATFORM_BASE_URL="https://production-platform.halcytone.com",
                PLATFORM_API_KEY="prod-platform-api-key-12345"
            )
        else:
            external_services_config = ExternalServicesConfig(
                CRM_BASE_URL="https://staging-crm.halcytone.com",
                CRM_API_KEY="staging-crm-api-key-12345",
                PLATFORM_BASE_URL="https://staging-platform.halcytone.com",
                PLATFORM_API_KEY="staging-platform-api-key-12345"
            )

        return ProductionSettings(
            ENVIRONMENT=environment,
            USE_MOCK_SERVICES=use_mock_services,
            DRY_RUN_MODE=use_mock_services,
            security=security_config,
            external_services=external_services_config
        )

    @pytest.mark.asyncio
    async def test_development_environment_uses_mock_services(self):
        """Test that development environment uses mock services by default"""
        settings = self.create_test_settings("development", use_mock_services=True)
        factory = ServiceFactory(settings)

        # Create CRM client
        crm_client = factory.create_crm_client()
        assert crm_client.base_url == "http://localhost:8001"
        assert crm_client.api_key == "mock-crm-api-key"
        assert crm_client.environment == "development"

        # Create Platform client
        platform_client = factory.create_platform_client()
        assert platform_client.base_url == "http://localhost:8002"
        assert platform_client.api_key == "mock-platform-api-key"
        assert platform_client.environment == "development"

    @pytest.mark.asyncio
    async def test_production_environment_uses_real_services(self):
        """Test that production environment uses real service endpoints"""
        settings = self.create_test_settings("production", use_mock_services=False)
        factory = ServiceFactory(settings)

        # Create CRM client
        crm_client = factory.create_crm_client()
        assert crm_client.base_url == "https://production-crm.halcytone.com"
        assert crm_client.api_key == "prod-crm-api-key-12345"
        assert crm_client.environment == "production"

        # Create Platform client
        platform_client = factory.create_platform_client()
        assert platform_client.base_url == "https://production-platform.halcytone.com"
        assert platform_client.api_key == "prod-platform-api-key-12345"
        assert platform_client.environment == "production"

    @pytest.mark.asyncio
    async def test_staging_environment_uses_staging_services(self):
        """Test that staging environment uses staging service endpoints"""
        settings = self.create_test_settings("staging", use_mock_services=False)
        factory = ServiceFactory(settings)

        # Create CRM client
        crm_client = factory.create_crm_client()
        assert crm_client.base_url == "https://staging-crm.halcytone.com"
        assert crm_client.api_key == "staging-crm-api-key-12345"
        assert crm_client.environment == "staging"

        # Create Platform client
        platform_client = factory.create_platform_client()
        assert platform_client.base_url == "https://staging-platform.halcytone.com"
        assert platform_client.api_key == "staging-platform-api-key-12345"
        assert platform_client.environment == "staging"

    @pytest.mark.asyncio
    async def test_force_mock_services_override(self):
        """Test that USE_MOCK_SERVICES=True overrides environment-based selection"""
        settings = self.create_test_settings("production", use_mock_services=True)
        factory = ServiceFactory(settings)

        # Even in production, should use mock services when forced
        crm_client = factory.create_crm_client()
        assert crm_client.base_url == "http://localhost:8001"
        assert crm_client.api_key == "mock-crm-api-key"

        platform_client = factory.create_platform_client()
        assert platform_client.base_url == "http://localhost:8002"
        assert platform_client.api_key == "mock-platform-api-key"

    @pytest.mark.asyncio
    async def test_service_container_integration(self):
        """Test service container properly configures publishers"""
        settings = self.create_test_settings("staging", use_mock_services=False)
        container = ServiceContainer(settings)

        # Get publishers
        publishers = await container.get_publishers()

        assert "email" in publishers
        assert "web" in publishers
        assert "social" in publishers

        # Verify publishers are configured with correct endpoints
        # Note: Publishers use the config dict format, so they should have the right URLs
        assert publishers["email"].config["crm_base_url"] == "https://staging-crm.halcytone.com"
        assert publishers["email"].config["platform_base_url"] == "https://staging-platform.halcytone.com"

    @pytest.mark.asyncio
    async def test_service_validation(self):
        """Test service validation functionality"""
        settings = self.create_test_settings("development", use_mock_services=True)
        factory = ServiceFactory(settings)

        # Mock the test_connection method to avoid actual network calls
        with patch('src.halcytone_content_generator.services.crm_client_v2.EnhancedCRMClient.test_connection') as mock_crm_test:
            mock_crm_test.return_value = {
                'connected': True,
                'service': 'Mock CRM',
                'version': '1.0.0'
            }

            validation_results = await factory.validate_services()

            assert 'crm' in validation_results
            assert 'platform' in validation_results
            assert validation_results['crm']['status'] == 'connected'
            assert validation_results['crm']['environment'] == 'development'

    @pytest.mark.asyncio
    async def test_production_config_validation_errors(self):
        """Test that production configuration validation catches common errors"""
        # Test with localhost URLs in production (should fail)
        from src.halcytone_content_generator.config.enhanced_config import SecurityConfig, ExternalServicesConfig

        security_config = SecurityConfig(
            API_KEY_ENCRYPTION_KEY="test-encryption-key-32-chars-long-1234",
            JWT_SECRET_KEY="test-jwt-secret-key-32-chars-long-abcd",
            API_KEY="test-api-key-16-chars"
        )

        # Bad production config with localhost URLs
        bad_external_services_config = ExternalServicesConfig(
            CRM_BASE_URL="http://localhost:8001",  # Should fail in production
            CRM_API_KEY="mock-crm-key",  # Should fail - contains 'mock'
            PLATFORM_BASE_URL="http://localhost:8002",  # Should fail in production
            PLATFORM_API_KEY="test-platform-key"  # Should fail - contains 'test'
        )

        with pytest.raises(ValueError, match="Critical.*configuration errors"):
            ProductionSettings(
                ENVIRONMENT="production",
                USE_MOCK_SERVICES=False,
                DRY_RUN_MODE=False,
                security=security_config,
                external_services=bad_external_services_config
            )

    @pytest.mark.asyncio
    async def test_environment_specific_dry_run_behavior(self):
        """Test that dry run behavior is environment-specific"""
        # Development with dry run should use mocks
        dev_settings = self.create_test_settings("development", use_mock_services=False)
        dev_settings.DRY_RUN_MODE = True

        dev_factory = ServiceFactory(dev_settings)
        dev_crm_client = dev_factory.create_crm_client()

        # In development with dry run, should use mock services
        assert dev_crm_client.base_url == "http://localhost:8001"

        # Production with dry run should still use production endpoints
        prod_settings = self.create_test_settings("production", use_mock_services=False)
        prod_settings.DRY_RUN_MODE = True

        prod_factory = ServiceFactory(prod_settings)
        prod_crm_client = prod_factory.create_crm_client()

        # In production with dry run, should still use production endpoints
        assert prod_crm_client.base_url == "https://production-crm.halcytone.com"

    @pytest.mark.asyncio
    async def test_service_caching(self):
        """Test that services are properly cached and reused"""
        settings = self.create_test_settings("staging", use_mock_services=False)
        factory = ServiceFactory(settings)

        # Create clients multiple times
        crm_client1 = factory.create_crm_client()
        crm_client2 = factory.create_crm_client()

        # Should be the same instance due to caching
        assert crm_client1 is crm_client2

        # Force recreate should create new instance
        crm_client3 = factory.create_crm_client(force_recreate=True)
        assert crm_client1 is not crm_client3

    @pytest.mark.asyncio
    async def test_get_service_info(self):
        """Test service information retrieval"""
        settings = self.create_test_settings("production", use_mock_services=False)
        factory = ServiceFactory(settings)

        service_info = factory.get_service_info()

        assert service_info["environment"] == "production"
        assert service_info["dry_run_mode"] == False
        assert service_info["use_mock_services"] == False
        assert "available_services" in service_info
        assert "cached_clients" in service_info


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])