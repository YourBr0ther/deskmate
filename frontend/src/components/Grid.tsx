/**
 * Grid component - 64x16 room grid system
 */

import React, { useCallback, useMemo, useEffect, useState } from 'react';
import { useRoomStore } from '../stores/roomStore';
import { useChatStore } from '../stores/chatStore';
import { Position } from '../types/room';
import { useAssistantAnimation } from '../hooks/useAssistantAnimation';

const Grid: React.FC = () => {
  const {
    gridSize,
    cellSize,
    objects,
    assistant,
    getGridMap,
    selectObject,
    selectedObject,
    moveAssistant,
    loadObjectsFromAPI,
    loadAssistantFromAPI,
    moveAssistantToPosition,
    draggedObject,
    setDraggedObject,
    moveObjectToPosition,
    setObjectState,
    getObjectStates,
    sitOnFurniture
  } = useRoomStore();

  const { sendAssistantMove, isConnected } = useChatStore();

  // Local state for enhanced drag-and-drop
  const [isDragging, setIsDragging] = useState(false);
  const [dragPreviewPosition, setDragPreviewPosition] = useState<Position | null>(null);
  const [dragValid, setDragValid] = useState(true);

  const gridMap = useMemo(() => getGridMap(), [getGridMap]);

  // Use animation hook for smooth assistant movement
  const assistantAnimation = useAssistantAnimation({
    currentPosition: assistant.position,
    targetPosition: assistant.targetPosition,
    isMoving: assistant.isMoving,
    movementPath: assistant.movementPath,
    cellSize,
    speed: assistant.movementSpeed || 2
  });

  // Load objects and assistant from API on component mount
  useEffect(() => {
    loadObjectsFromAPI();
    loadAssistantFromAPI();
  }, [loadObjectsFromAPI, loadAssistantFromAPI]);

  // Validate if an object can be placed at a position
  const canPlaceObjectAt = useCallback((objectId: string, position: Position) => {
    const obj = objects.find(o => o.id === objectId);
    if (!obj) return false;

    // Check if all cells the object would occupy are available
    for (let y = position.y; y < position.y + obj.size.height; y++) {
      for (let x = position.x; x < position.x + obj.size.width; x++) {
        const cell = gridMap[y]?.[x];
        if (!cell || cell.occupied || (cell.objectId && cell.objectId !== objectId)) {
          return false;
        }
      }
    }

    // Check bounds
    if (position.x < 0 || position.y < 0 ||
        position.x + obj.size.width > gridSize.width ||
        position.y + obj.size.height > gridSize.height) {
      return false;
    }

    return true;
  }, [objects, gridMap, gridSize]);

  const handleCellClick = useCallback(async (position: Position) => {
    // If we're dragging an object, try to drop it here
    if (draggedObject) {
      const draggedObj = objects.find(obj => obj.id === draggedObject);
      if (draggedObj && canPlaceObjectAt(draggedObject, position)) {
        const success = await moveObjectToPosition(draggedObject, position);
        if (success) {
          console.log(`Successfully moved ${draggedObj.name} to (${position.x}, ${position.y})`);
        } else {
          console.log(`Failed to move ${draggedObj.name} - API error`);
        }
      } else {
        console.log(`Cannot place ${draggedObj?.name} at (${position.x}, ${position.y}) - position invalid`);
      }

      // Reset drag state
      setDraggedObject(null);
      setIsDragging(false);
      setDragPreviewPosition(null);
      setDragValid(true);
      return;
    }

    // Check if clicked on an object
    const clickedObject = objects.find(obj =>
      position.x >= obj.position.x &&
      position.x < obj.position.x + obj.size.width &&
      position.y >= obj.position.y &&
      position.y < obj.position.y + obj.size.height
    );

    if (clickedObject) {
      selectObject(clickedObject.id);

      // Check if object is movable (items and decorations can be movable, large furniture is not)
      const isMovable = clickedObject.movable;

      if (isMovable) {
        setDraggedObject(clickedObject.id);
        setIsDragging(true);
        setDragPreviewPosition(position);
        console.log(`Started dragging ${clickedObject.name} from (${position.x}, ${position.y})`);
      } else {
        console.log(`Selected non-movable object: ${clickedObject.name}`);
      }
    } else {
      // Move assistant to clicked position if it's walkable
      const cell = gridMap[position.y]?.[position.x];
      if (cell && cell.walkable && !cell.occupied) {
        // Use WebSocket if connected, otherwise fall back to direct API
        if (isConnected) {
          sendAssistantMove(position.x, position.y);
          // Sent assistant move request via WebSocket
        } else {
          // Fallback to direct API call
          const success = await moveAssistantToPosition(position.x, position.y);
          if (success) {
            // Assistant moved successfully via API
          }
        }
        selectObject(undefined);
      }
    }
  }, [objects, gridMap, selectObject, moveAssistant, draggedObject, setDraggedObject, moveObjectToPosition, moveAssistantToPosition]);

  const handleCellRightClick = useCallback(async (e: React.MouseEvent, position: Position) => {
    e.preventDefault(); // Prevent context menu

    // If we're dragging, cancel the drag operation
    if (isDragging && draggedObject) {
      setDraggedObject(null);
      setIsDragging(false);
      setDragPreviewPosition(null);
      setDragValid(true);
      console.log('Drag operation cancelled');
      return;
    }

    // Check if right-clicked on an object
    const clickedObject = objects.find(obj =>
      position.x >= obj.position.x &&
      position.x < obj.position.x + obj.size.width &&
      position.y >= obj.position.y &&
      position.y < obj.position.y + obj.size.height
    );

    if (clickedObject && clickedObject.interactive) {
      // Get current states
      const states = await getObjectStates(clickedObject.id);

      // Handle sitting on furniture
      if (clickedObject.type === 'furniture' && (clickedObject.id === 'bed' || clickedObject.id === 'desk')) {
        const success = await sitOnFurniture(clickedObject.id);
        if (success) {
          console.log(`Assistant is now sitting on ${clickedObject.name}`);
        } else {
          console.log(`Failed to sit on ${clickedObject.name}`);
        }
        return;
      }

      // Toggle common states based on object type
      if (clickedObject.id === 'window') {
        const isOpen = states?.open === 'true';
        await setObjectState(clickedObject.id, 'open', isOpen ? 'false' : 'true');
        console.log(`${clickedObject.name} is now ${isOpen ? 'closed' : 'open'}`);
      } else if (clickedObject.id === 'door') {
        const isOpen = states?.open === 'true';
        await setObjectState(clickedObject.id, 'open', isOpen ? 'false' : 'true');
        console.log(`${clickedObject.name} is now ${isOpen ? 'closed' : 'open'}`);
      } else if (clickedObject.id === 'lamp_001') {
        const isOn = states?.power === 'on';
        await setObjectState(clickedObject.id, 'power', isOn ? 'off' : 'on');
        console.log(`${clickedObject.name} is now ${isOn ? 'off' : 'on'}`);
      } else {
        console.log(`Right-clicked on ${clickedObject.name} - no state actions defined`);
      }
    }
  }, [objects, getObjectStates, setObjectState, sitOnFurniture]);

  const handleCellHover = useCallback((position: Position) => {
    if (isDragging && draggedObject) {
      setDragPreviewPosition(position);
      setDragValid(canPlaceObjectAt(draggedObject, position));
    }
  }, [isDragging, draggedObject, canPlaceObjectAt]);

  const getCellClass = useCallback((x: number, y: number) => {
    const cell = gridMap[y]?.[x];
    if (!cell) return 'grid-cell';

    let classes = 'grid-cell';

    if (cell.occupied && cell.objectId !== assistant.id) {
      classes += ' occupied';
    }

    if (cell.objectId === selectedObject) {
      classes += ' ring-2 ring-blue-500';
    }

    if (cell.objectId === draggedObject) {
      classes += ' opacity-50 ring-2 ring-yellow-500';
    }

    // Show drag preview for the drop zone
    if (isDragging && draggedObject && dragPreviewPosition) {
      const draggedObj = objects.find(o => o.id === draggedObject);
      if (draggedObj) {
        const inDropZone = x >= dragPreviewPosition.x &&
                          x < dragPreviewPosition.x + draggedObj.size.width &&
                          y >= dragPreviewPosition.y &&
                          y < dragPreviewPosition.y + draggedObj.size.height;

        if (inDropZone) {
          classes += dragValid
            ? ' ring-2 ring-green-400 bg-green-500/20'
            : ' ring-2 ring-red-400 bg-red-500/20';
        }
      }
    }

    if (cell.objectId === assistant.id) {
      classes += ' bg-green-500 border-green-400';
    }

    // Add object-specific background for furniture
    if (cell.objectId && cell.objectId !== assistant.id) {
      const obj = objects.find(o => o.id === cell.objectId);
      if (obj) {
        switch (obj.id) {
          case 'bed':
            classes += ' bg-purple-800/30 border-purple-400';
            break;
          case 'desk':
            classes += ' bg-orange-800/30 border-orange-400';
            break;
          case 'window':
            classes += ' bg-blue-800/30 border-blue-400';
            break;
          case 'door':
            classes += ' bg-amber-800/30 border-amber-400';
            break;
        }
      }
    }

    return classes;
  }, [gridMap, selectedObject, assistant.id, objects]);

  const getCellContent = useCallback((x: number, y: number) => {
    const cell = gridMap[y]?.[x];
    if (!cell) return null;

    // Assistant is now rendered separately for smooth animations
    if (cell.objectId === assistant.id) {
      return null;
    }

    // Show object markers
    if (cell.objectId && cell.objectId !== assistant.id) {
      const obj = objects.find(o => o.id === cell.objectId);
      if (obj) {
        const getObjectColor = (objType: string, objId: string) => {
          switch (objId) {
            case 'bed': return 'bg-purple-600 text-purple-100';
            case 'desk': return 'bg-orange-600 text-orange-100';
            case 'window': return 'bg-blue-500 text-blue-100';
            case 'door': return 'bg-amber-700 text-amber-100';
            default: return 'bg-gray-600 text-gray-100';
          }
        };

        return (
          <div className="w-full h-full flex items-center justify-center">
            <div className={`text-xs font-bold truncate rounded px-1 ${getObjectColor(obj.type, obj.id)}`}>
              {obj.name.charAt(0)}
            </div>
          </div>
        );
      }
    }

    return null;
  }, [gridMap, assistant.id, objects]);

  return (
    <div className="grid-area bg-room-bg relative overflow-hidden">
      {/* Grid container */}
      <div
        className="absolute inset-0"
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${gridSize.width}, ${cellSize.width}px)`,
          gridTemplateRows: `repeat(${gridSize.height}, ${cellSize.height}px)`,
          gap: '1px'
        }}
      >
        {Array.from({ length: gridSize.height }, (_, y) =>
          Array.from({ length: gridSize.width }, (_, x) => (
            <div
              key={`cell-${x}-${y}`}
              className={getCellClass(x, y)}
              onClick={() => handleCellClick({ x, y })}
              onContextMenu={(e) => handleCellRightClick(e, { x, y })}
              onMouseEnter={() => handleCellHover({ x, y })}
              style={{
                width: cellSize.width,
                height: cellSize.height
              }}
            >
              {getCellContent(x, y)}
            </div>
          ))
        )}
      </div>

      {/* Animated Assistant - Rendered separately for smooth movement */}
      <div
        className="absolute pointer-events-none transition-all duration-150 ease-linear"
        style={{
          left: assistantAnimation.animatedPosition.x * cellSize.width + cellSize.width / 2,
          top: assistantAnimation.animatedPosition.y * cellSize.height + cellSize.height / 2,
          transform: 'translate(-50%, -50%)',
          zIndex: 10
        }}
      >
        <div className="w-full h-full flex items-center justify-center">
          <div className={`w-3 h-3 bg-white rounded-full transition-all duration-200 ${
            assistant.sitting_on_object_id ? 'ring-2 ring-blue-400' : ''
          } ${assistantAnimation.isAnimating ? 'animate-pulse' : ''}`} />
          {assistant.sitting_on_object_id && (
            <div className="absolute text-xs text-blue-400 mt-4">
              💺
            </div>
          )}
          {assistantAnimation.isAnimating && (
            <div className="absolute text-xs text-green-400 -mt-6">
              🚶‍♂️
            </div>
          )}
        </div>
      </div>

      {/* Drag status indicator */}
      {isDragging && draggedObject && (
        <div className="absolute bottom-2 left-2 text-white text-sm bg-black/75 p-3 rounded-lg border border-gray-600">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${dragValid ? 'bg-green-400' : 'bg-red-400'}`} />
            <span>
              Dragging: <strong>{objects.find(o => o.id === draggedObject)?.name}</strong>
            </span>
          </div>
          {dragPreviewPosition && (
            <div className="text-xs text-gray-300 mt-1">
              Target: ({dragPreviewPosition.x}, {dragPreviewPosition.y})
              {!dragValid && <span className="text-red-400 ml-2">• Invalid position</span>}
            </div>
          )}
          <div className="text-xs text-gray-400 mt-1">
            Click to drop • Right-click to cancel
          </div>
        </div>
      )}

      {/* Grid overlay for debugging (can be removed) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="absolute top-2 left-2 text-white text-xs bg-black/50 p-2 rounded">
          Grid: {gridSize.width}x{gridSize.height} |
          Assistant: ({assistant.position.x}, {assistant.position.y}) |
          Objects: {objects.length}
          {assistant.sitting_on_object_id && (
            <div className="text-blue-400 mt-1">
              💺 Sitting on: {assistant.sitting_on_object_id}
            </div>
          )}
        </div>
      )}

      {/* Interaction hints */}
      <div className="absolute top-2 right-2 text-white text-xs bg-black/50 p-2 rounded max-w-48">
        <div className="font-medium mb-1">Interactions:</div>
        <div>• Left-click: Move or select</div>
        <div>• Right-click furniture: Sit (bed, desk)</div>
        <div>• Right-click objects: Toggle states</div>
        <div>• Drag: Move small objects</div>
      </div>
    </div>
  );
};

export default Grid;