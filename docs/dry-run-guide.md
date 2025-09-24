# Halcytone Content Generator - Dry Run System Guide

## Overview

The Halcytone Content Generator dry run system provides complete isolation from external APIs while maintaining full functionality through mock services. This guide covers operation, deployment, and management of the dry run infrastructure.

**Version:** Sprint 5 - Documentation & Production Readiness
**Last Updated:** 2025-01-24
**Status:** Production Ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Architecture](#system-architecture)
3. [Deployment](#deployment)
4. [Configuration](#configuration)
5. [Operation](#operation)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Security](#security)
9. [Performance](#performance)
10. [Maintenance](#maintenance)

---

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.11+ for direct service execution
- 8GB RAM recommended for full stack

### 30-Second Launch
```bash
# 1. Clone and navigate to project
cd halcytone-content-generator

# 2. Start mock services (required for dry run)
python mocks/crm_service.py &
python mocks/platform_service.py &

# 3. Start main application in dry run mode
export DRY_RUN_MODE=true
export USE_MOCK_SERVICES=true
python -m uvicorn src.halcytone_content_generator.main:app --host 0.0.0.0 --port 8000

# 4. Optional: Start monitoring stack
./scripts/start-monitoring.sh
```

### Verification
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/health  # Mock CRM
curl http://localhost:8002/health  # Mock Platform

# Test dry run content generation
curl -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{"preview_only": true}'
```

---

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                  Dry Run Architecture                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │  Content Gen    │    │   Mock Services │            │
│  │  (Port 8000)    │◄──►│  CRM: 8001      │            │
│  │                 │    │  Platform: 8002 │            │
│  │ DRY_RUN_MODE=1  │    │                 │            │
│  └─────────────────┘    └─────────────────┘            │
│           ▲                       ▲                     │
│           │                       │                     │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │   Monitoring    │    │  Log Aggregation│            │
│  │  (Port 3000)    │    │  Loki: 3100     │            │
│  │ Grafana/Prom    │    │  Promtail       │            │
│  └─────────────────┘    └─────────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Key Features
- **Complete API Isolation**: No external API calls in dry run mode
- **Mock Service Simulation**: Realistic CRM and Platform responses
- **Real-time Monitoring**: Full observability with Grafana dashboards
- **Error Simulation**: Configurable failure scenarios for testing
- **Performance Matching**: Mock services match real API performance

### Data Flow
1. **Request Reception**: Content generation requests received
2. **Dry Run Detection**: System checks `DRY_RUN_MODE` setting
3. **Mock Routing**: Publishers route to mock services (ports 8001/8002)
4. **Response Simulation**: Mock services return realistic responses
5. **Monitoring**: All operations tracked in Prometheus/Grafana

---

## Deployment

### Environment Setup

#### Required Environment Variables
```bash
# Core Configuration
DRY_RUN_MODE=true                    # Enable dry run mode
USE_MOCK_SERVICES=true              # Route to mock services
SERVICE_NAME="halcytone-dry-run"    # Service identification

# Security (Use secure values in production)
API_KEY_ENCRYPTION_KEY="production-encryption-key-2025"
JWT_SECRET_KEY="production-jwt-secret-2025"

# Optional Configuration
BATCH_DRY_RUN=true                  # Enable batch dry run
LOG_LEVEL=INFO                      # Logging level
MONITORING_ENABLED=true             # Enable metrics collection
```

#### Configuration File (`.env`)
```ini
# Halcytone Content Generator - Dry Run Configuration

# === CORE SETTINGS ===
DRY_RUN_MODE=true
USE_MOCK_SERVICES=true
SERVICE_NAME=halcytone-dry-run

# === MOCK SERVICE ENDPOINTS ===
MOCK_CRM_BASE_URL=http://localhost:8001
MOCK_PLATFORM_BASE_URL=http://localhost:8002

# === SECURITY ===
API_KEY_ENCRYPTION_KEY=production-encryption-key-2025
JWT_SECRET_KEY=production-jwt-secret-2025

# === PERFORMANCE ===
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
RATE_LIMIT_PER_MINUTE=1000

# === MONITORING ===
MONITORING_ENABLED=true
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
```

### Deployment Methods

#### Method 1: Docker Compose (Recommended)
```bash
# Full stack deployment
docker-compose -f docker-compose.yml up -d
docker-compose -f docker-compose.monitoring.yml up -d

# Verify deployment
docker-compose ps
curl http://localhost:8000/health
```

#### Method 2: Manual Service Startup
```bash
# Start mock services
python mocks/crm_service.py &
python mocks/platform_service.py &

# Start main application
export DRY_RUN_MODE=true
export USE_MOCK_SERVICES=true
python -m uvicorn src.halcytone_content_generator.main:app --host 0.0.0.0 --port 8000 &

# Start monitoring (optional)
./scripts/start-monitoring.sh
```

#### Method 3: Production Deployment
```bash
# Using provided deployment script
./scripts/deploy-dry-run.sh production

# Or with specific configuration
./scripts/deploy-dry-run.sh production --config production.env --monitoring
```

---

## Configuration

### Dry Run Mode Configuration

#### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `DRY_RUN_MODE` | `false` | Master dry run toggle |
| `USE_MOCK_SERVICES` | `false` | Route to mock services |
| `BATCH_DRY_RUN` | `false` | Enable batch operation dry run |
| `MOCK_CRM_BASE_URL` | `http://localhost:8001` | Mock CRM endpoint |
| `MOCK_PLATFORM_BASE_URL` | `http://localhost:8002` | Mock Platform endpoint |

#### Publisher Configuration
Publishers automatically detect dry run mode and route accordingly:

```python
# Email Publisher (CRM Integration)
if self.dry_run_mode and self.use_mock_services:
    self.base_url = "http://localhost:8001"  # Mock CRM

# Web Publisher (Platform Integration)
if self.dry_run_mode and self.use_mock_services:
    self.base_url = "http://localhost:8002"  # Mock Platform
```

### Mock Service Configuration

#### CRM Mock Service (Port 8001)
- **Health Endpoint**: `GET /health`
- **Email Sending**: `POST /api/v1/email/send`
- **Contact Management**: `POST /api/v1/contacts`
- **Campaign Creation**: `POST /api/v1/campaigns`
- **Subscriber Lists**: `GET /api/v1/users/subscribers`

#### Platform Mock Service (Port 8002)
- **Health Endpoint**: `GET /health`
- **Content Publishing**: `POST /api/v1/content/publish`
- **Social Media**: `POST /api/v1/social/post`
- **Analytics**: `GET /api/v1/analytics`

### Monitoring Configuration

#### Grafana Dashboards
- **Service Overview**: Real-time service health and performance
- **Mock Services**: Specialized monitoring for mock infrastructure
- **Dry Run Indicators**: Visual confirmation of dry run mode

#### Alert Configuration
- **Service Health**: Monitor main application and mock services
- **Performance**: Response time and error rate monitoring
- **Business Logic**: Content generation and processing alerts

---

## Operation

### Daily Operations

#### Morning Checklist
1. **Health Check**: Verify all services are running
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8001/health
   curl http://localhost:8002/health
   ```

2. **Monitoring Review**: Check Grafana dashboards
   - Service Overview: http://localhost:3000/d/halcytone-overview
   - Mock Services: http://localhost:3000/d/mock-services

3. **Log Review**: Check for any errors or warnings
   ```bash
   docker-compose logs --tail=50 halcytone-content-generator
   ```

#### Content Generation Testing
```bash
# Test email generation
curl -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{"send_email": true, "preview_only": true}'

# Test web publishing
curl -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{"publish_web": true, "preview_only": true}'

# Test social media
curl -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{"generate_social": true, "preview_only": true}'
```

### Error Scenarios Testing

#### Simulated Failures
Mock services support error simulation for testing resilience:

```bash
# Simulate CRM service failure
curl -X POST http://localhost:8001/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{"subject": "error test", "html_content": "test"}'

# Simulate timeout
curl -X POST http://localhost:8001/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{"subject": "slow test", "html_content": "test"}'

# Simulate validation error
curl -X POST http://localhost:8002/api/v1/content/publish \
  -H "Content-Type: application/json" \
  -d '{"title": "invalid test", "content": "test"}'
```

### Performance Testing

#### Load Testing
```bash
# Using curl for basic load testing
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/v2/generate-content \
    -H "Content-Type: application/json" \
    -d '{"preview_only": true}' &
done

# Monitor response times in Grafana
# Expected: <2s for 95th percentile
```

#### Capacity Planning
- **Concurrent Requests**: 100 (configurable via `MAX_CONCURRENT_REQUESTS`)
- **Memory Usage**: ~512MB per service under normal load
- **CPU Usage**: <50% under normal load
- **Response Time**: <2s for content generation (95th percentile)

---

## Monitoring

### Key Metrics

#### Service Health
- **Uptime**: Service availability percentage
- **Response Time**: 50th, 95th, 99th percentiles
- **Error Rate**: HTTP 5xx errors per minute
- **Request Rate**: Requests per second

#### Business Metrics
- **Content Generated**: Total content pieces generated
- **Emails Sent**: Total emails processed (via mock CRM)
- **Web Published**: Total web content published (via mock Platform)
- **Social Posts**: Total social media posts created

#### System Resources
- **CPU Usage**: System CPU utilization
- **Memory Usage**: RAM consumption
- **Disk I/O**: File system operations
- **Network I/O**: Network traffic

### Alerting

#### Critical Alerts
- Service downtime (immediate notification)
- High error rate (>5% for 2+ minutes)
- Critical response time (>5s for 2+ minutes)
- Memory exhaustion (>95% for 5+ minutes)

#### Warning Alerts
- Mock service downtime
- High response time (>2s for 5+ minutes)
- High resource usage (>80% CPU, >85% memory)
- Dry run mode disabled (immediate notification)

### Dashboards

#### Service Overview Dashboard
- Real-time service health status
- Request rate and response time graphs
- Resource utilization monitoring
- **Dry Run Mode Indicator** (key feature)
- Content generation operation counters

#### Mock Services Dashboard
- Mock CRM service performance
- Mock Platform service performance
- Mock service operation counters
- Error rate monitoring for mock endpoints

---

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check port conflicts
netstat -tulpn | grep :8000
netstat -tulpn | grep :8001
netstat -tulpn | grep :8002

# Check configuration
python -c "from src.halcytone_content_generator.config import get_settings; print(get_settings())"

# Check dependencies
pip install -r requirements.txt
```

#### Mock Services Not Responding
```bash
# Check mock service processes
ps aux | grep "mocks/"

# Restart mock services
pkill -f "crm_service.py"
pkill -f "platform_service.py"
python mocks/crm_service.py &
python mocks/platform_service.py &

# Verify mock service health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

#### High Response Times
1. Check system resources in Grafana
2. Review mock service performance
3. Check for database connection issues
4. Verify network connectivity between services

#### Content Generation Failures
1. Check application logs for errors
2. Verify mock service availability
3. Test individual publisher components
4. Review configuration settings

### Log Analysis

#### Key Log Patterns
```bash
# Content generation tracking
grep "content_generation" logs/app.log

# Publisher operations
grep "publisher_action" logs/app.log

# Dry run operations
grep "dry_run" logs/app.log

# Error patterns
grep -E "(ERROR|CRITICAL|Exception)" logs/app.log
```

#### Mock Service Logs
```bash
# CRM Mock Service
tail -f logs/crm-mock.log

# Platform Mock Service
tail -f logs/platform-mock.log

# Combined mock service logs
tail -f logs/crm-mock.log logs/platform-mock.log
```

---

## Security

### Security Features

#### API Key Management
- Encryption at rest using `API_KEY_ENCRYPTION_KEY`
- Secure key rotation procedures
- Environment-based configuration

#### Network Security
- Internal service communication only
- No external API connections in dry run mode
- Configurable rate limiting

#### Data Protection
- No sensitive data persistence in dry run mode
- Secure mock data generation
- Audit logging for all operations

### Security Checklist

#### Deployment Security
- [ ] Environment variables secured
- [ ] API keys encrypted
- [ ] Network access restricted
- [ ] Audit logging enabled
- [ ] Security scanning completed

#### Operational Security
- [ ] Regular security updates
- [ ] Access control verification
- [ ] Log monitoring active
- [ ] Incident response tested
- [ ] Backup procedures verified

---

## Performance

### Performance Targets

#### Response Time Targets
- **Content Generation**: <2s (95th percentile)
- **Health Checks**: <100ms
- **Mock Services**: <50ms
- **API Endpoints**: <1s (average)

#### Throughput Targets
- **Concurrent Requests**: 100
- **Requests per Second**: 50
- **Content Generation Rate**: 10/minute
- **Email Processing Rate**: 100/minute

#### Resource Utilization Targets
- **CPU Usage**: <50% steady state, <80% peak
- **Memory Usage**: <60% steady state, <85% peak
- **Disk I/O**: <70% utilization
- **Network I/O**: <50% bandwidth utilization

### Performance Optimization

#### Application Level
- Connection pooling for database operations
- Async I/O for external service calls
- Caching for frequently accessed data
- Rate limiting to prevent overload

#### Mock Service Level
- Fast response simulation (<50ms)
- Realistic data generation
- Configurable delay simulation
- Error scenario testing

#### System Level
- Adequate resource allocation
- SSD storage for fast I/O
- Network optimization
- Container resource limits

---

## Maintenance

### Regular Maintenance Tasks

#### Daily
- [ ] Health check all services
- [ ] Review monitoring dashboards
- [ ] Check for error patterns
- [ ] Verify dry run mode status

#### Weekly
- [ ] Review performance metrics
- [ ] Update mock service data
- [ ] Clean up log files
- [ ] Test error scenarios

#### Monthly
- [ ] Security updates
- [ ] Performance optimization review
- [ ] Documentation updates
- [ ] Capacity planning review

### Backup Procedures

#### Configuration Backup
```bash
# Backup configuration files
tar -czf config-backup-$(date +%Y%m%d).tar.gz \
  .env \
  monitoring/ \
  mocks/ \
  scripts/
```

#### Log Backup
```bash
# Archive old logs
find logs/ -name "*.log" -mtime +30 -exec gzip {} \;

# Backup to remote storage
rsync -av logs/ backup-server:/backups/halcytone-logs/
```

### Update Procedures

#### Application Updates
1. **Preparation**
   ```bash
   # Create backup
   ./scripts/backup-system.sh

   # Stop services gracefully
   docker-compose down
   ```

2. **Update**
   ```bash
   # Pull latest changes
   git pull origin main

   # Update dependencies
   pip install -r requirements.txt
   ```

3. **Deployment**
   ```bash
   # Start services
   docker-compose up -d

   # Verify health
   ./scripts/health-check.sh
   ```

4. **Verification**
   ```bash
   # Run smoke tests
   ./scripts/smoke-test.sh

   # Check monitoring
   curl http://localhost:3000/d/halcytone-overview
   ```

---

## Appendix

### Quick Reference

#### Service Endpoints
| Service | Port | Health Check | Dashboard |
|---------|------|--------------|-----------|
| Content Generator | 8000 | `/health` | N/A |
| Mock CRM | 8001 | `/health` | `/docs` |
| Mock Platform | 8002 | `/health` | `/docs` |
| Grafana | 3000 | `/api/health` | `/` |
| Prometheus | 9090 | `/-/healthy` | `/` |

#### Common Commands
```bash
# Service management
./scripts/start-monitoring.sh
docker-compose up -d
docker-compose logs -f

# Health checks
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# Testing
curl -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{"preview_only": true}'
```

#### Configuration Files
- **Main Config**: `.env`
- **Docker Compose**: `docker-compose.yml`, `docker-compose.monitoring.yml`
- **Monitoring**: `monitoring/prometheus/prometheus.yml`
- **Mock Services**: `mocks/crm_service.py`, `mocks/platform_service.py`

### Support Contacts
- **Development Team**: development@halcytone.local
- **Operations Team**: operations@halcytone.local
- **Emergency Contact**: +1-555-HALCYTONE

---

*Last Updated: Sprint 5 - Documentation & Production Readiness*
*Version: 1.0*
*Contact: Kevin (Development Team)*