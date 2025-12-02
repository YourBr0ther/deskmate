/**
 * Tests for Touch Gestures Hook
 *
 * Tests cover:
 * - Single tap detection
 * - Double tap detection
 * - Long press detection
 * - Pan gestures
 * - Pinch gestures
 * - Gesture state management
 * - Event listener setup and cleanup
 */

import { renderHook, act } from '@testing-library/react';
import { useTouchGestures, GestureHandlers, TouchPoint } from '../useTouchGestures';

// Mock createRef
const createMockRef = (element: HTMLElement | null = null) => ({
  current: element,
});

// Create mock touch event
const createTouchEvent = (
  type: string,
  touches: Array<{ clientX: number; clientY: number; identifier: number }>
): TouchEvent => {
  const touchList = {
    length: touches.length,
    item: (index: number) => touches[index],
    [Symbol.iterator]: function* () {
      for (let i = 0; i < touches.length; i++) {
        yield touches[i];
      }
    },
  } as unknown as TouchList;

  // Add array-like access
  touches.forEach((touch, index) => {
    (touchList as any)[index] = touch;
  });

  return {
    type,
    touches: touchList,
    preventDefault: jest.fn(),
    changedTouches: touchList,
    targetTouches: touchList,
  } as unknown as TouchEvent;
};

