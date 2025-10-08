# Content Generator Dashboard - Standalone Product

**Status**: ⚠️ Backend Ready | Dashboard Repository Needed
**Last Updated**: 2025-10-02

---

## Architecture Overview

**IMPORTANT**: This is a **standalone product** separate from the existing Command Center.

```
┌─────────────────────────────────────────────┐
│  Toombos Dashboard      │
│  (Dedicated Repository - To Be Created)     │
│  - Next.js/React Application                │
│  - Content Management UI                    │
│  - Real-time WebSocket Updates              │
│  - Performance Monitoring Views             │
│  - API Key Management                       │
│  - Job Queue Management                     │
└────────────────┬────────────────────────────┘
                 │ HTTP/REST + WebSocket
                 ▼
┌─────────────────────────────────────────────┐
│  Toombos API            │
│  (This Repository)                          │
│  - FastAPI Backend                          │
│  - REST Endpoints                           │
│  - WebSocket Server                         │
│  - Health/Metrics Endpoints                 │
└─────────────────────────────────────────────┘
```

**Note**: The existing Command Center is a **separate product** and will remain separate.

---

## Product Positioning

### Standalone Content Generator
- **Product**: Commercial SaaS content generation platform
- **Target**: Direct customers (not internal tool)
- **Dashboard**: Dedicated UI for content generator customers
- **Repository Structure**:
  - Backend API: `toombos-backend` (this repo)
  - Dashboard UI: `toombos-backend-dashboard` (to be created)

### Existing Command Center
- **Product**: Separate internal/commercial platform
- **Purpose**: Broader platform management
- **Relationship**: May consume Content Generator API as one of many integrations
- **Repository**: Separate existing codebase

---

## Backend API Status

### ✅ Ready for Dashboard Integration

The backend API is production-ready and waiting for its dedicated dashboard:

1. **CORS Configured** - `main.py:92-98`
   - Currently allows all origins for development
   - Will be configured for dashboard domain

2. **Comprehensive REST API**
   - Content generation endpoints
   - Health monitoring endpoints
   - Cache management endpoints
   - Batch operations endpoints
   - Schema-validated endpoints

3. **Real-Time WebSocket Support**
   - Live content updates
   - Session management
   - Real-time notifications

4. **Monitoring & Observability**
   - Prometheus metrics endpoints
   - Health check probes
   - Performance metrics
   - System status endpoints

5. **Authentication Ready**
   - JWT token support
   - API key authentication
   - Role-based access control

---

## Dashboard Repository Requirements

### Repository Name
`toombos-backend-dashboard`

### Recommended Tech Stack

**Option 1: Next.js 14 (Recommended)**
```
Framework: Next.js 14 + App Router
Language: TypeScript
UI Library: Shadcn/ui or Chakra UI
State: React Query (TanStack Query)
Forms: React Hook Form + Zod
Charts: Recharts or Tremor
WebSocket: native WebSocket API
Styling: Tailwind CSS
```

**Option 2: React + Vite**
```
Framework: Vite + React 18
Language: TypeScript
UI Library: Material-UI or Ant Design
State: React Query + Zustand
Forms: React Hook Form + Zod
Charts: Recharts
WebSocket: native WebSocket API
Styling: Tailwind CSS
```

### Initial Setup Commands

