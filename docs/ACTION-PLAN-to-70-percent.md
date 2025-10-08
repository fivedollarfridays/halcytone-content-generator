# Action Plan: Reaching 70% Test Coverage
**Created**: 2025-10-07, Post Session 10
**Current Coverage**: 41-42% (4,766/11,698 statements)
**Target Coverage**: 70% (8,189/11,698 statements)
**Gap**: 3,423 statements needed

---

## Phase 0: Immediate - Test Discovery Audit (Session 11)
**Duration**: 2-3 hours
**Expected Gain**: 400-600 statements (test discovery, not new tests)

### Objectives
Verify which tests exist but aren't being discovered/run properly.

### Tasks
1. **Run targeted tests for "completed" modules** (1 hour)
   ```bash
   pytest tests/unit/test_personalization*.py --cov=services.personalization
   pytest tests/unit/test_user_segmentation*.py --cov=services.user_segmentation
   pytest tests/unit/test_ab_testing*.py --cov=services.ab_testing
   pytest tests/unit/test_cache_manager*.py --cov=services.cache_manager
   pytest tests/unit/test_tone_manager*.py --cov=services.tone_manager
   ```

2. **Document actual coverage** (30 min)
   - Record real coverage for each module
   - Identify gaps between claimed and actual
   - Update baseline coverage numbers

3. **Fix test discovery issues** (1 hour)
   - Review pytest.ini and test configuration
   - Fix import paths if needed
   - Ensure all test files are discovered

### Expected Outcome
- **Optimistic**: Find 500-600 already-tested statements
- **Realistic**: Find 300-400 already-tested statements
- **Updated baseline**: 42-45% coverage verified

---

## Phase 1: High-Impact Services (Sessions 12-14)
**Duration**: 4-5 days (3 sessions @ 3-4 hours each)
**Expected Gain**: 800 statements → +6.8 percentage points
**Target Coverage After**: 48-52%

### Session 12: Social Publisher (3-4 hours)
**Module**: services/publishers/social_publisher.py
**Current**: 24% | **Target**: 70% | **Gap**: 225 statements

#### Test Strategy
Create 60-80 comprehensive tests covering:
- **Platform-specific publishing** (20 tests)
  - Twitter: 280 char limit, hashtags, threads
  - LinkedIn: professional tone, article mode
  - Facebook: engagement optimization, link preview
  - Instagram: image requirements, caption formatting

- **Content validation** (15 tests)
  - Character limits per platform
  - Image/video requirements
  - Hashtag validation
  - URL handling

- **Publishing workflow** (15 tests)
  - Single post publishing
  - Cross-platform publishing
  - Scheduled posts
  - Draft mode

- **Error handling** (10 tests)
  - API failures
  - Rate limiting
  - Retry logic
  - Fallback strategies

- **Analytics integration** (10 tests)
  - Post tracking
  - Engagement metrics
  - Performance analytics

### Session 13: A/B Testing Service (3-4 hours)
**Module**: services/ab_testing.py
**Current**: 0-31% | **Target**: 70% | **Gap**: 300 statements

#### Test Strategy
Create 50-70 comprehensive tests covering:
- **Test creation and management** (15 tests)
  - Create A/B test variants
  - Configure test parameters
  - Test validation
  - Test lifecycle management

- **User assignment** (12 tests)
  - Random assignment algorithms
  - Deterministic assignment (same user → same variant)
  - Segment-based assignment
  - Control group management

- **Metrics tracking** (12 tests)
  - Variant performance tracking
  - Conversion tracking
  - Engagement metrics
  - Statistical significance

- **Results analysis** (10 tests)
  - Winner determination
  - Statistical analysis
  - Confidence intervals
  - Results reporting

- **Integration** (8 tests)
  - Content delivery integration
  - Analytics integration
  - User segmentation integration

### Session 14: User Segmentation Service (3-4 hours)
**Module**: services/user_segmentation.py
**Current**: 0-35% | **Target**: 70% | **Gap**: 272 statements

#### Test Strategy
Create 50-60 comprehensive tests covering:
- **Segment creation** (12 tests)
  - Demographic segmentation
  - Behavioral segmentation
  - Engagement-based segmentation
  - Custom segment rules

- **User classification** (15 tests)
  - Assign users to segments
  - Multi-segment membership
  - Segment priority handling
  - Dynamic segment updates

