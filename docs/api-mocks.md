# Mock Service API Documentation

## Overview

The Halcytone Content Generator dry run system includes comprehensive mock services that simulate external API behavior without making actual external calls. This documentation covers the Mock CRM Service and Mock Platform Service APIs.

**Version:** Sprint 5 - Documentation & Production Readiness
**Last Updated:** 2025-01-24

---

## Mock CRM Service (Port 8001)

The Mock CRM Service simulates a customer relationship management system, providing email sending, contact management, and campaign functionality.

**Base URL:** `http://localhost:8001`
**Interactive Documentation:** `http://localhost:8001/docs`

### Authentication

Mock CRM Service accepts any API key for development purposes. In production simulation mode, use:
- **Header:** `Authorization: Bearer mock-crm-api-key`
- **Alternative:** `X-API-Key: mock-crm-api-key`

### Common Response Headers

```http
Content-Type: application/json
X-Mock-Service: crm-v1.0.0
X-Request-ID: uuid4-generated-id
```

### Health Check

#### GET /health

Check service health and availability.

**Response:**
```json
{
  "status": "healthy",
  "service": "mock-crm",
  "version": "1.0.0",
  "timestamp": "2025-01-24T16:23:20.655873Z"
}
```

**Response Codes:**
- `200` - Service healthy
- `503` - Service unavailable

### Email Operations

#### POST /api/v1/email/send

Send an email through the mock CRM system.

**Request Body:**
```json
{
  "subject": "Weekly Newsletter",
  "html_content": "<html><body><h1>Hello World</h1></body></html>",
  "text_content": "Hello World",
  "recipients": ["user@example.com", "admin@example.com"],
  "campaign_id": "campaign-123",
  "sender_email": "noreply@halcytone.com",
  "metadata": {
    "source": "content-generator",
    "dry_run": true
  }
}
```

**Response (Success):**
```json
{
  "message_id": "msg_abc123def456",
  "status": "sent",
  "recipients_count": 2,
  "timestamp": "2025-01-24T16:23:20.655873Z",
  "campaign_id": "campaign-123"
}
```

**Response Codes:**
- `200` - Email sent successfully
- `400` - Invalid request format
- `408` - Timeout (when subject contains "timeout")
- `500` - Server error (when subject contains "error")

**Error Simulation:**
The mock service simulates various error conditions based on request content:

| Subject Contains | Behavior | Response Code |
|------------------|----------|---------------|
| "error" | Simulates CRM error | 500 |
| "timeout" | Simulates timeout | 408 |
| "invalid" | Simulates validation error | 400 |
| "slow" | 2-second delay | 200 (delayed) |

#### GET /api/v1/email/{message_id}/status

Get the delivery status of a sent email.

**Path Parameters:**
- `message_id` (string): The message ID returned from email send

**Response:**
```json
{
  "message_id": "msg_abc123def456",
  "status": "delivered",
  "timestamp": "2025-01-24T16:23:20.655873Z",
  "events": [
    {
      "event": "sent",
      "timestamp": "2025-01-24T16:23:20.655873Z"
    },
    {
      "event": "delivered",
      "timestamp": "2025-01-24T16:23:25.123456Z"
    }
  ]
}
```

**Status Values:**
- `sent` - Email accepted for delivery
- `delivered` - Email delivered to recipient
- `opened` - Email opened by recipient
- `clicked` - Links in email clicked
- `bounced` - Email bounced
- `failed` - Delivery failed

### Contact Management

#### POST /api/v1/contacts

