# Production Monitoring Stack

## Overview

The Halcytone Content Generator production monitoring stack provides comprehensive observability through metrics, logs, distributed tracing, and alerting. The stack is designed for production environments with high availability, scalability, and operational efficiency.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Halcytone Application                        │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│    FastAPI      │   Health        │    Metrics      │  Logging  │
│    Endpoints    │   Checks        │   Collection    │  System   │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
         │                 │                 │              │
         │                 │                 │              │
         ▼                 ▼                 ▼              ▼
┌───────────────┐ ┌────────────────┐ ┌─────────────┐ ┌─────────────┐
│   Jaeger      │ │   Prometheus   │ │  Grafana    │ │ ELK Stack   │
│  (Tracing)    │ │   (Metrics)    │ │(Dashboards) │ │   (Logs)    │
└───────────────┘ └────────────────┘ └─────────────┘ └─────────────┘
         │                 │                 │              │
         │                 ▼                 │              │
         │        ┌────────────────┐         │              │
         │        │  AlertManager  │         │              │
         │        │  (Alerting)    │         │              │
         │        └────────────────┘         │              │
         │                 │                 │              │
         └─────────────────┼─────────────────┼──────────────┘
                           │                 │
                           ▼                 ▼
                  ┌─────────────────┐ ┌─────────────────┐
                  │  Notifications  │ │   Operations    │
                  │ (Slack/Email/   │ │    Dashboard    │
                  │  PagerDuty)     │ │                 │
                  └─────────────────┘ └─────────────────┘
```

## Components

### 1. Metrics Collection (Prometheus)

**Purpose**: Collect and store time-series metrics from the application and infrastructure.

**Configuration**:
- **Scrape interval**: 15 seconds
- **Retention**: 30 days
- **Storage**: 10GB limit with automatic cleanup
- **Targets**: Application, system metrics, external services

**Key Metrics**:
- HTTP request rates, response times, error rates
- Content generation performance and quality scores
- System resources (CPU, memory, disk)
- External service latency and availability
- Database query performance
- Cache hit rates and performance

### 2. Visualization (Grafana)

**Purpose**: Create dashboards and visualizations for metrics and alerts.

**Features**:
- **Pre-built dashboards**: Application overview, performance, errors, infrastructure
- **Real-time monitoring**: Live updates every 30 seconds
- **Alerting**: Grafana-native alerts with multiple notification channels
- **Data sources**: Prometheus, Elasticsearch, Jaeger integration

**Access**:
- **URL**: http://localhost:3000
- **Credentials**: admin/admin123 (change in production)

### 3. Log Aggregation (ELK Stack)

**Components**:
- **Elasticsearch**: Log storage and indexing
- **Logstash**: Log processing and transformation
- **Kibana**: Log visualization and analysis
- **Filebeat**: Log shipping from containers and files

**Features**:
- **Structured logging**: JSON format with correlation IDs
- **Log parsing**: Automatic extraction of application context
- **Index management**: Daily indexes with lifecycle policies
- **Search capabilities**: Full-text search with filtering and aggregation

### 4. Distributed Tracing (Jaeger)

**Purpose**: Track requests across service boundaries and identify performance bottlenecks.

**Features**:
- **Request tracing**: End-to-end request flow tracking
- **Performance analysis**: Identify slow operations and dependencies
- **Error tracking**: Trace errors across service calls
- **Service map**: Visual representation of service dependencies

**Integration**:
- FastAPI automatic instrumentation
- External API call tracing
- Database operation tracing
- Content generation workflow tracing

### 5. Alerting (AlertManager)

**Purpose**: Route alerts to appropriate teams with intelligent grouping and escalation.

**Features**:
- **Multi-channel notifications**: Slack, email, PagerDuty
- **Alert routing**: Team-based routing with escalation
- **Inhibition rules**: Suppress noisy alerts during outages
- **Silence management**: Maintenance window handling

## Quick Start

### 1. Start Monitoring Stack

```bash
# Setup monitoring infrastructure
python scripts/setup_monitoring.py --environment production

# Or manually with Docker Compose
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

### 2. Verify Services

```bash
# Check all services are running
python scripts/setup_monitoring.py --action verify

# Access monitoring UIs
open http://localhost:3000    # Grafana
open http://localhost:5601    # Kibana
open http://localhost:9090    # Prometheus
open http://localhost:16686   # Jaeger
```

