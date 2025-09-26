"""
Enhanced Configuration Management with Secrets Integration
Supports environment-specific configuration and secure secrets management
"""

import os
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from pathlib import Path

from .secrets_manager import (
    get_secrets_manager,
    SecretReference,
    SecretsProvider,
    UnifiedSecretsManager
)

logger = logging.getLogger(__name__)


class SecurityConfig(BaseSettings):
    """Security-specific configuration with validation"""

    # Encryption keys - must be strong in production
    API_KEY_ENCRYPTION_KEY: str = Field(..., min_length=32)
    JWT_SECRET_KEY: str = Field(..., min_length=32)

    # API keys for this service
    API_KEY: str = Field(..., min_length=16)

    # Session and cookie security
    SESSION_SECRET_KEY: Optional[str] = None
    SECURE_COOKIES: bool = True
    CSRF_SECRET_KEY: Optional[str] = None

    @field_validator('API_KEY_ENCRYPTION_KEY', 'JWT_SECRET_KEY')
    @classmethod
    def validate_strong_secrets(cls, v, info):
        """Ensure secrets are strong enough for production"""
        field_name = info.field_name

        if len(v) < 32:
            raise ValueError(f'{field_name} must be at least 32 characters long')

        # Check for development placeholder values
        dev_patterns = ['dev-', 'development', 'test-', 'replace-in-production']
        for pattern in dev_patterns:
            if pattern in v.lower():
                if os.getenv('ENVIRONMENT', '').lower() == 'production':
                    raise ValueError(f'{field_name} contains development placeholder in production')
                logger.warning(f'{field_name} appears to contain development placeholder')

        return v


class ExternalServicesConfig(BaseSettings):
    """External service configuration with secrets integration"""

    # CRM Service
    CRM_BASE_URL: str
    CRM_API_KEY: str = Field(..., min_length=8)
    CRM_TIMEOUT: int = 30
    CRM_MAX_RETRIES: int = 3

    # Platform Service
    PLATFORM_BASE_URL: str
    PLATFORM_API_KEY: str = Field(..., min_length=8)
    PLATFORM_TIMEOUT: int = 30
    PLATFORM_MAX_RETRIES: int = 3

    # Content Sources
    LIVING_DOC_TYPE: str = Field(default="google_docs", pattern="^(google_docs|notion|internal)$")
    LIVING_DOC_ID: str = ""

    # Google Services
    GOOGLE_CREDENTIALS_JSON: Optional[str] = None
    GOOGLE_PROJECT_ID: Optional[str] = None

    # Notion Services
    NOTION_API_KEY: Optional[str] = None
    NOTION_DATABASE_ID: Optional[str] = None

    # AI Services
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_TIMEOUT: int = 60


class DatabaseConfig(BaseSettings):
    """Database configuration (if applicable)"""

    DATABASE_URL: Optional[str] = None
    DATABASE_MIN_CONNECTIONS: int = 5
    DATABASE_MAX_CONNECTIONS: int = 20
    DATABASE_TIMEOUT: int = 30
    DATABASE_SSL_MODE: str = "prefer"
    DATABASE_POOL_RECYCLE: int = 3600


class CacheConfig(BaseSettings):
    """Caching configuration"""

    # Basic cache settings
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 300
    CACHE_MAX_SIZE: int = 1000

    # Redis configuration
    CACHE_REDIS_ENABLED: bool = False
    CACHE_REDIS_URL: Optional[str] = None
    CACHE_REDIS_PASSWORD: Optional[str] = None
    CACHE_REDIS_DB: int = 0
    CACHE_REDIS_TIMEOUT: int = 5

    # Local cache settings
    CACHE_LOCAL_ENABLED: bool = True
    CACHE_LOCAL_MAX_SIZE: int = 100