- **Segment analytics** (10 tests)
  - Segment size calculation
  - Segment overlap analysis
  - Segment performance metrics
  - Growth tracking

- **Content personalization** (12 tests)
  - Segment-specific content
  - Personalization strategies
  - Content recommendations
  - A/B test integration

---

## Phase 2: Infrastructure Services (Sessions 15-17)
**Duration**: 3-4 days (3 sessions @ 2-3 hours each)
**Expected Gain**: 550 statements → +4.7 percentage points
**Target Coverage After**: 53-57%

### Session 15: Content Assembler V2 (2-3 hours)
**Module**: services/content_assembler_v2.py
**Current**: 0% | **Target**: 70% | **Gap**: 253 statements

#### Test Strategy (40-50 tests)
- Content assembly workflows
- Template processing
- Variable substitution
- Multi-format output
- Validation and quality checks

### Session 16: Monitoring Metrics (2-3 hours)
**Module**: monitoring/metrics.py
**Current**: 0% | **Target**: 70% | **Gap**: 154 statements

#### Test Strategy (30-40 tests)
- Metric collection
- Metric aggregation
- Performance tracking
- Export/reporting
- Alerting thresholds

### Session 17: Health Checks (2-3 hours)
**Module**: health/health_checks.py
**Current**: 0% | **Target**: 70% | **Gap**: 140 statements

#### Test Strategy (30-40 tests)
- Service health checks
- Dependency checks
- Database connectivity
- External service status
- Health status reporting

---

## Phase 3: API Layer (Sessions 18-19)
**Duration**: 3-4 days (2 sessions @ 4-5 hours each)
**Expected Gain**: 400 statements → +3.4 percentage points
**Target Coverage After**: 57-60%

### Session 18: Schema Validated Endpoints (4-5 hours)
**Module**: api/endpoints_schema_validated.py
**Current**: 0-21% | **Target**: 70% | **Gap**: 162 statements

#### Prerequisites
- Review existing 15 tests from Session 5
- Identify coverage gaps

#### Test Strategy (30-40 additional tests)
- Complete validation endpoint coverage
- Schema type endpoints
- Validation rules endpoints
- Content type discovery
- Error handling paths

### Session 19: V2 Endpoints (4-5 hours)
**Module**: api/endpoints_v2.py
**Current**: 0-12% | **Target**: 70% | **Gap**: 144 statements

#### Prerequisites
- **BLOCKER FIX**: Resolve FastAPI Request mocking architecture
- Review existing test patterns
- Design new mocking approach

#### Test Strategy (40-50 tests)
- Enhanced content generation endpoints
- Preview mode functionality
- Content validation endpoints
- Integration endpoints
- Error handling and edge cases

---

## Phase 4: V2 Client Infrastructure (Sessions 20-21)
**Duration**: 4-5 days (2 sessions @ 4-5 hours each)
**Expected Gain**: 500 statements → +4.3 percentage points
**Target Coverage After**: 61-64%

### Session 20: Fix CRM Client V2 Tests (3-4 hours)
**Module**: services/crm_client_v2.py
**Current**: 26% (11 tests, 10 failing) | **Target**: 70% | **Gap**: 173 statements

#### Issues to Resolve
- Mock settings missing DRY_RUN_MODE attribute
- Async mock issues
- Test fixture problems

#### Test Strategy
- Fix existing 11 tests (2 hours)
- Add 30-40 new tests (2 hours)
- Cover rate limiting, circuit breaker, bulk operations

### Session 21: Fix Platform Client V2 Tests (3-4 hours)
**Module**: services/platform_client_v2.py
**Current**: 32% (37 tests, 34 failing) | **Target**: 70% | **Gap**: 191 statements

#### Issues to Resolve
- Mock settings initialization
- Async operation handling
- Test configuration issues

#### Test Strategy
- Fix existing 37 tests (2 hours)
- Add 20-30 new tests (2 hours)
- Cover publishing, content management, analytics

---

## Phase 5: Final Push (Sessions 22-25)
**Duration**: 4-6 days
**Expected Gain**: 500-800 statements → +4-7 percentage points
**Target Coverage After**: 65-71%

### Session 22: AI Content Enhancer (3 hours)
**Module**: services/ai_content_enhancer.py
**Current**: 37-57% | **Target**: 70% | **Gap**: ~80 statements

