/**
 * Tests for Device Detection Hooks
 *
 * Tests cover:
 * - useDeviceDetection - device type and screen detection
 * - useResponsiveValue - responsive value selection
 * - useMediaQuery - media query matching
 * - useDeviceCapabilities - device capability detection
 * - useLayoutConfig - layout configuration
 */

import { renderHook, act } from '@testing-library/react';
import {
  useDeviceDetection,
  useResponsiveValue,
  useMediaQuery,
  useDeviceCapabilities,
  useLayoutConfig,
  DeviceInfo,
} from '../useDeviceDetection';

// Mock window properties
const mockWindow = (width: number, height: number, isTouch = false) => {
  Object.defineProperty(window, 'innerWidth', { value: width, writable: true });
  Object.defineProperty(window, 'innerHeight', { value: height, writable: true });
  Object.defineProperty(window, 'devicePixelRatio', { value: 1, writable: true });

  // Mock touch detection
  if (isTouch) {
    Object.defineProperty(window, 'ontouchstart', { value: () => {}, writable: true });
  } else {
    delete (window as any).ontouchstart;
  }

  Object.defineProperty(navigator, 'maxTouchPoints', { value: isTouch ? 1 : 0, writable: true });
  Object.defineProperty(navigator, 'userAgent', {
    value: isTouch
      ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
      : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    writable: true,
  });
};

// Mock matchMedia
const mockMatchMedia = (matches: boolean) => {
  window.matchMedia = jest.fn().mockImplementation((query) => ({
    matches,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }));
};

describe('useDeviceDetection', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Desktop Detection', () => {
    it('should detect desktop for large screens', () => {
      mockWindow(1920, 1080);

      const { result } = renderHook(() => useDeviceDetection());

      expect(result.current.type).toBe('desktop');
      expect(result.current.isDesktop).toBe(true);
      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(false);
    });

    it('should return correct screen dimensions', () => {
      mockWindow(1920, 1080);

      const { result } = renderHook(() => useDeviceDetection());

      expect(result.current.screenWidth).toBe(1920);
      expect(result.current.screenHeight).toBe(1080);
    });

    it('should detect landscape orientation for wider screens', () => {
      mockWindow(1920, 1080);

      const { result } = renderHook(() => useDeviceDetection());

      expect(result.current.orientation).toBe('landscape');
    });
  });

  describe('Tablet Detection', () => {
    it('should detect tablet for medium screens', () => {
      mockWindow(800, 600);

      const { result } = renderHook(() => useDeviceDetection());

      expect(result.current.type).toBe('tablet');
      expect(result.current.isTablet).toBe(true);
    });
  });

  describe('Mobile Detection', () => {
    it('should detect mobile for small screens', () => {
      mockWindow(375, 667, true);

      const { result } = renderHook(() => useDeviceDetection());

      expect(result.current.type).toBe('mobile');
      expect(result.current.isMobile).toBe(true);
    });

    it('should detect portrait orientation for taller screens', () => {
      mockWindow(375, 667);

      const { result } = renderHook(() => useDeviceDetection());

      expect(result.current.orientation).toBe('portrait');
    });

    it('should detect touch capability', () => {
      mockWindow(375, 667, true);

      const { result } = renderHook(() => useDeviceDetection());

      expect(result.current.isTouch).toBe(true);
    });
  });

  describe('Custom Breakpoints', () => {
    it('should respect custom breakpoints', () => {
      mockWindow(900, 600);

      const customBreakpoints = {
        mobile: 600,
        tablet: 900,
        desktop: 901,
      };

      const { result } = renderHook(() => useDeviceDetection(customBreakpoints));

      // 900px with tablet breakpoint at 900 should be tablet
      expect(result.current.type).toBe('tablet');
    });
  });

  describe('Resize Events', () => {
    it('should update on window resize', () => {
      mockWindow(1920, 1080);

      const { result } = renderHook(() => useDeviceDetection());

      expect(result.current.type).toBe('desktop');

      // Simulate resize to mobile
      act(() => {
        mockWindow(375, 667, true);
        window.dispatchEvent(new Event('resize'));
      });

      expect(result.current.type).toBe('mobile');
    });
  });
});

describe('useResponsiveValue', () => {
  it('should return mobile value on mobile', () => {
    mockWindow(375, 667, true);

    const { result } = renderHook(() =>
      useResponsiveValue({
        mobile: 'mobile-value',
        tablet: 'tablet-value',
        desktop: 'desktop-value',
      })
    );

    expect(result.current).toBe('mobile-value');
  });

  it('should return desktop value on desktop', () => {
    mockWindow(1920, 1080);

    const { result } = renderHook(() =>
      useResponsiveValue({
        mobile: 'mobile-value',
        desktop: 'desktop-value',
      })
    );

    expect(result.current).toBe('desktop-value');
  });

  it('should fallback to desktop when tablet value not provided', () => {
    mockWindow(800, 600);

    const { result } = renderHook(() =>
      useResponsiveValue({
        mobile: 'mobile-value',
        desktop: 'desktop-value',
      })
    );

    expect(result.current).toBe('desktop-value');
  });
});

describe('useMediaQuery', () => {
  it('should return true when media query matches', () => {
    mockMatchMedia(true);

    const { result } = renderHook(() => useMediaQuery('(min-width: 1024px)'));

    expect(result.current).toBe(true);
  });

  it('should return false when media query does not match', () => {
    mockMatchMedia(false);

    const { result } = renderHook(() => useMediaQuery('(min-width: 1024px)'));

    expect(result.current).toBe(false);
  });
});

describe('useDeviceCapabilities', () => {
  it('should detect touch capabilities on mobile', () => {
    mockWindow(375, 667, true);

    const { result } = renderHook(() => useDeviceCapabilities());

    expect(result.current.hasTouch).toBe(true);
    expect(result.current.hasLimitedViewport).toBe(true);
    expect(result.current.needsLargeTargets).toBe(true);
  });

  it('should detect hover capability on desktop', () => {
    mockWindow(1920, 1080);

    const { result } = renderHook(() => useDeviceCapabilities());

    expect(result.current.hasHover).toBe(true);
    expect(result.current.prefersPreciseInput).toBe(true);
    expect(result.current.canMultitask).toBe(true);
  });
});

describe('useLayoutConfig', () => {
  it('should return mobile layout config on mobile', () => {
    mockWindow(375, 667, true);

    const { result } = renderHook(() => useLayoutConfig());

    expect(result.current.chatPanelWidth).toBe('100%');
    expect(result.current.floorPlanWidth).toBe('100%');
    expect(result.current.showSideBySide).toBe(false);
    expect(result.current.useOverlays).toBe(true);
    expect(result.current.layout).toBe('stacked');
  });

  it('should return desktop layout config on desktop', () => {
    mockWindow(1920, 1080);

    const { result } = renderHook(() => useLayoutConfig());

    expect(result.current.chatPanelWidth).toBe('30%');
    expect(result.current.floorPlanWidth).toBe('70%');
    expect(result.current.showSideBySide).toBe(true);
    expect(result.current.useOverlays).toBe(false);
    expect(result.current.layout).toBe('split');
  });

  it('should return larger touch targets on touch devices', () => {
    mockWindow(375, 667, true);

    const { result } = renderHook(() => useLayoutConfig());

    expect(result.current.minTouchTarget).toBe(44);
  });

  it('should return smaller targets on non-touch devices', () => {
    mockWindow(1920, 1080);

    const { result } = renderHook(() => useLayoutConfig());

    expect(result.current.minTouchTarget).toBe(24);
  });
});