class MonitoringConfig(BaseSettings):
    """Monitoring and observability configuration"""

    # Metrics
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    METRICS_PATH: str = "/metrics"

    # Health checks
    HEALTH_CHECK_TIMEOUT: int = 10
    HEALTH_CHECK_INTERVAL: int = 30

    # Logging
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    LOG_FORMAT: str = Field(default="json", pattern="^(json|text)$")
    LOG_DESTINATION: str = Field(default="stdout", pattern="^(stdout|file|both)$")
    LOG_FILE_PATH: Optional[str] = None
    LOG_MAX_SIZE: str = "100MB"
    LOG_BACKUP_COUNT: int = 5

    # Tracing
    ENABLE_TRACING: bool = False
    JAEGER_ENDPOINT: Optional[str] = None

    # Correlation IDs
    CORRELATION_ID_HEADER: str = "X-Correlation-ID"


class AlertConfig(BaseSettings):
    """Alerting configuration"""

    # Email alerts
    ALERT_EMAIL_ENABLED: bool = False
    ALERT_EMAIL_RECIPIENTS: List[str] = Field(default_factory=list)
    ALERT_EMAIL_SMTP_HOST: Optional[str] = None
    ALERT_EMAIL_SMTP_PORT: int = 587
    ALERT_EMAIL_USERNAME: Optional[str] = None
    ALERT_EMAIL_PASSWORD: Optional[str] = None

    # Slack alerts
    ALERT_SLACK_ENABLED: bool = False
    ALERT_SLACK_WEBHOOK_URL: Optional[str] = None
    ALERT_SLACK_CHANNEL: str = "#alerts"

    # Alert thresholds
    ALERT_ERROR_RATE_THRESHOLD: float = 1.0  # 1%
    ALERT_RESPONSE_TIME_THRESHOLD: int = 1000  # 1 second
    ALERT_MEMORY_THRESHOLD: int = 85  # 85%


class ProductionSettings(BaseSettings):
    """Enhanced production-ready settings with secrets management"""

    # Basic service configuration
    SERVICE_NAME: str = "halcytone-content-generator"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKER_PROCESSES: int = 1
    WORKER_THREADS: int = 10
    WORKER_TIMEOUT: int = 120

    # Security configuration (nested)
    security: SecurityConfig

    # External services configuration (nested)
    external_services: ExternalServicesConfig

    # Database configuration (nested)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # Cache configuration (nested)
    cache: CacheConfig = Field(default_factory=CacheConfig)

    # Monitoring configuration (nested)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    # Alert configuration (nested)
    alerts: AlertConfig = Field(default_factory=AlertConfig)

    # Dry run settings
    DRY_RUN_MODE: bool = False
    USE_MOCK_SERVICES: bool = False

    # Feature flags
    feature_flags: Dict[str, bool] = Field(default_factory=dict)

    # Secrets management configuration
    SECRETS_PROVIDER: str = Field(default="environment", pattern="^(azure_key_vault|aws_secrets_manager|environment|local_file)$")
    SECRETS_FALLBACK_TO_ENV: bool = True

    # Azure Key Vault settings
    AZURE_KEY_VAULT_URL: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None

    # AWS Secrets Manager settings
    AWS_REGION: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_nested_delimiter = "__"  # Allow SECURITY__API_KEY format

    @model_validator(mode='before')
    @classmethod
    def environment_specific_validation(cls, values):
        """Apply environment-specific validation rules"""
        environment = values.get('ENVIRONMENT', 'development').lower()

        if environment == 'production':
            # Production-specific validations
            if values.get('DEBUG', False):
                raise ValueError('DEBUG must be False in production')

            if values.get('DRY_RUN_MODE', False):
                raise ValueError('DRY_RUN_MODE must be False in production')

            if values.get('USE_MOCK_SERVICES', False):
                raise ValueError('USE_MOCK_SERVICES must be False in production')

            # Ensure monitoring is enabled in production
            if not values.get('monitoring', {}).get('ENABLE_METRICS', True):
                logger.warning('Metrics disabled in production - this is not recommended')

        elif environment == 'development':
            # Development-specific settings
            if not values.get('DEBUG', True):
                logger.info('DEBUG disabled in development environment')

        return values

    @field_validator('WORKER_PROCESSES')
    @classmethod
    def validate_worker_processes(cls, v):
        """Validate worker process count"""
        # Get environment from environment variable since we can't access other fields in field validator
        environment = os.getenv('ENVIRONMENT', 'development').lower()

        if environment == 'production' and v < 2:
            logger.warning('Single worker process in production may impact availability')

        if v > 10:
            logger.warning(f'High worker process count ({v}) may impact resource usage')

        return v