Create a new contact in the CRM system.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "tags": ["newsletter", "customer"],
  "metadata": {
    "source": "web_signup",
    "utm_campaign": "newsletter"
  }
}
```

**Response:**
```json
{
  "contact_id": "contact_uuid4_generated",
  "email": "newuser@example.com",
  "status": "active",
  "created_at": "2025-01-24T16:23:20.655873Z"
}
```

**Response Codes:**
- `201` - Contact created successfully
- `400` - Invalid email format
- `409` - Contact already exists

#### GET /api/v1/contacts

List contacts with pagination.

**Query Parameters:**
- `limit` (int, default=100): Number of contacts to return
- `offset` (int, default=0): Number of contacts to skip

**Response:**
```json
{
  "contacts": [
    {
      "contact_id": "contact_123",
      "email": "user1@example.com",
      "first_name": "User",
      "last_name": "One",
      "tags": ["newsletter"],
      "created_at": "2025-01-24T16:23:20.655873Z",
      "status": "active"
    }
  ],
  "total": 1234,
  "limit": 100,
  "offset": 0
}
```

#### GET /api/v1/contacts/count

Get contact statistics.

**Response:**
```json
{
  "total": 5432,
  "active": 4821,
  "unsubscribed": 611,
  "bounced": 89,
  "last_updated": "2025-01-24T16:23:20.655873Z"
}
```

### Subscriber Management

#### GET /api/v1/users/subscribers

Get list of newsletter subscribers.

**Query Parameters:**
- `limit` (int, default=100): Number of subscribers to return
- `offset` (int, default=0): Number of subscribers to skip
- `status` (string, default="active"): Filter by status
- `newsletter_opt_in` (bool): Filter by newsletter opt-in status

**Response:**
```json
{
  "subscribers": [
    {
      "id": "sub_0001",
      "email": "subscriber1@example.com",
      "first_name": "Subscriber",
      "last_name": "One",
      "status": "active",
      "subscription_date": "2024-01-01T00:00:00Z",
      "tags": ["newsletter", "dry-run"],
      "metadata": {}
    }
  ],
  "total": 1000,
  "limit": 100,
  "offset": 0,
  "status_filter": "active",
  "newsletter_opt_in_filter": true
}
```

### Campaign Management

#### POST /api/v1/campaigns

Create a new email campaign.

**Request Body:**
```json
{
  "name": "Weekly Newsletter Campaign",
  "description": "Regular newsletter sent to subscribers",
  "tags": ["newsletter", "weekly"],
  "metadata": {
    "template_id": "template_123",
    "send_date": "2025-01-25T10:00:00Z"
  }
}
```

**Response:**
```json
{
  "campaign_id": "campaign_uuid4_generated",
  "name": "Weekly Newsletter Campaign",
  "status": "draft",
  "created_at": "2025-01-24T16:23:20.655873Z"
}
```

#### GET /api/v1/campaigns/{campaign_id}/analytics

Get campaign performance analytics.

**Path Parameters:**
- `campaign_id` (string): The campaign ID

**Response:**
```json
{
  "campaign_id": "campaign_123",
  "sent": 2500,
  "delivered": 2350,
  "opened": 940,
  "clicked": 235,
  "unsubscribed": 12,
  "bounced": 45,
  "open_rate": 0.4,
  "click_rate": 0.094,
  "last_updated": "2025-01-24T16:23:20.655873Z"
}
```

### Reporting

#### GET /api/v1/reports/emails

Get email sending reports.

**Query Parameters:**
- `days` (int, default=7): Number of days to include in report

**Response:**
```json
{
  "period_days": 7,
  "total_emails": 12500,
  "emails_by_day": [
    {
      "date": "2025-01-24",
      "sent": 1250,
      "delivered": 1180,
      "opened": 520
    },
    {
      "date": "2025-01-23",
      "sent": 890,
      "delivered": 845,
      "opened": 380
    }
  ],
  "top_subjects": [
    {
      "subject": "Weekly Breathscape Update",
      "sent": 500,
      "open_rate": 0.42
    },
    {
      "subject": "New Meditation Techniques",
      "sent": 350,
      "open_rate": 0.38
    }
  ]
}
```

### Administrative

#### GET /api/v1/stats

Get mock service statistics.

**Response:**
```json
{
  "service": "mock-crm",
  "uptime": "healthy",
  "requests_handled": 1234,
  "emails_sent": 567,
  "contacts_created": 89,
  "campaigns_created": 12,
  "timestamp": "2025-01-24T16:23:20.655873Z"
}
```

#### DELETE /api/v1/test-data

Clear all mock test data (development only).

**Response:**
```json
{
  "status": "success",
  "message": "All test data cleared"
}
```

---

## Mock Platform Service (Port 8002)

The Mock Platform Service simulates a content publishing platform with web publishing, social media, and analytics capabilities.

**Base URL:** `http://localhost:8002`
**Interactive Documentation:** `http://localhost:8002/docs`

