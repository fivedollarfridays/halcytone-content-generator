# AI Agents Playbook - Halcytone Command Center

This playbook guides AI agents working on the Halcytone Command Center platform transformation. Follow these instructions precisely to transform the Platform API into a unified service orchestrator and monitoring hub, and implement the Content Generator service.

## Context Loop Discipline (MANDATORY)

Always maintain these fields in `/context/development.md`:

- **Overall goal is:** Transform Platform API into auth consumer and service orchestrator with comprehensive monitoring AND implement Content Generator service
- **Last action was:** What just completed (include commit SHA if applicable)
- **Next action will be:** The immediate next step from the roadmap
- **Blockers/Risks:** Authentication migration dependencies, service integration issues, security concerns, content API access

**After every change:**
```bash
bpsai-pair context-sync --last "What you did" --next "Next step" --blockers "Any issues"
```

## Current Mission - Platform Transformation & Content Generation

### Primary Goals
1. **Platform Orchestration** (Sprints 1-5 ✅ COMPLETE)
   - Consumes authentication from CRM service (no local auth)
   - Orchestrates cross-service operations
   - Provides comprehensive monitoring and observability
   - Offers unified API gateway capabilities
   - Maintains service registry and health checks
   - Delivers real-time dashboard visibility

2. **Content Generator Service** (Sprint 6 🚧 IN PROGRESS)
   - Automated multi-channel content generation
   - Email newsletter distribution via CRM
   - Website update publishing
   - Social media content creation
   - Living document integration
   - Service-to-service authentication

[Previous Sprint 1-5 Implementation Guides remain unchanged - see original file]

---

## Sprint 6 Implementation Guide - Content Generator Service

### 1. Service Architecture Setup (CRITICAL - START HERE)

#### Repository Initialization
```bash
# Create new repository or module
mkdir halcytone-content-generator
cd halcytone-content-generator

# Initialize Python project with same standards as Platform API
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install core dependencies matching platform standards
pip install fastapi uvicorn pydantic python-dotenv
pip install httpx tenacity  # For resilient service calls
pip install jinja2  # For templating
pip install google-api-python-client  # If using Google Docs
```

#### Project Structure (Follow Platform Patterns)
```
halcytone-content-generator/
├── src/
│   └── halcytone_content_generator/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app entry
│       ├── config.py               # Settings management
│       ├── api/
│       │   ├── __init__.py
│       │   └── endpoints.py       # API routes
│       ├── core/
│       │   ├── __init__.py
│       │   ├── auth.py           # Service authentication
│       │   └── resilience.py     # Circuit breakers (reuse from platform)
│       ├── services/
│       │   ├── __init__.py
│       │   ├── document_fetcher.py  # Living doc integration
│       │   ├── content_assembler.py # Content generation logic
│       │   ├── crm_client.py       # CRM API integration
│       │   └── platform_client.py  # Platform API integration
│       └── schemas/
│           ├── __init__.py
│           └── content.py         # Pydantic models
├── tests/
├── docker/
├── .env.example
└── README.md
```

#### Configuration Management
```python
# halcytone_content_generator/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service Configuration
    SERVICE_NAME: str = "content-generator"
    API_KEY: str  # For this service's authentication
    
    # External Services
    CRM_BASE_URL: str
    CRM_API_KEY: str  # For calling CRM
    PLATFORM_BASE_URL: str
    PLATFORM_API_KEY: str  # For calling Platform API
    
    # Content Source
    LIVING_DOC_TYPE: str = "google_docs"  # or "notion", "internal"
    LIVING_DOC_ID: str
    GOOGLE_CREDENTIALS_JSON: str | None = None
    
    # Optional AI
    OPENAI_API_KEY: str | None = None
    
    class Config:
        env_file = ".env"
```

### 2. Living Document Integration

