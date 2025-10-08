/**
 * JobStatusCard Component
 * Displays detailed status for a single sync job
 */

import React from 'react';
import type { JobStatusCardProps, JobStatus } from '../types/content-generator';

export const JobStatusCard: React.FC<JobStatusCardProps> = ({
  job,
  onRetry,
  onCancel,
  onViewDetails,
  compact = false,
}) => {
  const getStatusColor = (status: JobStatus) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-100 border-green-200';
      case 'in_progress':
        return 'text-blue-700 bg-blue-100 border-blue-200';
      case 'pending':
        return 'text-yellow-700 bg-yellow-100 border-yellow-200';
      case 'failed':
        return 'text-red-700 bg-red-100 border-red-200';
      case 'partial':
        return 'text-orange-700 bg-orange-100 border-orange-200';
      case 'cancelled':
        return 'text-gray-700 bg-gray-100 border-gray-200';
      default:
        return 'text-gray-700 bg-gray-100 border-gray-200';
    }
  };

  const getStatusIcon = (status: JobStatus) => {
    switch (status) {
      case 'completed':
        return (
          <svg
            className="w-6 h-6 text-green-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'in_progress':
        return (
          <svg
            className="w-6 h-6 text-blue-600 animate-spin"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        );
      case 'pending':
        return (
          <svg
            className="w-6 h-6 text-yellow-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'failed':
        return (
          <svg
            className="w-6 h-6 text-red-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'partial':
        return (
          <svg
            className="w-6 h-6 text-orange-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'cancelled':
        return (
          <svg
            className="w-6 h-6 text-gray-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z"
              clipRule="evenodd"
            />
          </svg>
        );
      default:
        return null;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const calculateDuration = () => {
    if (!job.started_at) return null;
    const start = new Date(job.started_at).getTime();
    const end = job.completed_at
      ? new Date(job.completed_at).getTime()
      : Date.now();
    const durationMs = end - start;
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'email':
        return '📧';
      case 'website':
        return '🌐';
      case 'social_twitter':
        return '🐦';
      case 'social_linkedin':
        return '💼';
      case 'social_facebook':
        return '👥';
      default:
        return '📍';
    }
  };

  if (compact) {
    return (
      <div
        className={`border-2 rounded-lg p-4 ${getStatusColor(job.status)}`}
        onClick={() => onViewDetails?.(job.job_id)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon(job.status)}
            <div>
              <div className="font-semibold text-sm">{job.status.toUpperCase()}</div>
              <div className="text-xs opacity-75">
                {job.channels.map((c) => getChannelIcon(c)).join(' ')}
              </div>
            </div>
          </div>
          <div className="text-xs opacity-75">
            {formatDate(job.created_at).split(',')[0]}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`border-2 rounded-lg p-6 ${getStatusColor(job.status)}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {getStatusIcon(job.status)}
          <div>
            <h3 className="text-xl font-bold">{job.status.toUpperCase()}</h3>
            <p className="text-sm opacity-75 font-mono">Job ID: {job.job_id}</p>
          </div>
        </div>
        {job.correlation_id && (
          <div className="text-xs opacity-75 font-mono bg-white bg-opacity-50 px-2 py-1 rounded">
            {job.correlation_id.substring(0, 8)}
          </div>
        )}
      </div>

      {/* Document Info */}
      <div className="mb-4 p-3 bg-white bg-opacity-50 rounded">
        <div className="text-sm font-medium opacity-75 mb-1">Document</div>
        <div className="font-mono text-sm">{job.document_id}</div>
      </div>

      {/* Channels */}
      <div className="mb-4">
        <div className="text-sm font-medium opacity-75 mb-2">Channels</div>
        <div className="flex flex-wrap gap-2">
          {job.channels.map((channel) => (
            <div
              key={channel}
              className="px-3 py-1 bg-white bg-opacity-50 rounded-full text-sm font-medium flex items-center space-x-1"
            >
              <span>{getChannelIcon(channel)}</span>
              <span>{channel}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Timestamps */}
      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div>
          <div className="font-medium opacity-75">Created</div>
          <div>{formatDate(job.created_at)}</div>
        </div>
        {job.scheduled_for && (
          <div>
            <div className="font-medium opacity-75">Scheduled</div>
            <div>{formatDate(job.scheduled_for)}</div>
          </div>
        )}
        {job.started_at && (
          <div>
            <div className="font-medium opacity-75">Started</div>
            <div>{formatDate(job.started_at)}</div>
          </div>
        )}
        {job.completed_at && (
          <div>
            <div className="font-medium opacity-75">Completed</div>
            <div>{formatDate(job.completed_at)}</div>
          </div>
        )}
      </div>

      {/* Duration */}
      {calculateDuration() && (
        <div className="mb-4 text-sm">
          <div className="font-medium opacity-75">Duration</div>
          <div className="text-lg font-bold">{calculateDuration()}</div>
        </div>
      )}

      {/* Results */}
      {job.results && Object.keys(job.results).length > 0 && (
        <div className="mb-4">
          <div className="text-sm font-medium opacity-75 mb-2">Results</div>
          <div className="space-y-2">
            {Object.entries(job.results).map(([channel, result]) => (
              <div
                key={channel}
                className="flex items-center justify-between p-2 bg-white bg-opacity-50 rounded"
              >
                <div className="flex items-center space-x-2">
                  <span>{getChannelIcon(channel)}</span>
                  <span className="font-medium capitalize">{channel}</span>
                </div>
                <div className="flex items-center space-x-2">
                  {result.status === 'success' ? (
                    <span className="text-green-700 font-semibold">✓ Success</span>
                  ) : (
                    <span className="text-red-700 font-semibold">✕ Failed</span>
                  )}
                  {result.url && (
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs underline hover:no-underline"
                    >
                      View
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Errors */}
      {job.errors && job.errors.length > 0 && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
          <div className="text-sm font-medium text-red-800 mb-2">Errors</div>
          <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
            {job.errors.map((error, idx) => (
              <li key={idx}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Metadata */}
      {job.metadata && Object.keys(job.metadata).length > 0 && (
        <div className="mb-4">
          <div className="text-sm font-medium opacity-75 mb-2">Metadata</div>
          <div className="bg-white bg-opacity-50 rounded p-3 text-xs font-mono overflow-auto max-h-32">
            {JSON.stringify(job.metadata, null, 2)}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex space-x-3 mt-6 pt-4 border-t border-current border-opacity-20">
        {job.status === 'failed' && onRetry && (
          <button
            onClick={() => onRetry(job.job_id)}
            className="flex-1 px-4 py-2 bg-white bg-opacity-90 hover:bg-opacity-100 rounded-lg font-medium transition-colors"
          >
            🔄 Retry
          </button>
        )}
        {(job.status === 'pending' || job.status === 'in_progress') && onCancel && (
          <button
            onClick={() => onCancel(job.job_id)}
            className="flex-1 px-4 py-2 bg-white bg-opacity-90 hover:bg-opacity-100 rounded-lg font-medium transition-colors"
          >
            ⊘ Cancel
          </button>
        )}
        {onViewDetails && (
          <button
            onClick={() => onViewDetails(job.job_id)}
            className="flex-1 px-4 py-2 bg-white bg-opacity-90 hover:bg-opacity-100 rounded-lg font-medium transition-colors"
          >
            👁 Details
          </button>
        )}
      </div>
    </div>
  );
};

export default JobStatusCard;
