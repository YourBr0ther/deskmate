/**
 * Mobile-optimized floor plan component.
 *
 * Provides touch-optimized floor plan rendering with:
 * - Canvas-based rendering for performance
 * - Touch gesture support (pinch, pan, tap, long press)
 * - Smooth animations and transitions
 * - Mobile-specific optimizations
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';

import { useTouchGestures, TouchPoint } from '../../hooks/useTouchGestures';
import { FloorPlan, Assistant, FurnitureItem, Position } from '../../types/floorPlan';

interface MobileFloorPlanProps {
  floorPlan: FloorPlan | null;
  assistant: Assistant | null;
  className?: string;
  style?: React.CSSProperties;
  onObjectSelect?: (objectId: string) => void;
  onAssistantMove?: (position: Position) => void;
  onObjectLongPress?: (objectId: string, position: Position) => void;
}

interface ViewportState {
  x: number;
  y: number;
  scale: number;
  rotation: number;
}

interface AnimationState {
  isAnimating: boolean;
  startTime: number;
  duration: number;
  startViewport: ViewportState;
  targetViewport: ViewportState;
}

// Default floor plan dimensions when none provided
const DEFAULT_DIMENSIONS = { width: 1920, height: 480, scale: 1, units: 'pixels' as const };

/**
 * Mobile floor plan component with Canvas rendering and touch gestures.
 */
