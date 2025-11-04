/**
 * Touch gesture handling hook for mobile floor plan interactions.
 *
 * Provides comprehensive touch gesture support including:
 * - Single tap: Select objects or move assistant
 * - Double tap: Zoom to fit object/area
 * - Pinch: Zoom in/out on floor plan
 * - Pan: Move around large floor plans
 * - Long press: Object context menu
 */

import { useRef, useCallback, useEffect } from 'react';

export interface TouchPoint {
  x: number;
  y: number;
  id: number;
}

export interface GestureState {
  isActive: boolean;
  type: GestureType | null;
  startTime: number;
  startPoints: TouchPoint[];
  currentPoints: TouchPoint[];
  deltaX: number;
  deltaY: number;
  scale: number;
  velocity: { x: number; y: number };
}

export type GestureType = 'tap' | 'double-tap' | 'long-press' | 'pan' | 'pinch';

export interface GestureHandlers {
  onTap?: (point: TouchPoint) => void;
  onDoubleTap?: (point: TouchPoint) => void;
  onLongPress?: (point: TouchPoint) => void;
  onPanStart?: (point: TouchPoint) => void;
  onPanMove?: (deltaX: number, deltaY: number, velocity: { x: number; y: number }) => void;
  onPanEnd?: (velocity: { x: number; y: number }) => void;
  onPinchStart?: (center: TouchPoint, initialDistance: number) => void;
  onPinchMove?: (center: TouchPoint, scale: number, distance: number) => void;
  onPinchEnd?: (scale: number) => void;
}

export interface TouchGestureConfig {
  tapTimeout: number;
  doubleTapTimeout: number;
  longPressTimeout: number;
  moveThreshold: number;
  pinchThreshold: number;
  maxVelocityDecay: number;
}

const DEFAULT_CONFIG: TouchGestureConfig = {
  tapTimeout: 300,        // Max time for tap
  doubleTapTimeout: 300,  // Max time between taps for double-tap
  longPressTimeout: 500,  // Time to trigger long press
  moveThreshold: 10,      // Min movement to start pan/pinch
  pinchThreshold: 20,     // Min distance change for pinch
  maxVelocityDecay: 0.95  // Velocity decay for momentum
};

/**
 * Hook for handling touch gestures on mobile devices.
 */
