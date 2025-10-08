# Toombos - Troubleshooting Guide

## Overview

This troubleshooting guide provides systematic approaches to diagnosing and resolving issues with the Toombos dry run system.

**Version:** Sprint 5 - Documentation & Production Readiness
**Last Updated:** 2025-01-24

---

## Quick Diagnostic Commands

### System Status Check
```bash
# Check all service health
./scripts/health-check-all.sh

# Or manually:
curl -f http://localhost:8000/health || echo "Main service DOWN"
curl -f http://localhost:8001/health || echo "Mock CRM DOWN"
curl -f http://localhost:8002/health || echo "Mock Platform DOWN"
curl -f http://localhost:3000/api/health || echo "Grafana DOWN"
```

### Configuration Verification
```bash
# Verify dry run configuration
python -c "
from src.halcytone_content_generator.config import get_settings
s = get_settings()
print(f'DRY_RUN_MODE: {s.DRY_RUN_MODE}')
print(f'USE_MOCK_SERVICES: {s.USE_MOCK_SERVICES}')
print('Config loaded successfully!')
"
```

### Log Quick Check
```bash
# Check recent errors
tail -n 50 logs/app.log | grep -E "(ERROR|CRITICAL|Exception)"

# Check service startup
tail -n 20 logs/app.log | grep -E "(startup|ready|listening)"
```

---

## Service-Specific Issues

### Main Application (Port 8000)

#### Issue: Service Won't Start

**Symptoms:**
- `curl http://localhost:8000/health` returns connection refused
- Process not visible in `ps aux | grep uvicorn`
- Startup errors in logs

**Diagnostic Steps:**
```bash
# 1. Check port availability
netstat -tulpn | grep :8000
lsof -i :8000

# 2. Check Python environment
python -c "import src.halcytone_content_generator.main"

# 3. Check configuration loading
python -c "from src.halcytone_content_generator.config import get_settings; print(get_settings())"

# 4. Check dependencies
pip check
```

**Common Causes & Solutions:**
| Cause | Solution |
|-------|----------|
| Port already in use | `kill $(lsof -ti:8000)` or use different port |
| Missing dependencies | `pip install -r requirements.txt` |
| Configuration error | Check `.env` file format and values |
| Python path issues | `export PYTHONPATH=$(pwd):$PYTHONPATH` |

#### Issue: High Response Times

**Symptoms:**
- Grafana shows >2s response times
- Timeout errors in client requests
- CPU/memory usage normal

**Diagnostic Steps:**
```bash
# 1. Test specific endpoints
time curl -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{"preview_only": true}'

# 2. Check database connections
grep -i "database" logs/app.log | tail -10

# 3. Check mock service response times
time curl http://localhost:8001/health
time curl http://localhost:8002/health
```

**Solutions:**
- Restart mock services if they're slow
- Check system resources (CPU/memory/disk)
- Review recent configuration changes
- Scale up resources if consistently slow

#### Issue: Content Generation Failures

**Symptoms:**
- 500 errors on content generation endpoints
- "Content generation failed" in logs
- Mock services responding normally

**Diagnostic Steps:**
```bash
# 1. Test with minimal payload
curl -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{"preview_only": true}' -v

# 2. Check publisher-specific errors
grep -i "publisher" logs/app.log | tail -20

# 3. Verify dry run mode
grep -i "dry.*run" logs/app.log | tail -10
```

**Solutions:**
- Verify mock services are accessible
- Check publisher configuration
- Restart application if configuration changed
- Review document fetcher connectivity

### Mock CRM Service (Port 8001)

#### Issue: CRM Mock Service Down

**Symptoms:**
- `curl http://localhost:8001/health` fails
- Email publishing errors in main app
- "CRM service unavailable" alerts

**Diagnostic Steps:**
```bash
# 1. Check process status
ps aux | grep "crm_service.py"

# 2. Check port usage
netstat -tulpn | grep :8001

# 3. Check service logs
tail -f logs/crm-mock.log

# 4. Try manual restart
python mocks/crm_service.py
```

