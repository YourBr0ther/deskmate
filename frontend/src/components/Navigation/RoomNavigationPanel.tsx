/**
 * Room Navigation Panel Component
 *
 * Provides controls for multi-room navigation including:
 * - Room list and quick navigation
 * - Navigation status and progress
 * - Doorway information
 * - Path preview and controls
 */

import React, { useState, useEffect } from 'react';

import { useRoomNavigation } from '../../hooks/useRoomNavigation';
import { Room, Doorway, FloorPlan } from '../../types/floorPlan';

interface RoomNavigationPanelProps {
  floorPlan: FloorPlan | null;
  rooms: Room[];
  doorways: Doorway[];
  currentRoomId: string | null;
  onRoomSelect: (roomId: string) => void;
  onNavigationStart: (roomId: string) => void;
  className?: string;
}

const RoomNavigationPanel: React.FC<RoomNavigationPanelProps> = ({
  floorPlan,
  rooms,
  doorways,
  currentRoomId,
  onRoomSelect,
  onNavigationStart,
  className = ''
}) => {
  const [selectedRoom, setSelectedRoom] = useState<string | null>(currentRoomId);
  const [showPathPreview, setShowPathPreview] = useState(false);

  const {
    navigationStatus,
    isLoading,
    error,
    assistantPosition,
    navigateToRoom,
    previewPath,
    cancelNavigation,
    getNavigationProgress,
    isNavigating
  } = useRoomNavigation({
    onRoomTransition: (fromRoom, toRoom) => {
      console.log(`Room transition: ${fromRoom} → ${toRoom}`);
      onRoomSelect(toRoom);
    },
    onNavigationComplete: (targetRoom) => {
      console.log(`Navigation completed to room: ${targetRoom}`);
    },
    onNavigationError: (errorMsg) => {
      console.error('Navigation error:', errorMsg);
    }
  });

  // Update selected room when current room changes
  useEffect(() => {
    setSelectedRoom(currentRoomId);
  }, [currentRoomId]);

  // Get room display information
  const getRoomInfo = (room: Room) => {
    const connectedRooms = doorways.filter(doorway =>
      doorway.connections.room_a === room.id || doorway.connections.room_b === room.id
    );

    return {
      ...room,
      connectionCount: connectedRooms.length,
      isAccessible: connectedRooms.some(d => d.accessibility?.is_accessible || false),
      isCurrent: room.id === currentRoomId
    };
  };

  // Handle room navigation
  const handleNavigateToRoom = async (roomId: string) => {
    if (roomId === currentRoomId) return;

    setShowPathPreview(false);
    const result = await navigateToRoom(roomId, rooms);

    if (result.success) {
      onNavigationStart(roomId);
    }
  };

  // Handle path preview
  const handlePreviewPath = async (roomId: string) => {
    if (roomId === currentRoomId) return;

    const targetRoom = rooms.find(r => r.id === roomId);
    if (!targetRoom) return;

    const centerX = targetRoom.bounds.x + targetRoom.bounds.width / 2;
    const centerY = targetRoom.bounds.y + targetRoom.bounds.height / 2;

    const preview = await previewPath({
      target_x: centerX,
      target_y: centerY,
      target_room_id: roomId
    });

    if (preview) {
      setShowPathPreview(true);
      // You could store and display the preview path here
    }
  };

  // Room type icons
  const getRoomIcon = (roomType: string) => {
    const icons = {
      living_room: '🛋️',
      bedroom: '🛏️',
      kitchen: '🍳',
      bathroom: '🚿',
      office: '💼',
      dining_room: '🍽️',
      studio: '🏠',
      meeting_room: '📅',
      break_room: '☕',
      workspace: '💻'
    };
    return icons[roomType as keyof typeof icons] || '📍';
  };

  // Navigation progress component
  const NavigationProgress = () => {
    if (!isNavigating) return null;

    const progress = getNavigationProgress();

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-blue-900">
            Navigating to {navigationStatus.target_room_id}
          </span>
          <button
            onClick={cancelNavigation}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Cancel
          </button>
        </div>

        <div className="w-full bg-blue-200 rounded-full h-2 mb-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="flex justify-between text-xs text-blue-700">
          <span>
            Step {navigationStatus.current_step || 0} of {navigationStatus.total_steps || 0}
          </span>
          {navigationStatus.estimated_remaining && (
            <span>
              {Math.ceil(navigationStatus.estimated_remaining)}s remaining
            </span>
          )}
        </div>
      </div>
    );
  };

  // Room list item component
  const RoomListItem = ({ room }: { room: Room }) => {
    const roomInfo = getRoomInfo(room);
    const isSelected = selectedRoom === room.id;
    const isCurrent = room.id === currentRoomId;

    return (
      <div
        className={`
          p-3 rounded-lg border cursor-pointer transition-all duration-200
          ${isCurrent
            ? 'bg-green-50 border-green-300 ring-2 ring-green-200'
            : isSelected
            ? 'bg-blue-50 border-blue-300'
            : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
          }
        `}
        onClick={() => setSelectedRoom(room.id)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{getRoomIcon(room.type)}</span>
            <div>
              <h4 className="font-medium text-gray-900">{room.name}</h4>
              <p className="text-xs text-gray-500">
                {roomInfo.connectionCount} connection{roomInfo.connectionCount !== 1 ? 's' : ''}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-1">
            {isCurrent && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Current
              </span>
            )}

            {!isCurrent && roomInfo.isAccessible && (
              <div className="flex space-x-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handlePreviewPath(room.id);
                  }}
                  className="px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded transition-colors"
                  title="Preview path"
                >
                  👁️
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleNavigateToRoom(room.id);
                  }}
                  disabled={isLoading || isNavigating}
                  className="px-2 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors disabled:opacity-50"
                  title="Navigate to room"
                >
                  Go
                </button>
              </div>
            )}

            {!roomInfo.isAccessible && (
              <span className="text-xs text-red-500" title="Not accessible">
                🚫
              </span>
            )}
          </div>
        </div>

        {isSelected && room.id !== currentRoomId && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <div className="flex justify-between text-xs text-gray-600">
              <span>
                {room.bounds.width}×{room.bounds.height} px
              </span>
              <span>
                Floor: {room.properties.floor_material}
              </span>
            </div>
          </div>
        )}
      </div>
    );
  };

  if (!floorPlan) {
    return (
      <div className={`bg-gray-100 p-4 rounded-lg ${className}`}>
        <p className="text-gray-500 text-center">No floor plan loaded</p>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">Room Navigation</h3>
        <div className="text-xs text-gray-500">
          {rooms.length} room{rooms.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Navigation progress */}
      <NavigationProgress />

      {/* Current position info */}
      {assistantPosition && (
        <div className="bg-gray-50 rounded-lg p-3 mb-4">
          <div className="text-xs text-gray-600 mb-1">Assistant Position</div>
          <div className="text-sm font-mono">
            ({Math.round(assistantPosition.position.x)}, {Math.round(assistantPosition.position.y)})
          </div>
          <div className="text-xs text-gray-500">
            Facing: {assistantPosition.facing}
            {isNavigating && (
              <span className="ml-2 text-blue-600">Moving...</span>
            )}
          </div>
        </div>
      )}

      {/* Room list */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {rooms.map(room => (
          <RoomListItem key={room.id} room={room} />
        ))}
      </div>

      {/* Floor plan info */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          <div>Floor Plan: {floorPlan.name}</div>
          <div>
            Dimensions: {floorPlan.dimensions.width}×{floorPlan.dimensions.height} px
          </div>
          <div>
            Scale: {floorPlan.dimensions.scale} px/{floorPlan.dimensions.units}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoomNavigationPanel;