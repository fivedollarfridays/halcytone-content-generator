# Repository Rename Plan: halcytone-content-generator → toombos-backend

**Created:** 2025-10-07
**Updated:** 2025-10-07
**Priority:** HIGH
**Estimated Effort:** 2-3 days
**Sprint:** Phase 2C - Codebase Cleanup (or dedicated rename sprint)

## Executive Summary

This document outlines the comprehensive plan to rename the repository from `halcytone-content-generator` to `toombos-backend`, including all code, documentation, configuration, and infrastructure references.

**Scope:** 241 files contain references to "halcytone" (case-insensitive search)

## Objectives

1. Rename Python package from `halcytone_content_generator` to `toombos`
2. Rename repository from `halcytone-content-generator` to `toombos-backend`
3. Update all import statements across the codebase
4. Rename directory structure to reflect new name
5. Update all documentation and configuration files
6. Update infrastructure and deployment configurations
7. Update monitoring and observability configurations
8. Maintain backward compatibility where needed (API endpoints, etc.)

## Rename Strategy

### Phase 1: Preparation & Risk Mitigation (4 hours)

#### 1.1 Backup & Branch Creation
- [ ] Create feature branch: `feature/rename-to-toombos`
- [ ] Document current state (git commit hash, test coverage baseline)
- [ ] Run full test suite and document baseline: `pytest --cov`
- [ ] Create backup of key configuration files

#### 1.2 Dependency Analysis
- [ ] List all external integrations that may reference the old name
- [ ] Document API endpoints that should remain stable
- [ ] Identify environment variables that need updating
- [ ] Check for hardcoded references in external systems (if any)

#### 1.3 Communication Plan
- [ ] Notify team members of rename timeline
- [ ] Update dashboard repository to reference new backend name
- [ ] Plan for DNS/domain updates (if applicable)

### Phase 2: Core Rename Operations (8-10 hours)

#### 2.1 Python Package Rename
**Priority: CRITICAL**

1. **Directory Structure**
   ```bash
   # Rename main package directory
   src/halcytone_content_generator/ → src/toombos/

   # Repository will be renamed to: toombos-backend
   ```

2. **Update All Import Statements** (Automated with script recommended)
   - [ ] Replace `from halcytone_content_generator` → `from toombos`
   - [ ] Replace `import halcytone_content_generator` → `import toombos`
   - Files affected: ~150+ Python files in:
     - `src/toombos/` (formerly halcytone_content_generator)
     - `tests/unit/`
     - `tests/integration/`
     - `tests/performance/`
     - `scripts/`
     - `mocks/`
     - `performance/`
     - `migrations/`

3. **Package Metadata**
   - [ ] Update `src/toombos/__init__.py` docstrings
   - [ ] Update version info if present

#### 2.2 Configuration Files
**Priority: CRITICAL**

1. **Docker Configuration**
   - [ ] `Dockerfile.prod` - Update comments and labels
   - [ ] `docker-compose.yml` - Update service names and image names
   - [ ] `docker-compose.dev.yml` - Update service names
   - [ ] `docker-compose.prod.yml` - Update service names and image names
   - [ ] `docker-compose.mocks.yml` - Update service references
   - [ ] `docker-compose.monitoring.yml` - Update service references

2. **Kubernetes Deployment**
   - [ ] `deployment/kubernetes/deployment.yaml` - Update app labels and names
   - [ ] `deployment/kubernetes/service.yaml` - Update service names
   - [ ] `deployment/kubernetes/ingress.yaml` - Update backend service references
   - [ ] `deployment/kubernetes/configmap.yaml` - Update app references
   - [ ] `deployment/kubernetes/secrets.yaml` - Update app references
   - [ ] `deployment/kubernetes/autoscaling.yaml` - Update target references

3. **Deployment Scripts**
   - [ ] `deployment/scripts/deploy-kubernetes.sh`
   - [ ] `deployment/scripts/deploy-docker-compose.sh`
   - [ ] `deployment/README.md`

4. **Environment Configuration**
   - [ ] `.env.example` - Update variable names and comments
   - [ ] Update any hardcoded "halcytone" in config keys

