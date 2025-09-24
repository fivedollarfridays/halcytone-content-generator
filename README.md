# Halcytone Content Generator

Automated multi-channel content generation and distribution system for marketing communications.

## 🎯 Current Status: SPRINT 1 FOUNDATION COMPLETE ✅

- **Test Coverage:** **26%** overall (up from 11% - significant improvement achieved)
- **Core Systems:** Comprehensive test coverage for critical components
- **Documentation:** ✅ Complete editor guide and workflows
- **Publisher Pattern:** ✅ Fully implemented with enhanced testing
- **Technical Debt:** ✅ Major deprecations and test failures resolved
- **Status:** Foundation established with robust test infrastructure

### Recent Achievements (Sprint 1)
- ✅ **ContentValidator:** 97% coverage (158 statements - comprehensive validation system)
- ✅ **Endpoints API:** 95% coverage for both v1 and v2 (204 statements total)
- ✅ **AI Content Enhancer:** 56% coverage (was 0%)
- ✅ **AI Prompts:** 95% coverage (was 0%)
- ✅ **Content Assembler:** 100% coverage (64 statements)
- ✅ **Platform Client:** 100% coverage (46 statements)
- ✅ **Test Failures:** All 22 test failures resolved
- ✅ **Template Infrastructure:** Complete testing framework with 26 ContentValidator tests

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

- **Advanced Features**
  - **Publisher Pattern Architecture** for scalable multi-channel publishing
  - **Automated Social Media Posting** with Twitter API v2 and LinkedIn UGC API
  - **Background Scheduling Queue** with retry logic and rate limiting
  - **Real-time Posting Analytics** with performance tracking
  - **Breathscape Templates** specialized for wellness/breathing content
  - **Dry-run Mode** for safe content preview and testing
  - **Batch Content Generation** with comprehensive scheduling
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
```

## API Documentation

Complete API documentation is available at:
- Local: http://localhost:8000/docs (Swagger UI)
- Documentation: [docs/API.md](docs/API.md)

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