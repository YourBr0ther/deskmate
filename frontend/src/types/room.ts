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

export interface Assistant {
  id: string;
  position: Position;
  targetPosition?: Position;
  isMoving: boolean;
  currentAction?: string;
  mood: 'happy' | 'neutral' | 'sad' | 'excited' | 'tired';
  status: 'active' | 'idle' | 'busy';
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