#### 2.3 CI/CD & GitHub Workflows
**Priority: HIGH**

- [ ] `.github/workflows/ci.yml` - Update workflow names and references
- [ ] `.github/workflows/deploy-staging.yml` - Update deployment references
- [ ] `.github/workflows/deploy-production.yml` - Update deployment references
- [ ] `.github/workflows/performance-regression.yml` - Update test references

#### 2.4 Monitoring & Observability
**Priority: HIGH**

1. **Prometheus Configuration**
   - [ ] `monitoring/prometheus/prometheus.yml` - Update job names and targets
   - [ ] `monitoring/prometheus/rules/application.yml` - Update alert names
   - [ ] `monitoring/prometheus/rules/halcytone-alerts.yml` - Rename file and update content
   - [ ] `monitoring/prometheus/alerts/performance-alerts.yml` - Update alert names

2. **Grafana Dashboards**
   - [ ] `monitoring/grafana/dashboards/halcytone-overview.json` - Rename file and update dashboard
   - [ ] `monitoring/grafana/dashboards/halcytone-performance.json` - Rename file and update dashboard
   - [ ] `monitoring/grafana/dashboards/mock-services.json` - Update references
   - [ ] `monitoring/grafana/provisioning/dashboards/dashboards.yml` - Update paths

3. **Other Monitoring**
   - [ ] `monitoring/elasticsearch/elasticsearch.yml` - Update index names
   - [ ] `monitoring/kibana/kibana.yml` - Update index patterns
   - [ ] `monitoring/logstash/config/logstash.yml` - Update pipeline references
   - [ ] `monitoring/logstash/pipeline/logstash.conf` - Update log patterns
   - [ ] `monitoring/filebeat/filebeat.yml` - Update input paths
   - [ ] `monitoring/promtail/promtail-config.yml` - Update labels

#### 2.5 Scripts & Utilities
**Priority: MEDIUM**

- [ ] `scripts/README.md` - Update script descriptions
- [ ] `scripts/analyze_coverage.py` - Update references
- [ ] `scripts/run_e2e_tests.py` - Update references
- [ ] `scripts/validate_security.py` - Update references
- [ ] `scripts/validate_external_services.py` - Update references
- [ ] `scripts/setup_aws_secrets.sh` - Update secret names
- [ ] `scripts/config_manager.py` - Update config references
- [ ] `scripts/start_mock_services.py` - Update service names
- [ ] `scripts/start-mock-services.sh` - Update service names
- [ ] `scripts/start-mock-services.bat` - Update service names
- [ ] `scripts/validate-dry-run.sh` - Update validation references
- [ ] `scripts/start-monitoring.sh` - Update monitoring references
- [ ] `scripts/security_audit.py` - Update audit scope
- [ ] `scripts/deployment_notifications.py` - Update notification messages
- [ ] `scripts/setup_monitoring.py` - Update monitoring setup
- [ ] `scripts/go_live_validation.py` - Update validation references
- [ ] `scripts/run_performance_baseline.py` - Update baseline references

### Phase 3: Documentation Updates (4-6 hours)

#### 3.1 Root Documentation
**Priority: HIGH**

- [ ] `README.md` - Update project name, descriptions, URLs
- [ ] `CLAUDE.md` - Update project references
- [ ] `AGENTS.md` - Update project references
- [ ] `CONTRIBUTING.md` - Update contribution guidelines
- [ ] `SECURITY.md` - Update security reporting
- [ ] `Makefile` - Update targets and comments

#### 3.2 Context Files
**Priority: HIGH**

- [ ] `context/development.md` - Update project name throughout
- [ ] `context/agents.md` - Update AI assistant references
- [ ] `context/project_tree.md` - Update directory structure

#### 3.3 Documentation Directory
**Priority: MEDIUM**