**Common Solutions:**
```bash
# Restart CRM mock service
pkill -f "crm_service.py"
python mocks/crm_service.py > logs/crm-mock.log 2>&1 &

# Verify startup
sleep 2
curl http://localhost:8001/health
```

#### Issue: CRM Mock Service Errors

**Symptoms:**
- 500 errors from mock CRM endpoints
- "Simulated CRM error" in logs
- Inconsistent email publishing results

**Diagnostic Steps:**
```bash
# 1. Test CRM endpoints directly
curl -X POST http://localhost:8001/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{"subject": "test", "html_content": "test content"}'

# 2. Check for error simulation
curl -X POST http://localhost:8001/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{"subject": "error test", "html_content": "test"}'
```

**Solutions:**
- Review subject line (avoid "error", "timeout", "invalid")
- Check CRM mock configuration
- Restart CRM service to reset state
- Review CRM service logs for specific errors

### Mock Platform Service (Port 8002)

#### Issue: Platform Mock Service Down

**Symptoms:**
- `curl http://localhost:8002/health` fails
- Web publishing errors in main app
- "Platform service unavailable" alerts

**Diagnostic Steps:**
```bash
# 1. Check process and port
ps aux | grep "platform_service.py"
netstat -tulpn | grep :8002

# 2. Check service logs
tail -f logs/platform-mock.log

# 3. Manual restart test
python mocks/platform_service.py
```

**Solutions:**
```bash
# Restart Platform mock service
pkill -f "platform_service.py"
python mocks/platform_service.py > logs/platform-mock.log 2>&1 &

# Verify startup
sleep 2
curl http://localhost:8002/health
```

### Monitoring Stack Issues

#### Issue: Grafana Not Accessible

**Symptoms:**
- `curl http://localhost:3000/api/health` fails
- Dashboards not loading
- "Connection refused" errors

**Diagnostic Steps:**
```bash
# 1. Check Docker containers
docker-compose -f docker-compose.monitoring.yml ps

# 2. Check container logs
docker-compose -f docker-compose.monitoring.yml logs grafana

# 3. Check port conflicts
netstat -tulpn | grep :3000
```

**Solutions:**
```bash
# Restart monitoring stack
docker-compose -f docker-compose.monitoring.yml down
docker-compose -f docker-compose.monitoring.yml up -d

# Or use convenience script
./scripts/start-monitoring.sh restart
```

#### Issue: No Metrics in Grafana

**Symptoms:**
- Dashboards show "No data"
- Prometheus targets down
- Missing metrics in Prometheus

**Diagnostic Steps:**
```bash
# 1. Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# 2. Check metrics endpoints
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics
curl http://localhost:8002/metrics

# 3. Check Prometheus configuration
cat monitoring/prometheus/prometheus.yml
```

**Solutions:**
- Add `/metrics` endpoints to applications if missing
- Verify Prometheus scrape configuration
- Check network connectivity between services
- Restart Prometheus to reload configuration

---

## Configuration Issues

### Environment Variable Problems

#### Issue: Configuration Not Loading

**Symptoms:**
- Default values being used instead of environment values
- "Configuration validation failed" errors
- Services starting with wrong settings

**Diagnostic Steps:**
```bash
# 1. Check environment variables
env | grep -E "(DRY_RUN|MOCK|HALCYTONE)"

# 2. Check .env file
cat .env | grep -v "^#"

# 3. Test configuration loading
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('DRY_RUN_MODE:', os.getenv('DRY_RUN_MODE'))
print('USE_MOCK_SERVICES:', os.getenv('USE_MOCK_SERVICES'))
"
```

**Solutions:**
- Verify `.env` file format (no spaces around `=`)
- Check file permissions on `.env`
- Restart services after configuration changes
- Use `export` for shell environment variables

#### Issue: Pydantic Validation Errors

