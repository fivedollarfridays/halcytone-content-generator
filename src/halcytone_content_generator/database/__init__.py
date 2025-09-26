"""
Database Package for Halcytone Content Generator
Provides database connectivity, models, and migration management
"""

from .connection import (
    DatabaseConnection,
    get_database,
    get_session,
    init_database,
    close_database,
    DatabaseSessionManager
)

from .models import Base, metadata

from .config import (
    DatabaseSettings,
    get_database_settings,
    DatabaseType
)

__all__ = [
    # Connection management
    'DatabaseConnection',
    'get_database',
    'get_session',
    'init_database',
    'close_database',
    'DatabaseSessionManager',

    # Models
    'Base',
    'metadata',

    # Configuration
    'DatabaseSettings',
    'get_database_settings',
    'DatabaseType',
]