All files in `docs/` directory (50+ files):
- [ ] `docs/README.md`
- [ ] `docs/API.md`
- [ ] `docs/ARCHITECTURE-STANDALONE-PRODUCT.md`
- [ ] `docs/AUTOMATED_SOCIAL_POSTING.md`
- [ ] `docs/USER_GUIDE.md`
- [ ] `docs/api-client-integration.md`
- [ ] `docs/command-center-integration.md` (DEPRECATED - can remove references)
- [ ] `docs/DEPRECATED-command-center-integration.md`
- [ ] `docs/command-center-quick-start.md`
- [ ] `docs/content-generator-dashboard.md`
- [ ] `docs/dashboard-repository-created-2025-10-02.md`
- [ ] `docs/database-configuration.md`
- [ ] `docs/secrets-management.md`
- [ ] `docs/deployment-procedures.md`
- [ ] `docs/deployment-runbook.md`
- [ ] `docs/dry-run-guide.md`
- [ ] `docs/go-live-execution-report.md`
- [ ] `docs/go-live-sign-off.md`
- [ ] `docs/health-checks.md`
- [ ] `docs/incident-response-playbook.md`
- [ ] `docs/key-user-workflows.md`
- [ ] `docs/marketing-editor-guide.md`
- [ ] `docs/mock-services-guide.md`
- [ ] `docs/monitoring-runbook.md`
- [ ] `docs/monitoring-stack.md`
- [ ] `docs/openapi-spec.yaml`
- [ ] `docs/performance-baseline.md`
- [ ] `docs/production-configuration-guide.md`
- [ ] `docs/production-deployment-checklist.md`
- [ ] `docs/production-readiness-summary.md`
- [ ] `docs/troubleshooting.md`
- [ ] `docs/websocket-integration-guide.md`
- [ ] All test coverage and sprint documentation files

#### 3.4 Test Documentation
**Priority: LOW**

- [ ] `tests/example_contract/README.md`
- [ ] `tests/example_integration/README.md`

#### 3.5 Template Files
**Priority: LOW**

- [ ] `templates/adr.md`
- [ ] `templates/directory_note.md`

#### 3.6 Performance Documentation
**Priority: LOW**

- [ ] `performance/README.md`

### Phase 4: Test Suite Updates (2-4 hours)

#### 4.1 Test Files
**Priority: CRITICAL**

Update all test files (100+ files):
- [ ] All files in `tests/unit/` (60+ files)
- [ ] All files in `tests/integration/` (10+ files)
- [ ] All files in `tests/performance/` (5+ files)
- [ ] All files in `tests/contracts/` (if any)

**Import Statement Updates:**
```python
# Old
from halcytone_content_generator.services import ContentAssembler
from halcytone_content_generator.api.endpoints import router

# New
from toombos.services import ContentAssembler
from toombos.api.endpoints import router
```

#### 4.2 Test Coverage Files
- [ ] `coverage.json` - May contain references to old package name
- [ ] HTML coverage reports in `htmlcov/` - Will be regenerated

### Phase 5: Verification & Testing (4-6 hours)

#### 5.1 Automated Verification
- [ ] Run find/grep to ensure no remaining "halcytone" references
- [ ] Check for case variations: "Halcytone", "HALCYTONE", "halcytone"
- [ ] Verify all import statements are updated

#### 5.2 Test Suite Execution
- [ ] Run full unit test suite: `pytest tests/unit/ -v`
- [ ] Run integration tests: `pytest tests/integration/ -v`
- [ ] Run performance tests: `pytest tests/performance/ -v`
- [ ] Verify test coverage: `pytest --cov=toombos --cov-report=html`
- [ ] Compare coverage to baseline (should be similar)

#### 5.3 Application Testing
- [ ] Build Docker image with new name
- [ ] Run application locally: `python -m toombos.main` or via Docker
- [ ] Test health endpoints: `/health`, `/health/ready`, `/health/live`
- [ ] Test API endpoints: POST to content generation endpoints
- [ ] Verify monitoring metrics are being collected
- [ ] Check logs for any old package name references

#### 5.4 Infrastructure Testing
- [ ] Deploy to local development environment
- [ ] Verify Docker Compose stack starts correctly
- [ ] Verify Kubernetes manifests are valid: `kubectl apply --dry-run`
- [ ] Check monitoring dashboards load correctly
- [ ] Verify alerting rules are valid

