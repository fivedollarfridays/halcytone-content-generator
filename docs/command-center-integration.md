# Command Center Integration Guide

**Status**: ✅ Backend API Ready for Command Center Integration
**Last Updated**: 2025-09-30

---

## Overview

The **Toombos** is a **headless backend service** designed to be consumed by a separate **Command Center/Hub UI application**. This document describes the integration points and APIs available for building a front-end dashboard.

---

## Architecture

```
┌─────────────────────────────────────┐
│   Command Center UI (Separate Repo) │
│   - React/Vue/Angular Dashboard     │
│   - Content Management Interface    │
│   - Real-time WebSocket Updates     │
│   - Performance Monitoring Views    │
└────────────────┬────────────────────┘
                 │ HTTP/REST + WebSocket
                 ▼
┌─────────────────────────────────────┐
│  Toombos API    │
│  (This Repository)                   │
│  - FastAPI Backend                   │
│  - REST Endpoints                    │
│  - WebSocket Server                  │
│  - Health/Metrics Endpoints          │
└─────────────────────────────────────┘
```

---

## Backend Readiness Status

### ✅ What's Ready for Integration

1. **CORS Configured** - `main.py:92-98`
   ```python
   allow_origins=["*"]  # Configure for your command center domain
   allow_credentials=True
   allow_methods=["*"]
   allow_headers=["*"]
   ```

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

## API Endpoints for Command Center

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: Configure `CORS_ORIGINS` environment variable

### Core Endpoints

#### 1. Health & Status
```
GET  /health              # Basic health check
GET  /health/detailed     # Detailed component health
GET  /ready               # Readiness probe
GET  /live                # Liveness probe
GET  /startup             # Startup probe
GET  /metrics             # Prometheus metrics
POST /health/check/{component}  # Manual component check
```

#### 2. Content Generation (v1)
```
POST /api/v1/generate             # Generate content
POST /api/v1/generate/email       # Generate email content
POST /api/v1/generate/social      # Generate social media content
POST /api/v1/batch/generate       # Batch content generation
GET  /api/v1/content/{content_id} # Retrieve generated content
```

#### 3. Content Generation (v2 - Enhanced)
```
POST /api/v2/content/generate     # Generate with full validation
GET  /api/v2/content/{content_id} # Get content by ID
PUT  /api/v2/content/{content_id} # Update content
DELETE /api/v2/content/{content_id} # Delete content
POST /api/v2/content/batch        # Batch operations
GET  /api/v2/templates            # List available templates
```

#### 4. WebSocket (Real-time)
```
WS /ws/content/{client_id}        # Content updates stream
WS /ws/session/{session_id}       # Session-specific updates
```

#### 5. Cache Management
```
POST /api/v1/cache/invalidate     # Invalidate cache
GET  /api/v1/cache/stats          # Cache statistics
POST /api/v1/cache/clear          # Clear all caches
GET  /api/v1/cache/history        # Invalidation history
```

#### 6. Critical Operations
```
POST /api/critical/emergency-publish  # Emergency content publishing
POST /api/critical/rollback           # Rollback recent changes
GET  /api/critical/status             # Critical system status
```

---

## Integration Patterns

### Pattern 1: Polling Dashboard

**Use Case**: Simple admin dashboard with periodic updates

```javascript
// Command Center - Dashboard Component
const DashboardWidget = () => {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const fetchHealth = async () => {
      const response = await fetch('http://localhost:8000/health/detailed');
      setHealth(await response.json());
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 5000); // Poll every 5s

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="health-widget">
      <h2>System Health: {health?.status}</h2>
      <div>Uptime: {health?.uptime_seconds}s</div>
      <div>Checks Passed: {health?.checks_passed}/{health?.checks_total}</div>
    </div>
  );
};
```

### Pattern 2: Real-time WebSocket Updates

**Use Case**: Live content generation monitoring

```javascript
// Command Center - Real-time Content Monitor
const ContentMonitor = ({ clientId }) => {
  const [updates, setUpdates] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/content/${clientId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setUpdates(prev => [data, ...prev]);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => ws.close();
  }, [clientId]);

  return (
    <div className="content-monitor">
      <h2>Live Content Updates</h2>
      {updates.map((update, i) => (
        <div key={i} className="update-item">
          <span>{update.timestamp}</span>
          <span>{update.type}</span>
          <span>{update.message}</span>
        </div>
      ))}
    </div>
  );
};
```

### Pattern 3: Content Generation Interface

**Use Case**: User-facing content creation form

```javascript
// Command Center - Content Generator Form
const ContentGeneratorForm = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleGenerate = async (formData) => {
    setLoading(true);

    const response = await fetch('http://localhost:8000/api/v2/content/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify({
        living_doc_id: formData.docId,
        channel: formData.channel,
        tone: formData.tone,
        dry_run: formData.dryRun
      })
    });

    const data = await response.json();
    setResult(data);
    setLoading(false);
  };

  return (
    <form onSubmit={(e) => { e.preventDefault(); handleGenerate(e.target); }}>
      {/* Form fields */}
      <button type="submit" disabled={loading}>
        {loading ? 'Generating...' : 'Generate Content'}
      </button>
      {result && <ContentPreview content={result} />}
    </form>
  );
};
```

---

## CORS Configuration for Production

### Backend Configuration (This Repo)

**File**: `src/halcytone_content_generator/main.py:92-98`

**Current** (Development):
```python
allow_origins=["*"]  # Allow all origins
```

**Recommended** (Production):
```python
# Set via environment variable
allow_origins=[
    "https://dashboard.halcytone.com",  # Your command center domain
    "https://admin.halcytone.com",      # Admin panel domain
    "http://localhost:3000",             # Local development
]
```

**Environment Variable**:
```bash
# .env
CORS_ORIGINS=https://dashboard.halcytone.com,https://admin.halcytone.com
```

### Update Code to Use Environment Variable

```python
# main.py
from .config import Settings

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Authentication Integration

### JWT Token Flow

1. **Command Center** authenticates user
2. **Command Center** requests JWT from backend
3. **Backend** validates credentials and issues JWT
4. **Command Center** includes JWT in all API requests

```javascript
// Command Center - API Client
const apiClient = {
  async request(endpoint, options = {}) {
    const token = localStorage.getItem('auth_token');

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.headers
      }
    });

    if (response.status === 401) {
      // Token expired, redirect to login
      window.location.href = '/login';
      return;
    }

    return response.json();
  }
};
```

---

## Monitoring Dashboard Integration

### Grafana Embedding

**Grafana Dashboard URLs** (when monitoring stack is running):
- Main Overview: `http://localhost:3000/d/halcytone-overview`
- Performance: `http://localhost:3000/d/halcytone-performance`

**Embed in Command Center**:
```html
<!-- Command Center - Embedded Grafana Dashboard -->
<iframe
  src="http://grafana-host:3000/d/halcytone-overview?orgId=1&refresh=5s&kiosk"
  width="100%"
  height="600"
  frameborder="0">
</iframe>
```

### Custom Metrics Dashboard

**Fetch Prometheus Metrics**:
```javascript
// Command Center - Custom Metrics Dashboard
const MetricsDashboard = () => {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      const response = await fetch('http://localhost:8000/metrics');
      const text = await response.text();

      // Parse Prometheus metrics format
      const parsed = parsePrometheusMetrics(text);
      setMetrics(parsed);
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000); // Every 10s

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="metrics-dashboard">
      <MetricCard
        title="Uptime"
        value={metrics?.app_uptime_seconds}
        unit="seconds"
      />
      <MetricCard
        title="CPU Usage"
        value={metrics?.app_cpu_usage_percent}
        unit="%"
      />
      <MetricCard
        title="Memory Usage"
        value={metrics?.app_memory_usage_percent}
        unit="%"
      />
    </div>
  );
};
```

---

## Required Command Center Features

### Minimum Viable Command Center

1. **System Health Dashboard**
   - Overall system status (healthy/degraded/unhealthy)
   - Component health breakdown
   - Uptime tracking
   - Real-time alerts

2. **Content Generation Interface**
   - Form to trigger content generation
   - Document source selection
   - Channel selection (email, social, web)
   - Tone/style configuration
   - Dry run toggle
   - Preview generated content

3. **Content Management**
   - List recent content generations
   - View content details
   - Edit/update content
   - Delete content
   - Schedule publishing

4. **Cache Management**
   - View cache statistics
   - Invalidate specific caches
   - Clear all caches
   - View invalidation history

