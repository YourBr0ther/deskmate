/**
 * Store Migration Service
 *
 * Handles the migration from the old fragmented store system
 * (roomStore + floorPlanStore) to the new unified spatialStore.
 *
 * This service provides a smooth transition path while maintaining
 * backward compatibility during the migration period.
 */

import { useSpatialStore, SpatialObject, Room } from '../stores/spatialStore';
import { useRoomStore } from '../stores/roomStore';
import { useFloorPlanStore } from '../stores/floorPlanStore';
import { LegacyGridConverter } from '../utils/coordinateSystem';

export interface MigrationResult {
  success: boolean;
  migratedObjects: number;
  migratedRooms: number;
  errors: string[];
  warnings: string[];
}

export class StoreMigrationService {
  private static instance: StoreMigrationService;

  private constructor() {}

  static getInstance(): StoreMigrationService {
    if (!StoreMigrationService.instance) {
      StoreMigrationService.instance = new StoreMigrationService();
    }
    return StoreMigrationService.instance;
  }

  /**
   * Migrate data from old stores to the new unified spatial store
   */
  async migrateToSpatialStore(): Promise<MigrationResult> {
    const result: MigrationResult = {
      success: false,
      migratedObjects: 0,
      migratedRooms: 0,
      errors: [],
      warnings: []
    };

    try {
      // Clear the spatial store first
      const spatialStore = useSpatialStore.getState();
      spatialStore.clearAllData();

      // Migrate from roomStore
      await this.migrateFromRoomStore(result);

      // Migrate from floorPlanStore
      await this.migrateFromFloorPlanStore(result);

      result.success = result.errors.length === 0;

      console.log('Store migration completed:', result);
      return result;

    } catch (error) {
      result.errors.push(`Migration failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      result.success = false;
      return result;
    }
  }

  /**
   * Migrate data from the old roomStore
   */
  private async migrateFromRoomStore(result: MigrationResult): Promise<void> {
    try {
      const roomStore = useRoomStore.getState();
      const spatialStore = useSpatialStore.getState();

      // Migrate objects
      if (roomStore.objects && roomStore.objects.length > 0) {
        for (const obj of roomStore.objects) {
          try {
            // Normalize position to pixel coordinates
            const position = LegacyGridConverter.normalizePosition(obj.position);

            // Convert size to pixels if needed
            let size = obj.size;
            if (LegacyGridConverter.isLegacyGridCoordinate({ x: size.width, y: size.height })) {
              size = {
                width: size.width * 30, // Convert grid cells to pixels
                height: size.height * 30
              };
            }

            const spatialObject: SpatialObject = {
              id: obj.id,
              type: obj.type as any || 'furniture',
              name: obj.name,
              position,
              size,
              solid: obj.solid ?? true,
              interactive: obj.interactive ?? true,
              movable: obj.movable ?? false,
              states: obj.states || {},
              room_id: 'main-room',
              properties: (obj as any).properties || {}
            };

            spatialStore.addObject(spatialObject);
            result.migratedObjects++;

          } catch (error) {
            result.errors.push(`Failed to migrate object ${obj.id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
          }
        }
      }

      // Migrate assistant state
      if (roomStore.assistant) {
        const assistantPosition = LegacyGridConverter.normalizePosition(roomStore.assistant.position);

        spatialStore.setAssistantStatus({
          position: assistantPosition,
          mood: roomStore.assistant.mood as any,
          status: roomStore.assistant.status as any,
          holding_object_id: roomStore.assistant.holding_object_id,
          sitting_on_object_id: roomStore.assistant.sitting_on_object_id
        });

        result.warnings.push('Assistant state migrated from roomStore');
      }

      // Migrate storage items (if any)
      if ((roomStore as any).storageItems) {
        for (const item of (roomStore as any).storageItems) {
          try {
            spatialStore.addStorageItem({
              id: item.id,
              name: item.name,
              type: item.type,
              size: item.size,
              properties: item.properties || {},
              created_at: item.created_at || new Date().toISOString()
            });
          } catch (error) {
            result.errors.push(`Failed to migrate storage item ${item.id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
          }
        }
      }

    } catch (error) {
      result.errors.push(`RoomStore migration failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Migrate data from the old floorPlanStore
   */
  private async migrateFromFloorPlanStore(result: MigrationResult): Promise<void> {
    try {
      const floorPlanStore = useFloorPlanStore.getState();
      const spatialStore = useSpatialStore.getState();

      // Migrate floor plan data if available
      if (floorPlanStore.currentFloorPlan) {
        const floorPlan = floorPlanStore.currentFloorPlan;

        // Migrate rooms from floor plan
        if ((floorPlan as any).rooms) {
          for (const room of (floorPlan as any).rooms) {
            try {
              const spatialRoom: Room = {
                id: room.id,
                name: room.name,
                dimensions: room.dimensions || { width: 1920, height: 480 },
                objects: []
              };

              spatialStore.addRoom(spatialRoom);
              result.migratedRooms++;

              // Migrate furniture in this room
              if (room.furniture) {
                for (const furniture of room.furniture) {
                  try {
                    const spatialObject: SpatialObject = {
                      id: furniture.id,
                      type: 'furniture',
                      name: furniture.name,
                      position: furniture.position,
                      size: furniture.size,
                      solid: furniture.solid !== false,
                      interactive: furniture.interactive !== false,
                      movable: furniture.movable === true,
                      states: furniture.states || {},
                      room_id: room.id,
                      properties: {
                        furniture_type: furniture.type,
                        style: furniture.style,
                        color: furniture.color
                      }
                    };

                    spatialStore.addObject(spatialObject);
                    result.migratedObjects++;

                  } catch (error) {
                    result.errors.push(`Failed to migrate furniture ${furniture.id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
                  }
                }
              }

            } catch (error) {
              result.errors.push(`Failed to migrate room ${room.id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
            }
          }
        }

        // Set the first migrated room as current
        const rooms = Object.keys(spatialStore.entities.rooms);
        if (rooms.length > 0) {
          spatialStore.setCurrentRoom(rooms[0]);
        }
      }

      // Migrate assistant state from floor plan store
      if (floorPlanStore.assistant) {
        const assistant = floorPlanStore.assistant;

        spatialStore.setAssistantStatus({
          position: assistant.location.position,
          facing: assistant.location.facing as any,
          mood: assistant.status.mood as any,
          energy_level: assistant.status.energy_level,
          status: assistant.status.mode === 'active' ? 'active' : 'idle',
          current_action: assistant.status.action
        });

        result.warnings.push('Assistant state migrated from floorPlanStore');
      }

    } catch (error) {
      result.errors.push(`FloorPlanStore migration failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Validate the migrated data for consistency
   */
  validateMigration(): { isValid: boolean; issues: string[] } {
    const issues: string[] = [];
    const spatialStore = useSpatialStore.getState();

    try {
      // Check if we have at least one room
      const rooms = Object.keys(spatialStore.entities.rooms);
      if (rooms.length === 0) {
        issues.push('No rooms found after migration');
      }

      // Check if current room is set
      if (!spatialStore.ui.currentRoomId) {
        issues.push('No current room set after migration');
      }

      // Check if assistant position is valid
      const assistant = spatialStore.assistant;
      if (!assistant.position || assistant.position.x < 0 || assistant.position.y < 0) {
        issues.push('Assistant position is invalid after migration');
      }

      // Check if all objects have valid positions and sizes
      const objects = Object.values(spatialStore.entities.objects);
      for (const obj of objects) {
        if (!obj.position || obj.position.x < 0 || obj.position.y < 0) {
          issues.push(`Object ${obj.id} has invalid position`);
        }

        if (!obj.size || obj.size.width <= 0 || obj.size.height <= 0) {
          issues.push(`Object ${obj.id} has invalid size`);
        }

        if (!spatialStore.entities.rooms[obj.room_id]) {
          issues.push(`Object ${obj.id} references non-existent room ${obj.room_id}`);
        }
      }

      // Check for object position overlaps (warnings)
      for (let i = 0; i < objects.length; i++) {
        for (let j = i + 1; j < objects.length; j++) {
          const obj1 = objects[i];
          const obj2 = objects[j];

          if (obj1.solid && obj2.solid && obj1.room_id === obj2.room_id) {
            // Simple overlap check
            const overlap = (
              obj1.position.x < obj2.position.x + obj2.size.width &&
              obj1.position.x + obj1.size.width > obj2.position.x &&
              obj1.position.y < obj2.position.y + obj2.size.height &&
              obj1.position.y + obj1.size.height > obj2.position.y
            );

            if (overlap) {
              issues.push(`Objects ${obj1.id} and ${obj2.id} overlap (warning)`);
            }
          }
        }
      }

      return {
        isValid: issues.filter(issue => !issue.includes('warning')).length === 0,
        issues
      };

    } catch (error) {
      issues.push(`Validation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      return { isValid: false, issues };
    }
  }

  /**
   * Create a backup of the current store states before migration
   */
  createBackup(): { roomStore: any; floorPlanStore: any } {
    try {
      const roomStore = useRoomStore.getState();
      const floorPlanStore = useFloorPlanStore.getState();

      return {
        roomStore: {
          objects: [...roomStore.objects],
          assistant: { ...roomStore.assistant },
          selectedObject: roomStore.selectedObject,
          viewMode: roomStore.viewMode,
          gridSize: { ...roomStore.gridSize },
          storageItems: (roomStore as any).storageItems ? [...(roomStore as any).storageItems] : []
        },
        floorPlanStore: {
          currentFloorPlan: floorPlanStore.currentFloorPlan ? { ...floorPlanStore.currentFloorPlan } : null,
          assistant: floorPlanStore.assistant ? { ...floorPlanStore.assistant } : null,
          selectedObjectId: floorPlanStore.selectedObjectId,
          isLoading: floorPlanStore.isLoading,
          error: floorPlanStore.error
        }
      };
    } catch (error) {
      console.error('Failed to create store backup:', error);
      return { roomStore: {}, floorPlanStore: {} };
    }
  }

  /**
   * Check if migration is needed by examining the stores
   */
  isMigrationNeeded(): boolean {
    try {
      const roomStore = useRoomStore.getState();
      const floorPlanStore = useFloorPlanStore.getState();
      const spatialStore = useSpatialStore.getState();

      // If spatial store has data, migration may not be needed
      const hasData = Object.keys(spatialStore.entities.objects).length > 0 ||
                      Object.keys(spatialStore.entities.rooms).length > 1; // More than just main-room

      // If old stores have data, migration is needed
      const hasOldData = roomStore.objects.length > 0 ||
                         floorPlanStore.currentFloorPlan !== null;

      return hasOldData && !hasData;
    } catch (error) {
      console.error('Error checking migration status:', error);
      return false;
    }
  }
}

// Export singleton instance
export const storeMigration = StoreMigrationService.getInstance();