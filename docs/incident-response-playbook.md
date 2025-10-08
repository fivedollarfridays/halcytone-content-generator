# Toombos - Incident Response Playbook

## Overview

This incident response playbook provides structured procedures for identifying, responding to, and resolving incidents in the Toombos dry run system.

**Version:** Sprint 5 - Documentation & Production Readiness
**Last Updated:** 2025-01-24
**Emergency Contact:** +1-555-HALCYTONE

---

## Table of Contents

1. [Incident Classification](#incident-classification)
2. [Response Team Structure](#response-team-structure)
3. [Incident Response Process](#incident-response-process)
4. [Specific Incident Types](#specific-incident-types)
5. [Communication Procedures](#communication-procedures)
6. [Recovery Procedures](#recovery-procedures)
7. [Post-Incident Activities](#post-incident-activities)
8. [Emergency Contacts](#emergency-contacts)

---

## Incident Classification

### Severity Levels

#### P0 - Critical (Emergency Response)
- **Complete system outage** affecting all users
- **Data corruption or loss**
- **Security breach** with confirmed data exposure
- **Service unavailable** for >15 minutes

**Response Time:** 5 minutes
**Escalation:** Immediate page to on-call engineer
**Communication:** Every 15 minutes until resolved

#### P1 - High (Urgent Response)
- **Major feature unavailable** (content generation, publishing)
- **Performance degradation** >50% slower than baseline
- **Mock service failures** affecting dry run functionality
- **Monitoring system down**

**Response Time:** 15 minutes
**Escalation:** Slack/email to development team
**Communication:** Every 30 minutes until resolved

#### P2 - Medium (Standard Response)
- **Minor feature issues** not affecting core functionality
- **Performance issues** <50% degradation
- **Non-critical alerts** firing repeatedly
- **Documentation or UI issues**

**Response Time:** 1 hour
**Escalation:** Email to team lead
**Communication:** Daily updates until resolved

#### P3 - Low (Planned Response)
- **Enhancement requests**
- **Minor bugs** with workarounds available
- **Maintenance tasks**
- **Technical debt** items

**Response Time:** Next business day
**Escalation:** Team backlog
**Communication:** Weekly status updates

### Impact Assessment Matrix

| Severity | Users Affected | Service Impact | Business Impact |
|----------|----------------|----------------|-----------------|
| P0 | All | Complete outage | Critical business stoppage |
| P1 | >50% | Major degradation | Significant business impact |
| P2 | <50% | Minor issues | Limited business impact |
| P3 | Few/None | Cosmetic issues | Minimal business impact |

---

## Response Team Structure

### Primary Response Team

#### Incident Commander (IC)
- **Role**: Overall incident coordination and decision making
- **Primary**: Development Team Lead
- **Backup**: Senior Developer
- **Responsibilities**:
  - Incident assessment and classification
  - Resource coordination and assignment
  - Communication with stakeholders
  - Decision making for major actions

#### Technical Lead
- **Role**: Technical investigation and resolution
- **Primary**: Senior Backend Developer
- **Backup**: Platform Engineer
- **Responsibilities**:
  - Technical root cause analysis
  - Implementation of fixes
  - System recovery coordination
  - Technical communication to IC

#### Communications Lead
- **Role**: Stakeholder communication and documentation
- **Primary**: Operations Manager
- **Backup**: Product Manager
- **Responsibilities**:
  - Status page updates
  - Stakeholder notifications
  - Incident documentation
  - Post-incident communication

### Extended Response Team

#### Subject Matter Experts (SMEs)
- **Database Administrator**: Database-related incidents
- **Security Engineer**: Security incidents
- **DevOps Engineer**: Infrastructure incidents
- **Product Manager**: Business impact assessment

#### Support Resources
- **On-call Engineer**: 24/7 availability for P0/P1 incidents
- **Vendor Support**: External service provider support
- **Management**: Executive escalation path

---

## Incident Response Process

### Initial Response (0-15 minutes)

#### 1. Incident Detection
**Detection Methods:**
- Automated monitoring alerts (Grafana/Prometheus)
- User reports via support channels
- Proactive monitoring by team members
- External monitoring services

**Initial Actions:**
```bash
# Immediate triage commands
curl -f http://localhost:8000/health || echo "Main service DOWN"
curl -f http://localhost:8001/health || echo "Mock CRM DOWN"
curl -f http://localhost:8002/health || echo "Mock Platform DOWN"

# Check monitoring dashboards
echo "Check Grafana: http://localhost:3000/d/halcytone-overview"
echo "Check Prometheus: http://localhost:9090/targets"
```

#### 2. Initial Assessment
**Severity Classification:**
- Determine impact and urgency using severity matrix
- Consider user impact and business context
- Evaluate system-wide vs. component-specific issues

**Documentation Start:**
- Create incident ticket in tracking system
- Set initial severity level
- Begin incident timeline log
- Assign incident ID: `INC-YYYY-MMDD-NNNN`

#### 3. Team Mobilization
**Notification Process:**
```bash
# P0 - Critical
- Page on-call engineer immediately
- Notify incident commander via phone
- Create emergency bridge call
- Alert management within 10 minutes

# P1 - High
- Slack notification to #halcytone-incidents
- Email to development team
- Create response team chat channel
- Notify stakeholders within 30 minutes
```

### Investigation Phase (15-60 minutes)

#### 1. Information Gathering

**System Status Check:**
```bash
# Service health comprehensive check
./scripts/health-check-all.sh

# Resource utilization
top -b -n 1 | head -20
df -h
free -h

# Recent logs analysis
tail -n 100 logs/halcytone.log | grep -E "(ERROR|CRITICAL|Exception)"
tail -n 100 logs/crm-mock.log | grep -E "(ERROR|Exception)"
tail -n 100 logs/platform-mock.log | grep -E "(ERROR|Exception)"

# Network connectivity
netstat -tulpn | grep -E ":800[0-2]"
ss -tuln | grep -E ":800[0-2]"
```

**Monitoring Data Review:**
- Check Grafana dashboards for anomalies
- Review Prometheus metrics for resource spikes
- Analyze alert timeline and correlation
- Check external monitoring services

#### 2. Impact Assessment

**User Impact Analysis:**
- Number of affected users/requests
- Service availability percentage
- Performance degradation metrics
- Business function impact

**System Impact Analysis:**
- Affected components and services
- Dependency mapping and cascade effects
- Data integrity assessment
- Security implications

#### 3. Root Cause Hypothesis

**Common Failure Patterns:**
- **Service startup failures**: Configuration, dependencies, resources
- **Performance degradation**: Resource exhaustion, database issues
- **Network issues**: Connectivity, DNS, firewall
- **Configuration errors**: Environment variables, service discovery
- **External dependencies**: Third-party service failures

### Resolution Phase (Variable duration)

#### 1. Immediate Mitigation

**P0 Critical Response:**
```bash
# Emergency service restart
sudo supervisorctl stop halcytone:*
sudo supervisorctl start halcytone:*

# Or container restart
docker-compose restart

# Verify basic functionality
./scripts/smoke-test.sh

# Enable maintenance mode (if available)
echo "MAINTENANCE_MODE=true" >> .env.production
```

**P1 High Response:**
```bash
# Graceful service restart
sudo supervisorctl restart halcytone:halcytone-main

# Clear any stuck processes
pkill -f "halcytone.*stuck"

# Resource cleanup
rm -rf /tmp/halcytone-*
find logs/ -name "*.log" -size +100M -delete
```

#### 2. Workaround Implementation

**Service Bypass:**
- Route traffic around failed components
- Enable fallback mechanisms
- Disable non-essential features temporarily
- Scale resources if needed

**Configuration Rollback:**
```bash
# Rollback to last known good configuration
cp backups/config-last-good/.env .env
sudo supervisorctl restart halcytone:*

# Or rollback code deployment
git checkout last-known-good-tag
./scripts/deploy.sh
```

#### 3. Permanent Fix

**Code Fixes:**
- Develop and test fix in development environment
- Create hotfix branch for urgent fixes
- Deploy fix with proper testing
- Verify fix resolves root cause

**Infrastructure Changes:**
- Update server configurations
- Modify monitoring thresholds
- Implement preventive measures
- Update documentation

### Communication Throughout

#### Status Updates

**P0/P1 Communication Template:**
```
INCIDENT UPDATE - [INC-2025-0124-001]

Status: [INVESTIGATING|MITIGATING|RESOLVED]
Severity: P1 - High
Started: 2025-01-24 14:30 UTC
Last Update: 2025-01-24 15:15 UTC

Impact:
- Content generation service experiencing intermittent failures
- Estimated 30% of requests failing
- Mock services operating normally

Current Actions:
- Investigating database connection timeouts
- Implementing connection pool adjustments
- Monitoring service recovery

Next Update: 15:45 UTC or upon status change
```

**Internal Communication Channels:**
- **Slack**: #halcytone-incidents (real-time updates)
- **Email**: stakeholder-alerts@halcytone.com (formal notifications)
- **Bridge Call**: Zoom/Teams room for P0 incidents
- **Status Page**: status.halcytone.com (public updates)

---

## Specific Incident Types

### Application Service Failures

#### Main Application Down (P0)

**Symptoms:**
- Health check endpoint returning 503/timeout
- All API endpoints unreachable
- Monitoring shows service as down

**Immediate Actions:**
```bash
# 1. Verify service status
curl -v http://localhost:8000/health
ps aux | grep uvicorn

# 2. Check logs for errors
tail -n 50 logs/halcytone.log
journalctl -u halcytone-main -n 50

# 3. Attempt restart
sudo supervisorctl restart halcytone:halcytone-main
# Wait 30 seconds
curl http://localhost:8000/health

# 4. If restart fails, check configuration
python -c "from src.halcytone_content_generator.config import get_settings; get_settings()"
```

**Escalation Triggers:**
- Service doesn't restart after 2 attempts
- Configuration validation fails
- System resource exhaustion detected

#### Content Generation Failures (P1)

**Symptoms:**
- Content generation endpoints returning 500 errors
- Timeouts on content processing
- Publisher integration failures

**Investigation Steps:**
```bash
# 1. Test content generation directly
curl -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{"preview_only": true}' -v

# 2. Check mock service connectivity
curl http://localhost:8001/health
curl http://localhost:8002/health

# 3. Review publisher logs
grep -i "publisher\|error" logs/halcytone.log | tail -20

# 4. Test individual publishers
python -c "
from src.halcytone_content_generator.services.publishers.email_publisher import EmailPublisher
# Test publisher functionality
"
```

### Mock Service Incidents

#### Mock CRM Service Down (P1)

**Symptoms:**
- CRM health check failing
- Email publishing errors
- Port 8001 unreachable

**Resolution Steps:**
```bash
# 1. Check process status
ps aux | grep crm_service.py
netstat -tulpn | grep :8001

# 2. Review logs
tail -n 30 logs/crm-mock.log

# 3. Restart service
pkill -f crm_service.py
python mocks/crm_service.py > logs/crm-mock.log 2>&1 &

# 4. Verify recovery
sleep 5
curl http://localhost:8001/health

# 5. Test email functionality
curl -X POST http://localhost:8001/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{"subject": "test", "html_content": "test"}'
```

### Performance Incidents

#### High Response Times (P2)

**Symptoms:**
- API response times >2 seconds
- Grafana showing performance degradation
- User complaints about slowness

**Investigation Checklist:**
```bash
# 1. Resource utilization check
top -b -n 1 | head -10
free -h
df -h

# 2. Database performance
grep -i "database\|query" logs/halcytone.log | tail -10

# 3. Network latency
ping localhost
curl -w "@curl-format.txt" http://localhost:8000/health

# 4. Mock service performance
time curl http://localhost:8001/health
time curl http://localhost:8002/health
```

**Mitigation Actions:**
- Scale up resources if needed
- Restart services to clear memory leaks
- Enable caching mechanisms
- Disable non-essential features temporarily

### Security Incidents

#### Potential Security Breach (P0)

**Immediate Containment:**
```bash
# 1. Isolate affected systems
sudo ufw deny incoming
sudo ufw deny outgoing
sudo ufw allow ssh

# 2. Preserve evidence
cp -r logs/ security-incident-$(date +%Y%m%d-%H%M%S)/
netstat -an > network-connections-$(date +%Y%m%d-%H%M%S).log

# 3. Check for indicators of compromise
grep -i "attack\|breach\|intrusion" logs/*.log
last -n 20
who -a
```

**Investigation Steps:**
- Review authentication logs
- Check for unusual network activity
- Verify data integrity
- Contact security team immediately

### Infrastructure Incidents

#### Monitoring System Down (P1)

**Symptoms:**
- Grafana dashboards not accessible
- No alerts being generated
- Prometheus targets down

**Recovery Actions:**
```bash
# 1. Check monitoring stack
docker-compose -f docker-compose.monitoring.yml ps

# 2. Review container logs
docker-compose -f docker-compose.monitoring.yml logs grafana
docker-compose -f docker-compose.monitoring.yml logs prometheus

# 3. Restart monitoring stack
docker-compose -f docker-compose.monitoring.yml restart

# 4. Verify recovery
curl http://localhost:3000/api/health
curl http://localhost:9090/-/healthy
```

---

## Recovery Procedures

### Service Recovery

#### Standard Recovery Process
```bash
# 1. Assess current state
./scripts/health-check-all.sh

# 2. Stop failed services
sudo supervisorctl stop halcytone:*

# 3. Clear temporary resources
rm -rf /tmp/halcytone-*
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 4. Restart services in order
python mocks/crm_service.py > logs/crm-mock.log 2>&1 &
sleep 2
python mocks/platform_service.py > logs/platform-mock.log 2>&1 &
sleep 2
sudo supervisorctl start halcytone:halcytone-main

# 5. Verify recovery
sleep 10
./scripts/smoke-test.sh
```

#### Emergency Recovery (Last Resort)
```bash
# 1. Complete system reset
sudo supervisorctl stop halcytone:*
docker-compose -f docker-compose.monitoring.yml down

# 2. Restore from backup
cp -r backups/emergency-restore/* ./

# 3. Reset permissions
chown -R halcytone:halcytone .
chmod +x scripts/*.sh

# 4. Full restart
source venv/bin/activate
export $(cat .env.production | xargs)
./scripts/start-all-services.sh

# 5. Comprehensive validation
./scripts/validate-deployment.sh
```

### Data Recovery

#### Configuration Recovery
```bash
# 1. Backup current (potentially corrupted) config
cp .env.production .env.production.incident-backup

# 2. Restore from last known good
cp backups/config-daily/.env.production.$(date -d "yesterday" +%Y%m%d) .env.production

# 3. Validate configuration
python -c "
from src.halcytone_content_generator.config import get_settings
s = get_settings()
print('Configuration restored successfully')
print(f'Environment: {s.ENVIRONMENT}')
"

# 4. Restart with restored config
sudo supervisorctl restart halcytone:*
```

#### Log Data Recovery
```bash
# 1. Check for corrupted log files
find logs/ -name "*.log" -size 0 -delete

# 2. Restore from backup if needed
rsync -av backups/logs-$(date +%Y%m%d)/ logs/

# 3. Fix log permissions
chown -R halcytone:halcytone logs/
chmod 644 logs/*.log
```

---

## Post-Incident Activities

### Immediate Post-Resolution (0-2 hours)

#### 1. Service Stabilization
```bash
# Monitor for 30 minutes after resolution
for i in {1..6}; do
    echo "Stability check $i/6 at $(date)"
    ./scripts/health-check-all.sh
    sleep 300  # 5 minutes
done

# Check resource usage trends
python scripts/resource-monitoring.py --duration 30min --output post-incident-monitoring.json
```

#### 2. Communication Closure
**Resolution Notification Template:**
```
INCIDENT RESOLVED - [INC-2025-0124-001]

Status: RESOLVED
Resolved At: 2025-01-24 16:45 UTC
Duration: 2h 15m

Summary:
- Content generation service experienced intermittent failures due to database connection pool exhaustion
- Implemented connection pool size increase from 5 to 20 connections
- All services restored and operating normally

Impact:
- Estimated 30% of content generation requests failed during incident window
- No data loss occurred
- Mock services remained operational throughout incident

Resolution:
- Increased database connection pool size
- Implemented additional connection monitoring
- Added connection pool metrics to Grafana dashboards

Monitoring:
- Services will be monitored closely for the next 24 hours
- Additional alerts added for connection pool exhaustion

Next Steps:
- Post-incident review scheduled for 2025-01-25 at 10:00 AM
- Follow-up improvements will be implemented next week
```

### Short-term Follow-up (2-24 hours)

#### 1. Incident Documentation
**Complete Incident Report Sections:**
- Timeline of events
- Root cause analysis
- Impact assessment
- Resolution steps taken
- Lessons learned

#### 2. Preventive Measures
```bash
# Implement additional monitoring
cat >> monitoring/prometheus/rules/post-incident-alerts.yml << 'EOF'
- alert: DatabaseConnectionPoolExhaustion
  expr: database_connection_pool_active / database_connection_pool_size > 0.9
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: Database connection pool near exhaustion
EOF

# Restart Prometheus to load new rules
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

#### 3. System Hardening
- Update configuration parameters based on lessons learned
- Implement additional health checks
- Enhance monitoring and alerting
- Update documentation with new procedures

### Long-term Follow-up (1 week - 1 month)

#### 1. Post-Incident Review (PIR)
**PIR Agenda:**
- What happened? (Timeline review)
- Why did it happen? (Root cause analysis)
- How was it resolved? (Response effectiveness)
- How can we prevent it? (Preventive measures)
- What did we learn? (Process improvements)

**PIR Participants:**
- Incident Commander
- Technical responders
- Affected stakeholders
- Management representative

#### 2. Process Improvements
**Action Items Tracking:**
- Technical improvements (code, configuration, infrastructure)
- Process improvements (procedures, documentation, training)
- Tooling improvements (monitoring, automation, testing)
- Communication improvements (notifications, escalation)

#### 3. Knowledge Sharing
- Update incident response playbook
- Conduct team training sessions
- Share learnings with broader organization
- Update monitoring and alerting strategies

---

## Emergency Contacts

### Primary Response Team

| Role | Name | Phone | Email | Backup |
|------|------|--------|-------|---------|
| Incident Commander | Development Lead | +1-555-DEV-LEAD | dev-lead@halcytone.com | Senior Developer |
| Technical Lead | Backend Engineer | +1-555-BACKEND | backend@halcytone.com | Platform Engineer |
| Communications | Operations Manager | +1-555-OPS-MGR | ops@halcytone.com | Product Manager |

### Escalation Contacts

| Level | Role | Contact | When to Escalate |
|-------|------|---------|------------------|
| L2 | Engineering Manager | +1-555-ENG-MGR | P0 not resolved in 1 hour |
| L3 | VP Engineering | +1-555-VP-ENG | P0 not resolved in 2 hours |
| L4 | CTO | +1-555-CTO | Major business impact >4 hours |

### External Contacts

| Service | Contact | Phone | Account ID |
|---------|---------|--------|------------|
| Cloud Provider | AWS Support | +1-800-AWS-SUPPORT | Account: 123456789 |
| Monitoring Service | DataDog | +1-866-329-4466 | org: halcytone |
| Security Service | CrowdStrike | +1-855-797-4532 | Customer: H12345 |

### Communication Channels

#### Internal
- **Slack**: #halcytone-incidents (immediate response)
- **Email**: incident-team@halcytone.com (formal notifications)
- **Phone**: Emergency bridge: +1-555-BRIDGE-1

#### External
- **Status Page**: https://status.halcytone.com
- **Customer Support**: support@halcytone.com
- **Public Relations**: pr@halcytone.com (if public incident)

### After-Hours Support

#### On-Call Schedule
- **Week 1**: Primary: Backend Engineer, Secondary: Platform Engineer
- **Week 2**: Primary: Frontend Engineer, Secondary: DevOps Engineer
- **Week 3**: Primary: QA Engineer, Secondary: Backend Engineer
- **Week 4**: Primary: Platform Engineer, Secondary: Frontend Engineer

#### On-Call Responsibilities
- Respond to P0/P1 alerts within 5/15 minutes
- Execute incident response procedures
- Escalate when needed
- Document incident progress

---

## Incident Response Tools

### Monitoring and Alerting
- **Grafana**: http://localhost:3000 (dashboards and alerts)
- **Prometheus**: http://localhost:9090 (metrics and queries)
- **Log Analysis**: Loki via Grafana Explore

### Communication Tools
- **Slack**: #halcytone-incidents channel
- **Email**: Automated incident notifications
- **Conference Bridge**: Emergency response calls

### Documentation Tools
- **Incident Tracking**: GitHub Issues or Jira tickets
- **Knowledge Base**: Confluence or internal wiki
- **Runbooks**: This playbook and related procedures

### Recovery Tools
- **Backup Systems**: Daily automated backups
- **Deployment Tools**: Automated deployment scripts
- **Testing Tools**: Smoke tests and health checks

---

*Last Updated: Sprint 5 - Documentation & Production Readiness*
*Emergency Hotline: +1-555-HALCYTONE*
*Contact: Development Team*