### Session 23: Templates & Utilities (3 hours)
**Modules**: Various template and utility modules
**Target**: Bring multiple small modules to 70%+

### Session 24: Database Layer (4-5 hours)
**Prerequisites**: **BLOCKER - Pydantic v2 migration required**
**Modules**: database/connection.py, database/managers.py
**Expected Gain**: 300+ statements

### Session 25: Final Gaps & Polish (3-4 hours)
- Address remaining modules below 70%
- Fix any failing tests
- Comprehensive coverage verification
- Documentation updates

---

## Blocker Resolution Tasks

### Blocker 1: Pydantic v2 Migration (Est. 4-6 hours)
**Priority**: High (blocks Phase 5, Session 24)
**Affected Modules**: database/*, config validation

**Tasks**:
1. Update Pydantic v2 imports (BaseSettings → Settings)
2. Update field validators syntax
3. Update configuration patterns
4. Fix affected tests
5. Verify database module functionality

**Recommendation**: Schedule before Session 24 or after reaching 65% coverage

### Blocker 2: FastAPI Request Mocking (Est. 3-4 hours)
**Priority**: Medium (blocks Phase 3, Session 19)
**Affected Modules**: api/endpoints_v2.py

**Tasks**:
1. Research FastAPI Request object structure
2. Design comprehensive Request mock
3. Create reusable test fixtures
4. Refactor existing tests
5. Validate new approach

**Recommendation**: Schedule before Session 19 or defer until after 65% coverage

---

## Success Metrics

### Coverage Milestones
- [ ] **Phase 0 Complete**: 42-45% (test discovery)
- [ ] **Phase 1 Complete**: 48-52% (high-impact services)
- [ ] **Phase 2 Complete**: 53-57% (infrastructure)
- [ ] **Phase 3 Complete**: 57-60% (API layer)
- [ ] **Phase 4 Complete**: 61-64% (V2 clients)
- [ ] **Phase 5 Complete**: 65-71% (final push)
- [ ] **TARGET ACHIEVED**: **≥70%** ✓

### Quality Metrics
- [ ] All tests passing (no failures)
- [ ] No critical module <50% coverage
- [ ] All Priority 1 modules ≥70%
- [ ] Test suite runs in <10 minutes
- [ ] Zero test discovery issues

### Production Readiness
- [ ] All blockers resolved
- [ ] Integration tests 100% passing
- [ ] Error handling paths covered
- [ ] Monitoring and health checks functional

---

## Timeline Estimates

### Optimistic (14-16 days)
- Assumes test discovery finds 500+ statements
- No major blockers encountered
- Efficient test development
- **Target Date**: ~2 weeks from Session 11

### Realistic (18-21 days)
- Test discovery finds 300-400 statements
- Minor blockers resolved inline
- Normal test development pace
- **Target Date**: ~3 weeks from Session 11

### Pessimistic (25-30 days)
- Test discovery finds minimal statements
- Major blockers require extended fixes
- Complex test scenarios encountered
- **Target Date**: ~4 weeks from Session 11

---

## Execution Recommendations

### Session Structure
1. **Start**: Clear objective (1 module or logical group)
2. **Plan**: Review module, identify test categories (15 min)
3. **Execute**: Write tests in focused batches (2-3 hours)
4. **Verify**: Run tests, check coverage, fix failures (30 min)
5. **Document**: Update session log, coverage tracking (15 min)

### Best Practices
- ✅ Run targeted tests, not full suite
- ✅ Verify coverage after each session
- ✅ Focus on quality over quantity
- ✅ Use established test patterns
- ✅ Document blockers immediately

### Risk Mitigation
- Keep sessions focused (1 module max)
- Don't let perfect be the enemy of good
- Skip complex edge cases if blocking progress
- Document "good enough" coverage thresholds
- Prioritize critical paths over exhaustive coverage

---

## Conclusion

**Path to 70% is clear and achievable:**
- 5 well-defined phases
- 15-25 focused sessions
- 18-21 days realistic timeline
- Proven test patterns established

**Next Action**: Execute Phase 0 (Test Discovery Audit) in Session 11 to establish accurate baseline and potentially gain 300-600 statements through better test discovery.

**Success Indicators**:
- Steady progress (+2-7 points per phase)
- Manageable session scope (2-4 hours each)
- Clear blocker identification and resolution plan
- Quality maintained throughout

The foundation is strong (Sessions 1-10), and the path forward is systematic and realistic.