**Symptoms:**
- "ValidationError: extra inputs not permitted"
- "field required" errors on startup
- Configuration loading fails

**Diagnostic Steps:**
```bash
# 1. Check Settings model
python -c "
from src.halcytone_content_generator.config import Settings
try:
    s = Settings()
    print('Settings loaded successfully')
except Exception as e:
    print(f'Settings error: {e}')
"

# 2. Check specific field validation
python -c "
from src.halcytone_content_generator.config import Settings
import os
print('Current env vars:')
for key in ['DRY_RUN_MODE', 'USE_MOCK_SERVICES', 'API_KEY_ENCRYPTION_KEY']:
    print(f'{key}: {os.getenv(key)}')
"
```

**Solutions:**
- Add missing fields to Settings model
- Remove extra fields from environment
- Check field types (bool vs string)
- Review Pydantic v2 migration requirements

### Mock Service Configuration

#### Issue: Mock Services Using Wrong Ports

**Symptoms:**
- Connection errors to mock services
- Services starting on unexpected ports
- Port conflicts between services

**Diagnostic Steps:**
```bash
# 1. Check configured ports
grep -r "port.*800" mocks/
grep -r "8001\|8002" src/

# 2. Check actual listening ports
netstat -tulpn | grep -E ":800[12]"

# 3. Check service startup logs
grep -i "listening\|port\|server" logs/*mock*.log
```

**Solutions:**
- Update mock service configurations
- Check for port environment variables
- Restart services on correct ports
- Update client configurations to match

---

## Performance Issues

### High CPU Usage

#### Issue: CPU Usage >80%

**Symptoms:**
- Grafana CPU dashboard shows high usage
- Slow system response
- High load averages

**Diagnostic Steps:**
```bash
# 1. Identify resource-heavy processes
top -p $(pgrep -d',' python)
htop -p $(pgrep -d',' -f "halcytone|mock")

# 2. Check for infinite loops
strace -p $(pgrep -f "main:app") -c

# 3. Profile application if needed
python -m cProfile -o profile.stats main.py
```

**Solutions:**
- Scale up resources (CPU cores)
- Optimize application code
- Add request rate limiting
- Check for memory leaks causing garbage collection

### High Memory Usage

#### Issue: Memory Usage >85%

**Symptoms:**
- Memory usage alerts
- System becoming unresponsive
- Out of memory errors

**Diagnostic Steps:**
```bash
# 1. Check memory usage by process
ps aux --sort=-%mem | head -20

# 2. Check for memory leaks
valgrind --tool=massif python main.py

# 3. Monitor memory over time
watch -n 5 'free -h; echo ""; ps aux --sort=-%mem | head -5'
```

**Solutions:**
- Increase available memory
- Implement memory monitoring
- Add garbage collection tuning
- Profile application for memory leaks

### Slow Response Times

#### Issue: Response Times >2 seconds

**Symptoms:**
- Grafana response time graphs show high values
- User complaints about slow performance
- Timeout errors

**Diagnostic Steps:**
```bash
# 1. Test individual components
time curl http://localhost:8000/health
time curl http://localhost:8001/health
time curl http://localhost:8002/health

# 2. Profile application performance
python -m cProfile -o profile.stats -s cumulative main.py

# 3. Check database query performance
grep -i "query\|database" logs/app.log | tail -20
```

**Solutions:**
- Optimize database queries
- Add caching layers
- Scale services horizontally
- Review application architecture

---

## Network Issues

### Service Communication Problems

#### Issue: Services Can't Communicate

**Symptoms:**
- "Connection refused" between services
- Network timeout errors
- Services healthy individually but integration fails

**Diagnostic Steps:**
```bash
# 1. Test network connectivity
telnet localhost 8001
telnet localhost 8002
nc -zv localhost 8000 8001 8002

# 2. Check firewall rules
sudo iptables -L -n
sudo ufw status

# 3. Check service binding
netstat -tulpn | grep -E ":800[012]"
```