### 3. Configure Application

```python
# In your FastAPI application
from src.halcytone_content_generator.monitoring import (
    setup_metrics, setup_tracing, metrics_middleware
)

# Setup metrics
setup_metrics({
    "service.name": "halcytone-content-generator",
    "service.version": "0.1.0",
    "environment": "production"
})

# Setup tracing
setup_tracing(
    service_name="halcytone-content-generator",
    jaeger_endpoint="http://jaeger:14268/api/traces"
)

# Add middleware
app.add_middleware(metrics_middleware())
```

## Configuration

### Environment Variables

```bash
# Core settings
ENVIRONMENT=production
PROMETHEUS_HOST=prometheus
GRAFANA_ADMIN_PASSWORD=your-secure-password

# Alerting
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
CRITICAL_ALERT_EMAILS=ops@yourcompany.com
PAGERDUTY_INTEGRATION_KEY=your-pagerduty-key

# Tracing
JAEGER_AGENT_HOST=jaeger
JAEGER_AGENT_PORT=6831

# Logging
ELASTICSEARCH_HOST=elasticsearch
KIBANA_HOST=kibana
LOG_LEVEL=INFO
```

### Monitoring Configuration Files

| Component | Configuration File | Purpose |
|-----------|-------------------|---------|
| Prometheus | `monitoring/prometheus/prometheus.yml` | Scrape targets and rules |
| Grafana | `monitoring/grafana/provisioning/` | Dashboards and datasources |
| AlertManager | `monitoring/alertmanager/alertmanager.yml` | Alert routing and notifications |
| Elasticsearch | `monitoring/elasticsearch/elasticsearch.yml` | Cluster and index settings |
| Logstash | `monitoring/logstash/pipeline/logstash.conf` | Log processing pipeline |

## Dashboards

### 1. Application Overview
- Service health status and uptime
- Request rates and response times
- Error rates and success metrics
- Content generation performance
- External service dependencies

### 2. Performance Monitoring
- Response time percentiles (50th, 95th, 99th)
- Throughput and concurrency metrics
- Content generation duration and quality
- Database query performance
- Cache hit rates and efficiency

### 3. Error Analysis
- Error rate trends and patterns
- Exception tracking and categorization
- Failed content generation analysis
- External service failure rates
- System error correlation

### 4. Infrastructure Metrics
- System resource utilization (CPU, memory, disk)
- Container metrics and health
- Network performance and connectivity
- Database connection pools
- Queue sizes and processing rates

### 5. Business Metrics
- Content generation volume and types
- API usage patterns and trends
- User activity and engagement
- Template usage statistics
- Quality score distributions

## Alerting Rules

### Critical Alerts (Immediate Response)
- Application down or unresponsive
- Database connection failures
- High error rates (>5%)
- Critical resource exhaustion (>95% memory/disk)
- External service complete failures

### Warning Alerts (Attention Required)
- High response times (>2s)
- Elevated error rates (>1%)
- Resource usage warnings (>80%)
- Content generation failures (>10%)
- External service degradation

### Info Alerts (Monitoring)
- Traffic pattern changes
- New deployments
- Configuration changes
- Scheduled maintenance events
- Performance trend notifications

## Log Analysis

