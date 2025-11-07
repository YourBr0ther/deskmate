/**
 * Floor Plan Selector Component
 *
 * Provides a UI for selecting and activating floor plan templates.
 * Includes template discovery, loading, and activation functionality.
 */

import React, { useState } from 'react';

import { useFloorPlanManager, FloorPlanTemplate, TemplateFile } from '../../hooks/useFloorPlanManager';

interface FloorPlanSelectorProps {
  onFloorPlanSelected: (floorPlan: FloorPlanTemplate) => void;
  onFloorPlanActivated: (floorPlan: FloorPlanTemplate) => void;
  className?: string;
}

const FloorPlanSelector: React.FC<FloorPlanSelectorProps> = ({
  onFloorPlanSelected,
  onFloorPlanActivated,
  className = ''
}) => {
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [showTemplateFiles, setShowTemplateFiles] = useState(false);

  const {
    templates,
    templateFiles,
    activeFloorPlan,
    isLoading,
    error,
    hasTemplates,
    hasTemplateFiles,
    loadAllTemplates,
    loadTemplate,
    activateFloorPlan,
    getTemplatesByCategory,
    refresh
  } = useFloorPlanManager({
    autoLoadTemplates: false,
    onFloorPlanActivated: (floorPlan) => {
      console.log('Floor plan activated:', floorPlan);
      onFloorPlanActivated(floorPlan);
    },
    onLoadError: (errorMsg) => {
      console.error('Floor plan manager error:', errorMsg);
    }
  });

  // Handle template selection
  const handleTemplateSelect = (template: FloorPlanTemplate) => {
    setSelectedTemplate(template.id);
    onFloorPlanSelected(template);
  };

  // Handle template activation
  const handleActivateTemplate = async (templateId: string) => {
    const result = await activateFloorPlan(templateId);
    if (result.success) {
      setSelectedTemplate(templateId);
    }
  };

  // Handle load all templates
  const handleLoadAllTemplates = async () => {
    const result = await loadAllTemplates();
    if (result?.success) {
      console.log(`Loaded ${result.summary.loaded}/${result.summary.total} templates`);
    }
  };

  // Handle load single template
  const handleLoadTemplate = async (templateFile: TemplateFile) => {
    const result = await loadTemplate(templateFile.file_name);
    if (result.success) {
      console.log(`Loaded template: ${result.template_name}`);
      setShowTemplateFiles(false);
    }
  };

  // Get category icon
  const getCategoryIcon = (category: string) => {
    const icons = {
      apartment: '🏠',
      house: '🏡',
      office: '🏢',
      studio: '🏠',
      commercial: '🏪',
      unknown: '📋'
    };
    return icons[category as keyof typeof icons] || icons.unknown;
  };

  // Get template status color
  const getStatusColor = (template: FloorPlanTemplate) => {
    if (template.is_active) return 'bg-green-100 border-green-300 text-green-800';
    if (selectedTemplate === template.id) return 'bg-blue-100 border-blue-300 text-blue-800';
    return 'bg-white border-gray-200 text-gray-800';
  };

  // Template card component
  const TemplateCard = ({ template }: { template: FloorPlanTemplate }) => (
    <div
      className={`
        border rounded-lg p-4 cursor-pointer transition-all duration-200 hover:shadow-md
        ${getStatusColor(template)}
      `}
      onClick={() => handleTemplateSelect(template)}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{getCategoryIcon(template.category)}</span>
          <div>
            <h3 className="font-semibold">{template.name}</h3>
            <p className="text-sm opacity-75">{template.description}</p>
            <div className="text-xs mt-1 space-x-2">
              <span>{template.room_count} rooms</span>
              <span>•</span>
              <span>{template.dimensions.width}×{template.dimensions.height}</span>
              <span>•</span>
              <span className="capitalize">{template.category}</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end space-y-2">
          {template.is_active && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Active
            </span>
          )}

          {!template.is_active && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleActivateTemplate(template.id);
              }}
              disabled={isLoading}
              className="px-3 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Loading...' : 'Activate'}
            </button>
          )}
        </div>
      </div>
    </div>
  );

  // Template file card component
  const TemplateFileCard = ({ templateFile }: { templateFile: TemplateFile }) => (
    <div className="border border-gray-200 rounded-lg p-3 bg-gray-50">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getCategoryIcon(templateFile.category)}</span>
          <div>
            <h4 className="font-medium text-sm">{templateFile.name}</h4>
            <p className="text-xs text-gray-600">{templateFile.description}</p>
            <div className="text-xs text-gray-500 mt-1">
              {templateFile.room_count} rooms • {templateFile.furniture_count} furniture
            </div>
          </div>
        </div>

        <button
          onClick={() => handleLoadTemplate(templateFile)}
          disabled={isLoading}
          className="px-2 py-1 text-xs bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors disabled:opacity-50"
        >
          Load
        </button>
      </div>
    </div>
  );

  const categorizedTemplates = getTemplatesByCategory();

  return (
    <div className={`floor-plan-selector ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Floor Plans</h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={refresh}
            disabled={isLoading}
            className="px-2 py-1 text-xs bg-gray-500 hover:bg-gray-600 text-white rounded transition-colors disabled:opacity-50"
            title="Refresh"
          >
            🔄
          </button>

          {hasTemplateFiles && (
            <button
              onClick={() => setShowTemplateFiles(!showTemplateFiles)}
              className="px-2 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
            >
              {showTemplateFiles ? 'Hide Files' : 'Show Files'}
            </button>
          )}
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <div className="text-sm text-gray-600">Loading floor plans...</div>
        </div>
      )}

      {/* No templates state */}
      {!hasTemplates && !isLoading && (
        <div className="text-center py-8">
          <div className="text-gray-500 mb-4">
            <div className="text-4xl mb-2">📋</div>
            <p>No floor plan templates loaded</p>
          </div>

          {hasTemplateFiles && (
            <div className="space-y-2">
              <p className="text-sm text-gray-600">
                Found {templateFiles.length} template file{templateFiles.length !== 1 ? 's' : ''}
              </p>
              <button
                onClick={handleLoadAllTemplates}
                disabled={isLoading}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors disabled:opacity-50"
              >
                Load All Templates
              </button>
            </div>
          )}
        </div>
      )}

      {/* Template files section */}
      {showTemplateFiles && hasTemplateFiles && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-gray-700">Available Template Files</h3>
            <button
              onClick={handleLoadAllTemplates}
              disabled={isLoading}
              className="px-3 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors disabled:opacity-50"
            >
              Load All
            </button>
          </div>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {templateFiles.map((templateFile) => (
              <TemplateFileCard key={templateFile.file_name} templateFile={templateFile} />
            ))}
          </div>
        </div>
      )}

      {/* Templates by category */}
      {hasTemplates && (
        <div className="space-y-6">
          {Object.entries(categorizedTemplates).map(([category, categoryTemplates]) => (
            <div key={category}>
              <h3 className="font-medium text-gray-700 mb-3 capitalize">
                {getCategoryIcon(category)} {category} ({categoryTemplates.length})
              </h3>
              <div className="space-y-3">
                {categoryTemplates.map((template) => (
                  <TemplateCard key={template.id} template={template} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Active floor plan info */}
      {activeFloorPlan && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            <div className="font-medium">Currently Active:</div>
            <div className="flex items-center space-x-2 mt-1">
              <span>{getCategoryIcon(activeFloorPlan.category)}</span>
              <span>{activeFloorPlan.name}</span>
              <span className="text-gray-400">•</span>
              <span>{activeFloorPlan.room_count} rooms</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FloorPlanSelector;