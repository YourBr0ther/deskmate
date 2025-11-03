/**
 * Zustand store for room state management
 */

import { create } from 'zustand';
import { RoomState, GridObject, Assistant, Position, GridMap, StorageItem } from '../types/room';

interface RoomStore extends RoomState {
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

  // Computed values
  getGridMap: () => GridMap;
  getGridDimensions: () => { width: number; height: number };
  isPositionOccupied: (position: Position) => boolean;
  getObjectAt: (position: Position) => GridObject | undefined;
}

// Grid constants
const GRID_WIDTH = 64;
const GRID_HEIGHT = 16;
const CELL_WIDTH = 20;
const CELL_HEIGHT = 30;

// Mobile grid constants (8x8 for mobile screens)
const MOBILE_GRID_WIDTH = 8;
const MOBILE_GRID_HEIGHT = 8;

// Initial room objects (basic furniture)
const initialObjects: GridObject[] = [
  {
    id: 'bed',
    type: 'furniture',
    name: 'Bed',
    position: { x: 50, y: 12 },
    size: { width: 8, height: 4 },
    solid: true,
    interactive: true,
    movable: false,
    states: { made: true }
  },
  {
    id: 'desk',
    type: 'furniture',
    name: 'Desk',
    position: { x: 10, y: 2 },
    size: { width: 6, height: 3 },
    solid: true,
    interactive: true,
    movable: false,
    states: { cluttered: false }
  },
  {
    id: 'window',
    type: 'furniture',
    name: 'Window',
    position: { x: 30, y: 0 },
    size: { width: 8, height: 1 },
    solid: false,
    interactive: true,
    movable: false,
    states: { open: false, curtains: 'closed' }
  },
  {
    id: 'door',
    type: 'furniture',
    name: 'Door',
    position: { x: 0, y: 8 },
    size: { width: 1, height: 3 },
    solid: false,
    interactive: true,
    movable: false,
    states: { open: false, locked: false }
  }
];

// Initial assistant state
const initialAssistant: Assistant = {
  id: 'assistant',
  position: { x: 32, y: 8 }, // Center of room
  isMoving: false,
  mood: 'neutral',
  status: 'idle',
  sitting_on_object_id: null
};

export const useRoomStore = create<RoomStore>((set, get) => ({
  // Initial state
  gridSize: { width: GRID_WIDTH, height: GRID_HEIGHT },
  cellSize: { width: CELL_WIDTH, height: CELL_HEIGHT },
  objects: initialObjects,
  assistant: initialAssistant,
  selectedObject: undefined,
  viewMode: 'desktop',
  draggedObject: null,
  storageItems: [],
  storageVisible: false,

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
        ? { width: MOBILE_GRID_WIDTH, height: MOBILE_GRID_HEIGHT }
        : { width: GRID_WIDTH, height: GRID_HEIGHT }
    })),

  // Drag and Drop Actions
  setDraggedObject: (objectId) =>
    set({ draggedObject: objectId }),

  moveObjectToPosition: async (objectId, position) => {
    try {
      const response = await fetch(`/api/room/objects/${objectId}/move`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(position),
      });

      if (response.ok) {
        // Update local state
        const { objects } = get();
        const updatedObjects = objects.map(obj =>
          obj.id === objectId
            ? { ...obj, position }
            : obj
        );
        set({ objects: updatedObjects });
        return true;
      } else {
        console.error('Failed to move object:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Error moving object:', error);
      return false;
    }
  },

  // API Actions
  setObjects: (objects) =>
    set({ objects }),

  loadObjectsFromAPI: async () => {
    try {
      const response = await fetch('/api/room/objects');
      if (response.ok) {
        const apiObjects = await response.json();

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
      } else {
        console.error('Failed to load objects from API');
      }
    } catch (error) {
      console.error('Error loading objects:', error);
    }
  },

  // Computed values
  getGridMap: () => {
    const { objects, assistant, gridSize } = get();

    // Initialize empty grid
    const grid: GridMap = Array(gridSize.height).fill(null).map((_, y) =>
      Array(gridSize.width).fill(null).map((_, x) => ({
        x,
        y,
        occupied: false,
        walkable: true
      }))
    );

    // Mark object positions
    objects.forEach((obj) => {
      for (let y = obj.position.y; y < obj.position.y + obj.size.height; y++) {
        for (let x = obj.position.x; x < obj.position.x + obj.size.width; x++) {
          if (x >= 0 && x < gridSize.width && y >= 0 && y < gridSize.height) {
            grid[y][x].occupied = true;
            grid[y][x].objectId = obj.id;
            grid[y][x].walkable = !obj.solid;
          }
        }
      }
    });

    // Mark assistant position
    const { x, y } = assistant.position;
    if (x >= 0 && x < gridSize.width && y >= 0 && y < gridSize.height) {
      grid[y][x].occupied = true;
      grid[y][x].objectId = assistant.id;
      grid[y][x].walkable = false;
    }

    return grid;
  },

  getGridDimensions: () => {
    const { viewMode } = get();
    return viewMode === 'mobile'
      ? { width: MOBILE_GRID_WIDTH, height: MOBILE_GRID_HEIGHT }
      : { width: GRID_WIDTH, height: GRID_HEIGHT };
  },

  isPositionOccupied: (position) => {
    const { objects, assistant } = get();

    // Check assistant position
    if (assistant.position.x === position.x && assistant.position.y === position.y) {
      return true;
    }

    // Check objects
    return objects.some((obj) => {
      return (
        position.x >= obj.position.x &&
        position.x < obj.position.x + obj.size.width &&
        position.y >= obj.position.y &&
        position.y < obj.position.y + obj.size.height &&
        obj.solid
      );
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
            sitting_on_object_id: assistantData.interaction?.sitting_on
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
}));