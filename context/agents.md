# AI Agents Playbook - Halcytone Content Generator

This playbook guides AI agents working on the Halcytone Content Generator service. Follow these instructions precisely to enhance the content generation capabilities with batch processing, improved modularity, and production readiness.

## Context Loop Discipline (MANDATORY)

Always maintain these fields in `/context/development.md`:

- **Overall goal is:** Transform Content Generator into production-ready service with batch processing and enhanced modularity
- **Last action was:** What just completed (include commit SHA if applicable)
- **Next action will be:** The immediate next step from Sprint 7 roadmap
- **Blockers/Risks:** Social API credentials, rate limits, approval workflows, performance constraints

**After every change:**
```bash
git add -A && git commit -m "feat: [component] - description" && git push
bpsai-pair context-sync --last "What you did" --next "Next step" --blockers "Any issues"
```

## Current Mission - Content Generator Enhancement

### Sprint 7 Goals 🚧 IN PROGRESS
1. **Batch Content Generation** - Weekly planning capabilities
2. **Channel Adapter Refactoring** - Modular publisher architecture  
3. **Dry-Run Mode** - Safe testing and preview
4. **Error Resilience** - Robust handling and retries
5. **Breathscape Integration** - Narrative focus across channels

---

## Sprint 7 Implementation Guide

### 1. Batch Content Generation (START HERE)

#### Implementation Steps
```python
# halcytone_content_generator/api/batch.py
from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime, timedelta
from ..services.content_assembler import ContentAssembler
from ..schemas.content import BatchContentRequest, BatchContentResponse

router = APIRouter(prefix="/batch", tags=["batch"])

@router.post("/generate")
async def generate_batch(
    period: str = Query("week", regex="^(day|week|month)$"),
    days: Optional[int] = Query(None, ge=1, le=31),
    channels: List[str] = Query(["email", "web", "twitter", "linkedin"]),
    preview_only: bool = Query(False)
) -> BatchContentResponse:
    """
    Generate batch content for specified period
    
    Period options:
    - day: Single day's content
    - week: 7 days of content (default)
    - month: 30 days of content
    
    Or specify custom 'days' parameter
    """
    # Calculate number of content pieces needed
    content_days = days or {"day": 1, "week": 7, "month": 30}[period]
    
    # Implementation continues...
```

#### Content Scheduling Module
```python
# halcytone_content_generator/services/scheduler.py
class ContentScheduler:
    """Manages content distribution across time periods"""
    
    def __init__(self):
        self.content_rules = {
            'breathscape': {'min_per_week': 2, 'max_per_week': 3},
            'hardware': {'min_per_week': 1, 'max_per_week': 2},
            'tips': {'min_per_week': 1, 'max_per_week': 2},
            'vision': {'min_per_week': 0, 'max_per_week': 1}
        }
    
    def distribute_content(self, content: Dict, days: int) -> List[Dict]:
        """
        Distribute content items across specified days
        Ensures variety and proper pacing
        """
        scheduled = []
        # Algorithm to spread content with variety
        # Avoid duplicate topics on same day
        # Balance content types across period
        return scheduled
```

### 2. Channel Adapter Refactoring (CRITICAL)

#### Publisher Interface
```python
# halcytone_content_generator/publishers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..schemas.content import ContentBundle

class Publisher(ABC):
    """Base interface for all content publishers"""
    
    @abstractmethod
    async def publish(self, content: ContentBundle, dry_run: bool = False) -> Dict[str, Any]:
        """Publish content to channel"""
        pass
    
    @abstractmethod
    async def validate(self, content: ContentBundle) -> bool:
        """Validate content meets channel requirements"""
        pass
    
    @abstractmethod
    async def preview(self, content: ContentBundle) -> Dict[str, Any]:
        """Generate preview without publishing"""
        pass
    
    @abstractmethod
    def get_limits(self) -> Dict[str, int]:
        """Return channel-specific limits (chars, rate, etc)"""
        pass
```

#### Channel Implementations
```python
# halcytone_content_generator/publishers/email.py
from .base import Publisher
from ..services.crm_client import CRMClient

class EmailPublisher(Publisher):
    def __init__(self, crm_client: CRMClient):
        self.client = crm_client
        self.rate_limit = 100  # emails per hour
        self.batch_size = 50
    
    async def publish(self, content: ContentBundle, dry_run: bool = False) -> Dict:
        if dry_run:
            return {
                "status": "dry_run",
                "recipients": await self._get_recipient_count(),
                "would_send": content.html[:200]
            }
        
        # Actual publishing logic with batching
        return await self.client.send_newsletter_bulk(
            content.subject,
            content.html,
            content.text
        )
    
    async def validate(self, content: ContentBundle) -> bool:
        # Check subject length, HTML validity, etc.
        return len(content.subject) <= 100
    
    async def preview(self, content: ContentBundle) -> Dict:
        return {
            "subject": content.subject,
            "preview_text": content.text[:150],
            "recipient_count": await self._get_recipient_count()
        }
    
    def get_limits(self) -> Dict[str, int]:
        return {
            "subject_max": 100,
            "rate_per_hour": self.rate_limit,
            "batch_size": self.batch_size
        }
```