#### Document Structure Requirements
```markdown
# Halcytone Updates Living Document

## [Breathscape] Recent Updates
- **Date:** 2025-01-15
- **Title:** Enhanced Breathing Pattern Analysis
- **Content:** We've improved our ML models to detect...

## [Hardware] Development Progress
- **Date:** 2025-01-15
- **Title:** Prototype v2 Sensor Testing
- **Content:** Our custom hardware now features...

## [Tips] Breathing Tip of the Month
- **Title:** Box Breathing Technique
- **Content:** This ancient technique helps...

## [Vision] Company Mission
- **Content:** At Halcytone, we believe breathing...
```

#### Google Docs Fetcher Implementation
```python
# halcytone_content_generator/services/document_fetcher.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re
from typing import Dict, List

class DocumentFetcher:
    def __init__(self, credentials_json: str, doc_id: str):
        self.doc_id = doc_id
        self.service = self._init_google_service(credentials_json)
    
    def _init_google_service(self, credentials_json: str):
        creds = service_account.Credentials.from_service_account_info(
            json.loads(credentials_json),
            scopes=['https://www.googleapis.com/auth/documents.readonly']
        )
        return build('docs', 'v1', credentials=creds)
    
    async def fetch_content(self) -> Dict[str, List[Dict]]:
        """Fetch and parse living document into categorized content"""
        doc = self.service.documents().get(documentId=self.doc_id).execute()
        content = self._extract_text(doc)
        
        # Parse into categories
        categories = {
            'breathscape': [],
            'hardware': [],
            'tips': [],
            'vision': []
        }
        
        current_category = None
        current_item = {}
        
        for line in content.split('\n'):
            if '[Breathscape]' in line:
                current_category = 'breathscape'
            elif '[Hardware]' in line:
                current_category = 'hardware'
            elif '[Tips]' in line:
                current_category = 'tips'
            elif '[Vision]' in line:
                current_category = 'vision'
            elif line.startswith('**Date:**'):
                current_item['date'] = line.split(':', 1)[1].strip()
            elif line.startswith('**Title:**'):
                current_item['title'] = line.split(':', 1)[1].strip()
            elif line.startswith('**Content:**'):
                current_item['content'] = line.split(':', 1)[1].strip()
                if current_category and current_item:
                    categories[current_category].append(current_item)
                    current_item = {}
        
        return categories
```

### 3. Content Assembly Logic

