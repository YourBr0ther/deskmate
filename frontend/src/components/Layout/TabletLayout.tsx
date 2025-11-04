/**
 * Tablet layout component for DeskMate.
 *
 * Provides an adaptive layout that can switch between split and stacked modes
 * depending on orientation and user preference.
 */

import React, { useState } from 'react';
import { useDeviceDetection, useLayoutConfig } from '../../hooks/useDeviceDetection';

// Placeholder components - these will be implemented in later tasks
const FloorPlanContainer = React.lazy(() =>
  import('../FloorPlan/FloorPlanContainer').catch(() => ({
    default: () => <div className="flex-1 bg-gray-100 flex items-center justify-center">Floor Plan (Coming Soon)</div>
  }))
);

const ChatContainer = React.lazy(() =>
  import('../Chat/ChatContainer').catch(() => ({
    default: () => <div className="w-full h-full bg-white flex items-center justify-center">Chat (Coming Soon)</div>
  }))
);

interface TabletLayoutProps {
  children?: React.ReactNode;
}

type TabletLayoutMode = 'split' | 'stacked' | 'floor-plan-only' | 'chat-only';

/**
 * Tablet adaptive layout component.
 */
export const TabletLayout: React.FC<TabletLayoutProps> = ({ children }) => {
  const deviceInfo = useDeviceDetection();
  const layoutConfig = useLayoutConfig();
  const [layoutMode, setLayoutMode] = useState<TabletLayoutMode>('split');
  const [chatCollapsed, setChatCollapsed] = useState(false);

  // Auto-adjust layout based on orientation
  React.useEffect(() => {
    if (deviceInfo.orientation === 'portrait') {
      setLayoutMode('stacked');
    } else if (deviceInfo.orientation === 'landscape') {
      setLayoutMode('split');
    }
  }, [deviceInfo.orientation]);

  const renderSplitLayout = () => (
    <div className="tablet-split-layout flex h-screen w-full">
      {/* Floor Plan Panel */}
      <div className={`floor-plan-panel flex flex-col transition-all duration-300 ${
        chatCollapsed ? 'w-full' : 'w-3/5'
      }`}>
        {renderFloorPlanHeader()}
        <div className="floor-plan-content flex-1 overflow-hidden">
          <React.Suspense fallback={<div className="flex items-center justify-center h-full">Loading Floor Plan...</div>}>
            <FloorPlanContainer />
          </React.Suspense>
        </div>
        {renderFloorPlanFooter()}
      </div>

      {/* Chat Panel */}
      {!chatCollapsed && (
        <div className="chat-panel w-2/5 flex flex-col bg-white border-l border-gray-200">
          {renderChatHeader()}
          <div className="chat-content flex-1 overflow-hidden">
            <React.Suspense fallback={<div className="flex items-center justify-center h-full">Loading Chat...</div>}>
              <ChatContainer />
            </React.Suspense>
          </div>
        </div>
      )}
    </div>
  );

  const renderStackedLayout = () => (
    <div className="tablet-stacked-layout flex flex-col h-screen w-full">
      {/* Top Section - Floor Plan */}
      <div className={`floor-plan-section flex flex-col transition-all duration-300 ${
        layoutMode === 'chat-only' ? 'h-0 overflow-hidden' : 'h-3/5'
      }`}>
        {renderFloorPlanHeader()}
        <div className="floor-plan-content flex-1 overflow-hidden">
          <React.Suspense fallback={<div className="flex items-center justify-center h-full">Loading Floor Plan...</div>}>
            <FloorPlanContainer />
          </React.Suspense>
        </div>
      </div>

      {/* Bottom Section - Chat */}
      <div className={`chat-section flex flex-col bg-white border-t border-gray-200 transition-all duration-300 ${
        layoutMode === 'floor-plan-only' ? 'h-0 overflow-hidden' : 'h-2/5'
      }`}>
        {renderChatHeader()}
        <div className="chat-content flex-1 overflow-hidden">
          <React.Suspense fallback={<div className="flex items-center justify-center h-full">Loading Chat...</div>}>
            <ChatContainer />
          </React.Suspense>
        </div>
      </div>
    </div>
  );

  const renderFloorPlanHeader = () => (
    <div className="floor-plan-header bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <h1 className="text-lg font-semibold text-gray-800">DeskMate</h1>

        {/* Room Navigation (simplified for tablet) */}
        <div className="flex space-x-1">
          <button className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded border border-blue-200">
            Living
          </button>
          <button className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded border border-gray-200">
            Kitchen
          </button>
        </div>
      </div>

      {/* Layout Controls */}
      <div className="flex items-center space-x-2">
        {/* Layout mode toggle */}
        <div className="flex bg-gray-100 rounded p-1">
          <button
            onClick={() => setLayoutMode(deviceInfo.orientation === 'portrait' ? 'stacked' : 'split')}
            className={`px-2 py-1 text-xs rounded ${
              (layoutMode === 'split' || layoutMode === 'stacked') ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500'
            }`}
          >
            Both
          </button>
          <button
            onClick={() => setLayoutMode('floor-plan-only')}
            className={`px-2 py-1 text-xs rounded ${
              layoutMode === 'floor-plan-only' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500'
            }`}
          >
            Plan
          </button>
          <button
            onClick={() => setLayoutMode('chat-only')}
            className={`px-2 py-1 text-xs rounded ${
              layoutMode === 'chat-only' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500'
            }`}
          >
            Chat
          </button>
        </div>

        {/* Chat collapse toggle (split mode only) */}
        {layoutMode === 'split' && (
          <button
            onClick={() => setChatCollapsed(!chatCollapsed)}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );

  const renderFloorPlanFooter = () => (
    <div className="floor-plan-footer bg-white border-t border-gray-200 px-4 py-2 flex items-center justify-between">
      <div className="flex items-center space-x-3 text-sm text-gray-600">
        <span>Assistant: Living Room</span>
        <span>•</span>
        <span>Active</span>
      </div>

      {/* Simplified controls for tablet */}
      <div className="flex items-center space-x-2">
        <button className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200">
          Fit
        </button>
        <button className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200">
          Zoom
        </button>
      </div>
    </div>
  );

  const renderChatHeader = () => (
    <div className="chat-header bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        {/* Assistant Avatar */}
        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
          <span className="text-white text-sm font-medium">AI</span>
        </div>
        <div>
          <h2 className="font-medium text-gray-800">Assistant</h2>
          <p className="text-xs text-gray-500">Online</p>
        </div>
      </div>

      {/* Chat Controls */}
      <div className="flex items-center space-x-2">
        <button className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
          </svg>
        </button>

        {layoutMode === 'stacked' && (
          <button
            onClick={() => setLayoutMode('chat-only')}
            className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div
      className="tablet-layout w-full h-screen bg-gray-50"
      data-layout-mode={layoutMode}
      data-orientation={deviceInfo.orientation}
    >
      {deviceInfo.orientation === 'landscape' && layoutMode === 'split'
        ? renderSplitLayout()
        : renderStackedLayout()
      }

      {/* Render children if provided */}
      {children}

      {/* Tablet-specific styles */}
      <style>
        {`
        .tablet-layout {
          touch-action: pan-x pan-y;
        }

        .floor-plan-panel,
        .chat-panel,
        .floor-plan-section,
        .chat-section {
          transition: width 0.3s ease, height 0.3s ease;
        }

        .tablet-layout button {
          min-height: 44px;
          min-width: 44px;
        }

        .tablet-layout .text-xs {
          font-size: 14px; /* Larger text for tablet readability */
        }
        `}
      </style>
    </div>
  );
};

export default TabletLayout;