```python
# halcytone_content_generator/publishers/social.py
class TwitterPublisher(Publisher):
    MAX_CHARS = 280
    
    async def publish(self, content: ContentBundle, dry_run: bool = False) -> Dict:
        # Format for Twitter's constraints
        tweet = self._format_tweet(content)
        
        if dry_run:
            return {"status": "dry_run", "tweet": tweet}
        
        # Future: actual Twitter API call
        return {"status": "generated", "content": tweet}
    
    def _format_tweet(self, content: ContentBundle) -> str:
        # Truncate and add hashtags
        text = content.text[:200] + "..."
        hashtags = " #Breathscape #HealthTech"
        link = " halcytone.com/updates"
        
        available = self.MAX_CHARS - len(hashtags) - len(link)
        return text[:available] + hashtags + link
```

### 3. Dry-Run Mode Implementation

#### Service-Level Dry Run
```python
# halcytone_content_generator/services/content_sync.py
class ContentSyncService:
    def __init__(self, config: Settings):
        self.config = config
        self.publishers = self._init_publishers()
    
    async def sync_content(
        self, 
        content: Dict,
        channels: List[str],
        dry_run: bool = False
    ) -> Dict:
        """
        Sync content across channels with dry-run support
        """
        results = {}
        
        for channel in channels:
            publisher = self.publishers.get(channel)
            if not publisher:
                results[channel] = {"error": "Publisher not configured"}
                continue
            
            try:
                # Always validate first
                bundle = self._prepare_content(content, channel)
                if not await publisher.validate(bundle):
                    results[channel] = {"error": "Validation failed"}
                    continue
                
                # Publish with dry_run flag
                result = await publisher.publish(bundle, dry_run=dry_run)
                results[channel] = result
                
                if not dry_run:
                    # Log actual publication
                    await self._log_publication(channel, result)
                    
            except Exception as e:
                logger.error(f"Failed to publish to {channel}: {e}")
                results[channel] = {"error": str(e)}
                # Don't fail entire job for one channel
        
        return {
            "dry_run": dry_run,
            "timestamp": datetime.utcnow().isoformat(),
            "results": results
        }
```

#### API Endpoint with Dry Run
```python
# halcytone_content_generator/main.py
@app.post("/generate-content")
async def generate_content(
    dry_run: bool = Query(False, description="Preview without sending"),
    channels: List[str] = Query(["email", "web"]),
    settings: Settings = Depends(get_settings)
):
    """Enhanced endpoint with dry-run mode"""
    
    if dry_run:
        logger.info("Running in DRY RUN mode - no content will be sent")
    
    # Fetch and assemble content as before
    content = await fetch_and_assemble_content(settings)
    
    # Use sync service with dry_run flag
    sync_service = ContentSyncService(settings)
    results = await sync_service.sync_content(
        content, 
        channels, 
        dry_run=dry_run
    )
    
    return results
```

### 4. Enhanced Error Handling

#### Resilience Patterns
```python
# halcytone_content_generator/core/resilience.py
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Callable, Any
import asyncio

class ResilientPublisher:
    """Wrapper for publishers with resilience patterns"""
    
    def __init__(self, publisher: Publisher):
        self.publisher = publisher
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def publish_with_retry(self, content: ContentBundle) -> Dict:
        """Publish with automatic retry on failure"""
        
        if not self.circuit_breaker.is_open():
            try:
                result = await self.publisher.publish(content)
                self.circuit_breaker.record_success()
                return result
            except Exception as e:
                self.circuit_breaker.record_failure()
                logger.error(f"Publish failed: {e}")
                raise
        else:
            # Circuit is open, fail fast
            raise CircuitBreakerOpenError(
                f"Circuit breaker open for {self.publisher.__class__.__name__}"
            )
    
    async def publish_with_fallback(
        self, 
        content: ContentBundle,
        fallback_queue: Optional[Queue] = None
    ) -> Dict:
        """Publish with fallback to queue on failure"""
        try:
            return await self.publish_with_retry(content)
        except Exception as e:
            if fallback_queue:
                await fallback_queue.put({
                    "content": content,
                    "publisher": self.publisher.__class__.__name__,
                    "error": str(e),
                    "timestamp": datetime.utcnow()
                })
                return {"status": "queued", "reason": str(e)}
            raise
```

