# AI Agents Playbook - Halcytone Content Generator

This playbook guides AI agents working on the Halcytone Content Generator service. Follow these instructions precisely to implement the Dry Run System and enhance production readiness.

## Context Loop Discipline (MANDATORY)

Always maintain these fields in `/context/development.md`:

- **Overall goal is:** Implement secure dry run system with complete mock infrastructure
- **Last action was:** What just completed (include commit SHA if applicable)
- **Next action will be:** The immediate next step from current sprint
- **Blockers/Risks:** Security issues, missing mock services, external dependencies

**After every change:**
```bash
git add -A && git commit -m "feat: [component] - description" && git push
bpsai-pair context-sync --last "What you did" --next "Next step" --blockers "Any issues"
```

## 🚨 CRITICAL SECURITY MISSION - Dry Run System Implementation

### IMMEDIATE ACTION REQUIRED: Security Remediation

**COMPROMISED CREDENTIALS DETECTED:**
- Google Docs API: [REDACTED - Key exposed and revoked]
- Notion API: [REDACTED - Token exposed and revoked]

**EXECUTE NOW (0-4 hours):**
```bash
# Hour 1: Revoke and regenerate
# 1. Go to Google Cloud Console and revoke the exposed key
# 2. Go to Notion Integration settings and revoke the token
# 3. Generate new development-only credentials
# 4. Store in secure password manager

# Hour 2-3: Clean repository
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Update .gitignore
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "!.env.example" >> .gitignore

# Create safe template
cp .env .env.example
# Edit .env.example to remove actual values

# Hour 4: Validate
python -m halcytone_content_generator.validate_config
pytest tests/test_configuration.py
```

---

## Dry Run Sprint Implementation Guides

### 🔥 Dry Run Sprint 1: Security Foundation & Emergency Fixes

**Duration:** 1 day | **Priority:** CRITICAL

#### Security Remediation Implementation

```python
# scripts/security_audit.py
import os
import re
from pathlib import Path
from typing import List, Dict

class SecurityAuditor:
    """Audit repository for security issues"""
    
    def __init__(self):
        self.sensitive_patterns = [
            r'AIza[0-9A-Za-z\-_]+',  # Google API keys
            r'ntn_[0-9A-Za-z]+',      # Notion tokens
            r'sk-[a-zA-Z0-9]+',       # OpenAI keys
            r'Bearer\s+[A-Za-z0-9\-._~+/]+',  # Bearer tokens
        ]
        
    def scan_repository(self) -> Dict[str, List[str]]:
        """Scan all files for exposed credentials"""
        findings = {}
        
        for path in Path('.').rglob('*'):
            if path.is_file() and not self.is_ignored(path):
                content = path.read_text(errors='ignore')
                for pattern in self.sensitive_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        findings[str(path)] = matches
                        
        return findings
    
    def is_ignored(self, path: Path) -> bool:
        """Check if path should be ignored"""
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.pytest_cache'}
        return any(part in ignore_dirs for part in path.parts)

# Run the audit
if __name__ == "__main__":
    auditor = SecurityAuditor()
    findings = auditor.scan_repository()
    
    if findings:
        print("⚠️ SECURITY ISSUES FOUND:")
        for file, keys in findings.items():
            print(f"  File: {file}")
            for key in keys:
                print(f"    - {key[:10]}...")
    else:
        print("✅ No exposed credentials found")
```

#### Environment Configuration Template

```python
# .env.example
# Halcytone Content Generator - Environment Configuration Template
# Copy this file to .env and fill in your actual values

# API Keys (NEVER commit actual keys)
GOOGLE_DOCS_API_KEY=your_google_docs_api_key_here
GOOGLE_DOCS_SERVICE_ACCOUNT_JSON=path/to/service-account.json
NOTION_API_TOKEN=your_notion_integration_token_here
OPENAI_API_KEY=your_openai_api_key_here

# Service Endpoints
CRM_API_URL=http://localhost:8001
PLATFORM_API_URL=http://localhost:8002

# Feature Flags
DRY_RUN_MODE=true
USE_MOCK_SERVICES=true
ENABLE_MONITORING=false

# Security
API_KEY_ENCRYPTION_KEY=generate_a_secure_key_here
JWT_SECRET_KEY=generate_another_secure_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost/halcytone

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Monitoring (optional)
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

---

### Dry Run Sprint 2: Mock Service Infrastructure

**Duration:** 1-2 days | **Priority:** HIGH

#### Mock CRM Service Implementation

```python
# mocks/crm_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

app = FastAPI(title="Mock CRM Service", version="1.0.0")

class EmailRequest(BaseModel):
    subject: str
    html_content: str
    text_content: str
    recipients: Optional[List[str]] = None
    campaign_id: Optional[str] = None

class EmailResponse(BaseModel):
    message_id: str
    status: str
    recipients_count: int
    timestamp: datetime

