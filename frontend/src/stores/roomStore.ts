/**
 * Zustand store for room state management
 */

import { create } from 'zustand';

import { RoomState, GridObject, Assistant, Position, GridMap, StorageItem } from '../types/room';
import { api } from '../utils/api';
import {
  ROOM_WIDTH,
  ROOM_HEIGHT,
  distance,
  canInteract,
  isWithinBounds,
  clampToRoom,
  LegacyGridConverter
} from '../utils/coordinateSystem';
import { StoreErrorState, createInitialErrorState, withErrorHandling } from '../utils/storeErrorHandler';

interface RoomStore extends RoomState, StoreErrorState {
  // Actions
  setAssistantPosition: (position: Position) => void;
  moveAssistant: (targetPosition: Position) => void;
  setAssistantAction: (action: string | undefined) => void;
  setAssistantMood: (mood: Assistant['mood']) => void;
  setAssistantStatus: (status: Assistant['status']) => void;
  addObject: (object: GridObject) => void;
  removeObject: (objectId: string) => void;
  updateObject: (objectId: string, updates: Partial<GridObject>) => void;
  selectObject: (objectId?: string) => void;
  setViewMode: (mode: 'mobile' | 'desktop') => void;

  // Drag and Drop
  draggedObject: string | null;
  setDraggedObject: (objectId: string | null) => void;
  moveObjectToPosition: (objectId: string, position: Position) => Promise<boolean>;

  // API Actions
  loadObjectsFromAPI: () => Promise<void>;
  setObjects: (objects: GridObject[]) => void;

  // State Management
  setObjectState: (objectId: string, key: string, value: string) => Promise<boolean>;
  getObjectStates: (objectId: string) => Promise<Record<string, string> | null>;

  // Assistant Management
  loadAssistantFromAPI: () => Promise<void>;
  moveAssistantToPosition: (x: number, y: number) => Promise<boolean>;
  sitOnFurniture: (furnitureId: string) => Promise<boolean>;

  // Storage Management
  toggleStorageVisibility: () => void;
  loadStorageItems: () => Promise<void>;
  addToStorage: (itemData: Partial<StorageItem>) => Promise<boolean>;
  placeFromStorage: (itemId: string, position: Position) => Promise<boolean>;
  moveObjectToStorage: (objectId: string) => Promise<boolean>;

  // Storage Placement State
  selectedStorageItemId: string | null;
  isStoragePlacementActive: boolean;
  startStoragePlacement: (itemId: string) => void;
  clearStoragePlacement: () => void;

  // Error handling
  clearError: () => void;

  // Computed values
  getGridMap: () => GridMap;
  getGridDimensions: () => { width: number; height: number };
  isPositionOccupied: (position: Position) => boolean;
  getObjectAt: (position: Position) => GridObject | undefined;
}

// Room dimensions in pixels (unified coordinate system)
const ROOM_PIXEL_WIDTH = ROOM_WIDTH;   // 1920 pixels
const ROOM_PIXEL_HEIGHT = ROOM_HEIGHT; // 480 pixels

// Legacy grid constants (for backward compatibility only)
const LEGACY_GRID_WIDTH = 64;
const LEGACY_GRID_HEIGHT = 16;
const CELL_SIZE = 30;  // pixels per cell

// Mobile scaled dimensions (for responsive design)
const MOBILE_SCALE_FACTOR = 0.25; // Mobile shows 1/4 scale
const MOBILE_WIDTH = ROOM_PIXEL_WIDTH * MOBILE_SCALE_FACTOR;
const MOBILE_HEIGHT = ROOM_PIXEL_HEIGHT * MOBILE_SCALE_FACTOR;

// Initial room objects (basic furniture) - now using pixel coordinates
const initialObjects: GridObject[] = [
  {
    id: 'bed',
    type: 'furniture',
    name: 'Bed',
    position: { x: 1500, y: 360 }, // Converted from grid (50, 12)
    size: { width: 240, height: 120 }, // Converted from grid (8, 4)
    solid: true,
    interactive: true,
    movable: false,
    states: { made: true }
  },
  {
    id: 'desk',
    type: 'furniture',
    name: 'Desk',
    position: { x: 300, y: 60 }, // Converted from grid (10, 2)
    size: { width: 180, height: 90 }, // Converted from grid (6, 3)
    solid: true,
    interactive: true,
    movable: false,
    states: { cluttered: false }
  },
  {
    id: 'window',
    type: 'furniture',
    name: 'Window',
    position: { x: 900, y: 0 }, // Converted from grid (30, 0)
    size: { width: 240, height: 30 }, // Converted from grid (8, 1)
    solid: false,
    interactive: true,
    movable: false,
    states: { open: false, curtains: 'closed' }
  },
  {
    id: 'door',
    type: 'furniture',
    name: 'Door',
    position: { x: 0, y: 240 }, // Converted from grid (0, 8)
    size: { width: 30, height: 90 }, // Converted from grid (1, 3)
    solid: false,
    interactive: true,
    movable: false,
    states: { open: false, locked: false }
  }
];

