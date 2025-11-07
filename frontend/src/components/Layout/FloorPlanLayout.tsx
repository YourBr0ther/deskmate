/**
 * Enhanced Floor Plan Layout Component
 *
 * Main layout component that integrates floor plan management, room navigation,
 * and template selection into a cohesive interface. Supports both desktop and
 * mobile responsive layouts.
 */

import React, { useState, useEffect, useCallback } from 'react';

import { useDeviceDetection } from '../../hooks/useDeviceDetection';
import { useFloorPlanManager, FloorPlanTemplate } from '../../hooks/useFloorPlanManager';
import { useRoomNavigation } from '../../hooks/useRoomNavigation';
import { FloorPlan, Room, Doorway, Assistant } from '../../types/floorPlan';
import FloatingChatWidget from '../Chat/FloatingChatWidget';
import FloorPlanSelector from '../FloorPlan/FloorPlanSelector';
import { TopDownRenderer } from '../FloorPlan/TopDownRenderer';
import RoomNavigationPanel from '../Navigation/RoomNavigationPanel';

interface FloorPlanLayoutProps {
  className?: string;
  children?: React.ReactNode;
}

const FloorPlanLayout: React.FC<FloorPlanLayoutProps> = ({ className = '', children }) => {
  // Device detection
  const { isMobile, isTablet } = useDeviceDetection();

  // Local state
  const [selectedTemplate, setSelectedTemplate] = useState<FloorPlanTemplate | null>(null);
  const [showSelector, setShowSelector] = useState(false);
  const [showNavigation, setShowNavigation] = useState(true);
  const [selectedRoom, setSelectedRoom] = useState<string | null>(null);

  // Floor plan management
  const {
    templates,
    activeFloorPlan,
    currentFloorPlan,
    isLoading: isFloorPlanLoading,
    error: floorPlanError,
    activateFloorPlan,
    refresh: refreshFloorPlans
  } = useFloorPlanManager({
    autoLoadTemplates: true,
    onFloorPlanActivated: (floorPlan) => {
      console.log('Floor plan activated:', floorPlan.name);
      setShowSelector(false);
    }
  });

  // Room navigation
  const {
    assistantPosition,
    isNavigating,
    navigationStatus,
    isLoading: isNavigationLoading,
    error: navigationError
  } = useRoomNavigation({
    onRoomTransition: (fromRoom, toRoom) => {
      console.log(`Room transition: ${fromRoom} → ${toRoom}`);
      setSelectedRoom(toRoom);
    },
    onNavigationComplete: (targetRoom) => {
      console.log(`Navigation completed to: ${targetRoom}`);
    }
  });

  // Handle template selection
  const handleTemplateSelected = useCallback((template: FloorPlanTemplate) => {
    setSelectedTemplate(template);
  }, []);

  // Handle template activation
  const handleTemplateActivated = useCallback((template: FloorPlanTemplate) => {
    setSelectedTemplate(template);
    setShowSelector(false);
  }, []);

  // Handle room selection
  const handleRoomSelect = useCallback((roomId: string) => {
    setSelectedRoom(roomId);
  }, []);

  // Handle navigation start
  const handleNavigationStart = useCallback((roomId: string) => {
    console.log('Navigation started to room:', roomId);
  }, []);

  // Mock assistant data (would come from actual assistant state)
  const mockAssistant: Assistant = {
    id: 'default',
    location: {
      position: {
        x: assistantPosition?.position.x || 650,
        y: assistantPosition?.position.y || 300
      },
      facing: 'right' as const,
      facing_angle: assistantPosition?.facing_angle || 0
    },
    status: {
      mood: 'neutral',
      action: isNavigating ? 'walking' : 'idle',
      energy_level: 0.8,
      mode: 'active'
    }
  };

  // Check if we have a workable floor plan
  const hasFloorPlan = currentFloorPlan && currentFloorPlan.rooms && currentFloorPlan.rooms.length > 0;
  const hasTemplates = templates.length > 0;

  // Mobile layout
  if (isMobile) {
    return (
      <div className={`floor-plan-layout-mobile h-full flex flex-col ${className}`}>
        {/* Mobile header */}
        <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <div>
            <h1 className="font-semibold text-gray-900">
              {currentFloorPlan?.name || 'DeskMate Floor Plan'}
            </h1>
            {activeFloorPlan && (
              <p className="text-xs text-gray-500">
                {activeFloorPlan.room_count} rooms • {activeFloorPlan.category}
              </p>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowNavigation(!showNavigation)}
              className="p-2 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
              title="Toggle navigation"
            >
              🧭
            </button>
            <button
              onClick={() => setShowSelector(!showSelector)}
              className="p-2 bg-blue-100 hover:bg-blue-200 rounded transition-colors"
              title="Select floor plan"
            >
              📋
            </button>
          </div>
        </div>

        {/* Floor plan selector modal */}
        {showSelector && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg max-w-lg w-full max-h-[80vh] overflow-hidden">
              <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                <h2 className="font-semibold">Select Floor Plan</h2>
                <button
                  onClick={() => setShowSelector(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
              <div className="p-4 overflow-y-auto max-h-[60vh]">
                <FloorPlanSelector
                  onFloorPlanSelected={handleTemplateSelected}
                  onFloorPlanActivated={handleTemplateActivated}
                />
              </div>
            </div>
          </div>
        )}

        {/* Navigation panel modal */}
        {showNavigation && hasFloorPlan && (
          <div className="fixed inset-x-0 bottom-0 bg-white border-t border-gray-200 z-40 max-h-[50vh] overflow-hidden">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="font-semibold">Room Navigation</h2>
              <button
                onClick={() => setShowNavigation(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="overflow-y-auto max-h-[35vh]">
              <RoomNavigationPanel
                floorPlan={currentFloorPlan}
                rooms={currentFloorPlan.rooms}
                doorways={currentFloorPlan.doorways}
                currentRoomId={selectedRoom}
                onRoomSelect={handleRoomSelect}
                onNavigationStart={handleNavigationStart}
              />
            </div>
          </div>
        )}

        {/* Main floor plan view */}
        <div className="flex-1 relative bg-gray-100">
          {hasFloorPlan ? (
            <TopDownRenderer
              floorPlan={currentFloorPlan}
              assistant={mockAssistant}
              selectedObject={undefined}
              showNavigationPath={true}
              showDoorwayHighlights={true}
              enableRoomNavigation={true}
              onRoomClick={handleRoomSelect}
              className="w-full h-full"
            />
          ) : (
            <div className="flex items-center justify-center h-full text-center p-8">
              <div>
                <div className="text-6xl mb-4">🏠</div>
                <h2 className="text-xl font-semibold text-gray-700 mb-2">No Floor Plan Active</h2>
                <p className="text-gray-500 mb-4">Select a floor plan template to get started</p>
                <button
                  onClick={() => setShowSelector(true)}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
                >
                  Select Floor Plan
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Floating chat widget */}
        <FloatingChatWidget
          state="minimized"
          onStateChange={() => {}}
          className="z-30"
        />

        {/* Status indicators */}
        {(isFloorPlanLoading || isNavigationLoading) && (
          <div className="fixed top-4 right-4 bg-blue-100 border border-blue-300 rounded-lg p-2 z-20">
            <div className="text-xs text-blue-800">Loading...</div>
          </div>
        )}
      </div>
    );
  }

  // Desktop layout
  return (
    <div className={`floor-plan-layout-desktop h-full flex ${className}`}>
      {/* Left sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <h1 className="font-semibold text-gray-900">DeskMate Floor Plan</h1>
          {activeFloorPlan && (
            <p className="text-sm text-gray-500">{activeFloorPlan.name}</p>
          )}
        </div>

        {/* Floor plan selector */}
        <div className="p-4 border-b border-gray-200">
          <FloorPlanSelector
            onFloorPlanSelected={handleTemplateSelected}
            onFloorPlanActivated={handleTemplateActivated}
          />
        </div>

        {/* Room navigation */}
        {hasFloorPlan && (
          <div className="flex-1 overflow-y-auto">
            <RoomNavigationPanel
              floorPlan={currentFloorPlan}
              rooms={currentFloorPlan.rooms}
              doorways={currentFloorPlan.doorways}
              currentRoomId={selectedRoom}
              onRoomSelect={handleRoomSelect}
              onNavigationStart={handleNavigationStart}
              className="p-4"
            />
          </div>
        )}

        {/* Error display */}
        {(floorPlanError || navigationError) && (
          <div className="p-4 bg-red-50 border-t border-red-200">
            <p className="text-sm text-red-800">
              {floorPlanError || navigationError}
            </p>
          </div>
        )}
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col">
        {/* Floor plan view */}
        <div className="flex-1 bg-gray-100 relative">
          {hasFloorPlan ? (
            <TopDownRenderer
              floorPlan={currentFloorPlan}
              assistant={mockAssistant}
              selectedObject={undefined}
              showNavigationPath={true}
              showDoorwayHighlights={true}
              enableRoomNavigation={true}
              onRoomClick={handleRoomSelect}
              className="w-full h-full"
            />
          ) : (
            <div className="flex items-center justify-center h-full text-center">
              <div>
                <div className="text-8xl mb-6">🏠</div>
                <h2 className="text-2xl font-semibold text-gray-700 mb-4">Welcome to DeskMate</h2>
                <p className="text-gray-500 mb-6 max-w-md">
                  Select a floor plan template from the sidebar to start exploring
                  multi-room navigation with your AI assistant.
                </p>
                {!hasTemplates && (
                  <button
                    onClick={refreshFloorPlans}
                    className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
                  >
                    Load Floor Plan Templates
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Status bar */}
        <div className="bg-white border-t border-gray-200 px-4 py-2 flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            {assistantPosition && (
              <span>
                Assistant: ({Math.round(assistantPosition.position.x)}, {Math.round(assistantPosition.position.y)})
              </span>
            )}
            {selectedRoom && (
              <span>Room: {selectedRoom}</span>
            )}
            {isNavigating && (
              <span className="text-blue-600">
                Navigating... ({navigationStatus.current_step}/{navigationStatus.total_steps})
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            {isFloorPlanLoading && <span>Loading floor plan...</span>}
            {isNavigationLoading && <span>Processing navigation...</span>}
          </div>
        </div>
      </div>

      {/* Chat panel would go here */}
      {children}
    </div>
  );
};

export default FloorPlanLayout;