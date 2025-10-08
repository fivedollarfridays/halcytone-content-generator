# Production Deployment Checklist

Complete checklist for deploying the Toombos to production.

**Deployment Date**: _____________
**Deployment Manager**: _____________
**Environment**: Production
**Version**: _____________

---

## Pre-Deployment Phase (1-2 weeks before)

### 1. Infrastructure Preparation

- [ ] **Cloud Infrastructure Provisioned**
  - [ ] Kubernetes cluster created (if using K8s)
  - [ ] Virtual machines provisioned (if using Docker Compose)
  - [ ] Network configuration completed
  - [ ] Firewall rules configured
  - [ ] Load balancer provisioned
  - [ ] DNS records created

- [ ] **Database Setup**
  - [ ] PostgreSQL instance created
  - [ ] Database user created with appropriate permissions
  - [ ] SSL/TLS certificates configured
  - [ ] Connection pooling configured (PgBouncer if needed)
  - [ ] Backup automation configured
  - [ ] Read replicas configured (if applicable)
  - [ ] Connection tested from application servers

- [ ] **Cache Layer Setup**
  - [ ] Redis instance created
  - [ ] Redis password configured
  - [ ] Persistence enabled (AOF or RDB)
  - [ ] Connection tested from application servers

- [ ] **Storage Setup**
  - [ ] S3 bucket created for backups
  - [ ] IAM roles/policies configured
  - [ ] Lifecycle policies configured
  - [ ] Encryption enabled

### 2. Secrets Management

- [ ] **Secrets Manager Configured**
  - [ ] AWS Secrets Manager / Azure Key Vault / HashiCorp Vault set up
  - [ ] IAM permissions configured for application access
  - [ ] Automatic rotation policies configured

- [ ] **API Keys Obtained**
  - [ ] CRM API key obtained and tested
  - [ ] Platform API key obtained and tested
  - [ ] OpenAI API key obtained and tested
  - [ ] Google Cloud service account created
  - [ ] Notion API key obtained (if applicable)

- [ ] **Security Secrets Generated**
  - [ ] JWT secret key generated (32+ characters)
  - [ ] API key encryption key generated (32+ characters)
  - [ ] Content Generator API key generated
  - [ ] Webhook secrets generated

- [ ] **Secrets Stored**
  - [ ] Run `scripts/setup_aws_secrets.sh` (or equivalent)
  - [ ] All secrets verified in secrets manager
  - [ ] Access policies tested

### 3. Configuration

- [ ] **Environment Configuration**
  - [ ] `.env.production` created from template
  - [ ] All placeholder values replaced
  - [ ] Database connection string configured
  - [ ] Redis connection string configured
  - [ ] External service URLs configured
  - [ ] Log levels set appropriately (WARNING/INFO)
  - [ ] Debug mode disabled (`DEBUG=false`)
  - [ ] Dry run disabled (`DRY_RUN=false`, `USE_MOCK_SERVICES=false`)