5. **Monitoring Views**
   - Embedded Grafana dashboards
   - Real-time metrics
   - Performance graphs
   - Error logs

### Advanced Features (Optional)

6. **A/B Testing Dashboard**
   - Create A/B tests
   - View test results
   - Compare variations

7. **Approval Workflow UI**
   - Content approval queue
   - Multi-level approval visualization
   - Approval/rejection actions

8. **Analytics Dashboard**
   - Content performance metrics
   - Engagement analytics
   - Channel-specific insights

9. **User Management**
   - User roles and permissions
   - API key management
   - Audit logs

---

## Example Command Center Tech Stacks

### Option 1: React + TypeScript
```
Frontend: React 18 + TypeScript
State: React Query + Zustand
UI: Material-UI or Ant Design
Charts: Recharts or Chart.js
WebSocket: native WebSocket API
```

### Option 2: Vue 3 + TypeScript
```
Frontend: Vue 3 Composition API + TypeScript
State: Pinia
UI: Vuetify or Element Plus
Charts: Vue-ChartJS
WebSocket: vue-native-websocket
```

### Option 3: Next.js (Full-Stack)
```
Frontend: Next.js 14 + React Server Components
API Routes: Next.js API routes (optional proxy)
State: SWR or React Query
UI: Shadcn/ui or Chakra UI
Charts: Tremor or Recharts
```

---

## Backend Configuration Checklist

### Current Status: ✅ Ready for Integration

- [x] CORS middleware enabled
- [x] REST API endpoints documented
- [x] WebSocket support implemented
- [x] Health check endpoints available
- [x] Metrics endpoints (Prometheus format)
- [x] Authentication system ready
- [x] Error handling standardized
- [x] API versioning (v1, v2)
- [x] Request validation (Pydantic)
- [x] Response schemas defined

### Configuration Needed for Production

- [ ] Set specific CORS origins (not `*`)
- [ ] Configure JWT secret keys
- [ ] Set up API rate limiting
- [ ] Configure authentication providers
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (Nginx/Traefik)

---

## Quick Start for Command Center Development

### 1. Start Backend Services

```bash
# Start the content generator API
cd toombos-backend
docker-compose up -d

# Or run locally
python -m uvicorn src.halcytone_content_generator.main:app --reload

# Start monitoring stack
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Verify Backend is Running

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Grafana dashboard
open http://localhost:3000
```

### 3. Create Command Center Project

```bash
# Example: React command center
npx create-react-app halcytone-command-center --template typescript
cd halcytone-command-center

# Install dependencies
npm install axios react-query recharts

# Set API base URL
echo "REACT_APP_API_URL=http://localhost:8000" > .env
```

### 4. Test API Connection

```javascript
// src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 10000,
});

export const getHealth = () => apiClient.get('/health/detailed');
export const generateContent = (data) => apiClient.post('/api/v2/content/generate', data);
```

---

## API Documentation

The backend provides **interactive API documentation**:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These include:
- All endpoint descriptions
- Request/response schemas
- Example requests
- Try-it-out functionality

---

## Next Steps

### For Command Center Development

1. **Choose Tech Stack** - React/Vue/Next.js
2. **Set Up Project** - Create new repository
3. **Build Core Features**:
   - Authentication flow
   - System health dashboard
   - Content generation interface
   - Real-time updates (WebSocket)
4. **Integrate Monitoring** - Embed Grafana or build custom
5. **Add Advanced Features** - A/B testing, analytics, etc.

### Backend Updates Needed

If specific command center requirements arise:

1. **New Endpoints** - Add to this backend
2. **WebSocket Events** - Extend event types
3. **Authentication** - Configure OAuth/SAML if needed
4. **CORS** - Update allowed origins
5. **Rate Limiting** - Configure per-endpoint limits

---

## Support & Documentation

- **API Docs**: http://localhost:8000/docs
- **Health Endpoints**: See `src/halcytone_content_generator/api/health_endpoints.py`
- **WebSocket**: See `src/halcytone_content_generator/api/websocket_endpoints.py`
- **Configuration**: See `src/halcytone_content_generator/config.py`

---

**Status**: ✅ **Backend is ready for Command Center integration**
**Next**: Build the Command Center UI in a separate repository

