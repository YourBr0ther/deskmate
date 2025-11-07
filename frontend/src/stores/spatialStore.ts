/**
 * Unified Spatial Store for DeskMate
 *
 * This store consolidates roomStore and floorPlanStore into a single,
 * normalized state management solution for all spatial data including:
 * - Room objects and furniture
 * - Assistant position and state
 * - Floor plan data
 * - Storage items
 *
 * Uses normalized state patterns and optimistic updates for better performance.
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

import { api } from '../utils/api';
import { Position, Size } from '../utils/coordinateSystem';

// ============================================================================
// Type Definitions
// ============================================================================

export interface SpatialObject {
  id: string;
  type: 'furniture' | 'item' | 'storage_item';
  name: string;
  position: Position;
  size: Size;
  solid: boolean;
  interactive: boolean;
  movable: boolean;
  states: Record<string, any>;
  room_id: string;
  properties?: Record<string, any>;
}

export interface Assistant {
  id: string;
  position: Position;
  isMoving: boolean;
  mood: 'neutral' | 'happy' | 'curious' | 'tired' | 'focused';
  status: 'idle' | 'active' | 'moving' | 'interacting';
  facing: 'up' | 'down' | 'left' | 'right';
  sitting_on_object_id: string | null;
  holding_object_id: string | null;
  energy_level: number;
  current_action: string;
}

export interface Room {
  id: string;
  name: string;
  dimensions: Size;
  background_color?: string;
  objects: string[]; // Array of object IDs
}

export interface StorageItem {
  id: string;
  name: string;
  type: string;
  size: Size;
  properties: Record<string, any>;
  created_at: string;
}

// Normalized state structure
export interface SpatialEntities {
  objects: Record<string, SpatialObject>;
  rooms: Record<string, Room>;
  storageItems: Record<string, StorageItem>;
}

// UI state
export interface SpatialUI {
  currentRoomId: string | null;
  selectedObjectId: string | null;
  draggedObjectId: string | null;
  viewMode: 'desktop' | 'tablet' | 'mobile';
  showGrid: boolean;
  gridSize: Size;
  isLoading: boolean;
  error: string | null;
}

// Optimistic update tracking
export interface PendingOperation {
  id: string;
  type: 'move' | 'create' | 'delete' | 'update';
  timestamp: number;
  rollbackData?: any;
}

export interface SpatialStore {
  // Normalized entities
  entities: SpatialEntities;
  assistant: Assistant;
  ui: SpatialUI;
  pendingOps: Record<string, PendingOperation>;

  // ========================================================================
  // Computed Selectors (memoized)
  // ========================================================================

  getCurrentRoom: () => Room | null;
  getCurrentRoomObjects: () => SpatialObject[];
  getObjectsNearPosition: (position: Position, distance: number) => SpatialObject[];
  getInteractableObjects: () => SpatialObject[];
  getMovableObjects: () => SpatialObject[];

  // ========================================================================
  // Object Management
  // ========================================================================

  // Optimistic updates with rollback
  moveObject: (objectId: string, newPosition: Position) => Promise<void>;
  createObject: (object: Omit<SpatialObject, 'id'>) => Promise<void>;
  deleteObject: (objectId: string) => Promise<void>;
  updateObjectState: (objectId: string, states: Record<string, any>) => Promise<void>;

  // Immediate updates (for WebSocket events)
  setObjectPosition: (objectId: string, position: Position) => void;
  setObjectStates: (objectId: string, states: Record<string, any>) => void;
  addObject: (object: SpatialObject) => void;
  removeObject: (objectId: string) => void;

  // ========================================================================
  // Assistant Management
  // ========================================================================

  setAssistantPosition: (position: Position) => void;
  setAssistantStatus: (status: Partial<Assistant>) => void;
  moveAssistant: (position: Position) => Promise<void>;

  // ========================================================================
  // Room Management
  // ========================================================================

  setCurrentRoom: (roomId: string) => void;
  addRoom: (room: Room) => void;
  removeRoom: (roomId: string) => void;

  // ========================================================================
  // Storage Management
  // ========================================================================

  addStorageItem: (item: StorageItem) => void;
  removeStorageItem: (itemId: string) => void;
  placeStorageItem: (itemId: string, position: Position) => Promise<void>;

  // ========================================================================
  // UI State Management
  // ========================================================================

  selectObject: (objectId: string | null) => void;
  setDraggedObject: (objectId: string | null) => void;
  setViewMode: (mode: SpatialUI['viewMode']) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // ========================================================================
  // Optimistic Update Management
  // ========================================================================

  addPendingOperation: (op: PendingOperation) => void;
  completePendingOperation: (operationId: string) => void;
  rollbackPendingOperation: (operationId: string) => void;
  clearExpiredOperations: () => void;

  // ========================================================================
  // Data Loading
  // ========================================================================

  loadRoomData: (roomId: string) => Promise<void>;
  loadStorageItems: () => Promise<void>;
  refreshData: () => Promise<void>;

  // ========================================================================
  // Utility Functions
  // ========================================================================

  getObjectById: (id: string) => SpatialObject | undefined;
  getStorageItemById: (id: string) => StorageItem | undefined;
  isPositionOccupied: (position: Position) => boolean;
  getObjectAt: (position: Position) => SpatialObject | undefined;

  // Reset functions
  resetToDefaults: () => void;
  clearAllData: () => void;
}

// ============================================================================
// Initial State
// ============================================================================

const initialAssistant: Assistant = {
  id: 'assistant',
  position: { x: 960, y: 240 }, // Center of 1920x480 room
  isMoving: false,
  mood: 'neutral',
  status: 'idle',
  facing: 'right',
  sitting_on_object_id: null,
  holding_object_id: null,
  energy_level: 0.8,
  current_action: 'Standing idle'
};

const initialUI: SpatialUI = {
  currentRoomId: 'main-room',
  selectedObjectId: null,
  draggedObjectId: null,
  viewMode: 'desktop',
  showGrid: false,
  gridSize: { width: 1920, height: 480 },
  isLoading: false,
  error: null
};

const initialEntities: SpatialEntities = {
  objects: {},
  rooms: {
    'main-room': {
      id: 'main-room',
      name: 'Main Room',
      dimensions: { width: 1920, height: 480 },
      objects: []
    }
  },
  storageItems: {}
};

// ============================================================================
// Store Implementation
// ============================================================================

export const useSpatialStore = create<SpatialStore>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // Initial state
      entities: initialEntities,
      assistant: initialAssistant,
      ui: initialUI,
      pendingOps: {},

      // ======================================================================
      // Computed Selectors
      // ======================================================================

      getCurrentRoom: () => {
        const { entities, ui } = get();
        return ui.currentRoomId ? entities.rooms[ui.currentRoomId] || null : null;
      },

      getCurrentRoomObjects: () => {
        const { entities, ui } = get();
        const currentRoom = ui.currentRoomId ? entities.rooms[ui.currentRoomId] : null;
        if (!currentRoom) return [];

        return currentRoom.objects
          .map(id => entities.objects[id])
          .filter(Boolean);
      },

      getObjectsNearPosition: (position: Position, distance: number) => {
        const objects = get().getCurrentRoomObjects();
        return objects.filter(obj => {
          const dx = obj.position.x - position.x;
          const dy = obj.position.y - position.y;
          return Math.sqrt(dx * dx + dy * dy) <= distance;
        });
      },

      getInteractableObjects: () => {
        return get().getCurrentRoomObjects().filter(obj => obj.interactive);
      },

      getMovableObjects: () => {
        return get().getCurrentRoomObjects().filter(obj => obj.movable);
      },

      // ======================================================================
      // Object Management with Optimistic Updates
      // ======================================================================

      moveObject: async (objectId: string, newPosition: Position) => {
        const operationId = `move-${objectId}-${Date.now()}`;
        const currentObject = get().entities.objects[objectId];

        if (!currentObject) return;

        // Optimistic update
        const rollbackData = { ...currentObject };
        get().addPendingOperation({
          id: operationId,
          type: 'move',
          timestamp: Date.now(),
          rollbackData
        });

        set((state) => {
          state.entities.objects[objectId].position = newPosition;
        });

        try {
          const result = await api.moveObject(objectId, newPosition);

          if (result.success) {
            get().completePendingOperation(operationId);
          } else {
            get().rollbackPendingOperation(operationId);
            get().setError(result.error || 'Failed to move object');
          }
        } catch (error) {
          get().rollbackPendingOperation(operationId);
          get().setError(error instanceof Error ? error.message : 'Unknown error');
        }
      },

      createObject: async (objectData: Omit<SpatialObject, 'id'>) => {
        const tempId = `temp-${Date.now()}`;
        const operationId = `create-${tempId}`;

        // Optimistic update
        const tempObject: SpatialObject = { ...objectData, id: tempId };

        get().addPendingOperation({
          id: operationId,
          type: 'create',
          timestamp: Date.now()
        });

        set((state) => {
          state.entities.objects[tempId] = tempObject;
          state.entities.rooms[objectData.room_id]?.objects.push(tempId);
        });

        try {
          // API call would create the object and return real ID
          // For now, simulate success
          await new Promise(resolve => setTimeout(resolve, 100));

          get().completePendingOperation(operationId);
        } catch (error) {
          get().rollbackPendingOperation(operationId);
          get().setError(error instanceof Error ? error.message : 'Failed to create object');
        }
      },

      deleteObject: async (objectId: string) => {
        const operationId = `delete-${objectId}-${Date.now()}`;
        const currentObject = get().entities.objects[objectId];

        if (!currentObject) return;

        get().addPendingOperation({
          id: operationId,
          type: 'delete',
          timestamp: Date.now(),
          rollbackData: currentObject
        });

        set((state) => {
          delete state.entities.objects[objectId];

          // Remove from room
          Object.values(state.entities.rooms).forEach(room => {
            const index = room.objects.indexOf(objectId);
            if (index > -1) {
              room.objects.splice(index, 1);
            }
          });
        });

        try {
          // API call would delete the object
          await new Promise(resolve => setTimeout(resolve, 100));

          get().completePendingOperation(operationId);
        } catch (error) {
          get().rollbackPendingOperation(operationId);
          get().setError(error instanceof Error ? error.message : 'Failed to delete object');
        }
      },

      updateObjectState: async (objectId: string, states: Record<string, any>) => {
        const operationId = `update-${objectId}-${Date.now()}`;
        const currentObject = get().entities.objects[objectId];

        if (!currentObject) return;

        const rollbackData = { ...currentObject.states };
        get().addPendingOperation({
          id: operationId,
          type: 'update',
          timestamp: Date.now(),
          rollbackData
        });

        set((state) => {
          Object.assign(state.entities.objects[objectId].states, states);
        });

        try {
          const result = await api.setObjectState(objectId, Object.keys(states)[0], Object.values(states)[0]);

          if (result.success) {
            get().completePendingOperation(operationId);
          } else {
            get().rollbackPendingOperation(operationId);
            get().setError(result.error || 'Failed to update object state');
          }
        } catch (error) {
          get().rollbackPendingOperation(operationId);
          get().setError(error instanceof Error ? error.message : 'Unknown error');
        }
      },

      // ======================================================================
      // Immediate Updates (for WebSocket events)
      // ======================================================================

      setObjectPosition: (objectId: string, position: Position) => {
        set((state) => {
          if (state.entities.objects[objectId]) {
            state.entities.objects[objectId].position = position;
          }
        });
      },

      setObjectStates: (objectId: string, states: Record<string, any>) => {
        set((state) => {
          if (state.entities.objects[objectId]) {
            Object.assign(state.entities.objects[objectId].states, states);
          }
        });
      },

      addObject: (object: SpatialObject) => {
        set((state) => {
          state.entities.objects[object.id] = object;
          if (!state.entities.rooms[object.room_id]?.objects.includes(object.id)) {
            state.entities.rooms[object.room_id]?.objects.push(object.id);
          }
        });
      },

      removeObject: (objectId: string) => {
        set((state) => {
          delete state.entities.objects[objectId];

          Object.values(state.entities.rooms).forEach(room => {
            const index = room.objects.indexOf(objectId);
            if (index > -1) {
              room.objects.splice(index, 1);
            }
          });
        });
      },

      // ======================================================================
      // Assistant Management
      // ======================================================================

      setAssistantPosition: (position: Position) => {
        set((state) => {
          state.assistant.position = position;
        });
      },

      setAssistantStatus: (status: Partial<Assistant>) => {
        set((state) => {
          Object.assign(state.assistant, status);
        });
      },

      moveAssistant: async (position: Position) => {
        // Optimistic update
        const oldPosition = get().assistant.position;
        get().setAssistantPosition(position);

        try {
          const result = await api.moveAssistant(position.x, position.y);

          if (!result.success) {
            // Rollback on failure
            get().setAssistantPosition(oldPosition);
            get().setError(result.error || 'Failed to move assistant');
          }
        } catch (error) {
          get().setAssistantPosition(oldPosition);
          get().setError(error instanceof Error ? error.message : 'Unknown error');
        }
      },

      // ======================================================================
      // Room Management
      // ======================================================================

      setCurrentRoom: (roomId: string) => {
        set((state) => {
          state.ui.currentRoomId = roomId;
        });
      },

      addRoom: (room: Room) => {
        set((state) => {
          state.entities.rooms[room.id] = room;
        });
      },

      removeRoom: (roomId: string) => {
        set((state) => {
          delete state.entities.rooms[roomId];
          if (state.ui.currentRoomId === roomId) {
            state.ui.currentRoomId = Object.keys(state.entities.rooms)[0] || null;
          }
        });
      },

      // ======================================================================
      // Storage Management
      // ======================================================================

      addStorageItem: (item: StorageItem) => {
        set((state) => {
          state.entities.storageItems[item.id] = item;
        });
      },

      removeStorageItem: (itemId: string) => {
        set((state) => {
          delete state.entities.storageItems[itemId];
        });
      },

      placeStorageItem: async (itemId: string, position: Position) => {
        const item = get().entities.storageItems[itemId];
        if (!item) return;

        try {
          const result = await api.placeFromStorage(itemId, position);

          if (result.success) {
            // Remove from storage, add to room
            get().removeStorageItem(itemId);
            // The backend should send a WebSocket event to add the object
          } else {
            get().setError(result.error || 'Failed to place storage item');
          }
        } catch (error) {
          get().setError(error instanceof Error ? error.message : 'Unknown error');
        }
      },

      // ======================================================================
      // UI State Management
      // ======================================================================

      selectObject: (objectId: string | null) => {
        set((state) => {
          state.ui.selectedObjectId = objectId;
        });
      },

      setDraggedObject: (objectId: string | null) => {
        set((state) => {
          state.ui.draggedObjectId = objectId;
        });
      },

      setViewMode: (mode: SpatialUI['viewMode']) => {
        set((state) => {
          state.ui.viewMode = mode;

          // Adjust grid size based on view mode
          switch (mode) {
            case 'mobile':
              state.ui.gridSize = { width: 480, height: 120 };
              break;
            case 'tablet':
              state.ui.gridSize = { width: 960, height: 240 };
              break;
            default:
              state.ui.gridSize = { width: 1920, height: 480 };
          }
        });
      },

      setLoading: (loading: boolean) => {
        set((state) => {
          state.ui.isLoading = loading;
        });
      },

      setError: (error: string | null) => {
        set((state) => {
          state.ui.error = error;
        });
      },

      // ======================================================================
      // Optimistic Update Management
      // ======================================================================

      addPendingOperation: (op: PendingOperation) => {
        set((state) => {
          state.pendingOps[op.id] = op;
        });
      },

      completePendingOperation: (operationId: string) => {
        set((state) => {
          delete state.pendingOps[operationId];
        });
      },

      rollbackPendingOperation: (operationId: string) => {
        set((state) => {
          const op = state.pendingOps[operationId];
          if (op && op.rollbackData) {
            switch (op.type) {
              case 'move':
                if (op.rollbackData.id && state.entities.objects[op.rollbackData.id]) {
                  state.entities.objects[op.rollbackData.id] = op.rollbackData;
                }
                break;
              case 'delete':
                state.entities.objects[op.rollbackData.id] = op.rollbackData;
                break;
              case 'update':
                if (op.rollbackData.id && state.entities.objects[op.rollbackData.id]) {
                  state.entities.objects[op.rollbackData.id].states = op.rollbackData;
                }
                break;
            }
          }
          delete state.pendingOps[operationId];
        });
      },

      clearExpiredOperations: () => {
        const now = Date.now();
        const maxAge = 10000; // 10 seconds

        set((state) => {
          Object.keys(state.pendingOps).forEach(id => {
            if (now - state.pendingOps[id].timestamp > maxAge) {
              delete state.pendingOps[id];
            }
          });
        });
      },

      // ======================================================================
      // Data Loading
      // ======================================================================

      loadRoomData: async (roomId: string) => {
        get().setLoading(true);
        get().setError(null);

        try {
          const objectsResult = await api.getObjects();

          if (objectsResult.success && objectsResult.data) {
            set((state) => {
              // Clear existing objects for this room
              state.entities.rooms[roomId].objects = [];

              // Add objects
              objectsResult.data.forEach((obj: any) => {
                const spatialObject: SpatialObject = {
                  id: obj.id,
                  type: obj.type || 'furniture',
                  name: obj.name,
                  position: obj.position,
                  size: obj.size,
                  solid: obj.solid !== false,
                  interactive: obj.interactive !== false,
                  movable: obj.movable === true,
                  states: obj.states || {},
                  room_id: roomId,
                  properties: obj.properties || {}
                };

                state.entities.objects[obj.id] = spatialObject;
                state.entities.rooms[roomId].objects.push(obj.id);
              });
            });
          }

          // Load assistant state
          const assistantResult = await api.getAssistantState();
          if (assistantResult.success && assistantResult.data) {
            get().setAssistantStatus({
              position: assistantResult.data.position,
              status: assistantResult.data.status,
              mood: assistantResult.data.mood
            });
          }

        } catch (error) {
          get().setError(error instanceof Error ? error.message : 'Failed to load room data');
        } finally {
          get().setLoading(false);
        }
      },

      loadStorageItems: async () => {
        try {
          const result = await api.getStorageItems();

          if (result.success && result.data) {
            set((state) => {
              state.entities.storageItems = {};
              result.data.forEach((item: any) => {
                state.entities.storageItems[item.id] = {
                  id: item.id,
                  name: item.name,
                  type: item.type,
                  size: item.size,
                  properties: item.properties || {},
                  created_at: item.created_at
                };
              });
            });
          }
        } catch (error) {
          get().setError(error instanceof Error ? error.message : 'Failed to load storage items');
        }
      },

      refreshData: async () => {
        const currentRoomId = get().ui.currentRoomId;
        if (currentRoomId) {
          await Promise.all([
            get().loadRoomData(currentRoomId),
            get().loadStorageItems()
          ]);
        }
      },

      // ======================================================================
      // Utility Functions
      // ======================================================================

      getObjectById: (id: string) => {
        return get().entities.objects[id];
      },

      getStorageItemById: (id: string) => {
        return get().entities.storageItems[id];
      },

      isPositionOccupied: (position: Position) => {
        const objects = get().getCurrentRoomObjects();
        const assistant = get().assistant;

        // Check assistant collision
        if (Math.abs(assistant.position.x - position.x) < 30 &&
            Math.abs(assistant.position.y - position.y) < 30) {
          return true;
        }

        // Check object collisions
        return objects.some(obj =>
          obj.solid &&
          position.x >= obj.position.x &&
          position.x < obj.position.x + obj.size.width &&
          position.y >= obj.position.y &&
          position.y < obj.position.y + obj.size.height
        );
      },

      getObjectAt: (position: Position) => {
        const objects = get().getCurrentRoomObjects();
        return objects.find(obj =>
          position.x >= obj.position.x &&
          position.x < obj.position.x + obj.size.width &&
          position.y >= obj.position.y &&
          position.y < obj.position.y + obj.size.height
        );
      },

      // ======================================================================
      // Reset Functions
      // ======================================================================

      resetToDefaults: () => {
        set({
          entities: initialEntities,
          assistant: initialAssistant,
          ui: initialUI,
          pendingOps: {}
        });
      },

      clearAllData: () => {
        set((state) => {
          state.entities = {
            objects: {},
            rooms: {
              'main-room': {
                id: 'main-room',
                name: 'Main Room',
                dimensions: { width: 1920, height: 480 },
                objects: []
              }
            },
            storageItems: {}
          };
          state.ui.selectedObjectId = null;
          state.ui.draggedObjectId = null;
          state.ui.error = null;
          state.pendingOps = {};
        });
      }
    }))
  )
);

// ============================================================================
// Cleanup subscription for expired operations
// ============================================================================

// Clean up expired operations every 30 seconds
setInterval(() => {
  useSpatialStore.getState().clearExpiredOperations();
}, 30000);