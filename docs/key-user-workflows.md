# 5 Key User Workflows

## Table of Contents
1. [Weekly Content Update Workflow](#1-weekly-content-update-workflow)
2. [Blog Post Creation and Publishing](#2-blog-post-creation-and-publishing)
3. [Urgent Announcement Distribution](#3-urgent-announcement-distribution)
4. [Session Summary Generation](#4-session-summary-generation)
5. [Batch Content Processing](#5-batch-content-processing)

---

## 1. Weekly Content Update Workflow

### Overview
Generate and distribute weekly updates across all channels every Tuesday at 10:00 AM EST.

### User Roles
- **Primary**: Content Editor
- **Approval**: Marketing Manager
- **Distribution**: Automated System

### Step-by-Step Process

#### Monday 2:00 PM - Content Collection
```bash
# 1. Fetch content from living document
GET /api/content/fetch-document
Authorization: Bearer {editor_token}

# Response includes categorized content:
# - Breathscape updates
# - Hardware developments
# - Weekly tips
# - Vision statements
```

#### Monday 4:00 PM - Content Generation
```bash
# 2. Generate multi-channel content
POST /api/v2/generate-content
Authorization: Bearer {editor_token}
Content-Type: application/json

{
  "send_email": true,
  "publish_web": true,
  "generate_social": true,
  "template_style": "weekly_update",
  "tone": "encouraging",
  "validate_before_generate": true,
  "social_platforms": ["twitter", "linkedin", "facebook"]
}
```

#### Tuesday 9:00 AM - Review & Approval
1. **Editor Review**
   - Check content accuracy
   - Verify links and images
   - Confirm scheduling

2. **Marketing Approval**
   - Review messaging alignment
   - Approve social media posts
   - Confirm distribution list

```bash
# 3. Preview content before sending
POST /api/v2/generate-content
{
  "preview_only": true,
  "include_preview": true
}
```

#### Tuesday 10:00 AM - Publication
```bash
# 4. Execute distribution
POST /api/v2/sync-content
{
  "content_id": "{generated_content_id}",
  "publish_immediately": true,
  "invalidate_cache": true
}
```

#### Tuesday 2:00 PM - Performance Monitoring
```bash
# 5. Check analytics
GET /api/analytics/summary?content_id={content_id}

# Monitor:
# - Email open rates
# - Click-through rates
# - Social engagement
# - Website traffic
```

### Success Criteria
- ✅ All channels updated within 5 minutes
- ✅ Email delivery rate >98%
- ✅ Social posts live on all platforms
- ✅ Website cache invalidated
- ✅ Analytics tracking active

### Common Issues & Solutions
| Issue | Solution |
|-------|----------|
| Content fetch fails | Use cached backup from previous week |
| Email service down | Queue for retry, notify subscribers |
| Social API limit | Stagger posts over 30 minutes |
| Cache not clearing | Manual invalidation via admin panel |

---

## 2. Blog Post Creation and Publishing

### Overview
Create SEO-optimized blog posts with multi-channel promotion.

### User Roles
- **Primary**: Content Writer
- **Review**: Editor
- **SEO**: Marketing Specialist
- **Approval**: Content Manager

### Step-by-Step Process

#### Step 1: Content Creation
```bash
# Create blog post draft
POST /api/v2/generate-content
Authorization: Bearer {writer_token}
Content-Type: application/json

{
  "content": {
    "type": "blog",
    "title": "The Science Behind Coherent Breathing",
    "content": "Full article content...",
    "category": "Science & Research",
    "author": "Dr. Sarah Chen",
    "target_keywords": ["coherent breathing", "HRV", "breathing technique"],
    "seo_description": "Discover the science behind coherent breathing and how it improves HRV."
  },
  "preview_only": true,
  "seo_optimize": true,
  "tone": "medical_scientific"
}
```

#### Step 2: SEO Optimization
```bash
# Validate SEO metrics
POST /api/v2/validate-content
{
  "content": {...},
  "strict_mode": true
}

# Check:
# - Title length (50-60 chars)
# - Meta description (150-160 chars)
# - Keyword density (1-2%)
# - Reading level
# - Internal/external links
```

#### Step 3: Editorial Review
1. **Content Review**
   - Fact-checking
   - Grammar and style
   - Brand voice consistency
   - Image optimization

2. **Technical Review**
   - Schema markup
   - Open Graph tags
   - Twitter cards
   - AMP compatibility

#### Step 4: Publishing
```bash
# Publish to website and generate social posts
POST /api/v2/generate-content
{
  "content": {...},
  "publish_web": true,
  "generate_social": true,
  "social_platforms": ["twitter", "linkedin"],
  "schedule_time": "2024-03-15T14:00:00Z"
}
```

#### Step 5: Promotion
```bash
# Schedule email newsletter mention
POST /api/email/schedule-campaign
{
  "campaign_type": "blog_announcement",
  "blog_id": "{blog_id}",
  "send_time": "2024-03-16T10:00:00Z",
  "segment": "blog_subscribers"
}
```

### Success Criteria
- ✅ SEO score >80/100
- ✅ Published to website
- ✅ Social posts scheduled
- ✅ Email campaign created
- ✅ Analytics tracking enabled

---

## 3. Urgent Announcement Distribution

### Overview
Rapidly distribute time-sensitive announcements across all channels.

### User Roles
- **Primary**: Marketing Manager
- **Approval**: Executive Team
- **Execution**: System Administrator

### Step-by-Step Process

#### Step 1: Create Announcement
```bash
# Create urgent announcement
POST /api/v2/generate-content
Authorization: Bearer {manager_token}
X-Priority: HIGH

{
  "content": {
    "type": "announcement",
    "title": "🎉 Breathscape 2.0 Launch",
    "content": "Major announcement content...",
    "urgency": "high",
    "priority": 1,
    "featured": true,
    "call_to_action": "Download Now",
    "expiry_date": "2024-03-20T23:59:59Z"
  },
  "send_email": true,
  "publish_web": true,
  "generate_social": true,
  "invalidate_cache": true,
  "bypass_queue": true
}
```

#### Step 2: Executive Approval (< 30 minutes)
```bash
# Request expedited approval
POST /api/approval/request
{
  "content_id": "{announcement_id}",
  "urgency": "critical",
  "approvers": ["ceo@halcytone.com", "cmo@halcytone.com"],
  "deadline": "30_minutes"
}
```

#### Step 3: Multi-Channel Distribution
```bash
# Execute immediate distribution
POST /api/batch/distribute
{
  "content_id": "{announcement_id}",
  "channels": ["email", "web", "social", "push"],
  "priority": "immediate",
  "override_schedule": true
}
```

#### Step 4: Cache Invalidation
```bash
# Force cache refresh
POST /api/cache/invalidate
{
  "targets": ["cdn", "local", "api", "redis"],
  "patterns": ["/*"],
  "force": true,
  "reason": "Urgent announcement"
}
```

#### Step 5: Monitor Distribution
```bash
# Real-time monitoring
GET /api/monitor/distribution/{announcement_id}
WebSocket: ws://api/monitor/live/{announcement_id}

# Track:
# - Email delivery status
# - Website update confirmation
# - Social post status
# - Push notification delivery
```

### Success Criteria
- ✅ All channels updated within 5 minutes
- ✅ Email blast sent to all subscribers
- ✅ Website banner activated
- ✅ Social posts live on all platforms
- ✅ Push notifications delivered
- ✅ Cache fully invalidated

---

## 4. Session Summary Generation

### Overview
Generate and distribute personalized summaries after each Halcytone Live session.

### User Roles
- **Primary**: Session Instructor
- **System**: Automated Processing
- **Recipients**: Session Participants

### Step-by-Step Process

#### Step 1: Connect to Live Session
```javascript
// WebSocket connection for real-time data
const ws = new WebSocket('ws://api/sessions/{session_id}/connect');

ws.on('message', (event) => {
  // Process real-time events:
  // - participant_joined
  // - hrv_milestone
  // - technique_changed
  // - session_metrics
});
```

#### Step 2: Collect Session Data
```bash
# Session data structure
{
  "session_id": "session-123",
  "session_name": "Morning Breathwork",
  "instructor": "Jane Doe",
  "participants": 25,
  "duration_minutes": 30,
  "average_hrv_improvement": 15.5,
  "techniques_used": ["Box Breathing", "4-7-8"],
  "milestones": [
    {"user": "user1", "achievement": "First 10-min session"},
    {"user": "user2", "improvement": 22.5}
  ]
}
```

#### Step 3: Generate Summaries
```bash
# Auto-generate personalized summaries
POST /api/sessions/{session_id}/generate-summary
{
  "include_personal_stats": true,
  "include_group_stats": true,
  "include_achievements": true,
  "template": "session_summary"
}
```

#### Step 4: Personalize Content
```python
# For each participant
for participant in session.participants:
    summary = {
        "personal_stats": {
            "hrv_improvement": participant.hrv_change,
            "session_duration": participant.duration,
            "techniques_practiced": participant.techniques
        },
        "achievements": participant.new_achievements,
        "recommendations": generate_recommendations(participant),
        "next_session": suggest_next_session(participant)
    }
```

#### Step 5: Distribute Summaries
```bash
# Send personalized emails
POST /api/email/batch-send
{
  "template": "session_summary",
  "recipients": [
    {
      "email": "user1@example.com",
      "data": {personalized_summary_1}
    },
    {
      "email": "user2@example.com",
      "data": {personalized_summary_2}
    }
  ],
  "send_immediately": true
}
```

### Success Criteria
- ✅ Summaries generated within 5 minutes of session end
- ✅ All participants receive personalized email
- ✅ Achievements tracked and displayed
- ✅ Instructor receives aggregate report
- ✅ Data synced to user profiles

---

## 5. Batch Content Processing

### Overview
Process multiple content items efficiently for campaign launches or content libraries.

### User Roles
- **Primary**: Content Manager
- **Execution**: Batch Processing System
- **Monitoring**: System Administrator

### Step-by-Step Process

#### Step 1: Prepare Batch Content
```bash
# Prepare batch request
POST /api/batch/prepare
{
  "items": [
    {
      "content": {
        "type": "update",
        "title": "Breathing Tip #1",
        "content": "Content for tip 1..."
      },
      "channels": ["web", "social"]
    },
    // ... up to 100 items
  ],
  "batch_size": 10,  # Process in chunks
  "parallel_processing": true,
  "continue_on_error": true
}
```

#### Step 2: Submit for Processing
```bash
# Submit batch job
POST /api/batch/generate
{
  "batch_id": "{prepared_batch_id}",
  "priority": "normal",
  "scheduled_start": "2024-03-15T03:00:00Z",
  "notification_webhook": "https://webhook.site/batch-complete"
}

# Response
{
  "batch_id": "batch-abc123",
  "status": "queued",
  "estimated_completion": "2024-03-15T03:10:00Z",
  "monitor_url": "/api/batch/batch-abc123/status"
}
```

#### Step 3: Monitor Progress
```bash
# Poll for status
GET /api/batch/{batch_id}/status

# Response
{
  "batch_id": "batch-abc123",
  "status": "processing",
  "progress": 65,
  "processed_items": 65,
  "total_items": 100,
  "failed_items": 2,
  "current_chunk": 7,
  "estimated_remaining": "3 minutes"
}
```

#### Step 4: Handle Failures
```bash
# Retry failed items
POST /api/batch/{batch_id}/retry-failed
{
  "retry_strategy": "exponential_backoff",
  "max_retries": 3,
  "continue_on_error": true
}
```

#### Step 5: Review Results
```bash
# Get detailed results
GET /api/batch/{batch_id}/results

# Response
{
  "batch_id": "batch-abc123",
  "completed_at": "2024-03-15T03:09:45Z",
  "total_time_seconds": 585,
  "success_rate": 0.98,
  "results": [
    {
      "item_id": "item-1",
      "status": "success",
      "content_id": "content-123",
      "channels_published": ["web", "social"]
    },
    // ... all items
  ],
  "performance_metrics": {
    "items_per_second": 5.7,
    "average_item_time": 175,
    "peak_memory_mb": 245
  }
}
```

### Success Criteria
- ✅ Batch completes within performance targets (<2s for 10 items)
- ✅ Success rate >95%
- ✅ Failed items logged with retry option
- ✅ Memory usage stable
- ✅ Results accessible for audit

### Performance Benchmarks
| Batch Size | Target Time | Items/Second |
|------------|-------------|--------------|
| 10 items | <2 seconds | >5 |
| 50 items | <10 seconds | >5 |
| 100 items | <20 seconds | >5 |

---

## Workflow Quick Reference

### API Endpoints
```bash
# Content Generation
POST /api/v2/generate-content
POST /api/v2/validate-content
POST /api/batch/generate

# Distribution
POST /api/v2/sync-content
POST /api/email/send
POST /api/social/publish

# Monitoring
GET /api/analytics/summary
GET /api/batch/{id}/status
ws://api/sessions/{id}/connect

# Cache Management
POST /api/cache/invalidate
GET /api/cache/status
```

### Common Headers
```bash
Authorization: Bearer {token}
Content-Type: application/json
X-Priority: HIGH|NORMAL|LOW
X-Request-ID: {uuid}
```

### Response Codes
- `200 OK` - Success
- `201 Created` - Content created
- `202 Accepted` - Batch queued
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Invalid token
- `422 Unprocessable Entity` - Validation failed
- `429 Too Many Requests` - Rate limited
- `500 Internal Server Error` - System error

---

*Last Updated: January 2025 | Sprint 5 - Final Polish*