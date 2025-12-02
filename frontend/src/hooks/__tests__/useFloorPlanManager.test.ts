/**
 * Tests for Floor Plan Manager Hook
 *
 * Tests cover:
 * - Template discovery
 * - Template loading
 * - Floor plan activation
 * - Error handling
 * - Refresh operations
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useFloorPlanManager } from '../useFloorPlanManager';

// Mock fetch
global.fetch = jest.fn();

const mockTemplates = [
  {
    id: 'studio-apartment',
    name: 'Studio Apartment',
    description: 'A cozy studio apartment',
    category: 'residential',
    dimensions: { width: 1920, height: 480, scale: 30, units: 'px' },
    is_active: true,
    room_count: 1,
  },
  {
    id: 'office-suite',
    name: 'Office Suite',
    description: 'A professional office space',
    category: 'commercial',
    dimensions: { width: 2400, height: 600, scale: 30, units: 'px' },
    is_active: false,
    room_count: 3,
  },
];

const mockTemplateFiles = [
  {
    file_path: '/data/floor-plans/studio.json',
    file_name: 'studio.json',
    id: 'studio-apartment',
    name: 'Studio Apartment',
    category: 'residential',
    dimensions: { width: 1920, height: 480 },
    room_count: 1,
    furniture_count: 10,
    is_template: true,
  },
];

const mockFloorPlan = {
  id: 'studio-apartment',
  name: 'Studio Apartment',
  dimensions: { width: 1920, height: 480, scale: 30 },
  rooms: [
    { id: 'main-room', name: 'Main Room', bounds: { x: 0, y: 0, width: 1920, height: 480 } },
  ],
};

describe('useFloorPlanManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
  });

  describe('Initialization', () => {
    it('should initialize with empty state', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([]),
      });

      const { result } = renderHook(() => useFloorPlanManager());

      expect(result.current.templates).toEqual([]);
      expect(result.current.templateFiles).toEqual([]);
      expect(result.current.activeFloorPlan).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });

    it('should discover templates on mount', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: mockTemplateFiles }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockTemplates),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active_floor_plan: mockTemplates[0] }),
        });

      const { result } = renderHook(() => useFloorPlanManager());

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/rooms/templates/discover'),
          expect.any(Object)
        );
      });
    });
  });

  describe('discoverTemplates', () => {
    it('should discover available template files', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: [] }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active_floor_plan: null }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: mockTemplateFiles }),
        });

      const { result } = renderHook(() => useFloorPlanManager());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.discoverTemplates();
      });

      expect(result.current.templateFiles).toEqual(mockTemplateFiles);
    });

    it('should handle discovery error', async () => {
      const onLoadError = jest.fn();

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: false,
          json: () => Promise.resolve({ detail: 'Discovery failed' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active_floor_plan: null }),
        });

      const { result } = renderHook(() => useFloorPlanManager({ onLoadError }));

      await waitFor(() => {
        expect(result.current.error).toBe('Discovery failed');
      });
    });
  });

  describe('loadAllTemplates', () => {
    it('should load all templates from files', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: [] }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active_floor_plan: null }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              message: 'Loaded 2 templates',
              results: { studio: true, office: true },
              summary: { total: 2, loaded: 2, failed: 0 },
            }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockTemplates),
        });

      const { result } = renderHook(() => useFloorPlanManager());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let loadResult: any;
      await act(async () => {
        loadResult = await result.current.loadAllTemplates();
      });

      expect(loadResult).toEqual(
        expect.objectContaining({
          success: true,
          summary: { total: 2, loaded: 2, failed: 0 },
        })
      );
    });
  });

  describe('activateFloorPlan', () => {
    it('should activate a floor plan', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: [] }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockTemplates),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active_floor_plan: null }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active_floor_plan: mockTemplates[0] }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockTemplates),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockFloorPlan),
        });

      const onFloorPlanActivated = jest.fn();
      const { result } = renderHook(() =>
        useFloorPlanManager({ onFloorPlanActivated })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.activateFloorPlan('studio-apartment');
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/rooms/floor-plans/studio-apartment/activate'),
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('should handle activation error', async () => {
      const onLoadError = jest.fn();

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: [] }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active_floor_plan: null }),
        })
        .mockResolvedValueOnce({
          ok: false,
          json: () => Promise.resolve({ detail: 'Activation failed' }),
        });

      const { result } = renderHook(() => useFloorPlanManager({ onLoadError }));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let activationResult: any;
      await act(async () => {
        activationResult = await result.current.activateFloorPlan('invalid-id');
      });

      expect(activationResult.success).toBe(false);
      expect(result.current.error).toBe('Activation failed');
      expect(onLoadError).toHaveBeenCalled();
    });
  });

  describe('getTemplatesByCategory', () => {
    it('should group templates by category', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: [] }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockTemplates),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active_floor_plan: null }),
        });

      const { result } = renderHook(() => useFloorPlanManager());

      await waitFor(() => {
        expect(result.current.templates.length).toBeGreaterThan(0);
      });

      const categorized = result.current.getTemplatesByCategory();

      expect(categorized.residential).toBeDefined();
      expect(categorized.commercial).toBeDefined();
      expect(categorized.residential.length).toBe(1);
      expect(categorized.commercial.length).toBe(1);
    });
  });

  describe('Status Flags', () => {
    it('should track hasTemplates correctly', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: [] }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockTemplates),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active_floor_plan: null }),
        });

      const { result } = renderHook(() => useFloorPlanManager());

      await waitFor(() => {
        expect(result.current.hasTemplates).toBe(true);
      });
    });

    it('should track hasTemplateFiles correctly', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: mockTemplateFiles }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active_floor_plan: null }),
        });

      const { result } = renderHook(() => useFloorPlanManager());

      await waitFor(() => {
        expect(result.current.hasTemplateFiles).toBe(true);
      });
    });
  });

  describe('validateTemplate', () => {
    it('should validate template data', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: [] }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active_floor_plan: null }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ valid: true, errors: [] }),
        });

      const { result } = renderHook(() => useFloorPlanManager());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let validationResult: any;
      await act(async () => {
        validationResult = await result.current.validateTemplate({ name: 'Test' });
      });

      expect(validationResult.valid).toBe(true);
    });
  });
});