**Solutions:**
- Check service binding (0.0.0.0 vs 127.0.0.1)
- Verify firewall rules
- Check Docker networking if using containers
- Use proper hostname resolution

### DNS Resolution Issues

#### Issue: Hostname Resolution Failures

**Symptoms:**
- "Name resolution failed" errors
- Intermittent connectivity issues
- Services work with IP but not hostname

**Diagnostic Steps:**
```bash
# 1. Test DNS resolution
nslookup localhost
dig localhost

# 2. Check /etc/hosts
cat /etc/hosts | grep -E "(localhost|halcytone)"

# 3. Test with IP addresses
curl http://127.0.0.1:8000/health
```

**Solutions:**
- Use IP addresses instead of hostnames
- Update /etc/hosts file
- Check DNS server configuration
- Use service discovery if in containers

---

## Data Issues

### Mock Data Problems

#### Issue: Inconsistent Mock Data

**Symptoms:**
- Different responses from mock services
- Data doesn't match expected format
- Integration tests failing due to data format

**Diagnostic Steps:**
```bash
# 1. Test mock service responses
curl -X POST http://localhost:8001/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{"subject": "test", "html_content": "test"}' | jq .

# 2. Check mock data generation
python -c "
from mocks.crm_service import generate_mock_response
print(generate_mock_response())
"

# 3. Compare with expected schema
diff expected-response.json actual-response.json
```

**Solutions:**
- Update mock data generation logic
- Validate mock responses against schemas
- Reset mock service state
- Review API documentation for changes

### Database Connection Issues

#### Issue: Database Connectivity Problems

**Symptoms:**
- "Database connection failed" errors
- Timeouts on database operations
- Data persistence issues

**Diagnostic Steps:**
```bash
# 1. Check database service
systemctl status postgresql
docker ps | grep postgres

# 2. Test database connectivity
psql -h localhost -U username -d database_name -c "SELECT 1;"

# 3. Check connection pool
grep -i "connection.*pool" logs/app.log
```

**Solutions:**
- Restart database service
- Check connection string configuration
- Verify database permissions
- Monitor connection pool usage

---

## Security Issues

### Authentication Problems

#### Issue: API Key Validation Failures

**Symptoms:**
- "Invalid API key" errors
- Authentication bypassed unexpectedly
- Inconsistent access control

**Diagnostic Steps:**
```bash
# 1. Check API key configuration
python -c "
from src.halcytone_content_generator.config import get_settings
s = get_settings()
print('API_KEY_ENCRYPTION_KEY configured:', bool(s.API_KEY_ENCRYPTION_KEY))
"

# 2. Test API key validation
curl -H "Authorization: Bearer invalid-key" \
  http://localhost:8000/api/v2/generate-content

# 3. Check authentication logs
grep -i "auth\|token\|key" logs/app.log | tail -10
```

**Solutions:**
- Verify API key encryption/decryption
- Check authentication middleware
- Review security configuration
- Rotate compromised keys

### Access Control Issues

#### Issue: Unauthorized Access

**Symptoms:**
- Requests succeeding without authentication
- Access to restricted endpoints
- Security validation bypassed

**Diagnostic Steps:**
```bash
# 1. Test without authentication
curl http://localhost:8000/api/v2/generate-content

# 2. Check security middleware
grep -i "middleware\|security" logs/app.log

# 3. Review access control configuration
python -c "
from src.halcytone_content_generator.config import get_settings
s = get_settings()
print('Security settings configured')
"
```

**Solutions:**
- Enable authentication middleware
- Review endpoint security decorators
- Check bypass conditions for dry run mode
- Implement proper access controls

---

## Emergency Procedures

### Service Recovery

#### Complete System Failure

**Immediate Actions:**
```bash
# 1. Stop all services
pkill -f "halcytone\|mock.*service\|uvicorn"
docker-compose down

# 2. Check system resources
df -h
free -h
ps aux | head -20

# 3. Restart in minimal mode
export DRY_RUN_MODE=true
export USE_MOCK_SERVICES=true
python mocks/crm_service.py &
python mocks/platform_service.py &
python -m uvicorn src.halcytone_content_generator.main:app --host 0.0.0.0 --port 8000
```