```bash
# Create new repository
mkdir toombos-backend-dashboard
cd toombos-backend-dashboard
git init

# Option 1: Next.js
npx create-next-app@latest . --typescript --tailwind --app --use-npm

# Option 2: Vite + React
npm create vite@latest . -- --template react-ts
npm install

# Install dependencies
npm install @tanstack/react-query axios recharts
npm install react-hook-form @hookform/resolvers zod
npm install date-fns

# UI Library (choose one)
npm install @shadcn/ui  # For Next.js
# OR
npm install @mui/material @emotion/react @emotion/styled  # For React

# Development tools
npm install -D bpsai-pair

# Environment configuration
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

---

## Existing Frontend Components

### Available Components (To Be Migrated)

Located in `toombos-backend/frontend/src/components/`:

1. **ContentGeneratorHealth.tsx** (285 lines)
   - Health status monitoring
   - System metrics display
   - Real-time health checks
   - Component health breakdown

2. **ContentGenerationForm.tsx**
   - Content creation interface
   - Template selection
   - Channel configuration

3. **JobsList.tsx** & **JobStatusCard.tsx**
   - Job queue management
   - Status tracking
   - Real-time updates

4. **CacheStats.tsx**
   - Cache statistics
   - Cache management controls

5. **TemplateSelector.tsx**
   - Template browsing
   - Template selection UI

### Migration Strategy

1. **Copy Components**
   ```bash
   # From content-generator repo
   cp -r frontend/src/components/* \
     ../toombos-backend-dashboard/src/components/

   cp -r frontend/src/lib/* \
     ../toombos-backend-dashboard/src/lib/

   cp -r frontend/src/types/* \
     ../toombos-backend-dashboard/src/types/
   ```

2. **Update Imports**
   - Adjust import paths for Next.js structure
   - Update API client configuration
   - Fix any TypeScript errors

3. **Add Missing Pieces**
   - Create app routing structure
   - Add authentication flow
   - Build navigation/layout components
   - Add error boundaries

---

## Dashboard Feature Requirements

### MVP Features (Sprint 2 - 2 weeks)

1. **Authentication & Onboarding**
   - API key generation
   - User registration/login
   - API key management UI

2. **System Health Dashboard**
   - Overall system status
   - Component health breakdown
   - Uptime tracking
   - Real-time alerts

3. **Content Generation Interface**
   - Form to trigger content generation
   - Document source selection
   - Channel selection (email, social, web)
   - Tone/style configuration
   - Dry run toggle
   - Preview generated content

4. **Job Queue Management**
   - List active/pending jobs
   - Job status tracking
   - View job details
   - Cancel jobs
   - Real-time WebSocket updates

5. **Template Management**
   - Browse available templates
   - View template details
   - Create custom templates (if applicable)

6. **Cache Management**
   - View cache statistics
   - Invalidate specific caches
   - Clear all caches
   - View invalidation history

### Phase 2 Features (Future)

7. **Content Management**
   - List generated content
   - View content details
   - Edit/update content
   - Delete content
   - Version history

8. **Analytics Dashboard**
   - Content performance metrics
   - Generation success rates
   - Usage statistics
   - Channel performance

9. **Monitoring Views**
   - Embedded Grafana dashboards
   - Custom metrics visualization
   - Performance graphs
   - Error logs

10. **Advanced Settings**
    - Plugin configuration UI
    - Webhook management
    - Notification preferences
    - Account settings

---

## API Endpoints for Dashboard

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://api.contentgenerator.halcytone.com` (configure as needed)

### Core Endpoints

#### Health & Status
```
GET  /health              # Basic health check
GET  /health/detailed     # Detailed component health
GET  /ready               # Readiness probe
GET  /metrics             # Prometheus metrics
```

#### Content Generation
```
POST /api/v2/content/generate     # Generate content
GET  /api/v2/content/{content_id} # Get content by ID
PUT  /api/v2/content/{content_id} # Update content
DELETE /api/v2/content/{content_id} # Delete content
POST /api/v2/content/batch        # Batch operations
GET  /api/v2/templates            # List templates
```

#### Job Management
```
GET  /api/v2/jobs                 # List jobs
GET  /api/v2/jobs/{job_id}        # Get job status
DELETE /api/v2/jobs/{job_id}      # Cancel job
```

#### WebSocket (Real-time)
```
WS /ws/content/{client_id}        # Content updates stream
WS /ws/jobs/{session_id}          # Job status updates
```

#### Cache Management
```
POST /api/v1/cache/invalidate     # Invalidate cache
GET  /api/v1/cache/stats          # Cache statistics
POST /api/v1/cache/clear          # Clear all caches
```

See **API Documentation**: http://localhost:8000/docs

---

## Development Workflow

### Step 1: Create Dashboard Repository

```bash
# Create new repo
mkdir toombos-backend-dashboard
cd toombos-backend-dashboard
git init

# Set up Next.js
npx create-next-app@latest . --typescript --tailwind --app --use-npm

# Install dependencies
npm install @tanstack/react-query axios recharts react-hook-form zod

# Install bpsai-pair
pip install bpsai-pair
# Follow bpsai-pair setup recommendations in the dashboard repo
```

### Step 2: Configure Environment

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Step 3: Migrate Components

```bash
# Copy existing components from content-generator repo
# (Adjust paths as needed)
```

### Step 4: Set Up Project Structure

```
toombos-backend-dashboard/
├── src/
│   ├── app/                 # Next.js app router
│   │   ├── page.tsx        # Dashboard home
│   │   ├── generate/       # Content generation
│   │   ├── jobs/           # Job management
│   │   ├── templates/      # Template browser
│   │   └── settings/       # Settings
│   ├── components/         # React components (migrated)
│   ├── lib/               # Utilities & API client
│   ├── types/             # TypeScript types
│   └── hooks/             # Custom React hooks
├── public/                # Static assets
├── .env.local            # Environment variables
└── package.json          # Dependencies
```

### Step 5: Start Development

```bash
# Terminal 1: Backend API
cd toombos-backend
python -m uvicorn src.halcytone_content_generator.main:app --reload

# Terminal 2: Dashboard
cd toombos-backend-dashboard
npm run dev
```

Access:
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

---

## Timeline

### Current Status
- **Backend API**: ✅ Production-ready (waiting for dashboard)
- **Dashboard Repository**: ❌ Not created yet
- **Frontend Components**: ⚠️ Prototype components exist in `frontend/`

### Recommended Schedule

**Current Priority**: Complete test coverage to 70% (3-4 weeks)

**After Test Coverage Complete**:

**Sprint 2: Dashboard Development** (2 weeks)
- Week 1:
  - Create dashboard repository
  - Set up Next.js project
  - Migrate existing components
  - Implement authentication flow
  - Build core UI structure

- Week 2:
  - Complete content generation interface
  - Implement job queue management
  - Add real-time WebSocket updates
  - Deploy dashboard to staging
  - Integration testing

---

## CORS Configuration

### Backend Configuration Required

**File**: `src/halcytone_content_generator/main.py`

**Current** (Development):
```python
allow_origins=["*"]  # Allow all origins
```

**Production** (Update when dashboard domain is known):
```python
allow_origins=[
    "https://dashboard.contentgenerator.halcytone.com",  # Dashboard domain
    "http://localhost:3000",  # Local development
]
```

---

## Success Criteria

### Dashboard MVP Complete When:
- ✅ Repository created and initialized
- ✅ Next.js project set up with TypeScript
- ✅ All existing components migrated
- ✅ Authentication flow implemented
- ✅ Content generation form functional
- ✅ Job queue management working
- ✅ Real-time updates via WebSocket
- ✅ API key management UI complete
- ✅ Deployed to staging environment
- ✅ Integration tests passing

---

## Next Steps

### Immediate (After 70% Test Coverage)
1. **Create Repository**: `toombos-backend-dashboard`
2. **Set Up Next.js**: Initialize project with TypeScript + Tailwind
3. **Install bpsai-pair**: `pip install bpsai-pair` and configure
4. **Migrate Components**: Copy from `frontend/` and adapt
5. **Build Core Features**: Auth, content generation, job management
6. **Deploy Staging**: Get dashboard running end-to-end

### Documentation Needed in Dashboard Repo
1. README.md with setup instructions
2. API integration guide
3. Component documentation
4. Deployment guide
5. Environment configuration guide

---

## Important Notes

### ⚠️ Key Distinctions

**This Repository** (`toombos-backend`):
- Backend API for standalone content generation product
- FastAPI service
- Headless architecture
- Will be consumed by dedicated dashboard

**Dashboard Repository** (`toombos-backend-dashboard`):
- Frontend UI for content generator customers
- Standalone Next.js application
- Dedicated to content generator product only

**Command Center** (Separate existing product):
- Different product entirely
- May integrate with content generator API as one integration
- Remains independent

---

**Status**: ⏸️ **Waiting for Test Coverage Completion (70%)**
**Next**: Create `toombos-backend-dashboard` repository (Sprint 2)
**Timeline**: 2-3 weeks (after current test coverage work)

