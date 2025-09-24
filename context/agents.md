# AI Agents Playbook - Halcytone Content Generator

This playbook guides AI agents working on the Halcytone Content Generator service. Follow these instructions precisely to enhance documentation, testing, and ecosystem integration capabilities.

## Context Loop Discipline (MANDATORY)

Always maintain these fields in `/context/development.md`:

- **Overall goal is:** Align Content Generator with ecosystem requirements and reach production quality
- **Last action was:** What just completed (include commit SHA if applicable)
- **Next action will be:** The immediate next step from current sprint
- **Blockers/Risks:** Test coverage gaps, missing documentation, undefined workflows

**After every change:**
```bash
git add -A && git commit -m "feat: [component] - description" && git push
bpsai-pair context-sync --last "What you did" --next "Next step" --blockers "Any issues"
```

## Current Mission - Ecosystem Integration & Polish

### Active Sprint: Sprint 1 - Foundation & Cleanup ✅ COMPLETED
**Status:** Major foundation work completed with comprehensive testing infrastructure and documentation.

**Key Achievements:**
- ✅ Complete editor documentation (docs/editor-guide.md)
- ✅ Comprehensive test suites for AI/ML modules (0% → 60-95% coverage)
- ✅ Contract testing framework for external APIs
- ✅ Template testing infrastructure (email, social media)
- ✅ Publisher pattern enhanced testing
- ⚠️ Some test configuration issues need resolution

**Next Sprint:** Sprint 2 - Blog & Content Integration

---

## Sprint Implementation Guides

### Sprint 1: Foundation & Cleanup ✅ COMPLETED

**Final Status:** Foundation successfully established with major infrastructure improvements.

#### Completed Work Summary:
- **Documentation:** Complete editor guide with content types, flags, and workflows
- **Test Coverage:** Created comprehensive test suites for critical zero-coverage modules:
  - AI Content Enhancer: 60% coverage (was 0%)
  - AI Prompts: 95% coverage (was 0%)
  - Content Assembler: 100% coverage
  - Platform Client: 100% coverage
- **Contract Tests:** External API integration validation implemented
- **Template Infrastructure:** Email and social media testing frameworks ready
- **Publisher Pattern:** Enhanced test coverage for multi-channel publishing

#### Outstanding Issues:
- Test configuration mismatches in some comprehensive test files
- Import path inconsistencies need resolution
- Full coverage validation blocked by configuration issues

#### 1.1 Documentation Review 📝

**Editor Guide Creation**
```markdown
# docs/editor-guide.md

## Content Types

### Update
- Purpose: Weekly product updates
- Location: /updates page
- Fields: title, date, content, featured
- Example: "Breathscape Integration Complete"

### Blog
- Purpose: Technical deep-dives, user stories
- Location: /blog page
- Fields: title, author, date, content, tags
- Example: "The Science of Coherent Breathing"

### Announcement
- Purpose: Major releases, company news
- Location: Homepage banner + /updates
- Fields: title, date, content, priority
- Example: "Halcytone 2.0 Launch"

## Content Flags

### featured: true
- Shows content on homepage
- Limits: Max 3 featured at once
- Rotation: Weekly

### published: false
- Draft state
- Preview available via dry-run
- Not distributed to channels

## Workflow
1. Create content in living document
2. Tag with appropriate type and flags
3. Run dry-run preview
4. Review and approve
5. Publish to channels
```

**README Enhancement**
```markdown
# Setup Instructions

## Quick Start
1. Clone repository
2. Copy .env.example to .env
3. Configure API keys (see Configuration)
4. Install dependencies: pip install -r requirements.txt
5. Run tests: pytest
6. Start server: uvicorn main:app --reload

## Configuration
Required environment variables:
- GOOGLE_DOCS_CREDENTIALS: Service account JSON
- CRM_API_KEY: For newsletter distribution
- PLATFORM_API_KEY: For website publishing

## Content Types
See docs/editor-guide.md for content creation guidelines
```

#### 1.2 Test Coverage Audit 🧪

**Coverage Analysis Script**
```python
# scripts/analyze_coverage.py
import json
from pathlib import Path

def analyze_coverage_gaps():
    """Identify critical untested code paths"""
    
    critical_modules = [
        "services/crm_client.py",      # External API
        "services/platform_client.py",  # External API
        "services/google_docs.py",      # External API
        "publishers/email.py",          # Publisher pattern
        "publishers/web.py",            # Publisher pattern
        "api/batch.py",                 # Batch processing
    ]
    
    # Run coverage and identify gaps
    # Generate priority list for testing
    
    return {
        "current_coverage": 49,
        "target_coverage": 70,
        "critical_gaps": critical_modules,
        "estimated_effort": "2-3 days"
    }
```

