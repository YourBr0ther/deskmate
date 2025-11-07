/**
 * Hook for managing multi-room navigation and transitions.
 *
 * Provides functionality for:
 * - Room-to-room navigation
 * - Doorway transitions
 * - Navigation status tracking
 * - Path preview and visualization
 */

import { useState, useEffect, useCallback, useRef } from 'react';

import { FloorPlan, Room, Doorway, AssistantLocation } from '../types/floorPlan';

export interface NavigationRequest {
  target_x: number;
  target_y: number;
  target_room_id?: string;
  assistant_id?: string;
}

export interface NavigationPath {
  x: number;
  y: number;
  room_id: string;
}

export interface RoomTransition {
  from_room: string;
  to_room: string;
  doorway_id: string;
  doorway_position: { x: number; y: number };
  requires_interaction: boolean;
}

export interface NavigationStatus {
  active: boolean;
  navigation_id?: string;
  current_step?: number;
  total_steps?: number;
  target_position?: { x: number; y: number };
  target_room_id?: string;
  estimated_remaining?: number;
  user_initiated?: boolean;
}

export interface PathPreview {
  success: boolean;
  path: NavigationPath[];
  room_transitions: RoomTransition[];
  doorways_to_open: string[];
  estimated_duration: number;
  total_distance: number;
  waypoint_count: number;
}

interface UseRoomNavigationOptions {
  assistantId?: string;
  autoRefreshInterval?: number;
  onRoomTransition?: (fromRoom: string, toRoom: string) => void;
  onNavigationComplete?: (targetRoom: string) => void;
  onNavigationError?: (error: string) => void;
}

