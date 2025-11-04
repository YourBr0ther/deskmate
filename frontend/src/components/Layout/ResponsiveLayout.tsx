/**
 * Main responsive layout component for DeskMate.
 *
 * This component automatically selects the appropriate layout based on
 * device type and screen size, providing optimal user experience across
 * mobile, tablet, and desktop devices.
 */

import React, { Suspense } from 'react';
import { useDeviceDetection } from '../../hooks/useDeviceDetection';

// Lazy load layout components for better performance
const DesktopLayout = React.lazy(() => import('./DesktopLayout'));
const TabletLayout = React.lazy(() => import('./TabletLayout'));
const MobileLayout = React.lazy(() => import('./MobileLayout'));

interface ResponsiveLayoutProps {
  children?: React.ReactNode;
}

/**
 * Loading component displayed while layout components are loading.
 */
const LayoutLoading: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-100">
    <div className="text-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading DeskMate...</p>
    </div>
  </div>
);

/**
 * Error boundary for layout components.
 */
interface LayoutErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class LayoutErrorBoundary extends React.Component<
  { children: React.ReactNode; deviceType: string },
  LayoutErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode; deviceType: string }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): LayoutErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Layout Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-red-50">
          <div className="text-center p-8">
            <h2 className="text-xl font-semibold text-red-800 mb-4">
              Layout Error
            </h2>
            <p className="text-red-600 mb-4">
              Failed to load {this.props.deviceType} layout
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Main responsive layout component.
 */
export const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({
  children
}) => {
  const deviceInfo = useDeviceDetection();

  // Add debug info in development
  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('Device Info:', deviceInfo);
    }
  }, [deviceInfo]);

  // Select the appropriate layout component
  const getLayoutComponent = () => {
    switch (deviceInfo.type) {
      case 'mobile':
        return <MobileLayout />;
      case 'tablet':
        return <TabletLayout />;
      case 'desktop':
      default:
        return <DesktopLayout />;
    }
  };

  return (
    <div
      className="responsive-layout w-full h-screen overflow-hidden"
      data-device-type={deviceInfo.type}
      data-orientation={deviceInfo.orientation}
      style={{
        // CSS custom properties for responsive styling
        '--device-type': deviceInfo.type,
        '--screen-width': `${deviceInfo.screenWidth}px`,
        '--screen-height': `${deviceInfo.screenHeight}px`,
        '--is-touch': deviceInfo.isTouch ? '1' : '0',
        '--pixel-ratio': deviceInfo.pixelRatio.toString()
      } as React.CSSProperties}
    >
      <LayoutErrorBoundary deviceType={deviceInfo.type}>
        <Suspense fallback={<LayoutLoading />}>
          {getLayoutComponent()}
        </Suspense>
      </LayoutErrorBoundary>

      {/* Render children if provided (for testing or special cases) */}
      {children}

      {/* Development device info overlay */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed top-2 left-2 bg-black bg-opacity-75 text-white text-xs p-2 rounded z-50">
          <div>Device: {deviceInfo.type}</div>
          <div>Size: {deviceInfo.screenWidth}x{deviceInfo.screenHeight}</div>
          <div>Touch: {deviceInfo.isTouch ? 'Yes' : 'No'}</div>
          <div>Orientation: {deviceInfo.orientation}</div>
        </div>
      )}
    </div>
  );
};

export default ResponsiveLayout;