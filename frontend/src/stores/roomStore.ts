/**
 * Zustand store for room state management
 */

import { create } from 'zustand';
import { RoomState, GridObject, Assistant, Position, GridMap } from '../types/room';

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
  status: 'idle'
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
}));