### Phase 6: External Updates (2-4 hours)

#### 6.1 Repository Rename
**Note:** This should be done LAST after all code changes are merged

- [ ] Rename GitHub repository: `halcytone-content-generator` → `toombos-backend`
- [ ] Update repository description to "Toombos Backend API"
- [ ] Update repository topics/tags
- [ ] Set up redirect (GitHub does this automatically)

#### 6.2 Dashboard Repository Updates
- [ ] Update dashboard repository API client to reference new backend name
- [ ] Update dashboard documentation: https://github.com/fivedollarfridays/content-generator-dashboard
- [ ] Update environment variable examples

#### 6.3 External Service Updates (if applicable)
- [ ] Update AWS Secrets Manager secret names (if they include "halcytone")
- [ ] Update any external monitoring/alerting configurations
- [ ] Update DNS records (if domain includes "halcytone")
- [ ] Update CI/CD environment variables
- [ ] Notify any API consumers of the rename

## Recommended Execution Order

### Week 1: Preparation & Core Changes (Days 1-2)
1. **Day 1:** Phases 1.1-1.3 (Preparation)
2. **Day 2:** Phase 2.1 (Python package rename and imports)

### Week 1: Configuration & Infrastructure (Day 3)
3. **Day 3:** Phases 2.2-2.4 (Docker, K8s, CI/CD, Monitoring)

### Week 2: Documentation & Testing (Days 4-5)
4. **Day 4:** Phases 2.5 & 3 (Scripts and all documentation)
5. **Day 5:** Phases 4 & 5 (Test suite updates and verification)

### Week 2: External Updates & Go-Live (Day 6)
6. **Day 6:** Phase 6 (External updates and repository rename)

## Automation Recommendations

### Automated Find & Replace Script

Create a Python script to automate the bulk of replacements:

```python
#!/usr/bin/env python3
"""
Automated rename script for halcytone → toombos
Usage: python scripts/rename_to_toombos.py
"""

import os
import re
from pathlib import Path

# Define replacements
REPLACEMENTS = [
    # Package imports
    (r'from halcytone_content_generator', 'from toombos'),
    (r'import halcytone_content_generator', 'import toombos'),

    # Repository and text references
    (r'halcytone-content-generator', 'toombos-backend'),
    (r'halcytone_content_generator', 'toombos'),

    # Capitalized versions
    (r'Halcytone Content Generator', 'Toombos Backend'),
    (r'Halcytone', 'Toombos'),

    # Service names in configs
    (r'halcytone-service', 'toombos-service'),
    (r'halcytone_service', 'toombos_service'),
]

# Files to process
INCLUDE_PATTERNS = [
    '**/*.py',
    '**/*.md',
    '**/*.yml',
    '**/*.yaml',
    '**/*.json',
    '**/*.toml',
    '**/*.cfg',
    '**/*.ini',
    '**/*.txt',
    '**/*.sh',
    '**/*.bat',
    '**/Dockerfile*',
    '**/Makefile',
]

EXCLUDE_DIRS = [
    '.git',
    '__pycache__',
    'htmlcov',
    '.pytest_cache',
    'node_modules',
    'venv',
    '.venv',
]

def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed"""
    # Skip excluded directories
    for exclude in EXCLUDE_DIRS:
        if exclude in file_path.parts:
            return False

    # Check if matches include patterns
    for pattern in INCLUDE_PATTERNS:
        if file_path.match(pattern):
            return True

    return False

def process_file(file_path: Path, dry_run: bool = True) -> tuple[int, list[str]]:
    """Process a single file and apply replacements"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = []

        # Apply all replacements
        for pattern, replacement in REPLACEMENTS:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                changes.append(f"  - {pattern} → {replacement} ({len(matches)} occurrences)")

        # Write back if changes were made
        if content != original_content and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return len(changes), changes

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0, []

def main(dry_run: bool = True):
    """Main execution"""
    root = Path('.')
    total_files = 0
    total_changes = 0

    print(f"{'DRY RUN - ' if dry_run else ''}Scanning for files to rename...")
    print(f"Root directory: {root.absolute()}\n")

    # Find all files to process
    files_to_process = []
    for pattern in INCLUDE_PATTERNS:
        files_to_process.extend(root.glob(pattern))

    files_to_process = [f for f in files_to_process if should_process_file(f)]

    print(f"Found {len(files_to_process)} files to process\n")

    # Process each file
    for file_path in sorted(files_to_process):
        change_count, changes = process_file(file_path, dry_run)
        if change_count > 0:
            total_files += 1
            total_changes += change_count
            print(f"\n{file_path}:")
            for change in changes:
                print(change)

    print(f"\n{'DRY RUN - ' if dry_run else ''}Summary:")
    print(f"  Files modified: {total_files}")
    print(f"  Total changes: {total_changes}")

    if dry_run:
        print("\nThis was a DRY RUN. Run with --execute to apply changes.")

if __name__ == '__main__':
    import sys
    dry_run = '--execute' not in sys.argv
    main(dry_run)
```

