# Command Center Quick Start Guide

**For developers building the front-end dashboard**

---

## 🎯 What You're Building

A **web-based command center** that connects to the Toombos API to:
- Monitor system health
- Generate content
- Manage jobs and batches
- View real-time updates
- Control cache and services

---

## ✅ Backend is Ready

- ✅ API endpoints: 54 REST + WebSocket
- ✅ CORS enabled (configure for your domain)
- ✅ Authentication ready (JWT + API keys)
- ✅ WebSocket support for real-time updates
- ✅ Comprehensive health/metrics endpoints
- ✅ Interactive docs at `/docs`

---

## 🚀 Quick Start (5 Minutes)

### 1. Start the Backend

```bash
# Clone backend repo (if not already)
git clone https://github.com/your-org/toombos-backend.git
cd toombos-backend

# Start with Docker
docker-compose up -d

# Or run locally
python -m uvicorn src.halcytone_content_generator.main:app --reload
```

**Verify it's running**:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

### 2. Create Your Command Center Project

```bash
# React example
npx create-react-app halcytone-dashboard --template typescript
cd halcytone-dashboard

# Install dependencies
npm install axios react-query @tanstack/react-query recharts

# Create .env
echo "REACT_APP_API_URL=http://localhost:8000" > .env
```

### 3. Test API Connection

Create `src/api/client.ts`:
```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 10000,
});

// Test connection
export const testConnection = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

// Generate content
export const generateContent = async (data: any) => {
  const response = await apiClient.post('/api/v2/generate-content', data);
  return response.data;
};
```

### 4. Create First Component

Create `src/components/HealthWidget.tsx`:
```typescript
import { useEffect, useState } from 'react';
import { testConnection } from '../api/client';

export const HealthWidget = () => {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await testConnection();
        setHealth(data);
      } catch (error) {
        console.error('Failed to fetch health:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Loading...</div>;
  if (!health) return <div>Error connecting to API</div>;

  return (
    <div className="health-widget">
      <h2>System Status: {health.status}</h2>
      <p>Service: {health.service}</p>
      <p>Uptime: {health.uptime_seconds}s</p>
      <p>Environment: {health.environment}</p>
    </div>
  );
};
```

### 5. Run Your Dashboard

```bash
npm start
# Opens http://localhost:3000
```

You should see the health widget showing system status!

---

## 📚 Essential API Endpoints to Implement

### Priority 1: Core Dashboard (MVP)

```typescript
// 1. System Health
GET /health/detailed
// Use for: Main status indicator, component health breakdown

// 2. Metrics
GET /api/v2/metrics
// Use for: Real-time metrics dashboard

// 3. Generate Content
POST /api/v2/generate-content
// Use for: Main content generation form

// 4. Job Status
GET /api/v2/jobs/{job_id}
// Use for: Progress tracking after content generation

// 5. Service Status
GET /api/v1/services/status
// Use for: External service health monitoring
```

### Priority 2: Content Management

```typescript
// 6. List Templates
GET /api/v2/templates
// Use for: Template selector dropdown

// 7. List Jobs
GET /api/v2/jobs?status=pending&limit=50
// Use for: Job queue dashboard

// 8. Validate Content
POST /api/v2/validate-content
// Use for: Pre-publish validation

// 9. Preview Content
GET /api/v1/preview?content_id={id}&channel={channel}
// Use for: Content preview modal
```

### Priority 3: Real-Time Updates

```typescript
// 10. WebSocket Connection
WS /ws/content/{client_id}
// Use for: Live content updates, notifications

// Example WebSocket implementation
const ws = new WebSocket('ws://localhost:8000/ws/content/my-client-id');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Content update:', data);
  // Update UI with new content
};
```

---

## 🎨 Example Dashboard Components

### 1. Health Dashboard

```typescript
// src/components/HealthDashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export const HealthDashboard = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await apiClient.get('/health/detailed');
      return response.data;
    },
    refetchInterval: 5000, // Auto-refresh every 5s
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="health-dashboard">
      <h1>System Health: {data.status}</h1>

      <div className="metrics">
        <Metric label="Uptime" value={`${data.uptime_seconds}s`} />
        <Metric label="Checks Passed" value={`${data.checks_passed}/${data.checks_total}`} />
        <Metric label="Response Time" value={`${data.response_time_ms}ms`} />
      </div>

      <div className="components">
        <h2>Components</h2>
        {Object.entries(data.components).map(([name, component]: any) => (
          <ComponentStatus key={name} name={name} component={component} />
        ))}
      </div>

      {data.errors.length > 0 && (
        <div className="errors">
          <h3>Errors</h3>
          {data.errors.map((error: string, i: number) => (
            <div key={i} className="error">{error}</div>
          ))}
        </div>
      )}
    </div>
  );
};
```

### 2. Content Generator Form

```typescript
// src/components/ContentGenerator.tsx
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export const ContentGenerator = () => {
  const [formData, setFormData] = useState({
    living_doc_id: '',
    channel: 'email',
    tone: 'professional',
    dry_run: false,
  });

  const generateMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiClient.post('/api/v2/generate-content', data);
      return response.data;
    },
    onSuccess: (data) => {
      console.log('Content generated:', data);
      // Show success message, navigate to preview, etc.
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    generateMutation.mutate(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Generate Content</h2>

      <label>
        Document ID:
        <input
          type="text"
          value={formData.living_doc_id}
          onChange={(e) => setFormData({...formData, living_doc_id: e.target.value})}
          required
        />
      </label>

      <label>
        Channel:
        <select
          value={formData.channel}
          onChange={(e) => setFormData({...formData, channel: e.target.value})}
        >
          <option value="email">Email</option>
          <option value="social">Social Media</option>
          <option value="web">Website</option>
        </select>
      </label>

      <label>
        Tone:
        <select
          value={formData.tone}
          onChange={(e) => setFormData({...formData, tone: e.target.value})}
        >
          <option value="professional">Professional</option>
          <option value="casual">Casual</option>
          <option value="empowering">Empowering</option>
        </select>
      </label>

      <label>
        <input
          type="checkbox"
          checked={formData.dry_run}
          onChange={(e) => setFormData({...formData, dry_run: e.target.checked})}
        />
        Dry Run (test mode)
      </label>

      <button type="submit" disabled={generateMutation.isPending}>
        {generateMutation.isPending ? 'Generating...' : 'Generate Content'}
      </button>

      {generateMutation.isSuccess && (
        <div className="success">
          <h3>Content Generated!</h3>
          <pre>{JSON.stringify(generateMutation.data, null, 2)}</pre>
        </div>
      )}

      {generateMutation.isError && (
        <div className="error">
          Error: {generateMutation.error.message}
        </div>
      )}
    </form>
  );
};
```

### 3. Metrics Dashboard

```typescript
// src/components/MetricsDashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';
import { apiClient } from '../api/client';

export const MetricsDashboard = () => {
  const { data } = useQuery({
    queryKey: ['metrics'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v2/metrics');
      return response.data;
    },
    refetchInterval: 10000, // Refresh every 10s
  });

  if (!data) return <div>Loading metrics...</div>;

  return (
    <div className="metrics-dashboard">
      <h2>System Metrics</h2>

      <div className="metric-cards">
        <MetricCard
          title="CPU Usage"
          value={data.cpu_usage_percent}
          unit="%"
          status={data.cpu_usage_percent > 80 ? 'warning' : 'ok'}
        />
        <MetricCard
          title="Memory Usage"
          value={data.memory_usage_percent}
          unit="%"
          status={data.memory_usage_percent > 80 ? 'warning' : 'ok'}
        />
        <MetricCard
          title="Avg Response Time"
          value={data.avg_response_time_ms}
          unit="ms"
          status={data.avg_response_time_ms > 200 ? 'warning' : 'ok'}
        />
        <MetricCard
          title="Error Rate"
          value={(data.error_rate * 100).toFixed(2)}
          unit="%"
          status={data.error_rate > 0.05 ? 'error' : 'ok'}
        />
      </div>
    </div>
  );
};
```

### 4. Real-Time Updates with WebSocket

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useState } from 'react';

export const useWebSocket = (clientId: string) => {
  const [messages, setMessages] = useState<any[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/content/${clientId}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);
      setMessages((prev) => [data, ...prev]);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [clientId]);

  return { messages, connected };
};

