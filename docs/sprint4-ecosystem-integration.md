# Sprint 4: Ecosystem Integration - Complete Guide

## Overview

Sprint 4 introduces advanced tone management and cache invalidation systems to the Halcytone Content Generator, enabling sophisticated content personalization and optimized performance across all channels.

## 🎯 Features Implemented

### 1. Tone Expansion System
- **Professional Tone**: Business-focused content for B2B communications
- **Encouraging Tone**: Warm, supportive content for user engagement
- **Medical/Scientific Tone**: Evidence-based content for research and clinical updates

### 2. Per-Channel Tone Configuration
- Channel-specific tone defaults
- Content constraint validation
- Multi-tone blending capabilities
- Brand consistency validation

### 3. Cache Invalidation System
- Multi-target cache invalidation (CDN, local, API, Redis)
- CloudFlare API integration
- Webhook support with signature verification
- API key authentication
- Automated cache management

## 🔧 Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Tone Management Settings
TONE_SYSTEM_ENABLED=true
DEFAULT_TONE=encouraging
TONE_AUTO_SELECTION=true
TONE_VALIDATION_ENABLED=true
TONE_FALLBACK_ENABLED=true

# Per-channel tone preferences
TONE_EMAIL_DEFAULT=encouraging
TONE_WEB_DEFAULT=professional
TONE_SOCIAL_DEFAULT=encouraging
TONE_BLOG_DEFAULT=professional
TONE_RESEARCH_DEFAULT=medical_scientific

# Brand consistency settings
BRAND_VALIDATION_ENABLED=true
BRAND_VALIDATION_STRICT=false
BRAND_VALIDATION_SCORE_THRESHOLD=0.7

# Cache Invalidation Settings
CACHE_INVALIDATION_ENABLED=true
CACHE_INVALIDATION_API_KEYS=["your_api_key_1", "your_api_key_2"]
CACHE_WEBHOOK_SECRET=your_webhook_secret_here

# CDN Configuration
CDN_ENABLED=true
CDN_TYPE=cloudflare
CDN_API_KEY=your_cloudflare_api_key_here
CDN_ZONE_ID=your_cloudflare_zone_id_here
```

## 📝 API Usage

### Content Generation with Tone Selection

#### Basic Tone Selection
```bash
curl -X POST "http://localhost:8002/api/v1/v2/generate-content" \
  -H "Content-Type: application/json" \
  -d '{
    "send_email": true,
    "publish_web": true,
    "generate_social": true,
    "tone": "professional",
    "invalidate_cache": true
  }'
```

#### Per-Channel Tone Configuration
```bash
curl -X POST "http://localhost:8002/api/v1/v2/generate-content" \
  -H "Content-Type: application/json" \
  -d '{
    "send_email": true,
    "publish_web": true,
    "generate_social": true,
    "per_channel_tones": {
      "email": "encouraging",
      "web": "professional",
      "social": "encouraging"
    },
    "invalidate_cache": true,
    "cache_targets": ["cdn", "local"]
  }'
```

#### Multi-Tone Blending
```bash
curl -X POST "http://localhost:8002/api/v1/v2/generate-content" \
  -H "Content-Type: application/json" \
  -d '{
    "send_email": true,
    "tone_combination": "professional_encouraging",
    "invalidate_cache": true
  }'
```

### Cache Management

#### Manual Cache Invalidation
```bash
curl -X POST "http://localhost:8002/api/v1/cache/invalidate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "targets": ["cdn", "local", "api"],
    "patterns": ["api/v1/content/*", "assets/*"],
    "reason": "Content update deployment"
  }'
```

#### Cache Health Check
```bash
curl -X GET "http://localhost:8002/api/v1/cache/health" \
  -H "X-API-Key: your_api_key_here"
```

#### Cache Statistics
```bash
curl -X GET "http://localhost:8002/api/v1/cache/stats" \
  -H "X-API-Key: your_api_key_here"
