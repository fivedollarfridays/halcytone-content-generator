# Incremental Test Coverage Plan: 25% → 70%

**Created:** 2025-10-07
**Target Completion:** 2025-10-25 (18 days)
**Current Coverage:** 25-30% (estimated)
**Target Coverage:** 70%
**Gap:** 40-45 percentage points
**Estimated Effort:** 35-40 hours (5-6 working days)

---

## Executive Summary

This document outlines the phased approach to increase test coverage from current 25-30% to 70% target. The plan prioritizes:
1. **Zero-coverage modules first** (highest impact)
2. **Fixing existing failing tests** (quick wins)
3. **Enhancing medium-coverage modules** (polish)

**Key Strategy:** Incremental progress with daily coverage tracking to ensure we stay on target.

---

## Coverage Progression Roadmap

| Phase | Duration | Modules | Tests | Coverage Gain | Target |
|-------|----------|---------|-------|---------------|--------|
| **Start** | - | Baseline | 650+ | - | **25-30%** |
| **Phase 1** | 3 days | 3 zero-coverage modules | +135 | +15-20% | **40-45%** |
| **Phase 2** | 1 day | Fix failing tests | +40 fixed | +5-8% | **45-53%** |
| **Phase 3** | 1 day | main.py enhancement | +10 | +2-3% | **47-56%** |
| **Phase 4** | 2 days | Infrastructure modules | +60-85 | +5-10% | **52-66%** |
| **Phase 5** | 1-2 days | Final gap closing | Variable | +4-8% | **70%+** ✅ |

---

## Phase 1: Critical Zero-Coverage Modules (Days 1-3)

**Goal:** Address 3 modules with 0% coverage (1,778 lines of untested code)
**Expected Coverage Gain:** +15-20 percentage points
**Duration:** 24 hours (3 days)
**Target After Phase 1:** 40-45% overall coverage

### Day 1-2: services/email_analytics.py
**Lines:** 504 | **Current Coverage:** 0% | **Target:** 75%+ | **Time:** 8 hours

**Test File:** `tests/unit/test_email_analytics_comprehensive.py` (45 tests)

**Test Categories:**
1. Analytics Collection (12 tests) - Track opens, clicks, bounces, engagement
2. Performance Metrics (10 tests) - Calculate rates, scores, aggregations
3. Campaign Analytics (8 tests) - Campaign summaries, comparisons, tracking
4. Recipient Behavior (8 tests) - Individual tracking, engagement patterns
5. Data Export & Reporting (7 tests) - CSV/JSON export, report generation

---

### Day 3: services/content_sync.py
**Lines:** 578 | **Current Coverage:** 0% | **Target:** 75%+ | **Time:** 8 hours

**Test File:** `tests/unit/test_content_sync_comprehensive.py` (48 tests)

**Test Categories:**
1. Sync Orchestration (10 tests) - Multi-platform sync, retries, rollbacks
2. Conflict Resolution (12 tests) - Detect and resolve content conflicts
3. Sync Status Tracking (10 tests) - Progress tracking, queue management
4. Platform Integration (8 tests) - Email, web, social platform sync
5. Sync Operations (8 tests) - Full/incremental/delta sync modes

---

### Day 4: api/endpoints_schema_validated.py
**Lines:** 696 | **Current Coverage:** 0% | **Target:** 70%+ | **Time:** 8 hours

**Test File:** `tests/unit/test_endpoints_schema_validated_comprehensive.py` (42 tests)

**Test Categories:**
1. Content Generation Endpoints (10 tests) - Validated blog, updates, announcements
2. Validation Endpoints (8 tests) - Content validation with warnings and errors
3. Publishing Workflows (10 tests) - Multi-channel publishing with validation
4. Newsletter Endpoints (7 tests) - Newsletter generation and validation
5. Error Handling & Edge Cases (7 tests) - Invalid data, auth failures, timeouts

---

## Phase 2: Fix Failing Tests (Day 5)

**Goal:** Fix 40 failing tests to boost coverage quickly
**Expected Coverage Gain:** +5-8 percentage points
**Duration:** 6 hours (1 day)
**Target After Phase 2:** 45-53% overall coverage

### Part A: services/monitoring.py (4 hours)
**Current:** ~15% coverage, 26 tests failing
**Target:** 70%+ coverage, all tests passing