export const useRoomNavigation = (options: UseRoomNavigationOptions = {}) => {
  const {
    assistantId = 'default',
    autoRefreshInterval = 1000,
    onRoomTransition,
    onNavigationComplete,
    onNavigationError
  } = options;

  // State
  const [navigationStatus, setNavigationStatus] = useState<NavigationStatus>({ active: false });
  const [currentPath, setCurrentPath] = useState<NavigationPath[]>([]);
  const [roomTransitions, setRoomTransitions] = useState<RoomTransition[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [assistantPosition, setAssistantLocation] = useState<AssistantLocation | null>(null);

  // Refs for cleanup
  const statusPollingRef = useRef<NodeJS.Timeout | null>(null);
  const lastRoomRef = useRef<string | null>(null);

  // API Base URL
  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Helper function for API calls
  const apiCall = useCallback(async (endpoint: string, options: RequestInit = {}) => {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }, [API_BASE]);

  // Start navigation to position
  const navigateToPosition = useCallback(async (request: NavigationRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiCall('/rooms/navigate', {
        method: 'POST',
        body: JSON.stringify({
          ...request,
          assistant_id: assistantId,
        }),
      });

      if (response.success) {
        setCurrentPath(response.path || []);
        setRoomTransitions(response.room_transitions || []);

        // Start polling navigation status
        startStatusPolling();

        return {
          success: true,
          navigationId: response.navigation_id,
          estimatedDuration: response.estimated_duration,
          totalDistance: response.total_distance,
        };
      } else {
        throw new Error(response.error || 'Navigation failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Navigation failed';
      setError(errorMessage);
      onNavigationError?.(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  }, [assistantId, apiCall, onNavigationError]);

  // Navigate to room (center of room)
  const navigateToRoom = useCallback(async (roomId: string, rooms: Room[]) => {
    const targetRoom = rooms.find(room => room.id === roomId);
    if (!targetRoom) {
      const error = `Room ${roomId} not found`;
      setError(error);
      return { success: false, error };
    }

    // Calculate center of room
    const centerX = targetRoom.bounds.x + targetRoom.bounds.width / 2;
    const centerY = targetRoom.bounds.y + targetRoom.bounds.height / 2;

    return navigateToPosition({
      target_x: centerX,
      target_y: centerY,
      target_room_id: roomId,
    });
  }, [navigateToPosition]);

  // Preview path without executing
  const previewPath = useCallback(async (request: NavigationRequest): Promise<PathPreview | null> => {
    try {
      const response = await apiCall('/rooms/pathfind/preview', {
        method: 'POST',
        body: JSON.stringify({
          ...request,
          assistant_id: assistantId,
        }),
      });

      return response;
    } catch (err) {
      console.error('Error previewing path:', err);
      return null;
    }
  }, [assistantId, apiCall]);

  // Cancel active navigation
  const cancelNavigation = useCallback(async () => {
    if (!navigationStatus.navigation_id) {
      return { success: false, error: 'No active navigation to cancel' };
    }

    try {
      const response = await apiCall(`/rooms/navigation/cancel/${navigationStatus.navigation_id}`, {
        method: 'POST',
      });

      if (response.success) {
        stopStatusPolling();
        setNavigationStatus({ active: false });
        setCurrentPath([]);
        setRoomTransitions([]);
      }

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Cancel failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  }, [navigationStatus.navigation_id, apiCall]);

  // Get assistant position
  const refreshAssistantLocation = useCallback(async () => {
    try {
      const response = await apiCall(`/rooms/assistant/position/${assistantId}`);
      setAssistantLocation(response);
      return response;
    } catch (err) {
      console.error('Error getting assistant position:', err);
      return null;
    }
  }, [assistantId, apiCall]);

  // Start polling navigation status
  const startStatusPolling = useCallback(() => {
    if (statusPollingRef.current) {
      clearInterval(statusPollingRef.current);
    }

    statusPollingRef.current = setInterval(async () => {
      try {
        const response = await apiCall(`/rooms/navigation/status/${assistantId}`);
        setNavigationStatus(response);

        // Also refresh assistant position
        const position = await refreshAssistantLocation();

        // Check for room transitions
        if (position?.room_id && lastRoomRef.current && position.room_id !== lastRoomRef.current) {
          onRoomTransition?.(lastRoomRef.current, position.room_id);
        }
        lastRoomRef.current = position?.room_id || null;

        // Stop polling if navigation is complete
        if (!response.active) {
          stopStatusPolling();
          if (lastRoomRef.current) {
            onNavigationComplete?.(lastRoomRef.current);
          }
        }
      } catch (err) {
        console.error('Error polling navigation status:', err);
        stopStatusPolling();
      }
    }, autoRefreshInterval);
  }, [assistantId, apiCall, autoRefreshInterval, refreshAssistantLocation, onRoomTransition, onNavigationComplete]);

  // Stop polling navigation status
  const stopStatusPolling = useCallback(() => {
    if (statusPollingRef.current) {
      clearInterval(statusPollingRef.current);
      statusPollingRef.current = null;
    }
  }, []);

  // Get progress percentage
  const getNavigationProgress = useCallback(() => {
    if (!navigationStatus.active || !navigationStatus.total_steps) {
      return 0;
    }
    return Math.min(100, ((navigationStatus.current_step || 0) / navigationStatus.total_steps) * 100);
  }, [navigationStatus]);

  // Check if assistant is near doorway
  const checkDoorwayProximity = useCallback((
    assistantPos: { x: number; y: number },
    doorways: Doorway[],
    threshold: number = 50
  ) => {
    for (const doorway of doorways) {
      const doorwayPos = doorway.world_position;
      if (!doorwayPos) continue;

      const distance = Math.sqrt(
        Math.pow(assistantPos.x - doorwayPos.x, 2) +
        Math.pow(assistantPos.y - doorwayPos.y, 2)
      );

      if (distance <= threshold) {
        return {
          doorway,
          distance,
          canTransition: doorway.accessibility?.is_accessible && doorway.properties.door_state !== 'locked'
        };
      }
    }
    return null;
  }, []);

  // Initialize - get assistant position
  useEffect(() => {
    refreshAssistantLocation();
  }, [refreshAssistantLocation]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStatusPolling();
    };
  }, [stopStatusPolling]);

  return {
    // State
    navigationStatus,
    currentPath,
    roomTransitions,
    isLoading,
    error,
    assistantPosition,

    // Actions
    navigateToPosition,
    navigateToRoom,
    previewPath,
    cancelNavigation,
    refreshAssistantLocation,

    // Utilities
    getNavigationProgress,
    checkDoorwayProximity,
    isNavigating: navigationStatus.active,

    // Manual control
    startStatusPolling,
    stopStatusPolling,
  };
};