**Recovery Checklist:**
- [ ] Verify system resources available
- [ ] Start mock services first
- [ ] Start main application
- [ ] Verify health checks
- [ ] Test basic functionality
- [ ] Start monitoring stack
- [ ] Check all dashboards

#### Data Corruption

**Immediate Actions:**
```bash
# 1. Stop all services
./scripts/stop-all-services.sh

# 2. Backup current state
tar -czf emergency-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  logs/ config/ data/

# 3. Restore from last known good backup
./scripts/restore-backup.sh latest-good-backup.tar.gz

# 4. Restart services
./scripts/start-all-services.sh
```

### Escalation Procedures

#### When to Escalate

**Immediate Escalation (Page On-Call):**
- Complete system failure >5 minutes
- Data corruption detected
- Security breach suspected
- Critical alert storm (>10 critical alerts)

**Standard Escalation (Email/Slack):**
- Performance degradation >30 minutes
- Mock service failures >15 minutes
- Monitoring system failures
- Configuration issues requiring expertise

#### Escalation Contacts

| Severity | Contact | Response Time | Method |
|----------|---------|---------------|--------|
| P0 - Critical | On-call Engineer | 5 minutes | Phone/Page |
| P1 - High | Development Team | 15 minutes | Slack/Email |
| P2 - Medium | Operations Team | 1 hour | Email |
| P3 - Low | Team Lead | Next business day | Email |

### Communication Templates

#### Status Update Template
```
Subject: [INCIDENT] Halcytone Dry Run System - [Status]

Timeline:
- XX:XX - Issue detected: [brief description]
- XX:XX - Investigation started
- XX:XX - Root cause identified: [cause]
- XX:XX - Fix applied: [solution]
- XX:XX - Services restored

Impact:
- Affected services: [list]
- Duration: [time]
- User impact: [description]

Next Steps:
- [Action items]
- [Follow-up tasks]
- [Prevention measures]

Status: [INVESTIGATING|FIXING|MONITORING|RESOLVED]
```

---

## Preventive Measures

### Monitoring Setup

#### Health Check Automation
```bash
# Create automated health check script
cat > scripts/health-check-cron.sh << 'EOF'
#!/bin/bash
# Run every 5 minutes via cron

SERVICES=(
  "http://localhost:8000/health"
  "http://localhost:8001/health"
  "http://localhost:8002/health"
  "http://localhost:3000/api/health"
)

for service in "${SERVICES[@]}"; do
  if ! curl -sf "$service" > /dev/null; then
    echo "$(date): $service is down" >> logs/health-check.log
    # Send alert
    ./scripts/send-alert.sh "Service down: $service"
  fi
done
EOF

chmod +x scripts/health-check-cron.sh

# Add to crontab
echo "*/5 * * * * /path/to/toombos-backend/scripts/health-check-cron.sh" | crontab -
```

#### Log Rotation Setup
```bash
# Configure log rotation
sudo cat > /etc/logrotate.d/halcytone << 'EOF'
/path/to/toombos-backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
```

### Backup Automation
```bash
# Daily backup script
cat > scripts/daily-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/halcytone"
DATE=$(date +%Y%m%d)

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup configuration
tar -czf "$BACKUP_DIR/$DATE/config-$DATE.tar.gz" \
  .env \
  monitoring/ \
  mocks/ \
  scripts/

# Backup logs (last 7 days)
find logs/ -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/$DATE/" \;

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \;
EOF

chmod +x scripts/daily-backup.sh

# Add to crontab
echo "0 2 * * * /path/to/toombos-backend/scripts/daily-backup.sh" | crontab -
```

---

## Testing Procedures

