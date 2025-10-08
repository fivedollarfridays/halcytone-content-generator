/**
 * TypeScript types for Content Generator components
 */

// ========== Health & Status ==========

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: {
    database?: HealthCheck;
    cache?: HealthCheck;
    external_services?: HealthCheck;
    disk?: HealthCheck;
    memory?: HealthCheck;
  };
  uptime: number;
  version?: string;
}

export interface HealthCheck {
  status: 'pass' | 'fail' | 'warn';
  message?: string;
  latency_ms?: number;
}

export interface Metrics {
  requests_total: number;
  requests_per_second: number;
  avg_response_time_ms: number;
  error_rate: number;
  cache_hit_rate: number;
  active_jobs: number;
  queue_size: number;
}

// ========== Content Generation ==========

export type ContentType = 'update' | 'blog' | 'announcement';
export type Channel = 'email' | 'website' | 'social_twitter' | 'social_linkedin' | 'social_facebook';
export type TemplateStyle = 'modern' | 'classic' | 'minimal';

export interface ContentGenerationRequest {
  document_id?: string;
  channels: Channel[];
  content_type?: ContentType;
  template_style?: TemplateStyle;
  schedule_time?: string;
  dry_run?: boolean;
  metadata?: Record<string, any>;
}

export interface ContentGenerationResponse {
  job_id: string;
  status: JobStatus;
  channels: Channel[];
  created_at: string;
  scheduled_for?: string;
}

// ========== Jobs ==========

export type JobStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'partial' | 'cancelled';

export interface SyncJob {
  job_id: string;
  document_id: string;
  channels: Channel[];
  status: JobStatus;
  created_at: string;
  updated_at: string;
  scheduled_for?: string;
  started_at?: string;
  completed_at?: string;
  results?: JobResults;
  errors?: string[];
  metadata?: Record<string, any>;
  correlation_id?: string;
}

export interface JobResults {
  email?: ChannelResult;
  website?: ChannelResult;
  twitter?: ChannelResult;
  linkedin?: ChannelResult;
  facebook?: ChannelResult;
}

export interface ChannelResult {
  status: 'success' | 'failed';
  sent?: number;
  content_id?: string;
  url?: string;
  error?: string;
  timestamp: string;
}

export interface JobsListResponse {
  jobs: SyncJob[];
  total: number;
  page: number;
  page_size: number;
}

// ========== Cache ==========

export interface CacheStats {
  total_keys: number;
  hit_rate: number;
  miss_rate: number;
  hits: number;
  misses: number;
  evictions: number;
  memory_usage_mb: number;
  avg_ttl_seconds: number;
  oldest_key_age_seconds: number;
  cache_targets: {
    local?: CacheTargetStats;
    redis?: CacheTargetStats;
    api?: CacheTargetStats;
  };
}

export interface CacheTargetStats {
  enabled: boolean;
  hit_rate: number;
  total_keys: number;
  memory_mb?: number;
}

export interface CacheInvalidationRequest {
  cache_keys?: string[];
  pattern?: string;
  tags?: string[];
}

export interface CacheInvalidationResponse {
  invalidated: number;
  targets: string[];
  timestamp: string;
}

// ========== Templates ==========

export interface Template {
  id: string;
  name: string;
  description: string;
  style: TemplateStyle;
  preview_url?: string;
  supported_channels: Channel[];
  variables?: TemplateVariable[];
}

export interface TemplateVariable {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date';
  required: boolean;
  default_value?: any;
  description?: string;
}

// ========== Analytics ==========

export interface ContentAnalytics {
  total_views: number;
  unique_views: number;
  engagement_rate: number;
  avg_time_on_page: number;
  bounce_rate: number;
  conversions: number;
  by_channel: {
    [key in Channel]?: ChannelAnalytics;
  };
}

export interface ChannelAnalytics {
  views: number;
  clicks: number;
  conversions: number;
  engagement_rate: number;
}

export interface EmailAnalytics {
  total_sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  bounced: number;
  unsubscribed: number;
  open_rate: number;
  click_rate: number;
  bounce_rate: number;
  unsubscribe_rate: number;
}

// ========== Validation ==========

export interface ValidationResult {
  is_valid: boolean;
  content_type: ContentType;
  issues: string[];
  warnings: string[];
  enhanced_metadata?: {
    word_count?: number;
    reading_time?: number;
    seo_score?: number;
    recommended_channels?: Channel[];
  };
}

// ========== API Response ==========

export interface APIResponse<T = any> {
  data?: T;
  error?: APIError;
  success: boolean;
}

export interface APIError {
  message: string;
  code?: string;
  status?: number;
  details?: Record<string, any>;
}

// ========== Component Props ==========

export interface ContentGeneratorHealthProps {
  apiUrl: string;
  refreshInterval?: number;
  onStatusChange?: (status: HealthStatus) => void;
}

export interface ContentGenerationFormProps {
  apiUrl: string;
  apiKey?: string;
  onSubmit?: (job: SyncJob) => void;
  onError?: (error: APIError) => void;
  defaultChannels?: Channel[];
  defaultTemplate?: TemplateStyle;
}

export interface JobsListProps {
  apiUrl: string;
  apiKey?: string;
  refreshInterval?: number;
  pageSize?: number;
  statusFilter?: JobStatus[];
  onJobClick?: (job: SyncJob) => void;
}

export interface JobStatusCardProps {
  job: SyncJob;
  onRetry?: (jobId: string) => void;
  onCancel?: (jobId: string) => void;
  onViewDetails?: (jobId: string) => void;
  compact?: boolean;
}

export interface CacheStatsProps {
  apiUrl: string;
  apiKey?: string;
  refreshInterval?: number;
  onInvalidate?: (request: CacheInvalidationRequest) => void;
}

export interface TemplateSelectorProps {
  templates: Template[];
  selectedTemplate?: Template;
  onChange: (template: Template) => void;
  showPreview?: boolean;
  channelFilter?: Channel[];
}
