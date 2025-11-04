/**
 * TypeScript types for responsive room system
 */

export interface Position {
  x: number;
  y: number;
}

export interface GridObject {
  id: string;
  type: 'furniture' | 'decoration' | 'item' | 'assistant';
  name: string;
  position: Position;
  size: {
    width: number;
    height: number;
  };
  sprite?: string;
  interactive: boolean;
  solid: boolean;
  movable?: boolean;
  states?: Record<string, any>;
}

export interface StorageItem {
  id: string;
  name: string;
  description: string;
  type: 'decoration' | 'item' | 'tool';
  default_size: {
    width: number;
    height: number;
  };
  properties: {
    solid: boolean;
    interactive: boolean;
    movable: boolean;
  };
  sprite?: string;
  color?: string;
  stored_at: string;
  created_by: string;
  usage_count: number;
}

export interface Assistant {
  id: string;
  position: Position;
  targetPosition?: Position;
  isMoving: boolean;
  currentAction?: string;
  mood: 'happy' | 'neutral' | 'sad' | 'excited' | 'tired';
  status: 'active' | 'idle' | 'busy';
  sitting_on_object_id?: string | null;
  holding_object_id?: string | null;
  facing?: string;
  energy_level?: number; // 0.0 to 1.0
  // Animation state
  animatedPosition?: Position;
  movementPath?: Position[];
  movementSpeed?: number;
}

export interface RoomState {
  gridSize: {
    width: number;
    height: number;
  };
  cellSize: {
    width: number;
    height: number;
  };
  objects: GridObject[];
  assistant: Assistant;
  selectedObject?: string;
  viewMode: 'desktop' | 'mobile' | 'tablet';
  storageItems: StorageItem[];
  storageVisible: boolean;
}

export interface GridCell {
  x: number;
  y: number;
  occupied: boolean;
  objectId?: string;
  walkable: boolean;
}

export type GridMap = GridCell[][];

// Responsive breakpoint types
export type BreakpointKey = 'mobile' | 'tablet' | 'desktop';

export interface BreakpointConfig {
  gridColumns: number;
  gridRows: number;
  cellSize: { width: number; height: number };
  showSidebar: boolean;
  compactMode: boolean;
}