### Smoke Tests
```bash
# Basic smoke test script
cat > scripts/smoke-test.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Halcytone Dry Run System Smoke Test ==="

# Test 1: Health checks
echo "Testing service health..."
curl -f http://localhost:8000/health
curl -f http://localhost:8001/health
curl -f http://localhost:8002/health
echo "✓ All services healthy"

# Test 2: Basic content generation
echo "Testing content generation..."
response=$(curl -s -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{"preview_only": true}')
echo "$response" | jq . > /dev/null
echo "✓ Content generation working"

# Test 3: Mock services
echo "Testing mock services..."
curl -s -X POST http://localhost:8001/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{"subject": "test", "html_content": "test"}' | jq . > /dev/null
echo "✓ Mock CRM working"

curl -s -X POST http://localhost:8002/api/v1/content/publish \
  -H "Content-Type: application/json" \
  -d '{"title": "test", "content": "test"}' | jq . > /dev/null
echo "✓ Mock Platform working"

# Test 4: Monitoring
echo "Testing monitoring..."
curl -f http://localhost:3000/api/health > /dev/null
echo "✓ Monitoring accessible"

echo "=== All smoke tests passed! ==="
EOF

chmod +x scripts/smoke-test.sh
```

### Load Testing
```bash
# Simple load test script
cat > scripts/load-test.sh << 'EOF'
#!/bin/bash

CONCURRENT_REQUESTS=${1:-10}
TOTAL_REQUESTS=${2:-100}

echo "Running load test: $CONCURRENT_REQUESTS concurrent, $TOTAL_REQUESTS total"

# Install apache bench if needed
which ab > /dev/null || sudo apt-get install -y apache2-utils

# Run load test
ab -n $TOTAL_REQUESTS -c $CONCURRENT_REQUESTS \
  -p test-payload.json \
  -T application/json \
  http://localhost:8000/api/v2/generate-content

echo "Load test completed. Check response times in output above."
EOF

chmod +x scripts/load-test.sh

# Create test payload
cat > test-payload.json << 'EOF'
{"preview_only": true, "send_email": false, "publish_web": false}
EOF
```

---

## Support Information

### Getting Help

#### Internal Support
1. **Check Documentation**: This troubleshooting guide and main documentation
2. **Search Logs**: Use provided log analysis commands
3. **Check Monitoring**: Review Grafana dashboards
4. **Run Diagnostics**: Use provided diagnostic scripts

#### External Support
- **GitHub Issues**: https://github.com/company/toombos-backend/issues
- **Slack Channel**: #halcytone-support
- **Email**: support@halcytone.local

### Reporting Issues

#### Issue Report Template
```
**Environment:**
- Version: [git commit or version]
- Deployment: [local/staging/production]
- OS: [operating system]

**Issue Description:**
[Clear description of the problem]

**Steps to Reproduce:**
1. [First step]
2. [Second step]
3. [And so on...]

**Expected Result:**
[What should happen]

**Actual Result:**
[What actually happens]

**Logs/Screenshots:**
[Attach relevant logs or screenshots]

**Additional Context:**
[Any other relevant information]
```

### Useful Resources

#### Documentation Links
- **Main Documentation**: `docs/dry-run-guide.md`
- **Monitoring Guide**: `docs/monitoring-runbook.md`
- **API Documentation**: Mock service `/docs` endpoints
- **Configuration Reference**: `.env.example`

#### Useful Commands Reference
```bash
# Service management
./scripts/start-all-services.sh
./scripts/stop-all-services.sh
./scripts/restart-all-services.sh

# Health checks
./scripts/health-check-all.sh
./scripts/smoke-test.sh

# Diagnostics
./scripts/collect-diagnostic-info.sh
./scripts/check-configuration.sh

# Monitoring
./scripts/start-monitoring.sh
./scripts/check-metrics.sh

# Backup/Recovery
./scripts/backup-system.sh
./scripts/restore-backup.sh [backup-file]
```

---

*Last Updated: Sprint 5 - Documentation & Production Readiness*
*Contact: Development Team*