**Test Implementation Priority**
```python
# tests/test_crm_client.py
@pytest.mark.critical
class TestCRMClient:
    """Contract tests for CRM integration"""
    
    def test_send_newsletter_contract(self, mock_crm):
        """Verify API contract with CRM service"""
        client = CRMClient(api_key="test")
        
        # Test request format
        response = client.send_newsletter(
            subject="Test",
            html_content="<p>Test</p>",
            text_content="Test"
        )
        
        # Verify response contract
        assert "message_id" in response
        assert "recipients_count" in response
        
    def test_bulk_send_resilience(self, mock_crm):
        """Test batch sending with partial failures"""
        # Implement retry logic testing
        pass
```

---

### Sprint 2: Blog & Content Integration 📚

#### 2.1 Schema Validation Implementation

```python
# schemas/content_types.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime

class ContentBase(BaseModel):
    """Base content schema with validation"""
    
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    date: datetime
    author: Optional[str] = "Halcytone Team"
    
    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

class UpdateContent(ContentBase):
    """Weekly update schema"""
    type: Literal["update"] = "update"
    featured: bool = False
    tags: List[str] = []
    
class BlogContent(ContentBase):
    """Blog post schema"""
    type: Literal["blog"] = "blog"
    category: str
    reading_time: Optional[int] = None
    seo_description: Optional[str] = None
    
    @validator('reading_time', always=True)
    def calculate_reading_time(cls, v, values):
        if not v and 'content' in values:
            # ~200 words per minute
            word_count = len(values['content'].split())
            return max(1, word_count // 200)
        return v

class AnnouncementContent(ContentBase):
    """Major announcement schema"""
    type: Literal["announcement"] = "announcement"
    priority: Literal["low", "medium", "high"] = "medium"
    expires_at: Optional[datetime] = None
```

#### 2.2 API Contract Tests

```python
# tests/contracts/test_content_api.py
import pytest
from typing import Dict, Any

class TestContentAPIContract:
    """Ensure content API maintains consistent contract"""
    
    @pytest.fixture
    def valid_update_payload(self) -> Dict[str, Any]:
        return {
            "type": "update",
            "title": "Weekly Progress",
            "content": "This week we achieved...",
            "date": "2024-01-17T00:00:00Z",
            "featured": True
        }
    
    def test_update_content_contract(self, client, valid_update_payload):
        """Verify update content endpoint contract"""
        response = client.post("/content/update", json=valid_update_payload)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "published_to" in data
        assert isinstance(data["published_to"], list)
        
    def test_content_validation_errors(self, client):
        """Ensure proper validation error format"""
        invalid_payload = {"type": "update"}  # Missing required fields
        
        response = client.post("/content/update", json=invalid_payload)
        assert response.status_code == 422
        
        errors = response.json()["detail"]
        assert any(error["loc"] == ["body", "title"] for error in errors)
```

#### 2.3 Environment Configuration

```python
# core/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Environment-based configuration"""
    
    # API Endpoints
    public_content_api_url: str = "http://localhost:8003"
    crm_api_url: str = "http://localhost:8001/api"
    platform_api_url: str = "http://localhost:8002/api"
    
    # Feature Flags
    dry_run_mode: bool = False
    batch_processing_enabled: bool = True
    cache_enabled: bool = True
    
    # Limits
    max_batch_size: int = 100
    rate_limit_per_hour: int = 1000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
```

---

### Sprint 3: Halcytone Live Support 🎯

#### 3.1 Session Summary Templates

```python
# templates/session_summary.py
BREATHING_SESSION_TEMPLATE = """
# Breathing Session Summary

**Date:** {{ session.date }}
**Duration:** {{ session.duration_minutes }} minutes
**Pattern:** {{ session.pattern_name }}

## Session Metrics
- **Average Coherence:** {{ session.avg_coherence }}%
- **HRV Score:** {{ session.hrv_score }}
- **Breaths Completed:** {{ session.breath_count }}

## Insights
{{ session.ai_insights }}

## Progress
You've completed {{ user.total_sessions }} sessions this week!
Keep up the great work on your breathing journey.

---
*Generated by Halcytone Breathscape*
"""

# services/session_content.py
class SessionContentGenerator:
    """Generate content from breathing sessions"""
    
    async def create_session_summary(self, session_data: Dict) -> AnnouncementContent:
        """Create session summary announcement"""
        
        content = self.render_template(
            BREATHING_SESSION_TEMPLATE,
            session=session_data
        )
        
        return AnnouncementContent(
            type="announcement",
            title=f"Session Complete: {session_data['pattern_name']}",
            content=content,
            priority="low",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
```

---

### Sprint 4: Ecosystem Integration 🔗

#### 4.1 Tone System Implementation

