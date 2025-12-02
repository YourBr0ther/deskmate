/**
 * Floor plan container component.
 *
 * Manages floor plan state, data fetching, and coordinates between
 * the top-down renderer and the rest of the application.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';

import TopDownRenderer from './TopDownRenderer';
import { useDeviceDetection } from '../../hooks/useDeviceDetection';
import { useChatStore } from '../../stores/chatStore';
import { useSpatialStore } from '../../stores/spatialStore';
import { FloorPlan, Assistant as FloorPlanAssistant, Position } from '../../types/floorPlan';
import { logger } from '../../utils/logger';


interface FloorPlanContainerProps {
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Main floor plan container component.
 */
export const FloorPlanContainer: React.FC<FloorPlanContainerProps> = ({
  className = '',
  style = {}
}) => {
  const deviceInfo = useDeviceDetection();
  const { sendAssistantMove, isConnected } = useChatStore();

  // Get state from spatialStore
  const currentFloorPlan = useSpatialStore((state) => state.floorPlan.currentFloorPlan);
  const selectedFloorPlanId = useSpatialStore((state) => state.floorPlan.selectedFloorPlanId);
  const spatialAssistant = useSpatialStore((state) => state.assistant);
  const selectedObjectId = useSpatialStore((state) => state.ui.selectedObjectId);
  const isLoading = useSpatialStore((state) => state.ui.isLoading);
  const error = useSpatialStore((state) => state.ui.error);

  // Get actions from spatialStore
  const selectObject = useSpatialStore((state) => state.selectObject);
  const setAssistantPosition = useSpatialStore((state) => state.setAssistantPosition);
  const setObjectPosition = useSpatialStore((state) => state.setObjectPosition);
  const setCurrentFloorPlan = useSpatialStore((state) => state.setCurrentFloorPlan);

  // Storage placement state
  const isStoragePlacementActive = useSpatialStore((state) => state.ui.isStoragePlacementActive);
  const selectedStorageItemId = useSpatialStore((state) => state.ui.selectedStorageItemId);
  const clearStoragePlacement = useSpatialStore((state) => state.clearStoragePlacement);
  const placeStorageItem = useSpatialStore((state) => state.placeStorageItem);

  // Adapt spatialStore assistant to FloorPlan Assistant format for TopDownRenderer
  const assistant: FloorPlanAssistant | null = useMemo(() => {
    if (!spatialAssistant) return null;

    // Map current_action string to valid AssistantAction
    const validActions = ['idle', 'walking', 'sitting', 'talking', 'interacting'] as const;
    type AssistantAction = typeof validActions[number];
    const action: AssistantAction = validActions.includes(spatialAssistant.current_action as AssistantAction)
      ? spatialAssistant.current_action as AssistantAction
      : 'idle';

    // Map mood to valid AssistantMood (floorPlan types)
    const validMoods = ['happy', 'sad', 'neutral', 'excited', 'tired', 'confused', 'focused'] as const;
    type AssistantMood = typeof validMoods[number];
    const moodMap: Record<string, AssistantMood> = {
      happy: 'happy',
      neutral: 'neutral',
      tired: 'tired',
      focused: 'focused',
      curious: 'neutral', // Map 'curious' to 'neutral' as it's not in floorPlan types
    };
    const mood: AssistantMood = moodMap[spatialAssistant.mood] || 'neutral';

    return {
      id: spatialAssistant.id,
      location: {
        position: spatialAssistant.position,
        facing: spatialAssistant.facing || 'right',
        facing_angle: 0
      },
      status: {
        mood,
        action,
        energy_level: spatialAssistant.energy_level,
        mode: spatialAssistant.status === 'active' ? 'active' : 'idle'
      }
    };
  }, [spatialAssistant]);

  // Wrapper functions to match old API
  const updateAssistantPosition = useCallback((position: Position) => {
    setAssistantPosition(position);
  }, [setAssistantPosition]);

  const updateFurniturePosition = useCallback((objectId: string, position: Position) => {
    setObjectPosition(objectId, position);
  }, [setObjectPosition]);

  const placeFromStorage = useCallback(async (itemId: string, position: Position) => {
    await placeStorageItem(itemId, position);
    return true;
  }, [placeStorageItem]);

  // Helper function to create default floor plan
  const createDefaultFloorPlan = async (): Promise<FloorPlan> => {
    // Try to create a default floor plan via API
    const response = await fetch('/api/floor-plans/create-default', {
      method: 'POST'
    });

    if (response.ok) {
      return await response.json();
    }

    // Fallback to basic floor plan if API fails
    return {
      id: 'default',
      name: 'Default Room',
      description: 'A simple room layout',
      category: 'studio',
      dimensions: {
        width: 1920,
        height: 480,
        scale: 1.0,
        units: 'pixels'
      },
      styling: {
        background_color: '#F9FAFB',
        wall_color: '#374151',
        wall_thickness: 8
      },
      rooms: [],
      walls: [],
      doorways: [],
      furniture: []
    };
  };

  // Load floor plan data on mount
  useEffect(() => {
    loadFloorPlanData();
  }, []);

  // Reload floor plan data when selectedFloorPlanId changes (from FloorPlanSelector)
  useEffect(() => {
    if (selectedFloorPlanId && (!currentFloorPlan || currentFloorPlan.id !== selectedFloorPlanId)) {
      logger.debug('Floor plan selection changed, reloading:', selectedFloorPlanId);
      loadFloorPlanData(true); // Force reload
    }
  }, [selectedFloorPlanId]);

  const loadFloorPlanData = async (forceReload = false) => {
    if (currentFloorPlan && !forceReload) return; // Already have a floor plan

    try {
      logger.debug('Loading floor plan data...');

      // Fetch floor plan from correct API endpoint
      const floorPlanResponse = await fetch('/api/floor-plans/current');

      if (floorPlanResponse.ok) {
        const floorPlanData = await floorPlanResponse.json();
        logger.debug('Loaded floor plan data:', floorPlanData);
        setCurrentFloorPlan(floorPlanData);
      } else if (floorPlanResponse.status === 404) {
        logger.debug('No floor plan found, creating default');
        // No floor plan exists yet, use default
        const defaultFloorPlan = await createDefaultFloorPlan();
        setCurrentFloorPlan(defaultFloorPlan);
      } else {
        throw new Error(`Failed to load floor plan: ${floorPlanResponse.statusText}`);
      }

      // Load assistant state from API
      const assistantResponse = await fetch('/api/assistant/state');
      if (assistantResponse.ok) {
        const assistantData = await assistantResponse.json();
        logger.debug('Loaded assistant data:', assistantData);
        // Update assistant state through the store - correct data structure
        updateAssistantPosition({
          x: assistantData.position.x,
          y: assistantData.position.y
        });
      } else {
        logger.warn('Failed to load assistant state, using default');
      }

    } catch (err) {
      logger.error('Failed to load floor plan:', err);
      // Try to create a default floor plan as fallback
      try {
        const defaultFloorPlan = await createDefaultFloorPlan();
        setCurrentFloorPlan(defaultFloorPlan);
        logger.info('Created fallback default floor plan');
      } catch (fallbackErr) {
        logger.error('Failed to create fallback floor plan:', fallbackErr);
      }
    }
  };

  // Handle object selection
  const handleObjectClick = useCallback((objectId: string) => {
    selectObject(selectedObjectId === objectId ? null : objectId);
    logger.debug('Object clicked:', objectId);
  }, [selectObject, selectedObjectId]);

  // Handle position clicks (for movement and storage placement)
  const handlePositionClick = useCallback(async (position: Position) => {
    logger.debug('Position clicked (pixels):', position);

    // Check if we're in storage placement mode
    if (isStoragePlacementActive && selectedStorageItemId) {
      logger.debug('Placing storage item:', selectedStorageItemId, 'at pixel coordinates:', position);

      // Use pixel coordinates for storage placement
      const success = await placeFromStorage(selectedStorageItemId, position);
      if (success) {
        clearStoragePlacement();
        logger.info('Storage item placed successfully at:', position);
      } else {
        logger.error('Failed to place storage item');
      }
      return;
    }

    // For assistant movement, use pixel coordinates directly
    // Backend should handle any necessary conversions
    if (isConnected) {
      sendAssistantMove(position.x, position.y);
    } else {
      logger.warn('Not connected to WebSocket - cannot send movement command');
    }
  }, [isConnected, sendAssistantMove, isStoragePlacementActive, selectedStorageItemId, placeFromStorage, clearStoragePlacement]);

  // Handle assistant movement (local updates)
  const handleAssistantMove = useCallback((position: Position) => {
    updateAssistantPosition(position);
  }, [updateAssistantPosition]);

  // Handle object movement (drag and drop)
  const handleObjectMove = useCallback((objectId: string, position: Position) => {
    updateFurniturePosition(objectId, position);
    logger.debug(`Furniture ${objectId} moved to (${position.x}, ${position.y})`);
  }, [updateFurniturePosition]);

  // Handle object interactions (right-click actions)
  const handleObjectInteract = useCallback(async (objectId: string, action: string) => {
    logger.debug(`Object interaction: ${objectId} - ${action}`);

    // Send interaction command to backend
    try {
      const response = await fetch(`/api/objects/${objectId}/interact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });

      if (response.ok) {
        const result = await response.json();
        logger.debug(`Interaction result:`, result);

        // If it's a sit action, update assistant position
        if (action === 'sit' && result.assistant_position) {
          updateAssistantPosition(result.assistant_position);
        }
      }
    } catch (error) {
      logger.error(`Failed to interact with object:`, error);
    }
  }, [updateAssistantPosition]);

  if (isLoading) {
    return (
      <div className="floor-plan-loading flex items-center justify-center w-full h-full bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading floor plan...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="floor-plan-error flex items-center justify-center w-full h-full bg-red-50">
        <div className="text-center p-8">
          <div className="text-red-600 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-red-800 mb-2">Floor Plan Error</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => loadFloorPlanData(true)}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!currentFloorPlan || !assistant) {
    return (
      <div className="floor-plan-empty flex items-center justify-center w-full h-full bg-gray-100">
        <p className="text-gray-500">No floor plan data available</p>
      </div>
    );
  }

  return (
    <div className={`floor-plan-container relative w-full h-full ${className}`} style={style}>
      <TopDownRenderer
        floorPlan={currentFloorPlan}
        assistant={assistant}
        selectedObject={selectedObjectId || undefined}
        onObjectClick={handleObjectClick}
        onObjectMove={handleObjectMove}
        onObjectInteract={handleObjectInteract}
        onPositionClick={handlePositionClick}
        onAssistantMove={handleAssistantMove}
        isStoragePlacementActive={isStoragePlacementActive}
        className="w-full h-full"
      />

      {/* Object info panel for selected objects */}
      {selectedObjectId && (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 max-w-sm z-10">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-800">
              {currentFloorPlan.furniture.find(f => f.id === selectedObjectId)?.name || 'Object'}
            </h3>
            <button
              onClick={() => selectObject(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
          <div className="text-sm text-gray-600 space-y-1">
            {(() => {
              const obj = currentFloorPlan.furniture.find(f => f.id === selectedObjectId);
              if (!obj) return null;
              return (
                <>
                  <p><strong>Type:</strong> {obj.type}</p>
                  <p><strong>Material:</strong> {obj.visual.material}</p>
                  <p><strong>Style:</strong> {obj.visual.style}</p>
                  <p><strong>Interactive:</strong> {obj.properties.interactive ? 'Yes' : 'No'}</p>
                </>
              );
            })()}
          </div>
        </div>
      )}

      {/* Development info overlay */}
      {process.env.NODE_ENV === 'development' && (
        <div className="absolute bottom-4 left-4 bg-black bg-opacity-75 text-white text-xs p-2 rounded z-10">
          <div>Floor Plan: {currentFloorPlan.name}</div>
          <div>Rooms: {currentFloorPlan.rooms.length}</div>
          <div>Furniture: {currentFloorPlan.furniture.length}</div>
          <div>Assistant: {assistant.location.position.x.toFixed(0)}, {assistant.location.position.y.toFixed(0)}</div>
          {selectedObjectId && <div>Selected: {selectedObjectId}</div>}
        </div>
      )}
    </div>
  );
};

export default FloorPlanContainer;