#### Email Newsletter Generation
```python
# halcytone_content_generator/services/content_assembler.py
from jinja2 import Template
from datetime import datetime
from typing import Dict, List

class ContentAssembler:
    def __init__(self):
        self.email_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                .header { background: #4A90E2; color: white; padding: 20px; }
                .section { margin: 20px 0; padding: 15px; border-left: 3px solid #4A90E2; }
                .footer { background: #f4f4f4; padding: 20px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Halcytone Monthly Update</h1>
                <p>{{ month_year }}</p>
            </div>
            
            {% if breathscape_updates %}
            <div class="section">
                <h2>🫁 Breathscape Updates</h2>
                {% for update in breathscape_updates %}
                    <h3>{{ update.title }}</h3>
                    <p>{{ update.content }}</p>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if hardware_updates %}
            <div class="section">
                <h2>🔧 Hardware Development</h2>
                {% for update in hardware_updates %}
                    <h3>{{ update.title }}</h3>
                    <p>{{ update.content }}</p>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if tips %}
            <div class="section">
                <h2>💡 Breathing Tip</h2>
                {% for tip in tips %}
                    <h3>{{ tip.title }}</h3>
                    <p>{{ tip.content }}</p>
                {% endfor %}
            </div>
            {% endif %}
            
            <div class="footer">
                <h3>Our Vision</h3>
                <p>{{ vision }}</p>
                <p><a href="{{ website_url }}">Visit our website</a></p>
            </div>
        </body>
        </html>
        """
    
    def generate_newsletter(self, content: Dict[str, List[Dict]]) -> Dict[str, str]:
        """Generate email newsletter from categorized content"""
        template = Template(self.email_template)
        
        vision_text = content['vision'][0]['content'] if content['vision'] else ""
        
        html = template.render(
            month_year=datetime.now().strftime("%B %Y"),
            breathscape_updates=content['breathscape'][:2],  # Latest 2
            hardware_updates=content['hardware'][:1],  # Latest 1
            tips=content['tips'][:1],  # Latest tip
            vision=vision_text,
            website_url="https://halcytone.com/updates"
        )
        
        # Generate plain text version
        text = self._html_to_text(html)
        
        # Generate subject line
        subject = f"Halcytone {datetime.now().strftime('%B')} Update: "
        if content['breathscape']:
            subject += content['breathscape'][0]['title'][:30]
        
        return {
            'subject': subject,
            'html': html,
            'text': text
        }
    
    def generate_web_update(self, content: Dict[str, List[Dict]]) -> Dict[str, str]:
        """Generate website blog post from content"""
        # Combine all recent updates into a single post
        title = f"Halcytone Updates - {datetime.now().strftime('%B %Y')}"
        
        # Use markdown for website content
        body = f"# {title}\n\n"
        
        if content['breathscape']:
            body += "## Breathscape Updates\n\n"
            for update in content['breathscape']:
                body += f"### {update['title']}\n{update['content']}\n\n"
        
        if content['hardware']:
            body += "## Hardware Development\n\n"
            for update in content['hardware']:
                body += f"### {update['title']}\n{update['content']}\n\n"
        
        return {
            'title': title,
            'content': body,
            'excerpt': body[:200] + "..."
        }
    
    def generate_social_posts(self, content: Dict[str, List[Dict]]) -> List[Dict[str, str]]:
        """Generate social media snippets"""
        posts = []
        
        # Twitter/X post (280 chars)
        if content['breathscape']:
            update = content['breathscape'][0]
            tweet = f"🫁 {update['title'][:100]}... Read more: halcytone.com/updates"
            posts.append({'platform': 'twitter', 'content': tweet})
        
        # LinkedIn post (longer form)
        if content['hardware']:
            update = content['hardware'][0]
            linkedin = f"Exciting hardware update! {update['title']}\n\n{update['content'][:200]}...\n\n#HealthTech #Breathing #Innovation"
            posts.append({'platform': 'linkedin', 'content': linkedin})
        
        return posts
```

### 4. CRM Integration for Email Distribution

#### CRM Newsletter Endpoint Extension
```python
# Add to CRM Worker (TypeScript) - for reference
"""
// In CRM Worker, add this endpoint:
router.post('/api/v1/notifications/newsletter', async (request, env) => {
    const apiKey = request.headers.get('X-API-Key');
    if (apiKey !== env.CONTENT_GENERATOR_API_KEY) {
        return new Response('Unauthorized', { status: 401 });
    }
    
    const { subject, html, text } = await request.json();
    
    // Get all active subscribers
    const subscribers = await env.DB.prepare(
        'SELECT email FROM users WHERE newsletter_opt_in = 1'
    ).all();
    
    // Use existing EmailNotificationService
    const emailService = new EmailNotificationService(env);
    
    for (const subscriber of subscribers.results) {
        await emailService.sendEmail({
            to: [subscriber.email],
            subject,
            html,
            text
        });
    }
    
    return new Response(JSON.stringify({ sent: subscribers.results.length }));
});
"""
```

#### Python CRM Client
```python
# halcytone_content_generator/services/crm_client.py
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from ..core.resilience import CircuitBreaker

class CRMClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.breaker = CircuitBreaker(failure_threshold=5)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential())
    async def send_newsletter(self, subject: str, html: str, text: str) -> dict:
        """Send newsletter via CRM bulk email endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/notifications/newsletter",
                json={
                    "subject": subject,
                    "html": html,
                    "text": text
                },
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=30.0  # Longer timeout for bulk operations
            )
            response.raise_for_status()
            return response.json()
    
    async def get_subscriber_count(self) -> int:
        """Get count of newsletter subscribers"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/users/subscribers/count",
                headers={"X-API-Key": self.api_key}
            )
            return response.json()["count"]
```