```

## 🎨 Tone System Details

### Available Tones

#### 1. Professional Tone
**Best for**: B2B communications, partnerships, press releases
**Characteristics**:
- Formal, authoritative language
- Clear, direct messaging
- Business-focused terminology
- Data-driven insights

**Example Templates**:
- Email announcements
- Partnership communications
- Press releases
- Business updates

#### 2. Encouraging Tone
**Best for**: User engagement, community building, wellness content
**Characteristics**:
- Warm, supportive language
- Motivational messaging
- Personal connection
- Empathy-driven content

**Example Templates**:
- Welcome emails
- Progress celebrations
- Community updates
- User success stories

#### 3. Medical/Scientific Tone
**Best for**: Research updates, clinical content, scientific publications
**Characteristics**:
- Evidence-based language
- Clinical terminology
- Research-focused content
- Professional medical communication

**Example Templates**:
- Research updates
- Clinical guidelines
- Scientific publications
- Medical announcements

### Tone Selection Algorithm

The system uses intelligent tone selection based on:
1. **Content Type**: Different content types have default tone preferences
2. **Channel**: Each channel (email, web, social) has its own defaults
3. **Context**: Content volume and topic influence tone selection
4. **User Preferences**: Explicit tone requests override defaults

### Brand Consistency Validation

The system validates brand consistency by:
- Tone alignment scoring (0.0-1.0 scale)
- Content constraint checking
- Style guide compliance
- Multi-tone balance validation

## 🗄️ Cache System Details

### Supported Cache Targets

#### 1. CDN Cache
- **Provider**: CloudFlare (extensible to AWS CloudFront)
- **Scope**: Global content delivery
- **Invalidation**: API-based pattern matching
- **Authentication**: API key + Zone ID

#### 2. Local Cache
- **Type**: In-memory application cache
- **Scope**: Application-level caching
- **Invalidation**: Direct memory clearing
- **Performance**: Immediate effect

#### 3. API Cache
- **Type**: HTTP response caching
- **Scope**: API endpoint responses
- **Invalidation**: Pattern-based key clearing
- **Integration**: Automatic with content updates

#### 4. Redis Cache (Optional)
- **Type**: External Redis instance
- **Scope**: Distributed caching
- **Invalidation**: Key pattern matching
- **Configuration**: Redis URL required

### Webhook Integration

#### Webhook Signature Verification
```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

#### Webhook Payload Example
```json
{
  "event": "content_updated",
  "targets": ["cdn", "local"],
  "patterns": ["api/v1/content/*"],
  "reason": "Content management system update"
}
```

### Auto-Invalidation Triggers

The system automatically invalidates cache when:
1. **Content Generation**: After successful content generation
2. **Deployment**: On application deployment (configurable)
3. **Manual Updates**: Via API or webhook triggers
4. **Scheduled Tasks**: Time-based invalidation (optional)

## 🔍 Monitoring and Logging

### Tone System Monitoring
- Tone selection decisions logged with context
- Brand validation scores tracked
- Multi-tone blending ratios recorded
- Performance metrics for tone processing

### Cache System Monitoring
- Invalidation request tracking
- Success/failure rates per target
- Performance metrics (response times)
- Health status monitoring
- Historical invalidation logs

### Log Examples
```
INFO: Selected tone: professional for content_type=newsletter, channel=web
INFO: Brand validation score: 0.85 (threshold: 0.7)
INFO: Cache invalidation completed: req_id=abc123, targets=2, duration=245ms
WARNING: CDN invalidation failed: CloudFlare API rate limit exceeded
```

## 🧪 Testing

### Tone System Tests
```bash
# Test tone manager functionality
python -m pytest tests/unit/test_tone_manager.py -v

# Test tone templates
python -m pytest tests/unit/test_tone_templates.py -v

# Test multi-tone integration
python -m pytest tests/integration/test_multi_tone_generation.py -v
```

