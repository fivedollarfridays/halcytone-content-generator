# Automated Social Media Posting

## Overview

The Automated Social Media Posting feature provides enterprise-grade social media integration with direct API access to Twitter and LinkedIn platforms. This system includes background scheduling, comprehensive analytics, rate limiting, and robust error handling.

## Features

### ✅ Core Capabilities

- **Direct API Integration**: Twitter API v2 and LinkedIn UGC API
- **Background Scheduling**: Async task queue with configurable scheduling
- **Real-time Analytics**: Performance tracking and posting statistics
- **Rate Limiting**: Automatic API quota management with exponential backoff
- **Retry Logic**: Configurable retry attempts with intelligent error handling
- **Credential Management**: Secure OAuth token handling with expiration tracking
- **Platform Verification**: Real-time connection status checking

### 🔧 Technical Architecture

- **Publisher Pattern**: Extensible architecture for multiple social platforms
- **Async Processing**: Non-blocking background task execution
- **Error Recovery**: Comprehensive error handling with graceful degradation
- **Monitoring**: Health checks and platform connectivity verification
- **Dry Run Mode**: Safe testing without actual posting

## Configuration

### Environment Variables

```bash
# Twitter API Configuration
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# LinkedIn API Configuration
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
```

### Platform Credentials Setup

```python
from src.halcytone_content_generator.services.publishers.social_publisher import (
    SocialPublisher, PlatformCredentials
)

# Initialize publisher
publisher = SocialPublisher()

# Configure Twitter credentials
twitter_creds = PlatformCredentials(
    access_token="your_access_token",
    access_token_secret="your_access_token_secret",
    api_key="your_api_key",
    api_secret="your_api_secret"
)
await publisher.configure_platform("twitter", twitter_creds)

# Configure LinkedIn credentials
linkedin_creds = PlatformCredentials(
    access_token="your_linkedin_access_token",
    client_id="your_client_id",
    client_secret="your_client_secret"
)
await publisher.configure_platform("linkedin", linkedin_creds)
```

## Usage Examples

### Immediate Posting

```python
# Post immediately to social media
result = await publisher.publish(
    content="Your social media content",
    channels=["twitter", "linkedin"],
    options={
        "dry_run": False,
        "immediate": True
    }
)
```

### Scheduled Posting

```python
from datetime import datetime, timedelta

# Schedule a post for later
schedule_time = datetime.utcnow() + timedelta(hours=2)

result = await publisher.publish(
    content="Scheduled social media content",
    channels=["twitter"],
    options={
        "scheduled_for": schedule_time.isoformat(),
        "immediate": False
    }
)
```

### Batch Scheduling

```python
# Schedule multiple posts
posts = [
    {
        "content": "First post content",
        "platform": "twitter",
        "scheduled_for": datetime.utcnow() + timedelta(hours=1)
    },
    {
        "content": "Second post content",
        "platform": "linkedin",
        "scheduled_for": datetime.utcnow() + timedelta(hours=2)
    }
]

for post_data in posts:
    await publisher.schedule_post(
        post_id=f"batch_post_{uuid.uuid4()}",
        content=post_data["content"],
        platform=post_data["platform"],
        scheduled_for=post_data["scheduled_for"]
    )
```

## API Endpoints

### POST /api/v2/content/generate

Enhanced to support automated social posting:

```json
{
  "content_request": {
    "source": {
      "type": "document",
      "url": "https://docs.google.com/document/d/your-doc-id"
    },
    "channels": ["social_media"],
    "social_options": {
      "platforms": ["twitter", "linkedin"],
      "immediate": false,
      "scheduled_for": "2024-01-01T12:00:00Z"
    }
  }
}
```

### GET /api/v2/social/status

Check platform connection status:

```json
{
  "platforms": {
    "twitter": "connected",
    "linkedin": "connected"
  },
  "scheduler_status": "active",
  "queued_posts": 5
}
```

### GET /api/v2/social/analytics

Retrieve posting analytics:

```json
{
  "total_posts": 150,
  "successful_posts": 145,
  "failed_posts": 5,
  "platforms": {
    "twitter": {
      "posts": 80,
      "success_rate": 0.975
    },
    "linkedin": {
      "posts": 70,
      "success_rate": 0.957
    }
  }
}
```

## Platform-Specific Features

### Twitter Integration

- **API Version**: Twitter API v2
- **Authentication**: OAuth 1.0a
- **Rate Limits**: 300 tweets per 15-minute window
- **Features**: Text posts, media attachments, thread support
- **Character Limit**: 280 characters

### LinkedIn Integration

- **API Version**: LinkedIn UGC API
- **Authentication**: OAuth 2.0
- **Rate Limits**: 100 posts per day
- **Features**: Text posts, article sharing, company page posting
- **Character Limit**: 3,000 characters

## Error Handling

### Retry Logic

```python
# Configurable retry settings
retry_config = {
    "max_retries": 3,
    "backoff_factor": 2.0,
    "retry_statuses": [429, 500, 502, 503, 504]
}
```

### Rate Limit Management

- Automatic detection of rate limit headers
- Intelligent backoff with exponential delay
- Queue pausing when limits exceeded
- Automatic resume when limits reset

### Error Categories

1. **Temporary Errors**: Network issues, rate limits (auto-retry)
2. **Permanent Errors**: Invalid credentials, content violations (no retry)
3. **Platform Errors**: API downtime, service unavailable (retry with backoff)

## Monitoring and Analytics

### Real-time Metrics

- Posts per platform
- Success/failure rates
- Average posting time
- Queue length and processing rate
- Rate limit consumption

### Health Checks

```python
# Check platform connectivity
twitter_status = await publisher.verify_platform_connection("twitter")
linkedin_status = await publisher.verify_platform_connection("linkedin")

# Get overall health
health = await publisher.health_check()
```

### Performance Analytics

```python
# Get detailed posting statistics
stats = await publisher.get_posting_stats()
print(f"Total posts: {stats.total_posts}")
print(f"Success rate: {stats.success_rate:.2%}")
print(f"Average response time: {stats.avg_response_time:.2f}s")
```

## Testing

### Unit Tests

The automated social posting includes comprehensive test coverage:

- **30 test cases** covering all functionality
- **API integration testing** with aioresponses
- **Error scenario testing** for robust error handling
- **Rate limiting validation**
- **Credential management testing**

### Running Tests

```bash
# Run all social publisher tests
pytest tests/unit/test_social_publisher_automated.py -v

# Run with coverage
pytest tests/unit/test_social_publisher_automated.py --cov=src/halcytone_content_generator/services/publishers/social_publisher --cov-report=html
```

## Security Considerations

### Credential Protection

- OAuth tokens encrypted at rest
- Automatic token refresh handling
- Secure credential validation
- No plaintext storage of sensitive data

### API Security

- HMAC request signing for authentication
- Rate limit compliance to prevent API abuse
- Input validation and sanitization
- Secure error handling without information leakage

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify API credentials are current
   - Check token expiration dates
   - Ensure proper OAuth flow completion

2. **Rate Limit Exceeded**
   - Monitor posting frequency
   - Review rate limit headers
   - Adjust scheduling intervals

3. **Content Validation Errors**
   - Check character limits per platform
   - Validate content format requirements
   - Review platform content policies

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging for social publisher
logger = logging.getLogger('src.halcytone_content_generator.services.publishers.social_publisher')
logger.setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features

- **Additional Platforms**: Instagram, Facebook, TikTok integration
- **Advanced Analytics**: Engagement metrics, reach analysis
- **Content Optimization**: AI-driven content suggestions
- **Visual Content**: Image and video posting support
- **Bulk Operations**: Mass scheduling and content management

### API Roadmap

- **Webhook Support**: Real-time posting notifications
- **Template Engine**: Reusable content templates
- **A/B Testing**: Content variation testing
- **Campaign Management**: Multi-post campaign coordination