### Authentication

Mock Platform Service accepts any API key for development purposes. In production simulation mode, use:
- **Header:** `Authorization: Bearer mock-platform-api-key`
- **Alternative:** `X-API-Key: mock-platform-api-key`

### Health Check

#### GET /health

Check service health and availability.

**Response:**
```json
{
  "status": "healthy",
  "service": "mock-platform",
  "version": "1.0.0",
  "timestamp": "2025-01-24T16:23:20.655873Z"
}
```

### Content Publishing

#### POST /api/v1/content/publish

Publish content to the platform.

**Request Body:**
```json
{
  "title": "Understanding Breathscape Technology",
  "content": "<p>Detailed article content here...</p>",
  "content_type": "web_update",
  "metadata": {
    "excerpt": "A comprehensive guide to Breathscape technology",
    "correlation_id": "web-understanding-breathscape-technology"
  },
  "tags": ["breathscape", "technology", "meditation"],
  "publish_immediately": true
}
```

**Response:**
```json
{
  "id": "content_uuid4_generated",
  "title": "Understanding Breathscape Technology",
  "status": "published",
  "url": "/updates/understanding-breathscape-technology",
  "published_at": "2025-01-24T16:23:20.655873Z",
  "correlation_id": "web-understanding-breathscape-technology"
}
```

**Response Codes:**
- `201` - Content published successfully
- `400` - Invalid content format
- `413` - Content too large
- `500` - Server error (when title contains "error")

**Error Simulation:**

| Title Contains | Behavior | Response Code |
|----------------|----------|---------------|
| "error" | Simulates platform error | 500 |
| "invalid" | Simulates validation error | 400 |
| "large" | Simulates content too large | 413 |

#### GET /api/v1/content/{content_id}

Retrieve published content.

**Path Parameters:**
- `content_id` (string): The content ID

**Response:**
```json
{
  "id": "content_123",
  "title": "Understanding Breathscape Technology",
  "content": "<p>Detailed article content...</p>",
  "status": "published",
  "url": "/updates/understanding-breathscape-technology",
  "published_at": "2025-01-24T16:23:20.655873Z",
  "tags": ["breathscape", "technology"],
  "view_count": 1250,
  "engagement_score": 0.78
}
```

#### GET /api/v1/content

List published content with pagination.

**Query Parameters:**
- `limit` (int, default=20): Number of items to return
- `offset` (int, default=0): Number of items to skip
- `status` (string): Filter by status
- `tag` (string): Filter by tag

**Response:**
```json
{
  "content": [
    {
      "id": "content_123",
      "title": "Understanding Breathscape Technology",
      "status": "published",
      "published_at": "2025-01-24T16:23:20.655873Z",
      "tags": ["breathscape", "technology"],
      "view_count": 1250
    }
  ],
  "total": 456,
  "limit": 20,
  "offset": 0
}
```

### Social Media

#### POST /api/v1/social/post

Create a social media post.

**Request Body:**
```json
{
  "platform": "twitter",
  "content": "Excited to share our latest insights on Breathscape technology! 🧘✨",
  "media_urls": ["https://example.com/image.jpg"],
  "schedule_at": "2025-01-25T10:00:00Z",
  "metadata": {
    "correlation_id": "social-breathscape-insights",
    "campaign": "technology-awareness"
  }
}
```

**Response:**
```json
{
  "post_id": "post_uuid4_generated",
  "platform": "twitter",
  "status": "scheduled",
  "scheduled_at": "2025-01-25T10:00:00Z",
  "post_url": "https://twitter.com/halcytone/status/123456789",
  "created_at": "2025-01-24T16:23:20.655873Z"
}
```

**Supported Platforms:**
- `twitter`
- `linkedin`
- `instagram`
- `facebook`

#### GET /api/v1/social/posts

List social media posts.

**Query Parameters:**
- `platform` (string): Filter by platform
- `status` (string): Filter by status
- `limit` (int, default=20): Number of posts to return
- `offset` (int, default=0): Number of posts to skip

