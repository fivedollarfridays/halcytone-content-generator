# Content Generator API Client

Python API client library for interacting with the Content Generator API.

## Features

- ✅ Type-safe async/await API
- ✅ Automatic retry with exponential backoff
- ✅ Correlation ID tracking
- ✅ Structured error handling
- ✅ Request/response logging
- ✅ Timeout management
- ✅ Authentication support

## Installation

The API client is part of the `halcytone_content_generator` package:

```python
from halcytone_content_generator.lib.api import ContentGeneratorClient
```

## Quick Start

### Basic Usage

```python
import asyncio
from halcytone_content_generator.lib.api import ContentGeneratorClient

async def main():
    # Initialize client
    client = ContentGeneratorClient(
        base_url="https://api.example.com",
        api_key="your-api-key",
        timeout=60.0
    )

    # Check health
    health = await client.health_check()
    print(f"Status: {health.data}")

    # Generate content
    response = await client.generate_content(
        send_email=True,
        publish_web=True,
        document_id="gdocs:your-doc-id"
    )

    if response.is_success():
        print("Content generated successfully!")
        print(response.json())
    else:
        print(f"Error: {response.error}")

asyncio.run(main())
```

### Content Synchronization (V2 API)

```python
from datetime import datetime, timedelta

async def sync_example():
    client = ContentGeneratorClient(base_url="https://api.example.com")

    # Sync content to multiple channels
    response = await client.sync_content(
        document_id="gdocs:123abc",
        channels=["email", "website", "social_twitter"],
        dry_run=False
    )

    job_id = response.data["job_id"]
    print(f"Sync job created: {job_id}")

    # Check job status
    status = await client.get_sync_job(job_id)
    print(f"Job status: {status.data['status']}")

    # Schedule for future
    future_time = datetime.now() + timedelta(days=1)
    scheduled = await client.sync_content(
        document_id="gdocs:456def",
        channels=["email"],
        schedule_time=future_time
    )
    print(f"Scheduled for: {future_time}")
```

### Content Validation

```python
async def validate_example():
    client = ContentGeneratorClient(base_url="https://api.example.com")

    content_data = {
        "type": "update",
        "title": "Weekly Progress Update",
        "content": "This week we completed...",
        "published": True,
        "tags": ["progress", "weekly"]
    }

    # Validate content structure
    validation = await client.validate_content(
        content=content_data,
        content_type="update",
        strict=True
    )

    if validation.data["is_valid"]:
        print("Content is valid!")
    else:
        print(f"Validation issues: {validation.data['issues']}")
```

### Batch Operations

```python
async def batch_example():
    client = ContentGeneratorClient(base_url="https://api.example.com")

    # Generate multiple content items
    batch_requests = [
        {
            "document_id": "gdocs:doc1",
            "channels": ["email"]
        },
        {
            "document_id": "gdocs:doc2",
            "channels": ["website", "social_linkedin"]
        },
        {
            "document_id": "notion:page3",
            "channels": ["email", "website"]
        }
    ]

    response = await client.batch_generate(
        requests=batch_requests,
        parallel=True,
        fail_fast=False
    )

    results = response.data["results"]
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
```

### Cache Management

```python
async def cache_example():
    client = ContentGeneratorClient(base_url="https://api.example.com")

    # Invalidate specific cache keys
    await client.invalidate_cache(
        cache_keys=["content:123", "content:456"]
    )

    # Invalidate by pattern
    await client.invalidate_cache(
        pattern="content:*"
    )

    # Invalidate by tags
    await client.invalidate_cache(
        tags=["blog", "update"]
    )

    # Get cache statistics
    stats = await client.get_cache_stats()
    print(f"Cache hit rate: {stats.data['hit_rate']}")
```

### Analytics & Reporting

```python
from datetime import datetime, timedelta

async def analytics_example():
    client = ContentGeneratorClient(base_url="https://api.example.com")

    # Get content analytics
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    analytics = await client.get_content_analytics(
        start_date=start_date,
        end_date=end_date,
        channels=["email", "website"]
    )

    print(f"Views: {analytics.data['total_views']}")
    print(f"Engagement: {analytics.data['engagement_rate']}")

    # Get email analytics
    email_stats = await client.get_email_analytics(
        campaign_id="campaign-123"
    )

    print(f"Open rate: {email_stats.data['open_rate']}")
    print(f"Click rate: {email_stats.data['click_rate']}")
```

## Error Handling