**Fix Strategy:**
- Update OpenTelemetry mocks
- Fix tracer/meter initialization
- Correct metric collection assertions
- Fix system resource mocks (psutil)

**File:** `tests/unit/test_monitoring.py` (26 tests to fix)

### Part B: api/endpoints_v2.py (2 hours)
**Current:** 28% coverage, 14 tests failing
**Target:** 50%+ coverage, all tests passing + 10 new tests

**Fix Strategy:**
- Fix async mocks for external dependencies
- Update validation error assertions
- Add 10 new tests for uncovered paths

**File:** `tests/unit/test_endpoints_v2_comprehensive.py` (14 fixes + 10 new)

---

## Phase 3: Enhance Medium-Coverage Modules (Day 6)

**Goal:** Boost main.py from 46% to 75%+
**Expected Coverage Gain:** +2-3 percentage points
**Duration:** 2 hours
**Target After Phase 3:** 47-56% overall coverage

### main.py Integration Tests
**Lines:** 132 | **Current:** 46% | **Target:** 75%+ | **Time:** 2 hours

**Add 10 new tests:**
- Application lifecycle (4 tests) - Startup, shutdown, middleware
- Router integration (3 tests) - All routers mounted, CORS config
- Health & monitoring (3 tests) - Prometheus, health manager

**File:** `tests/unit/test_main.py` (10 new tests + 2 fixes)

---

## Phase 4: Infrastructure & Remaining Gaps (Days 7-8)

**Goal:** Test infrastructure modules
**Expected Coverage Gain:** +5-10 percentage points
**Duration:** 8-10 hours (2 days)
**Target After Phase 4:** 52-66% overall coverage

**Priority Modules:**
1. Database modules (if exist) - 20-30 tests, 4 hours
2. External service clients - 25-35 tests, 4 hours
3. Remaining API endpoints - 15-20 tests, 2 hours

---

## Phase 5: Final Push to 70% (Days 9-10)

**Goal:** Close remaining gaps to reach 70% target
**Expected Coverage Gain:** +4-8 percentage points
**Duration:** Variable (2-8 hours)
**Target:** **70%+ overall coverage** ✅

**Activities:**
1. Run full coverage analysis
2. Identify highest-impact gaps
3. Add targeted tests for uncovered branches
4. Validate 70% target achieved
5. Generate final coverage report

---

## Daily Progress Template

```markdown
## Day X: [Date] - [Module Name]

### Target
- Module: [name]
- Lines: [count]
- Target Coverage: X%
- Estimated Tests: X

### Progress
- Tests created: X
- Tests passing: X
- Module coverage achieved: X%
- Overall project coverage: X%

### Blockers
- [None or describe]

### Notes
- [Key observations]
```

---

## Success Milestones

✅ **Milestone 1 (Day 3):** 40-45% coverage - Zero-coverage modules complete
✅ **Milestone 2 (Day 5):** 45-53% coverage - All failing tests fixed
✅ **Milestone 3 (Day 6):** 47-56% coverage - main.py enhanced
✅ **Milestone 4 (Day 8):** 52-66% coverage - Infrastructure tested
🎯 **Milestone 5 (Day 10):** **70%+ coverage - PHASE 1 COMPLETE**

---

## Quick Reference Commands

```bash
# Run coverage for specific module
pytest tests/unit/test_[module].py --cov=src.halcytone_content_generator.[path] --cov-report=term-missing

# Run all unit tests with coverage
pytest tests/unit/ --cov=src.halcytone_content_generator --cov-report=html --cov-report=term

# Generate HTML coverage report
pytest tests/unit/ --cov=src.halcytone_content_generator --cov-report=html
# View at: htmlcov/index.html

# Quick coverage summary
coverage report --include="src/halcytone_content_generator/*"
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Tests take longer than estimated | Use existing tests as templates, focus on high-value tests first |
| Unforeseen complexity | 20% time buffer allocated, can defer Phase 4 if needed |
| Code issues discovered | Document but don't fix, mock around issues |

---

## Post-70% Activities

1. Generate final coverage report
2. Update all documentation
3. Mark Phase 1 sprint as COMPLETE
4. Plan Phase 2B (Dashboard features)
5. Celebrate achievement! 🎉

---

**Related Documents:**
- Coverage summary: `docs/coverage-summary-2025-10-07.md`
- Daily progress log: `docs/daily-progress-log.md` (to be created)
- Sprint status: `context/development.md`
