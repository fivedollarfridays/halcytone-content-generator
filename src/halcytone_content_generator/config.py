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
    CORS_ORIGINS: str = "*"  # Comma-separated list of allowed origins

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

    # AI Services Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    # Security Configuration
    API_KEY_ENCRYPTION_KEY: str = "dev-encryption-key-replace-in-production"
    JWT_SECRET_KEY: str = "dev-jwt-secret-replace-in-production"
    AI_TEMPERATURE: float = 0.7  # Creativity level (0.0-1.0)
    AI_MAX_TOKENS: int = 1500  # Maximum response length
    AI_ENABLE_ENHANCEMENT: bool = True  # Enable AI content enhancement
    AI_ENABLE_QUALITY_SCORING: bool = True  # Enable AI quality scoring
    AI_ENABLE_PERSONALIZATION: bool = True  # Enable AI personalization
    AI_ENABLE_AB_TESTING: bool = False  # Enable A/B testing variations
    AI_DEFAULT_VARIATIONS: int = 3  # Default number of A/B test variations

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
    DRY_RUN: bool = False  # Global dry run mode for all operations (legacy)
    DRY_RUN_MODE: bool = False  # New dry run mode flag
    USE_MOCK_SERVICES: bool = False  # Use mock services instead of real APIs
    BATCH_DRY_RUN: bool = False  # Specific dry run for batch operations

    # Batch Processing Settings
    BATCH_MAX_ITEMS: int = 50  # Maximum items per batch
    BATCH_MAX_DAYS: int = 30  # Maximum days to generate content for
    BATCH_DEFAULT_PERIOD: str = "week"  # Default batch period
    BATCH_ENABLE_SCHEDULING: bool = True  # Enable scheduled batch generation

    # User Segmentation Settings
    USER_SEGMENTS_ENABLED: bool = True
    DEFAULT_SEGMENT: str = "general"
    SEGMENT_PERSONALIZATION: bool = True

    # Tone Management Settings (Sprint 4: Ecosystem Integration)
    TONE_SYSTEM_ENABLED: bool = True
    DEFAULT_TONE: str = "encouraging"  # professional, encouraging, medical_scientific
    TONE_AUTO_SELECTION: bool = True  # Enable automatic tone selection based on content type
    TONE_VALIDATION_ENABLED: bool = True  # Enable brand consistency validation
    TONE_FALLBACK_ENABLED: bool = True  # Enable fallback to default tone if selection fails

    # Per-channel tone preferences
    TONE_EMAIL_DEFAULT: str = "encouraging"
    TONE_WEB_DEFAULT: str = "professional"
    TONE_SOCIAL_DEFAULT: str = "encouraging"
    TONE_BLOG_DEFAULT: str = "professional"
    TONE_RESEARCH_DEFAULT: str = "medical_scientific"

    # Brand consistency settings
    BRAND_VALIDATION_ENABLED: bool = True
    BRAND_VALIDATION_STRICT: bool = False  # Strict mode fails on violations, relaxed mode provides warnings
    BRAND_VALIDATION_SCORE_THRESHOLD: float = 0.7  # Minimum brand alignment score (0.0-1.0)

    # Cache Invalidation Settings (Sprint 4: Ecosystem Integration)
    CACHE_INVALIDATION_ENABLED: bool = True
    CACHE_INVALIDATION_API_KEYS: list[str] = []  # List of valid API keys for cache operations
    CACHE_WEBHOOK_SECRET: str = ""  # Secret for webhook signature verification

    # CDN Configuration
    CDN_ENABLED: bool = False
    CDN_TYPE: str = "cloudflare"  # cloudflare, aws_cloudfront, custom
    CDN_API_KEY: str = ""
    CDN_ZONE_ID: str = ""
    CDN_BASE_URL: str = "https://api.cloudflare.com/client/v4"

    # Cache Targets Configuration
    CACHE_LOCAL_ENABLED: bool = True
    CACHE_API_ENABLED: bool = True
    CACHE_REDIS_ENABLED: bool = False
    CACHE_REDIS_URL: str = "redis://localhost:6379"

    # Cache Management Settings
    CACHE_MAX_HISTORY: int = 1000  # Maximum invalidation history entries to keep
    CACHE_DEFAULT_TTL: int = 3600  # Default cache TTL in seconds (1 hour)
    CACHE_WEBHOOK_TIMEOUT: int = 10  # Webhook timeout in seconds

    # Auto-invalidation triggers
    CACHE_AUTO_INVALIDATE_ON_CONTENT_UPDATE: bool = True
    CACHE_AUTO_INVALIDATE_ON_DEPLOYMENT: bool = True
    CACHE_AUTO_INVALIDATE_PATTERNS: list[str] = ["api/*", "content/*", "assets/*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()