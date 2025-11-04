/**
 * Coordinate conversion utilities for DeskMate.
 *
 * Handles conversion between the legacy grid coordinate system (64x16 cells)
 * and the new open-plan pixel coordinate system.
 */

import { Position } from '../types/room';

// Grid system constants (legacy)
export const GRID_CONSTANTS = {
  GRID_WIDTH: 64,
  GRID_HEIGHT: 16,
  CELL_WIDTH: 30,
  CELL_HEIGHT: 30,
  TOTAL_WIDTH: 64 * 30, // 1920px
  TOTAL_HEIGHT: 16 * 30, // 480px
} as const;

// Current floor plan constants (new system)
export const FLOOR_PLAN_CONSTANTS = {
  DEFAULT_WIDTH: 1300,
  DEFAULT_HEIGHT: 600,
} as const;

/**
 * Convert pixel coordinates to grid coordinates.
 * Used for backward compatibility with the grid-based backend.
 */
export function pixelToGrid(pixelPosition: Position, floorPlanDimensions?: { width: number; height: number }): Position {
  const floorWidth = floorPlanDimensions?.width || FLOOR_PLAN_CONSTANTS.DEFAULT_WIDTH;
  const floorHeight = floorPlanDimensions?.height || FLOOR_PLAN_CONSTANTS.DEFAULT_HEIGHT;

  // Convert pixel position to normalized coordinates (0-1)
  const normalizedX = Math.max(0, Math.min(1, pixelPosition.x / floorWidth));
  const normalizedY = Math.max(0, Math.min(1, pixelPosition.y / floorHeight));

  // Convert normalized coordinates to grid coordinates
  const gridX = Math.round(normalizedX * (GRID_CONSTANTS.GRID_WIDTH - 1));
  const gridY = Math.round(normalizedY * (GRID_CONSTANTS.GRID_HEIGHT - 1));

  return {
    x: Math.max(0, Math.min(GRID_CONSTANTS.GRID_WIDTH - 1, gridX)),
    y: Math.max(0, Math.min(GRID_CONSTANTS.GRID_HEIGHT - 1, gridY))
  };
}

/**
 * Convert grid coordinates to pixel coordinates.
 * Used when receiving updates from the grid-based backend.
 */
export function gridToPixel(gridPosition: Position, floorPlanDimensions?: { width: number; height: number }): Position {
  const floorWidth = floorPlanDimensions?.width || FLOOR_PLAN_CONSTANTS.DEFAULT_WIDTH;
  const floorHeight = floorPlanDimensions?.height || FLOOR_PLAN_CONSTANTS.DEFAULT_HEIGHT;

  // Convert grid coordinates to normalized coordinates (0-1)
  const normalizedX = gridPosition.x / (GRID_CONSTANTS.GRID_WIDTH - 1);
  const normalizedY = gridPosition.y / (GRID_CONSTANTS.GRID_HEIGHT - 1);

  // Convert normalized coordinates to pixel coordinates
  return {
    x: normalizedX * floorWidth,
    y: normalizedY * floorHeight
  };
}

/**
 * Check if a position appears to be in grid coordinates.
 * Grid coordinates are typically small integers (0-63, 0-15).
 */
export function isGridCoordinate(position: Position): boolean {
  return (
    Number.isInteger(position.x) &&
    Number.isInteger(position.y) &&
    position.x >= 0 &&
    position.x < GRID_CONSTANTS.GRID_WIDTH &&
    position.y >= 0 &&
    position.y < GRID_CONSTANTS.GRID_HEIGHT
  );
}

/**
 * Check if a position appears to be in pixel coordinates.
 * Pixel coordinates are typically larger numbers.
 */
export function isPixelCoordinate(position: Position): boolean {
  return !isGridCoordinate(position);
}

/**
 * Auto-detect coordinate system and convert to grid if needed.
 * This is useful for handling coordinates from unknown sources.
 */
export function ensureGridCoordinates(position: Position, floorPlanDimensions?: { width: number; height: number }): Position {
  if (isGridCoordinate(position)) {
    return position;
  }
  return pixelToGrid(position, floorPlanDimensions);
}

/**
 * Auto-detect coordinate system and convert to pixels if needed.
 * This is useful for handling coordinates from unknown sources.
 */
export function ensurePixelCoordinates(position: Position, floorPlanDimensions?: { width: number; height: number }): Position {
  if (isPixelCoordinate(position)) {
    return position;
  }
  return gridToPixel(position, floorPlanDimensions);
}