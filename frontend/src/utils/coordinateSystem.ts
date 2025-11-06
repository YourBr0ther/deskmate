/**
 * Unified Coordinate System for DeskMate Frontend
 *
 * This module provides a single, consistent pixel-based coordinate system
 * to replace the previous dual grid/pixel system. All spatial calculations
 * throughout DeskMate now use pixel coordinates exclusively.
 */

// Room dimensions in pixels (must match backend constants)
export const ROOM_WIDTH = 1920;
export const ROOM_HEIGHT = 480;

// Grid compatibility (for legacy calculations)
export const GRID_WIDTH = 64;
export const GRID_HEIGHT = 16;
export const CELL_SIZE = 30; // pixels per grid cell

// Distance thresholds in pixels
export const INTERACTION_DISTANCE = 80.0; // Distance for object interaction
export const NEARBY_DISTANCE = 150.0;     // Distance for "nearby" object detection
export const MOVEMENT_PRECISION = 5.0;    // Precision for movement calculations

/**
 * Position in pixel coordinates
 */
export interface Position {
  x: number;
  y: number;
}

/**
 * Size in pixels
 */
export interface Size {
  width: number;
  height: number;
}

/**
 * Bounding box in pixel coordinates
 */
export interface BoundingBox {
  position: Position;
  size: Size;
}

/**
 * Calculate Euclidean distance between two positions
 */
export function distance(pos1: Position, pos2: Position): number {
  return Math.sqrt((pos2.x - pos1.x) ** 2 + (pos2.y - pos1.y) ** 2);
}

/**
 * Calculate Manhattan distance between two positions
 */
export function manhattanDistance(pos1: Position, pos2: Position): number {
  return Math.abs(pos2.x - pos1.x) + Math.abs(pos2.y - pos1.y);
}

/**
 * Check if two positions are within interaction distance
 */
export function canInteract(pos1: Position, pos2: Position): boolean {
  return distance(pos1, pos2) <= INTERACTION_DISTANCE;
}

/**
 * Check if two positions are nearby (for visibility/awareness)
 */
export function isNearby(pos1: Position, pos2: Position): boolean {
  return distance(pos1, pos2) <= NEARBY_DISTANCE;
}

/**
 * Check if position is within room bounds
 */
export function isWithinBounds(position: Position): boolean {
  return position.x >= 0 && position.x <= ROOM_WIDTH &&
         position.y >= 0 && position.y <= ROOM_HEIGHT;
}

/**
 * Clamp position to room bounds
 */
export function clampToRoom(position: Position): Position {
  return {
    x: Math.max(0, Math.min(ROOM_WIDTH, position.x)),
    y: Math.max(0, Math.min(ROOM_HEIGHT, position.y))
  };
}

/**
 * Check if a point is within a bounding box
 */
export function pointInBoundingBox(point: Position, box: BoundingBox): boolean {
  return point.x >= box.position.x &&
         point.x < box.position.x + box.size.width &&
         point.y >= box.position.y &&
         point.y < box.position.y + box.size.height;
}

/**
 * Check if two bounding boxes overlap
 */
export function boundingBoxesOverlap(box1: BoundingBox, box2: BoundingBox): boolean {
  return box1.position.x < box2.position.x + box2.size.width &&
         box1.position.x + box1.size.width > box2.position.x &&
         box1.position.y < box2.position.y + box2.size.height &&
         box1.position.y + box1.size.height > box2.position.y;
}

/**
 * Get the center point of a bounding box
 */
export function getBoundingBoxCenter(box: BoundingBox): Position {
  return {
    x: box.position.x + box.size.width / 2,
    y: box.position.y + box.size.height / 2
  };
}

/**
 * Calculate minimum distance from point to bounding box
 */
export function distanceToBox(point: Position, box: BoundingBox): number {
  if (pointInBoundingBox(point, box)) {
    return 0;
  }

  const dx = Math.max(0, Math.max(box.position.x - point.x, point.x - (box.position.x + box.size.width)));
  const dy = Math.max(0, Math.max(box.position.y - point.y, point.y - (box.position.y + box.size.height)));

  return Math.sqrt(dx * dx + dy * dy);
}

/**
 * Find objects within a certain distance from a position
 */
export function getObjectsWithinDistance<T extends { position: Position }>(
  center: Position,
  objects: T[],
  maxDistance: number
): T[] {
  return objects.filter(obj => distance(center, obj.position) <= maxDistance);
}

/**
 * Legacy grid conversion utilities (for transition period only)
 */
export namespace LegacyGridConverter {
  /**
   * Convert grid coordinates to pixel coordinates
   */
  export function gridToPixels(gridX: number, gridY: number): Position {
    return {
      x: gridX * CELL_SIZE,
      y: gridY * CELL_SIZE
    };
  }

  /**
   * Convert pixel coordinates to grid coordinates (rounded)
   */
  export function pixelsToGrid(pixelX: number, pixelY: number): { x: number; y: number } {
    return {
      x: Math.round(pixelX / CELL_SIZE),
      y: Math.round(pixelY / CELL_SIZE)
    };
  }

  /**
   * Detect if coordinates appear to be legacy grid-based
   */
  export function isLegacyGridCoordinate(pos: Position): boolean {
    // Check if values are small integers that fit grid dimensions
    return Number.isInteger(pos.x) && Number.isInteger(pos.y) &&
           pos.x >= 0 && pos.x < GRID_WIDTH &&
           pos.y >= 0 && pos.y < GRID_HEIGHT;
  }

  /**
   * Normalize position to pixel coordinates, handling legacy grid coordinates
   */
  export function normalizePosition(pos: Position): Position {
    if (isLegacyGridCoordinate(pos)) {
      return gridToPixels(pos.x, pos.y);
    }
    return pos;
  }
}

/**
 * Convert CSS pixel values to coordinate system values
 */
export function cssToCoordinate(cssValue: number, containerSize: number, roomSize: number): number {
  return (cssValue / containerSize) * roomSize;
}

/**
 * Convert coordinate system values to CSS pixel values
 */
export function coordinateToCSS(coordinate: number, containerSize: number, roomSize: number): number {
  return (coordinate / roomSize) * containerSize;
}

/**
 * Utility for handling responsive coordinate conversion
 */
export class ResponsiveCoordinateConverter {
  constructor(
    private containerWidth: number,
    private containerHeight: number
  ) {}

  /**
   * Convert from room coordinates to CSS pixels
   */
  toCSS(position: Position): Position {
    return {
      x: coordinateToCSS(position.x, this.containerWidth, ROOM_WIDTH),
      y: coordinateToCSS(position.y, this.containerHeight, ROOM_HEIGHT)
    };
  }

  /**
   * Convert from CSS pixels to room coordinates
   */
  fromCSS(position: Position): Position {
    return {
      x: cssToCoordinate(position.x, this.containerWidth, ROOM_WIDTH),
      y: cssToCoordinate(position.y, this.containerHeight, ROOM_HEIGHT)
    };
  }

  /**
   * Convert size from room coordinates to CSS pixels
   */
  sizeToCSS(size: Size): Size {
    return {
      width: coordinateToCSS(size.width, this.containerWidth, ROOM_WIDTH),
      height: coordinateToCSS(size.height, this.containerHeight, ROOM_HEIGHT)
    };
  }

  /**
   * Convert size from CSS pixels to room coordinates
   */
  sizeFromCSS(size: Size): Size {
    return {
      width: cssToCoordinate(size.width, this.containerWidth, ROOM_WIDTH),
      height: cssToCoordinate(size.height, this.containerHeight, ROOM_HEIGHT)
    };
  }
}