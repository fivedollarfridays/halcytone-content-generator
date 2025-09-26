# Performance Testing Framework

A comprehensive performance testing and baseline establishment framework for the Halcytone Content Generator.

## Quick Start

### 1. Install Dependencies

```bash
pip install locust numpy
```

### 2. Start the Application

```bash
# Make sure the Halcytone API is running
python -m uvicorn src.halcytone_content_generator.main:app --host 0.0.0.0 --port 8000
```

### 3. Run Performance Tests

```bash
# Establish baseline performance metrics
python scripts/run_performance_baseline.py --type baseline

# Run complete performance suite
python scripts/run_performance_baseline.py --type complete

# Compare against previous baseline
python scripts/run_performance_baseline.py --type compare --operation mixed_workload_baseline
```

## Framework Components

### Load Testing (`load_tests.py`)

Comprehensive Locust-based load testing with multiple user patterns:

- **HealthCheckUser**: Focus on monitoring endpoints
- **ContentGenerationUser**: Core content generation operations
- **APIExplorationUser**: Various API endpoint testing
- **HeavyWorkloadUser**: High-intensity concurrent operations
- **MixedWorkloadUser**: Realistic combined usage patterns

### Baseline Collection (`baseline.py`)

Automated performance baseline collection and analysis:

- **BaselineCollector**: Collect performance metrics from load tests
- **MetricsAnalyzer**: Compare baselines and detect regressions
- **PerformanceBaseline**: Data structure for baseline storage

### Test Scenarios (`scenarios.py`)

Different performance testing scenarios:

- **BaselineScenario**: Establish performance baselines
- **StressTestScenario**: Find system breaking points
- **SpikeTestScenario**: Test sudden load increases
- **SoakTestScenario**: Extended duration testing

## Usage Examples

### Basic Baseline Collection

```python
from performance.baseline import BaselineCollector
from performance.load_tests import ContentGenerationUser

collector = BaselineCollector("http://localhost:8000")
baseline = collector.collect_baseline(
    user_class=ContentGenerationUser,
    users=10,
    spawn_rate=2,
    run_time=300
)

print(f"P95 Response Time: {baseline.response_time_p95}ms")
print(f"Throughput: {baseline.requests_per_second} RPS")
print(f"Error Rate: {baseline.error_rate:.2%}")
```

### Regression Analysis

```python
from performance.baseline import MetricsAnalyzer, BaselineCollector

collector = BaselineCollector()
analyzer = MetricsAnalyzer(collector)

# Compare current vs previous baseline
previous = collector.get_latest_baseline("content_generation")
current = collector.collect_baseline(...)

analysis = analyzer.compare_baselines(current, previous)
print(f"Overall Assessment: {analysis['overall_assessment']}")
```

### Custom Load Testing

```python
from locust import HttpUser, task, between
from performance.baseline import BaselineCollector

class CustomUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    @task
    def custom_endpoint(self):
        self.client.get("/api/custom-endpoint")

# Collect baseline for custom user pattern
collector = BaselineCollector()
baseline = collector.collect_baseline(CustomUser, users=5, run_time=180)
```

## Command Line Interface

### Available Commands

```bash
# Show help
python scripts/run_performance_baseline.py --help

# Different test types
python scripts/run_performance_baseline.py --type baseline     # Baseline collection
python scripts/run_performance_baseline.py --type stress      # Stress testing
python scripts/run_performance_baseline.py --type spike       # Spike testing
python scripts/run_performance_baseline.py --type soak        # Soak testing
python scripts/run_performance_baseline.py --type complete    # All tests
python scripts/run_performance_baseline.py --type compare     # Compare baselines
python scripts/run_performance_baseline.py --type trend       # Trend analysis
```

### Common Parameters

```bash
--host HOST                    # Target host (default: http://localhost:8000)
--users USERS                  # Concurrent users (default: 10)
--duration DURATION            # Test duration in seconds (default: 300)
--operation OPERATION          # Operation for comparison/trends
--days DAYS                    # Days for trend analysis (default: 30)
--verbose                      # Enable debug logging
--no-health-check             # Skip pre-test health check
```

## Performance Metrics

### Key Performance Indicators

- **Response Time**: Mean, median, P95, P99, max response times
- **Throughput**: Requests per second (RPS)
- **Error Rate**: Percentage of failed requests
- **Concurrency**: Number of concurrent users supported

### Success Criteria

| Operation | P95 Response Time | Min RPS | Max Error Rate |
|-----------|------------------|---------|----------------|
| Health Checks | < 100ms | > 50 | < 0.1% |
| Content Generation | < 5000ms | > 5 | < 5% |
| Mixed Workload | < 3000ms | > 10 | < 2% |

