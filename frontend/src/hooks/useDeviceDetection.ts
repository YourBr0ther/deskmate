/**
 * Device detection hook for responsive layout management.
 *
 * This hook provides device type detection and responsive breakpoint
 * management for the multi-device DeskMate interface.
 */

import { useState, useEffect } from 'react';

export type DeviceType = 'mobile' | 'tablet' | 'desktop';

export interface DeviceInfo {
  type: DeviceType;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  screenWidth: number;
  screenHeight: number;
  orientation: 'portrait' | 'landscape';
  isTouch: boolean;
  pixelRatio: number;
}

export interface ResponsiveBreakpoints {
  mobile: number;
  tablet: number;
  desktop: number;
}

const DEFAULT_BREAKPOINTS: ResponsiveBreakpoints = {
  mobile: 768,    // < 768px = mobile
  tablet: 1024,   // 768px - 1024px = tablet
  desktop: 1025   // >= 1025px = desktop
};

/**
 * Hook for detecting device type and responsive breakpoints.
 */
export const useDeviceDetection = (customBreakpoints?: Partial<ResponsiveBreakpoints>) => {
  const breakpoints = { ...DEFAULT_BREAKPOINTS, ...customBreakpoints };

  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo>(() => {
    // Initialize with default values for SSR compatibility
    return {
      type: 'desktop' as DeviceType,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      screenWidth: 1920,
      screenHeight: 1080,
      orientation: 'landscape' as const,
      isTouch: false,
      pixelRatio: 1
    };
  });

  const detectDevice = () => {
    if (typeof window === 'undefined') return;

    const width = window.innerWidth;
    const height = window.innerHeight;
    const pixelRatio = window.devicePixelRatio || 1;
    const orientation = width > height ? 'landscape' : 'portrait';

    // Device type detection based on screen width
    let type: DeviceType;
    if (width < breakpoints.mobile) {
      type = 'mobile';
    } else if (width < breakpoints.desktop) {
      type = 'tablet';
    } else {
      type = 'desktop';
    }

    // Touch capability detection
    const isTouch = 'ontouchstart' in window ||
                   navigator.maxTouchPoints > 0 ||
                   (navigator as any).msMaxTouchPoints > 0;

    // User agent based mobile detection (fallback)
    const userAgent = navigator.userAgent.toLowerCase();
    const isMobileUA = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);

    // Final mobile detection combines screen size and UA
    const isMobileDevice = type === 'mobile' || (isTouch && isMobileUA);

    setDeviceInfo({
      type: isMobileDevice ? 'mobile' : type,
      isMobile: isMobileDevice,
      isTablet: type === 'tablet' && !isMobileDevice,
      isDesktop: type === 'desktop' && !isMobileDevice,
      screenWidth: width,
      screenHeight: height,
      orientation,
      isTouch,
      pixelRatio
    });
  };

  useEffect(() => {
    // Initial detection
    detectDevice();

    // Listen for resize events
    const handleResize = () => {
      detectDevice();
    };

    // Listen for orientation changes
    const handleOrientationChange = () => {
      // Delay to ensure dimensions are updated
      setTimeout(detectDevice, 100);
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleOrientationChange);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleOrientationChange);
    };
  }, []);

  return deviceInfo;
};

/**
 * Hook for responsive value selection based on device type.
 */
export const useResponsiveValue = <T>(values: {
  mobile: T;
  tablet?: T;
  desktop: T;
}): T => {
  const { type } = useDeviceDetection();

  switch (type) {
    case 'mobile':
      return values.mobile;
    case 'tablet':
      return values.tablet || values.desktop;
    case 'desktop':
    default:
      return values.desktop;
  }
};

/**
 * Hook for media query matching.
 */
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);

    const handler = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    mediaQuery.addListener(handler);
    return () => mediaQuery.removeListener(handler);
  }, [query]);

  return matches;
};

/**
 * Predefined media queries for common breakpoints.
 */
export const mediaQueries = {
  mobile: '(max-width: 767px)',
  tablet: '(min-width: 768px) and (max-width: 1024px)',
  desktop: '(min-width: 1025px)',
  touch: '(pointer: coarse)',
  hover: '(hover: hover)',
  portrait: '(orientation: portrait)',
  landscape: '(orientation: landscape)',
  highDPI: '(-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi)'
};

/**
 * Hook for detecting specific device capabilities.
 */
export const useDeviceCapabilities = () => {
  const deviceInfo = useDeviceDetection();

  return {
    hasTouch: deviceInfo.isTouch,
    hasHover: !deviceInfo.isMobile,
    supportsPointerEvents: 'PointerEvent' in window,
    supportsGestures: deviceInfo.isTouch && deviceInfo.isMobile,
    prefersPreciseInput: deviceInfo.isDesktop,
    hasLimitedViewport: deviceInfo.isMobile,
    canMultitask: deviceInfo.isDesktop || deviceInfo.isTablet,
    needsLargeTargets: deviceInfo.isTouch,
    supportsKeyboard: deviceInfo.isDesktop || deviceInfo.isTablet
  };
};

/**
 * Hook for getting device-specific layout configuration.
 */
export const useLayoutConfig = () => {
  const deviceInfo = useDeviceDetection();

  return {
    chatPanelWidth: deviceInfo.isMobile ? '100%' : '30%',
    floorPlanWidth: deviceInfo.isMobile ? '100%' : '70%',
    showSideBySide: !deviceInfo.isMobile,
    useOverlays: deviceInfo.isMobile,
    minTouchTarget: deviceInfo.isTouch ? 44 : 24,
    padding: deviceInfo.isMobile ? 8 : 16,
    fontSize: {
      small: deviceInfo.isMobile ? 12 : 11,
      normal: deviceInfo.isMobile ? 14 : 13,
      large: deviceInfo.isMobile ? 16 : 15
    },
    layout: deviceInfo.isMobile ? 'stacked' : deviceInfo.isTablet ? 'collapsible' : 'split'
  };
};