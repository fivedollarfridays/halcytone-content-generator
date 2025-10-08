/**
 * TemplateSelector Component
 * Template picker with preview and filtering
 */

import React, { useState } from 'react';
import type {
  TemplateSelectorProps,
  Template,
  Channel,
} from '../types/content-generator';

export const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  templates,
  selectedTemplate,
  onChange,
  showPreview = true,
  channelFilter,
}) => {
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);

  // Filter templates by channel compatibility
  const filteredTemplates = channelFilter
    ? templates.filter((template) =>
        channelFilter.some((channel) => template.supported_channels.includes(channel))
      )
    : templates;

  const getStyleIcon = (style: string) => {
    switch (style) {
      case 'modern':
        return '✨';
      case 'classic':
        return '📜';
      case 'minimal':
        return '⚪';
      default:
        return '📄';
    }
  };

  const getChannelIcon = (channel: Channel) => {
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

  const handleTemplateClick = (template: Template) => {
    onChange(template);
    if (showPreview) {
      setPreviewTemplate(template);
    }
  };

  const closePreview = () => {
    setPreviewTemplate(null);
  };

  return (
    <div className="space-y-4">
      {/* Template Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTemplates.map((template) => (
          <div
            key={template.id}
            onClick={() => handleTemplateClick(template)}
            className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
              selectedTemplate?.id === template.id
                ? 'border-blue-500 bg-blue-50 shadow-md'
                : 'border-gray-300 bg-white hover:border-gray-400 hover:shadow'
            }`}
          >
            {/* Template Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">{getStyleIcon(template.style)}</span>
                <div>
                  <h3 className="font-bold text-gray-900">{template.name}</h3>
                  <span className="text-xs text-gray-600 capitalize">
                    {template.style}
                  </span>
                </div>
              </div>
              {selectedTemplate?.id === template.id && (
                <svg
                  className="w-6 h-6 text-blue-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </div>

            {/* Description */}
            <p className="text-sm text-gray-700 mb-3 min-h-[40px]">
              {template.description}
            </p>

            {/* Supported Channels */}
            <div className="mb-3">
              <div className="text-xs text-gray-600 mb-1">Supported Channels</div>
              <div className="flex flex-wrap gap-1">
                {template.supported_channels.map((channel) => (
                  <span
                    key={channel}
                    className="text-lg"
                    title={channel}
                  >
                    {getChannelIcon(channel)}
                  </span>
                ))}
              </div>
            </div>

            {/* Variables Indicator */}
            {template.variables && template.variables.length > 0 && (
              <div className="text-xs text-gray-600">
                {template.variables.length} variable
                {template.variables.length !== 1 ? 's' : ''}
              </div>
            )}

            {/* Preview Link */}
            {template.preview_url && showPreview && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setPreviewTemplate(template);
                }}
                className="mt-3 w-full px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-sm font-medium transition-colors"
              >
                👁 Preview
              </button>
            )}
          </div>
        ))}
      </div>

      {/* No Results */}
      {filteredTemplates.length === 0 && (
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
          <p className="text-lg font-medium">No templates found</p>
          <p className="text-sm mt-1">
            {channelFilter
              ? 'No templates support the selected channels'
              : 'No templates available'}
          </p>
        </div>
      )}

      {/* Preview Modal */}
      {previewTemplate && showPreview && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={closePreview}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-3xl">{getStyleIcon(previewTemplate.style)}</span>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {previewTemplate.name}
                  </h2>
                  <p className="text-sm text-gray-600">{previewTemplate.description}</p>
                </div>
              </div>
              <button
                onClick={closePreview}
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Template Info */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    Style
                  </h3>
                  <div className="text-lg capitalize">{previewTemplate.style}</div>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    Template ID
                  </h3>
                  <div className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                    {previewTemplate.id}
                  </div>
                </div>
              </div>

              {/* Supported Channels */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  Supported Channels
                </h3>
                <div className="flex flex-wrap gap-2">
                  {previewTemplate.supported_channels.map((channel) => (
                    <div
                      key={channel}
                      className="px-3 py-2 bg-blue-50 text-blue-900 rounded-lg text-sm font-medium flex items-center space-x-2"
                    >
                      <span>{getChannelIcon(channel)}</span>
                      <span>{channel}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Variables */}
              {previewTemplate.variables && previewTemplate.variables.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    Template Variables
                  </h3>
                  <div className="space-y-2">
                    {previewTemplate.variables.map((variable) => (
                      <div
                        key={variable.name}
                        className="border border-gray-200 rounded-lg p-3"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-mono text-sm font-bold">
                            {variable.name}
                          </span>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                              {variable.type}
                            </span>
                            {variable.required && (
                              <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded font-semibold">
                                Required
                              </span>
                            )}
                          </div>
                        </div>
                        {variable.description && (
                          <p className="text-sm text-gray-600 mb-1">
                            {variable.description}
                          </p>
                        )}
                        {variable.default_value !== undefined && (
                          <div className="text-xs text-gray-500">
                            Default: {JSON.stringify(variable.default_value)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Preview Image */}
              {previewTemplate.preview_url && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    Template Preview
                  </h3>
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <img
                      src={previewTemplate.preview_url}
                      alt={`${previewTemplate.name} preview`}
                      className="w-full h-auto"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                        e.currentTarget.parentElement!.innerHTML =
                          '<div class="p-8 text-center text-gray-500">Preview not available</div>';
                      }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-white border-t border-gray-200 p-6 flex justify-end space-x-3">
              <button
                onClick={closePreview}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
              >
                Close
              </button>
              <button
                onClick={() => {
                  onChange(previewTemplate);
                  closePreview();
                }}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Select Template
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateSelector;