```python
from halcytone_content_generator.lib.api import APIError

async def error_handling_example():
    client = ContentGeneratorClient(base_url="https://api.example.com")

    try:
        response = await client.generate_content(send_email=True)

    except APIError as e:
        print(f"API Error: {e.message}")
        print(f"Status Code: {e.status_code}")
        print(f"Response: {e.response}")

        # Handle specific errors
        if e.status_code == 401:
            print("Authentication failed")
        elif e.status_code == 429:
            print("Rate limit exceeded")
        elif e.status_code >= 500:
            print("Server error - retry later")
```

## Correlation IDs

Use correlation IDs to track requests across services:

```python
async def correlation_example():
    client = ContentGeneratorClient(base_url="https://api.example.com")

    # Generate correlation ID
    correlation_id = client.generate_correlation_id()
    print(f"Tracking request: {correlation_id}")

    # Use across multiple requests
    await client.generate_content(
        send_email=True,
        correlation_id=correlation_id
    )

    await client.get_content_analytics(
        correlation_id=correlation_id
    )

    # Check logs with correlation ID to trace the full request flow
```

## Configuration

### Environment Variables

```bash
export CONTENT_GENERATOR_API_URL="https://api.example.com"
export CONTENT_GENERATOR_API_KEY="your-api-key"
export CONTENT_GENERATOR_TIMEOUT="60"
export CONTENT_GENERATOR_MAX_RETRIES="3"
```

### Load from Config

```python
import os

client = ContentGeneratorClient(
    base_url=os.getenv("CONTENT_GENERATOR_API_URL"),
    api_key=os.getenv("CONTENT_GENERATOR_API_KEY"),
    timeout=float(os.getenv("CONTENT_GENERATOR_TIMEOUT", "60")),
    max_retries=int(os.getenv("CONTENT_GENERATOR_MAX_RETRIES", "3"))
)
```

## Advanced Usage

### Custom Headers

```python
client = ContentGeneratorClient(
    base_url="https://api.example.com",
    headers={
        "X-Custom-Header": "value",
        "X-Client-Version": "1.0.0"
    }
)
```

### Per-Request Timeout

```python
# Override default timeout for specific requests
response = await client.batch_generate(
    requests=large_batch,
    timeout=300.0  # 5 minutes for large batch
)
```

### Connection Testing

```python
async def test_connection():
    client = ContentGeneratorClient(base_url="https://api.example.com")

    if await client.test_connection():
        print("✅ API connection successful")
    else:
        print("❌ API connection failed")
```

## API Reference

### ContentGeneratorClient Methods

#### Health & Status
- `health_check()` - Check API health
- `readiness_check()` - Check if API is ready
- `startup_probe()` - Check startup status
- `metrics()` - Get API metrics

#### Content Generation (V1)
- `generate_content()` - Generate and publish content
- `preview_content()` - Preview content without publishing

#### Content Synchronization (V2)
- `sync_content()` - Sync content across channels
- `get_sync_job()` - Get sync job status
- `list_sync_jobs()` - List all sync jobs
- `cancel_sync_job()` - Cancel a pending job

#### Content Validation
- `validate_content()` - Validate content structure

#### Cache Management
- `invalidate_cache()` - Invalidate cache entries
- `get_cache_stats()` - Get cache statistics
- `clear_all_caches()` - Clear all caches

#### Batch Operations
- `batch_generate()` - Generate multiple content items

#### Analytics & Reporting
- `get_content_analytics()` - Get content performance data
- `get_email_analytics()` - Get email campaign metrics

#### Configuration
- `get_config()` - Get current configuration
- `update_config()` - Update configuration

#### Helpers
- `generate_correlation_id()` - Generate correlation ID
- `test_connection()` - Test API connectivity

## Testing

```python
import pytest
from halcytone_content_generator.lib.api import ContentGeneratorClient

@pytest.mark.asyncio
async def test_client():
    client = ContentGeneratorClient(base_url="http://localhost:8000")

    health = await client.health_check()
    assert health.is_success()
    assert health.data["status"] == "healthy"
```

## Best Practices

1. **Use Correlation IDs**: Track requests across services for better debugging
2. **Handle Errors Gracefully**: Always wrap API calls in try/except
3. **Set Appropriate Timeouts**: Use longer timeouts for batch operations
4. **Respect Rate Limits**: Implement backoff when receiving 429 errors
5. **Use Dry Run**: Test with `dry_run=True` before production runs
6. **Monitor Performance**: Use the metrics endpoint to track API performance
7. **Cache Wisely**: Invalidate caches when content changes

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/halcytone-content-generator/issues
- Documentation: https://docs.example.com/content-generator
