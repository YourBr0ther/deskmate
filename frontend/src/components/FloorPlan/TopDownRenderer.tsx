/**
 * Top-down floor plan renderer component.
 *
 * Renders architectural-style floor plans using SVG with rooms, walls,
 * doorways, furniture, and the assistant in a top-down perspective.
 * Includes multi-room navigation support with path visualization.
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';

import { useRoomNavigation, NavigationPath } from '../../hooks/useRoomNavigation';
import { useSettingsStore } from '../../stores/settingsStore';
import { FloorPlan, Room, Wall, Doorway, FurnitureItem, Assistant, Position } from '../../types/floorPlan';
import { logger } from '../../utils/logger';

// Local component types
interface Size {
  width: number;
  height: number;
}

interface TopDownRendererProps {
  floorPlan: FloorPlan;
  assistant: Assistant;
  selectedObject?: string;
  onObjectClick?: (objectId: string) => void;
  onObjectMove?: (objectId: string, position: Position) => void;
  onObjectInteract?: (objectId: string, action: string) => void;
  onPositionClick?: (position: Position) => void;
  onAssistantMove?: (position: Position) => void;
  onDoorwayClick?: (doorwayId: string) => void;
  onRoomClick?: (roomId: string) => void;
  showNavigationPath?: boolean;
  showDoorwayHighlights?: boolean;
  enableRoomNavigation?: boolean;
  isStoragePlacementActive?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Top-down SVG floor plan renderer.
 */