// Initial assistant state - now using pixel coordinates
const initialAssistant: Assistant = {
  id: 'assistant',
  position: { x: ROOM_PIXEL_WIDTH / 2, y: ROOM_PIXEL_HEIGHT / 2 }, // Center of room (960, 240)
  isMoving: false,
  mood: 'neutral',
  status: 'idle',
  sitting_on_object_id: null,
  holding_object_id: null
};

export const useRoomStore = create<RoomStore>((set, get) => ({
  // Initial state - now using pixel-based dimensions
  gridSize: { width: ROOM_PIXEL_WIDTH, height: ROOM_PIXEL_HEIGHT },
  cellSize: { width: 1, height: 1 }, // No longer applicable with pixel coordinates
  objects: initialObjects,
  assistant: initialAssistant,
  selectedObject: undefined,
  viewMode: 'desktop',
  draggedObject: null,
  storageItems: [],
  storageVisible: false,

  // Storage placement state
  selectedStorageItemId: null,
  isStoragePlacementActive: false,

  // Error handling state
  ...createInitialErrorState(),

  // Clear error
  clearError: () => set({ error: null, lastErrorTimestamp: null }),

  // Assistant actions
  setAssistantPosition: (position) =>
    set((state) => ({
      assistant: { ...state.assistant, position, isMoving: false }
    })),

  moveAssistant: (targetPosition) =>
    set((state) => ({
      assistant: {
        ...state.assistant,
        targetPosition,
        isMoving: true
      }
    })),

  setAssistantAction: (currentAction) =>
    set((state) => ({
      assistant: { ...state.assistant, currentAction }
    })),

  setAssistantMood: (mood) =>
    set((state) => ({
      assistant: { ...state.assistant, mood }
    })),

  setAssistantStatus: (status) =>
    set((state) => ({
      assistant: { ...state.assistant, status }
    })),

  // Object management
  addObject: (object) =>
    set((state) => ({
      objects: [...state.objects, object]
    })),

  removeObject: (objectId) =>
    set((state) => ({
      objects: state.objects.filter((obj) => obj.id !== objectId),
      selectedObject: state.selectedObject === objectId ? undefined : state.selectedObject
    })),

  updateObject: (objectId, updates) =>
    set((state) => ({
      objects: state.objects.map((obj) =>
        obj.id === objectId ? { ...obj, ...updates } : obj
      )
    })),

  selectObject: (objectId) =>
    set({ selectedObject: objectId }),

  setViewMode: (mode) =>
    set((state) => ({
      viewMode: mode,
      gridSize: mode === 'mobile'
        ? { width: MOBILE_WIDTH, height: MOBILE_HEIGHT }
        : { width: ROOM_PIXEL_WIDTH, height: ROOM_PIXEL_HEIGHT }
    })),

  // Drag and Drop Actions
  setDraggedObject: (objectId) =>
    set({ draggedObject: objectId }),

  moveObjectToPosition: async (objectId, position) => {
    return withErrorHandling(
      async () => {
        const result = await api.moveObject(objectId, position);

        if (result.success) {
          // Update local state
          const { objects } = get();
          const updatedObjects = objects.map(obj =>
            obj.id === objectId ? { ...obj, position } : obj
          );
          set({ objects: updatedObjects });
          return true;
        } else {
          throw new Error(result.error || 'Failed to move object');
        }
      },
      {
        storeName: 'roomStore',
        operation: 'moveObjectToPosition',
        setState: (update) => set(update),
        onSuccess: () => true,
        onError: () => false,
      }
    ).then(result => result || false);
  },

  // API Actions
  setObjects: (objects) =>
    set({ objects }),

  loadObjectsFromAPI: async () => {
    await withErrorHandling(
      async () => {
        const result = await api.getObjects();

        if (result.success) {
          const apiObjects = result.data;

          // Convert API objects to frontend format
          const frontendObjects: GridObject[] = apiObjects.map((obj: any) => ({
            id: obj.id,
            type: obj.type,
            name: obj.name,
            position: obj.position,
            size: obj.size,
            solid: obj.properties.solid,
            interactive: obj.properties.interactive,
            movable: obj.properties.movable,
            states: obj.states || {}
          }));

          set({ objects: frontendObjects });
          return frontendObjects;
        } else {
          throw new Error(result.error || 'Failed to load objects');
        }
      },
      {
        storeName: 'roomStore',
        operation: 'loadObjectsFromAPI',
        setState: (update) => set(update),
      }
    );
  },

  // Computed values - updated for pixel coordinates
  getGridMap: () => {
    const { objects, assistant, viewMode } = get();

    // For backward compatibility, create a logical grid overlay on pixel coordinates
    const logicalGridWidth = viewMode === 'mobile' ? 32 : LEGACY_GRID_WIDTH;
    const logicalGridHeight = viewMode === 'mobile' ? 8 : LEGACY_GRID_HEIGHT;
    const cellSizeX = ROOM_PIXEL_WIDTH / logicalGridWidth;
    const cellSizeY = ROOM_PIXEL_HEIGHT / logicalGridHeight;

    // Initialize empty grid
    const grid: GridMap = Array(logicalGridHeight).fill(null).map((_, y) =>
      Array(logicalGridWidth).fill(null).map((_, x) => ({
        x,
        y,
        occupied: false,
        walkable: true
      }))
    );

    // Mark object positions - convert pixel positions to logical grid
    objects.forEach((obj) => {
      const gridStartX = Math.floor(obj.position.x / cellSizeX);
      const gridStartY = Math.floor(obj.position.y / cellSizeY);
      const gridEndX = Math.ceil((obj.position.x + obj.size.width) / cellSizeX);
      const gridEndY = Math.ceil((obj.position.y + obj.size.height) / cellSizeY);

      for (let y = gridStartY; y < gridEndY && y < logicalGridHeight; y++) {
        for (let x = gridStartX; x < gridEndX && x < logicalGridWidth; x++) {
          if (x >= 0 && y >= 0) {
            grid[y][x].occupied = true;
            grid[y][x].objectId = obj.id;
            grid[y][x].walkable = !obj.solid;
          }
        }
      }
    });

    // Mark assistant position - convert pixel position to logical grid
    const assistantGridX = Math.floor(assistant.position.x / cellSizeX);
    const assistantGridY = Math.floor(assistant.position.y / cellSizeY);

    if (assistantGridX >= 0 && assistantGridX < logicalGridWidth &&
        assistantGridY >= 0 && assistantGridY < logicalGridHeight) {
      grid[assistantGridY][assistantGridX].occupied = true;
      grid[assistantGridY][assistantGridX].objectId = assistant.id;
      grid[assistantGridY][assistantGridX].walkable = false;
    }

    return grid;
  },

  getGridDimensions: () => {
    const { viewMode } = get();
    return viewMode === 'mobile'
      ? { width: MOBILE_WIDTH, height: MOBILE_HEIGHT }
      : { width: ROOM_PIXEL_WIDTH, height: ROOM_PIXEL_HEIGHT };
  },

  isPositionOccupied: (position) => {
    const { objects, assistant } = get();

    // Check assistant position - using pixel-based collision detection
    const assistantSize = 30; // Assistant size in pixels
    const assistantRect = {
      x: assistant.position.x,
      y: assistant.position.y,
      width: assistantSize,
      height: assistantSize
    };

    const pointRect = {
      x: position.x,
      y: position.y,
      width: 1,
      height: 1
    };

    // Check collision with assistant
    if (assistantRect.x < pointRect.x + pointRect.width &&
        assistantRect.x + assistantRect.width > pointRect.x &&
        assistantRect.y < pointRect.y + pointRect.height &&
        assistantRect.y + assistantRect.height > pointRect.y) {
      return true;
    }

    // Check objects using pixel-based collision detection
    return objects.some((obj) => {
      if (!obj.solid) return false;

      return (obj.position.x < position.x + 1 &&
              obj.position.x + obj.size.width > position.x &&
              obj.position.y < position.y + 1 &&
              obj.position.y + obj.size.height > position.y);
    });
  },

  getObjectAt: (position) => {
    const { objects } = get();

    return objects.find((obj) =>
      position.x >= obj.position.x &&
      position.x < obj.position.x + obj.size.width &&
      position.y >= obj.position.y &&
      position.y < obj.position.y + obj.size.height
    );
  },

  // State Management API calls
  setObjectState: async (objectId, key, value) => {
    try {
      const response = await fetch(`/api/room/objects/${objectId}/state`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ key, value, updated_by: 'user' }),
      });

      if (response.ok) {
        // Update local state - reload objects to get updated states
        await get().loadObjectsFromAPI();
        return true;
      } else {
        console.error('Failed to set object state:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Error setting object state:', error);
      return false;
    }
  },

  getObjectStates: async (objectId) => {
    try {
      const response = await fetch(`/api/room/objects/${objectId}/states`);
      if (response.ok) {
        return await response.json();
      } else {
        console.error('Failed to get object states:', response.statusText);
        return null;
      }
    } catch (error) {
      console.error('Error getting object states:', error);
      return null;
    }
  },

  // Assistant API calls
  loadAssistantFromAPI: async () => {
    try {
      const response = await fetch('/api/assistant/state');
      if (response.ok) {
        const assistantData = await response.json();

        // Update assistant state
        set((state) => ({
          assistant: {
            ...state.assistant,
            position: assistantData.position,
            isMoving: assistantData.movement.is_moving,
            targetPosition: assistantData.movement.target,
            movementPath: assistantData.movement.path?.map(([x, y]: [number, number]) => ({ x, y })),
            movementSpeed: assistantData.movement.speed || 2,
            currentAction: assistantData.status.action,
            mood: assistantData.status.mood,
            status: assistantData.status.mode === 'active' ? 'active' : 'idle',
            sitting_on_object_id: assistantData.interaction?.sitting_on,
            holding_object_id: assistantData.holding_object_id
          }
        }));
      } else {
        console.error('Failed to load assistant from API');
      }
    } catch (error) {
      console.error('Error loading assistant:', error);
    }
  },

  moveAssistantToPosition: async (x, y) => {
    try {
      const response = await fetch('/api/assistant/move', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ target: { x, y } }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // Update local assistant state
          await get().loadAssistantFromAPI();
          console.log(`Assistant moved to (${x}, ${y})`);
          return true;
        } else {
          console.error('Failed to move assistant:', result.error);
          return false;
        }
      } else {
        console.error('Assistant move request failed:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Error moving assistant:', error);
      return false;
    }
  },

  sitOnFurniture: async (furnitureId) => {
    try {
      const response = await fetch('/api/assistant/sit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ furniture_id: furnitureId }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // Update local assistant state
          await get().loadAssistantFromAPI();
          console.log(`Assistant sitting on ${furnitureId}`);
          return true;
        } else {
          console.error('Failed to sit on furniture:', result.error);
          return false;
        }
      } else {
        console.error('Sit request failed:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Error sitting on furniture:', error);
      return false;
    }
  },

  // Storage Management
  toggleStorageVisibility: () =>
    set((state) => ({
      storageVisible: !state.storageVisible
    })),

  loadStorageItems: async () => {
    try {
      const response = await fetch('/api/room/storage');
      if (response.ok) {
        const items = await response.json();
        set({ storageItems: items });
        console.log(`Loaded ${items.length} storage items`);
      } else {
        console.error('Failed to load storage items:', response.statusText);
      }
    } catch (error) {
      console.error('Error loading storage items:', error);
    }
  },

  addToStorage: async (itemData) => {
    try {
      const response = await fetch('/api/room/storage', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(itemData),
      });

      if (response.ok) {
        const newItem = await response.json();
        set((state) => ({
          storageItems: [...state.storageItems, newItem]
        }));
        console.log(`Added ${newItem.name} to storage`);
        return true;
      } else {
        console.error('Failed to add item to storage:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Error adding item to storage:', error);
      return false;
    }
  },

  placeFromStorage: async (itemId, position) => {
    try {
      const response = await fetch(`/api/room/storage/${itemId}/place`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ x: position.x, y: position.y }),
      });

      if (response.ok) {
        const placedObject = await response.json();

        // Remove from storage and add to objects
        set((state) => ({
          storageItems: state.storageItems.filter(item => item.id !== itemId),
          objects: [...state.objects, placedObject]
        }));

        console.log(`Placed ${placedObject.name} at (${position.x}, ${position.y})`);
        return true;
      } else {
        console.error('Failed to place item from storage:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Error placing item from storage:', error);
      return false;
    }
  },

  moveObjectToStorage: async (objectId) => {
    try {
      const response = await fetch(`/api/room/objects/${objectId}/store`, {
        method: 'POST',
      });

      if (response.ok) {
        const storageItem = await response.json();

        // Remove from objects and add to storage
        set((state) => ({
          objects: state.objects.filter(obj => obj.id !== objectId),
          storageItems: [...state.storageItems, storageItem]
        }));

        console.log(`Moved ${storageItem.name} to storage`);
        return true;
      } else {
        console.error('Failed to move object to storage:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Error moving object to storage:', error);
      return false;
    }
  },

  // Storage Placement Management
  startStoragePlacement: (itemId) =>
    set({
      selectedStorageItemId: itemId,
      isStoragePlacementActive: true
    }),

  clearStoragePlacement: () =>
    set({
      selectedStorageItemId: null,
      isStoragePlacementActive: false
    }),
}));