export const MobileFloorPlan: React.FC<MobileFloorPlanProps> = ({
  floorPlan,
  assistant,
  className = '',
  style = {},
  onObjectSelect,
  onAssistantMove,
  onObjectLongPress
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();

  const [viewport, setViewport] = useState<ViewportState>({
    x: 0,
    y: 0,
    scale: 1,
    rotation: 0
  });

  const [selectedObject, setSelectedObject] = useState<string | null>(null);
  const [animation, setAnimation] = useState<AnimationState | null>(null);

  // Get dimensions from floor plan or use defaults
  const dimensions = floorPlan?.dimensions || DEFAULT_DIMENSIONS;

  // Initialize viewport to fit floor plan
  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    const scaleX = containerWidth / dimensions.width;
    const scaleY = containerHeight / dimensions.height;
    const initialScale = Math.min(scaleX, scaleY) * 0.9; // 90% to add padding

    const centerX = (containerWidth - dimensions.width * initialScale) / 2;
    const centerY = (containerHeight - dimensions.height * initialScale) / 2;

    setViewport({
      x: centerX,
      y: centerY,
      scale: initialScale,
      rotation: 0
    });
  }, [dimensions.width, dimensions.height]);

  // Convert screen coordinates to world coordinates
  const screenToWorld = useCallback((screenX: number, screenY: number): Position => {
    if (!containerRef.current) return { x: 0, y: 0 };

    const rect = containerRef.current.getBoundingClientRect();
    const x = (screenX - rect.left - viewport.x) / viewport.scale;
    const y = (screenY - rect.top - viewport.y) / viewport.scale;

    return { x, y };
  }, [viewport]);

  // Find object at position
  const getObjectAtPosition = useCallback((worldPos: Position): FurnitureItem | null => {
    if (!floorPlan?.furniture) return null;

    for (const furniture of floorPlan.furniture) {
      const { x, y } = furniture.position;
      const { width, height } = furniture.geometry;

      if (worldPos.x >= x && worldPos.x <= x + width &&
          worldPos.y >= y && worldPos.y <= y + height) {
        return furniture;
      }
    }
    return null;
  }, [floorPlan?.furniture]);

  // Touch gesture handlers
  const handleTap = useCallback((point: TouchPoint) => {
    const worldPos = screenToWorld(point.x, point.y);
    const object = getObjectAtPosition(worldPos);

    if (object) {
      setSelectedObject(object.id);
      onObjectSelect?.(object.id);
    } else {
      setSelectedObject(null);
      onAssistantMove?.(worldPos);
    }
  }, [screenToWorld, getObjectAtPosition, onObjectSelect, onAssistantMove]);

  const handleDoubleTap = useCallback((point: TouchPoint) => {
    const worldPos = screenToWorld(point.x, point.y);
    const object = getObjectAtPosition(worldPos);

    if (object) {
      // Zoom to fit object
      const padding = 50;
      const objectBounds = {
        x: object.position.x - padding,
        y: object.position.y - padding,
        width: object.geometry.width + padding * 2,
        height: object.geometry.height + padding * 2
      };

      zoomToFit(objectBounds);
    } else {
      // Zoom to fit entire floor plan
      zoomToFit();
    }
  }, [screenToWorld, getObjectAtPosition]);

  const handleLongPress = useCallback((point: TouchPoint) => {
    const worldPos = screenToWorld(point.x, point.y);
    const object = getObjectAtPosition(worldPos);

    if (object) {
      onObjectLongPress?.(object.id, worldPos);
    }
  }, [screenToWorld, getObjectAtPosition, onObjectLongPress]);

  const handlePanMove = useCallback((deltaX: number, deltaY: number) => {
    setViewport(prev => ({
      ...prev,
      x: prev.x + deltaX,
      y: prev.y + deltaY
    }));
  }, []);

  const handlePinchMove = useCallback((_center: TouchPoint, scale: number) => {
    setViewport(prev => {
      const newScale = Math.max(0.1, Math.min(5, prev.scale * scale));
      return {
        ...prev,
        scale: newScale
      };
    });
  }, []);

  // Zoom to fit function
  const zoomToFit = useCallback((bounds?: { x: number; y: number; width: number; height: number }) => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    const targetBounds = bounds || {
      x: 0,
      y: 0,
      width: dimensions.width,
      height: dimensions.height
    };

    const scaleX = containerWidth / targetBounds.width;
    const scaleY = containerHeight / targetBounds.height;
    const targetScale = Math.min(scaleX, scaleY) * 0.9;

    const centerX = (containerWidth - targetBounds.width * targetScale) / 2 - targetBounds.x * targetScale;
    const centerY = (containerHeight - targetBounds.height * targetScale) / 2 - targetBounds.y * targetScale;

    animateToViewport({
      x: centerX,
      y: centerY,
      scale: targetScale,
      rotation: 0
    });
  }, [dimensions]);

  // Animate viewport
  const animateToViewport = useCallback((targetViewport: ViewportState, duration = 300) => {
    const startViewport = { ...viewport };
    const startTime = Date.now();

    setAnimation({
      isAnimating: true,
      startTime,
      duration,
      startViewport,
      targetViewport
    });
  }, [viewport]);

  // Animation loop
  useEffect(() => {
    if (!animation) return;

    const animate = () => {
      const now = Date.now();
      const progress = Math.min((now - animation.startTime) / animation.duration, 1);
      const easeProgress = 1 - Math.pow(1 - progress, 3); // Ease out cubic

      if (progress >= 1) {
        setViewport(animation.targetViewport);
        setAnimation(null);
        return;
      }

      setViewport({
        x: animation.startViewport.x + (animation.targetViewport.x - animation.startViewport.x) * easeProgress,
        y: animation.startViewport.y + (animation.targetViewport.y - animation.startViewport.y) * easeProgress,
        scale: animation.startViewport.scale + (animation.targetViewport.scale - animation.startViewport.scale) * easeProgress,
        rotation: animation.startViewport.rotation + (animation.targetViewport.rotation - animation.startViewport.rotation) * easeProgress
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [animation]);

  // Set up touch gestures
  useTouchGestures(containerRef, {
    onTap: handleTap,
    onDoubleTap: handleDoubleTap,
    onLongPress: handleLongPress,
    onPanMove: handlePanMove,
    onPinchMove: handlePinchMove
  });

  // Canvas rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size to match container
    const rect = container.getBoundingClientRect();
    const scale = window.devicePixelRatio || 1;
    canvas.width = rect.width * scale;
    canvas.height = rect.height * scale;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    ctx.scale(scale, scale);

    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height);

    // Apply viewport transform
    ctx.save();
    ctx.translate(viewport.x, viewport.y);
    ctx.scale(viewport.scale, viewport.scale);
    ctx.rotate(viewport.rotation);

    // Render floor plan
    renderFloorPlan(ctx);

    ctx.restore();
  }, [viewport, selectedObject, floorPlan, assistant]);

  // Floor plan rendering function
  const renderFloorPlan = (ctx: CanvasRenderingContext2D) => {
    // If no floor plan, render placeholder
    if (!floorPlan) {
      ctx.fillStyle = '#F3F4F6';
      ctx.fillRect(0, 0, dimensions.width, dimensions.height);
      ctx.fillStyle = '#9CA3AF';
      ctx.font = '24px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('Loading floor plan...', dimensions.width / 2, dimensions.height / 2);
      return;
    }

    // Render background
    ctx.fillStyle = floorPlan.styling?.background_color || '#F3F4F6';
    ctx.fillRect(0, 0, dimensions.width, dimensions.height);

    // Render rooms
    floorPlan.rooms.forEach(room => {
      ctx.fillStyle = room.properties.floor_color;
      ctx.fillRect(room.bounds.x, room.bounds.y, room.bounds.width, room.bounds.height);

      // Room label
      ctx.fillStyle = '#6B7280';
      ctx.font = '14px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText(
        room.name,
        room.bounds.x + room.bounds.width / 2,
        room.bounds.y + room.bounds.height / 2
      );
    });

    // Render walls
    floorPlan.walls.forEach(wall => {
      ctx.strokeStyle = wall.properties.color;
      ctx.lineWidth = wall.properties.thickness;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(wall.geometry.start.x, wall.geometry.start.y);
      ctx.lineTo(wall.geometry.end.x, wall.geometry.end.y);
      ctx.stroke();
    });

    // Render doorways
    floorPlan.doorways?.forEach(doorway => {
      if (doorway.world_position) {
        const { x, y } = doorway.world_position;
        const width = doorway.position.width || 60;

        // Draw doorway opening
        ctx.fillStyle = '#E5E7EB';
        ctx.fillRect(x - width / 2, y - 5, width, 10);

        // Draw door indicator if it has a door
        if (doorway.properties.has_door) {
          ctx.strokeStyle = doorway.properties.door_state === 'locked' ? '#EF4444' : '#10B981';
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.arc(x, y, 8, 0, Math.PI * 2);
          ctx.stroke();
        }
      }
    });

    // Render furniture
    floorPlan.furniture.forEach(furniture => {
      const isSelected = selectedObject === furniture.id;

      ctx.fillStyle = furniture.visual.color;
      ctx.strokeStyle = isSelected ? '#3B82F6' : '#9CA3AF';
      ctx.lineWidth = isSelected ? 3 : 1;

      const { x, y } = furniture.position;
      const { width, height } = furniture.geometry;

      ctx.fillRect(x, y, width, height);
      ctx.strokeRect(x, y, width, height);

      // Furniture label
      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 12px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText(
        getFurnitureIcon(furniture.type, furniture.name),
        x + width / 2,
        y + height / 2 + 4
      );
    });

    // Render assistant
    if (assistant) {
      const { x, y } = assistant.location.position;
      ctx.fillStyle = getAssistantColor(assistant.status.mood);
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 2;

      ctx.beginPath();
      ctx.arc(x, y, 12, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // Assistant emoji
      ctx.fillStyle = '#000000';
      ctx.font = '16px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText(getAssistantEmoji(assistant.status.mood), x, y + 5);
    }
  };

  // Helper functions
  const getFurnitureIcon = (type: string, name: string): string => {
    const iconMap: Record<string, string> = {
      sofa: '🛋️', bed: '🛏️', table: '📋', desk: '💻', chair: '💺',
      lamp: '💡', tv: '📺', fridge: '🧊', plant: '🌱', bookshelf: '📚'
    };
    const key = name.toLowerCase();
    for (const [keyword, icon] of Object.entries(iconMap)) {
      if (key.includes(keyword)) return icon;
    }
    return '📦';
  };

  const getAssistantColor = (mood: string): string => {
    const colors: Record<string, string> = {
      happy: '#10B981',
      excited: '#F59E0B',
      neutral: '#6B7280',
      sad: '#6366F1',
      tired: '#8B5CF6',
      confused: '#EC4899',
      focused: '#0EA5E9'
    };
    return colors[mood] || '#6B7280';
  };

  const getAssistantEmoji = (mood: string): string => {
    const emojis: Record<string, string> = {
      happy: '😊',
      excited: '🤩',
      neutral: '😐',
      sad: '😢',
      tired: '😴',
      confused: '🤔',
      focused: '🧐'
    };
    return emojis[mood] || '😐';
  };

  return (
    <div
      ref={containerRef}
      className={`mobile-floor-plan relative w-full h-full overflow-hidden touch-none ${className}`}
      style={style}
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        style={{ touchAction: 'none' }}
      />

      {/* Controls overlay */}
      <div className="absolute top-4 right-4 flex flex-col space-y-2 z-10">
        <button
          onClick={() => zoomToFit()}
          className="w-10 h-10 bg-white bg-opacity-90 rounded-full shadow-lg flex items-center justify-center text-gray-700 hover:bg-opacity-100 active:scale-95"
          aria-label="Fit to view"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 2a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V4a2 2 0 00-2-2H4zm3 5a1 1 0 011-1h4a1 1 0 110 2H8a1 1 0 01-1-1zm0 4a1 1 0 011-1h4a1 1 0 110 2H8a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
        </button>
      </div>

      {/* Selected object indicator */}
      {selectedObject && floorPlan && (
        <div className="absolute bottom-4 left-4 bg-white bg-opacity-90 rounded-lg px-3 py-2 shadow-lg z-10">
          <p className="text-sm font-medium text-gray-800">
            {floorPlan.furniture.find(f => f.id === selectedObject)?.name}
          </p>
        </div>
      )}

      {/* Loading indicator */}
      {!floorPlan && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 bg-opacity-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Loading floor plan...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MobileFloorPlan;
