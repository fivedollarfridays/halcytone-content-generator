/**
 * ContentGeneratorHealth Component
 * Displays API health status, checks, and system metrics
 */

import React, { useState, useEffect, useCallback } from 'react';
import type {
  HealthStatus,
  Metrics,
  Content GeneratorHealthProps,
} from '../types/content-generator';
import { ContentGeneratorAPI } from '../lib/api-client';

export const ContentGeneratorHealth: React.FC<ContentGeneratorHealthProps> = ({
  apiUrl,
  refreshInterval = 30000, // 30 seconds
  onStatusChange,
}) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const api = new ContentGeneratorAPI(apiUrl);

  const fetchHealth = useCallback(async () => {
    try {
      const [healthResponse, metricsResponse] = await Promise.all([
        api.healthCheck(),
        api.metrics(),
      ]);

      if (healthResponse.success && healthResponse.data) {
        setHealth(healthResponse.data);
        setError(null);
        onStatusChange?.(healthResponse.data);
      } else {
        setError(healthResponse.error?.message || 'Failed to fetch health');
      }

      if (metricsResponse.success && metricsResponse.data) {
        setMetrics(metricsResponse.data);
      }

      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [apiUrl, onStatusChange]);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchHealth, refreshInterval]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'pass':
        return 'text-green-600 bg-green-50';
      case 'degraded':
      case 'warn':
        return 'text-yellow-600 bg-yellow-50';
      case 'unhealthy':
      case 'fail':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (loading && !health) {
    return (
      <div className="animate-pulse bg-white rounded-lg shadow p-6">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error && !health) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <svg
            className="w-5 h-5 text-red-600 mr-2"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          <span className="text-red-800 font-medium">Health Check Failed</span>
        </div>
        <p className="text-red-700 text-sm mt-2">{error}</p>
        <button
          onClick={fetchHealth}
          className="mt-3 text-sm text-red-600 hover:text-red-800 font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!health) return null;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div
            className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(
              health.status
            )}`}
          >
            {health.status.toUpperCase()}
          </div>
          <h2 className="text-xl font-bold text-gray-900">API Health</h2>
        </div>
        {lastUpdate && (
          <span className="text-sm text-gray-500">
            Updated {lastUpdate.toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* System Info */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Uptime</div>
          <div className="text-2xl font-bold text-gray-900">
            {formatUptime(health.uptime)}
          </div>
        </div>
        {health.version && (
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600">Version</div>
            <div className="text-2xl font-bold text-gray-900">
              {health.version}
            </div>
          </div>
        )}
        {metrics && (
          <>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">Active Jobs</div>
              <div className="text-2xl font-bold text-gray-900">
                {metrics.active_jobs}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">Queue Size</div>
              <div className="text-2xl font-bold text-gray-900">
                {metrics.queue_size}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Health Checks */}
      {health.checks && Object.keys(health.checks).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            System Checks
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(health.checks).map(([name, check]) => (
              <div
                key={name}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 capitalize">
                    {name.replace(/_/g, ' ')}
                  </span>
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded ${getStatusColor(
                      check.status
                    )}`}
                  >
                    {check.status}
                  </span>
                </div>
                {check.message && (
                  <p className="text-sm text-gray-600 mb-1">{check.message}</p>
                )}
                {check.latency_ms !== undefined && (
                  <p className="text-xs text-gray-500">
                    Latency: {check.latency_ms.toFixed(2)}ms
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metrics */}
      {metrics && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Performance Metrics
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-sm text-blue-600 font-medium">
                Requests/sec
              </div>
              <div className="text-2xl font-bold text-blue-900">
                {metrics.requests_per_second.toFixed(2)}
              </div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-sm text-purple-600 font-medium">
                Avg Response
              </div>
              <div className="text-2xl font-bold text-purple-900">
                {metrics.avg_response_time_ms.toFixed(0)}ms
              </div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-sm text-green-600 font-medium">
                Cache Hit Rate
              </div>
              <div className="text-2xl font-bold text-green-900">
                {(metrics.cache_hit_rate * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-sm text-red-600 font-medium">Error Rate</div>
              <div className="text-2xl font-bold text-red-900">
                {(metrics.error_rate * 100).toFixed(2)}%
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 font-medium">
                Total Requests
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {metrics.requests_total.toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Refresh Button */}
      <div className="flex justify-end">
        <button
          onClick={fetchHealth}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Refreshing...' : 'Refresh Now'}
        </button>
      </div>
    </div>
  );
};

export default ContentGeneratorHealth;
