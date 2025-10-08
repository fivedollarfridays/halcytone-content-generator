# Architecture: Standalone Content Generator Product

**Last Updated**: 2025-10-02
**Status**: ✅ Architecture Clarified

---

## Executive Summary

**Toombos** is a **standalone commercial SaaS product** with its own dedicated dashboard, **separate and independent from the existing Command Center platform**.

---

## Key Architectural Facts

### Two Separate Products

| Product | Description | Repository | Purpose |
|---------|-------------|------------|---------|
| **Content Generator** | AI-powered content generation platform | `toombos-backend` (backend)<br>`toombos-backend-dashboard` (frontend) | Commercial SaaS product for content creation |
| **Command Center** | Broader platform management system | Existing separate codebase | Internal/commercial platform for multiple services |

### Relationship

- **Independent Products**: Each operates standalone
- **Potential Integration**: Command Center MAY consume Content Generator API as one integration among many
- **No Tight Coupling**: Content Generator does not depend on Command Center
- **Separate Customers**: Content Generator has its own customer base and dashboard

---

## Content Generator Architecture

### Repository Structure

```
┌─────────────────────────────────────────────┐
│  Content Generator Product (Standalone)     │
└─────────────────────────────────────────────┘
         │
         ├── Backend API
         │   ├── Repository: toombos-backend
         │   ├── Framework: FastAPI (Python 3.11+)
         │   ├── Status: ✅ Production-ready
         │   ├── Features: REST API, WebSocket, Auth, Monitoring
         │   └── Current: 13.3% test coverage → 70% target
         │
         └── Dashboard (Frontend)
             ├── Repository: toombos-backend-dashboard
             ├── Framework: Next.js 14 + TypeScript
             ├── Status: ⏸️ To be created (after 70% backend coverage)
             ├── Components: Prototype components exist in frontend/
             └── Purpose: Customer-facing UI for content generation
```

### Tech Stack

**Backend (toombos-backend)**:
- FastAPI + Python 3.11+
- PostgreSQL + Redis
- Docker containerization
- Prometheus/Grafana monitoring
- JWT + API key authentication

**Dashboard (toombos-backend-dashboard - To Be Created)**:
- Next.js 14 + TypeScript
- Tailwind CSS + Shadcn/ui
- React Query for API state
- WebSocket for real-time updates
- Vercel/Netlify deployment

---

## Development Phases

### Phase 1: Test Coverage Enhancement ⚙️ **IN PROGRESS**
**Goal**: Achieve 70% backend test coverage
**Duration**: 3-4 weeks
**Status**: 13.3% → 70% (99 tests added, 600 remaining)

### Phase 2: Dashboard Repository Creation 📱 **PENDING**
**Goal**: Create standalone dashboard repository
**Duration**: 2 weeks
**Starts After**: 70% coverage achieved
**Tasks**:
- Create `toombos-backend-dashboard` repo
- Set up Next.js 14 + TypeScript
- Install bpsai-pair
- Migrate components from `frontend/`
- Build authentication, content generation, job management UIs

### Phase 3: Production Deployment 🚀 **PENDING**
**Goal**: Deploy backend + dashboard to production
**Duration**: 1-2 weeks
**Starts After**: Dashboard MVP complete
**Tasks**:
- Deploy backend to production (Docker)
- Deploy dashboard to Vercel/Netlify
- Configure domains and SSL
- Onboard first customers

---

## What Changed (Documentation Update 2025-10-02)

### Old Confusion
❌ Documentation referenced "Command Center integration"
❌ Unclear whether Content Generator was part of Command Center
❌ Mixed messaging about standalone vs integrated product

### Current Clarity
✅ Content Generator is **standalone commercial product**
✅ Command Center is **separate existing product**
✅ Content Generator has **its own dedicated dashboard** (separate repo)
✅ Command Center may integrate with CG API (optional, not required)

---

## File Organization

### Updated Documentation
- ✅ `docs/toombos-frontend.md` - Dashboard setup guide (NEW)
- ✅ `context/development.md` - Updated with standalone architecture
- ✅ `docs/DEPRECATED-command-center-integration.md` - Deprecated old doc
- ✅ `docs/ARCHITECTURE-STANDALONE-PRODUCT.md` - This file (NEW)

### Existing Components
- `frontend/src/components/` - Prototype dashboard components (to be migrated)
- `frontend/src/lib/` - API client library (to be migrated)
- `frontend/src/types/` - TypeScript types (to be migrated)

---

## Timeline Summary

| Week | Phase | Activities |
|------|-------|-----------|
| 1-3 | Test Coverage | Add ~600 tests to reach 70% coverage |
| 4-5 | Dashboard Creation | Create repo, setup Next.js, migrate components, build UI |
| 6 | Production Deployment | Deploy backend + dashboard, onboard customers |

**Total Timeline**: ~6 weeks to production launch

---

## Key URLs & Resources

### Current
- **Backend API Docs**: http://localhost:8000/docs
- **Monitoring**: Grafana dashboard (when running)
- **Development Guide**: `context/development.md`
- **Dashboard Guide**: `docs/toombos-frontend.md`

### Future (After Deployment)
- **Production API**: TBD (e.g., api.contentgenerator.halcytone.com)
- **Dashboard**: TBD (e.g., dashboard.contentgenerator.halcytone.com)
- **Customer Docs**: TBD

---

## Decision Log

### 2025-10-02: Architecture Clarification
**Decision**: Content Generator is standalone product with dedicated dashboard, separate from Command Center

**Rationale**:
- Clear product positioning
- Independent commercial viability
- Separate customer bases
- Simplified architecture
- No tight coupling concerns

**Impact**:
- Dashboard needs separate repository
- Documentation updated across all files
- Timeline adjusted for dashboard creation
- No Command Center dependencies to remove

---

## Quick Reference

### "Is Content Generator part of Command Center?"
**No.** They are separate, independent products.

### "Do they share a UI?"
**No.** Content Generator has its own dedicated dashboard in a separate repository.

### "Can Command Center use Content Generator?"
**Yes**, as an API integration (one of many services it might integrate with).

### "When will the dashboard be ready?"
**6 weeks from now** (after backend reaches 70% test coverage).

### "Where are the existing frontend components?"
In `frontend/` directory, will be migrated to new dashboard repository.

---

**Document Owner**: Kevin
**Last Review**: 2025-10-02
**Next Review**: After Phase 2 (Dashboard Creation)
