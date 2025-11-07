/**
 * Hook for managing floor plan templates and activation.
 *
 * Provides functionality for:
 * - Loading and discovering templates
 * - Activating floor plans
 * - Managing template state
 * - Floor plan switching
 */

import { useState, useEffect, useCallback } from 'react';

import { FloorPlan } from '../types/floorPlan';

export interface FloorPlanTemplate {
  id: string;
  name: string;
  description?: string;
  category: string;
  dimensions: {
    width: number;
    height: number;
    scale: number;
    units: string;
  };
  is_active: boolean;
  room_count: number;
  created_by?: string;
  version?: string;
}

export interface TemplateFile {
  file_path: string;
  file_name: string;
  id: string;
  name: string;
  description?: string;
  category: string;
  dimensions: {
    width: number;
    height: number;
    scale?: number;
    units?: string;
  };
  room_count: number;
  furniture_count: number;
  is_template: boolean;
}

export interface LoadResults {
  success: boolean;
  message: string;
  results: Record<string, boolean>;
  summary: {
    total: number;
    loaded: number;
    failed: number;
  };
}

interface UseFloorPlanManagerOptions {
  autoLoadTemplates?: boolean;
  onFloorPlanActivated?: (floorPlan: FloorPlanTemplate) => void;
  onLoadError?: (error: string) => void;
}

export const useFloorPlanManager = (options: UseFloorPlanManagerOptions = {}) => {
  const {
    autoLoadTemplates = false,
    onFloorPlanActivated,
    onLoadError
  } = options;

  // State
  const [templates, setTemplates] = useState<FloorPlanTemplate[]>([]);
  const [templateFiles, setTemplateFiles] = useState<TemplateFile[]>([]);
  const [activeFloorPlan, setActiveFloorPlan] = useState<FloorPlanTemplate | null>(null);
  const [currentFloorPlan, setCurrentFloorPlan] = useState<FloorPlan | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // API Base URL
  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Helper function for API calls
  const apiCall = useCallback(async (endpoint: string, options: RequestInit = {}) => {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }, [API_BASE]);

  // Discover available template files
  const discoverTemplates = useCallback(async () => {
    try {
      setError(null);
      const response = await apiCall('/rooms/templates/discover');
      setTemplateFiles(response.templates || []);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to discover templates';
      setError(errorMessage);
      onLoadError?.(errorMessage);
      return null;
    }
  }, [apiCall, onLoadError]);

  // Load all templates from files to database
  const loadAllTemplates = useCallback(async (): Promise<LoadResults | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiCall('/rooms/templates/load-all', {
        method: 'POST',
      });

      // Refresh templates list after loading
      await refreshTemplates();

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load templates';
      setError(errorMessage);
      onLoadError?.(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [apiCall, onLoadError]);

  // Load single template file
  const loadTemplate = useCallback(async (templateFile: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiCall(`/rooms/templates/load/${encodeURIComponent(templateFile)}`, {
        method: 'POST',
      });

      if (response.success) {
        // Refresh templates list
        await refreshTemplates();
      }

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load template';
      setError(errorMessage);
      onLoadError?.(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  }, [apiCall, onLoadError]);

  // Get all loaded templates
  const refreshTemplates = useCallback(async () => {
    try {
      setError(null);
      const response = await apiCall('/rooms/floor-plans');
      setTemplates(response);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get templates';
      setError(errorMessage);
      return [];
    }
  }, [apiCall]);

  // Get active floor plan
  const refreshActiveFloorPlan = useCallback(async () => {
    try {
      const response = await apiCall('/rooms/floor-plans/active');
      setActiveFloorPlan(response.active_floor_plan);
      return response.active_floor_plan;
    } catch (err) {
      console.error('Error getting active floor plan:', err);
      return null;
    }
  }, [apiCall]);

  // Get detailed floor plan data
  const getFloorPlan = useCallback(async (floorPlanId: string): Promise<FloorPlan | null> => {
    try {
      setError(null);
      const response = await apiCall(`/rooms/floor-plans/${floorPlanId}`);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get floor plan';
      setError(errorMessage);
      return null;
    }
  }, [apiCall]);

  // Activate a floor plan
  const activateFloorPlan = useCallback(async (floorPlanId: string, assistantId: string = 'default') => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiCall(`/rooms/floor-plans/${floorPlanId}/activate?assistant_id=${assistantId}`, {
        method: 'POST',
      });

      if (response.success) {
        // Refresh active floor plan and templates
        await Promise.all([
          refreshActiveFloorPlan(),
          refreshTemplates()
        ]);

        // Get detailed floor plan data
        const detailedFloorPlan = await getFloorPlan(floorPlanId);
        if (detailedFloorPlan) {
          setCurrentFloorPlan(detailedFloorPlan);
        }

        // Find the activated template
        const activatedTemplate = templates.find(t => t.id === floorPlanId);
        if (activatedTemplate) {
          onFloorPlanActivated?.(activatedTemplate);
        }
      }

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to activate floor plan';
      setError(errorMessage);
      onLoadError?.(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  }, [apiCall, refreshActiveFloorPlan, refreshTemplates, getFloorPlan, templates, onFloorPlanActivated, onLoadError]);

  // Validate template data
  const validateTemplate = useCallback(async (templateData: any) => {
    try {
      const response = await apiCall('/rooms/templates/validate', {
        method: 'POST',
        body: JSON.stringify(templateData),
      });
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to validate template';
      setError(errorMessage);
      return { valid: false, errors: [errorMessage] };
    }
  }, [apiCall]);

  // Get templates by category
  const getTemplatesByCategory = useCallback(() => {
    const categorized: Record<string, FloorPlanTemplate[]> = {};

    templates.forEach(template => {
      const category = template.category || 'uncategorized';
      if (!categorized[category]) {
        categorized[category] = [];
      }
      categorized[category].push(template);
    });

    return categorized;
  }, [templates]);

  // Check if templates are loaded
  const hasTemplates = templates.length > 0;
  const hasTemplateFiles = templateFiles.length > 0;

  // Initialize
  useEffect(() => {
    const initialize = async () => {
      // Always discover template files
      await discoverTemplates();

      // Get existing templates
      await refreshTemplates();

      // Get active floor plan
      await refreshActiveFloorPlan();

      // Auto-load templates if enabled and no templates exist
      if (autoLoadTemplates && templates.length === 0 && templateFiles.length > 0) {
        await loadAllTemplates();
      }
    };

    initialize();
  }, []); // Only run on mount

  // Update current floor plan when active changes
  useEffect(() => {
    const updateCurrentFloorPlan = async () => {
      if (activeFloorPlan) {
        const detailed = await getFloorPlan(activeFloorPlan.id);
        if (detailed) {
          setCurrentFloorPlan(detailed);
        }
      } else {
        setCurrentFloorPlan(null);
      }
    };

    updateCurrentFloorPlan();
  }, [activeFloorPlan, getFloorPlan]);

  return {
    // State
    templates,
    templateFiles,
    activeFloorPlan,
    currentFloorPlan,
    isLoading,
    error,

    // Status
    hasTemplates,
    hasTemplateFiles,

    // Actions
    discoverTemplates,
    loadAllTemplates,
    loadTemplate,
    activateFloorPlan,
    refreshTemplates,
    refreshActiveFloorPlan,
    getFloorPlan,
    validateTemplate,

    // Utilities
    getTemplatesByCategory,

    // Manual refresh
    refresh: async () => {
      await Promise.all([
        discoverTemplates(),
        refreshTemplates(),
        refreshActiveFloorPlan()
      ]);
    }
  };
};