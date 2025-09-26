"""
Configuration Management Package
Provides enhanced configuration with secrets management and validation
"""

from .enhanced_config import (
    ProductionSettings,
    ConfigurationManager,
    get_production_settings,
    get_settings_sync,
    reset_config_manager
)

from .secrets_manager import (
    get_secrets_manager,
    SecretsProvider,
    SecretReference,
    UnifiedSecretsManager,
    reset_secrets_manager
)

from .validation import (
    validate_configuration,
    is_production_ready,
    ValidationSeverity,
    ValidationIssue,
    ConfigurationValidator
)

# Import Settings and get_settings from parent module's config.py
# Use absolute import to avoid conflicts
from src.halcytone_content_generator.config import Settings, get_settings

__all__ = [
    # Enhanced configuration
    'ProductionSettings',
    'ConfigurationManager',
    'get_production_settings',
    'get_settings_sync',
    'reset_config_manager',

    # Secrets management
    'get_secrets_manager',
    'SecretsProvider',
    'SecretReference',
    'UnifiedSecretsManager',
    'reset_secrets_manager',

    # Validation
    'validate_configuration',
    'is_production_ready',
    'ValidationSeverity',
    'ValidationIssue',
    'ConfigurationValidator',

    # Legacy compatibility
    'Settings',
    'get_settings',
]