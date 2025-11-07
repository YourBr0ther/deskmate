/**
 * Desktop layout component for DeskMate.
 *
 * Provides a split-panel layout with floor plan on the left (70%)
 * and persistent chat panel on the right (30%).
 */

import React, { useState, useCallback } from 'react';

import { useLayoutConfig } from '../../hooks/useDeviceDetection';
import { useFloorPlanStore } from '../../stores/floorPlanStore';
import { useRoomStore } from '../../stores/roomStore';
import { useSettingsStore } from '../../stores/settingsStore';
import DebugOverlay from '../Debug/DebugOverlay';
import DebugPanel from '../Debug/DebugPanel';

// Phase 12B Components
const FloorPlanContainer = React.lazy(() => import('../FloorPlan/FloorPlanContainer'));
const FloorPlanSelector = React.lazy(() => import('../FloorPlan/FloorPlanSelector'));
const ChatContainer = React.lazy(() => import('../Chat/ChatContainer'));
const AssistantSelector = React.lazy(() => import('../AssistantSelection/AssistantSelector'));
const StorageCloset = React.lazy(() => import('../StorageCloset'));

interface DesktopLayoutProps {
  children?: React.ReactNode;
}

/**
 * Desktop split-panel layout component.
 */
export const DesktopLayout: React.FC<DesktopLayoutProps> = ({ children }) => {
  const layoutConfig = useLayoutConfig();
  const { currentFloorPlan } = useFloorPlanStore();
  const { openSettings } = useSettingsStore();
  const { toggleStorageVisibility, storageVisible } = useRoomStore();
  const [sidebarWidth, setSidebarWidth] = useState(30); // Percentage
  const [isResizing, setIsResizing] = useState(false);
  const [showFloorPlanOptions, setShowFloorPlanOptions] = useState(false);

  // Handle panel resizing
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsResizing(true);
    e.preventDefault();

    const handleMouseMove = (e: MouseEvent) => {
      const containerWidth = window.innerWidth;
      const newWidth = ((containerWidth - e.clientX) / containerWidth) * 100;

      // Constrain between 20% and 50%
      const constrainedWidth = Math.max(20, Math.min(50, newWidth));
      setSidebarWidth(constrainedWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, []);

  const floorPlanWidth = 100 - sidebarWidth;

  return (
    <div className="desktop-layout flex h-screen w-full bg-gray-50">
      {/* Floor Plan Panel */}
      <div
        className="floor-plan-panel flex flex-col"
        style={{ width: `${floorPlanWidth}%` }}
      >
        {/* Floor Plan Header */}
        <div className="floor-plan-header bg-white border-b border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-4">
              <h1 className="text-lg font-semibold text-gray-800">DeskMate</h1>

              {/* Current Floor Plan Display */}
              {currentFloorPlan && (
                <div className="text-sm text-gray-600">
                  <span className="font-medium">{currentFloorPlan.name}</span>
                  <span className="text-gray-400 ml-2">•</span>
                  <span className="ml-2">{currentFloorPlan.rooms.length} rooms</span>
                </div>
              )}
            </div>

            {/* Floor Plan Controls */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowFloorPlanOptions(!showFloorPlanOptions)}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md border border-blue-200 hover:bg-blue-200"
              >
                Floor Plans
              </button>
              <button
                onClick={toggleStorageVisibility}
                className={`p-2 rounded transition-colors ${
                  storageVisible
                    ? 'text-amber-600 bg-amber-100 hover:bg-amber-200'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
                title={storageVisible ? "Close Storage Closet" : "Open Storage Closet"}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </button>
              <button
                onClick={openSettings}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                title="Open Settings"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>

          {/* Floor Plan Options Dropdown */}
          {showFloorPlanOptions && (
            <div className="mb-3 p-3 bg-gray-50 rounded-lg border">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-medium text-gray-700">Available Floor Plans</div>
                <button
                  onClick={() => setShowFloorPlanOptions(false)}
                  className="text-xs text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
              <React.Suspense
                fallback={
                  <div className="flex items-center justify-center py-4">
                    <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                    <span className="ml-2 text-sm text-gray-600">Loading floor plans...</span>
                  </div>
                }
              >
                <FloorPlanSelector
                  onFloorPlanSelected={(floorPlan) => {
                    console.log('Floor plan selected:', floorPlan);
                  }}
                  onFloorPlanActivated={(floorPlan) => {
                    console.log('Floor plan activated:', floorPlan);
                    setShowFloorPlanOptions(false);
                  }}
                  className="max-h-96 overflow-y-auto"
                />
              </React.Suspense>
            </div>
          )}

          {/* Room Navigation Tabs */}
          {currentFloorPlan && (
            <div className="flex space-x-2">
              {currentFloorPlan.rooms.map((room, index) => (
                <button
                  key={room.id}
                  className={`px-3 py-1 text-sm rounded-md border ${
                    index === 0
                      ? 'bg-blue-100 text-blue-700 border-blue-200'
                      : 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-200'
                  }`}
                >
                  {room.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Floor Plan Content */}
        <div className="floor-plan-content flex-1 relative overflow-hidden">
          <React.Suspense
            fallback={
              <div className="flex items-center justify-center h-full bg-gray-100">
                <div className="text-center">
                  <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mb-4"></div>
                  <div className="text-gray-600">Loading Floor Plan...</div>
                </div>
              </div>
            }
          >
            <FloorPlanContainer />
          </React.Suspense>
        </div>

        {/* Floor Plan Footer */}
        <div className="floor-plan-footer bg-white border-t border-gray-200 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span>Assistant: Living Room</span>
            <span>•</span>
            <span>Status: Active</span>
          </div>

          {/* Zoom Controls */}
          <div className="flex items-center space-x-2">
            <button className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200">
              Zoom-
            </button>
            <button className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200">
              Fit
            </button>
            <button className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200">
              Zoom+
            </button>
          </div>
        </div>
      </div>

      {/* Resizer */}
      <div
        className={`resize-handle w-1 bg-gray-300 hover:bg-blue-400 cursor-col-resize flex-shrink-0 ${
          isResizing ? 'bg-blue-400' : ''
        }`}
        onMouseDown={handleMouseDown}
        title="Drag to resize panels"
      />

      {/* Chat Panel */}
      <div
        className="chat-panel flex flex-col bg-white border-l border-gray-200"
        style={{ width: `${sidebarWidth}%` }}
      >
        {/* Chat Header */}
        <div className="chat-header bg-white border-b border-gray-200 px-4 py-3">
          {/* Assistant Selection */}
          <div className="mb-3">
            <React.Suspense
              fallback={
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-gray-200 rounded animate-pulse"></div>
                  <div className="h-4 bg-gray-200 rounded w-24 animate-pulse"></div>
                </div>
              }
            >
              <AssistantSelector
                compact={true}
                onAssistantChange={(assistantId) => {
                  console.log('Assistant changed to:', assistantId);
                }}
              />
            </React.Suspense>
          </div>

          {/* Chat Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-medium">AI</span>
              </div>
              <div>
                <p className="text-xs text-gray-500">Chat Assistant</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" clipRule="evenodd" />
                </svg>
              </button>
              <button className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Chat Content */}
        <div className="chat-content flex-1 overflow-hidden">
          <React.Suspense
            fallback={
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-gray-500">
                  <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mb-2"></div>
                  <div className="text-gray-600">Loading Chat...</div>
                </div>
              </div>
            }
          >
            <ChatContainer />
          </React.Suspense>
        </div>
      </div>

      {/* Render children if provided */}
      {children}

      {/* Storage Closet Integration */}
      <React.Suspense
        fallback={null}
      >
        <StorageCloset />
      </React.Suspense>

      {/* Click outside to close floor plan options */}
      {showFloorPlanOptions && (
        <div
          className="fixed inset-0 z-10"
          onClick={() => setShowFloorPlanOptions(false)}
        />
      )}

      {/* Desktop-specific styles */}
      <style>
        {`
        .resize-handle {
          transition: background-color 0.2s ease;
        }

        .resize-handle:hover {
          background-color: #3b82f6;
        }

        .desktop-layout {
          user-select: ${isResizing ? 'none' : 'auto'};
        }

        .floor-plan-panel,
        .chat-panel {
          min-width: 300px;
        }
        `}
      </style>

      {/* Debug Components */}
      <DebugOverlay />
      <DebugPanel />
    </div>
  );
};

export default DesktopLayout;