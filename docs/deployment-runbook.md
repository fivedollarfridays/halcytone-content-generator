# Production Deployment Runbook

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Environments](#deployment-environments)
3. [Deployment Process](#deployment-process)
4. [Configuration Management](#configuration-management)
5. [Health Checks](#health-checks)
6. [Rollback Procedures](#rollback-procedures)
7. [Monitoring & Alerts](#monitoring--alerts)
8. [Troubleshooting](#troubleshooting)
9. [Emergency Procedures](#emergency-procedures)

---

## Pre-Deployment Checklist

### Code Quality Gates
- [ ] All tests passing (>70% coverage)
- [ ] No critical security vulnerabilities
- [ ] Code review approved by 2+ reviewers
- [ ] Performance benchmarks met (<2s batch generation)
- [ ] Documentation updated
- [ ] API contracts verified

### Infrastructure Requirements
- [ ] Docker images built and tagged
- [ ] Database migrations prepared
- [ ] SSL certificates valid (>30 days)
- [ ] CDN configuration verified
- [ ] Load balancer health checks configured
- [ ] Backup systems operational

### External Dependencies
- [ ] Google Docs API credentials valid
- [ ] Notion API token active
- [ ] CRM integration tested
- [ ] Email service quotas sufficient
- [ ] Social media API limits checked
- [ ] OpenAI API credits available

---

## Deployment Environments

### Development
```yaml
Environment: development
URL: https://dev.content.halcytone.com
Branch: develop
Auto-deploy: Yes
Database: PostgreSQL (dev-db.halcytone.internal)
```

### Staging
```yaml
Environment: staging
URL: https://staging.content.halcytone.com
Branch: staging
Auto-deploy: No (manual approval)
Database: PostgreSQL (staging-db.halcytone.internal)
```

### Production
```yaml
Environment: production
URL: https://content.halcytone.com
Branch: main
Auto-deploy: No (manual deployment)
Database: PostgreSQL (prod-db.halcytone.internal)
```

---

## Deployment Process

### 1. Build & Test Phase

```bash
# Step 1: Pull latest code
git checkout main
git pull origin main

# Step 2: Install dependencies
pip install -r requirements.txt

# Step 3: Run tests
pytest tests/ --cov=src --cov-report=term-missing
# Ensure coverage > 70%

# Step 4: Build Docker image
docker build -t halcytone-content-generator:v1.0.0 .

# Step 5: Run security scan
docker scan halcytone-content-generator:v1.0.0

# Step 6: Tag image
docker tag halcytone-content-generator:v1.0.0 \
  registry.halcytone.com/content-generator:v1.0.0

# Step 7: Push to registry
docker push registry.halcytone.com/content-generator:v1.0.0
```

### 2. Database Migration

```bash
# Step 1: Backup current database
pg_dump -h prod-db.halcytone.internal -U postgres -d content_db \
  > backup_$(date +%Y%m%d_%H%M%S).sql

# Step 2: Test migrations on staging
alembic upgrade head --sql > migration.sql
psql -h staging-db.halcytone.internal -U postgres -d content_db < migration.sql

# Step 3: Verify migration
python scripts/verify_migration.py --env staging

# Step 4: Apply to production (during maintenance window)
alembic upgrade head
```

### 3. Application Deployment

#### Blue-Green Deployment Strategy

```bash
# Step 1: Deploy to Green environment
kubectl apply -f k8s/deployment-green.yaml

# Step 2: Wait for pods to be ready
kubectl wait --for=condition=ready pod \
  -l app=content-generator,version=green \
  --timeout=300s

# Step 3: Run smoke tests
python scripts/smoke_tests.py --env green

# Step 4: Switch traffic to Green
kubectl patch service content-generator -p \
  '{"spec":{"selector":{"version":"green"}}}'

# Step 5: Monitor for 15 minutes
python scripts/monitor_deployment.py --duration 900

# Step 6: If successful, scale down Blue
kubectl scale deployment content-generator-blue --replicas=0
```

### 4. Post-Deployment Verification

```bash
# Health check
curl -X GET https://content.halcytone.com/health

# API verification
python scripts/api_verification.py --env production

# Content generation test
curl -X POST https://content.halcytone.com/api/v2/generate-content \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @test_payload.json

# Cache warming
python scripts/cache_warmer.py --env production

# Performance validation
python scripts/performance_test.py --env production
```

---

## Configuration Management

### Environment Variables

```bash
# Core Settings
ENVIRONMENT=production
APP_NAME=halcytone-content-generator
LOG_LEVEL=INFO
DEBUG=false

# Database
DATABASE_URL=postgresql://user:pass@prod-db.halcytone.internal:5432/content_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis Cache
REDIS_URL=redis://prod-redis.halcytone.internal:6379/0
REDIS_MAX_CONNECTIONS=50

# API Keys (stored in secrets manager)
GOOGLE_CREDENTIALS_JSON=${SECRET_GOOGLE_CREDS}
NOTION_API_KEY=${SECRET_NOTION_KEY}
OPENAI_API_KEY=${SECRET_OPENAI_KEY}

# Service URLs
CRM_SERVICE_URL=https://crm.halcytone.com
PLATFORM_API_URL=https://api.halcytone.com

# Performance
WORKER_COUNT=4
WORKER_CLASS=uvicorn.workers.UvicornWorker
WORKER_CONNECTIONS=1000
TIMEOUT=30

# Features
CACHE_ENABLED=true
RATE_LIMITING_ENABLED=true
TONE_SYSTEM_ENABLED=true
DRY_RUN=false
```

### Secrets Management

```yaml
# Using HashiCorp Vault
vault:
  address: https://vault.halcytone.internal
  namespace: production
  secrets:
    - path: secret/content-generator/google
      key: GOOGLE_CREDENTIALS_JSON
    - path: secret/content-generator/notion
      key: NOTION_API_KEY
    - path: secret/content-generator/openai
      key: OPENAI_API_KEY
    - path: secret/content-generator/database
      key: DATABASE_PASSWORD
```

---

## Health Checks

### Application Health

```python
# Endpoint: GET /health
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2025-01-24T10:00:00Z",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "google_docs": "ok",
    "notion": "ok"
  }
}

# Endpoint: GET /ready
{
  "ready": true,
  "initialized": true,
  "dependencies": {
    "database": true,
    "cache": true,
    "external_apis": true
  }
}
```

### Monitoring Script

```python
#!/usr/bin/env python3
# scripts/health_monitor.py

import requests
import time
import sys

def check_health(url):
    try:
        response = requests.get(f"{url}/health", timeout=5)
        data = response.json()

        if data["status"] != "healthy":
            return False, f"Unhealthy status: {data}"

        for service, status in data["checks"].items():
            if status != "ok":
                return False, f"Service {service} is not ok"

        return True, "All systems operational"

    except Exception as e:
        return False, f"Health check failed: {str(e)}"

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://content.halcytone.com"

    while True:
        healthy, message = check_health(url)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

        if not healthy:
            # Send alert
            requests.post("https://alerts.halcytone.com/webhook",
                         json={"severity": "critical", "message": message})

        time.sleep(30)
```

---

## Rollback Procedures

### Immediate Rollback (< 5 minutes)

```bash
# Step 1: Switch traffic back to Blue
kubectl patch service content-generator -p \
  '{"spec":{"selector":{"version":"blue"}}}'

# Step 2: Verify Blue is serving traffic
curl -I https://content.halcytone.com/health

# Step 3: Scale down Green
kubectl scale deployment content-generator-green --replicas=0

# Step 4: Tag failed deployment
git tag -a "failed-$(date +%Y%m%d-%H%M%S)" -m "Failed deployment"
git push origin --tags
```

### Database Rollback

```bash
# Step 1: Stop application
kubectl scale deployment content-generator --replicas=0

# Step 2: Restore database backup
psql -h prod-db.halcytone.internal -U postgres -c "DROP DATABASE content_db;"
psql -h prod-db.halcytone.internal -U postgres -c "CREATE DATABASE content_db;"
psql -h prod-db.halcytone.internal -U postgres -d content_db < backup_latest.sql

# Step 3: Rollback migrations
alembic downgrade -1

# Step 4: Deploy previous version
kubectl set image deployment/content-generator \
  content-generator=registry.halcytone.com/content-generator:v0.9.9

# Step 5: Scale up application
kubectl scale deployment content-generator --replicas=4
```

---

## Monitoring & Alerts

### Key Metrics

```yaml
Application Metrics:
  - Request rate (req/sec)
  - Response time (p50, p95, p99)
  - Error rate (4xx, 5xx)
  - Active connections
  - Memory usage
  - CPU usage

Business Metrics:
  - Content generated per hour
  - Email send rate
  - Social posts published
  - Cache hit rate
  - API usage by endpoint

Infrastructure Metrics:
  - Pod restarts
  - Node CPU/Memory
  - Database connections
  - Redis memory usage
  - Disk I/O
  - Network latency
```

### Alert Configuration

```yaml
# Prometheus Alert Rules
groups:
  - name: content_generator
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for 5 minutes"

      - alert: SlowResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow response times"
          description: "95th percentile response time > 2s"

      - alert: DatabaseConnectionPoolExhausted
        expr: database_connections_used / database_connections_max > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "Over 90% of database connections in use"
```

### Logging

```python
# Structured logging configuration
LOGGING = {
    'version': 1,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'json',
            'filename': '/var/log/content-generator/app.log',
            'maxBytes': 104857600,  # 100MB
            'backupCount': 10
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
}
```

---

## Troubleshooting

### Common Issues

#### 1. High Memory Usage
```bash
# Check memory usage
kubectl top pods -l app=content-generator

# Get heap dump
kubectl exec -it content-generator-xxx -- python -m memory_profiler

# Restart with increased memory
kubectl set resources deployment/content-generator \
  --limits=memory=4Gi --requests=memory=2Gi
```

#### 2. Database Connection Issues
```bash
# Check connection pool
psql -h prod-db.halcytone.internal -U postgres -c \
  "SELECT count(*) FROM pg_stat_activity WHERE application_name='content-generator';"

# Kill idle connections
psql -h prod-db.halcytone.internal -U postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE state='idle' AND state_change < NOW() - INTERVAL '10 minutes';"

# Increase pool size
kubectl set env deployment/content-generator DATABASE_POOL_SIZE=40
```

#### 3. Cache Issues
```bash
# Clear Redis cache
redis-cli -h prod-redis.halcytone.internal FLUSHDB

# Check Redis memory
redis-cli -h prod-redis.halcytone.internal INFO memory

# Restart Redis if needed
kubectl rollout restart statefulset/redis
```

#### 4. API Rate Limiting
```bash
# Check current limits
curl -I https://content.halcytone.com/api/v2/generate-content

# Temporarily increase limits
kubectl set env deployment/content-generator RATE_LIMIT_PER_MINUTE=1000

# Monitor rate limit hits
kubectl logs -f deployment/content-generator | grep "rate_limit"
```

### Debug Mode

```bash
# Enable debug logging
kubectl set env deployment/content-generator LOG_LEVEL=DEBUG DEBUG=true

# Stream logs
kubectl logs -f deployment/content-generator --tail=100

# Interactive debugging
kubectl exec -it content-generator-xxx -- python
>>> from src.halcytone_content_generator import app
>>> app.debug_info()
```

---

## Emergency Procedures

### Complete Service Outage

```bash
#!/bin/bash
# emergency_recovery.sh

echo "=== EMERGENCY RECOVERY INITIATED ==="

# Step 1: Switch to disaster recovery site
kubectl config use-context dr-cluster
kubectl apply -f k8s/dr-deployment.yaml

# Step 2: Update DNS to point to DR
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456 \
  --change-batch file://dr-dns-change.json

# Step 3: Notify stakeholders
python scripts/send_alerts.py --severity critical \
  --message "Service switched to DR site"

# Step 4: Start recovery of primary site
./recover_primary.sh &

echo "=== DR SITE ACTIVE ==="
```

### Data Corruption Recovery

```bash
# Step 1: Stop all writes
kubectl set env deployment/content-generator READ_ONLY=true

# Step 2: Identify corruption extent
python scripts/data_integrity_check.py

# Step 3: Restore from last known good backup
./restore_from_backup.sh --timestamp "2025-01-24 00:00:00"

# Step 4: Replay transaction logs
python scripts/replay_transactions.py --from "2025-01-24 00:00:00"

# Step 5: Verify data integrity
python scripts/data_integrity_check.py --full

# Step 6: Resume normal operations
kubectl set env deployment/content-generator READ_ONLY=false
```

### Security Breach Response

```bash
# Step 1: Isolate affected systems
kubectl label nodes affected-node quarantine=true
kubectl taint nodes affected-node quarantine=true:NoSchedule

# Step 2: Rotate all credentials
python scripts/rotate_credentials.py --all

# Step 3: Enable enhanced logging
kubectl set env deployment/content-generator \
  SECURITY_AUDIT_MODE=true \
  LOG_ALL_REQUESTS=true

# Step 4: Deploy with security patches
kubectl set image deployment/content-generator \
  content-generator=registry.halcytone.com/content-generator:security-patch

# Step 5: Audit all recent activities
python scripts/security_audit.py --days 7
```

---

## Maintenance Windows

### Scheduled Maintenance

```yaml
Regular Maintenance:
  Schedule: Every Sunday 2:00 AM - 4:00 AM EST
  Notifications: 72 hours in advance
  Tasks:
    - Database optimization
    - Index rebuilding
    - Log rotation
    - Certificate renewal
    - Security patches

Emergency Maintenance:
  Notification: Minimum 1 hour (critical: immediate)
  Approval: VP Engineering or CTO
  Communication:
    - Status page update
    - Email to affected users
    - Slack announcement
```

### Maintenance Mode

```bash
# Enable maintenance mode
kubectl apply -f k8s/maintenance-page.yaml
kubectl patch service content-generator -p \
  '{"spec":{"selector":{"app":"maintenance"}}}'

# Perform maintenance tasks
./maintenance_tasks.sh

# Disable maintenance mode
kubectl patch service content-generator -p \
  '{"spec":{"selector":{"app":"content-generator"}}}'
kubectl delete -f k8s/maintenance-page.yaml
```

---

## Contact Information

### Escalation Path

1. **Level 1**: On-call Engineer
   - PagerDuty: content-generator-oncall
   - Response time: 5 minutes

2. **Level 2**: Team Lead
   - Slack: #content-gen-emergency
   - Phone: +1-555-LEAD-001
   - Response time: 15 minutes

3. **Level 3**: Engineering Manager
   - Email: eng-manager@halcytone.com
   - Phone: +1-555-MGR-001
   - Response time: 30 minutes

4. **Level 4**: VP Engineering / CTO
   - Direct phone (emergency only)
   - Response time: 1 hour

### External Dependencies

- **Google Cloud Support**: support.google.com/cloud
- **AWS Support**: console.aws.amazon.com/support
- **Notion API**: developers.notion.com
- **OpenAI Support**: help.openai.com

---

## Appendix

### Deployment Checklist Template

```markdown
## Deployment: v[VERSION] - [DATE]

**Deployer**: [NAME]
**Ticket**: [JIRA-123]

### Pre-Deployment
- [ ] Code review completed
- [ ] Tests passing
- [ ] Database backup taken
- [ ] Stakeholders notified

### Deployment
- [ ] Blue environment deployed
- [ ] Health checks passing
- [ ] Smoke tests completed
- [ ] Traffic switched

### Post-Deployment
- [ ] Monitoring verified
- [ ] Performance validated
- [ ] Documentation updated
- [ ] Team notified

### Notes
[Any special considerations or issues]
```

---

*Last Updated: January 2025 | Version 1.0 | Sprint 5*