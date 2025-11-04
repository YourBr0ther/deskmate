/**
 * Mobile layout component for DeskMate.
 *
 * Provides a full-screen floor plan view with a floating chat widget
 * that can be minimized, partially expanded, or fully expanded.
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useDeviceDetection, useLayoutConfig } from '../../hooks/useDeviceDetection';

// Phase 12B Mobile Components
const MobileFloorPlan = React.lazy(() => import('../FloorPlan/MobileFloorPlan'));
const FloatingChatWidget = React.lazy(() => import('../Chat/FloatingChatWidget'));

interface MobileLayoutProps {
  children?: React.ReactNode;
}

type ChatWidgetState = 'minimized' | 'partial' | 'expanded';

/**
 * Mobile layout component with floating chat widget.
 */
export const MobileLayout: React.FC<MobileLayoutProps> = ({ children }) => {
  const deviceInfo = useDeviceDetection();
  const layoutConfig = useLayoutConfig();
  const [chatState, setChatState] = useState<ChatWidgetState>('minimized');
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [currentRoom, setCurrentRoom] = useState('Living Room');

  // Check if this is the user's first visit
  useEffect(() => {
    const hasVisited = localStorage.getItem('deskmate-mobile-visited');
    if (!hasVisited) {
      setShowOnboarding(true);
      localStorage.setItem('deskmate-mobile-visited', 'true');
    }
  }, []);

  // Handle back button for Android
  useEffect(() => {
    const handleBackButton = () => {
      if (chatState === 'expanded') {
        setChatState('minimized');
        return false; // Prevent default back behavior
      }
      return true; // Allow default back behavior
    };

    // Listen for Android back button
    const handlePopState = () => {
      handleBackButton();
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [chatState]);

  const handleChatStateChange = useCallback((newState: ChatWidgetState) => {
    setChatState(newState);

    // Add browser history entry for expanded state (Android back button support)
    if (newState === 'expanded' && chatState !== 'expanded') {
      window.history.pushState({ chatExpanded: true }, '');
    }
  }, [chatState]);

  const renderMobileHeader = () => (
    <div className="mobile-header bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between relative z-10">
      <div className="flex items-center space-x-3">
        <h1 className="text-lg font-semibold text-gray-800">DeskMate</h1>

        {/* Current Room Indicator */}
        <div className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
          {currentRoom}
        </div>
      </div>

      {/* Mobile Controls */}
      <div className="flex items-center space-x-2">
        {/* Room Selector */}
        <button
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full active:bg-gray-200"
          onClick={() => {/* Open room selector */}}
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>

        {/* Settings Menu */}
        <button
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full active:bg-gray-200"
          onClick={() => {/* Open settings */}}
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
    </div>
  );

  const renderOnboardingOverlay = () => {
    if (!showOnboarding) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg p-6 max-w-sm w-full text-center">
          <div className="mb-4">
            <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl">👋</span>
            </div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">Welcome to DeskMate!</h2>
            <p className="text-gray-600 text-sm">
              Tap objects to interact, pinch to zoom, and tap the chat bubble to talk with your AI assistant.
            </p>
          </div>

          <div className="space-y-3 mb-6">
            <div className="flex items-center space-x-3 text-left">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 text-sm">👆</span>
              </div>
              <span className="text-sm text-gray-700">Tap objects to interact</span>
            </div>
            <div className="flex items-center space-x-3 text-left">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 text-sm">🤏</span>
              </div>
              <span className="text-sm text-gray-700">Pinch to zoom and pan</span>
            </div>
            <div className="flex items-center space-x-3 text-left">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 text-sm">💬</span>
              </div>
              <span className="text-sm text-gray-700">Tap chat to talk with assistant</span>
            </div>
          </div>

          <button
            onClick={() => setShowOnboarding(false)}
            className="w-full bg-blue-500 text-white py-3 rounded-lg font-medium hover:bg-blue-600 active:bg-blue-700"
          >
            Got it!
          </button>
        </div>
      </div>
    );
  };

  const renderStatusBar = () => (
    <div className="mobile-status-bar bg-white border-t border-gray-200 px-4 py-2 flex items-center justify-between text-sm text-gray-600">
      <div className="flex items-center space-x-4">
        <span>Assistant: Living Room</span>
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
          <span>Active</span>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex items-center space-x-2">
        <button className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
          Center
        </button>
        <button className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
          Fit
        </button>
      </div>
    </div>
  );

  return (
    <div
      className="mobile-layout flex flex-col h-screen w-full bg-gray-50 relative overflow-hidden"
      data-chat-state={chatState}
      data-orientation={deviceInfo.orientation}
    >
      {/* Mobile Header */}
      {renderMobileHeader()}

      {/* Floor Plan Container */}
      <div className="floor-plan-container flex-1 relative overflow-hidden">
        <React.Suspense
          fallback={
            <div className="flex items-center justify-center h-full bg-gray-100">
              <div className="text-center">
                <div className="animate-pulse bg-gray-300 h-4 w-32 rounded mb-2"></div>
                <div className="animate-pulse bg-gray-300 h-3 w-24 rounded"></div>
              </div>
            </div>
          }
        >
          <MobileFloorPlan />
        </React.Suspense>

        {/* Floor Plan Overlay (dimmed when chat is expanded) */}
        {chatState === 'expanded' && (
          <div
            className="absolute inset-0 bg-black bg-opacity-30 z-20"
            onClick={() => handleChatStateChange('minimized')}
          />
        )}
      </div>

      {/* Status Bar */}
      {chatState !== 'expanded' && renderStatusBar()}

      {/* Floating Chat Widget */}
      <React.Suspense fallback={null}>
        <FloatingChatWidget
          state={chatState}
          onStateChange={handleChatStateChange}
        />
      </React.Suspense>

      {/* Onboarding Overlay */}
      {renderOnboardingOverlay()}

      {/* Render children if provided */}
      {children}

      {/* Mobile-specific styles */}
      <style>
        {`
        .mobile-layout {
          /* Prevent zoom on double tap */
          touch-action: pan-x pan-y;
          /* Prevent text selection */
          user-select: none;
          -webkit-user-select: none;
          /* Prevent callouts on long press */
          -webkit-touch-callout: none;
        }

        /* Ensure buttons are touch-friendly */
        .mobile-layout button {
          min-height: 44px;
          min-width: 44px;
        }

        /* Smooth transitions */
        .floor-plan-container {
          transition: opacity 0.3s ease;
        }

        /* Safe area handling for notched devices */
        .mobile-header {
          padding-top: max(12px, env(safe-area-inset-top));
        }

        .mobile-status-bar {
          padding-bottom: max(8px, env(safe-area-inset-bottom));
        }

        /* Prevent overscroll bounce */
        .mobile-layout {
          overscroll-behavior: contain;
        }

        /* Handle landscape orientation */
        @media (orientation: landscape) {
          .mobile-header {
            padding-top: 8px;
            padding-bottom: 8px;
          }
        }

        /* Dark theme for OLED screens */
        @media (prefers-color-scheme: dark) {
          .mobile-layout {
            background-color: #111827;
          }
        }
        `}
      </style>
    </div>
  );
};

export default MobileLayout;