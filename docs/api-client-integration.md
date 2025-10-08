# API Client Integration

## Overview

Added comprehensive Python API client library for the Content Generator service, providing a modern, type-safe interface for interacting with all API endpoints.

## Files Created

### Core Library
- `src/halcytone_content_generator/lib/__init__.py` - Package initialization
- `src/halcytone_content_generator/lib/base_client.py` - Base API client with retry logic, error handling, and logging

### Specialized Clients
- `src/halcytone_content_generator/lib/api/__init__.py` - API clients package
- `src/halcytone_content_generator/lib/api/content_generator.py` - Content Generator specialized client
- `src/halcytone_content_generator/lib/api/examples.py` - Complete usage examples
- `src/halcytone_content_generator/lib/api/README.md` - Comprehensive documentation

### Tests
- `tests/unit/test_api_client.py` - 22 unit tests (all passing ✅)

## Features

### Base API Client (`APIClient`)
- ✅ **Async/await support** - Modern Python async patterns
- ✅ **Automatic retry** - Exponential backoff on failures
- ✅ **Error handling** - Structured `APIError` exceptions
- ✅ **Logging** - Request/response logging
- ✅ **Timeout management** - Configurable per-request timeouts
- ✅ **Authentication** - Bearer token support
- ✅ **Correlation IDs** - Request tracking across services
- ✅ **Custom headers** - Flexible header management

### Content Generator Client (`ContentGeneratorClient`)

Specialized client extending base client with domain-specific methods:

#### Health & Monitoring
- `health_check()` - API health status
- `readiness_check()` - Readiness probe
- `startup_probe()` - Startup status
- `metrics()` - API metrics

#### Content Generation (V1 API)
- `generate_content()` - Generate and publish content
- `preview_content()` - Preview without publishing

#### Content Synchronization (V2 API)
- `sync_content()` - Multi-channel content sync
- `get_sync_job()` - Job status tracking
- `list_sync_jobs()` - List all sync jobs
- `cancel_sync_job()` - Cancel pending job

#### Content Validation
- `validate_content()` - Validate content structure

#### Cache Management
- `invalidate_cache()` - Invalidate cache entries
- `get_cache_stats()` - Cache statistics
- `clear_all_caches()` - Clear all caches

#### Batch Operations
- `batch_generate()` - Batch content generation

#### Analytics & Reporting
- `get_content_analytics()` - Content performance metrics
- `get_email_analytics()` - Email campaign metrics

#### Configuration
- `get_config()` - Get configuration
- `update_config()` - Update configuration

#### Utilities
- `generate_correlation_id()` - Generate correlation ID
- `test_connection()` - Test API connectivity

## Usage Examples

### Basic Usage

```python
from halcytone_content_generator.lib.api.content_generator import ContentGeneratorClient

async def main():
    # Initialize client
    client = ContentGeneratorClient(
        base_url="https://api.example.com",
        api_key="your-api-key"
    )

    # Check health
    health = await client.health_check()
    print(health.data)

    # Generate content
    response = await client.generate_content(
        send_email=True,
        publish_web=True,
        document_id="gdocs:doc-id"
    )
```

### Multi-Channel Sync

```python
# Sync to multiple channels
response = await client.sync_content(
    document_id="gdocs:123",
    channels=["email", "website", "social_twitter"],
    dry_run=False
)

job_id = response.data["job_id"]

# Check job status
status = await client.get_sync_job(job_id)
```

### Content Validation

```python
# Validate before publishing
validation = await client.validate_content(
    content={
        "type": "update",
        "title": "Weekly Update",
        "content": "Content here...",
        "published": True
    },
    strict=True
)

if validation.data["is_valid"]:
    print("✅ Valid!")
```

### Batch Operations

```python
# Generate multiple items
response = await client.batch_generate(
    requests=[
        {"document_id": "gdocs:1", "channels": ["email"]},
        {"document_id": "gdocs:2", "channels": ["website"]},
    ],
    parallel=True
)
```

### Error Handling

```python
from halcytone_content_generator.lib import APIError

try:
    await client.generate_content(send_email=True)
except APIError as e:
    if e.status_code == 401:
        print("Authentication failed")
    elif e.status_code >= 500:
        print("Server error")
```

## Import Patterns

```python
# Base client and core types
from halcytone_content_generator.lib import APIClient, APIError, APIResponse

# Specialized Content Generator client
from halcytone_content_generator.lib.api.content_generator import ContentGeneratorClient
```

## Configuration

### Environment Variables

```bash
export CONTENT_GENERATOR_API_URL="https://api.example.com"
export CONTENT_GENERATOR_API_KEY="your-api-key"
export CONTENT_GENERATOR_TIMEOUT="60"
export CONTENT_GENERATOR_MAX_RETRIES="3"
```

### Initialize from Config

```python
import os

client = ContentGeneratorClient(
    base_url=os.getenv("CONTENT_GENERATOR_API_URL"),
    api_key=os.getenv("CONTENT_GENERATOR_API_KEY"),
    timeout=float(os.getenv("CONTENT_GENERATOR_TIMEOUT", "60")),
    max_retries=int(os.getenv("CONTENT_GENERATOR_MAX_RETRIES", "3"))
)
```

## Testing

All API client code is fully tested:

```bash
# Run API client tests
pytest tests/unit/test_api_client.py -v

# Results: 22 tests passed ✅
```

## Documentation

Complete documentation available in:
- `src/halcytone_content_generator/lib/api/README.md` - Full API reference
- `src/halcytone_content_generator/lib/api/examples.py` - 11 complete examples

## Architecture

```
src/halcytone_content_generator/lib/
├── __init__.py                    # Package exports
├── base_client.py                 # Base APIClient class
└── api/
    ├── __init__.py                # API clients package
    ├── content_generator.py       # ContentGeneratorClient
    ├── examples.py                # Usage examples
    └── README.md                  # Documentation
```

## Benefits

1. **Type Safety** - Structured request/response types
2. **Reliability** - Automatic retries and error handling
3. **Observability** - Built-in logging and correlation IDs
4. **Developer Experience** - Clear, intuitive API
5. **Testability** - Fully tested with mocks
6. **Extensibility** - Easy to add new clients
7. **Documentation** - Comprehensive docs and examples

## Next Steps

Consider adding:
- [ ] Response caching for GET requests
- [ ] Rate limiting client-side
- [ ] Webhook event listeners
- [ ] Streaming response support
- [ ] CLI tool using the client library
- [ ] Additional specialized clients (Analytics, Monitoring, etc.)

## Related Documentation

- [API Reference](../README.md) - Main API documentation
- [Content Sync](./content-sync.md) - Content synchronization guide
- [Testing Guide](./testing.md) - Testing strategies