// Usage in component
export const LiveUpdates = () => {
  const { messages, connected } = useWebSocket('my-dashboard-client');

  return (
    <div className="live-updates">
      <h2>Live Updates {connected ? '🟢' : '🔴'}</h2>
      {messages.map((msg, i) => (
        <div key={i} className="update-item">
          <span className="timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</span>
          <span className="type">{msg.type}</span>
          <span className="message">{msg.data?.message}</span>
        </div>
      ))}
    </div>
  );
};
```

---

## 🔐 Authentication Setup

### 1. Add Auth to API Client

```typescript
// src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 10000,
});

// Add auth token to all requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export { apiClient };
```

### 2. Login Component

```typescript
// src/components/Login.tsx
import { useState } from 'react';
import { apiClient } from '../api/client';

export const Login = ({ onSuccess }: { onSuccess: () => void }) => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Note: Adjust endpoint based on your auth implementation
      const response = await apiClient.post('/api/v1/auth/login', credentials);
      localStorage.setItem('auth_token', response.data.access_token);
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Login failed');
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <h2>Login</h2>
      {error && <div className="error">{error}</div>}
      <input
        type="text"
        placeholder="Username"
        value={credentials.username}
        onChange={(e) => setCredentials({...credentials, username: e.target.value})}
      />
      <input
        type="password"
        placeholder="Password"
        value={credentials.password}
        onChange={(e) => setCredentials({...credentials, password: e.target.value})}
      />
      <button type="submit">Login</button>
    </form>
  );
};
```

---

## 🎨 UI Component Libraries (Recommended)

### Material-UI (MUI)
```bash
npm install @mui/material @emotion/react @emotion/styled
```

### Ant Design
```bash
npm install antd
```

### Chakra UI
```bash
npm install @chakra-ui/react @emotion/react @emotion/styled framer-motion
```

### Shadcn/ui (Recommended for modern look)
```bash
npx shadcn-ui@latest init
```

---

## 📊 Monitoring Integration

### Embed Grafana Dashboard

```typescript
// src/components/GrafanaEmbed.tsx
export const GrafanaEmbed = () => {
  return (
    <iframe
      src="http://localhost:3000/d/halcytone-overview?orgId=1&refresh=5s&kiosk"
      width="100%"
      height="600"
      frameBorder="0"
      title="Grafana Dashboard"
    />
  );
};
```

---

## 🧪 Testing Your Integration

### Test Checklist

```bash
# 1. Backend health check
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}

# 2. Generate content test
curl -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{
    "living_doc_id": "test123",
    "channel": "email",
    "tone": "professional",
    "dry_run": true
  }'

# 3. Get metrics
curl http://localhost:8000/api/v2/metrics

# 4. WebSocket test (use browser console)
const ws = new WebSocket('ws://localhost:8000/ws/content/test-client');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
```

---

## 📖 Full Documentation

- **Complete API Reference**: See `api-reference-for-command-center.md`
- **Integration Guide**: See `command-center-integration.md`
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

---

## 🚀 Next Steps

1. ✅ Start backend (Docker or local)
2. ✅ Create React/Vue project
3. ✅ Implement health widget
4. ✅ Add content generation form
5. ✅ Integrate WebSocket updates
6. ⬜ Add authentication
7. ⬜ Implement job monitoring
8. ⬜ Add cache management UI
9. ⬜ Embed Grafana dashboards
10. ⬜ Deploy to production

---

## 💡 Pro Tips

1. **Use React Query** - Handles caching, refetching, and state management
2. **WebSocket Reconnection** - Implement auto-reconnect logic
3. **Error Boundaries** - Wrap components in error boundaries
4. **Loading States** - Show loading indicators for better UX
5. **Polling Intervals** - Use appropriate intervals (5s for health, 10s for metrics)
6. **Responsive Design** - Make dashboard mobile-friendly
7. **Dark Mode** - Consider adding dark mode support
8. **Notifications** - Use toast notifications for real-time updates

---

## 🆘 Troubleshooting

### CORS Error
```
Add backend domain to CORS origins in backend config
```

### WebSocket Connection Failed
```
Check that backend is running and port 8000 is accessible
```

### 401 Unauthorized
```
Add auth token to requests or configure API key
```

### Slow API Responses
```
Check backend logs, may need to scale services
```

---

**Ready to build? Start with the Health Dashboard and expand from there!** 🎉
