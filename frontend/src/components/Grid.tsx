/**
 * Grid component - 64x16 room grid system
 */

import React, { useCallback, useMemo, useEffect } from 'react';
import { useRoomStore } from '../stores/roomStore';
import { useChatStore } from '../stores/chatStore';
import { Position } from '../types/room';

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
    getObjectStates
  } = useRoomStore();

  const { sendAssistantMove, isConnected } = useChatStore();

  const gridMap = useMemo(() => getGridMap(), [getGridMap]);

  // Load objects and assistant from API on component mount
  useEffect(() => {
    loadObjectsFromAPI();
    loadAssistantFromAPI();
  }, [loadObjectsFromAPI, loadAssistantFromAPI]);

  const handleCellClick = useCallback(async (position: Position) => {
    // If we're dragging an object, try to drop it here
    if (draggedObject) {
      const draggedObj = objects.find(obj => obj.id === draggedObject);
      if (draggedObj) {
        const success = await moveObjectToPosition(draggedObject, position);
        if (success) {
          // Object moved successfully
        } else {
          // Failed to move object - position occupied or invalid
        }
      }
      setDraggedObject(null);
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
        // Started dragging object
      } else {
        // Selected non-movable object
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
  }, [objects, getObjectStates, setObjectState]);

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

    // Show assistant
    if (cell.objectId === assistant.id) {
      return (
        <div className="w-full h-full flex items-center justify-center">
          <div className="w-3 h-3 bg-white rounded-full" />
        </div>
      );
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

      {/* Grid overlay for debugging (can be removed) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="absolute top-2 left-2 text-white text-xs bg-black/50 p-2 rounded">
          Grid: {gridSize.width}x{gridSize.height} |
          Assistant: ({assistant.position.x}, {assistant.position.y}) |
          Objects: {objects.length}
        </div>
      )}
    </div>
  );
};

export default Grid;