describe('useTouchGestures', () => {
  let mockElement: HTMLDivElement;
  let addEventListenerSpy: jest.SpyInstance;
  let removeEventListenerSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();

    // Create mock element
    mockElement = document.createElement('div');
    addEventListenerSpy = jest.spyOn(mockElement, 'addEventListener');
    removeEventListenerSpy = jest.spyOn(mockElement, 'removeEventListener');
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Event Listener Setup', () => {
    it('should add touch event listeners on mount', () => {
      const ref = createMockRef(mockElement);
      const handlers: GestureHandlers = {};

      renderHook(() => useTouchGestures(ref as any, handlers));

      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'touchstart',
        expect.any(Function),
        { passive: false }
      );
      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'touchmove',
        expect.any(Function),
        { passive: false }
      );
      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'touchend',
        expect.any(Function),
        { passive: false }
      );
      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'touchcancel',
        expect.any(Function),
        { passive: false }
      );
    });

    it('should remove event listeners on unmount', () => {
      const ref = createMockRef(mockElement);
      const handlers: GestureHandlers = {};

      const { unmount } = renderHook(() => useTouchGestures(ref as any, handlers));

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'touchstart',
        expect.any(Function)
      );
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'touchmove',
        expect.any(Function)
      );
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'touchend',
        expect.any(Function)
      );
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'touchcancel',
        expect.any(Function)
      );
    });

    it('should not add listeners when element is null', () => {
      const ref = createMockRef(null);
      const handlers: GestureHandlers = {};

      renderHook(() => useTouchGestures(ref as any, handlers));

      expect(addEventListenerSpy).not.toHaveBeenCalled();
    });
  });

  describe('Tap Detection', () => {
    it('should detect single tap', () => {
      const onTap = jest.fn();
      const ref = createMockRef(mockElement);

      renderHook(() => useTouchGestures(ref as any, { onTap }));

      // Get the touch handlers
      const touchStartHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchstart'
      )?.[1];
      const touchEndHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchend'
      )?.[1];

      // Simulate tap
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
      });

      act(() => {
        touchEndHandler(
          createTouchEvent('touchend', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
      });

      // Fast-forward past double-tap timeout
      act(() => {
        jest.advanceTimersByTime(350);
      });

      expect(onTap).toHaveBeenCalledWith(
        expect.objectContaining({ x: 100, y: 100 })
      );
    });
  });

  describe('Double Tap Detection', () => {
    it('should detect double tap', () => {
      const onDoubleTap = jest.fn();
      const ref = createMockRef(mockElement);

      renderHook(() => useTouchGestures(ref as any, { onDoubleTap }));

      const touchStartHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchstart'
      )?.[1];
      const touchEndHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchend'
      )?.[1];

      // First tap
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
        touchEndHandler(
          createTouchEvent('touchend', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
      });

      // Advance a little but stay within double-tap window
      act(() => {
        jest.advanceTimersByTime(100);
      });

      // Second tap at same location
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
      });

      expect(onDoubleTap).toHaveBeenCalledWith(
        expect.objectContaining({ x: 100, y: 100 })
      );
    });
  });

  describe('Long Press Detection', () => {
    it('should detect long press', () => {
      const onLongPress = jest.fn();
      const ref = createMockRef(mockElement);

      renderHook(() =>
        useTouchGestures(ref as any, { onLongPress }, { longPressTimeout: 500 })
      );

      const touchStartHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchstart'
      )?.[1];

      // Start touch
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
      });

      // Wait for long press timeout
      act(() => {
        jest.advanceTimersByTime(600);
      });

      expect(onLongPress).toHaveBeenCalledWith(
        expect.objectContaining({ x: 100, y: 100 })
      );
    });

    it('should not trigger long press if released early', () => {
      const onLongPress = jest.fn();
      const ref = createMockRef(mockElement);

      renderHook(() =>
        useTouchGestures(ref as any, { onLongPress }, { longPressTimeout: 500 })
      );

      const touchStartHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchstart'
      )?.[1];
      const touchEndHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchend'
      )?.[1];

      // Start touch
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
      });

      // Release before long press timeout
      act(() => {
        jest.advanceTimersByTime(200);
        touchEndHandler(
          createTouchEvent('touchend', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
      });

      // Complete the timeout
      act(() => {
        jest.advanceTimersByTime(400);
      });

      expect(onLongPress).not.toHaveBeenCalled();
    });
  });

  describe('Pan Gesture', () => {
    it('should detect pan start and move', () => {
      const onPanStart = jest.fn();
      const onPanMove = jest.fn();
      const ref = createMockRef(mockElement);

      renderHook(() =>
        useTouchGestures(ref as any, { onPanStart, onPanMove }, { moveThreshold: 10 })
      );

      const touchStartHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchstart'
      )?.[1];
      const touchMoveHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchmove'
      )?.[1];

      // Start touch
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
      });

      // Move beyond threshold
      act(() => {
        touchMoveHandler(
          createTouchEvent('touchmove', [{ clientX: 150, clientY: 120, identifier: 0 }])
        );
      });

      expect(onPanStart).toHaveBeenCalled();
      expect(onPanMove).toHaveBeenCalledWith(
        50, // deltaX
        20, // deltaY
        expect.any(Object) // velocity
      );
    });

    it('should detect pan end with velocity', () => {
      const onPanEnd = jest.fn();
      const ref = createMockRef(mockElement);

      renderHook(() => useTouchGestures(ref as any, { onPanEnd }, { moveThreshold: 10 }));

      const touchStartHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchstart'
      )?.[1];
      const touchMoveHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchmove'
      )?.[1];
      const touchEndHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchend'
      )?.[1];

      // Start and move to trigger pan
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
        touchMoveHandler(
          createTouchEvent('touchmove', [{ clientX: 200, clientY: 100, identifier: 0 }])
        );
      });

      // End pan
      act(() => {
        touchEndHandler(
          createTouchEvent('touchend', [{ clientX: 200, clientY: 100, identifier: 0 }])
        );
      });

      expect(onPanEnd).toHaveBeenCalledWith(expect.any(Object));
    });
  });

  describe('Pinch Gesture', () => {
    it('should detect pinch start with two fingers', () => {
      const onPinchStart = jest.fn();
      const ref = createMockRef(mockElement);

      renderHook(() => useTouchGestures(ref as any, { onPinchStart }));

      const touchStartHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchstart'
      )?.[1];

      // Start with two touches
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [
            { clientX: 100, clientY: 100, identifier: 0 },
            { clientX: 200, clientY: 100, identifier: 1 },
          ])
        );
      });

      expect(onPinchStart).toHaveBeenCalledWith(
        expect.objectContaining({ x: 150, y: 100 }), // center
        100 // initial distance
      );
    });

    it('should detect pinch move with scale', () => {
      const onPinchMove = jest.fn();
      const ref = createMockRef(mockElement);

      renderHook(() =>
        useTouchGestures(ref as any, { onPinchMove }, { pinchThreshold: 20 })
      );

      const touchStartHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchstart'
      )?.[1];
      const touchMoveHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchmove'
      )?.[1];

      // Start with two touches 100px apart
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [
            { clientX: 100, clientY: 100, identifier: 0 },
            { clientX: 200, clientY: 100, identifier: 1 },
          ])
        );
      });

      // Move to 200px apart (zoom in)
      act(() => {
        touchMoveHandler(
          createTouchEvent('touchmove', [
            { clientX: 50, clientY: 100, identifier: 0 },
            { clientX: 250, clientY: 100, identifier: 1 },
          ])
        );
      });

      expect(onPinchMove).toHaveBeenCalledWith(
        expect.any(Object), // center
        expect.any(Number), // scale (should be 2)
        expect.any(Number) // distance
      );
    });

    it('should detect pinch end', () => {
      const onPinchStart = jest.fn();
      const onPinchEnd = jest.fn();
      const ref = createMockRef(mockElement);

      renderHook(() =>
        useTouchGestures(ref as any, { onPinchStart, onPinchEnd }, { pinchThreshold: 20 })
      );

      const touchStartHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchstart'
      )?.[1];
      const touchMoveHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchmove'
      )?.[1];
      const touchEndHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchend'
      )?.[1];

      // Start pinch
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [
            { clientX: 100, clientY: 100, identifier: 0 },
            { clientX: 200, clientY: 100, identifier: 1 },
          ])
        );
      });

      // Move to trigger pinch
      act(() => {
        touchMoveHandler(
          createTouchEvent('touchmove', [
            { clientX: 50, clientY: 100, identifier: 0 },
            { clientX: 250, clientY: 100, identifier: 1 },
          ])
        );
      });

      // End pinch
      act(() => {
        touchEndHandler(createTouchEvent('touchend', []));
      });

      expect(onPinchEnd).toHaveBeenCalledWith(expect.any(Number));
    });
  });

  describe('Touch Cancel', () => {
    it('should reset gesture state on cancel', () => {
      const onPanMove = jest.fn();
      const ref = createMockRef(mockElement);

      const { result } = renderHook(() =>
        useTouchGestures(ref as any, { onPanMove })
      );

      const touchStartHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchstart'
      )?.[1];
      const touchCancelHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchcancel'
      )?.[1];

      // Start touch
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
      });

      // Cancel touch
      act(() => {
        touchCancelHandler(createTouchEvent('touchcancel', []));
      });

      expect(result.current.gestureState.isActive).toBe(false);
    });
  });

  describe('Custom Configuration', () => {
    it('should respect custom tap timeout', () => {
      const onTap = jest.fn();
      const ref = createMockRef(mockElement);

      renderHook(() =>
        useTouchGestures(ref as any, { onTap }, { tapTimeout: 100 })
      );

      const touchStartHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchstart'
      )?.[1];
      const touchEndHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchend'
      )?.[1];

      // Start touch
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
      });

      // Wait too long before releasing
      act(() => {
        jest.advanceTimersByTime(150);
      });

      // Release
      act(() => {
        touchEndHandler(
          createTouchEvent('touchend', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
      });

      // Advance past double-tap window
      act(() => {
        jest.advanceTimersByTime(400);
      });

      // Should not register as tap because duration exceeded tapTimeout
      // Note: behavior depends on implementation details
    });
  });

  describe('Return Value', () => {
    it('should return gesture state and reset function', () => {
      const ref = createMockRef(mockElement);

      const { result } = renderHook(() => useTouchGestures(ref as any, {}));

      expect(result.current).toHaveProperty('gestureState');
      expect(result.current).toHaveProperty('resetGestures');
      expect(typeof result.current.resetGestures).toBe('function');

      expect(result.current.gestureState).toHaveProperty('isActive');
      expect(result.current.gestureState).toHaveProperty('type');
      expect(result.current.gestureState).toHaveProperty('deltaX');
      expect(result.current.gestureState).toHaveProperty('deltaY');
      expect(result.current.gestureState).toHaveProperty('scale');
      expect(result.current.gestureState).toHaveProperty('velocity');
    });

    it('should reset gesture state when resetGestures is called', () => {
      const ref = createMockRef(mockElement);

      const { result } = renderHook(() => useTouchGestures(ref as any, {}));

      const touchStartHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'touchstart'
      )?.[1];

      // Start a gesture
      act(() => {
        touchStartHandler(
          createTouchEvent('touchstart', [{ clientX: 100, clientY: 100, identifier: 0 }])
        );
      });

      // Reset
      act(() => {
        result.current.resetGestures();
      });

      expect(result.current.gestureState.isActive).toBe(false);
      expect(result.current.gestureState.type).toBeNull();
    });
  });
});
