# Performance Baseline Documentation

## Overview

This document establishes performance baselines for the Toombos API to enable detection of performance degradation and support capacity planning decisions. These baselines were established through comprehensive load testing using realistic usage patterns.

## Baseline Collection Methodology

### Testing Framework

- **Tool**: Locust load testing framework
- **Language**: Python 3.11+
- **Architecture**: HTTP-based load testing with multiple user patterns
- **Metrics Collection**: Real-time response time, throughput, and error rate tracking

### Test Environment

- **Target Host**: `http://localhost:8000`
- **Load Generation**: Local machine (development baseline)
- **Duration**: 3-10 minutes per scenario
- **Ramp-up**: Gradual user spawn (1-3 users/second)

### User Patterns Tested

1. **Health Check Pattern** (HealthCheckUser)
   - Focus: System health and monitoring endpoints
   - Weight: Low concurrent load (5 users)
   - Endpoints: `/health`, `/ready`, `/live`, `/metrics`

2. **Content Generation Pattern** (ContentGenerationUser)
   - Focus: Core content generation functionality
   - Weight: Medium concurrent load (10 users)
   - Endpoints: `/api/v2/content/generate`, `/api/v2/content/validate`, `/api/v1/content/batch`

3. **Mixed Workload Pattern** (MixedWorkloadUser)
   - Focus: Realistic combined usage
   - Weight: High concurrent load (20 users)
   - Workflow: Validate → Generate → Status Check

## Service Level Indicators (SLIs)

### Primary SLIs

| Metric | Target | Measurement |
|--------|---------|-------------|
| **Availability** | 99.9% | Error rate < 0.1% |
| **Content Generation Latency** | P95 < 5000ms | 95th percentile response time |
| **Health Check Latency** | P95 < 100ms | 95th percentile response time |
| **API Throughput** | > 10 RPS | Requests per second sustained |

### Secondary SLIs

| Metric | Target | Measurement |
|--------|---------|-------------|
| **Batch Processing Latency** | P95 < 30000ms | Batch operations response time |
| **Validation Latency** | P95 < 1000ms | Content validation response time |
| **Error Recovery** | < 5 minutes | Time to restore normal operation |

## Performance Baselines

### Health Check Endpoints

**Baseline Characteristics:**
- **Concurrent Users**: 5
- **Test Duration**: 180 seconds
- **Target RPS**: 50+
- **Expected P95**: < 100ms
- **Expected Error Rate**: < 0.1%

**Success Criteria:**
```python
{
    "response_time_p95": 100,    # 100ms max
    "error_rate": 0.001,         # 0.1% max
    "min_rps": 50                # At least 50 RPS
}
```

**Endpoints Covered:**
- `GET /health` - Basic health check
- `GET /ready` - Readiness probe
- `GET /live` - Liveness probe
- `GET /metrics` - Prometheus metrics

### Content Generation Operations

**Baseline Characteristics:**
- **Concurrent Users**: 10
- **Test Duration**: 300 seconds
- **Target RPS**: 5+
- **Expected P95**: < 5000ms
- **Expected Error Rate**: < 5%

**Success Criteria:**
```python
{
    "response_time_p95": 5000,   # 5s for content generation
    "error_rate": 0.05,          # 5% max for baseline
    "min_rps": 5                 # At least 5 content generations/sec
}
```

**Operations Covered:**
- `POST /api/v2/content/generate` - Individual content generation
- `POST /api/v2/content/generate/enhanced` - AI-enhanced content
- `POST /api/v1/content/batch` - Batch content generation
- `POST /api/v2/content/validate` - Content validation

### Mixed Realistic Workload

**Baseline Characteristics:**
- **Concurrent Users**: 20
- **Test Duration**: 600 seconds
- **Target RPS**: 10+
- **Expected P95**: < 3000ms
- **Expected Error Rate**: < 2%

**Success Criteria:**
```python
{
    "response_time_p95": 3000,   # 3s for mixed operations
    "error_rate": 0.02,          # 2% max
    "min_rps": 10                # At least 10 operations/sec
}
```

**Workflow Pattern:**
1. Content validation request
2. Content generation request
3. Service status check
4. Periodic health monitoring

## Baseline Execution

### Prerequisites

1. **Application Running**: Halcytone API server running on `http://localhost:8000`
2. **Dependencies**: Install performance testing dependencies
   ```bash
   pip install locust numpy
   ```

3. **Service Health**: All health endpoints responding normally

### Running Baseline Collection

#### Quick Baseline Collection
```bash
python scripts/run_performance_baseline.py --type baseline
```

#### Custom Baseline Parameters
```bash
python scripts/run_performance_baseline.py \
    --type baseline \
    --host http://localhost:8000 \
    --users 15 \
    --duration 420 \
    --verbose
```

#### Complete Performance Suite
```bash
python scripts/run_performance_baseline.py --type complete
```

### Results Storage

- **Location**: `performance/results/`
- **Format**: JSON files with ISO timestamps
- **Naming**: `{operation}_{YYYYMMDD_HHMMSS}.json`
- **Reports**: Markdown reports generated automatically

## Baseline Analysis

### Metrics Collected

Each baseline includes:

```json
{
  "operation": "content_generation_baseline",
  "environment": "baseline",
  "version": "0.1.0",
  "timestamp": "2024-01-01T12:00:00",

  "response_time_mean": 2500.0,
  "response_time_median": 2000.0,
  "response_time_p95": 4500.0,
  "response_time_p99": 8000.0,
  "response_time_max": 12000.0,

  "requests_per_second": 8.5,
  "concurrent_users": 10,
  "total_requests": 2550,

  "error_rate": 0.02,
  "error_count": 51,

  "test_duration": 300
}
```