class ConfigurationManager:
    """Manages configuration loading with secrets integration"""

    def __init__(self, environment: Optional[str] = None):
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.secrets_manager: Optional[UnifiedSecretsManager] = None
        self._settings: Optional[ProductionSettings] = None

    async def _init_secrets_manager(self, settings_dict: Dict[str, Any]) -> UnifiedSecretsManager:
        """Initialize the appropriate secrets manager"""
        provider_name = settings_dict.get('SECRETS_PROVIDER', 'environment')
        fallback = settings_dict.get('SECRETS_FALLBACK_TO_ENV', True)

        try:
            provider = SecretsProvider(provider_name)
        except ValueError:
            logger.warning(f"Invalid secrets provider '{provider_name}', falling back to environment")
            provider = SecretsProvider.ENVIRONMENT

        return get_secrets_manager(provider, fallback)

    def _load_base_config(self) -> Dict[str, Any]:
        """Load base configuration from environment files"""
        config_data = {}

        # Load environment-specific .env file first
        env_files = [
            f".env.{self.environment}",
            f".env.{self.environment}.local",
            ".env",
            ".env.local"
        ]

        for env_file in env_files:
            if os.path.exists(env_file):
                logger.info(f"Loading configuration from {env_file}")
                # Load using python-dotenv for proper parsing
                from dotenv import dotenv_values
                file_config = dotenv_values(env_file)
                config_data.update(file_config)

        # Override with actual environment variables
        for key, value in os.environ.items():
            config_data[key] = value

        return config_data

    async def _load_secrets(self, settings_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Load secrets and merge with configuration"""
        if not self.secrets_manager:
            self.secrets_manager = await self._init_secrets_manager(settings_dict)

        # Define secrets that should be loaded from secrets manager
        secret_refs = [
            SecretReference("API_KEY_ENCRYPTION_KEY", SecretsProvider(settings_dict.get('SECRETS_PROVIDER', 'environment'))),
            SecretReference("JWT_SECRET_KEY", SecretsProvider(settings_dict.get('SECRETS_PROVIDER', 'environment'))),
            SecretReference("API_KEY", SecretsProvider(settings_dict.get('SECRETS_PROVIDER', 'environment'))),
            SecretReference("CRM_API_KEY", SecretsProvider(settings_dict.get('SECRETS_PROVIDER', 'environment'))),
            SecretReference("PLATFORM_API_KEY", SecretsProvider(settings_dict.get('SECRETS_PROVIDER', 'environment'))),
            SecretReference("OPENAI_API_KEY", SecretsProvider(settings_dict.get('SECRETS_PROVIDER', 'environment')), required=False),
            SecretReference("GOOGLE_CREDENTIALS_JSON", SecretsProvider(settings_dict.get('SECRETS_PROVIDER', 'environment')), required=False),
            SecretReference("NOTION_API_KEY", SecretsProvider(settings_dict.get('SECRETS_PROVIDER', 'environment')), required=False),
        ]

        # Load secrets
        secrets = await self.secrets_manager.get_secrets_batch(secret_refs)

        # Merge secrets into configuration, but don't override existing values
        for key, value in secrets.items():
            if value and key not in settings_dict:
                settings_dict[key] = value

        return settings_dict

    async def load_settings(self) -> ProductionSettings:
        """Load complete settings with secrets integration"""
        if self._settings is not None:
            return self._settings

        # Load base configuration
        config_data = self._load_base_config()

        # Load secrets
        config_data = await self._load_secrets(config_data)

        # Create nested configuration structures
        security_config = {k[9:]: v for k, v in config_data.items() if k.startswith('SECURITY__')}
        if not security_config:
            # Fallback to flat structure
            security_config = {
                'API_KEY_ENCRYPTION_KEY': config_data.get('API_KEY_ENCRYPTION_KEY', ''),
                'JWT_SECRET_KEY': config_data.get('JWT_SECRET_KEY', ''),
                'API_KEY': config_data.get('API_KEY', ''),
            }

        external_services_config = {k[18:]: v for k, v in config_data.items() if k.startswith('EXTERNAL_SERVICES__')}
        if not external_services_config:
            # Fallback to flat structure
            external_services_config = {
                'CRM_BASE_URL': config_data.get('CRM_BASE_URL', ''),
                'CRM_API_KEY': config_data.get('CRM_API_KEY', ''),
                'PLATFORM_BASE_URL': config_data.get('PLATFORM_BASE_URL', ''),
                'PLATFORM_API_KEY': config_data.get('PLATFORM_API_KEY', ''),
                'LIVING_DOC_TYPE': config_data.get('LIVING_DOC_TYPE', 'google_docs'),
                'LIVING_DOC_ID': config_data.get('LIVING_DOC_ID', ''),
                'GOOGLE_CREDENTIALS_JSON': config_data.get('GOOGLE_CREDENTIALS_JSON'),
                'NOTION_API_KEY': config_data.get('NOTION_API_KEY'),
                'NOTION_DATABASE_ID': config_data.get('NOTION_DATABASE_ID'),
                'OPENAI_API_KEY': config_data.get('OPENAI_API_KEY'),
                'OPENAI_MODEL': config_data.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            }

        # Create settings with proper nesting
        try:
            self._settings = ProductionSettings(
                **config_data,
                security=SecurityConfig(**security_config),
                external_services=ExternalServicesConfig(**external_services_config),
            )
        except Exception as e:
            logger.error(f"Failed to create settings: {e}")
            logger.error(f"Security config: {security_config}")
            logger.error(f"External services config: {external_services_config}")
            raise

        logger.info(f"Configuration loaded successfully for environment: {self.environment}")
        return self._settings

    def validate_production_readiness(self, settings: ProductionSettings) -> List[str]:
        """Validate that configuration is ready for production deployment"""
        issues = []

        if settings.ENVIRONMENT != 'production':
            return issues  # Only validate production environments

        # Check required secrets
        if 'dev-' in settings.security.API_KEY_ENCRYPTION_KEY:
            issues.append("API_KEY_ENCRYPTION_KEY contains development placeholder")

        if 'dev-' in settings.security.JWT_SECRET_KEY:
            issues.append("JWT_SECRET_KEY contains development placeholder")

        # Check external service configuration
        if not settings.external_services.CRM_BASE_URL.startswith('https://'):
            issues.append("CRM_BASE_URL must use HTTPS in production")

        if not settings.external_services.PLATFORM_BASE_URL.startswith('https://'):
            issues.append("PLATFORM_BASE_URL must use HTTPS in production")

        # Check security settings
        if settings.DEBUG:
            issues.append("DEBUG must be disabled in production")

        if settings.DRY_RUN_MODE:
            issues.append("DRY_RUN_MODE must be disabled in production")

        if settings.USE_MOCK_SERVICES:
            issues.append("USE_MOCK_SERVICES must be disabled in production")

        # Check monitoring
        if not settings.monitoring.ENABLE_METRICS:
            issues.append("Metrics should be enabled in production")

        return issues


# Global configuration manager
_config_manager: Optional[ConfigurationManager] = None


async def get_production_settings(environment: Optional[str] = None) -> ProductionSettings:
    """Get production settings with secrets integration"""
    global _config_manager

    if _config_manager is None:
        _config_manager = ConfigurationManager(environment)

    return await _config_manager.load_settings()


def reset_config_manager():
    """Reset configuration manager (for testing)"""
    global _config_manager
    _config_manager = None


# Async compatibility function
def get_settings_sync() -> ProductionSettings:
    """Synchronous wrapper for getting settings (compatibility)"""
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(get_production_settings())
    except RuntimeError:
        # If no event loop is running, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(get_production_settings())
        finally:
            loop.close()