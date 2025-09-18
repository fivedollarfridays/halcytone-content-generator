# Halcytone Content Generator API Documentation

## Overview

The Halcytone Content Generator is a microservice that automates multi-channel content distribution for marketing communications. It fetches content from living documents (Google Docs, Notion) and distributes it across email newsletters, website updates, and social media platforms.

## Base URL

```
Production: https://api.halcytone.com/content-generator
Staging: https://staging.halcytone.com/content-generator
Local: http://localhost:8000
```

## Authentication

All API endpoints require authentication using API keys passed in the `X-API-Key` header.

```http
X-API-Key: your-api-key-here
```

### API Key Permissions

- `read`: Read content and fetch documents
- `write`: Generate and publish content
- `admin`: Full access including configuration

## API Endpoints

### Health & Status

#### GET /health

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "content-generator",
  "version": "0.1.0"
}
```

#### GET /ready

Check if service is ready to handle requests.

**Response:**
```json
{
  "ready": true,
  "dependencies": {
    "crm": "connected",
    "platform": "connected",
    "document_sources": "ready"
  }
}
```

### Version 1 API

#### POST /api/v1/content/generate

Generate content for specified channels.

**Request Body:**
```json
{
  "source": "google_docs | notion | mock",
  "document_id": "document-id-here",
  "channels": ["email", "web", "social"],
  "template": "modern | minimal | plain",
  "custom_data": {
    "key": "value"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "generated": {
    "email": {
      "subject": "Newsletter Subject",
      "html": "<html>...</html>",
      "text": "Plain text version..."
    },
    "web": {
      "title": "Update Title",
      "html": "<article>...</article>",
      "tags": ["tag1", "tag2"],
      "seo_metadata": {...}
    },
    "social": [
      {
        "platform": "twitter",
        "content": "Tweet text...",
        "hashtags": ["#tag1", "#tag2"]
      }
    ]
  }
}
```

#### POST /api/v1/content/fetch

Fetch content from a document source.

**Request Body:**
```json
{
  "source": "google_docs | notion | url",
  "document_id": "document-id",
  "parse_strategy": "markdown | structured | freeform"
}
```

**Response:**
```json
{
  "status": "success",
  "content": {
    "breathscape": [
      {
        "title": "Section Title",
        "content": "Content text...",
        "tags": ["tag1"],
        "date": "2024-01-15T00:00:00Z"
      }
    ],
    "hardware": [...],
    "tips": [...],
    "company_vision": [...]
  }
}
```

#### POST /api/v1/newsletter/send

Send newsletter via CRM integration.

**Request Body:**
```json
{
  "subject": "Newsletter Subject",
  "html_content": "<html>...</html>",
  "text_content": "Plain text...",
  "recipient_filter": {
    "segment": "active_users",
    "tags": ["newsletter"]
  },
  "test_mode": false,
  "schedule_time": "2024-01-20T10:00:00Z"
}
```

**Response:**
```json
{
  "status": "success",
  "job_id": "email-job-123",
  "recipients": 500,
  "scheduled": true,
  "scheduled_time": "2024-01-20T10:00:00Z"
}
```

### Version 2 API (Enhanced)

#### POST /api/v2/content/sync

Synchronize content across multiple channels with advanced features.

**Request Body:**
```json
{
  "document_id": "gdocs:doc-id | notion:page-id",
  "channels": ["email", "website", "twitter", "linkedin", "facebook"],
  "schedule_time": "2024-01-20T10:00:00Z",
  "correlation_id": "request-correlation-id",
  "options": {
    "email_template": "modern",
    "seo_optimize": true,
    "test_mode": false
  }
}
```

**Response:**
```json
{
  "job_id": "sync-job-123",
  "status": "pending | in_progress | completed | failed | partial",
  "created_at": "2024-01-15T10:30:00Z",
  "scheduled_for": "2024-01-20T10:00:00Z",
  "channels": ["email", "website"],
  "correlation_id": "request-correlation-id"
}
```

#### GET /api/v2/jobs/{job_id}

Get status of a sync job.

**Response:**
```json
{
  "job_id": "sync-job-123",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:35:00Z",
  "results": {
    "email": {
      "status": "sent",
      "recipients": 500,
      "job_id": "email-job-456"
    },
    "website": {
      "status": "published",
      "content_id": "content-789",
      "url": "/updates/content-789"
    }
  },
  "errors": []
}
```

#### GET /api/v2/jobs

List recent sync jobs.

**Query Parameters:**
- `limit`: Maximum number of jobs to return (default: 10, max: 100)
- `status`: Filter by status (pending, completed, failed)
- `channel`: Filter by channel

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "sync-job-123",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "channels": ["email", "website"]
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 10
}
```

#### GET /api/v2/metrics

Get service metrics and statistics.

**Response:**
```json
{
  "total_jobs": 1000,
  "active_jobs": 5,
  "status_breakdown": {
    "completed": 900,
    "failed": 50,
    "partial": 30,
    "pending": 20
  },
  "channel_breakdown": {
    "email": 800,
    "website": 750,
    "twitter": 400,
    "linkedin": 300,
    "facebook": 250
  },
  "success_rate": 90.0,
  "average_processing_time_seconds": 45,
  "last_sync_times": {
    "gdocs:main-doc": "2024-01-15T09:00:00Z"
  }
}
```

#### POST /api/v2/jobs/{job_id}/retry

Retry a failed or partial job.

**Response:**
```json
{
  "new_job_id": "sync-job-retry-456",
  "status": "pending",
  "original_job_id": "sync-job-123",
  "created_at": "2024-01-15T11:00:00Z"
}
```

### Platform Integration

#### POST /api/v2/platform/publish

Publish content to Platform API.

**Request Body:**
```json
{
  "title": "Content Title",
  "content": "<html>...</html>",
  "category": "updates | blog | news",
  "tags": ["tag1", "tag2"],
  "author": "Author Name",
  "seo_metadata": {
    "meta_description": "Description...",
    "og_image": "https://..."
  },
  "status": "draft | scheduled | published",
  "scheduled_time": "2024-01-20T10:00:00Z"
}
```

**Response:**
```json
{
  "content_id": "content-123",
  "status": "published",
  "url": "/updates/content-123",
  "version": 1,
  "published_at": "2024-01-15T10:30:00Z"
}
```

#### GET /api/v2/platform/content/{content_id}/metrics

Get metrics for published content.

**Response:**
```json
{
  "content_id": "content-123",
  "views": 1500,
  "unique_views": 1200,
  "engagement_rate": 5.5,
  "average_time_seconds": 45,
  "shares": 25,
  "comments": 10
}
```

### Email Analytics

#### GET /api/v2/analytics/campaigns/{campaign_id}

Get email campaign analytics.

**Response:**
```json
{
  "campaign_id": "campaign-123",
  "total_sent": 500,
  "total_delivered": 495,
  "total_opened": 200,
  "unique_opens": 150,
  "total_clicked": 50,
  "unique_clicks": 40,
  "open_rate": 30.3,
  "click_rate": 8.1,
  "unsubscribe_rate": 0.5,
  "popular_links": [
    {
      "url": "https://example.com",
      "clicks": 25
    }
  ]
}
```

#### GET /api/v2/analytics/recipients/{email}

Get recipient engagement metrics.

**Response:**
```json
{
  "email": "user@example.com",
  "campaigns_received": 20,
  "campaigns_opened": 15,
  "campaigns_clicked": 8,
  "engagement_score": 75.5,
  "status": "active",
  "last_open": "2024-01-14T10:00:00Z",
  "last_click": "2024-01-14T10:05:00Z"
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request

```json
{
  "error": "validation_error",
  "message": "Invalid request parameters",
  "details": {
    "field": "error description"
  }
}
```

### 401 Unauthorized

```json
{
  "error": "unauthorized",
  "message": "Invalid or missing API key"
}
```

### 403 Forbidden

```json
{
  "error": "forbidden",
  "message": "Insufficient permissions for this operation"
}
```

### 429 Too Many Requests

```json
{
  "error": "rate_limit_exceeded",
  "message": "API rate limit exceeded",
  "retry_after": 60
}
```

### 500 Internal Server Error

```json
{
  "error": "internal_error",
  "message": "An internal error occurred",
  "correlation_id": "error-correlation-id"
}
```

## Rate Limiting

API requests are rate-limited based on your API key tier:

- **Basic**: 100 requests per minute
- **Standard**: 500 requests per minute
- **Premium**: 1000 requests per minute

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## Webhooks

Configure webhooks to receive notifications about job status changes.

### Webhook Events

- `job.completed`: Job finished successfully
- `job.failed`: Job failed
- `job.partial`: Job partially completed
- `email.sent`: Email campaign sent
- `content.published`: Content published to website

### Webhook Payload

```json
{
  "event": "job.completed",
  "timestamp": "2024-01-15T10:35:00Z",
  "data": {
    "job_id": "sync-job-123",
    "status": "completed",
    "channels": ["email", "website"],
    "results": {...}
  },
  "signature": "hmac-signature-here"
}
```

## SDK Examples

### Python

```python
import httpx
from typing import List, Dict, Optional

class HalcytoneContentClient:
    def __init__(self, api_key: str, base_url: str = "https://api.halcytone.com"):
        self.api_key = api_key
        self.base_url = f"{base_url}/content-generator"
        self.headers = {"X-API-Key": api_key}

    async def sync_content(
        self,
        document_id: str,
        channels: List[str],
        schedule_time: Optional[str] = None
    ) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v2/content/sync",
                headers=self.headers,
                json={
                    "document_id": document_id,
                    "channels": channels,
                    "schedule_time": schedule_time
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_job_status(self, job_id: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v2/jobs/{job_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

# Usage
client = HalcytoneContentClient("your-api-key")
job = await client.sync_content(
    "gdocs:doc-123",
    ["email", "website"]
)
print(f"Job created: {job['job_id']}")
```

### JavaScript/TypeScript

```typescript
class HalcytoneContentClient {
  private apiKey: string;
  private baseUrl: string;

  constructor(apiKey: string, baseUrl = "https://api.halcytone.com") {
    this.apiKey = apiKey;
    this.baseUrl = `${baseUrl}/content-generator`;
  }

  async syncContent(
    documentId: string,
    channels: string[],
    scheduleTime?: string
  ): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v2/content/sync`, {
      method: "POST",
      headers: {
        "X-API-Key": this.apiKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        document_id: documentId,
        channels: channels,
        schedule_time: scheduleTime,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async getJobStatus(jobId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v2/jobs/${jobId}`, {
      headers: {
        "X-API-Key": this.apiKey,
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }
}

// Usage
const client = new HalcytoneContentClient("your-api-key");
const job = await client.syncContent("gdocs:doc-123", ["email", "website"]);
console.log(`Job created: ${job.job_id}`);
```

## Best Practices

1. **Use Correlation IDs**: Include a correlation ID in your requests for easier debugging and tracing.

2. **Handle Rate Limits**: Implement exponential backoff when receiving 429 responses.

3. **Batch Operations**: Use the sync endpoint to handle multiple channels in one request.

4. **Monitor Job Status**: Poll job status endpoints or configure webhooks for real-time updates.

5. **Test Mode**: Use test_mode flag when testing email campaigns to avoid sending to real recipients.

6. **Cache Responses**: Cache content fetch responses to reduce API calls for frequently accessed documents.

7. **Error Handling**: Implement robust error handling for network failures and API errors.

## Support

For support, please contact:
- Email: support@halcytone.com
- Documentation: https://docs.halcytone.com
- Status Page: https://status.halcytone.com