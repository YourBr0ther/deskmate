/**
 * Floor plan container component.
 *
 * Manages floor plan state, data fetching, and coordinates between
 * the top-down renderer and the rest of the application.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useDeviceDetection } from '../../hooks/useDeviceDetection';
import { FloorPlan, Assistant, Position } from '../../types/floorPlan';
import TopDownRenderer from './TopDownRenderer';


interface FloorPlanContainerProps {
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Main floor plan container component.
 */
export const FloorPlanContainer: React.FC<FloorPlanContainerProps> = ({
  className = '',
  style = {}
}) => {
  const deviceInfo = useDeviceDetection();
  const [floorPlan, setFloorPlan] = useState<FloorPlan | null>(null);
  const [assistant, setAssistant] = useState<Assistant | null>(null);
  const [selectedObject, setSelectedObject] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load floor plan data
  useEffect(() => {
    loadFloorPlanData();
  }, []);

  const loadFloorPlanData = async () => {
    try {
      setLoading(true);
      setError(null);

      // For now, use mock data. In real implementation, this would fetch from API
      const mockFloorPlan: FloorPlan = {
        id: 'studio_apartment',
        name: 'Studio Apartment',
        description: 'A cozy studio apartment with modern amenities',
        category: 'studio',
        dimensions: {
          width: 1300,
          height: 600,
          scale: 1.0,
          units: 'pixels'
        },
        styling: {
          background_color: '#F9FAFB',
          wall_color: '#374151',
          wall_thickness: 8
        },
        rooms: [
          {
            id: 'studio_main',
            name: 'Studio',
            type: 'studio',
            bounds: { x: 50, y: 50, width: 1200, height: 500 },
            properties: {
              floor_color: '#F3F4F6',
              floor_material: 'hardwood',
              lighting_level: 0.8
            }
          }
        ],
        walls: [
          {
            id: 'wall_north',
            geometry: { start: { x: 50, y: 50 }, end: { x: 1250, y: 50 } },
            properties: { type: 'exterior', thickness: 8, material: 'drywall', color: '#374151' }
          },
          {
            id: 'wall_east',
            geometry: { start: { x: 1250, y: 50 }, end: { x: 1250, y: 550 } },
            properties: { type: 'exterior', thickness: 8, material: 'drywall', color: '#374151' }
          },
          {
            id: 'wall_south',
            geometry: { start: { x: 1250, y: 550 }, end: { x: 50, y: 550 } },
            properties: { type: 'exterior', thickness: 8, material: 'drywall', color: '#374151' }
          },
          {
            id: 'wall_west',
            geometry: { start: { x: 50, y: 550 }, end: { x: 50, y: 50 } },
            properties: { type: 'exterior', thickness: 8, material: 'drywall', color: '#374151' }
          },
          {
            id: 'wall_kitchen',
            geometry: { start: { x: 200, y: 100 }, end: { x: 400, y: 100 } },
            properties: { type: 'interior', thickness: 4, material: 'drywall', color: '#6B7280' }
          }
        ],
        doorways: [
          {
            id: 'door_entrance',
            wall_id: 'wall_west',
            position: { position_on_wall: 0.7, width: 80 },
            connections: { room_a: 'studio_main', room_b: 'hallway' },
            properties: { type: 'door', has_door: true, door_state: 'closed' },
            accessibility: { is_accessible: true, requires_interaction: true },
            world_position: { x: 50, y: 400 }
          }
        ],
        furniture: [
          {
            id: 'kitchen_counter',
            name: 'Kitchen Counter',
            type: 'furniture',
            position: { x: 80, y: 120, rotation: 0 },
            geometry: { width: 300, height: 60 },
            visual: { color: '#8B4513', material: 'wood', style: 'modern' },
            properties: { solid: true, interactive: true, movable: false }
          },
          {
            id: 'refrigerator',
            name: 'Refrigerator',
            type: 'appliance',
            position: { x: 80, y: 200, rotation: 0 },
            geometry: { width: 60, height: 60 },
            visual: { color: '#E5E7EB', material: 'metal', style: 'modern' },
            properties: { solid: true, interactive: true, movable: false }
          },
          {
            id: 'sofa',
            name: 'Sofa',
            type: 'furniture',
            position: { x: 500, y: 300, rotation: 0 },
            geometry: { width: 180, height: 80 },
            visual: { color: '#6B7280', material: 'fabric', style: 'modern' },
            properties: { solid: true, interactive: true, movable: false }
          },
          {
            id: 'coffee_table',
            name: 'Coffee Table',
            type: 'furniture',
            position: { x: 550, y: 400, rotation: 0 },
            geometry: { width: 80, height: 40 },
            visual: { color: '#92400E', material: 'wood', style: 'modern' },
            properties: { solid: true, interactive: true, movable: false }
          },
          {
            id: 'bed',
            name: 'Bed',
            type: 'furniture',
            position: { x: 900, y: 350, rotation: 0 },
            geometry: { width: 160, height: 120 },
            visual: { color: '#F3F4F6', material: 'fabric', style: 'modern' },
            properties: { solid: true, interactive: true, movable: false }
          },
          {
            id: 'nightstand',
            name: 'Nightstand',
            type: 'furniture',
            position: { x: 1070, y: 370, rotation: 0 },
            geometry: { width: 40, height: 40 },
            visual: { color: '#8B4513', material: 'wood', style: 'modern' },
            properties: { solid: true, interactive: true, movable: false }
          }
        ]
      };

      const mockAssistant: Assistant = {
        id: 'default',
        location: {
          position: { x: 650, y: 300 },
          facing: 'right',
          facing_angle: 45
        },
        status: {
          mood: 'happy',
          action: 'idle',
          energy_level: 0.8,
          mode: 'active'
        }
      };

      setFloorPlan(mockFloorPlan);
      setAssistant(mockAssistant);

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load floor plan');
    } finally {
      setLoading(false);
    }
  };

  // Handle object selection
  const handleObjectClick = useCallback((objectId: string) => {
    setSelectedObject(prev => prev === objectId ? null : objectId);
    console.log('Object clicked:', objectId);
  }, []);

  // Handle position clicks (for movement)
  const handlePositionClick = useCallback((position: Position) => {
    console.log('Position clicked:', position);
    // In real implementation, this would trigger assistant movement
  }, []);

  // Handle assistant movement
  const handleAssistantMove = useCallback((position: Position) => {
    if (!assistant) return;

    setAssistant(prev => prev ? {
      ...prev,
      location: {
        ...prev.location,
        position
      }
    } : null);
  }, [assistant]);

  if (loading) {
    return (
      <div className="floor-plan-loading flex items-center justify-center w-full h-full bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading floor plan...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="floor-plan-error flex items-center justify-center w-full h-full bg-red-50">
        <div className="text-center p-8">
          <div className="text-red-600 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-red-800 mb-2">Floor Plan Error</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadFloorPlanData}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!floorPlan || !assistant) {
    return (
      <div className="floor-plan-empty flex items-center justify-center w-full h-full bg-gray-100">
        <p className="text-gray-500">No floor plan data available</p>
      </div>
    );
  }

  return (
    <div className={`floor-plan-container relative w-full h-full ${className}`} style={style}>
      <TopDownRenderer
        floorPlan={floorPlan}
        assistant={assistant}
        selectedObject={selectedObject || undefined}
        onObjectClick={handleObjectClick}
        onPositionClick={handlePositionClick}
        onAssistantMove={handleAssistantMove}
        className="w-full h-full"
      />

      {/* Object info panel for selected objects */}
      {selectedObject && (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 max-w-sm z-10">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-800">
              {floorPlan.furniture.find(f => f.id === selectedObject)?.name || 'Object'}
            </h3>
            <button
              onClick={() => setSelectedObject(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
          <div className="text-sm text-gray-600 space-y-1">
            {(() => {
              const obj = floorPlan.furniture.find(f => f.id === selectedObject);
              if (!obj) return null;
              return (
                <>
                  <p><strong>Type:</strong> {obj.type}</p>
                  <p><strong>Material:</strong> {obj.visual.material}</p>
                  <p><strong>Style:</strong> {obj.visual.style}</p>
                  <p><strong>Interactive:</strong> {obj.properties.interactive ? 'Yes' : 'No'}</p>
                </>
              );
            })()}
          </div>
        </div>
      )}

      {/* Development info overlay */}
      {process.env.NODE_ENV === 'development' && (
        <div className="absolute bottom-4 left-4 bg-black bg-opacity-75 text-white text-xs p-2 rounded z-10">
          <div>Floor Plan: {floorPlan.name}</div>
          <div>Rooms: {floorPlan.rooms.length}</div>
          <div>Furniture: {floorPlan.furniture.length}</div>
          <div>Assistant: {assistant.location.position.x.toFixed(0)}, {assistant.location.position.y.toFixed(0)}</div>
          {selectedObject && <div>Selected: {selectedObject}</div>}
        </div>
      )}
    </div>
  );
};

export default FloorPlanContainer;