**Response:**
```json
{
  "posts": [
    {
      "post_id": "post_123",
      "platform": "twitter",
      "content": "Exciting news about Breathscape!",
      "status": "published",
      "published_at": "2025-01-24T16:23:20.655873Z",
      "engagement": {
        "likes": 45,
        "shares": 12,
        "comments": 8
      }
    }
  ],
  "total": 89,
  "limit": 20,
  "offset": 0
}
```

### Analytics

#### GET /api/v1/analytics/content

Get content performance analytics.

**Query Parameters:**
- `content_id` (string): Specific content ID
- `days` (int, default=30): Number of days to include
- `metric` (string): Specific metric to retrieve

**Response:**
```json
{
  "period_days": 30,
  "total_views": 15000,
  "unique_visitors": 8500,
  "average_time_on_page": 180,
  "bounce_rate": 0.35,
  "top_content": [
    {
      "id": "content_123",
      "title": "Understanding Breathscape Technology",
      "views": 2500,
      "engagement_score": 0.78
    }
  ],
  "daily_stats": [
    {
      "date": "2025-01-24",
      "views": 1200,
      "unique_visitors": 890
    }
  ]
}
```

#### GET /api/v1/analytics/social

Get social media performance analytics.

**Query Parameters:**
- `platform` (string): Filter by platform
- `days` (int, default=30): Number of days to include

**Response:**
```json
{
  "period_days": 30,
  "platforms": {
    "twitter": {
      "posts": 45,
      "total_reach": 25000,
      "engagement_rate": 0.042,
      "top_post": {
        "post_id": "post_123",
        "content": "Breathscape technology breakthrough!",
        "likes": 89,
        "shares": 23
      }
    },
    "linkedin": {
      "posts": 12,
      "total_reach": 8500,
      "engagement_rate": 0.068
    }
  },
  "overall_engagement_rate": 0.051
}
```

### SEO and Performance

#### GET /api/v1/seo/analysis

Get SEO analysis for published content.

**Query Parameters:**
- `content_id` (string): Specific content ID
- `url` (string): Specific URL to analyze

**Response:**
```json
{
  "content_id": "content_123",
  "url": "/updates/understanding-breathscape-technology",
  "seo_score": 85,
  "analysis": {
    "title_optimization": {
      "score": 90,
      "length": 35,
      "keywords_present": true
    },
    "meta_description": {
      "score": 80,
      "length": 155,
      "call_to_action": true
    },
    "content_quality": {
      "score": 88,
      "word_count": 1250,
      "readability_score": 75,
      "keyword_density": 0.025
    }
  },
  "recommendations": [
    "Add more internal links",
    "Optimize images with alt text",
    "Consider adding FAQ section"
  ]
}
```

### Administrative

#### GET /api/v1/stats

Get mock platform service statistics.

**Response:**
```json
{
  "service": "mock-platform",
  "uptime": "healthy",
  "requests_handled": 2345,
  "content_published": 156,
  "social_posts_created": 89,
  "analytics_requests": 234,
  "timestamp": "2025-01-24T16:23:20.655873Z"
}
```

#### DELETE /api/v1/test-data

Clear all mock test data (development only).

**Response:**
```json
{
  "status": "success",
  "message": "All platform test data cleared"
}
```

---

## Integration Examples

### Complete Content Generation Workflow

```bash
# 1. Generate content via main application
curl -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{
    "send_email": true,
    "publish_web": true,
    "generate_social": true,
    "preview_only": false
  }'

# This triggers:
# - Email sending via Mock CRM Service
# - Web publishing via Mock Platform Service
# - Social media posting via Mock Platform Service
```

### Publisher Integration Testing

```python
# Example: Test email publisher with mock CRM
import asyncio
import httpx

async def test_email_publishing():
    async with httpx.AsyncClient() as client:
        # Test email sending
        response = await client.post(
            "http://localhost:8001/api/v1/email/send",
            json={
                "subject": "Test Newsletter",
                "html_content": "<h1>Hello from Halcytone!</h1>",
                "text_content": "Hello from Halcytone!",
                "recipients": ["test@example.com"],
                "campaign_id": "test-campaign"
            }
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "sent"

        # Get email status
        message_id = result["message_id"]
        status_response = await client.get(
            f"http://localhost:8001/api/v1/email/{message_id}/status"
        )

        assert status_response.status_code == 200
        status_result = status_response.json()
        assert status_result["status"] in ["sent", "delivered"]

# Run the test
asyncio.run(test_email_publishing())
```

