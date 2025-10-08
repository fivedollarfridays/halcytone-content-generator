# ⚠️ DEPRECATED - Frontend Directory

**Status**: ❌ **DEPRECATED as of 2025-10-02**
**Reason**: Components migrated to dedicated dashboard repository
**Replacement**: https://github.com/fivedollarfridays/content-generator-dashboard

---

## Important Notice

This `frontend/` directory is **DEPRECATED** and should no longer be used for development.

### Why Deprecated?

All frontend components have been migrated to a dedicated, standalone dashboard repository as part of the Content Generator product architecture.

**Old Architecture** (Incorrect):
```
halcytone-content-generator/
├── backend (Python/FastAPI)
└── frontend/ (React components) ← DEPRECATED
```

**New Architecture** (Correct):
```
halcytone-content-generator/           # Backend API only
└── (Python/FastAPI backend)

content-generator-dashboard/            # Dashboard (separate repo)
└── (Next.js + TypeScript)
```

---

## Migration Complete ✅

### Components Migrated (2025-10-02)

All components from `frontend/src/components/` have been migrated to the dashboard repository:

| Component | Old Location | New Location |
|-----------|--------------|--------------|
| ContentGeneratorHealth.tsx | `frontend/src/components/` | `components/features/` |
| ContentGenerationForm.tsx | `frontend/src/components/` | `components/features/` |
| JobsList.tsx | `frontend/src/components/` | `components/features/` |
| JobStatusCard.tsx | `frontend/src/components/` | `components/features/` |
| CacheStats.tsx | `frontend/src/components/` | `components/features/` |
| TemplateSelector.tsx | `frontend/src/components/` | `components/features/` |

### Supporting Files Migrated

| File | Old Location | New Location |
|------|--------------|--------------|
| api-client.ts | `frontend/src/lib/` | `lib/api/api-client.ts` |
| content-generator.ts (types) | `frontend/src/types/` | `types/content-generator.ts` |

---

## New Dashboard Repository

**Repository**: https://github.com/fivedollarfridays/content-generator-dashboard

**Framework**: Next.js 15.5.4 + TypeScript + Tailwind CSS

**Features**:
- ✅ All components migrated and working
- ✅ Build passing (0 errors)
- ✅ Comprehensive documentation
- ✅ BPS AI Pair configuration
- ✅ API client with environment variables
- ✅ Responsive design

### Quick Start (New Dashboard)

```bash
# Clone the dashboard repository
git clone https://github.com/fivedollarfridays/content-generator-dashboard.git
cd content-generator-dashboard

# Install dependencies
npm install

# Configure environment
# Edit .env.local with your API URL

# Start development server
npm run dev

# Visit http://localhost:3000
```

---

## What Happens to This Directory?

### Current Status (2025-10-02)
- ⏸️ Directory kept for reference during transition
- ⚠️ Not actively maintained
- ❌ Do not use for new development

### Future Plans (Phase 2C - Cleanup)
This directory will be either:
1. **Moved** to `deprecated/frontend/` for archival
2. **Deleted** entirely (recommended after dashboard is production-verified)

**Recommendation**: Delete this directory after the dashboard is successfully deployed to production and verified working.

---

## For Developers

### If You're Looking for Frontend Code

**Don't look here!** Go to the dashboard repository:
- **Repository**: https://github.com/fivedollarfridays/content-generator-dashboard
- **Local Path** (if cloned): `/c/Users/kmast/PycharmProjects/content-generator-dashboard`

### If You Need to Make Frontend Changes

1. Clone the dashboard repository
2. Make your changes there
3. Test with the backend API running
4. Submit PR to the dashboard repository

### If You're Working on Backend

You don't need anything from this directory. The backend API is completely independent:
- Backend provides REST API and WebSocket endpoints
- Dashboard consumes these endpoints
- No shared code between backend and dashboard

---

## Migration Details

### When Migrated
**Date**: 2025-10-02
**Duration**: ~2 hours

### What Was Done
1. Created new Next.js 14 repository
2. Set up TypeScript + Tailwind CSS
3. Copied all 6 components
4. Copied API client and types
5. Updated all import paths
6. Created comprehensive documentation
7. Pushed to GitHub
8. Verified build passes

### Migration Documentation
See: `docs/dashboard-repository-created-2025-10-02.md` in this repository

---

## Architecture Clarification

### Content Generator is a Standalone Product

**This backend repository**:
- FastAPI service providing REST API
- WebSocket support
- Health monitoring
- No frontend code (anymore)

**Dashboard repository**:
- Next.js application
- Consumes backend API
- Standalone deployment
- Independent development

**Command Center**:
- Completely separate existing product
- May integrate with Content Generator API (optional)
- Not related to this frontend directory

---

## FAQs

### Q: Can I still use components from this directory?
**A**: No. Use the dashboard repository instead. Components here are outdated.

### Q: Will this directory be updated?
**A**: No. All frontend development happens in the dashboard repository.

### Q: When will this directory be deleted?
**A**: After the dashboard is deployed to production and verified working (Phase 2C).

### Q: What if I find a bug in a component here?
**A**: Fix it in the dashboard repository. This directory is not maintained.

### Q: Can I copy code from here?
**A**: The dashboard repository has the latest versions. Use those instead.

---

## Related Documentation

### In This Repository
- **Architecture Overview**: `docs/ARCHITECTURE-STANDALONE-PRODUCT.md`
- **Dashboard Setup Guide**: `docs/content-generator-dashboard.md`
- **Migration Summary**: `docs/dashboard-repository-created-2025-10-02.md`
- **Development Roadmap**: `context/development.md`

### In Dashboard Repository
- **README**: https://github.com/fivedollarfridays/content-generator-dashboard/blob/master/README.md
- **Setup Summary**: https://github.com/fivedollarfridays/content-generator-dashboard/blob/master/SETUP-SUMMARY.md
- **BPS AI Config**: https://github.com/fivedollarfridays/content-generator-dashboard/blob/master/.bpsai/config.yaml

---

## Contact

For questions about the dashboard or this migration:
- Check dashboard README: https://github.com/fivedollarfridays/content-generator-dashboard
- Review architecture docs: `docs/ARCHITECTURE-STANDALONE-PRODUCT.md`
- See development roadmap: `context/development.md`

---

**Directory Deprecated**: 2025-10-02
**Replacement**: https://github.com/fivedollarfridays/content-generator-dashboard
**Status**: ⚠️ DO NOT USE - Migrate to dashboard repository

**This directory will be removed in Phase 2C (Cleanup sprint)**