- [ ] **SSL/TLS Certificates**
  - [ ] SSL certificates obtained (Let's Encrypt or commercial CA)
  - [ ] Certificates installed on load balancer/ingress
  - [ ] Certificate auto-renewal configured
  - [ ] Certificate expiration monitoring configured

- [ ] **Container Images**
  - [ ] Production Dockerfile created (`Dockerfile.prod`)
  - [ ] Multi-stage build optimized
  - [ ] Security scanning completed
  - [ ] Image built and pushed to registry
  - [ ] Image tags/versions documented

### 4. External Service Validation

- [ ] **Service Connectivity Tested**
  - [ ] Run `python scripts/validate_external_services.py --all`
  - [ ] Google Docs API accessible
  - [ ] Notion API accessible (if used)
  - [ ] OpenAI API accessible
  - [ ] CRM service reachable and authenticated
  - [ ] Platform service reachable and authenticated
  - [ ] Database connection successful
  - [ ] Redis connection successful

- [ ] **Service Permissions Verified**
  - [ ] Google service account has document access
  - [ ] Notion integration has database access
  - [ ] Database user has correct privileges
  - [ ] API rate limits reviewed and acceptable

### 5. Monitoring & Observability

- [ ] **Monitoring Stack Deployed**
  - [ ] Prometheus deployed and configured
  - [ ] Grafana deployed and configured
  - [ ] Jaeger deployed (for tracing)
  - [ ] Log aggregation configured (ELK, CloudWatch, etc.)

- [ ] **Dashboards Configured**
  - [ ] Application overview dashboard
  - [ ] Performance metrics dashboard
  - [ ] Infrastructure metrics dashboard
  - [ ] Business metrics dashboard

- [ ] **Alerts Configured**
  - [ ] High error rate alerts
  - [ ] High response time alerts
  - [ ] Service down alerts
  - [ ] Database connection alerts
  - [ ] Memory/CPU threshold alerts
  - [ ] Alert destinations configured (email, Slack)

### 6. Testing

- [ ] **Staging Environment**
  - [ ] Staging environment matches production configuration
  - [ ] Full deployment tested in staging
  - [ ] Load testing completed
  - [ ] Performance benchmarks meet SLA requirements
  - [ ] Failover scenarios tested

- [ ] **Integration Tests**
  - [ ] All integration tests passing
  - [ ] Contract tests passing
  - [ ] End-to-end tests passing
  - [ ] Performance tests passing

- [ ] **Load Testing**
  - [ ] Run `python scripts/run_performance_baseline.py`
  - [ ] Response time < 500ms for 95th percentile
  - [ ] Error rate < 0.1%
  - [ ] Successful handling of expected peak load
  - [ ] Auto-scaling verified

---

## Deployment Phase (Day of deployment)

### 7. Pre-Deployment Verification

- [ ] **Team Readiness**
  - [ ] All team members notified of deployment
  - [ ] Rollback plan reviewed
  - [ ] On-call engineer identified
  - [ ] Deployment window communicated

- [ ] **Final Checks**
  - [ ] All tests passing in CI/CD
  - [ ] No critical bugs in backlog
  - [ ] Database migrations prepared (if applicable)
  - [ ] Rollback scripts tested
  - [ ] Maintenance page ready (if needed)

### 8. Deployment Execution

#### Option A: Docker Compose Deployment

- [ ] **Deploy to Docker Compose**
  ```bash
  ./deployment/scripts/deploy-docker-compose.sh production
  ```
  - [ ] Pre-deployment checks passed
  - [ ] Images built successfully
  - [ ] Rolling update completed
  - [ ] Health checks passing
  - [ ] All services healthy
  - [ ] Endpoints responding correctly

#### Option B: Kubernetes Deployment

- [ ] **Deploy to Kubernetes**
  ```bash
  ./deployment/scripts/deploy-kubernetes.sh production halcytone
  ```
  - [ ] Cluster connectivity verified
  - [ ] Secrets validated
  - [ ] ConfigMaps applied
  - [ ] Deployment applied
  - [ ] Pods running (3/3 minimum)
  - [ ] HPA configured and active
  - [ ] Ingress configured
  - [ ] Endpoints responding correctly

### 9. Post-Deployment Verification

- [ ] **Service Health**
  - [ ] Health endpoint responding: `curl https://api.halcytone.com/health`
  - [ ] Readiness endpoint responding: `curl https://api.halcytone.com/ready`
  - [ ] API docs accessible: `https://api.halcytone.com/docs`

- [ ] **External Service Connectivity**
  - [ ] Run validation: `python scripts/validate_external_services.py --all`
  - [ ] All external services reachable
  - [ ] No authentication errors in logs

- [ ] **Functional Testing**
  - [ ] Content generation working
  - [ ] Email distribution working
  - [ ] Platform integration working
  - [ ] CRM integration working
  - [ ] Caching working
  - [ ] Scheduling working

- [ ] **Performance Verification**
  - [ ] Response times within SLA (<500ms)
  - [ ] Error rate within SLA (<0.1%)
  - [ ] CPU usage normal (<70%)
  - [ ] Memory usage normal (<80%)
  - [ ] Database connections normal

### 10. Monitoring Verification

- [ ] **Metrics Collection**
  - [ ] Prometheus collecting metrics
  - [ ] Grafana dashboards showing data
  - [ ] No gaps in metric collection

- [ ] **Logging**
  - [ ] Application logs flowing
  - [ ] No critical errors in logs
  - [ ] Log levels appropriate
  - [ ] Log aggregation working

- [ ] **Alerts**
  - [ ] Alert system functional
  - [ ] Test alert sent and received
  - [ ] Alert routing correct

### 11. Documentation

- [ ] **Deployment Documentation**
  - [ ] Deployment notes documented
  - [ ] Version/tag recorded
  - [ ] Configuration changes documented
  - [ ] Known issues documented

- [ ] **Runbooks Updated**
  - [ ] Operations runbook current
  - [ ] Troubleshooting guide current
  - [ ] Escalation procedures current

---

## Post-Deployment Phase (24-48 hours after)

### 12. Monitoring & Validation

- [ ] **24-Hour Health Check**
  - [ ] No critical errors
  - [ ] Performance within SLA
  - [ ] No memory leaks detected
  - [ ] No database connection issues
  - [ ] Auto-scaling working as expected

- [ ] **User Feedback**
  - [ ] No major user complaints
  - [ ] Content quality acceptable
  - [ ] Delivery times acceptable

### 13. Optimization

- [ ] **Performance Tuning**
  - [ ] Review slow query logs
  - [ ] Optimize database queries if needed
  - [ ] Adjust cache TTL if needed
  - [ ] Tune connection pools if needed

- [ ] **Scaling Adjustment**
  - [ ] Review auto-scaling behavior
  - [ ] Adjust HPA thresholds if needed
  - [ ] Adjust resource limits if needed

### 14. Security

- [ ] **Security Review**
  - [ ] Review access logs for anomalies
  - [ ] Verify no secrets in logs
  - [ ] Confirm SSL/TLS working correctly
  - [ ] Review API authentication patterns

### 15. Backup Verification

- [ ] **Backup Testing**
  - [ ] Verify automated backups running
  - [ ] Test backup restoration
  - [ ] Verify backup retention policy
  - [ ] Confirm off-site backup replication

---

## Go-Live Validation

### 16. Go-Live Criteria

- [ ] **Technical Criteria**
  - [ ] All services healthy for 24 hours
  - [ ] Performance metrics within SLA
  - [ ] No critical bugs
  - [ ] Monitoring and alerts functional
  - [ ] Backups successful

- [ ] **Business Criteria**
  - [ ] Content generation accuracy acceptable
  - [ ] Delivery success rate acceptable
  - [ ] User feedback positive
  - [ ] Stakeholder approval obtained

### 17. Final Sign-Off

- [ ] **Deployment Manager**: _________________ Date: _______
- [ ] **Technical Lead**: _________________ Date: _______
- [ ] **Product Owner**: _________________ Date: _______

---

## Rollback Plan (If Needed)

### Emergency Rollback Procedure

**Trigger Conditions:**
- Critical bug affecting core functionality
- Performance degradation >50%
- Data integrity issues
- Security vulnerability discovered

**Rollback Steps:**

#### Docker Compose Rollback
```bash
# 1. Stop current deployment
docker-compose -f docker-compose.prod.yml down

# 2. Revert to previous version
git checkout <previous-tag>

# 3. Rebuild and deploy
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify health
curl https://api.halcytone.com/health
```

#### Kubernetes Rollback
```bash
# 1. Rollback deployment
kubectl rollout undo deployment/content-generator -n halcytone

# 2. Check rollout status
kubectl rollout status deployment/content-generator -n halcytone

# 3. Verify pods
kubectl get pods -n halcytone -l app=content-generator

# 4. Test endpoints
curl https://api.halcytone.com/health
```

**Post-Rollback Actions:**
- [ ] Notify stakeholders
- [ ] Document issue in incident report
- [ ] Review logs and metrics
- [ ] Identify root cause
- [ ] Create fix plan
- [ ] Schedule re-deployment

---

## Additional Resources

- **Deployment Guide**: `deployment/README.md`
- **Secrets Management**: `docs/secrets-management.md`
- **Database Configuration**: `docs/database-configuration.md`
- **Monitoring Runbook**: `docs/monitoring-runbook.md`
- **Scripts Documentation**: `scripts/README.md`

---

## Notes

Use this section to document any deployment-specific notes, issues encountered, or deviations from the checklist:

```
[Add deployment notes here]
```

---

**Checklist Version**: 1.0
**Last Updated**: 2025-09-30
**Next Review Date**: 2026-01-30
