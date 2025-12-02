/**
 * Tests for Spatial Store
 *
 * Tests cover:
 * - Initial state
 * - Object management (add, remove, move, update)
 * - Assistant management
 * - Room management
 * - Storage management
 * - UI state
 * - Optimistic updates
 * - Computed selectors
 */

import { act } from '@testing-library/react';
import { useSpatialStore, SpatialObject, Room, StorageItem } from '../spatialStore';

// Mock the api module
jest.mock('../../utils/api', () => ({
  api: {
    moveObject: jest.fn(),
    getObjects: jest.fn(),
    getAssistantState: jest.fn(),
    getStorageItems: jest.fn(),
    setObjectState: jest.fn(),
    moveAssistant: jest.fn(),
    placeFromStorage: jest.fn(),
  },
}));

// Mock coordinateConversion
jest.mock('../../utils/coordinateConversion', () => ({
  gridToPixel: jest.fn((pos, _dims) => ({ x: pos.x * 30, y: pos.y * 30 })),
}));

describe('SpatialStore', () => {
  // Reset store before each test
  beforeEach(() => {
    act(() => {
      useSpatialStore.getState().resetToDefaults();
    });
  });

  // ========================================================================
  // Initial State Tests
  // ========================================================================

  describe('Initial State', () => {
    it('should have correct initial assistant state', () => {
      const state = useSpatialStore.getState();

      expect(state.assistant.id).toBe('assistant');
      expect(state.assistant.position).toEqual({ x: 960, y: 240 });
      expect(state.assistant.isMoving).toBe(false);
      expect(state.assistant.mood).toBe('neutral');
      expect(state.assistant.status).toBe('idle');
    });

    it('should have correct initial UI state', () => {
      const state = useSpatialStore.getState();

      expect(state.ui.currentRoomId).toBe('main-room');
      expect(state.ui.selectedObjectId).toBeNull();
      expect(state.ui.isLoading).toBe(false);
      expect(state.ui.error).toBeNull();
    });

    it('should have default main room', () => {
      const state = useSpatialStore.getState();

      expect(state.entities.rooms['main-room']).toBeDefined();
      expect(state.entities.rooms['main-room'].name).toBe('Main Room');
    });

    it('should have empty objects and storage', () => {
      const state = useSpatialStore.getState();

      expect(Object.keys(state.entities.objects)).toHaveLength(0);
      expect(Object.keys(state.entities.storageItems)).toHaveLength(0);
    });
  });

  // ========================================================================
  // Object Management Tests
  // ========================================================================

  describe('Object Management', () => {
    const testObject: SpatialObject = {
      id: 'test-obj-1',
      type: 'furniture',
      name: 'Test Desk',
      position: { x: 100, y: 100 },
      size: { width: 60, height: 40 },
      solid: true,
      interactive: true,
      movable: false,
      states: { power: 'off' },
      room_id: 'main-room',
    };

    it('should add object to entities and room', () => {
      act(() => {
        useSpatialStore.getState().addObject(testObject);
      });

      const state = useSpatialStore.getState();
      expect(state.entities.objects['test-obj-1']).toEqual(testObject);
      expect(state.entities.rooms['main-room'].objects).toContain('test-obj-1');
    });

    it('should not duplicate object in room', () => {
      act(() => {
        useSpatialStore.getState().addObject(testObject);
        useSpatialStore.getState().addObject(testObject);
      });

      const state = useSpatialStore.getState();
      const count = state.entities.rooms['main-room'].objects.filter(
        (id) => id === 'test-obj-1'
      ).length;
      expect(count).toBe(1);
    });

    it('should remove object from entities and room', () => {
      act(() => {
        useSpatialStore.getState().addObject(testObject);
        useSpatialStore.getState().removeObject('test-obj-1');
      });

      const state = useSpatialStore.getState();
      expect(state.entities.objects['test-obj-1']).toBeUndefined();
      expect(state.entities.rooms['main-room'].objects).not.toContain('test-obj-1');
    });

    it('should set object position', () => {
      act(() => {
        useSpatialStore.getState().addObject(testObject);
        useSpatialStore.getState().setObjectPosition('test-obj-1', { x: 200, y: 150 });
      });

      const state = useSpatialStore.getState();
      expect(state.entities.objects['test-obj-1'].position).toEqual({ x: 200, y: 150 });
    });

    it('should set object states', () => {
      act(() => {
        useSpatialStore.getState().addObject(testObject);
        useSpatialStore.getState().setObjectStates('test-obj-1', { power: 'on', brightness: 50 });
      });

      const state = useSpatialStore.getState();
      expect(state.entities.objects['test-obj-1'].states.power).toBe('on');
      expect(state.entities.objects['test-obj-1'].states.brightness).toBe(50);
    });

    it('should get object by ID', () => {
      act(() => {
        useSpatialStore.getState().addObject(testObject);
      });

      const obj = useSpatialStore.getState().getObjectById('test-obj-1');
      expect(obj).toEqual(testObject);
    });

    it('should return undefined for unknown object ID', () => {
      const obj = useSpatialStore.getState().getObjectById('unknown');
      expect(obj).toBeUndefined();
    });
  });

  // ========================================================================
  // Assistant Management Tests
  // ========================================================================

  describe('Assistant Management', () => {
    it('should set assistant position', () => {
      act(() => {
        useSpatialStore.getState().setAssistantPosition({ x: 500, y: 300 });
      });

      const state = useSpatialStore.getState();
      expect(state.assistant.position).toEqual({ x: 500, y: 300 });
    });

    it('should update assistant status partially', () => {
      act(() => {
        useSpatialStore.getState().setAssistantStatus({
          mood: 'happy',
          status: 'active',
        });
      });

      const state = useSpatialStore.getState();
      expect(state.assistant.mood).toBe('happy');
      expect(state.assistant.status).toBe('active');
      // Other fields should remain unchanged
      expect(state.assistant.facing).toBe('right');
    });

    it('should sync assistant from backend data', () => {
      const backendData = {
        position: { x: 800, y: 200 },
        status: {
          mode: 'active',
          action: 'talking',
          mood: 'curious',
        },
      };

      act(() => {
        useSpatialStore.getState().syncAssistantFromBackend(backendData);
      });

      const state = useSpatialStore.getState();
      expect(state.assistant.status).toBe('active');
      expect(state.assistant.current_action).toBe('talking');
      expect(state.assistant.mood).toBe('curious');
    });
  });

  // ========================================================================
  // Room Management Tests
  // ========================================================================

  describe('Room Management', () => {
    it('should set current room', () => {
      act(() => {
        useSpatialStore.getState().setCurrentRoom('another-room');
      });

      const state = useSpatialStore.getState();
      expect(state.ui.currentRoomId).toBe('another-room');
    });

    it('should add new room', () => {
      const newRoom: Room = {
        id: 'bedroom',
        name: 'Bedroom',
        dimensions: { width: 800, height: 400 },
        objects: [],
      };

      act(() => {
        useSpatialStore.getState().addRoom(newRoom);
      });

      const state = useSpatialStore.getState();
      expect(state.entities.rooms['bedroom']).toEqual(newRoom);
    });

    it('should remove room and update current if needed', () => {
      const newRoom: Room = {
        id: 'temp-room',
        name: 'Temporary Room',
        dimensions: { width: 800, height: 400 },
        objects: [],
      };

      act(() => {
        useSpatialStore.getState().addRoom(newRoom);
        useSpatialStore.getState().setCurrentRoom('temp-room');
        useSpatialStore.getState().removeRoom('temp-room');
      });

      const state = useSpatialStore.getState();
      expect(state.entities.rooms['temp-room']).toBeUndefined();
      // Should fallback to another room
      expect(state.ui.currentRoomId).toBe('main-room');
    });

    it('should get current room', () => {
      const room = useSpatialStore.getState().getCurrentRoom();
      expect(room).not.toBeNull();
      expect(room?.id).toBe('main-room');
    });
  });

  // ========================================================================
  // Storage Management Tests
  // ========================================================================

  describe('Storage Management', () => {
    const testStorageItem: StorageItem = {
      id: 'storage-1',
      name: 'Stored Lamp',
      type: 'decoration',
      size: { width: 30, height: 30 },
      properties: {},
      created_at: new Date().toISOString(),
    };

    it('should add storage item', () => {
      act(() => {
        useSpatialStore.getState().addStorageItem(testStorageItem);
      });

      const state = useSpatialStore.getState();
      expect(state.entities.storageItems['storage-1']).toEqual(testStorageItem);
    });

    it('should remove storage item', () => {
      act(() => {
        useSpatialStore.getState().addStorageItem(testStorageItem);
        useSpatialStore.getState().removeStorageItem('storage-1');
      });

      const state = useSpatialStore.getState();
      expect(state.entities.storageItems['storage-1']).toBeUndefined();
    });

    it('should get storage item by ID', () => {
      act(() => {
        useSpatialStore.getState().addStorageItem(testStorageItem);
      });

      const item = useSpatialStore.getState().getStorageItemById('storage-1');
      expect(item).toEqual(testStorageItem);
    });
  });

  // ========================================================================
  // UI State Tests
  // ========================================================================

  describe('UI State', () => {
    it('should select object', () => {
      act(() => {
        useSpatialStore.getState().selectObject('obj-123');
      });

      const state = useSpatialStore.getState();
      expect(state.ui.selectedObjectId).toBe('obj-123');
    });

    it('should deselect object', () => {
      act(() => {
        useSpatialStore.getState().selectObject('obj-123');
        useSpatialStore.getState().selectObject(null);
      });

      const state = useSpatialStore.getState();
      expect(state.ui.selectedObjectId).toBeNull();
    });

    it('should set dragged object', () => {
      act(() => {
        useSpatialStore.getState().setDraggedObject('obj-456');
      });

      const state = useSpatialStore.getState();
      expect(state.ui.draggedObjectId).toBe('obj-456');
    });

    it('should set view mode and adjust grid size', () => {
      act(() => {
        useSpatialStore.getState().setViewMode('mobile');
      });

      const state = useSpatialStore.getState();
      expect(state.ui.viewMode).toBe('mobile');
      expect(state.ui.gridSize).toEqual({ width: 480, height: 120 });
    });

    it('should set loading state', () => {
      act(() => {
        useSpatialStore.getState().setLoading(true);
      });

      expect(useSpatialStore.getState().ui.isLoading).toBe(true);

      act(() => {
        useSpatialStore.getState().setLoading(false);
      });

      expect(useSpatialStore.getState().ui.isLoading).toBe(false);
    });

    it('should set error state', () => {
      act(() => {
        useSpatialStore.getState().setError('Something went wrong');
      });

      const state = useSpatialStore.getState();
      expect(state.ui.error).toBe('Something went wrong');
    });

    it('should toggle storage visibility', () => {
      const initialState = useSpatialStore.getState().ui.storageVisible;

      act(() => {
        useSpatialStore.getState().toggleStorageVisibility();
      });

      expect(useSpatialStore.getState().ui.storageVisible).toBe(!initialState);
    });

    it('should start storage placement', () => {
      act(() => {
        useSpatialStore.getState().startStoragePlacement('item-1');
      });

      const state = useSpatialStore.getState();
      expect(state.ui.selectedStorageItemId).toBe('item-1');
      expect(state.ui.isStoragePlacementActive).toBe(true);
    });

    it('should clear storage placement', () => {
      act(() => {
        useSpatialStore.getState().startStoragePlacement('item-1');
        useSpatialStore.getState().clearStoragePlacement();
      });

      const state = useSpatialStore.getState();
      expect(state.ui.selectedStorageItemId).toBeNull();
      expect(state.ui.isStoragePlacementActive).toBe(false);
    });
  });

  // ========================================================================
  // Floor Plan Tests
  // ========================================================================

  describe('Floor Plan', () => {
    const testFloorPlan = {
      id: 'fp-1',
      name: 'Test Floor Plan',
      dimensions: { width: 1920, height: 480 },
      rooms: [],
    };

    it('should set current floor plan', () => {
      act(() => {
        useSpatialStore.getState().setCurrentFloorPlan(testFloorPlan as any);
      });

      const state = useSpatialStore.getState();
      expect(state.floorPlan.currentFloorPlan).toEqual(testFloorPlan);
      expect(state.floorPlan.selectedFloorPlanId).toBe('fp-1');
    });

    it('should clear floor plan', () => {
      act(() => {
        useSpatialStore.getState().setCurrentFloorPlan(testFloorPlan as any);
        useSpatialStore.getState().clearFloorPlan();
      });

      const state = useSpatialStore.getState();
      expect(state.floorPlan.currentFloorPlan).toBeNull();
      expect(state.floorPlan.selectedFloorPlanId).toBeNull();
    });
  });

  // ========================================================================
  // Optimistic Update Tests
  // ========================================================================

  describe('Optimistic Updates', () => {
    it('should add pending operation', () => {
      const operation = {
        id: 'op-1',
        type: 'move' as const,
        timestamp: Date.now(),
        rollbackData: { position: { x: 0, y: 0 } },
      };

      act(() => {
        useSpatialStore.getState().addPendingOperation(operation);
      });

      const state = useSpatialStore.getState();
      expect(state.pendingOps['op-1']).toEqual(operation);
    });

    it('should complete pending operation', () => {
      const operation = {
        id: 'op-2',
        type: 'move' as const,
        timestamp: Date.now(),
      };

      act(() => {
        useSpatialStore.getState().addPendingOperation(operation);
        useSpatialStore.getState().completePendingOperation('op-2');
      });

      const state = useSpatialStore.getState();
      expect(state.pendingOps['op-2']).toBeUndefined();
    });

    it('should clear expired operations', () => {
      const oldOperation = {
        id: 'old-op',
        type: 'move' as const,
        timestamp: Date.now() - 15000, // 15 seconds ago (> 10 second max age)
      };

      act(() => {
        useSpatialStore.getState().addPendingOperation(oldOperation);
        useSpatialStore.getState().clearExpiredOperations();
      });

      const state = useSpatialStore.getState();
      expect(state.pendingOps['old-op']).toBeUndefined();
    });
  });

  // ========================================================================
  // Computed Selectors Tests
  // ========================================================================

  describe('Computed Selectors', () => {
    const interactiveObject: SpatialObject = {
      id: 'interactive-1',
      type: 'furniture',
      name: 'Interactive Object',
      position: { x: 100, y: 100 },
      size: { width: 30, height: 30 },
      solid: true,
      interactive: true,
      movable: false,
      states: {},
      room_id: 'main-room',
    };

    const movableObject: SpatialObject = {
      id: 'movable-1',
      type: 'item',
      name: 'Movable Object',
      position: { x: 200, y: 100 },
      size: { width: 20, height: 20 },
      solid: false,
      interactive: false,
      movable: true,
      states: {},
      room_id: 'main-room',
    };

    beforeEach(() => {
      act(() => {
        useSpatialStore.getState().addObject(interactiveObject);
        useSpatialStore.getState().addObject(movableObject);
      });
    });

    it('should get current room objects', () => {
      const objects = useSpatialStore.getState().getCurrentRoomObjects();
      expect(objects.length).toBe(2);
    });

    it('should get interactable objects', () => {
      const interactable = useSpatialStore.getState().getInteractableObjects();
      expect(interactable.length).toBe(1);
      expect(interactable[0].id).toBe('interactive-1');
    });

    it('should get movable objects', () => {
      const movable = useSpatialStore.getState().getMovableObjects();
      expect(movable.length).toBe(1);
      expect(movable[0].id).toBe('movable-1');
    });

    it('should get objects near position', () => {
      const nearby = useSpatialStore.getState().getObjectsNearPosition(
        { x: 110, y: 110 },
        50
      );
      expect(nearby.length).toBe(1);
      expect(nearby[0].id).toBe('interactive-1');
    });

    it('should check if position is occupied', () => {
      const isOccupied = useSpatialStore.getState().isPositionOccupied({ x: 110, y: 110 });
      expect(isOccupied).toBe(true);
    });

    it('should get object at position', () => {
      const obj = useSpatialStore.getState().getObjectAt({ x: 110, y: 110 });
      expect(obj?.id).toBe('interactive-1');
    });
  });

  // ========================================================================
  // Reset Tests
  // ========================================================================

  describe('Reset Functions', () => {
    it('should reset to defaults', () => {
      // Modify state
      act(() => {
        useSpatialStore.getState().setError('Some error');
        useSpatialStore.getState().setLoading(true);
        useSpatialStore.getState().selectObject('obj-1');
      });

      // Reset
      act(() => {
        useSpatialStore.getState().resetToDefaults();
      });

      const state = useSpatialStore.getState();
      expect(state.ui.error).toBeNull();
      expect(state.ui.isLoading).toBe(false);
      expect(state.ui.selectedObjectId).toBeNull();
    });

    it('should clear all data', () => {
      const testObject: SpatialObject = {
        id: 'obj-1',
        type: 'furniture',
        name: 'Test',
        position: { x: 0, y: 0 },
        size: { width: 10, height: 10 },
        solid: true,
        interactive: false,
        movable: false,
        states: {},
        room_id: 'main-room',
      };

      act(() => {
        useSpatialStore.getState().addObject(testObject);
        useSpatialStore.getState().clearAllData();
      });

      const state = useSpatialStore.getState();
      expect(Object.keys(state.entities.objects)).toHaveLength(0);
      expect(state.ui.selectedObjectId).toBeNull();
    });
  });
});