## Results and Reporting

### Storage Structure

```
performance/results/
├── baseline/
│   ├── health_check_baseline_20240101_120000.json
│   ├── content_generation_baseline_20240101_120500.json
│   └── mixed_workload_baseline_20240101_121000.json
├── stress/
│   └── content_generation_stress_20240101_121500.json
├── spike/
│   └── spike_test_20240101_122000.json
└── soak/
    └── soak_test_20240101_123000.json
```

### Baseline Data Format

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
  "test_duration": 300,
  "raw_data": {
    "endpoints": {...},
    "timeline": [...],
    "errors": [...]
  }
}
```

### Report Generation

```python
from performance.baseline import create_baseline_report

baselines = [baseline1, baseline2, baseline3]
report = create_baseline_report(baselines, "performance/results/report.md")
```

Generated reports include:
- Performance summary
- SLI recommendations
- Alert threshold suggestions
- Trend analysis
- Capacity planning guidance

## Integration with Monitoring

### Prometheus Metrics Integration

The performance framework can be integrated with the monitoring stack:

```python
# In your application
from src.halcytone_content_generator.monitoring import setup_metrics

# Metrics will be collected during performance tests
setup_metrics({"service.name": "halcytone-content-generator"})
```

### Grafana Dashboards

Create performance dashboards using baseline data:
- Response time percentiles vs baselines
- Throughput trends over time
- Error rate monitoring
- SLI compliance tracking

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Regression Test
on: [push, pull_request]

jobs:
  performance-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install locust numpy

    - name: Start application
      run: |
        python -m uvicorn src.halcytone_content_generator.main:app &
        sleep 10

    - name: Run baseline test
      run: |
        python scripts/run_performance_baseline.py --type baseline --duration 120

    - name: Check for regressions
      run: |
        python scripts/run_performance_baseline.py --type compare --operation mixed_workload_baseline
```

## Troubleshooting

### Common Issues

1. **Service Not Running**
   ```bash
   # Check if service is accessible
   curl http://localhost:8000/health
   ```

2. **Import Errors**
   ```bash
   # Install missing dependencies
   pip install locust numpy requests
   ```

3. **Permission Errors**
   ```bash
   # Create results directory
   mkdir -p performance/results
   chmod 755 performance/results
   ```

4. **Memory Issues with Large Tests**
   ```bash
   # Reduce concurrent users or test duration
   python scripts/run_performance_baseline.py --users 5 --duration 60
   ```

### Debug Mode

```bash
# Enable verbose logging for troubleshooting
python scripts/run_performance_baseline.py --type baseline --verbose
```

## Best Practices

### 1. Test Environment Consistency
- Use consistent hardware and network conditions
- Test against isolated environment when possible
- Document environmental factors affecting performance

### 2. Realistic Load Patterns
- Model actual user behavior in test scenarios
- Include think time between requests
- Test both peak and average load conditions

### 3. Baseline Management
- Establish baselines early in development
- Update baselines after significant changes
- Maintain historical baseline data for trend analysis

### 4. Regression Detection
- Set appropriate threshold for regression alerts
- Consider baseline variance when setting thresholds
- Investigate all confirmed performance regressions

### 5. Capacity Planning
- Test beyond current requirements
- Model growth scenarios
- Plan scaling strategies based on baseline data

## Advanced Usage

### Custom Test Scenarios

```python
from performance.scenarios import TestScenario
from performance.load_tests import BaseHalcytoneUser

class CustomTestUser(BaseHalcytoneUser):
    @task
    def custom_workflow(self):
        # Implement custom test workflow
        pass

scenario = TestScenario(
    name="custom_test",
    description="Custom test scenario",
    user_classes=[CustomTestUser],
    users=15,
    spawn_rate=2,
    run_time=240,
    objectives=["Test custom functionality"],
    success_criteria={
        "response_time_p95": 2000,
        "error_rate": 0.01,
        "min_rps": 8
    }
)
```

### Trend Analysis

```python
from performance.baseline import MetricsAnalyzer

analyzer = MetricsAnalyzer(collector)
trends = analyzer.analyze_trend("content_generation_baseline", days=30)

print(f"Response time trend: {trends['trends']['response_time_p95']['change_percent']}%")
print(f"Throughput trend: {trends['trends']['requests_per_second']['change_percent']}%")
```

---

For detailed performance baseline documentation, see [`docs/performance-baseline.md`](../docs/performance-baseline.md).

For monitoring stack integration, see [`docs/monitoring-stack.md`](../docs/monitoring-stack.md).