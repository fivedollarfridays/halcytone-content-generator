/**
 * ContentGenerationForm Component
 * Form for generating and publishing content across channels
 */

import React, { useState, useCallback } from 'react';
import type {
  ContentGenerationFormProps,
  Channel,
  TemplateStyle,
  ContentType,
  SyncJob,
} from '../types/content-generator';
import { ContentGeneratorAPI } from '../lib/api-client';

export const ContentGenerationForm: React.FC<ContentGenerationFormProps> = ({
  apiUrl,
  apiKey,
  onSubmit,
  onError,
  defaultChannels = [],
  defaultTemplate = 'modern',
}) => {
  const [documentId, setDocumentId] = useState('');
  const [channels, setChannels] = useState<Channel[]>(defaultChannels);
  const [contentType, setContentType] = useState<ContentType>('update');
  const [templateStyle, setTemplateStyle] = useState<TemplateStyle>(defaultTemplate);
  const [scheduleTime, setScheduleTime] = useState('');
  const [dryRun, setDryRun] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<SyncJob | null>(null);

  const api = new ContentGeneratorAPI(apiUrl, apiKey);

  const availableChannels: { value: Channel; label: string; icon: string }[] = [
    { value: 'email', label: 'Email Newsletter', icon: '📧' },
    { value: 'website', label: 'Website', icon: '🌐' },
    { value: 'social_twitter', label: 'Twitter/X', icon: '🐦' },
    { value: 'social_linkedin', label: 'LinkedIn', icon: '💼' },
    { value: 'social_facebook', label: 'Facebook', icon: '👥' },
  ];

  const contentTypes: { value: ContentType; label: string }[] = [
    { value: 'update', label: 'Update' },
    { value: 'blog', label: 'Blog Post' },
    { value: 'announcement', label: 'Announcement' },
  ];

  const templateStyles: { value: TemplateStyle; label: string; description: string }[] = [
    { value: 'modern', label: 'Modern', description: 'Clean, contemporary design' },
    { value: 'classic', label: 'Classic', description: 'Traditional, timeless style' },
    { value: 'minimal', label: 'Minimal', description: 'Simple, focused layout' },
  ];

  const toggleChannel = (channel: Channel) => {
    setChannels((prev) =>
      prev.includes(channel)
        ? prev.filter((c) => c !== channel)
        : [...prev, channel]
    );
  };

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);
      setSuccess(null);

      // Validation
      if (!documentId.trim()) {
        setError('Document ID is required');
        return;
      }

      if (channels.length === 0) {
        setError('Select at least one channel');
        return;
      }

      setLoading(true);

      try {
        const request = {
          document_id: documentId.trim(),
          channels,
          content_type: contentType,
          template_style: templateStyle,
          dry_run: dryRun,
          ...(scheduleTime && { schedule_time: scheduleTime }),
        };

        const response = await api.generateContent(request);

        if (response.success && response.data) {
          setSuccess(response.data);
          onSubmit?.(response.data);

          // Reset form on success (optional)
          if (!dryRun) {
            setDocumentId('');
            setScheduleTime('');
          }
        } else {
          const errorMsg = response.error?.message || 'Generation failed';
          setError(errorMsg);
          onError?.(response.error!);
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMsg);
        onError?.({ message: errorMsg });
      } finally {
        setLoading(false);
      }
    },
    [documentId, channels, contentType, templateStyle, scheduleTime, dryRun, api, onSubmit, onError]
  );

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Generate Content</h2>
        <p className="text-sm text-gray-600 mt-1">
          Create and publish content across multiple channels
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Document ID */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Document ID
            <span className="text-red-500 ml-1">*</span>
          </label>
          <input
            type="text"
            value={documentId}
            onChange={(e) => setDocumentId(e.target.value)}
            placeholder="gdocs:1234567890 or notion:abc123"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <p className="text-xs text-gray-500 mt-1">
            Enter Google Docs or Notion document ID
          </p>
        </div>

        {/* Channels */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Channels
            <span className="text-red-500 ml-1">*</span>
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {availableChannels.map((channel) => (
              <button
                key={channel.value}
                type="button"
                onClick={() => toggleChannel(channel.value)}
                disabled={loading}
                className={`px-4 py-3 rounded-lg border-2 transition-all ${
                  channels.includes(channel.value)
                    ? 'border-blue-500 bg-blue-50 text-blue-900'
                    : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <div className="flex items-center space-x-2">
                  <span className="text-xl">{channel.icon}</span>
                  <span className="font-medium">{channel.label}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Content Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Content Type
          </label>
          <div className="flex space-x-4">
            {contentTypes.map((type) => (
              <label key={type.value} className="flex items-center">
                <input
                  type="radio"
                  value={type.value}
                  checked={contentType === type.value}
                  onChange={(e) => setContentType(e.target.value as ContentType)}
                  disabled={loading}
                  className="mr-2"
                />
                <span className="text-sm">{type.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Template Style */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Template Style
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {templateStyles.map((template) => (
              <button
                key={template.value}
                type="button"
                onClick={() => setTemplateStyle(template.value)}
                disabled={loading}
                className={`px-4 py-3 rounded-lg border-2 transition-all text-left ${
                  templateStyle === template.value
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 bg-white hover:border-gray-400'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <div className="font-medium text-gray-900">{template.label}</div>
                <div className="text-xs text-gray-600 mt-1">
                  {template.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Schedule Time */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Schedule Time (Optional)
          </label>
          <input
            type="datetime-local"
            value={scheduleTime}
            onChange={(e) => setScheduleTime(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <p className="text-xs text-gray-500 mt-1">
            Leave empty to publish immediately
          </p>
        </div>

        {/* Dry Run */}
        <div className="flex items-center">
          <input
            type="checkbox"
            id="dryRun"
            checked={dryRun}
            onChange={(e) => setDryRun(e.target.checked)}
            disabled={loading}
            className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="dryRun" className="text-sm text-gray-700">
            Dry run (preview without publishing)
          </label>
        </div>

        {/* Error Display */}
        {error && (
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
              <span className="text-red-800 font-medium">Error</span>
            </div>
            <p className="text-red-700 text-sm mt-2">{error}</p>
          </div>
        )}

        {/* Success Display */}
        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg
                className="w-5 h-5 text-green-600 mr-2"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-green-800 font-medium">
                {dryRun ? 'Preview Generated' : 'Content Submitted'}
              </span>
            </div>
            <div className="text-sm text-green-700 mt-2">
              <p>Job ID: {success.job_id}</p>
              <p>Status: {success.status}</p>
              {success.scheduled_for && (
                <p>Scheduled for: {new Date(success.scheduled_for).toLocaleString()}</p>
              )}
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex space-x-4">
          <button
            type="submit"
            disabled={loading || channels.length === 0 || !documentId.trim()}
            className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
                {dryRun ? 'Generating Preview...' : 'Generating...'}
              </span>
            ) : (
              <span>{dryRun ? 'Generate Preview' : 'Generate & Publish'}</span>
            )}
          </button>
          {success && (
            <button
              type="button"
              onClick={() => setSuccess(null)}
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
            >
              New
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default ContentGenerationForm;