### Cache System Tests
```bash
# Test cache manager
python -m pytest tests/unit/test_cache_manager.py -v

# Test cache invalidation API
python -m pytest tests/integration/test_cache_invalidation_integration.py -v
```

### Full Integration Tests
```bash
# Test complete Sprint 4 integration
python -m pytest tests/unit/test_tone_manager.py tests/unit/test_tone_templates.py tests/unit/test_cache_manager.py tests/integration/ --cov=src --cov-report=term-missing --tb=short -q
```

## 🚀 Deployment

### Production Checklist

#### Tone System
- [ ] Configure tone preferences for all channels
- [ ] Set brand validation thresholds
- [ ] Test tone selection with production content
- [ ] Verify multi-tone blending works as expected

#### Cache System
- [ ] Configure CDN API credentials
- [ ] Set up webhook endpoints and secrets
- [ ] Test cache invalidation across all targets
- [ ] Configure monitoring and alerting
- [ ] Set up API key rotation schedule

#### Environment Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Fill in all required API keys and secrets
- [ ] Test configuration with dry-run mode
- [ ] Verify external service connectivity

## 🔧 Troubleshooting

### Common Issues

#### Tone System
**Issue**: Tone not applied to generated content
- **Solution**: Check `TONE_SYSTEM_ENABLED=true` in environment
- **Debug**: Review tone selection logs for decision context

**Issue**: Brand validation failing
- **Solution**: Adjust `BRAND_VALIDATION_SCORE_THRESHOLD` or disable strict mode
- **Debug**: Check validation scores in application logs

#### Cache System
**Issue**: CDN invalidation failing
- **Solution**: Verify CloudFlare API key and zone ID
- **Debug**: Check CloudFlare API rate limits and response codes

**Issue**: Webhook signature verification failing
- **Solution**: Ensure webhook secret matches on both ends
- **Debug**: Log raw webhook payload and signature for comparison

### Debug Commands
```bash
# Test tone manager initialization
python -c "from src.halcytone_content_generator.services.tone_manager import tone_manager; print(f'Profiles: {len(tone_manager.tone_profiles)}')"

# Test cache manager
python -c "from src.halcytone_content_generator.services.cache_manager import CacheManager; print('Cache manager OK')"

# Test configuration
python -c "from src.halcytone_content_generator.config import get_settings; s=get_settings(); print(f'Tone enabled: {s.TONE_SYSTEM_ENABLED}, Cache enabled: {s.CACHE_INVALIDATION_ENABLED}')"
```

## 📊 Performance Impact

### Tone System
- **Processing Overhead**: ~5-15ms per content generation request
- **Memory Usage**: ~10MB for tone profiles and templates
- **Storage**: Negligible (templates are code-based)

### Cache System
- **CDN Invalidation**: 200-500ms per request (depends on CDN provider)
- **Local Cache**: <5ms invalidation time
- **API Overhead**: ~10-20ms for cache management operations
- **Storage**: History logs (~1KB per invalidation request)

## 🔮 Future Enhancements

### Planned Features
1. **Advanced Tone Analytics**: Content performance by tone
2. **Dynamic Tone Learning**: AI-powered tone optimization
3. **Multi-CDN Support**: AWS CloudFront, Azure CDN integration
4. **Smart Cache Prewarming**: Predictive content caching
5. **A/B Testing Integration**: Tone-based content experiments

### API Evolution
- GraphQL endpoint for complex tone queries
- Real-time tone adjustment via WebSocket
- Batch cache operations API
- Cache analytics dashboard

---

## 📚 Additional Resources

- [API Documentation](./API.md)
- [User Guide](./USER_GUIDE.md)
- [Development Setup](../README.md)
- [Sprint 3 Completion Report](./sprint3-completion-report.md)

For questions or support, please refer to the project's issue tracker or contact the development team.