@app.post("/api/v1/email/send", response_model=EmailResponse)
async def send_email(request: EmailRequest):
    """Simulate email sending"""
    
    # Simulate various scenarios
    if "error" in request.subject.lower():
        raise HTTPException(status_code=500, detail="Simulated CRM error")
    
    if "slow" in request.subject.lower():
        import asyncio
        await asyncio.sleep(2)  # Simulate slow response
    
    return EmailResponse(
        message_id=str(uuid.uuid4()),
        status="sent",
        recipients_count=len(request.recipients) if request.recipients else 100,
        timestamp=datetime.utcnow()
    )

@app.get("/api/v1/contacts/count")
async def get_contact_count():
    """Simulate contact count endpoint"""
    return {"total": 5432, "active": 4821, "unsubscribed": 611}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "mock-crm"}
```

#### Mock Platform Service Implementation

```python
# mocks/platform_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

app = FastAPI(title="Mock Platform Service", version="1.0.0")

class ContentPublishRequest(BaseModel):
    title: str
    content: str
    content_type: str
    metadata: Optional[Dict[str, Any]] = {}

class ContentPublishResponse(BaseModel):
    content_id: str
    url: str
    status: str
    published_at: datetime

@app.post("/api/v1/content/publish", response_model=ContentPublishResponse)
async def publish_content(request: ContentPublishRequest):
    """Simulate content publishing"""
    
    # Simulate various scenarios
    if "draft" in request.title.lower():
        status = "draft"
    elif "error" in request.title.lower():
        raise HTTPException(status_code=400, detail="Invalid content format")
    else:
        status = "published"
    
    content_id = str(uuid.uuid4())
    
    return ContentPublishResponse(
        content_id=content_id,
        url=f"https://halcytone.com/content/{content_id}",
        status=status,
        published_at=datetime.utcnow()
    )

@app.get("/api/v1/analytics/content/{content_id}")
async def get_content_analytics(content_id: str):
    """Simulate analytics data"""
    return {
        "content_id": content_id,
        "views": 1234,
        "engagement_rate": 0.045,
        "avg_time_on_page": 180
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "mock-platform"}
```

#### Docker Compose for Mock Services

```yaml
# docker-compose.mocks.yml
version: '3.8'