Save as `scripts/rename_to_toombos.py` and run:
```bash
# Dry run first
python scripts/rename_to_toombos.py

# Execute when ready
python scripts/rename_to_toombos.py --execute
```

## Rollback Plan

If issues are discovered after merge:

1. **Immediate Rollback**
   ```bash
   git revert <merge-commit-hash>
   git push origin main
   ```

2. **Directory Rename Rollback**
   ```bash
   mv src/toombos src/halcytone_content_generator
   # Re-run tests to ensure everything works
   ```

3. **Partial Rollback**
   - Keep the feature branch
   - Cherry-pick only the working commits
   - Fix issues and re-merge

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Broken imports | HIGH | MEDIUM | Comprehensive testing before merge |
| Test failures | HIGH | MEDIUM | Run full test suite multiple times |
| Deployment issues | MEDIUM | LOW | Test in staging environment first |
| External service breakage | HIGH | LOW | Document all external dependencies first |
| Monitoring gaps | MEDIUM | MEDIUM | Verify all monitoring configs |
| Lost git history | LOW | LOW | GitHub maintains redirects automatically |
| Database migration issues | MEDIUM | LOW | No schema changes, only code rename |
| API client breakage | MEDIUM | LOW | Coordinate with dashboard team |

## Success Criteria

- [ ] All 241 files with "halcytone" references updated
- [ ] Full test suite passing with 0 failures
- [ ] Test coverage maintained at current level (13%+)
- [ ] Application starts successfully via Docker
- [ ] Health endpoints responding correctly
- [ ] Monitoring dashboards display correctly
- [ ] No references to "halcytone" in codebase (verified by search)
- [ ] Documentation updated and consistent
- [ ] Dashboard repository updated to reference new name
- [ ] CI/CD pipelines passing

## Post-Rename Checklist

- [ ] Update project status in `context/development.md`
- [ ] Announce rename to team
- [ ] Update any external documentation/wikis
- [ ] Monitor for any issues in first 48 hours
- [ ] Archive old dashboard references
- [ ] Update any external integrations
- [ ] Celebrate successful rename! 🎉

## Sprint Integration

This rename task will be added to the sprint plan as either:
- **Option 1:** Part of Phase 2C (Codebase Cleanup) - Makes sense since Phase 2C already includes deprecation work
- **Option 2:** Dedicated "Repository Rename Sprint" after Phase 2C

**Recommended:** Integrate into Phase 2C as a major sub-task.

## References

- Original repository: https://github.com/<owner>/halcytone-content-generator
- New repository name: `toombos-backend`
- Dashboard repository: https://github.com/fivedollarfridays/content-generator-dashboard
- Current branch: `feature/production-deployment`
- Sprint documentation: `context/development.md`

## Name Rationale

- **Package name**: `toombos` (Python package, import statements)
- **Repository name**: `toombos-backend` (GitHub repo, clear it's the backend API)
- **Service name**: `toombos-service` (Docker, Kubernetes, monitoring configs)
- This matches the pattern of having a clear backend/frontend separation