### 5. Platform API Integration for Website Updates

#### Platform Client Implementation
```python
# halcytone_content_generator/services/platform_client.py
import httpx
from datetime import datetime

class PlatformClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
    
    async def publish_update(self, title: str, content: str, excerpt: str) -> dict:
        """Publish content update to website"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/updates",
                json={
                    "title": title,
                    "content": content,
                    "excerpt": excerpt,
                    "published": True,
                    "created_at": datetime.utcnow().isoformat()
                },
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
```

### 6. Main API Endpoints

#### FastAPI Application
```python
# halcytone_content_generator/main.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from .config import Settings
from .services.document_fetcher import DocumentFetcher
from .services.content_assembler import ContentAssembler
from .services.crm_client import CRMClient
from .services.platform_client import PlatformClient
import logging

logger = logging.getLogger(__name__)
app = FastAPI(title="Halcytone Content Generator")

def get_settings():
    return Settings()

@app.post("/generate-content")
async def generate_content(
    background_tasks: BackgroundTasks,
    send_email: bool = True,
    publish_web: bool = True,
    preview_only: bool = False,
    settings: Settings = Depends(get_settings)
):
    """
    Generate and distribute content across all channels
    
    Args:
        send_email: Send newsletter via CRM
        publish_web: Publish to website
        preview_only: Only return preview without sending
    """
    try:
        # Step 1: Fetch living document
        fetcher = DocumentFetcher(
            settings.GOOGLE_CREDENTIALS_JSON,
            settings.LIVING_DOC_ID
        )
        content = await fetcher.fetch_content()
        logger.info(f"Fetched content with {sum(len(v) for v in content.values())} items")
        
        # Step 2: Assemble content
        assembler = ContentAssembler()
        newsletter = assembler.generate_newsletter(content)
        web_update = assembler.generate_web_update(content)
        social_posts = assembler.generate_social_posts(content)
        
        if preview_only:
            return {
                "newsletter": newsletter,
                "web_update": web_update,
                "social_posts": social_posts
            }
        
        results = {}
        
        # Step 3: Send newsletter
        if send_email:
            crm = CRMClient(settings.CRM_BASE_URL, settings.CRM_API_KEY)
            email_result = await crm.send_newsletter(
                newsletter['subject'],
                newsletter['html'],
                newsletter['text']
            )
            results['email'] = email_result
            logger.info(f"Newsletter sent to {email_result.get('sent', 0)} recipients")
        
        # Step 4: Publish to website
        if publish_web:
            platform = PlatformClient(settings.PLATFORM_BASE_URL, settings.PLATFORM_API_KEY)
            web_result = await platform.publish_update(
                web_update['title'],
                web_update['content'],
                web_update['excerpt']
            )
            results['web'] = web_result
            logger.info(f"Web update published: {web_result.get('id')}")
        
        # Step 5: Log social posts for manual handling
        results['social'] = social_posts
        logger.info(f"Generated {len(social_posts)} social media posts")
        
        return {
            "status": "success",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "content-generator"}
```

### 7. Testing Strategy

#### Integration Test Example
```python
# tests/integration/test_content_flow.py
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_content_generation_flow():
    """Test complete content generation and distribution flow"""
    
    # Mock living document content
    mock_content = {
        'breathscape': [{'title': 'Test Update', 'content': 'Test content'}],
        'hardware': [],
        'tips': [{'title': 'Breathing Tip', 'content': 'Breathe deeply'}],
        'vision': [{'content': 'Our vision for better breathing'}]
    }
    
    with patch('document_fetcher.DocumentFetcher.fetch_content', return_value=mock_content):
        with patch('crm_client.CRMClient.send_newsletter', return_value={'sent': 100}):
            with patch('platform_client.PlatformClient.publish_update', return_value={'id': 'update-123'}):
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post("/generate-content")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data['status'] == 'success'
                    assert data['results']['email']['sent'] == 100
                    assert data['results']['web']['id'] == 'update-123'
```

