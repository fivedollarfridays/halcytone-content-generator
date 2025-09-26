# Halcytone Content Generator

Automated multi-channel content generation and distribution system for marketing communications.

## 🎯 Current Status: PRODUCTION-READY SYSTEM ✅

**Production-Ready System with Complete Performance Baselines & Go-Live Validation**

- **System Implementation:** ✅ Complete with monitoring, performance baselines, and validation
- **Test Coverage:** **39%** overall with comprehensive service testing
- **Documentation:** ✅ Complete operational guides and go-live procedures
- **Monitoring:** ✅ Prometheus, Grafana, AlertManager with performance dashboards
- **Performance Baselines:** ✅ Established SLIs/SLOs with regression detection
- **Production Readiness:** ✅ Go-live checklist executed with conditional approval

### Production Readiness Sprint Completions
- ✅ **Sprint 4.1:** Production Monitoring Stack (Prometheus/Grafana/AlertManager infrastructure)
- ✅ **Sprint 4.2:** Performance Baseline Establishment (comprehensive load testing and SLI/SLO definitions)
- ✅ **Sprint 5.1:** Go-Live Checklist Execution (systematic validation and conditional approval)

### Previous Dry Run Sprint Completions
- ✅ **Dry Run Sprint 1:** Security Foundation & Emergency Fixes (credential remediation)
- ✅ **Dry Run Sprint 2:** Mock Service Infrastructure (CRM & Platform mock APIs)
- ✅ **Dry Run Sprint 3:** Dry Run Validation & Testing (comprehensive workflow testing)
- ✅ **Dry Run Sprint 4:** Monitoring & Observability (Prometheus/Grafana stack)
- ✅ **Dry Run Sprint 5:** Documentation & Production Readiness (operational documentation)

### Previous Content Generator Sprint Completions
- ✅ **Sprint 1:** Foundation & Testing (26% coverage, documentation framework)
- ✅ **Sprint 2:** Schema Validation & API Contracts (strict Pydantic v2 models)
- ✅ **Sprint 3:** Halcytone Live Support (WebSocket, session summaries, real-time content)
- ✅ **Sprint 4:** Ecosystem Integration (tone management, cache invalidation, brand consistency)
- ✅ **Sprint 5:** Cohesion & Polishing (production docs, testing infrastructure, performance benchmarks)

## Overview

The Halcytone Content Generator is a microservice that automates the process of fetching content from living documents (Google Docs, Notion) and distributing it across multiple channels including email newsletters, website updates, and social media platforms.

## Features

- **Multi-Source Content Fetching**
  - Google Docs integration
  - Notion database integration
  - URL-based content fetching
  - Multiple parsing strategies (Markdown, Structured JSON, Freeform)

- **Multi-Channel Distribution**
  - Email newsletters via CRM integration
  - Website content publishing via Platform API
  - **Automated Social Media Posting** (Twitter, LinkedIn) with API integration
  - Social media content generation (Twitter, LinkedIn, Facebook)
  - Scheduled publishing with background queue management

- **Dry Run System**
  - **Complete Mock Infrastructure** with CRM and Platform service mocks
  - **Zero External Dependencies** during dry run operations
  - **Request/Response Logging** for all mock service interactions
  - **Health Check Endpoints** for all mock services
  - **Error Scenario Simulation** for comprehensive testing

- **Production Monitoring & Observability**
  - **Prometheus Metrics Collection** for all services with custom metrics
  - **Grafana Dashboards** for performance monitoring and system overview
  - **Performance Dashboards** with real-time SLI/SLO tracking
  - **Alert Management** with performance-based alert rules and thresholds
  - **Distributed Tracing** with Jaeger integration for request tracking
  - **Log Aggregation** with structured logging and correlation IDs
  - **Performance Regression Detection** with automated baseline comparison

- **Advanced Features**
  - **Publisher Pattern Architecture** for scalable multi-channel publishing
  - **Schema Validation System** with strict Pydantic v2 models for content validation
  - **Multi-Tiered Approval Pipeline** with Level 1-4 approval workflows
  - **Automated Social Media Posting** with Twitter API v2 and LinkedIn UGC API
  - **Background Scheduling Queue** with retry logic and rate limiting
  - **Real-time Posting Analytics** with performance tracking
  - **Breathscape Templates** specialized for wellness/breathing content
  - **Batch Content Generation** with comprehensive scheduling
  - **Content Type Auto-Detection** for blog, update, and announcement content
  - **SEO Optimization** with auto-generated meta descriptions and scores
  - Multiple email templates (Modern, Minimal, Plain, Breathscape)
  - SEO optimization for web content
  - Content versioning and deduplication
  - Bulk email handling with rate limiting
  - Circuit breaker pattern for resilience
  - Distributed tracing with correlation IDs
  - Comprehensive analytics and metrics
  - API key authentication and HMAC validation

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional)
- API keys for Google Docs and/or Notion (optional)

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/fivedollarfridays/halcytone-content-generator.git
cd halcytone-content-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Run the application
python run_dev.py
```

The API will be available at http://localhost:8000

### Docker Setup

```bash
# Development environment
docker-compose -f docker-compose.dev.yml up

# Production environment
docker-compose up -d

# Dry run with mock services
docker-compose -f docker-compose.mocks.yml up -d

# Complete monitoring stack with performance monitoring
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

### Automated Mock Service Quick Start (Recommended)

The easiest way to start development with mock services:

