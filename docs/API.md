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

### Session Management API (Sprint 3: Halcytone Live Support)

#### POST /api/v2/session-summary

Generate multi-channel content summary for a breathing session.

**Request Body:**
```json
{
  "title": "Morning Breathing Session",
  "content": "Deep breathing session for stress relief",
  "session_id": "session-2024-03-21-001",
  "session_duration": 1800,
  "participant_count": 25,
  "breathing_techniques": ["Box Breathing", "4-7-8 Breathing"],
  "average_hrv_improvement": 12.5,
  "key_achievements": ["Perfect synchronization", "100% completion rate"],
  "session_type": "live",
  "instructor_name": "Sarah Chen",
  "session_date": "2024-03-21T10:00:00Z",
  "published": true,
  "channels": ["email", "web", "social"],
  "publish_immediately": false
}
```

**Response:**
```json
{
  "status": "preview",
  "content_id": "uuid-here",
  "preview_urls": {
    "session": "/sessions/session-2024-03-21-001"
  },
  "newsletter": {
    "subject": "Session Summary: Morning Breathing Session",
    "html": "<html>...</html>",
    "text": "Plain text version..."
  },
  "web_update": {
    "title": "Morning Breathing Session",
    "content": "<article>...</article>",
    "slug": "session-2024-03-21-001-summary",
    "seo_description": "Session with 25 participants achieving 12.5% HRV improvement"
  },
  "social_posts": {
    "twitter": {
      "content": "Just completed an amazing Morning Breathing Session! ...",
      "hashtags": ["#breathwork", "#mindfulness"]
    },
    "linkedin": {
      "content": "Professional update about the session...",
      "hashtags": ["#wellness", "#corporate"]
    },
    "facebook": {
      "content": "Community-focused session update...",
      "hashtags": ["#health", "#community"]
    }
  }
}
```

#### POST /api/v2/live-announce

Broadcast real-time announcements to active sessions.

**Request Body:**
```json
{
  "announcement": {
    "type": "session_starting",
    "title": "Morning Session Starting Soon!",
    "message": "Join us in 5 minutes for guided breathing",
    "action_url": "/sessions/join/morning-001"
  },
  "session_id": "morning-001"
}
```

**Response:**
```json
{
  "status": "announced",
  "sessions_notified": ["morning-001"],
  "participant_count": 25,
  "delivered": true
}
```

#### GET /api/v2/session/{session_id}/content

Get session-specific content and metrics.

**Query Parameters:**
- `include_metrics`: Include session metrics (default: false)
- `include_replay`: Include message replay data (default: false)

**Response:**
```json
{
  "session_id": "morning-001",
  "active": true,
  "session_info": {
    "title": "Morning Breathing Session",
    "instructor": "Sarah Chen",
    "participant_count": 25,
    "participants": [
      {"id": "user-001", "name": "John D.", "joined_at": "2024-03-21T10:00:00Z"}
    ],
    "started_at": "2024-03-21T10:00:00Z",
    "techniques_used": ["Box Breathing", "4-7-8 Breathing"]
  },
  "metrics": {
    "average_hrv": 12.5,
    "completion_rate": 0.95,
    "quality_score": 4.5,
    "engagement_rate": 0.92
  },
  "replay": {
    "message_count": 42,
    "messages": [
      {
        "timestamp": "2024-03-21T10:00:00Z",
        "type": "session_started",
        "content": {...}
      }
    ]
  }
}
```

#### GET /api/v2/sessions/live

List currently active live sessions.

**Query Parameters:**
- `include_metrics`: Include real-time metrics (default: false)

**Response:**
```json
{
  "count": 2,
  "sessions": [
    {
      "session_id": "morning-001",
      "title": "Morning Breathing Session",
      "instructor": "Sarah Chen",
      "participant_count": 25,
      "active": true,
      "started_at": "2024-03-21T10:00:00Z",
      "metrics": {
        "current_hrv_improvement": 8.5
      }
    },
    {
      "session_id": "afternoon-001",
      "title": "Afternoon Relaxation",
      "instructor": "Mike Johnson",
      "participant_count": 18,
      "active": true,
      "started_at": "2024-03-21T14:00:00Z",
      "metrics": {
        "current_hrv_improvement": 6.2
      }
    }
  ]
}
```

### WebSocket API

#### WebSocket /ws/live-updates

Connect to receive real-time session updates.

**Connection URL:**
```
ws://localhost:8000/ws/live-updates?session_id={session_id}&client_id={client_id}&role={role}
```

**Query Parameters:**
- `session_id`: Session to join (required)
- `client_id`: Unique client identifier (required)
- `role`: Connection role (participant|instructor|observer|admin) (default: participant)

**Message Types (Server → Client):**

| Type | Description | Payload |
|------|-------------|---------|
| `welcome` | Connection established | `{session_id, client_id, role, participant_count}` |
| `participant_joined` | New participant | `{name, count, timestamp}` |
| `technique_changed` | Breathing technique update | `{title, instruction, duration}` |
| `hrv_milestone` | HRV achievement | `{improvement, message, achievement}` |
| `session_ending` | Session concluding | `{summary_available, duration}` |
| `error` | Error occurred | `{code, message, details}` |

**Message Types (Client → Server):**

| Type | Description | Payload |
|------|-------------|---------|
| `heartbeat` | Keep connection alive | `{}` |
| `technique_feedback` | Rate technique | `{technique, rating, difficulty}` |
| `participant_status` | Update status | `{status, hrv_reading}` |

**Example Client Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live-updates?session_id=morning-001&client_id=user-123&role=participant');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'welcome':
      console.log('Connected to session:', data.session_id);
      break;
    case 'technique_changed':
      updateTechnique(data.content);
      break;
    case 'hrv_milestone':
      showAchievement(data.content);
      break;
  }
};

// Send heartbeat every 30 seconds
setInterval(() => {
  ws.send(JSON.stringify({type: 'heartbeat'}));
}, 30000);
```

## Support

For support, please contact:
- Email: support@halcytone.com
- Documentation: https://docs.halcytone.com
- Status Page: https://status.halcytone.com