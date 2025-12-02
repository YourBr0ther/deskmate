/**
 * Tests for WebSocket Integration Hooks
 *
 * Tests cover:
 * - useWebSocketIntegration - connection management
 * - useWebSocketSender - typed message sending
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useWebSocketIntegration, useWebSocketSender } from '../useWebSocketIntegration';

// Mock websocketService
const mockWebsocketService = {
  connect: jest.fn(),
  disconnect: jest.fn(),
  send: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  connected: false,
};

jest.mock('../../services/websocketService', () => ({
  websocketService: mockWebsocketService,
}));

// Mock stores
const mockSetConnected = jest.fn();
const mockSetError = jest.fn();

jest.mock('../../stores/chatStore', () => ({
  useChatStore: () => ({
    setConnected: mockSetConnected,
  }),
}));

jest.mock('../../stores/spatialStore', () => ({
  useSpatialStore: () => ({
    setError: mockSetError,
  }),
}));

describe('useWebSocketIntegration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockWebsocketService.connected = false;
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Auto Connection', () => {
    it('should auto-connect by default', async () => {
      mockWebsocketService.connect.mockResolvedValue(undefined);

      renderHook(() => useWebSocketIntegration());

      await waitFor(() => {
        expect(mockWebsocketService.connect).toHaveBeenCalled();
      });
    });

    it('should not auto-connect when disabled', () => {
      renderHook(() => useWebSocketIntegration({ autoConnect: false }));

      expect(mockWebsocketService.connect).not.toHaveBeenCalled();
    });

    it('should update store on successful connection', async () => {
      mockWebsocketService.connect.mockResolvedValue(undefined);

      renderHook(() => useWebSocketIntegration());

      await waitFor(() => {
        expect(mockSetConnected).toHaveBeenCalledWith(true);
        expect(mockSetError).toHaveBeenCalledWith(null);
      });
    });
  });

  describe('Connection Errors', () => {
    it('should handle connection failure', async () => {
      mockWebsocketService.connect.mockRejectedValue(new Error('Connection failed'));

      renderHook(() => useWebSocketIntegration());

      await waitFor(() => {
        expect(mockSetConnected).toHaveBeenCalledWith(false);
        expect(mockSetError).toHaveBeenCalledWith('Failed to connect to server');
      });
    });

    it('should retry connection on error when enabled', async () => {
      mockWebsocketService.connect
        .mockRejectedValueOnce(new Error('First failure'))
        .mockResolvedValueOnce(undefined);

      renderHook(() => useWebSocketIntegration({ reconnectOnError: true }));

      await waitFor(() => {
        expect(mockWebsocketService.connect).toHaveBeenCalledTimes(1);
      });

      // Fast-forward through retry delay
      act(() => {
        jest.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(mockWebsocketService.connect).toHaveBeenCalledTimes(2);
      });
    });

    it('should not retry when reconnectOnError is false', async () => {
      mockWebsocketService.connect.mockRejectedValue(new Error('Connection failed'));

      renderHook(() => useWebSocketIntegration({ reconnectOnError: false }));

      await waitFor(() => {
        expect(mockWebsocketService.connect).toHaveBeenCalledTimes(1);
      });

      // Fast-forward through potential retry delay
      act(() => {
        jest.advanceTimersByTime(10000);
      });

      expect(mockWebsocketService.connect).toHaveBeenCalledTimes(1);
    });
  });

  describe('Cleanup', () => {
    it('should disconnect on unmount', async () => {
      mockWebsocketService.connect.mockResolvedValue(undefined);

      const { unmount } = renderHook(() => useWebSocketIntegration());

      await waitFor(() => {
        expect(mockWebsocketService.connect).toHaveBeenCalled();
      });

      unmount();

      expect(mockWebsocketService.disconnect).toHaveBeenCalled();
      expect(mockSetConnected).toHaveBeenCalledWith(false);
    });
  });

  describe('Return Value', () => {
    it('should return connection status and methods', async () => {
      mockWebsocketService.connect.mockResolvedValue(undefined);
      mockWebsocketService.connected = true;

      const { result } = renderHook(() => useWebSocketIntegration());

      expect(result.current).toHaveProperty('connected');
      expect(result.current).toHaveProperty('send');
      expect(result.current).toHaveProperty('addEventListener');
      expect(result.current).toHaveProperty('removeEventListener');
    });
  });
});

describe('useWebSocketSender', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockWebsocketService.connected = true;
  });

  describe('Chat Messages', () => {
    it('should send chat message', () => {
      const { result } = renderHook(() => useWebSocketSender());

      act(() => {
        result.current.sendChatMessage('Hello', { name: 'TestPersona' });
      });

      expect(mockWebsocketService.send).toHaveBeenCalledWith('chat_message', {
        message: 'Hello',
        persona_context: { name: 'TestPersona' },
      });
    });

    it('should request chat history', () => {
      const { result } = renderHook(() => useWebSocketSender());

      act(() => {
        result.current.requestChatHistory('Alice');
      });

      expect(mockWebsocketService.send).toHaveBeenCalledWith('request_chat_history', {
        persona_name: 'Alice',
      });
    });

    it('should clear chat', () => {
      const { result } = renderHook(() => useWebSocketSender());

      act(() => {
        result.current.clearChat('persona', 'Bob');
      });

      expect(mockWebsocketService.send).toHaveBeenCalledWith('clear_chat', {
        clear_type: 'persona',
        persona_name: 'Bob',
      });
    });
  });

  describe('Assistant Control', () => {
    it('should send move assistant command', () => {
      const { result } = renderHook(() => useWebSocketSender());

      act(() => {
        result.current.moveAssistant(100, 200);
      });

      expect(mockWebsocketService.send).toHaveBeenCalledWith('assistant_move', {
        x: 100,
        y: 200,
      });
    });
  });

  describe('Object Manipulation', () => {
    it('should send move object command', () => {
      const { result } = renderHook(() => useWebSocketSender());

      act(() => {
        result.current.moveObject('obj-123', 50, 75);
      });

      expect(mockWebsocketService.send).toHaveBeenCalledWith('object_move', {
        object_id: 'obj-123',
        x: 50,
        y: 75,
      });
    });

    it('should send interact with object command', () => {
      const { result } = renderHook(() => useWebSocketSender());

      act(() => {
        result.current.interactWithObject('lamp-1', 'toggle');
      });

      expect(mockWebsocketService.send).toHaveBeenCalledWith('object_interact', {
        object_id: 'lamp-1',
        action: 'toggle',
      });
    });

    it('should send pick up object command', () => {
      const { result } = renderHook(() => useWebSocketSender());

      act(() => {
        result.current.pickUpObject('book-1');
      });

      expect(mockWebsocketService.send).toHaveBeenCalledWith('object_pick_up', {
        object_id: 'book-1',
      });
    });

    it('should send put down object command', () => {
      const { result } = renderHook(() => useWebSocketSender());

      act(() => {
        result.current.putDownObject(150, 200);
      });

      expect(mockWebsocketService.send).toHaveBeenCalledWith('object_put_down', {
        x: 150,
        y: 200,
      });
    });

    it('should send put down without position', () => {
      const { result } = renderHook(() => useWebSocketSender());

      act(() => {
        result.current.putDownObject();
      });

      expect(mockWebsocketService.send).toHaveBeenCalledWith('object_put_down', {
        x: undefined,
        y: undefined,
      });
    });
  });

  describe('Model Control', () => {
    it('should send change model command', () => {
      const { result } = renderHook(() => useWebSocketSender());

      act(() => {
        result.current.changeModel('gpt-4o-mini');
      });

      expect(mockWebsocketService.send).toHaveBeenCalledWith('model_change', {
        model_id: 'gpt-4o-mini',
      });
    });
  });
});