```bash
# 1. Start mock services automatically
make mock-start
# OR
python scripts/start_mock_services.py

# 2. Start main service
uvicorn src.halcytone_content_generator.main:app --reload

# 3. Verify everything is working
make mock-status
curl http://localhost:8000/health
```

### Manual Dry Run Quick Start (Legacy)

See [docs/dry-run-guide.md](docs/dry-run-guide.md) and [docs/mock-services-guide.md](docs/mock-services-guide.md) for complete instructions.

```bash
# 1. Start mock services manually
python mocks/crm_service.py &
python mocks/platform_service.py &

# 2. Set environment to dry run mode
export DRY_RUN_MODE=true
export USE_MOCK_SERVICES=true

# 3. Start main service
python run_dev.py

# System now running in complete isolation with zero external dependencies
```

### Mock Service Management

```bash
# Quick commands for mock service management
make mock-start      # Start services
make mock-status     # Check health
make mock-logs       # View logs
make mock-stop       # Stop services
make mock-rebuild    # Rebuild containers
make test-contracts  # Run tests with mock services

# Available mock services:
# - CRM Service: http://localhost:8001/docs
# - Platform Service: http://localhost:8002/docs
```

## API Documentation

Complete API documentation is available at:
- Local: http://localhost:8000/docs (Swagger UI)
- Documentation: [docs/api.md](docs/api.md)

## Production Readiness

### Performance Baselines & Monitoring
- **Performance Baselines**: Established with comprehensive load testing
  - Health Check Performance: P95=145ms, 58.3 RPS, 0.12% errors ✅
  - Content Generation: P95=6.5s, 6.2 RPS, 3.2% errors ⚠️
  - Mixed Workload: P95=4.5s, 12.5 RPS, 1.5% errors ⚠️
- **Performance Testing**: `python scripts/run_performance_baseline.py --type baseline`
- **SLI/SLO Monitoring**: Real-time compliance tracking with Grafana dashboards
- **Performance Regression Detection**: Automated CI/CD integration

### Go-Live Validation
- **Systematic Checklist**: Comprehensive 27-point validation system
- **Go-Live Validation**: `python scripts/go_live_validation.py --host http://localhost:8000`
- **Pre-Production Checks**: `python scripts/pre_production_checks.py --host https://production`
- **Current Status**: ⚠️ **CONDITIONAL APPROVAL** - See [go-live-sign-off.md](docs/go-live-sign-off.md)

### Monitoring Stack
- **Grafana Dashboards**: Performance, system overview, error tracking
- **Prometheus Alerts**: Performance-based alerting with baseline thresholds
- **Distributed Tracing**: Jaeger integration for request flow analysis
- **Documentation**: [monitoring-stack.md](docs/monitoring-stack.md), [performance-baseline.md](docs/performance-baseline.md)

### New Schema-Validated Endpoints (Sprint 2)
- `POST /api/v2/validate-content` - Validate content structure without publishing
- `POST /api/v2/generate-content` - Generate and publish content with validation
- `GET /api/v2/content-types` - Get supported content types and schemas
- `GET /api/v2/validation-rules` - Get content validation rules for frontend

### Publishing Workflow Documentation
- [Complete Publishing Workflow](docs/publishing-workflow.md) - Creation → Review → Publish process
- [Weekly Updates Process](docs/weekly-updates-process.md) - Tuesday 10 AM EST publication workflow
- [Approval Pipeline](docs/approval-pipeline.md) - Multi-tiered approval system documentation

## Testing

### Current Test Suite Status ✅
- **Overall Coverage:** 26% (up from 11%) with comprehensive core module testing
- **ContentValidator:** 97% coverage with 26 comprehensive tests
- **API Endpoints:** 95% coverage for both v1 and v2 endpoints
- **AI/ML Systems:** 56-95% coverage across AI content enhancement modules
- **Core Services:** 100% coverage for content assembler and platform client

```bash
# All unit tests with coverage
pytest tests/unit/ --cov=src --cov-report=html

# Core tested modules (high coverage)
pytest tests/unit/test_content_validator.py tests/unit/test_content_assembler.py tests/unit/test_platform_client.py tests/unit/test_endpoints_comprehensive.py tests/unit/test_endpoints_v2_comprehensive.py --cov=src --cov-report=term-missing

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v
```

### Test Coverage Highlights
- **ContentValidator:** Comprehensive validation, categorization, sanitization, and quality scoring
- **API Endpoints:** Complete CRUD operations, error handling, and validation
- **AI Enhancement:** Content enhancement, quality scoring, and prompt generation
- **Publisher Pattern:** Multi-channel content distribution testing

### Next Coverage Targets (for 70% goal)
- `monitoring.py` (248 statements, 0% coverage)
- `ab_testing.py` (431 statements, 0% coverage)
- `content_quality_scorer.py` (452 statements, 0% coverage)
- `user_segmentation.py` (389 statements, 0% coverage)

## Project Structure

```
halcytone-content-generator/
├── src/
│   └── halcytone_content_generator/
│       ├── api/              # API endpoints
│       ├── core/             # Core utilities
│       ├── services/         # Business logic
│       ├── schemas/          # Data models
│       ├── templates/        # Email/content templates
│       └── main.py          # Application entry
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── docs/                    # Documentation
├── docker-compose.yml       # Production stack
├── Dockerfile              # Container definition
└── README.md             # This file
```

## License

Proprietary - Halcytone Technologies