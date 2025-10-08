"""
Configuration Management Package
Provides enhanced configuration with secrets management and validation
"""

# Import base Settings first by directly loading the config module to avoid circular import
import sys
import os
from pathlib import Path

# Add parent directory to path to import config.py directly
parent_dir = Path(__file__).parent.parent
config_module_path = parent_dir / "config.py"

# Import Settings and get_settings from the config.py file (not the package)
import importlib.util
spec = importlib.util.spec_from_file_location("base_config", config_module_path)
base_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_config)

Settings = base_config.Settings
get_settings = base_config.get_settings

# Now import the enhanced config modules
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