/**
 * Zustand store for floor plan state management using pixel coordinates.
 *
 * This store replaces the grid-based roomStore for the new open-plan system.
 * Uses pixel coordinates throughout and integrates with the FloorPlan types.
 */

import { create } from 'zustand';

import { FloorPlan, Assistant, Position, FurnitureItem } from '../types/floorPlan';
import { gridToPixel } from '../utils/coordinateConversion';

interface FloorPlanState {
  // Current floor plan
  currentFloorPlan: FloorPlan | null;
  selectedFloorPlanId: string | null;

  // Assistant state (pixel coordinates)
  assistant: Assistant | null;

  // UI state
  selectedObjectId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setCurrentFloorPlan: (floorPlan: FloorPlan) => void;
  clearFloorPlan: () => void;

  // Assistant management
  setAssistant: (assistant: Assistant) => void;
  updateAssistantPosition: (position: Position) => void;
  updateAssistantStatus: (status: Partial<Assistant['status']>) => void;

  // Object management
  selectObject: (objectId: string | null) => void;
  updateFurniturePosition: (objectId: string, position: Position) => void;

  // API integration
  loadFloorPlanFromAPI: (floorPlanId: string) => Promise<void>;
  syncAssistantFromBackend: (backendAssistantData: any) => void;

  // Utility functions
  getObjectById: (objectId: string) => FurnitureItem | null;
  getPositionInRoom: (position: Position) => string | null;
  isPositionAccessible: (position: Position) => boolean;
}

const initialAssistant: Assistant = {
  id: 'default',
  location: {
    position: { x: 650, y: 300 }, // Center of typical floor plan
    facing: 'right',
    facing_angle: 0
  },
  status: {
    mood: 'neutral',
    action: 'idle',
    energy_level: 0.8,
    mode: 'active'
  }
};

export const useFloorPlanStore = create<FloorPlanState>((set, get) => ({
  // Initial state
  currentFloorPlan: null,
  selectedFloorPlanId: null,
  assistant: initialAssistant,
  selectedObjectId: null,
  isLoading: false,
  error: null,

  // Floor plan management
  setCurrentFloorPlan: (floorPlan) => {
    set({
      currentFloorPlan: floorPlan,
      selectedFloorPlanId: floorPlan.id,
      error: null
    });
  },

  clearFloorPlan: () => {
    set({
      currentFloorPlan: null,
      selectedFloorPlanId: null,
      selectedObjectId: null
    });
  },

  // Assistant management
  setAssistant: (assistant) => {
    set({ assistant });
  },

  updateAssistantPosition: (position) => {
    set((state) => ({
      assistant: state.assistant ? {
        ...state.assistant,
        location: {
          ...state.assistant.location,
          position
        }
      } : null
    }));
  },

  updateAssistantStatus: (status) => {
    set((state) => ({
      assistant: state.assistant ? {
        ...state.assistant,
        status: {
          ...state.assistant.status,
          ...status
        }
      } : null
    }));
  },

  // Object management
  selectObject: (objectId) => {
    set({ selectedObjectId: objectId });
  },

  updateFurniturePosition: (objectId, position) => {
    set((state) => {
      if (!state.currentFloorPlan) return state;

      const updatedFurniture = state.currentFloorPlan.furniture.map(item =>
        item.id === objectId ? { ...item, position } : item
      );

      return {
        currentFloorPlan: {
          ...state.currentFloorPlan,
          furniture: updatedFurniture
        }
      };
    });
  },

  // API integration
  loadFloorPlanFromAPI: async (floorPlanId) => {
    set({ isLoading: true, error: null });

    try {
      // TODO: Replace with actual API call
      const response = await fetch(`/api/floor-plans/${floorPlanId}`);

      if (!response.ok) {
        throw new Error(`Failed to load floor plan: ${response.statusText}`);
      }

      const floorPlan: FloorPlan = await response.json();
      get().setCurrentFloorPlan(floorPlan);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      set({ error: errorMessage });
      console.error('Error loading floor plan:', error);
    } finally {
      set({ isLoading: false });
    }
  },

  // Sync assistant data from grid-based backend
  syncAssistantFromBackend: (backendData) => {
    const state = get();

    if (!state.assistant || !state.currentFloorPlan) return;

    // Convert grid coordinates to pixel coordinates if needed
    let position = state.assistant.location.position;

    if (backendData.position) {
      // Check if backend position looks like grid coordinates
      const isGridPos = backendData.position.x < 64 && backendData.position.y < 16;

      if (isGridPos) {
        // Convert grid to pixel coordinates
        position = gridToPixel(
          { x: backendData.position.x, y: backendData.position.y },
          state.currentFloorPlan.dimensions
        );
      } else {
        // Already pixel coordinates
        position = { x: backendData.position.x, y: backendData.position.y };
      }
    }

    // Update assistant with converted coordinates and backend status
    set({
      assistant: {
        ...state.assistant,
        location: {
          ...state.assistant.location,
          position
        },
        status: {
          ...state.assistant.status,
          mode: backendData.status?.mode || state.assistant.status.mode,
          action: backendData.status?.action || state.assistant.status.action,
          mood: backendData.status?.mood || state.assistant.status.mood
        }
      }
    });
  },

  // Utility functions
  getObjectById: (objectId) => {
    const state = get();
    return state.currentFloorPlan?.furniture.find(item => item.id === objectId) || null;
  },

  getPositionInRoom: (position) => {
    const state = get();
    if (!state.currentFloorPlan) return null;

    // Find which room contains this position
    for (const room of state.currentFloorPlan.rooms) {
      const { x, y, width, height } = room.bounds;
      if (
        position.x >= x &&
        position.x <= x + width &&
        position.y >= y &&
        position.y <= y + height
      ) {
        return room.id;
      }
    }

    return null;
  },

  isPositionAccessible: (position) => {
    const state = get();
    if (!state.currentFloorPlan) return false;

    // Check if position is within any room bounds
    const roomId = get().getPositionInRoom(position);
    if (!roomId) return false;

    // Check if position intersects with solid furniture
    for (const furniture of state.currentFloorPlan.furniture) {
      if (!furniture.properties.solid) continue;

      const furnitureRight = furniture.position.x + furniture.geometry.width;
      const furnitureBottom = furniture.position.y + furniture.geometry.height;

      if (
        position.x >= furniture.position.x &&
        position.x <= furnitureRight &&
        position.y >= furniture.position.y &&
        position.y <= furnitureBottom
      ) {
        return false; // Position is blocked by furniture
      }
    }

    return true;
  }
}));