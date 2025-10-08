/**
 * API Client for Content Generator
 * TypeScript client matching the Python API
 */

import type {
  HealthStatus,
  Metrics,
  SyncJob,
  JobsListResponse,
  ContentGenerationRequest,
  CacheStats,
  CacheInvalidationRequest,
  CacheInvalidationResponse,
  ValidationResult,
  APIResponse,
} from '../types/content-generator';

export class ContentGeneratorAPI {
  private baseUrl: string;
  private apiKey?: string;
  private correlationIdHeader = 'X-Correlation-ID';

  constructor(baseUrl: string, apiKey?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.apiKey = apiKey;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<APIResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: {
            message: data.detail || data.message || 'Request failed',
            status: response.status,
            details: data,
          },
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: {
          message: error instanceof Error ? error.message : 'Network error',
        },
      };
    }
  }

  // ========== Health & Status ==========

  async healthCheck(): Promise<APIResponse<HealthStatus>> {
    return this.request<HealthStatus>('/health');
  }

  async readinessCheck(): Promise<APIResponse<{ ready: boolean }>> {
    return this.request('/ready');
  }

  async metrics(): Promise<APIResponse<Metrics>> {
    return this.request<Metrics>('/metrics');
  }

  // ========== Content Generation ==========

  async generateContent(
    request: ContentGenerationRequest
  ): Promise<APIResponse<SyncJob>> {
    return this.request<SyncJob>('/api/v2/content/sync', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async previewContent(documentId?: string): Promise<APIResponse<any>> {
    const params = documentId ? `?document_id=${documentId}` : '';
    return this.request(`/api/v1/preview${params}`);
  }

  async validateContent(
    content: any,
    contentType?: string,
    strict = true
  ): Promise<APIResponse<ValidationResult>> {
    return this.request<ValidationResult>('/api/v2/content/validate', {
      method: 'POST',
      body: JSON.stringify({ content, content_type: contentType, strict }),
    });
  }

  // ========== Jobs ==========

  async listJobs(params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<APIResponse<JobsListResponse>> {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.set('status', params.status);
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.offset) queryParams.set('offset', params.offset.toString());

    const query = queryParams.toString();
    return this.request<JobsListResponse>(
      `/api/v2/content/sync${query ? `?${query}` : ''}`
    );
  }

  async getJob(jobId: string): Promise<APIResponse<SyncJob>> {
    return this.request<SyncJob>(`/api/v2/content/sync/${jobId}`);
  }

  async cancelJob(jobId: string): Promise<APIResponse<{ cancelled: boolean }>> {
    return this.request(`/api/v2/content/sync/${jobId}`, {
      method: 'DELETE',
    });
  }

  async retryJob(jobId: string): Promise<APIResponse<SyncJob>> {
    return this.request<SyncJob>(`/api/v2/content/sync/${jobId}/retry`, {
      method: 'POST',
    });
  }

  // ========== Cache ==========

  async getCacheStats(): Promise<APIResponse<CacheStats>> {
    return this.request<CacheStats>('/api/v2/cache/stats');
  }

  async invalidateCache(
    request: CacheInvalidationRequest
  ): Promise<APIResponse<CacheInvalidationResponse>> {
    return this.request<CacheInvalidationResponse>('/api/v2/cache/invalidate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async clearAllCaches(): Promise<APIResponse<{ cleared: boolean }>> {
    return this.request('/api/v2/cache/clear', {
      method: 'POST',
    });
  }

  // ========== Batch Operations ==========

  async batchGenerate(
    requests: ContentGenerationRequest[],
    parallel = true,
    failFast = false
  ): Promise<APIResponse<any>> {
    return this.request('/api/v2/batch/generate', {
      method: 'POST',
      body: JSON.stringify({ requests, parallel, fail_fast: failFast }),
    });
  }

  // ========== Utilities ==========

  setApiKey(apiKey: string) {
    this.apiKey = apiKey;
  }

  generateCorrelationId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

export default ContentGeneratorAPI;
