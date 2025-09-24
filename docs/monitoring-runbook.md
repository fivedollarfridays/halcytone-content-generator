# Halcytone Content Generator - Monitoring Runbook

## Overview

This runbook provides operational guidance for the Halcytone Content Generator monitoring infrastructure, part of Sprint 4 (Monitoring & Observability).

### Architecture

The monitoring stack consists of:
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Promtail**: Log collection agent
- **AlertManager**: Alert routing and notifications
- **Node Exporter**: System metrics

## Quick Start

### Starting the Monitoring Stack

```bash
# Start all monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services are running
docker-compose -f docker-compose.monitoring.yml ps

# Check service logs
docker-compose -f docker-compose.monitoring.yml logs -f [service-name]
```

### Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin / halcytone_monitor_2025 |
| Prometheus | http://localhost:9090 | None |
| AlertManager | http://localhost:9093 | None |
| Loki | http://localhost:3100 | None |

## Key Dashboards

### 1. Halcytone Service Overview
- **URL**: http://localhost:3000/d/halcytone-overview
- **Purpose**: Primary operational dashboard
- **Key Metrics**:
  - Service health status
  - Request rate and response times
  - Resource usage (CPU/Memory)
  - Dry run mode indicator
  - Content generation operations

### 2. Mock Services Dashboard
- **URL**: http://localhost:3000/d/mock-services
- **Purpose**: Monitor dry run infrastructure
- **Key Metrics**:
  - Mock CRM service operations
  - Mock Platform service operations
  - Response times for mock endpoints

## Alert Categories

### Critical Alerts
- **HalcytoneServiceDown**: Main service unavailable
- **CriticalResponseTime**: Response times > 5 seconds
- **HighErrorRate**: Error rate > 5%
- **CriticalMemoryUsage**: Memory usage > 95%

### Warning Alerts
- **MockCRMServiceDown**: Mock CRM unavailable
- **MockPlatformServiceDown**: Mock Platform unavailable
- **HighResponseTime**: Response times > 2 seconds
- **HighCPUUsage**: CPU usage > 80%
- **HighMemoryUsage**: Memory usage > 85%
- **DryRunModeDisabled**: Service not in dry run mode

### Business Alerts
- **NoContentGenerationActivity**: No content generated for 30 minutes
- **ContentGenerationFailures**: Failures in content generation
- **MockServiceInteractionFailure**: Issues with mock service communication

## Troubleshooting Guide

### Service Health Issues

#### Main Service Down
```bash
# Check service status
docker ps | grep halcytone
curl -f http://localhost:8000/health || echo "Service down"

# Check application logs
docker logs halcytone-content-generator

# Restart if needed
docker-compose restart halcytone-content-generator
```

#### Mock Services Down
```bash
# Check mock services
curl -f http://localhost:8001/health || echo "CRM Mock down"
curl -f http://localhost:8002/health || echo "Platform Mock down"

# Restart mock services
python mocks/crm_service.py &
python mocks/platform_service.py &
```

### Performance Issues

#### High Response Times
1. Check Grafana dashboard for response time percentiles
2. Review system resource usage
3. Check for database connection issues
4. Review recent deployments or configuration changes

#### High Error Rates
1. Check error logs in Loki dashboard
2. Filter by error status codes (5xx)
3. Identify failing endpoints
4. Check external service dependencies

### Resource Issues

#### High CPU/Memory Usage
1. Check system resource dashboard
2. Identify resource-intensive processes
3. Review recent load patterns
4. Consider scaling if sustained high usage

### Dry Run Issues

#### Dry Run Mode Disabled
1. Verify environment configuration
2. Check DRY_RUN_MODE setting
3. Ensure mock services are accessible
4. Review configuration loading logs

#### Mock Service Failures
1. Check mock service health endpoints
2. Review mock service logs
3. Verify network connectivity
4. Restart mock services if needed

## Log Analysis

### Using Loki/Grafana for Logs

1. **Access Logs**: Go to Grafana → Explore → Select Loki datasource
2. **Query Examples**:
   ```
   # All application logs
   {job="halcytone-content-generator"}

   # Error logs only
   {job="halcytone-content-generator"} |= "ERROR"

   # Mock service logs
   {job=~"mock-.*-service"}

   # Filter by time range
   {job="halcytone-content-generator"} |= "content generation" | json | __error__=""
   ```

### Common Log Patterns

- **Content Generation**: Look for `content_generation_complete`
- **Publisher Actions**: Search for `publisher_action`
- **Dry Run Operations**: Filter for `dry_run_mode`
- **Error Patterns**: Search for `ERROR`, `CRITICAL`, `exception`

## Maintenance Tasks

### Daily Checks
- [ ] Review service health dashboard
- [ ] Check for new alerts
- [ ] Verify dry run mode status
- [ ] Monitor resource usage trends

### Weekly Tasks
- [ ] Review alert patterns and adjust thresholds
- [ ] Cleanup old logs (retention policy)
- [ ] Update dashboards based on operational needs
- [ ] Review performance trends

### Monthly Tasks
- [ ] Capacity planning review
- [ ] Alert effectiveness analysis
- [ ] Dashboard optimization
- [ ] Documentation updates

## Performance Baselines

### Expected Response Times
- **Content Generation**: < 2 seconds (95th percentile)
- **Health Checks**: < 100ms
- **Mock Services**: < 50ms

### Expected Resource Usage
- **CPU**: < 50% steady state
- **Memory**: < 60% steady state
- **Disk I/O**: < 70% utilization

### Alert Thresholds
- **Response Time Warning**: > 2 seconds
- **Response Time Critical**: > 5 seconds
- **Error Rate Critical**: > 5%
- **Resource Warning**: > 80% CPU, 85% Memory

## Emergency Contacts

### Alert Escalation
1. **Level 1**: Development Team (Webhooks)
2. **Level 2**: Operations Team (Email)
3. **Level 3**: On-call Manager (SMS/Phone)

### Service Dependencies
- **Internal**: Main application, Mock services
- **External**: Google Docs API, Notion API (in live mode)
- **Infrastructure**: Docker, Host system

## Configuration Management

### Environment Variables
```bash
# Monitoring configuration
PROMETHEUS_RETENTION_DAYS=15
GRAFANA_ADMIN_PASSWORD=halcytone_monitor_2025
LOKI_RETENTION_PERIOD=30d
ALERTMANAGER_SLACK_WEBHOOK=disabled
```

### File Locations
- **Prometheus Config**: `monitoring/prometheus/prometheus.yml`
- **Grafana Dashboards**: `monitoring/grafana/dashboards/`
- **Alert Rules**: `monitoring/prometheus/rules/`
- **Log Config**: `monitoring/loki/loki-config.yml`

---

## Quick Reference Commands

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Stop monitoring stack
docker-compose -f docker-compose.monitoring.yml down

# View logs
docker-compose -f docker-compose.monitoring.yml logs -f grafana
docker-compose -f docker-compose.monitoring.yml logs -f prometheus

# Health checks
curl http://localhost:3000/api/health    # Grafana
curl http://localhost:9090/-/healthy     # Prometheus
curl http://localhost:3100/ready         # Loki

# Service restart
docker-compose -f docker-compose.monitoring.yml restart prometheus
docker-compose -f docker-compose.monitoring.yml restart grafana
```

---

*Last Updated: Sprint 4 - Monitoring & Observability*
*Contact: Kevin (Development Team)*