### Error Handling Testing

```bash
# Test CRM error scenarios
curl -X POST http://localhost:8001/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{"subject": "error test", "html_content": "test"}' \
  --fail || echo "Expected error occurred"

# Test Platform error scenarios
curl -X POST http://localhost:8002/api/v1/content/publish \
  -H "Content-Type: application/json" \
  -d '{"title": "invalid test", "content": "test"}' \
  --fail || echo "Expected error occurred"

# Test timeout scenarios
curl -X POST http://localhost:8001/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{"subject": "slow test", "html_content": "test"}' \
  --max-time 5 || echo "Expected timeout occurred"
```

---

## Development and Testing

### Local Development

#### Running Mock Services
```bash
# Start mock services individually
python mocks/crm_service.py &
python mocks/platform_service.py &

# Or use Docker
docker-compose -f docker-compose.mocks.yml up -d

# Verify services are running
curl http://localhost:8001/health
curl http://localhost:8002/health
```

#### Configuring Main Application
```bash
# Set environment variables for dry run mode
export DRY_RUN_MODE=true
export USE_MOCK_SERVICES=true
export MOCK_CRM_BASE_URL=http://localhost:8001
export MOCK_PLATFORM_BASE_URL=http://localhost:8002

# Start main application
python -m uvicorn src.halcytone_content_generator.main:app --reload
```

### Testing Strategies

#### Unit Testing Mock Services
```python
import pytest
from fastapi.testclient import TestClient
from mocks.crm_service import app as crm_app

@pytest.fixture
def crm_client():
    return TestClient(crm_app)

def test_crm_health_check(crm_client):
    response = crm_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_email_sending(crm_client):
    response = crm_client.post("/api/v1/email/send", json={
        "subject": "Test Email",
        "html_content": "<p>Test</p>",
        "recipients": ["test@example.com"]
    })
    assert response.status_code == 200
    assert "message_id" in response.json()
```

#### Integration Testing
```python
import pytest
import asyncio
from src.halcytone_content_generator.services.publishers.email_publisher import EmailPublisher
from src.halcytone_content_generator.config import get_settings

@pytest.mark.asyncio
async def test_publisher_integration():
    settings = get_settings()
    settings.DRY_RUN_MODE = True
    settings.USE_MOCK_SERVICES = True

    publisher = EmailPublisher(config={
        'crm_base_url': 'http://localhost:8001',
        'crm_api_key': 'mock-api-key'
    })

    # Test publishing
    from src.halcytone_content_generator.schemas.content import Content
    content = Content(content_type="email", title="Test", body="Test content")

    result = await publisher.publish(content)
    assert result.status == "SUCCESS"
```

### Performance Testing

#### Load Testing Mock Services
```bash
# Install apache bench
sudo apt-get install apache2-utils

# Test CRM service load
ab -n 1000 -c 10 -p test-email.json -T application/json \
  http://localhost:8001/api/v1/email/send

# Test Platform service load
ab -n 1000 -c 10 -p test-content.json -T application/json \
  http://localhost:8002/api/v1/content/publish
```

#### Memory and Resource Monitoring
```bash
# Monitor mock service resource usage
ps aux | grep -E "(crm_service|platform_service)"
top -p $(pgrep -d',' -f "mock.*service")

# Monitor with continuous updates
watch -n 2 'ps aux --sort=-%mem | grep mock | head -5'
```

---

## Configuration Reference

### Mock Service Configuration

#### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_CRM_PORT` | `8001` | Port for CRM mock service |
| `MOCK_PLATFORM_PORT` | `8002` | Port for Platform mock service |
| `MOCK_RESPONSE_DELAY` | `0` | Artificial delay in seconds |
| `MOCK_ERROR_RATE` | `0.0` | Percentage of requests to fail |
| `MOCK_DATA_RESET_INTERVAL` | `3600` | Seconds between data resets |