### 5. Breathscape Narrative Integration

#### Template Enhancement
```python
# halcytone_content_generator/templates/breathscape_focus.py
BREATHSCAPE_NEWSLETTER_TEMPLATE = """
<div class="hero-section">
    <h1>This Week in Breathscape</h1>
    <p class="subtitle">{{ breathscape_headline }}</p>
</div>

<div class="breathscape-updates">
    <h2>🫁 Development Highlights</h2>
    {% for update in breathscape_updates %}
        <article class="update">
            <h3>{{ update.title }}</h3>
            <p class="date">{{ update.date }}</p>
            <div class="content">{{ update.content | safe }}</div>
            {% if update.image %}
                <img src="{{ update.image }}" alt="{{ update.title }}">
            {% endif %}
        </article>
    {% endfor %}
</div>

<div class="technical-corner">
    <h2>🔧 Technical Deep Dive</h2>
    <p>{{ hardware_update }}</p>
</div>

<div class="breathing-tip">
    <h2>💡 Breathing Better</h2>
    {{ breathing_tip | safe }}
</div>
"""

# Social media templates with Breathscape focus
TWITTER_BREATHSCAPE_TEMPLATES = [
    "🫁 Breathscape Update: {title} {link} #Breathscape #BreathingTech",
    "New in Breathscape: {feature}. Experience better breathing. {link} #HealthTech",
    "Did you know? {fact} Learn more about Breathscape: {link}"
]
```

## Implementation Checklist

### Phase 1: Core Refactoring ⏳
- [ ] Create Publisher base interface
- [ ] Refactor existing publishers to implement interface
- [ ] Add dry_run parameter throughout stack
- [ ] Implement ContentScheduler for batch logic

### Phase 2: Batch Implementation 🔄
- [ ] Create /generateBatch endpoint
- [ ] Implement content distribution algorithm
- [ ] Add scheduling configuration
- [ ] Test with various period inputs

### Phase 3: Resilience & Testing 🔄
- [ ] Wrap all publishers with ResilientPublisher
- [ ] Implement fallback queue for failures
- [ ] Add comprehensive error logging
- [ ] Create dry-run integration tests

### Phase 4: Breathscape Focus ⏳
- [ ] Update newsletter templates
- [ ] Create Breathscape-specific social templates
- [ ] Ensure living document has Breathscape sections
- [ ] Test narrative consistency

### Phase 5: Production Prep ⏳
- [ ] Performance test batch operations
- [ ] Document all new endpoints
- [ ] Update monitoring dashboards
- [ ] Prepare rollback procedures

## Common Pitfalls to Avoid

### Batch Processing Pitfalls
- **Never** hardcode batch sizes or periods
- **Never** process all items in single transaction
- **Always** implement pagination for large batches
- **Always** validate total content before processing
- **Always** provide progress feedback for long operations

### Channel Adapter Pitfalls  
- **Never** mix channel-specific logic in core
- **Never** assume all channels support same features
- **Always** validate content per channel constraints
- **Always** handle channel unavailability gracefully
- **Always** respect rate limits per channel

### Dry-Run Pitfalls
- **Never** perform side effects in dry-run mode
- **Never** skip validation in dry-run
- **Always** return same structure as real run
- **Always** clearly mark dry-run results
- **Always** log dry-run executions

## Quick Reference Commands

```bash
# Run with batch generation
curl -X POST "http://localhost:8003/batch/generate?period=week&preview_only=true"

# Test dry-run mode
curl -X POST "http://localhost:8003/generate-content?dry_run=true"

# Run specific publisher tests
pytest tests/publishers/test_email_publisher.py -v

# Check publisher implementations
python -m halcytone_content_generator.publishers --list

# Validate all templates
python scripts/validate_templates.py
```

## Success Metrics

Track these for Sprint 7 success:
- Batch generation time < 2 min for week's content
- Dry-run accuracy 100% (matches real execution)
- Publisher test coverage > 90%
- Zero hardcoded channel logic in core
- All publishers implement common interface
- Error recovery success rate > 95%
- Breathscape mentioned in 80%+ of content

---

**Remember:** The goal is to make the Content Generator flexible, reliable, and maintainable. Every change should improve modularity, testability, or user experience. Focus on clean interfaces and separation of concerns.
