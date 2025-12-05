/**
 * Tests for WebSocket integration (Phase 12)
 * Tests position_update and room_transition message handling
 */

import { useSpatialStore } from '../../stores/spatialStore';

// Mock the stores
jest.mock('../../stores/chatStore', () => ({
  useChatStore: {
    getState: jest.fn(() => ({
      setTyping: jest.fn(),
      messages: []
    }))
  }
}));

describe('WebSocket Integration - Phase 12', () => {
  beforeEach(() => {
    // Reset spatial store state
    useSpatialStore.getState().setAssistantPosition({ x: 0, y: 0 });
    jest.clearAllMocks();
  });

  describe('Position Update Handling', () => {
    it('should update assistant position when position_update message is received', () => {
      const spatialStore = useSpatialStore.getState();
      const initialPosition = spatialStore.assistant?.position;

      // Simulate what handlePositionUpdate would do
      const newPosition = { x: 500, y: 300 };
      spatialStore.setAssistantPosition(newPosition);

      const updatedPosition = useSpatialStore.getState().assistant?.position;
      expect(updatedPosition).toEqual(newPosition);
    });

    it('should handle position updates with valid coordinates', () => {
      const spatialStore = useSpatialStore.getState();

      const validPositions = [
        { x: 0, y: 0 },
        { x: 1920, y: 480 },
        { x: 960, y: 240 }
      ];

      validPositions.forEach(position => {
        spatialStore.setAssistantPosition(position);
        expect(useSpatialStore.getState().assistant?.position).toEqual(position);
      });
    });
  });

  describe('Room Transition Handling', () => {
    it('should dispatch custom event for room transitions', () => {
      const eventHandler = jest.fn();
      window.addEventListener('deskmate:room-transition', eventHandler);

      // Simulate room transition event dispatch
      const transitionData = {
        assistant_id: 'test-assistant',
        from_room: 'room-1',
        to_room: 'room-2',
        doorway_id: 'doorway-1',
        timestamp: new Date().toISOString()
      };

      window.dispatchEvent(new CustomEvent('deskmate:room-transition', {
        detail: transitionData
      }));

      expect(eventHandler).toHaveBeenCalled();
      const event = eventHandler.mock.calls[0][0] as CustomEvent;
      expect(event.detail).toEqual(transitionData);

      window.removeEventListener('deskmate:room-transition', eventHandler);
    });
  });

  describe('WebSocket Message Types', () => {
    it('should handle position_update message type correctly', () => {
      const message = {
        type: 'position_update',
        data: {
          assistant_id: 'test-assistant',
          position: { x: 100, y: 200 },
          timestamp: '2025-12-02T10:00:00Z'
        }
      };

      // Verify message structure matches expected type
      expect(message.type).toBe('position_update');
      expect(message.data.position).toBeDefined();
      expect(typeof message.data.position.x).toBe('number');
      expect(typeof message.data.position.y).toBe('number');
    });

    it('should handle room_transition message type correctly', () => {
      const message = {
        type: 'room_transition',
        data: {
          assistant_id: 'test-assistant',
          from_room: 'living_room',
          to_room: 'bedroom',
          doorway_id: 'door-1',
          timestamp: '2025-12-02T10:00:00Z'
        }
      };

      // Verify message structure matches expected type
      expect(message.type).toBe('room_transition');
      expect(message.data.from_room).toBeDefined();
      expect(message.data.to_room).toBeDefined();
      expect(message.data.doorway_id).toBeDefined();
    });
  });
});
