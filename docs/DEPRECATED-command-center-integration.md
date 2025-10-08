# ⚠️ DEPRECATED - Command Center Integration Guide

**Status**: ❌ **DEPRECATED as of 2025-10-02**
**Reason**: Outdated architecture assumptions
**Replacement**: See `docs/toombos-frontend.md`

---

## Important Notice

This document is **DEPRECATED** and contains outdated information about integrating Content Generator with Command Center.

### Why This Was Deprecated

This document was written under the assumption that:
- Content Generator would be integrated into the existing Command Center product
- Command Center would be the primary UI for Content Generator
- The two products would be tightly coupled

### Actual Current Architecture

**Content Generator is a standalone commercial product:**
- **Separate from Command Center**: Two independent products
- **Dedicated Dashboard**: Content Generator has its own dashboard repository
- **Command Center Integration**: Optional, Command Center may consume CG API as one of many integrations

---

## See Updated Documentation

**For Dashboard Development:**
👉 **`docs/toombos-frontend.md`**
- Standalone dashboard architecture
- Dashboard repository setup guide
- Next.js project structure
- Component migration plan

**For Current Development Status:**
👉 **`context/development.md`**
- Current phase: Test coverage enhancement
- Timeline: Dashboard creation after 70% coverage
- Architecture: Standalone product with dedicated dashboard

**For API Integration:**
- API Documentation: http://localhost:8000/docs
- The backend API endpoints remain the same
- Only the UI/dashboard architecture changed

---

## Migration Notes

If you were following this document:

1. **Disregard references to "Command Center integration"**
   - Content Generator is standalone
   - Dashboard is in separate repository

2. **Follow new dashboard guide:**
   - Create `toombos-backend-dashboard` repository
   - Use Next.js 14 + TypeScript
   - Migrate components from `frontend/` directory

3. **Backend API unchanged:**
   - All endpoints still work as documented
   - CORS configuration will be updated for dashboard domain
   - No breaking changes to API

---

**Document Deprecated**: 2025-10-02
**Superseded By**: `docs/toombos-frontend.md`
**Reason**: Architecture clarification - standalone product vs Command Center integration

---

## Original Document Preserved Below (For Historical Reference)

<details>
<summary>Click to view original deprecated content</summary>

[Original content preserved but not shown here to avoid confusion]

This section intentionally omitted. If you need the original content for historical purposes, check git history:
```bash
git log -- docs/command-center-integration.md
```

</details>

---

**Do not use this document for new development.**
**Refer to `docs/toombos-frontend.md` instead.**
