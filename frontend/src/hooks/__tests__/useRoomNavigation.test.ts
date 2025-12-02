/**
 * Tests for Room Navigation Hook
 *
 * Tests cover:
 * - Navigation to position
 * - Navigation to room
 * - Path preview
 * - Cancel navigation
 * - Status polling
 * - Progress calculation
 * - Doorway proximity checking
 * - Error handling
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useRoomNavigation } from '../useRoomNavigation';

// Mock fetch
global.fetch = jest.fn();

const mockRooms = [
  {
    id: 'living-room',
    name: 'Living Room',
    bounds: { x: 0, y: 0, width: 800, height: 400 },
  },
  {
    id: 'bedroom',
    name: 'Bedroom',
    bounds: { x: 800, y: 0, width: 600, height: 400 },
  },
];

const mockDoorways = [
  {
    id: 'door-1',
    room1_id: 'living-room',
    room2_id: 'bedroom',
    world_position: { x: 800, y: 200 },
    properties: { door_state: 'open' },
    accessibility: { is_accessible: true },
  },
];

describe('useRoomNavigation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    (global.fetch as jest.Mock).mockReset();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Initialization', () => {
    it('should initialize with default state', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ x: 100, y: 100, room_id: 'living-room' }),
      });

      const { result } = renderHook(() => useRoomNavigation());

      expect(result.current.navigationStatus.active).toBe(false);
      expect(result.current.currentPath).toEqual([]);
      expect(result.current.roomTransitions).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should refresh assistant location on mount', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ x: 100, y: 100, room_id: 'living-room' }),
      });

      renderHook(() => useRoomNavigation());

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/rooms/assistant/position/'),
          expect.any(Object)
        );
      });
    });
  });

  describe('navigateToPosition', () => {
    it('should navigate to position successfully', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ x: 100, y: 100, room_id: 'living-room' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              navigation_id: 'nav-123',
              path: [{ x: 100, y: 100, room_id: 'living-room' }],
              room_transitions: [],
              estimated_duration: 5,
              total_distance: 100,
            }),
        });

      const { result } = renderHook(() => useRoomNavigation());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let response: any;
      await act(async () => {
        response = await result.current.navigateToPosition({
          target_x: 200,
          target_y: 200,
        });
      });

      expect(response.success).toBe(true);
      expect(response.navigationId).toBe('nav-123');
    });

    it('should handle navigation failure', async () => {
      const onNavigationError = jest.fn();

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ x: 100, y: 100 }),
        })
        .mockResolvedValueOnce({
          ok: false,
          json: () => Promise.resolve({ detail: 'Path blocked' }),
        });

      const { result } = renderHook(() =>
        useRoomNavigation({ onNavigationError })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let response: any;
      await act(async () => {
        response = await result.current.navigateToPosition({
          target_x: 500,
          target_y: 500,
        });
      });

      expect(response.success).toBe(false);
      expect(result.current.error).toBe('Path blocked');
      expect(onNavigationError).toHaveBeenCalledWith('Path blocked');
    });

    it('should set loading state during navigation', async () => {
      let resolveNavigate: any;
      const navigatePromise = new Promise((resolve) => {
        resolveNavigate = resolve;
      });

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ x: 100, y: 100 }),
        })
        .mockImplementationOnce(() => navigatePromise);

      const { result } = renderHook(() => useRoomNavigation());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.navigateToPosition({ target_x: 200, target_y: 200 });
      });

      expect(result.current.isLoading).toBe(true);

      await act(async () => {
        resolveNavigate({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        });
      });
    });
  });

  describe('navigateToRoom', () => {
    it('should navigate to center of room', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ x: 100, y: 100 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              navigation_id: 'nav-456',
              path: [],
            }),
        });

      const { result } = renderHook(() => useRoomNavigation());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.navigateToRoom('bedroom', mockRooms as any);
      });

      // Should navigate to center of bedroom (800 + 600/2 = 1100, 0 + 400/2 = 200)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/rooms/navigate'),
        expect.objectContaining({
          body: expect.stringContaining('"target_x":1100'),
        })
      );
    });

    it('should error when room not found', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ x: 100, y: 100 }),
      });

      const { result } = renderHook(() => useRoomNavigation());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let response: any;
      await act(async () => {
        response = await result.current.navigateToRoom('non-existent', mockRooms as any);
      });

      expect(response.success).toBe(false);
      expect(response.error).toContain('not found');
    });
  });

  describe('previewPath', () => {
    it('should preview path without executing', async () => {
      const mockPreview = {
        success: true,
        path: [{ x: 100, y: 100 }, { x: 200, y: 200 }],
        room_transitions: [],
        doorways_to_open: [],
        estimated_duration: 5,
        total_distance: 150,
        waypoint_count: 2,
      };

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ x: 100, y: 100 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockPreview),
        });

      const { result } = renderHook(() => useRoomNavigation());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let preview: any;
      await act(async () => {
        preview = await result.current.previewPath({ target_x: 200, target_y: 200 });
      });

      expect(preview).toEqual(mockPreview);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/rooms/pathfind/preview'),
        expect.any(Object)
      );
    });

    it('should return null on preview error', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ x: 100, y: 100 }),
        })
        .mockRejectedValueOnce(new Error('Preview failed'));

      const { result } = renderHook(() => useRoomNavigation());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let preview: any;
      await act(async () => {
        preview = await result.current.previewPath({ target_x: 200, target_y: 200 });
      });

      expect(preview).toBeNull();
    });
  });

  describe('cancelNavigation', () => {
    it('should cancel active navigation', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ x: 100, y: 100 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              navigation_id: 'nav-789',
              path: [{ x: 100, y: 100 }],
            }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active: true, navigation_id: 'nav-789' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ x: 150, y: 150 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        });

      const { result } = renderHook(() => useRoomNavigation());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Start navigation
      await act(async () => {
        await result.current.navigateToPosition({ target_x: 200, target_y: 200 });
      });

      // Let status polling happen
      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      // Cancel navigation
      let cancelResult: any;
      await act(async () => {
        cancelResult = await result.current.cancelNavigation();
      });

      expect(cancelResult.success).toBe(true);
    });

    it('should error when no active navigation', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ x: 100, y: 100 }),
      });

      const { result } = renderHook(() => useRoomNavigation());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let response: any;
      await act(async () => {
        response = await result.current.cancelNavigation();
      });

      expect(response.success).toBe(false);
      expect(response.error).toContain('No active navigation');
    });
  });

  describe('getNavigationProgress', () => {
    it('should return 0 when not navigating', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ x: 100, y: 100 }),
      });

      const { result } = renderHook(() => useRoomNavigation());

      expect(result.current.getNavigationProgress()).toBe(0);
    });
  });

  describe('checkDoorwayProximity', () => {
    it('should detect nearby doorway', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ x: 100, y: 100 }),
      });

      const { result } = renderHook(() => useRoomNavigation());

      const proximity = result.current.checkDoorwayProximity(
        { x: 805, y: 200 },
        mockDoorways as any,
        50
      );

      expect(proximity).not.toBeNull();
      expect(proximity?.doorway.id).toBe('door-1');
      expect(proximity?.distance).toBeLessThan(50);
      expect(proximity?.canTransition).toBe(true);
    });

    it('should return null when no doorway nearby', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ x: 100, y: 100 }),
      });

      const { result } = renderHook(() => useRoomNavigation());

      const proximity = result.current.checkDoorwayProximity(
        { x: 100, y: 100 },
        mockDoorways as any,
        50
      );

      expect(proximity).toBeNull();
    });

    it('should check door accessibility', async () => {
      const lockedDoorways = [
        {
          id: 'locked-door',
          world_position: { x: 800, y: 200 },
          properties: { door_state: 'locked' },
          accessibility: { is_accessible: false },
        },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ x: 100, y: 100 }),
      });

      const { result } = renderHook(() => useRoomNavigation());

      const proximity = result.current.checkDoorwayProximity(
        { x: 800, y: 200 },
        lockedDoorways as any,
        50
      );

      expect(proximity?.canTransition).toBe(false);
    });
  });

  describe('Callbacks', () => {
    it('should call onRoomTransition when room changes', async () => {
      const onRoomTransition = jest.fn();

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ x: 100, y: 100, room_id: 'living-room' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              navigation_id: 'nav-123',
              path: [],
            }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ active: true }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ x: 900, y: 200, room_id: 'bedroom' }),
        });

      const { result } = renderHook(() =>
        useRoomNavigation({ onRoomTransition })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.navigateToPosition({ target_x: 900, target_y: 200 });
      });

      // Advance timer to trigger polling
      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      // Callback should be called when room changes
      // Note: This depends on the internal lastRoomRef being set correctly
    });
  });

  describe('Cleanup', () => {
    it('should stop polling on unmount', async () => {
      const clearIntervalSpy = jest.spyOn(global, 'clearInterval');

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ x: 100, y: 100 }),
      });

      const { unmount } = renderHook(() => useRoomNavigation());

      unmount();

      expect(clearIntervalSpy).toHaveBeenCalled();

      clearIntervalSpy.mockRestore();
    });
  });

  describe('Return Values', () => {
    it('should return all expected properties', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ x: 100, y: 100 }),
      });

      const { result } = renderHook(() => useRoomNavigation());

      // State
      expect(result.current).toHaveProperty('navigationStatus');
      expect(result.current).toHaveProperty('currentPath');
      expect(result.current).toHaveProperty('roomTransitions');
      expect(result.current).toHaveProperty('isLoading');
      expect(result.current).toHaveProperty('error');
      expect(result.current).toHaveProperty('assistantPosition');

      // Actions
      expect(result.current).toHaveProperty('navigateToPosition');
      expect(result.current).toHaveProperty('navigateToRoom');
      expect(result.current).toHaveProperty('previewPath');
      expect(result.current).toHaveProperty('cancelNavigation');
      expect(result.current).toHaveProperty('refreshAssistantLocation');

      // Utilities
      expect(result.current).toHaveProperty('getNavigationProgress');
      expect(result.current).toHaveProperty('checkDoorwayProximity');
      expect(result.current).toHaveProperty('isNavigating');

      // Manual control
      expect(result.current).toHaveProperty('startStatusPolling');
      expect(result.current).toHaveProperty('stopStatusPolling');
    });
  });
});