```python
# services/tone_manager.py
from enum import Enum
from typing import Dict

class ContentTone(Enum):
    PROFESSIONAL = "professional"
    ENCOURAGING = "encouraging"  
    SCIENTIFIC = "scientific"
    CASUAL = "casual"

class ToneManager:
    """Manage content tone across channels"""
    
    def __init__(self):
        self.tone_templates = {
            ContentTone.PROFESSIONAL: {
                "greeting": "Dear Professional",
                "closing": "Best regards",
                "style": "formal, data-driven"
            },
            ContentTone.ENCOURAGING: {
                "greeting": "Hey there!",
                "closing": "Keep breathing!",
                "style": "warm, supportive"
            },
            ContentTone.SCIENTIFIC: {
                "greeting": "Greetings",
                "closing": "References available upon request",
                "style": "precise, evidence-based"
            }
        }
    
    def apply_tone(self, content: str, tone: ContentTone) -> str:
        """Apply tone transformations to content"""
        # Tone-specific transformations
        return self.transform_content(content, self.tone_templates[tone])
```

#### 4.2 Cache Invalidation

```python
# api/cache.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/cache", tags=["cache"])

@router.post("/invalidate")
async def invalidate_cache(
    targets: List[str] = ["cdn", "local", "api"],
    content_ids: Optional[List[str]] = None,
    api_key: str = Depends(verify_api_key)
):
    """Invalidate cache for immediate content updates"""
    
    invalidated = []
    
    if "cdn" in targets:
        # Purge CDN cache
        cdn_result = await purge_cdn_cache(content_ids)
        invalidated.append({"target": "cdn", "status": cdn_result})
    
    if "local" in targets:
        # Clear local cache
        local_cache.clear(content_ids)
        invalidated.append({"target": "local", "status": "cleared"})
    
    if "api" in targets:
        # Trigger API cache refresh
        await refresh_api_cache(content_ids)
        invalidated.append({"target": "api", "status": "refreshed"})
    
    return {
        "invalidated": invalidated,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

### Sprint 5: Cohesion & Polishing 💎

#### 5.1 Role Documentation

```markdown
# docs/roles/marketing-guide.md

## Marketing Team Workflow

### Content Creation
1. Draft in Google Docs/Notion
2. Tag with campaign identifiers
3. Request preview via dry-run
4. Schedule publication

### Performance Tracking
- View analytics dashboard
- Export engagement metrics
- A/B test content variations

### Approval Process
1. Create content
2. Submit for review
3. Legal/compliance check
4. Schedule publication
```

#### 5.2 Test Coverage Enhancement

```python
# tests/test_integration.py
@pytest.mark.integration
class TestEndToEndWorkflow:
    """Complete workflow testing"""
    
    async def test_complete_content_pipeline(self):
        """Test content from creation to distribution"""
        
        # 1. Create content
        content = await create_test_content()
        
        # 2. Validate
        assert await validate_content(content)
        
        # 3. Dry run
        preview = await generate_with_dry_run(content)
        assert preview["dry_run"] == True
        
        # 4. Publish
        result = await publish_content(content)
        assert all(
            channel in result["published_to"] 
            for channel in ["email", "web"]
        )
        
        # 5. Verify distribution
        assert await verify_email_sent()
        assert await verify_web_published()
```

---

## Common Pitfalls to Avoid

### Documentation Pitfalls
- **Never** assume users know the system
- **Always** include examples
- **Always** document error states
- **Never** skip configuration steps

### Testing Pitfalls
- **Never** test only happy paths
- **Always** test external API failures
- **Always** mock external services
- **Never** skip contract tests

### Integration Pitfalls
- **Never** hardcode endpoints
- **Always** use environment variables
- **Always** validate schemas
- **Never** trust external data

---

## Quick Reference Commands

```bash
# Sprint 1: Documentation & Testing
pytest --cov=halcytone_content_generator --cov-report=html
python scripts/analyze_coverage.py

# Sprint 2: Schema & Contracts
pytest tests/contracts/ -v
python -m halcytone_content_generator.schemas --validate

# Sprint 3: Session Support
curl -X POST "http://localhost:8003/session/summary" -d @session_data.json

# Sprint 4: Tone & Cache
curl -X POST "http://localhost:8003/cache/invalidate?targets=cdn,api"
curl -X POST "http://localhost:8003/content/generate?tone=professional"

# Sprint 5: Final Testing
pytest tests/ --cov-report=term-missing
python scripts/load_test.py --users 100 --duration 60
```

---

## Success Metrics Per Sprint

### Sprint 1
- Documentation completeness: 100%
- Test gaps identified: All critical modules
- Coverage plan created: Yes

### Sprint 2  
- Schema validation: 100% of content types
- Contract tests: All external APIs
- Config management: Environment-based

### Sprint 3
- Session templates: Created and tested
- Real-time support: WebSocket integration

### Sprint 4
- Tone options: 4 distinct tones
- Cache invalidation: <100ms response

### Sprint 5
- Test coverage: >70%
- Documentation: All roles covered
- Performance: <2s for batch operations

---

**Remember:** Each sprint builds on the previous one. Focus on creating a robust, well-documented, and thoroughly tested content generation service that seamlessly integrates with the Halcytone ecosystem.