export const useTouchGestures = (
  elementRef: React.RefObject<HTMLElement>,
  handlers: GestureHandlers,
  config: Partial<TouchGestureConfig> = {}
) => {
  const fullConfig = { ...DEFAULT_CONFIG, ...config };
  const gestureState = useRef<GestureState>({
    isActive: false,
    type: null,
    startTime: 0,
    startPoints: [],
    currentPoints: [],
    deltaX: 0,
    deltaY: 0,
    scale: 1,
    velocity: { x: 0, y: 0 }
  });

  const tapTimeout = useRef<NodeJS.Timeout | null>(null);
  const longPressTimeout = useRef<NodeJS.Timeout | null>(null);
  const lastTapTime = useRef<number>(0);
  const lastTapPoint = useRef<TouchPoint | null>(null);
  const velocityTracker = useRef<Array<{ point: TouchPoint; time: number }>>([]);

  // Utility functions
  const getTouchPoints = useCallback((touches: TouchList): TouchPoint[] => {
    return Array.from(touches).map(touch => ({
      x: touch.clientX,
      y: touch.clientY,
      id: touch.identifier
    }));
  }, []);

  const getDistance = useCallback((point1: TouchPoint, point2: TouchPoint): number => {
    const dx = point1.x - point2.x;
    const dy = point1.y - point2.y;
    return Math.sqrt(dx * dx + dy * dy);
  }, []);

  const getCenter = useCallback((points: TouchPoint[]): TouchPoint => {
    const sumX = points.reduce((sum, p) => sum + p.x, 0);
    const sumY = points.reduce((sum, p) => sum + p.y, 0);
    return {
      x: sumX / points.length,
      y: sumY / points.length,
      id: -1
    };
  }, []);

  const calculateVelocity = useCallback((currentPoint: TouchPoint, timeStamp: number): { x: number; y: number } => {
    const tracker = velocityTracker.current;

    // Add current point to tracker
    tracker.push({ point: currentPoint, time: timeStamp });

    // Keep only recent points (last 100ms)
    const cutoffTime = timeStamp - 100;
    velocityTracker.current = tracker.filter(entry => entry.time > cutoffTime);

    if (tracker.length < 2) return { x: 0, y: 0 };

    const firstEntry = tracker[0];
    const lastEntry = tracker[tracker.length - 1];
    const timeDiff = lastEntry.time - firstEntry.time;

    if (timeDiff === 0) return { x: 0, y: 0 };

    const dx = lastEntry.point.x - firstEntry.point.x;
    const dy = lastEntry.point.y - firstEntry.point.y;

    return {
      x: dx / timeDiff,
      y: dy / timeDiff
    };
  }, []);

  const clearTimeouts = useCallback(() => {
    if (tapTimeout.current) {
      clearTimeout(tapTimeout.current);
      tapTimeout.current = null;
    }
    if (longPressTimeout.current) {
      clearTimeout(longPressTimeout.current);
      longPressTimeout.current = null;
    }
  }, []);

  const resetGestureState = useCallback(() => {
    gestureState.current = {
      isActive: false,
      type: null,
      startTime: 0,
      startPoints: [],
      currentPoints: [],
      deltaX: 0,
      deltaY: 0,
      scale: 1,
      velocity: { x: 0, y: 0 }
    };
    velocityTracker.current = [];
    clearTimeouts();
  }, [clearTimeouts]);

  // Touch event handlers
  const handleTouchStart = useCallback((event: TouchEvent) => {
    event.preventDefault();

    const touches = getTouchPoints(event.touches);
    const timeStamp = Date.now();

    gestureState.current = {
      isActive: true,
      type: null,
      startTime: timeStamp,
      startPoints: touches,
      currentPoints: touches,
      deltaX: 0,
      deltaY: 0,
      scale: 1,
      velocity: { x: 0, y: 0 }
    };

    velocityTracker.current = [{ point: touches[0], time: timeStamp }];
    clearTimeouts();

    if (touches.length === 1) {
      const touch = touches[0];

      // Check for double tap
      if (lastTapTime.current && lastTapPoint.current &&
          timeStamp - lastTapTime.current < fullConfig.doubleTapTimeout &&
          getDistance(touch, lastTapPoint.current) < fullConfig.moveThreshold) {

        // Double tap detected
        gestureState.current.type = 'double-tap';
        handlers.onDoubleTap?.(touch);
        resetGestureState();
        return;
      }

      // Set up long press detection
      longPressTimeout.current = setTimeout(() => {
        if (gestureState.current.isActive && !gestureState.current.type) {
          gestureState.current.type = 'long-press';
          handlers.onLongPress?.(touch);
        }
      }, fullConfig.longPressTimeout);

    } else if (touches.length === 2) {
      // Start pinch gesture
      const center = getCenter(touches);
      const distance = getDistance(touches[0], touches[1]);

      gestureState.current.type = 'pinch';
      handlers.onPinchStart?.(center, distance);
    }
  }, [getTouchPoints, getDistance, getCenter, fullConfig, handlers, clearTimeouts, resetGestureState]);

  const handleTouchMove = useCallback((event: TouchEvent) => {
    event.preventDefault();

    if (!gestureState.current.isActive) return;

    const touches = getTouchPoints(event.touches);
    const timeStamp = Date.now();
    const state = gestureState.current;

    state.currentPoints = touches;

    if (touches.length === 1 && state.startPoints.length === 1) {
      const touch = touches[0];
      const startTouch = state.startPoints[0];

      state.deltaX = touch.x - startTouch.x;
      state.deltaY = touch.y - startTouch.y;
      state.velocity = calculateVelocity(touch, timeStamp);

      const distance = Math.sqrt(state.deltaX * state.deltaX + state.deltaY * state.deltaY);

      if (distance > fullConfig.moveThreshold) {
        clearTimeouts();

        if (!state.type) {
          // Start pan gesture
          state.type = 'pan';
          handlers.onPanStart?.(startTouch);
        }

        if (state.type === 'pan') {
          handlers.onPanMove?.(state.deltaX, state.deltaY, state.velocity);
        }
      }

    } else if (touches.length === 2 && state.startPoints.length === 2) {
      // Handle pinch gesture
      const center = getCenter(touches);
      const currentDistance = getDistance(touches[0], touches[1]);
      const startDistance = getDistance(state.startPoints[0], state.startPoints[1]);

      if (Math.abs(currentDistance - startDistance) > fullConfig.pinchThreshold) {
        state.type = 'pinch';
        state.scale = currentDistance / startDistance;
        handlers.onPinchMove?.(center, state.scale, currentDistance);
      }
    }
  }, [getTouchPoints, calculateVelocity, getCenter, getDistance, fullConfig, handlers, clearTimeouts]);

  const handleTouchEnd = useCallback((event: TouchEvent) => {
    event.preventDefault();

    if (!gestureState.current.isActive) return;

    const state = gestureState.current;
    const timeStamp = Date.now();
    const duration = timeStamp - state.startTime;

    clearTimeouts();

    if (state.type === 'pan') {
      handlers.onPanEnd?.(state.velocity);
    } else if (state.type === 'pinch') {
      handlers.onPinchEnd?.(state.scale);
    } else if (!state.type && state.startPoints.length === 1 && duration < fullConfig.tapTimeout) {
      // Simple tap
      const touch = state.startPoints[0];

      // Set up delayed tap to allow for double-tap detection
      tapTimeout.current = setTimeout(() => {
        handlers.onTap?.(touch);
      }, fullConfig.doubleTapTimeout);

      lastTapTime.current = timeStamp;
      lastTapPoint.current = touch;
    }

    resetGestureState();
  }, [handlers, fullConfig, clearTimeouts, resetGestureState]);

  const handleTouchCancel = useCallback((event: TouchEvent) => {
    event.preventDefault();
    resetGestureState();
  }, [resetGestureState]);

  // Set up event listeners
  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    // Add touch event listeners
    element.addEventListener('touchstart', handleTouchStart, { passive: false });
    element.addEventListener('touchmove', handleTouchMove, { passive: false });
    element.addEventListener('touchend', handleTouchEnd, { passive: false });
    element.addEventListener('touchcancel', handleTouchCancel, { passive: false });

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
      element.removeEventListener('touchcancel', handleTouchCancel);
      clearTimeouts();
    };
  }, [elementRef, handleTouchStart, handleTouchMove, handleTouchEnd, handleTouchCancel, clearTimeouts]);

  return {
    gestureState: gestureState.current,
    resetGestures: resetGestureState
  };
};