#### Docker Configuration
```yaml
# docker-compose.mocks.yml
version: '3.8'

services:
  mock-crm:
    build:
      context: .
      dockerfile: mocks/Dockerfile.crm
    ports:
      - "8001:8001"
    environment:
      - MOCK_RESPONSE_DELAY=0.1
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mock-platform:
    build:
      context: .
      dockerfile: mocks/Dockerfile.platform
    ports:
      - "8002:8002"
    environment:
      - MOCK_RESPONSE_DELAY=0.05
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## Troubleshooting

### Common Issues

#### Mock Service Not Responding
```bash
# Check if service is running
ps aux | grep -E "(crm_service|platform_service)"

# Check port availability
netstat -tulpn | grep -E ":(8001|8002)"

# Check service logs
tail -f logs/crm-mock.log
tail -f logs/platform-mock.log

# Restart services
pkill -f "mock.*service.py"
python mocks/crm_service.py &
python mocks/platform_service.py &
```

#### Unexpected Error Responses
Mock services simulate errors based on request content. Check if your request triggers error simulation:

- Subject/title contains "error" → 500 error
- Subject/title contains "invalid" → 400 error
- Subject/title contains "timeout" → 408 timeout
- Subject/title contains "slow" → 2-second delay

#### Integration Test Failures
```bash
# Verify mock service endpoints
curl -v http://localhost:8001/api/v1/email/send
curl -v http://localhost:8002/api/v1/content/publish

# Check main application configuration
python -c "
from src.halcytone_content_generator.config import get_settings
s = get_settings()
print(f'DRY_RUN_MODE: {s.DRY_RUN_MODE}')
print(f'USE_MOCK_SERVICES: {s.USE_MOCK_SERVICES}')
print(f'CRM URL configured: {hasattr(s, \"MOCK_CRM_BASE_URL\")}')
"
```

### Debug Mode

Enable debug logging for detailed request/response information:

```bash
# Start with debug logging
LOG_LEVEL=DEBUG python mocks/crm_service.py
LOG_LEVEL=DEBUG python mocks/platform_service.py
```

Debug logs include:
- Full request/response payloads
- Processing time for each request
- Mock data generation details
- Error simulation triggers

---

## API Versioning

### Current Version: v1

All mock services implement API version 1 (`/api/v1/*`). Version information is included in:

- **URL Path**: `/api/v1/endpoint`
- **Response Headers**: `X-API-Version: 1.0.0`
- **Service Info**: Available in health check and stats endpoints

### Future Compatibility

Mock services are designed to be backward compatible. When real API versions change:

1. Update mock service endpoints to match
2. Maintain v1 endpoints for existing integrations
3. Add new version endpoints (`/api/v2/*`) as needed
4. Update integration tests to cover multiple versions

---

## Support and Maintenance

### Logging

Mock services generate structured logs with:

```json
{
  "timestamp": "2025-01-24T16:23:20.655873Z",
  "level": "INFO",
  "service": "mock-crm",
  "endpoint": "/api/v1/email/send",
  "method": "POST",
  "status_code": 200,
  "response_time_ms": 15,
  "request_id": "req_abc123",
  "user_agent": "python-httpx/0.24.0"
}
```

### Monitoring

Mock services expose metrics at `/metrics` for Prometheus scraping:

```
# HELP mock_requests_total Total number of requests handled
# TYPE mock_requests_total counter
mock_requests_total{service="crm",endpoint="/api/v1/email/send"} 1234

# HELP mock_request_duration_seconds Request processing time
# TYPE mock_request_duration_seconds histogram
mock_request_duration_seconds_bucket{le="0.1"} 950
mock_request_duration_seconds_bucket{le="0.5"} 1200
```

### Data Persistence

Mock services maintain in-memory data that resets on restart. For persistent testing:

1. Use the `/api/v1/test-data` endpoints to clear data
2. Set up initialization scripts for consistent test data
3. Configure data reset intervals via environment variables

---

*Last Updated: Sprint 5 - Documentation & Production Readiness*
*Contact: Development Team*