### Baseline Validation

After collection, each baseline is validated against success criteria:

- ✅ **Pass**: All metrics within acceptable ranges
- ⚠️ **Warning**: Some metrics near thresholds
- ❌ **Fail**: Critical metrics exceed acceptable ranges

### Trend Analysis

Monitor baseline trends over time:

```bash
python scripts/run_performance_baseline.py \
    --type trend \
    --operation content_generation_baseline \
    --days 30
```

**Trend Indicators:**
- **Improving**: Response times decreasing, throughput increasing
- **Stable**: Metrics within 5% variance
- **Degrading**: Response times increasing, throughput decreasing

## Alert Thresholds

### Performance Alerts

Based on established baselines, implement these alert thresholds:

#### Warning Thresholds (25% above baseline)
```yaml
content_generation:
  response_time_p95: 6250ms    # 25% above 5000ms baseline
  throughput_rps: 4.5          # 10% below 5 RPS baseline
  error_rate: 6%               # 1% above 5% baseline

health_checks:
  response_time_p95: 125ms     # 25% above 100ms baseline
  throughput_rps: 45           # 10% below 50 RPS baseline
  error_rate: 0.2%             # 0.1% above 0.1% baseline
```

#### Critical Thresholds (50% above baseline)
```yaml
content_generation:
  response_time_p95: 7500ms    # 50% above baseline
  throughput_rps: 4.0          # 20% below baseline
  error_rate: 10%              # 5% above baseline

health_checks:
  response_time_p95: 150ms     # 50% above baseline
  throughput_rps: 40           # 20% below baseline
  error_rate: 0.5%             # 0.4% above baseline
```

### Alert Actions

- **Warning**: Log alert, notify development team
- **Critical**: Page on-call engineer, trigger incident response
- **Sustained**: Automatic scaling or load shedding

## Performance Regression Testing

### Automated Regression Detection

Compare new performance results against established baselines:

```bash
python scripts/run_performance_baseline.py \
    --type compare \
    --operation content_generation_baseline
```

**Regression Criteria:**
- **Response Time**: > 20% increase in P95
- **Throughput**: > 15% decrease in RPS
- **Error Rate**: > 5% absolute increase

### CI/CD Integration

Integrate performance regression testing in deployment pipeline:

```yaml
# .github/workflows/performance-test.yml
- name: Run Performance Baseline
  run: |
    python scripts/run_performance_baseline.py --type baseline --duration 120

- name: Compare Against Previous Baseline
  run: |
    python scripts/run_performance_baseline.py --type compare --operation mixed_workload_baseline

- name: Fail on Critical Regression
  run: |
    # Parse results and fail build if critical regression detected
```

## Capacity Planning

### Current Capacity (Baseline Environment)

Based on established baselines:

- **Content Generation**: ~5 RPS sustained with 10 concurrent users
- **Health Checks**: ~50 RPS sustained with 5 concurrent users
- **Mixed Workload**: ~10 RPS sustained with 20 concurrent users

### Scaling Recommendations

1. **Horizontal Scaling**: Add instances when approaching 80% of baseline capacity
2. **Vertical Scaling**: Increase resources when P95 > 25% above baseline
3. **Load Balancing**: Distribute load across multiple instances

### Traffic Growth Planning

- **2x Traffic**: Add 1 additional instance, monitor baseline metrics
- **5x Traffic**: Scale to 3-5 instances with load balancer
- **10x Traffic**: Implement caching, async processing, database optimization

## Monitoring Dashboard Integration

### Key Performance Dashboard

Create monitoring dashboards with these baseline-derived metrics:

1. **Response Time Dashboard**
   - P95 response time vs baseline (with alert thresholds)
   - Response time distribution histogram
   - Trend analysis over time

2. **Throughput Dashboard**
   - Current RPS vs baseline capacity
   - Request volume trends
   - Peak load analysis

3. **Error Rate Dashboard**
   - Error rate percentage vs baseline
   - Error categorization (4xx, 5xx)
   - Error rate correlation with load

4. **SLI Compliance Dashboard**
   - SLI achievement percentage
   - SLI trend over time
   - Alert frequency analysis

## Maintenance and Updates

### Baseline Refresh Schedule

- **Weekly**: Collect new baselines for trending
- **Monthly**: Review and update SLI targets
- **Quarterly**: Full baseline recalibration
- **After Major Releases**: New baseline establishment

### Baseline Evolution

As the system evolves, baselines should be updated to reflect:

- **Performance Improvements**: Lower response times, higher throughput
- **New Features**: Additional endpoints and operations
- **Infrastructure Changes**: Different hardware, cloud environments
- **Scale Changes**: Different user patterns and load levels

---

## Usage Examples

### Establish Initial Baselines
```bash
# Run comprehensive baseline collection
python scripts/run_performance_baseline.py --type complete

# Quick health check baseline
python scripts/run_performance_baseline.py --type baseline --duration 180
```

### Monitor for Regressions
```bash
# Compare current performance against last baseline
python scripts/run_performance_baseline.py --type compare --operation mixed_workload_baseline

# Analyze performance trends
python scripts/run_performance_baseline.py --type trend --operation content_generation_baseline --days 7
```

### Stress Testing
```bash
# Find system breaking points
python scripts/run_performance_baseline.py --type stress --users 50 --duration 300

# Test spike resilience
python scripts/run_performance_baseline.py --type spike
```

---

**Document Version**: 1.0
**Last Updated**: 2024-01-01
**Next Review**: 2024-04-01
**Owner**: Platform Team