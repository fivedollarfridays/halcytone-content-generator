# Health Check Implementation

## Overview

The Halcytone Content Generator implements comprehensive health checks for production monitoring, container orchestration, and operational visibility. The system provides multiple endpoints optimized for different use cases.

## Health Check Endpoints

### Core Endpoints

| Endpoint | Purpose | Response Codes | Use Case |
|----------|---------|----------------|----------|
| `/health` | Basic health status | 200, 503 | Load balancers, basic monitoring |
| `/health/detailed` | Detailed component health | 200, 503 | Debugging, comprehensive monitoring |
| `/ready` | Readiness check | 200, 503 | Kubernetes readiness probe |
| `/live` | Liveness check | 200, 503 | Kubernetes liveness probe |
| `/startup` | Startup probe | 200, 503 | Kubernetes startup probe |
| `/metrics` | Prometheus metrics | 200 | Metrics collection |

### Administrative Endpoints

| Endpoint | Purpose | Method | Use Case |
|----------|---------|--------|----------|
| `/health/check/{component}` | Manual component check | POST | Debugging, testing |

## Health Check Components

The system monitors the following components:

### 1. Database Connectivity
- **Component**: `database`
- **Check**: Connection and query execution
- **Healthy**: Connection successful, queries responding
- **Degraded**: Connection slow or intermittent
- **Unhealthy**: Connection failed or timeout

### 2. Cache System
- **Component**: `cache`
- **Check**: Set/get/delete operations
- **Healthy**: All operations successful
- **Degraded**: Some operations failing
- **Unhealthy**: Cache unavailable

### 3. External Services
- **Component**: `external_services`
- **Check**: CRM and Platform API connectivity
- **Healthy**: All services responding
- **Degraded**: Some services slow or unavailable
- **Unhealthy**: Multiple services failing

### 4. System Resources
- **Components**: `disk_space`, `memory`, `cpu`
- **Check**: Resource usage monitoring
- **Healthy**: < 75% usage
- **Degraded**: 75-90% usage
- **Unhealthy**: > 90% usage

## Response Formats

### Basic Health Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "halcytone-content-generator",
  "version": "0.1.0",
  "environment": "production",
  "uptime_seconds": 3600.5
}
```

### Detailed Health Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "halcytone-content-generator",
  "version": "0.1.0",
  "environment": "production",
  "uptime_seconds": 3600.5,
  "components": {
    "database": {
      "name": "database",
      "status": "healthy",
      "message": "Database connection healthy",
      "response_time_ms": 15.2,
      "last_check": "2024-01-01T12:00:00Z",
      "metadata": {
        "connection_pool_size": 20,
        "active_connections": 5
      }
    }
  },
  "checks_passed": 5,
  "checks_failed": 0,
  "checks_total": 5,
  "response_time_ms": 125.3,
  "warnings": [],
  "errors": []
}
```

### Readiness Response
```json
{
  "ready": true,
  "timestamp": "2024-01-01T12:00:00Z",
  "checks": [
    {
      "name": "configuration",
      "ready": true,
      "message": "Required configuration present",
      "required": true
    },
    {
      "name": "database",
      "ready": true,
      "message": "Database connected",
      "required": true
    }
  ],
  "total_checks": 5,
  "passed_checks": 5,
  "failed_checks": 0,
  "required_checks_passed": true
}
```

### Liveness Response
```json
{
  "alive": true,
  "timestamp": "2024-01-01T12:00:00Z",
  "pid": 12345,
  "memory_usage_mb": 256.7,
  "cpu_percent": 12.5,
  "thread_count": 8
}
```

## Configuration

Health checks can be configured through environment variables or the enhanced configuration system:

```env
# Health check configuration
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
HEALTH_CHECK_FAILURE_THRESHOLD=3
HEALTH_CHECK_SUCCESS_THRESHOLD=1
HEALTH_CHECK_CACHE_TTL=5

# Component-specific checks
HEALTH_CHECK_DATABASE=true
HEALTH_CHECK_CACHE=true
HEALTH_CHECK_EXTERNAL_APIS=true
HEALTH_CHECK_SYSTEM_RESOURCES=true
```

## Kubernetes Integration

### Liveness Probe
```yaml
livenessProbe:
  httpGet:
    path: /live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Readiness Probe
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
  successThreshold: 1
```

