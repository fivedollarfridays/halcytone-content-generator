/**
 * JobsList Component
 * Displays list of sync jobs with filtering and pagination
 */

import React, { useState, useEffect, useCallback } from 'react';
import type {
  JobsListProps,
  SyncJob,
  JobStatus,
  JobsListResponse,
} from '../types/content-generator';
import { ContentGeneratorAPI } from '../lib/api-client';

export const JobsList: React.FC<JobsListProps> = ({
  apiUrl,
  apiKey,
  refreshInterval = 10000, // 10 seconds
  pageSize = 20,
  statusFilter,
  onJobClick,
}) => {
  const [jobs, setJobs] = useState<SyncJob[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedStatus, setSelectedStatus] = useState<JobStatus | 'all'>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const api = new ContentGeneratorAPI(apiUrl, apiKey);

  const fetchJobs = useCallback(async () => {
    try {
      const params: any = {
        limit: pageSize,
        offset: (currentPage - 1) * pageSize,
      };

      if (selectedStatus !== 'all') {
        params.status = selectedStatus;
      }

      const response = await api.listJobs(params);

      if (response.success && response.data) {
        setJobs(response.data.jobs);
        setTotal(response.data.total);
        setError(null);
      } else {
        setError(response.error?.message || 'Failed to fetch jobs');
      }

      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [api, currentPage, pageSize, selectedStatus]);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchJobs, refreshInterval]);

  const getStatusColor = (status: JobStatus) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-100';
      case 'in_progress':
        return 'text-blue-700 bg-blue-100';
      case 'pending':
        return 'text-yellow-700 bg-yellow-100';
      case 'failed':
        return 'text-red-700 bg-red-100';
      case 'partial':
        return 'text-orange-700 bg-orange-100';
      case 'cancelled':
        return 'text-gray-700 bg-gray-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  const getStatusIcon = (status: JobStatus) => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'in_progress':
        return '⟳';
      case 'pending':
        return '⏱';
      case 'failed':
        return '✕';
      case 'partial':
        return '⚠';
      case 'cancelled':
        return '⊘';
      default:
        return '•';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const totalPages = Math.ceil(total / pageSize);

  const statuses: Array<{ value: JobStatus | 'all'; label: string }> = [
    { value: 'all', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
    { value: 'partial', label: 'Partial' },
    { value: 'cancelled', label: 'Cancelled' },
  ];

  if (loading && jobs.length === 0) {
    return (
      <div className="animate-pulse bg-white rounded-lg shadow p-6">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error && jobs.length === 0) {
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
          <span className="text-red-800 font-medium">Failed to Load Jobs</span>
        </div>
        <p className="text-red-700 text-sm mt-2">{error}</p>
        <button
          onClick={fetchJobs}
          className="mt-3 text-sm text-red-600 hover:text-red-800 font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Sync Jobs</h2>
          <p className="text-sm text-gray-600 mt-1">
            {total} total jobs
            {lastUpdate && (
              <span className="ml-2">• Updated {lastUpdate.toLocaleTimeString()}</span>
            )}
          </p>
        </div>
        <button
          onClick={fetchJobs}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Status Filter */}
      <div className="mb-6">
        <div className="flex flex-wrap gap-2">
          {statuses.map((status) => (
            <button
              key={status.value}
              onClick={() => {
                setSelectedStatus(status.value);
                setCurrentPage(1);
              }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedStatus === status.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status.label}
            </button>
          ))}
        </div>
      </div>

      {/* Jobs List */}
      {jobs.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <svg
            className="w-16 h-16 mx-auto mb-4 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-lg font-medium">No jobs found</p>
          <p className="text-sm mt-1">
            {selectedStatus !== 'all'
              ? `No ${selectedStatus} jobs`
              : 'Start by generating some content'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <div
              key={job.job_id}
              onClick={() => onJobClick?.(job)}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(
                        job.status
                      )}`}
                    >
                      {getStatusIcon(job.status)} {job.status.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500 font-mono">
                      {job.job_id.substring(0, 12)}...
                    </span>
                  </div>

                  <div className="text-sm text-gray-700 mb-2">
                    <span className="font-medium">Document:</span>{' '}
                    {job.document_id}
                  </div>

                  <div className="flex items-center space-x-4 text-xs text-gray-600">
                    <div className="flex items-center space-x-1">
                      <span>📍</span>
                      <span>{job.channels.join(', ')}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span>🕐</span>
                      <span>{formatDate(job.created_at)}</span>
                    </div>
                    {job.completed_at && (
                      <div className="flex items-center space-x-1">
                        <span>✓</span>
                        <span>{formatDate(job.completed_at)}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Channel Results Indicator */}
                {job.results && (
                  <div className="flex space-x-1 ml-4">
                    {Object.entries(job.results).map(([channel, result]) => (
                      <div
                        key={channel}
                        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs ${
                          result.status === 'success'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                        title={`${channel}: ${result.status}`}
                      >
                        {result.status === 'success' ? '✓' : '✕'}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Errors */}
              {job.errors && job.errors.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="text-xs text-red-600">
                    <span className="font-medium">Errors:</span>
                    <ul className="list-disc list-inside mt-1">
                      {job.errors.slice(0, 2).map((error, idx) => (
                        <li key={idx}>{error}</li>
                      ))}
                      {job.errors.length > 2 && (
                        <li>+{job.errors.length - 2} more...</li>
                      )}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6 pt-6 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            Page {currentPage} of {totalPages}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1 || loading}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages || loading}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobsList;
