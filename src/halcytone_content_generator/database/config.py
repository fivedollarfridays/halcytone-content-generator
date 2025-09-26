"""
Database Configuration Module
Handles database settings for different environments with production-ready defaults
"""

import os
import logging
from typing import Optional, Dict, Any
from enum import Enum
from urllib.parse import urlparse, parse_qs

from pydantic import BaseSettings, Field, field_validator, SecretStr
from pydantic_settings import SettingsConfigDict

logger = logging.getLogger(__name__)


class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"


class DatabaseSettings(BaseSettings):
    """
    Database configuration settings with environment-specific defaults
    """

    # Database connection URL (primary configuration method)
    DATABASE_URL: Optional[SecretStr] = Field(
        default=None,
        description="Complete database connection URL"
    )

    # Individual connection parameters (fallback if URL not provided)
    DATABASE_TYPE: DatabaseType = Field(
        default=DatabaseType.POSTGRESQL,
        description="Type of database to use"
    )
    DATABASE_HOST: str = Field(
        default="localhost",
        description="Database host address"
    )
    DATABASE_PORT: int = Field(
        default=5432,
        description="Database port"
    )
    DATABASE_NAME: str = Field(
        default="halcytone_content",
        description="Database name"
    )
    DATABASE_USER: str = Field(
        default="halcytone",
        description="Database username"
    )
    DATABASE_PASSWORD: Optional[SecretStr] = Field(
        default=None,
        description="Database password"
    )

    # Connection pool settings
    DATABASE_POOL_SIZE: int = Field(
        default=20,
        description="Maximum number of connections in the pool",
        ge=1,
        le=100
    )
    DATABASE_POOL_MAX_OVERFLOW: int = Field(
        default=10,
        description="Maximum overflow connections above pool_size",
        ge=0,
        le=50
    )
    DATABASE_POOL_TIMEOUT: int = Field(
        default=30,
        description="Seconds to wait before timing out",
        ge=1,
        le=300
    )
    DATABASE_POOL_RECYCLE: int = Field(
        default=3600,
        description="Seconds before connection recycling",
        ge=60,
        le=7200
    )
    DATABASE_POOL_PRE_PING: bool = Field(
        default=True,
        description="Test connections before using them"
    )

    # SSL/TLS settings
    DATABASE_SSL_MODE: str = Field(
        default="prefer",
        pattern="^(disable|allow|prefer|require|verify-ca|verify-full)$",
        description="SSL mode for database connection"
    )
    DATABASE_SSL_CERT: Optional[str] = Field(
        default=None,
        description="Path to SSL certificate file"
    )
    DATABASE_SSL_KEY: Optional[str] = Field(
        default=None,
        description="Path to SSL key file"
    )
    DATABASE_SSL_CA: Optional[str] = Field(
        default=None,
        description="Path to SSL CA certificate file"
    )

    # Performance settings
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Echo SQL statements (debug only)"
    )
    DATABASE_ECHO_POOL: bool = Field(
        default=False,
        description="Echo pool events (debug only)"
    )
    DATABASE_CONNECT_TIMEOUT: int = Field(
        default=10,
        description="Connection timeout in seconds",
        ge=1,
        le=60
    )
    DATABASE_COMMAND_TIMEOUT: int = Field(
        default=30,
        description="Command execution timeout in seconds",
        ge=1,
        le=300
    )

    # Migration settings
    DATABASE_AUTO_MIGRATE: bool = Field(
        default=False,
        description="Automatically run migrations on startup"
    )
    DATABASE_MIGRATION_DIR: str = Field(
        default="migrations",
        description="Directory containing migration files"
    )

    # Read replica settings (for scaling)
    DATABASE_READ_REPLICA_URL: Optional[SecretStr] = Field(
        default=None,
        description="Read replica database URL for read operations"
    )
    DATABASE_USE_READ_REPLICA: bool = Field(
        default=False,
        description="Enable read replica for read operations"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v, info):
        """Validate and sanitize database URL"""
        if v is None:
            return v

        url_str = v.get_secret_value() if hasattr(v, 'get_secret_value') else str(v)

        # Parse URL to validate format
        try:
            parsed = urlparse(url_str)

            # Check for required components
            if not parsed.scheme:
                raise ValueError("Database URL must include scheme (e.g., postgresql://)")

            # Validate scheme
            valid_schemes = [
                'postgresql', 'postgres', 'postgresql+asyncpg',
                'mysql', 'mysql+pymysql', 'mysql+aiomysql',
                'sqlite', 'sqlite+aiosqlite',
                'mongodb', 'mongodb+srv'
            ]

            if not any(parsed.scheme.startswith(s) for s in valid_schemes):
                raise ValueError(f"Unsupported database scheme: {parsed.scheme}")

            # Check for production requirements
            environment = os.getenv('ENVIRONMENT', 'development').lower()
            if environment == 'production':
                # Don't allow SQLite in production
                if parsed.scheme.startswith('sqlite'):
                    raise ValueError("SQLite is not recommended for production use")

                # Require password in production
                if parsed.username and not parsed.password:
                    logger.warning("Database URL has username but no password in production")

        except Exception as e:
            raise ValueError(f"Invalid database URL: {e}")

        return v

    @field_validator('DATABASE_SSL_MODE')
    @classmethod
    def validate_ssl_mode(cls, v, info):
        """Validate SSL mode for production"""
        environment = os.getenv('ENVIRONMENT', 'development').lower()

        if environment == 'production' and v in ['disable', 'allow']:
            logger.warning(
                f"Database SSL mode '{v}' is not recommended for production. "
                "Consider using 'require' or 'verify-full'"
            )

        return v

    @field_validator('DATABASE_POOL_SIZE')
    @classmethod
    def validate_pool_size(cls, v):
        """Validate pool size based on environment"""
        environment = os.getenv('ENVIRONMENT', 'development').lower()

        if environment == 'production' and v < 10:
            logger.warning(
                f"Database pool size {v} may be too small for production. "
                "Consider increasing to at least 10"
            )

        return v

    def get_database_url(self) -> str:
        """
        Get the database URL, building it from components if necessary
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL.get_secret_value()

        # Build URL from components
        if self.DATABASE_TYPE == DatabaseType.SQLITE:
            # SQLite uses a file path
            db_name = self.DATABASE_NAME
            if not db_name.endswith('.db'):
                db_name += '.db'
            return f"sqlite:///{db_name}"

        # Build URL for network databases
        password = self.DATABASE_PASSWORD.get_secret_value() if self.DATABASE_PASSWORD else ''
        auth = f"{self.DATABASE_USER}:{password}@" if self.DATABASE_USER else ""

        scheme = self.DATABASE_TYPE.value
        if self.DATABASE_TYPE == DatabaseType.POSTGRESQL:
            scheme = "postgresql"

        return f"{scheme}://{auth}{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    def get_async_database_url(self) -> str:
        """
        Get async-compatible database URL
        """
        url = self.get_database_url()

        # Convert to async drivers
        replacements = {
            'postgresql://': 'postgresql+asyncpg://',
            'postgres://': 'postgresql+asyncpg://',
            'mysql://': 'mysql+aiomysql://',
            'sqlite://': 'sqlite+aiosqlite://'
        }

        for old, new in replacements.items():
            if url.startswith(old):
                return url.replace(old, new, 1)

        return url

    def get_alembic_url(self) -> str:
        """
        Get database URL for Alembic migrations
        """
        url = self.get_database_url()

        # Alembic prefers specific drivers
        replacements = {
            'postgresql+asyncpg://': 'postgresql://',
            'mysql+aiomysql://': 'mysql://',
            'sqlite+aiosqlite://': 'sqlite://'
        }

        for old, new in replacements.items():
            if url.startswith(old):
                return url.replace(old, new, 1)

        return url

    def get_ssl_args(self) -> Dict[str, Any]:
        """
        Get SSL connection arguments for database
        """
        ssl_args = {}

        if self.DATABASE_SSL_MODE == 'disable':
            return {}

        if self.DATABASE_TYPE == DatabaseType.POSTGRESQL:
            ssl_args['sslmode'] = self.DATABASE_SSL_MODE

            if self.DATABASE_SSL_CERT:
                ssl_args['sslcert'] = self.DATABASE_SSL_CERT
            if self.DATABASE_SSL_KEY:
                ssl_args['sslkey'] = self.DATABASE_SSL_KEY
            if self.DATABASE_SSL_CA:
                ssl_args['sslrootcert'] = self.DATABASE_SSL_CA

        elif self.DATABASE_TYPE == DatabaseType.MYSQL:
            if self.DATABASE_SSL_MODE != 'disable':
                ssl_args['ssl'] = {
                    'ca': self.DATABASE_SSL_CA,
                    'cert': self.DATABASE_SSL_CERT,
                    'key': self.DATABASE_SSL_KEY
                }

        return ssl_args

    def get_pool_args(self) -> Dict[str, Any]:
        """
        Get connection pool arguments
        """
        return {
            'pool_size': self.DATABASE_POOL_SIZE,
            'max_overflow': self.DATABASE_POOL_MAX_OVERFLOW,
            'pool_timeout': self.DATABASE_POOL_TIMEOUT,
            'pool_recycle': self.DATABASE_POOL_RECYCLE,
            'pool_pre_ping': self.DATABASE_POOL_PRE_PING,
            'echo': self.DATABASE_ECHO,
            'echo_pool': self.DATABASE_ECHO_POOL,
            'connect_args': {
                'connect_timeout': self.DATABASE_CONNECT_TIMEOUT,
                'command_timeout': self.DATABASE_COMMAND_TIMEOUT,
                **self.get_ssl_args()
            }
        }

    def validate_production_readiness(self) -> list[str]:
        """
        Validate database configuration for production
        """
        issues = []
        environment = os.getenv('ENVIRONMENT', 'development').lower()

        if environment != 'production':
            return issues

        # Check for required production settings
        if not self.DATABASE_URL and not self.DATABASE_PASSWORD:
            issues.append("Database password is required in production")

        if self.DATABASE_TYPE == DatabaseType.SQLITE:
            issues.append("SQLite is not recommended for production")

        if self.DATABASE_SSL_MODE in ['disable', 'allow']:
            issues.append(f"SSL mode '{self.DATABASE_SSL_MODE}' is insecure for production")

        if self.DATABASE_ECHO or self.DATABASE_ECHO_POOL:
            issues.append("Database echo/logging should be disabled in production")

        if self.DATABASE_POOL_SIZE < 10:
            issues.append("Database pool size should be at least 10 for production")

        if not self.DATABASE_POOL_PRE_PING:
            issues.append("Connection pre-ping should be enabled for production reliability")

        return issues


# Global settings instance
_database_settings: Optional[DatabaseSettings] = None


def get_database_settings(reload: bool = False) -> DatabaseSettings:
    """
    Get database settings singleton

    Args:
        reload: Force reload of settings

    Returns:
        DatabaseSettings instance
    """
    global _database_settings

    if _database_settings is None or reload:
        _database_settings = DatabaseSettings()

        # Log configuration in non-production environments
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        if environment != 'production':
            logger.info(f"Database configuration loaded for {environment}")
            logger.debug(f"Database type: {_database_settings.DATABASE_TYPE}")
            logger.debug(f"Database host: {_database_settings.DATABASE_HOST}")
            logger.debug(f"Pool size: {_database_settings.DATABASE_POOL_SIZE}")

        # Validate production readiness
        issues = _database_settings.validate_production_readiness()
        if issues:
            for issue in issues:
                logger.warning(f"Database configuration issue: {issue}")

    return _database_settings


def reset_database_settings():
    """Reset database settings (for testing)"""
    global _database_settings
    _database_settings = None