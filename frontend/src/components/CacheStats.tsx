/**
 * CacheStats Component
 * Displays cache performance metrics and management controls
 */

import React, { useState, useEffect, useCallback } from 'react';
import type {
  CacheStatsProps,
  CacheStats as CacheStatsType,
  CacheInvalidationRequest,
} from '../types/content-generator';
import { ContentGeneratorAPI } from '../lib/api-client';

export const CacheStats: React.FC<CacheStatsProps> = ({
  apiUrl,
  apiKey,
  refreshInterval = 15000, // 15 seconds
  onInvalidate,
}) => {
  const [stats, setStats] = useState<CacheStatsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [invalidationMode, setInvalidationMode] = useState<'keys' | 'pattern' | 'tags'>('pattern');
  const [invalidationInput, setInvalidationInput] = useState('');
  const [invalidating, setInvalidating] = useState(false);
  const [invalidationSuccess, setInvalidationSuccess] = useState<string | null>(null);

  const api = new ContentGeneratorAPI(apiUrl, apiKey);

  const fetchStats = useCallback(async () => {
    try {
      const response = await api.getCacheStats();

      if (response.success && response.data) {
        setStats(response.data);
        setError(null);
      } else {
        setError(response.error?.message || 'Failed to fetch cache stats');
      }

      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchStats, refreshInterval]);

  const handleInvalidate = async () => {
    if (!invalidationInput.trim()) {
      setError('Please enter invalidation criteria');
      return;
    }

    setInvalidating(true);
    setError(null);
    setInvalidationSuccess(null);

    try {
      const request: CacheInvalidationRequest = {};

      if (invalidationMode === 'keys') {
        request.cache_keys = invalidationInput.split(',').map((k) => k.trim());
      } else if (invalidationMode === 'pattern') {
        request.pattern = invalidationInput.trim();
      } else if (invalidationMode === 'tags') {
        request.tags = invalidationInput.split(',').map((t) => t.trim());
      }

      const response = await api.invalidateCache(request);

      if (response.success && response.data) {
        setInvalidationSuccess(
          `Invalidated ${response.data.invalidated} cache entries`
        );
        setInvalidationInput('');
        onInvalidate?.(request);
        // Refresh stats after invalidation
        await fetchStats();
      } else {
        setError(response.error?.message || 'Invalidation failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setInvalidating(false);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to clear ALL caches? This cannot be undone.')) {
      return;
    }

    setInvalidating(true);
    setError(null);
    setInvalidationSuccess(null);

    try {
      const response = await api.clearAllCaches();

      if (response.success) {
        setInvalidationSuccess('All caches cleared successfully');
        await fetchStats();
      } else {
        setError(response.error?.message || 'Clear all failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setInvalidating(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  if (loading && !stats) {
    return (
      <div className="animate-pulse bg-white rounded-lg shadow p-6">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error && !stats) {
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
          <span className="text-red-800 font-medium">Failed to Load Cache Stats</span>
        </div>
        <p className="text-red-700 text-sm mt-2">{error}</p>
        <button
          onClick={fetchStats}
          className="mt-3 text-sm text-red-600 hover:text-red-800 font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Cache Performance</h2>
          <p className="text-sm text-gray-600 mt-1">
            {lastUpdate && `Updated ${lastUpdate.toLocaleTimeString()}`}
          </p>
        </div>
        <button
          onClick={fetchStats}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-sm text-blue-600 font-medium">Hit Rate</div>
          <div className="text-3xl font-bold text-blue-900">
            {(stats.hit_rate * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-blue-600 mt-1">
            {stats.hits.toLocaleString()} hits
          </div>
        </div>

        <div className="bg-purple-50 rounded-lg p-4">
          <div className="text-sm text-purple-600 font-medium">Miss Rate</div>
          <div className="text-3xl font-bold text-purple-900">
            {(stats.miss_rate * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-purple-600 mt-1">
            {stats.misses.toLocaleString()} misses
          </div>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="text-sm text-green-600 font-medium">Total Keys</div>
          <div className="text-3xl font-bold text-green-900">
            {stats.total_keys.toLocaleString()}
          </div>
          <div className="text-xs text-green-600 mt-1">
            {stats.evictions.toLocaleString()} evictions
          </div>
        </div>

        <div className="bg-orange-50 rounded-lg p-4">
          <div className="text-sm text-orange-600 font-medium">Memory Usage</div>
          <div className="text-3xl font-bold text-orange-900">
            {stats.memory_usage_mb.toFixed(1)} MB
          </div>
          <div className="text-xs text-orange-600 mt-1">
            Avg TTL: {formatDuration(stats.avg_ttl_seconds)}
          </div>
        </div>
      </div>

      {/* Cache Targets */}
      {stats.cache_targets && Object.keys(stats.cache_targets).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Cache Targets</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(stats.cache_targets).map(([target, targetStats]) => (
              <div
                key={target}
                className={`border-2 rounded-lg p-4 ${
                  targetStats.enabled
                    ? 'border-green-200 bg-green-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-bold uppercase text-gray-700">
                    {target}
                  </span>
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded ${
                      targetStats.enabled
                        ? 'bg-green-200 text-green-800'
                        : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {targetStats.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                {targetStats.enabled && (
                  <>
                    <div className="text-2xl font-bold text-gray-900 mb-1">
                      {(targetStats.hit_rate * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-600">
                      {targetStats.total_keys.toLocaleString()} keys
                      {targetStats.memory_mb !== undefined &&
                        ` • ${targetStats.memory_mb.toFixed(1)} MB`}
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cache Age */}
      {stats.oldest_key_age_seconds > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Oldest Cache Entry</div>
          <div className="text-xl font-bold text-gray-900">
            {formatDuration(stats.oldest_key_age_seconds)} old
          </div>
        </div>
      )}

      {/* Invalidation Controls */}
      <div className="border-t border-gray-200 pt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Cache Management
        </h3>

        {/* Invalidation Mode */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Invalidation Mode
          </label>
          <div className="flex space-x-4">
            {[
              { value: 'pattern', label: 'Pattern' },
              { value: 'keys', label: 'Specific Keys' },
              { value: 'tags', label: 'Tags' },
            ].map((mode) => (
              <label key={mode.value} className="flex items-center">
                <input
                  type="radio"
                  value={mode.value}
                  checked={invalidationMode === mode.value}
                  onChange={(e) =>
                    setInvalidationMode(e.target.value as 'keys' | 'pattern' | 'tags')
                  }
                  className="mr-2"
                />
                <span className="text-sm">{mode.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Invalidation Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {invalidationMode === 'pattern' && 'Pattern (e.g., content:*)'}
            {invalidationMode === 'keys' && 'Keys (comma-separated)'}
            {invalidationMode === 'tags' && 'Tags (comma-separated)'}
          </label>
          <input
            type="text"
            value={invalidationInput}
            onChange={(e) => setInvalidationInput(e.target.value)}
            placeholder={
              invalidationMode === 'pattern'
                ? 'content:*'
                : invalidationMode === 'keys'
                ? 'key1, key2, key3'
                : 'tag1, tag2'
            }
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={invalidating}
          />
        </div>

        {/* Success/Error Messages */}
        {invalidationSuccess && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
            <p className="text-green-800 text-sm">{invalidationSuccess}</p>
          </div>
        )}
        {error && stats && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={handleInvalidate}
            disabled={invalidating || !invalidationInput.trim()}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {invalidating ? 'Invalidating...' : 'Invalidate'}
          </button>
          <button
            onClick={handleClearAll}
            disabled={invalidating}
            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            Clear All
          </button>
        </div>
      </div>
    </div>
  );
};

export default CacheStats;
