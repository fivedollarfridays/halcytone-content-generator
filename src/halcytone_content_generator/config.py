"""
Configuration management for Halcytone Content Generator
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Service Configuration
    SERVICE_NAME: str = "content-generator"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    TEST_MODE: bool = False  # Add test_mode field

    # API Configuration
    API_KEY: str = ""  # This service's API key for authentication
    API_PREFIX: str = "/api/v1"

    # External Services
    CRM_BASE_URL: str = "http://localhost:8001"
    CRM_API_KEY: str = ""  # For calling CRM service
    PLATFORM_BASE_URL: str = "http://localhost:8000"
    PLATFORM_API_KEY: str = ""  # For calling Platform API

    # Content Source Configuration
    LIVING_DOC_TYPE: str = "google_docs"  # Options: google_docs, notion, internal
    LIVING_DOC_ID: str = ""
    GOOGLE_DOCS_API_KEY: Optional[str] = None
    GOOGLE_CREDENTIALS_JSON: Optional[str] = None
    NOTION_API_KEY: Optional[str] = None
    NOTION_DATABASE_ID: Optional[str] = None

    # Optional AI Services
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    # Email Configuration
    EMAIL_BATCH_SIZE: int = 100
    EMAIL_RATE_LIMIT: int = 10  # emails per second

    # Content Generation Settings
    NEWSLETTER_TEMPLATE: str = "default"
    WEB_UPDATE_TEMPLATE: str = "default"
    SOCIAL_PLATFORMS: list[str] = ["twitter", "linkedin"]

    # Monitoring & Observability
    CORRELATION_ID_HEADER: str = "X-Correlation-ID"
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    # Circuit Breaker Settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60  # seconds
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: str = "httpx.RequestError"

    # Retry Settings
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: float = 2.0
    RETRY_MAX_WAIT: int = 60  # seconds

    # Cache Settings
    CACHE_TTL: int = 300  # seconds
    ENABLE_CACHE: bool = True

    # Dry Run Settings
    DRY_RUN: bool = False  # Global dry run mode for all operations
    BATCH_DRY_RUN: bool = False  # Specific dry run for batch operations

    # Batch Processing Settings
    BATCH_MAX_ITEMS: int = 50  # Maximum items per batch
    BATCH_MAX_DAYS: int = 30  # Maximum days to generate content for
    BATCH_DEFAULT_PERIOD: str = "week"  # Default batch period
    BATCH_ENABLE_SCHEDULING: bool = True  # Enable scheduled batch generation

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()