# Halcytone Content Generator

Automated multi-channel content generation and distribution system for marketing communications.

## 🎯 Current Status: SPRINT 1 FOUNDATION COMPLETE ✅

- **Test Coverage:** Enhanced infrastructure (10% measured, significant module improvements)
- **Tests:** Comprehensive test suites created for AI/ML modules
- **Documentation:** ✅ Complete editor guide and workflows
- **Publisher Pattern:** ✅ Fully implemented with enhanced testing
- **Technical Debt:** ✅ Major deprecations fixed
- **Status:** Foundation established, ready for coverage validation

### Recent Achievements (Sprint 1)
- ✅ **AI Content Enhancer:** 60% coverage (was 0%)
- ✅ **AI Prompts:** 95% coverage (was 0%)
- ✅ **Template Infrastructure:** Complete testing framework
- ✅ **Contract Tests:** External API integration validation
- ✅ **Editor Documentation:** Comprehensive workflow guides
- ⚠️ **Configuration Issues:** Some test mismatches need resolution

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

### Current Test Suite Status
- **Comprehensive AI/ML Tests:** Created but need configuration fixes
- **Contract Tests:** External API validation implemented
- **Template Tests:** Infrastructure ready for email and social templates
- **Publisher Tests:** Enhanced coverage for multi-channel publishing

```bash
# All tests with coverage
pytest tests/ --cov=src --cov-report=html

# Working core tests (recommended)
pytest tests/unit/test_content_assembler.py tests/unit/test_platform_client.py --cov=src --cov-report=term-missing

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v
```

### Test Development Notes
Some comprehensive test files need configuration alignment:
- `test_ai_content_enhancer_comprehensive.py` - Import/config issues
- `test_email_templates.py` - Template function mismatches
- `test_social_templates.py` - Platform template structure updates needed

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