### Structured Logging Format

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "halcytone-content-generator",
  "logger": "content.generation",
  "message": "Content generation completed",
  "request_id": "req-12345",
  "user_id": "user-789",
  "content_type": "newsletter",
  "template": "modern",
  "duration_seconds": 2.5,
  "quality_score": 0.85,
  "environment": "production"
}
```

### Log Categories

1. **Request Logs**: HTTP requests and responses
2. **Application Logs**: Business logic and operations
3. **Error Logs**: Exceptions and failures
4. **Performance Logs**: Timing and resource usage
5. **Security Logs**: Authentication and authorization
6. **Audit Logs**: User actions and system changes

### Kibana Dashboards

- **Application Overview**: Service health and activity
- **Error Analysis**: Error patterns and troubleshooting
- **Performance Monitoring**: Response times and throughput
- **User Activity**: Request patterns and usage
- **Security Events**: Authentication and access logs

## Distributed Tracing

### Trace Categories

1. **HTTP Requests**: End-to-end request processing
2. **Content Generation**: Content creation workflow
3. **External API Calls**: CRM and Platform service calls
4. **Database Operations**: Query execution and performance
5. **Cache Operations**: Cache hits, misses, and updates
6. **Batch Processing**: Background job execution

### Trace Analysis

- **Latency Analysis**: Identify slow operations
- **Error Tracking**: Trace errors across services
- **Dependency Mapping**: Understand service relationships
- **Performance Optimization**: Find bottlenecks and inefficiencies

## Best Practices

### 1. Monitoring Strategy

- **Golden Signals**: Focus on latency, traffic, errors, and saturation
- **SLI/SLO Definition**: Define service level indicators and objectives
- **Alert Fatigue Prevention**: Tune thresholds and use intelligent routing
- **Baseline Establishment**: Understand normal behavior patterns

### 2. Dashboard Design

- **User-Centric**: Design dashboards for specific roles and use cases
- **Hierarchical Navigation**: Start broad, drill down for details
- **Consistent Timeframes**: Use consistent time windows across dashboards
- **Actionable Insights**: Include links to runbooks and troubleshooting guides

### 3. Log Management

- **Structured Format**: Use consistent JSON logging format
- **Context Enrichment**: Include correlation IDs and user context
- **Sensitive Data**: Filter out passwords, tokens, and PII
- **Retention Policies**: Balance storage costs with debugging needs

### 4. Alerting Philosophy

- **Actionable Alerts**: Only alert on conditions requiring action
- **Clear Ownership**: Route alerts to responsible teams
- **Escalation Paths**: Define clear escalation procedures
- **Alert Fatigue**: Monitor and reduce false positives

## Troubleshooting

### Common Issues

#### High Memory Usage
1. Check application memory metrics
2. Review recent deployment changes
3. Look for memory leaks in traces
4. Check database connection pools

#### Slow Response Times
1. Analyze response time percentiles
2. Check database query performance
3. Review external service latency
4. Examine content generation times

#### High Error Rates
1. Check error logs for patterns
2. Review recent code changes
3. Verify external service status
4. Check resource availability

#### Missing Metrics
1. Verify Prometheus targets are up
2. Check application metrics endpoint
3. Review firewall and network connectivity
4. Validate service discovery configuration

### Monitoring Service Issues

#### Prometheus Not Scraping
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify application metrics endpoint
curl http://localhost:8000/metrics

# Check network connectivity
docker network ls
docker network inspect halcytone_default
```

#### Grafana Dashboard Issues
```bash
# Check Grafana logs
docker logs grafana

# Verify data source configuration
curl -u admin:admin123 http://localhost:3000/api/datasources

# Test Prometheus connectivity
curl http://prometheus:9090/api/v1/query?query=up
```

#### ELK Stack Problems
```bash
# Check Elasticsearch cluster health
curl http://localhost:9200/_cluster/health

# Verify Logstash pipeline
curl http://localhost:9600/_node/stats/pipeline

# Check Kibana status
curl http://localhost:5601/api/status
```

## Maintenance

### Regular Tasks

1. **Index Management**: Clean up old Elasticsearch indexes
2. **Metric Retention**: Monitor Prometheus storage usage
3. **Dashboard Updates**: Keep dashboards current with application changes
4. **Alert Tuning**: Review and adjust alert thresholds
5. **Performance Review**: Analyze monitoring system performance

### Backup and Recovery

1. **Grafana Dashboards**: Export and version control dashboard JSON
2. **Prometheus Data**: Regular snapshots for long-term storage
3. **Elasticsearch Indexes**: Backup critical log data
4. **Configuration Files**: Version control all monitoring configurations

## Security

### Access Control
- Change default passwords
- Implement role-based access control
- Use HTTPS for all external access
- Restrict network access to monitoring services

### Data Protection
- Sanitize sensitive data in logs
- Encrypt data in transit and at rest
- Implement audit logging for monitoring access
- Regular security updates for monitoring components

## Scaling

### Horizontal Scaling
- Multiple Prometheus instances with federation
- Elasticsearch cluster scaling
- Logstash worker scaling
- Load balancing for Grafana

### Vertical Scaling
- Resource allocation optimization
- Storage performance tuning
- Query performance optimization
- Cache configuration tuning

---

## Support

For monitoring stack issues:
1. Check service health endpoints
2. Review component logs
3. Verify network connectivity
4. Consult component-specific documentation
5. Contact the platform team for assistance

**Monitoring Stack Version**: 1.0
**Last Updated**: $(date)
**Maintainer**: Platform Team