### Startup Probe
```yaml
startupProbe:
  httpGet:
    path: /startup
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 20
  successThreshold: 1
```

## Monitoring Integration

### Prometheus Metrics

The `/metrics` endpoint provides Prometheus-compatible metrics:

```
# HELP app_uptime_seconds Application uptime in seconds
# TYPE app_uptime_seconds gauge
app_uptime_seconds{service="halcytone-content-generator",environment="production"} 3600.5

# HELP app_component_health Component health status (1=healthy, 0=unhealthy)
# TYPE app_component_health gauge
app_component_health{component="database",service="halcytone-content-generator",environment="production"} 1

# HELP app_memory_usage_percent Memory usage percentage
# TYPE app_memory_usage_percent gauge
app_memory_usage_percent{service="halcytone-content-generator",environment="production"} 45.2
```

### Alerting Rules

Example Prometheus alerting rules:

```yaml
groups:
- name: halcytone-health
  rules:
  - alert: ServiceUnhealthy
    expr: app_component_health{service="halcytone-content-generator"} == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Halcytone component {{ $labels.component }} is unhealthy"

  - alert: HighMemoryUsage
    expr: app_memory_usage_percent{service="halcytone-content-generator"} > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage: {{ $value }}%"
```

## Health Check Logic

### Status Determination

1. **Healthy**: All checks pass within acceptable response times
2. **Degraded**: Some non-critical checks fail or response times are elevated
3. **Unhealthy**: Critical checks fail or system resources are exhausted
4. **Unknown**: Unable to determine status due to errors

### Failure Thresholds

- **CPU Usage**: > 90% = Unhealthy, > 75% = Degraded
- **Memory Usage**: > 90% = Unhealthy, > 80% = Degraded
- **Disk Usage**: > 90% = Unhealthy, > 80% = Degraded
- **Response Time**: > 10s = Unhealthy, > 5s = Degraded
- **Error Rate**: > 50% = Unhealthy, > 10% = Degraded

### Caching Strategy

Health check results are cached for 5 seconds by default to:
- Reduce system load during high-frequency polling
- Prevent cascading failures
- Improve response times for monitoring systems

## Troubleshooting

### Common Issues

#### 503 Service Unavailable
- Check individual components in `/health/detailed`
- Verify external service connectivity
- Check system resource usage

#### Slow Response Times
- Check database connection pool
- Verify cache performance
- Monitor system resources

#### Readiness Check Failures
- Validate required configuration
- Check external service endpoints
- Verify database connectivity

### Debug Commands

```bash
# Check basic health
curl http://localhost:8000/health

# Get detailed component status
curl http://localhost:8000/health/detailed

# Check readiness
curl http://localhost:8000/ready

# Force check specific component
curl -X POST http://localhost:8000/health/check/database

# Get Prometheus metrics
curl http://localhost:8000/metrics
```

### Manual Testing

Use the provided test script:

```bash
python test_health_simple.py --url http://localhost:8000
```

## Production Considerations

### Load Balancer Configuration

Configure load balancers to use `/health` for basic health checks:

```nginx
upstream halcytone {
    server app1:8000 max_fails=3 fail_timeout=30s;
    server app2:8000 max_fails=3 fail_timeout=30s;
}

location /health {
    access_log off;
    return 200;
}
```

### Monitoring Setup

1. **Basic Monitoring**: Poll `/health` every 30 seconds
2. **Detailed Monitoring**: Poll `/health/detailed` every 5 minutes
3. **Alerting**: Set up alerts on component failures
4. **Metrics**: Scrape `/metrics` every 15 seconds

### Performance Impact

Health checks are designed to be lightweight:
- Basic health check: < 10ms response time
- Detailed health check: < 100ms response time
- Database check: Single connection test
- Cache check: Minimal read/write operations
- System checks: Use cached system information

## Security Considerations

- Health endpoints do not require authentication
- Detailed responses may contain sensitive information
- Restrict access to administrative endpoints
- Monitor for health endpoint abuse
- Consider rate limiting for detailed checks

## Future Enhancements

Planned improvements:
- Custom health check plugins
- Health check history tracking
- Advanced alerting integration
- Performance benchmarking
- Distributed health checking