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

import { useDeviceDetection } from '../../hooks/useDeviceDetection';
import { useTouchGestures, TouchPoint } from '../../hooks/useTouchGestures';
import { FloorPlan, Assistant, FurnitureItem, Position } from '../../types/floorPlan';

interface MobileFloorPlanProps {
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

/**
 * Mobile floor plan component with Canvas rendering and touch gestures.
 */
export const MobileFloorPlan: React.FC<MobileFloorPlanProps> = ({
  className = '',
  style = {},
  onObjectSelect,
  onAssistantMove,
  onObjectLongPress
}) => {
  const deviceInfo = useDeviceDetection();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();

  // Mock data (in real app, this would come from props or context)
  const [floorPlan] = useState<FloorPlan>({
    id: 'studio_apartment',
    name: 'Studio Apartment',
    category: 'apartment',
    dimensions: { width: 1300, height: 600, scale: 1, units: 'pixels' },
    styling: {
      background_color: '#F3F4F6',
      wall_color: '#374151',
      wall_thickness: 8
    },
    rooms: [{
      id: 'studio_main',
      name: 'Studio',
      type: 'studio',
      bounds: { x: 50, y: 50, width: 1200, height: 500 },
      properties: {
        floor_color: '#F9FAFB',
        floor_material: 'hardwood',
        lighting_level: 0.8
      }
    }],
    walls: [
      { id: 'wall_1', geometry: { start: { x: 50, y: 50 }, end: { x: 1250, y: 50 } }, properties: { type: 'exterior', thickness: 8, material: 'drywall', color: '#374151' } },
      { id: 'wall_2', geometry: { start: { x: 1250, y: 50 }, end: { x: 1250, y: 550 } }, properties: { type: 'exterior', thickness: 8, material: 'drywall', color: '#374151' } },
      { id: 'wall_3', geometry: { start: { x: 1250, y: 550 }, end: { x: 50, y: 550 } }, properties: { type: 'exterior', thickness: 8, material: 'drywall', color: '#374151' } },
      { id: 'wall_4', geometry: { start: { x: 50, y: 550 }, end: { x: 50, y: 50 } }, properties: { type: 'exterior', thickness: 8, material: 'drywall', color: '#374151' } }
    ],
    doorways: [],
    furniture: [
      {
        id: 'sofa',
        name: 'Sofa',
        type: 'furniture',
        position: { x: 500, y: 300 },
        geometry: { width: 180, height: 80 },
        visual: { color: '#6B7280', material: 'fabric', style: 'modern' },
        properties: { solid: true, interactive: true, movable: false }
      },
      {
        id: 'coffee_table',
        name: 'Coffee Table',
        type: 'furniture',
        position: { x: 550, y: 400 },
        geometry: { width: 80, height: 40 },
        visual: { color: '#92400E', material: 'wood', style: 'modern' },
        properties: { solid: true, interactive: true, movable: true }
      },
      {
        id: 'bed',
        name: 'Bed',
        type: 'furniture',
        position: { x: 900, y: 350 },
        geometry: { width: 160, height: 120 },
        visual: { color: '#F3F4F6', material: 'fabric', style: 'modern' },
        properties: { solid: true, interactive: true, movable: false }
      }
    ]
  });

  const [assistant] = useState<Assistant>({
    id: 'default',
    location: {
      position: { x: 650, y: 300 },
      facing: 'right',
      facing_angle: 0
    },
    status: {
      action: 'idle',
      mood: 'happy',
      energy_level: 1.0,
      mode: 'active'
    }
  });

  const [viewport, setViewport] = useState<ViewportState>({
    x: 0,
    y: 0,
    scale: 1,
    rotation: 0
  });

  const [selectedObject, setSelectedObject] = useState<string | null>(null);
  const [animation, setAnimation] = useState<AnimationState | null>(null);

  // Initialize viewport to fit floor plan
  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    const scaleX = containerWidth / floorPlan.dimensions.width;
    const scaleY = containerHeight / floorPlan.dimensions.height;
    const initialScale = Math.min(scaleX, scaleY) * 0.9; // 90% to add padding

    const centerX = (containerWidth - floorPlan.dimensions.width * initialScale) / 2;
    const centerY = (containerHeight - floorPlan.dimensions.height * initialScale) / 2;

    setViewport({
      x: centerX,
      y: centerY,
      scale: initialScale,
      rotation: 0
    });
  }, [floorPlan.dimensions]);

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
    for (const furniture of floorPlan.furniture) {
      const { x, y } = furniture.position;
      const { width, height } = furniture.geometry;

      if (worldPos.x >= x && worldPos.x <= x + width &&
          worldPos.y >= y && worldPos.y <= y + height) {
        return furniture;
      }
    }
    return null;
  }, [floorPlan.furniture]);

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

  const handlePinchMove = useCallback((center: TouchPoint, scale: number) => {
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
      width: floorPlan.dimensions.width,
      height: floorPlan.dimensions.height
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
  }, [floorPlan.dimensions]);

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
  };

  // Helper functions
  const getFurnitureIcon = (type: string, name: string): string => {
    const iconMap: Record<string, string> = {
      sofa: '🛋️', bed: '🛏️', table: '📋', desk: '💻', chair: '💺'
    };
    const key = name.toLowerCase();
    for (const [keyword, icon] of Object.entries(iconMap)) {
      if (key.includes(keyword)) return icon;
    }
    return '📦';
  };

  const getAssistantColor = (mood: string): string => {
    const colors: Record<string, string> = {
      happy: '#10B981', excited: '#F59E0B', neutral: '#6B7280'
    };
    return colors[mood] || '#6B7280';
  };

  const getAssistantEmoji = (mood: string): string => {
    const emojis: Record<string, string> = {
      happy: '😊', excited: '🤩', neutral: '😐'
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
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 2a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V4a2 2 0 00-2-2H4zm3 5a1 1 0 011-1h4a1 1 0 110 2H8a1 1 0 01-1-1zm0 4a1 1 0 011-1h4a1 1 0 110 2H8a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
        </button>
      </div>

      {/* Selected object indicator */}
      {selectedObject && (
        <div className="absolute bottom-4 left-4 bg-white bg-opacity-90 rounded-lg px-3 py-2 shadow-lg z-10">
          <p className="text-sm font-medium text-gray-800">
            {floorPlan.furniture.find(f => f.id === selectedObject)?.name}
          </p>
        </div>
      )}
    </div>
  );
};

export default MobileFloorPlan;