### 8. Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

CMD ["uvicorn", "src.halcytone_content_generator.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

```yaml
# docker-compose.yml addition
services:
  content-generator:
    build: ./halcytone-content-generator
    environment:
      - CRM_BASE_URL=http://crm-worker:8001
      - PLATFORM_BASE_URL=http://platform-api:8000
      - CRM_API_KEY=${CRM_API_KEY}
      - PLATFORM_API_KEY=${PLATFORM_API_KEY}
      - LIVING_DOC_ID=${GOOGLE_DOC_ID}
      - GOOGLE_CREDENTIALS_JSON=${GOOGLE_CREDENTIALS_JSON}
    depends_on:
      - platform-api
      - crm-worker
    ports:
      - "8003:8003"
```

## Implementation Checklist

### Phase 1: Setup & Design ⏳
- [ ] Create Content Generator repository/module
- [ ] Set up living document (Google Doc/Notion)
- [ ] Design content structure and categories
- [ ] Document API contracts with CRM and Platform

### Phase 2: Core Development 🔄
- [ ] Implement document fetcher service
- [ ] Create content assembly logic
- [ ] Build CRM client for email distribution
- [ ] Develop Platform client for web publishing
- [ ] Add social media content generation

### Phase 3: Integration 🔄
- [ ] Extend CRM with newsletter endpoint
- [ ] Add updates API to Platform backend
- [ ] Create updates UI in Next.js frontend
- [ ] Configure service authentication (API keys)
- [ ] Set up correlation ID propagation

### Phase 4: Testing & QA ⏳
- [ ] Unit tests for all components
- [ ] Integration tests with mock services
- [ ] End-to-end testing in staging
- [ ] Content quality review process
- [ ] Performance and load testing

### Phase 5: Deployment ⏳
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Production environment configuration
- [ ] Monitoring and alerting
- [ ] First production newsletter

## Common Pitfalls to Avoid

### Content Generation Pitfalls
- **Never** hardcode content in the service
- **Never** send emails without opt-in verification
- **Never** publish without content review in v1
- **Always** validate living document structure
- **Always** handle partial content gracefully

### Integration Pitfalls  
- **Never** call services without circuit breakers
- **Never** ignore rate limits on email sending
- **Never** expose API keys in logs or responses
- **Always** use correlation IDs for tracing
- **Always** validate API responses

### Testing Pitfalls
- **Never** test with production email lists
- **Never** skip staging environment testing
- **Never** assume content format consistency
- **Always** test with empty/partial content
- **Always** verify email rendering

## Quick Reference Commands

```bash
# Local development
cd halcytone-content-generator
source venv/bin/activate
uvicorn src.halcytone_content_generator.main:app --reload

# Test content generation (preview only)
curl -X POST http://localhost:8003/generate-content?preview_only=true

# Run with Docker Compose
docker-compose up content-generator

# Run tests
pytest tests/ -v --cov

# Check service health
curl http://localhost:8003/health
```

## Success Metrics

Track these metrics for Content Generator success:
- Newsletter delivery rate > 95%
- Content generation time < 30 seconds
- Zero duplicate emails sent
- Website updates published within 1 minute
- Social posts generated for all channels
- Service availability > 99.9%
- Content consistency across channels 100%
- Living document sync reliability 100%

---

**Remember:** The Content Generator is a critical component for consistent communication across all channels. Every implementation decision should prioritize reliability, content quality, and maintainability while following the established microservice patterns of the Halcytone ecosystem.