services:
  mock-crm:
    build:
      context: ./mocks
      dockerfile: Dockerfile.crm
    ports:
      - "8001:8001"
    environment:
      - SERVICE_NAME=mock-crm
      - LOG_LEVEL=INFO
    volumes:
      - ./mocks/logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mock-platform:
    build:
      context: ./mocks
      dockerfile: Dockerfile.platform
    ports:
      - "8002:8002"
    environment:
      - SERVICE_NAME=mock-platform
      - LOG_LEVEL=INFO
    volumes:
      - ./mocks/logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mock-logger:
    image: busybox
    volumes:
      - ./mocks/logs:/logs
    command: tail -f /logs/*.log

networks:
  default:
    name: halcytone-mocks
```

---

### Dry Run Sprint 3: Validation & Testing

**Duration:** 2 days | **Priority:** HIGH

#### Dry Run Validation Script

```bash
#!/bin/bash
# scripts/validate-dry-run.sh

echo "🚀 Starting Dry Run Validation..."

# Check environment
if [ "$DRY_RUN_MODE" != "true" ]; then
    echo "❌ Error: DRY_RUN_MODE not enabled"
    exit 1
fi

# Start mock services
docker-compose -f docker-compose.mocks.yml up -d
sleep 5

# Run validation tests
echo "📋 Running validation suite..."

# Test 1: No external API calls
echo "Test 1: Checking for external API calls..."
python -m pytest tests/dry_run/test_no_external_calls.py -v

# Test 2: Content generation pipeline
echo "Test 2: Testing content generation..."
python -m pytest tests/dry_run/test_content_generation.py -v

# Test 3: Multi-channel publishing
echo "Test 3: Testing multi-channel publishing..."
python -m pytest tests/dry_run/test_publishing.py -v

# Test 4: Performance benchmarks
echo "Test 4: Running performance tests..."
python -m pytest tests/dry_run/test_performance.py -v

# Test 5: Error handling
echo "Test 5: Testing error scenarios..."
python -m pytest tests/dry_run/test_error_handling.py -v

# Generate report
python scripts/generate_test_report.py

echo "✅ Dry Run Validation Complete!"
```

#### Dry Run Test Suite

```python
# tests/dry_run/test_no_external_calls.py
import pytest
from unittest.mock import patch, MagicMock
import socket

class TestNoExternalCalls:
    """Ensure no external API calls in dry run mode"""
    
    @patch('socket.socket.connect')
    def test_no_external_connections(self, mock_connect):
        """Verify no external connections are made"""
        
        # Configure to raise on external connection attempts
        def check_connection(address):
            host, port = address
            allowed_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
            if host not in allowed_hosts:
                raise Exception(f"External connection attempted to {host}:{port}")
        
        mock_connect.side_effect = check_connection
        
        # Run content generation
        from halcytone_content_generator import generate_content
        content = generate_content(dry_run=True)
        
        # Should complete without external calls
        assert content is not None
        assert content.get('dry_run') == True
```

---

### Dry Run Sprint 4: Monitoring & Observability

**Duration:** 1-2 days | **Priority:** MEDIUM

#### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'content-generator'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'mock-crm'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/metrics'

  - job_name: 'mock-platform'
    static_configs:
      - targets: ['localhost:8002']
    metrics_path: '/metrics'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - 'alerts.yml'
```

#### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Halcytone Dry Run Monitor",
    "panels": [
      {
        "title": "Dry Run Mode Status",
        "type": "stat",
        "targets": [
          {
            "expr": "dry_run_mode_enabled",
            "legendFormat": "Status"
          }
        ]
      },
      {
        "title": "Mock Service Health",
        "type": "graph",
        "targets": [
          {
            "expr": "up{job=~\"mock-.*\"}",
            "legendFormat": "{{job}}"
          }
        ]
      },
      {
        "title": "Content Generation Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "content_generation_duration_seconds",
            "legendFormat": "Generation Time"
          }
        ]
      },
      {
        "title": "External API Calls Blocked",
        "type": "counter",
        "targets": [
          {
            "expr": "external_api_calls_blocked_total",
            "legendFormat": "Blocked Calls"
          }
        ]
      }
    ]
  }
}
```

---

### Dry Run Sprint 5: Documentation & Production Readiness

**Duration:** 1-2 days | **Priority:** MEDIUM

#### Dry Run Operations Guide

```markdown
# docs/dry-run-guide.md

## Dry Run System Overview

The Halcytone Content Generator Dry Run System provides a complete testing environment with zero external dependencies.

### Key Features
- Complete mock service infrastructure
- Request/response logging
- Performance monitoring
- Error simulation capabilities

### Starting Dry Run Mode

1. Set environment variable:
   ```bash
   export DRY_RUN_MODE=true
   export USE_MOCK_SERVICES=true
   ```

2. Start mock services:
   ```bash
   docker-compose -f docker-compose.mocks.yml up
   ```

3. Start content generator:
   ```bash
   uvicorn main:app --reload --env-file .env.dry-run
   ```

### Validation Checklist
- [ ] All mock services healthy
- [ ] No external API calls detected
- [ ] Content generation <2s
- [ ] Error handling functional
- [ ] Monitoring dashboards active

### Common Issues & Solutions

**Issue:** Mock services not responding
**Solution:** Check Docker logs: `docker-compose logs mock-crm`

**Issue:** External API calls detected
**Solution:** Verify DRY_RUN_MODE=true in environment

**Issue:** Slow performance
**Solution:** Check mock service response times in Grafana
```

---

## Common Pitfalls to Avoid

### Security Pitfalls
- **NEVER** commit .env files
- **ALWAYS** use .env.example templates
- **ALWAYS** rotate keys after exposure
- **NEVER** log sensitive data

### Mock Service Pitfalls
- **NEVER** connect to real APIs in dry run
- **ALWAYS** validate mock responses match contracts
- **ALWAYS** simulate error scenarios
- **NEVER** skip health checks

### Testing Pitfalls
- **NEVER** assume mocks are running
- **ALWAYS** verify dry run mode is active
- **ALWAYS** test timeout scenarios
- **NEVER** skip performance validation

---

## Quick Reference Commands

```bash
# Security Audit
python scripts/security_audit.py
git secrets --scan

# Mock Services
docker-compose -f docker-compose.mocks.yml up -d
curl http://localhost:8001/health
curl http://localhost:8002/health

# Dry Run Validation
export DRY_RUN_MODE=true
./scripts/validate-dry-run.sh

# Monitoring
docker-compose -f docker-compose.monitoring.yml up -d
open http://localhost:3000  # Grafana

# Testing
pytest tests/dry_run/ -v --cov
python scripts/performance_test.py
```

---

## Success Metrics Per Sprint

### Dry Run Sprint 1 (Security)
- Zero exposed credentials in repository ✓
- All services start with new credentials ✓
- Security scan passes ✓

### Dry Run Sprint 2 (Mocks)
- All mock services respond within 100ms ✓
- 100% API contract compliance ✓
- Complete request logging ✓

### Dry Run Sprint 3 (Validation)
- 100% core workflow test coverage ✓
- Content generation <2s ✓
- Zero external API calls in dry run ✓

### Dry Run Sprint 4 (Monitoring)
- All services visible in dashboards ✓
- Alert coverage for critical paths ✓
- Log retention configured ✓

### Dry Run Sprint 5 (Documentation)
- Complete runbook coverage ✓
- Team sign-off on procedures ✓
- Successful dry run demonstration ✓

---

**Remember:** Security is paramount. Fix exposed credentials immediately before proceeding with any other work. The dry run system ensures safe testing without risking production data or external service dependencies.