export const TopDownRenderer: React.FC<TopDownRendererProps> = ({
  floorPlan,
  assistant,
  selectedObject,
  onObjectClick,
  onObjectMove,
  onObjectInteract,
  onPositionClick,
  onAssistantMove,
  onDoorwayClick,
  onRoomClick,
  showNavigationPath = true,
  showDoorwayHighlights = true,
  enableRoomNavigation = true,
  isStoragePlacementActive = false,
  className = '',
  style = {}
}) => {
  const { display } = useSettingsStore();
  const svgRef = useRef<SVGSVGElement>(null);
  const [viewBox, setViewBox] = useState({
    x: 0,
    y: 0,
    width: floorPlan.dimensions.width,
    height: floorPlan.dimensions.height
  });
  const [scale, setScale] = useState(1);
  const [hoveredObject, setHoveredObject] = useState<string | null>(null);
  const [hoveredRoom, setHoveredRoom] = useState<string | null>(null);

  // Drag and drop state
  const [isDragging, setIsDragging] = useState(false);
  const [draggedObject, setDraggedObject] = useState<string | null>(null);
  const [dragStartPosition, setDragStartPosition] = useState<Position | null>(null);
  const [dragCurrentPosition, setDragCurrentPosition] = useState<Position | null>(null);
  const [dragValid, setDragValid] = useState(true);

  // Navigation hook
  const {
    currentPath,
    roomTransitions,
    isNavigating,
    navigationStatus,
    assistantPosition,
    navigateToPosition,
    previewPath,
    checkDoorwayProximity
  } = useRoomNavigation({
    onRoomTransition: (fromRoom, toRoom) => {
      logger.debug(`Room transition: ${fromRoom} → ${toRoom}`);
    }
  });

  // Calculate viewBox to fit content with padding
  useEffect(() => {
    const padding = 50;
    setViewBox({
      x: -padding,
      y: -padding,
      width: floorPlan.dimensions.width + (padding * 2),
      height: floorPlan.dimensions.height + (padding * 2)
    });
  }, [floorPlan.dimensions]);

  // Handle SVG click for movement
  const handleSVGClick = useCallback((event: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;

    const rect = svgRef.current.getBoundingClientRect();
    const scaleX = viewBox.width / rect.width;
    const scaleY = viewBox.height / rect.height;

    const x = (event.clientX - rect.left) * scaleX + viewBox.x;
    const y = (event.clientY - rect.top) * scaleY + viewBox.y;

    // If navigation is enabled, navigate to clicked position
    if (enableRoomNavigation) {
      navigateToPosition({ target_x: x, target_y: y });
    }

    onPositionClick?.({ x, y });
  }, [viewBox, onPositionClick, enableRoomNavigation, navigateToPosition]);

  // Handle room click
  const handleRoomClick = useCallback((event: React.MouseEvent, roomId: string) => {
    // In storage placement mode, all clicks should go to position handler
    if (isStoragePlacementActive) {
      return; // Let event bubble to SVG click handler
    }

    event.stopPropagation();
    if (enableRoomNavigation) {
      onRoomClick?.(roomId);
    }
  }, [enableRoomNavigation, onRoomClick, isStoragePlacementActive]);

  // Handle doorway click
  const handleDoorwayClick = useCallback((event: React.MouseEvent, doorwayId: string) => {
    // In storage placement mode, all clicks should go to position handler
    if (isStoragePlacementActive) {
      return; // Let event bubble to SVG click handler
    }

    event.stopPropagation();
    onDoorwayClick?.(doorwayId);
  }, [onDoorwayClick, isStoragePlacementActive]);

  // Render room backgrounds
  const renderRooms = () => {
    return floorPlan.rooms.map((room) => {
      const isHovered = hoveredRoom === room.id;
      const isCurrentRoom = assistantPosition?.room_id === room.id;

      return (
        <g key={`room-${room.id}`} className="room-group">
          {/* Room floor */}
          <rect
            x={room.bounds.x}
            y={room.bounds.y}
            width={room.bounds.width}
            height={room.bounds.height}
            fill={room.properties.floor_color}
            stroke={isCurrentRoom ? '#10B981' : isHovered ? '#3B82F6' : 'none'}
            strokeWidth={isCurrentRoom ? 3 : isHovered ? 2 : 0}
            strokeDasharray={isCurrentRoom ? '8,4' : 'none'}
            className={`room-floor ${enableRoomNavigation ? 'cursor-pointer' : ''} transition-all`}
            onClick={(e) => enableRoomNavigation && handleRoomClick(e, room.id)}
            onMouseEnter={() => enableRoomNavigation && setHoveredRoom(room.id)}
            onMouseLeave={() => setHoveredRoom(null)}
          />

        {/* Room material texture (simplified pattern) */}
        {room.properties.floor_material === 'carpet' && (
          <rect
            x={room.bounds.x}
            y={room.bounds.y}
            width={room.bounds.width}
            height={room.bounds.height}
            fill="url(#carpet-pattern)"
            opacity="0.3"
          />
        )}

        {/* Room label */}
        <text
          x={room.bounds.x + room.bounds.width / 2}
          y={room.bounds.y + room.bounds.height / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          className="room-label text-sm font-medium fill-gray-600"
          fontSize="14"
          fontFamily="system-ui, -apple-system, sans-serif"
          style={{ pointerEvents: 'none' }}
        >
          {room.name}
        </text>

        {/* Room navigation hint */}
        {enableRoomNavigation && isHovered && !isCurrentRoom && (
          <text
            x={room.bounds.x + room.bounds.width / 2}
            y={room.bounds.y + room.bounds.height / 2 + 20}
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-xs font-medium fill-blue-600"
            fontSize="10"
            style={{ pointerEvents: 'none' }}
          >
            Click to navigate
          </text>
        )}
      </g>
      );
    });
  };

  // Render walls
  const renderWalls = () => {
    return floorPlan.walls.map((wall) => (
      <line
        key={`wall-${wall.id}`}
        x1={wall.geometry.start.x}
        y1={wall.geometry.start.y}
        x2={wall.geometry.end.x}
        y2={wall.geometry.end.y}
        stroke={wall.properties.color}
        strokeWidth={wall.properties.thickness}
        strokeLinecap="round"
        className={`wall wall-${wall.properties.type}`}
      />
    ));
  };

  // Render doorways
  const renderDoorways = () => {
    return floorPlan.doorways.map((doorway) => {
      if (!doorway.world_position) return null;

      const { x, y } = doorway.world_position;
      const width = doorway.position.width;

      return (
        <g
          key={`doorway-${doorway.id}`}
          className={`doorway-group ${onDoorwayClick ? 'cursor-pointer' : ''}`}
          onClick={(e) => handleDoorwayClick(e, doorway.id)}
        >
          {/* Doorway opening (white space in wall) */}
          <rect
            x={x - width / 2}
            y={y - 4}
            width={width}
            height={8}
            fill="white"
            stroke="none"
          />

          {/* Door indicator if it's a door type */}
          {doorway.properties.type === 'door' && (
            <g>
              <rect
                x={x - width / 2}
                y={y - 2}
                width={width}
                height={4}
                fill="#8B4513"
                stroke="#654321"
                strokeWidth="1"
              />
              {/* Door handle */}
              <circle
                cx={x - width / 2 + 8}
                cy={y}
                r="1.5"
                fill="#FFD700"
              />
            </g>
          )}

          {/* Archway indicator */}
          {doorway.properties.type === 'archway' && (
            <path
              d={`M ${x - width / 2} ${y} A ${width / 2} ${width / 4} 0 0 1 ${x + width / 2} ${y}`}
              fill="none"
              stroke="#666"
              strokeWidth="2"
              strokeDasharray="2,2"
            />
          )}
        </g>
      );
    });
  };

  // Check if position is valid for furniture placement
  const isValidFurniturePosition = useCallback((furnitureId: string, position: Position, width: number, height: number) => {
    // Check bounds
    if (position.x < 0 || position.y < 0 ||
        position.x + width > floorPlan.dimensions.width ||
        position.y + height > floorPlan.dimensions.height) {
      return false;
    }

    // Check collision with other furniture
    for (const item of floorPlan.furniture) {
      if (item.id === furnitureId) continue; // Skip self
      if (!item.properties.solid) continue; // Skip non-solid items

      const itemRight = item.position.x + item.geometry.width;
      const itemBottom = item.position.y + item.geometry.height;
      const newRight = position.x + width;
      const newBottom = position.y + height;

      // Check for overlap
      if (!(position.x >= itemRight || newRight <= item.position.x ||
            position.y >= itemBottom || newBottom <= item.position.y)) {
        return false;
      }
    }

    return true;
  }, [floorPlan]);

  // Handle drag start
  const handleDragStart = useCallback((e: React.MouseEvent, item: FurnitureItem) => {
    if (!item.properties.movable) return;

    // In storage placement mode, disable furniture dragging
    if (isStoragePlacementActive) {
      return; // Let event bubble to SVG click handler
    }

    e.stopPropagation();
    setDraggedObject(item.id);
    setIsDragging(true);
    setDragStartPosition(item.position);
    setDragCurrentPosition(item.position);
    logger.debug(`Started dragging ${item.name}`);
  }, [isStoragePlacementActive]);

  // Handle drag move
  const handleDragMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging || !draggedObject) return;

    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;

    const scaleX = floorPlan.dimensions.width / rect.width;
    const scaleY = floorPlan.dimensions.height / rect.height;

    const newPosition: Position = {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY
    };

    // Snap to grid (optional)
    const gridSize = 10;
    newPosition.x = Math.round(newPosition.x / gridSize) * gridSize;
    newPosition.y = Math.round(newPosition.y / gridSize) * gridSize;

    const draggedItem = floorPlan.furniture.find(f => f.id === draggedObject);
    if (draggedItem) {
      const valid = isValidFurniturePosition(
        draggedObject,
        newPosition,
        draggedItem.geometry.width,
        draggedItem.geometry.height
      );
      setDragValid(valid);
      setDragCurrentPosition(newPosition);
    }
  }, [isDragging, draggedObject, floorPlan, isValidFurniturePosition]);

  // Handle drag end
  const handleDragEnd = useCallback((e: React.MouseEvent) => {
    if (!isDragging || !draggedObject || !dragCurrentPosition) return;

    // In storage placement mode, cancel any drag operations
    if (isStoragePlacementActive) {
      // Reset drag state without applying changes
      setIsDragging(false);
      setDraggedObject(null);
      setDragStartPosition(null);
      setDragCurrentPosition(null);
      setDragValid(true);
      return;
    }

    e.stopPropagation();

    const draggedItem = floorPlan.furniture.find(f => f.id === draggedObject);
    if (draggedItem && dragValid && onObjectMove) {
      // Update furniture position in store
      onObjectMove(draggedObject, dragCurrentPosition);
      logger.debug(`Moved ${draggedItem.name} to (${dragCurrentPosition.x}, ${dragCurrentPosition.y})`);
    } else {
      logger.debug('Invalid position - reverting');
    }

    // Reset drag state
    setIsDragging(false);
    setDraggedObject(null);
    setDragStartPosition(null);
    setDragCurrentPosition(null);
    setDragValid(true);
  }, [isDragging, draggedObject, dragCurrentPosition, dragValid, floorPlan, onObjectMove, isStoragePlacementActive]);

  // Render furniture
  const renderFurniture = () => {
    return floorPlan.furniture.map((item) => {
      const isSelected = selectedObject === item.id;
      const isHovered = hoveredObject === item.id;
      const isDragged = draggedObject === item.id;

      // Use drag position if currently dragging this item
      const position = isDragged && dragCurrentPosition ? dragCurrentPosition : item.position;
      const { x, y } = position;
      let { width, height } = item.geometry;

      // Adjust size based on display mode
      if (display.gridDisplayMode === 'compact') {
        width = Math.max(width * 0.8, 20);
        height = Math.max(height * 0.8, 20);
      } else if (display.gridDisplayMode === 'detailed') {
        width = Math.min(width * 1.2, 80);
        height = Math.min(height * 1.2, 80);
      }

      return (
        <g
          key={`furniture-${item.id}`}
          className={`furniture-group ${item.properties.movable ? 'cursor-move' : 'cursor-pointer'} ${isDragged ? 'dragging' : ''}`}
          onClick={(e) => {
            // In storage placement mode, all clicks should go to position handler
            if (isStoragePlacementActive) {
              return; // Let event bubble to SVG click handler
            }

            e.stopPropagation();
            if (!isDragging) {
              onObjectClick?.(item.id);
            }
          }}
          onMouseDown={(e) => handleDragStart(e, item)}
          onMouseEnter={() => !isDragging && setHoveredObject(item.id)}
          onMouseLeave={() => !isDragging && setHoveredObject(null)}
          onContextMenu={(e) => {
            e.preventDefault();
            if (item.properties.interactive && onObjectInteract) {
              // Handle right-click for object interaction
              if (item.type === 'furniture' && (item.id === 'bed' || item.id === 'sofa')) {
                onObjectInteract(item.id, 'sit');
              } else if (item.id === 'refrigerator') {
                onObjectInteract(item.id, 'open');
              } else if (item.name.toLowerCase().includes('lamp')) {
                onObjectInteract(item.id, 'toggle_power');
              }
            }
          }}
          style={{
            opacity: isDragged ? 0.7 : 1,
            cursor: item.properties.movable ? 'move' : 'pointer'
          }}
        >
          {/* Furniture shape */}
          <rect
            x={x}
            y={y}
            width={width}
            height={height}
            fill={isDragged && !dragValid ? '#EF4444' : item.visual.color}
            stroke={isDragged ? (dragValid ? '#10B981' : '#EF4444') : isSelected ? '#3B82F6' : isHovered ? '#6B7280' : '#9CA3AF'}
            strokeWidth={isDragged ? 3 : isSelected ? 3 : isHovered ? 2 : 1}
            rx="2"
            ry="2"
            className="furniture-shape"
            style={{
              filter: isHovered
                ? display.highQualityRendering
                  ? 'drop-shadow(0 4px 8px rgba(0,0,0,0.15)) drop-shadow(0 2px 4px rgba(0,0,0,0.1))'
                  : 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))'
                : display.highQualityRendering
                  ? 'drop-shadow(0 1px 2px rgba(0,0,0,0.05))'
                  : undefined
            }}
          />

          {/* Furniture icon/label - varies by display mode */}
          <text
            x={x + width / 2}
            y={y + height / 2}
            textAnchor="middle"
            dominantBaseline="middle"
            className="furniture-label text-xs fill-white"
            fontSize={display.gridDisplayMode === 'detailed' ? '12' : display.gridDisplayMode === 'compact' ? '8' : '10'}
            fontFamily="system-ui, -apple-system, sans-serif"
            fontWeight="500"
          >
            {display.gridDisplayMode === 'compact' ? getFurnitureIcon(item.type, item.name).split(' ')[0] : getFurnitureIcon(item.type, item.name)}
          </text>

          {/* Detailed mode: Show additional info */}
          {display.gridDisplayMode === 'detailed' && (
            <text
              x={x + width / 2}
              y={y + height / 2 + 15}
              textAnchor="middle"
              dominantBaseline="middle"
              className="furniture-detail text-xs fill-gray-300"
              fontSize="8"
              fontFamily="system-ui, -apple-system, sans-serif"
            >
              {item.name}
            </text>
          )}

          {/* Selection indicator */}
          {isSelected && (
            <rect
              x={x - 2}
              y={y - 2}
              width={width + 4}
              height={height + 4}
              fill="none"
              stroke="#3B82F6"
              strokeWidth="2"
              strokeDasharray="4,2"
              rx="4"
              ry="4"
              opacity="0.8"
            />
          )}
        </g>
      );
    });
  };

  // Render assistant
  const renderAssistant = () => {
    const { x, y } = assistant.location.position;
    const facingAngle = assistant.location.facing_angle;

    return (
      <g className="assistant-group">
        {/* Assistant body (circle) */}
        <circle
          cx={x}
          cy={y}
          r="12"
          fill={getAssistantColor(assistant.status.mood)}
          stroke="#FFFFFF"
          strokeWidth="2"
          className="assistant-body"
          style={{
            filter: display.highQualityRendering
              ? 'drop-shadow(0 4px 12px rgba(0,0,0,0.25)) drop-shadow(0 2px 6px rgba(0,0,0,0.15))'
              : 'drop-shadow(0 2px 6px rgba(0,0,0,0.2))'
          }}
        />

        {/* Facing direction indicator */}
        <path
          d={`M ${x} ${y} L ${x + Math.cos((facingAngle - 90) * Math.PI / 180) * 8} ${y + Math.sin((facingAngle - 90) * Math.PI / 180) * 8}`}
          stroke="#FFFFFF"
          strokeWidth="2"
          strokeLinecap="round"
        />

        {/* Assistant emoji/expression */}
        <text
          x={x}
          y={y + 1}
          textAnchor="middle"
          dominantBaseline="middle"
          className="assistant-face"
          fontSize="16"
        >
          {getAssistantEmoji(assistant.status.mood)}
        </text>

        {/* Status indicator */}
        <circle
          cx={x + 8}
          cy={y - 8}
          r="3"
          fill={assistant.status.action === 'idle' ? '#10B981' : '#F59E0B'}
          stroke="#FFFFFF"
          strokeWidth="1"
        />
      </g>
    );
  };

  // Helper function to get furniture icon
  const getFurnitureIcon = (type: string, name: string): string => {
    const iconMap: Record<string, string> = {
      sofa: '🛋️',
      couch: '🛋️',
      bed: '🛏️',
      table: '📋',
      desk: '💻',
      chair: '💺',
      refrigerator: '❄️',
      stove: '🔥',
      lamp: '💡',
      tv: '📺',
      bookshelf: '📚'
    };

    const key = name.toLowerCase();
    for (const [keyword, icon] of Object.entries(iconMap)) {
      if (key.includes(keyword)) return icon;
    }

    return type === 'furniture' ? '🪑' : type === 'appliance' ? '⚡' : '📦';
  };

  // Helper function to get assistant color based on mood
  const getAssistantColor = (mood: string): string => {
    const moodColors: Record<string, string> = {
      happy: '#10B981',
      excited: '#F59E0B',
      neutral: '#6B7280',
      sad: '#6366F1',
      tired: '#8B5CF6'
    };
    return moodColors[mood] || '#6B7280';
  };

  // Helper function to get assistant emoji
  const getAssistantEmoji = (mood: string): string => {
    const moodEmojis: Record<string, string> = {
      happy: '😊',
      excited: '🤩',
      neutral: '😐',
      sad: '😔',
      tired: '😴'
    };
    return moodEmojis[mood] || '😐';
  };

  // Render navigation path
  const renderNavigationPath = () => {
    if (!showNavigationPath || !currentPath || currentPath.length < 2) {
      return null;
    }

    const pathPoints = currentPath.map(point => `${point.x},${point.y}`).join(' ');

    return (
      <g className="navigation-path">
        {/* Path line */}
        <polyline
          points={pathPoints}
          fill="none"
          stroke="#3B82F6"
          strokeWidth="3"
          strokeDasharray="8,4"
          opacity="0.8"
          className="animate-pulse"
        />

        {/* Waypoint markers */}
        {currentPath.map((point, index) => {
          const isStart = index === 0;
          const isEnd = index === currentPath.length - 1;
          const isTransition = roomTransitions.some(t =>
            Math.abs(t.doorway_position.x - point.x) < 20 &&
            Math.abs(t.doorway_position.y - point.y) < 20
          );

          return (
            <g key={`waypoint-${index}`}>
              <circle
                cx={point.x}
                cy={point.y}
                r={isStart || isEnd ? 8 : isTransition ? 6 : 4}
                fill={isStart ? '#10B981' : isEnd ? '#EF4444' : isTransition ? '#F59E0B' : '#3B82F6'}
                stroke="white"
                strokeWidth="2"
                opacity="0.9"
              />

              {/* Labels for start/end */}
              {(isStart || isEnd) && (
                <text
                  x={point.x}
                  y={point.y - 15}
                  textAnchor="middle"
                  className="text-xs font-medium fill-gray-700"
                  fontSize="10"
                >
                  {isStart ? 'Start' : 'End'}
                </text>
              )}

              {/* Room transition indicator */}
              {isTransition && (
                <text
                  x={point.x}
                  y={point.y + 20}
                  textAnchor="middle"
                  className="text-xs font-medium fill-orange-600"
                  fontSize="8"
                >
                  🚪
                </text>
              )}
            </g>
          );
        })}

        {/* Progress indicator */}
        {isNavigating && navigationStatus.current_step && (
          <circle
            cx={currentPath[Math.min(navigationStatus.current_step - 1, currentPath.length - 1)]?.x || 0}
            cy={currentPath[Math.min(navigationStatus.current_step - 1, currentPath.length - 1)]?.y || 0}
            r="12"
            fill="none"
            stroke="#10B981"
            strokeWidth="3"
            opacity="0.8"
            className="animate-ping"
          />
        )}
      </g>
    );
  };

  // Render doorway highlights
  const renderDoorwayHighlights = () => {
    if (!showDoorwayHighlights || !assistantPosition) {
      return null;
    }

    return floorPlan.doorways.map(doorway => {
      if (!doorway.world_position) return null;

      const proximity = checkDoorwayProximity(
        assistantPosition.position,
        [doorway],
        60 // threshold
      );

      if (!proximity) return null;

      return (
        <g key={`doorway-highlight-${doorway.id}`}>
          <circle
            cx={doorway.world_position.x}
            cy={doorway.world_position.y}
            r="25"
            fill="rgba(59, 130, 246, 0.2)"
            stroke="#3B82F6"
            strokeWidth="2"
            strokeDasharray="4,2"
            className="animate-pulse"
          />
          <text
            x={doorway.world_position.x}
            y={doorway.world_position.y - 30}
            textAnchor="middle"
            className="text-xs font-medium fill-blue-600"
            fontSize="10"
          >
            Click to transition
          </text>
        </g>
      );
    });
  };

  return (
    <div className={`top-down-renderer ${className}`} style={style}>
      <svg
        ref={svgRef}
        className="w-full h-full"
        viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`}
        preserveAspectRatio="xMidYMid meet"
        onClick={handleSVGClick}
        onMouseMove={handleDragMove}
        onMouseUp={handleDragEnd}
        onMouseLeave={handleDragEnd}
        style={{
          cursor: isDragging ? 'grabbing' : 'default'
        }}
        // High quality rendering settings
        shapeRendering={display.highQualityRendering ? "geometricPrecision" : "auto"}
        textRendering={display.highQualityRendering ? "optimizeLegibility" : "auto"}
      >
        {/* Pattern definitions */}
        <defs>
          {/* High quality gradients for enhanced visuals */}
          {display.highQualityRendering && (
            <>
              <radialGradient id="assistant-glow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="rgba(59, 130, 246, 0.3)" />
                <stop offset="100%" stopColor="rgba(59, 130, 246, 0)" />
              </radialGradient>
              <linearGradient id="furniture-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgba(255, 255, 255, 0.1)" />
                <stop offset="100%" stopColor="rgba(0, 0, 0, 0.1)" />
              </linearGradient>
            </>
          )}

          <pattern
            id="carpet-pattern"
            patternUnits="userSpaceOnUse"
            width={display.highQualityRendering ? "8" : "10"}
            height={display.highQualityRendering ? "8" : "10"}
          >
            <rect width={display.highQualityRendering ? "8" : "10"} height={display.highQualityRendering ? "8" : "10"} fill="#E5E7EB" />
            <circle cx="2" cy="2" r={display.highQualityRendering ? "0.3" : "0.5"} fill="#9CA3AF" />
            <circle cx={display.highQualityRendering ? "6" : "8"} cy={display.highQualityRendering ? "6" : "8"} r={display.highQualityRendering ? "0.3" : "0.5"} fill="#9CA3AF" />
          </pattern>

          <pattern
            id="tile-pattern"
            patternUnits="userSpaceOnUse"
            width="20"
            height="20"
          >
            <rect width="20" height="20" fill="#F3F4F6" stroke="#E5E7EB" strokeWidth={display.highQualityRendering ? "0.5" : "1"} />
          </pattern>
        </defs>

        {/* Render floor plan elements in order */}
        {renderRooms()}
        {renderWalls()}
        {renderDoorways()}
        {renderFurniture()}
        {renderNavigationPath()}
        {renderDoorwayHighlights()}
        {renderAssistant()}

        {/* Grid overlay (optional) */}
        {process.env.NODE_ENV === 'development' && (
          <g className="grid-overlay opacity-20">
            {Array.from({ length: Math.floor(floorPlan.dimensions.width / 50) + 1 }, (_, i) => (
              <line
                key={`grid-v-${i}`}
                x1={i * 50}
                y1={0}
                x2={i * 50}
                y2={floorPlan.dimensions.height}
                stroke="#E5E7EB"
                strokeWidth="0.5"
              />
            ))}
            {Array.from({ length: Math.floor(floorPlan.dimensions.height / 50) + 1 }, (_, i) => (
              <line
                key={`grid-h-${i}`}
                x1={0}
                y1={i * 50}
                x2={floorPlan.dimensions.width}
                y2={i * 50}
                stroke="#E5E7EB"
                strokeWidth="0.5"
              />
            ))}
          </g>
        )}
      </svg>

      {/* Tooltip for hovered objects */}
      {hoveredObject && (
        <div className="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded pointer-events-none z-10">
          {floorPlan.furniture.find(f => f.id === hoveredObject)?.name || hoveredObject}
        </div>
      )}
    </div>
  );
};

export default TopDownRenderer;