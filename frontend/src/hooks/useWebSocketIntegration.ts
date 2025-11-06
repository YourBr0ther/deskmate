/**
 * WebSocket Integration Hook
 *
 * Provides a React hook to integrate the typed WebSocket service
 * with the store system for real-time updates.
 */

import { useEffect, useRef } from 'react';
import { websocketService } from '../services/websocketService';
import { useSpatialStore } from '../stores/spatialStore';
import { useChatStore } from '../stores/chatStore';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  reconnectOnError?: boolean;
}

export function useWebSocketIntegration(options: UseWebSocketOptions = {}) {
  const { autoConnect = true, reconnectOnError = true } = options;
  const connectionAttempted = useRef(false);

  // Store references
  const spatialStore = useSpatialStore();
  const chatStore = useChatStore();

  useEffect(() => {
    if (!autoConnect || connectionAttempted.current) {
      return;
    }

    connectionAttempted.current = true;

    const connectToWebSocket = async () => {
      try {
        await websocketService.connect();
        console.log('WebSocket connected successfully');

        // Update connection state in stores
        chatStore.setConnected(true);
        spatialStore.setError(null);

      } catch (error) {
        console.error('WebSocket connection failed:', error);
        chatStore.setConnected(false);
        spatialStore.setError('Failed to connect to server');

        if (reconnectOnError) {
          // Retry connection after a delay
          setTimeout(connectToWebSocket, 5000);
        }
      }
    };

    connectToWebSocket();

    // Cleanup on unmount
    return () => {
      websocketService.disconnect();
      chatStore.setConnected(false);
    };
  }, [autoConnect, reconnectOnError, chatStore, spatialStore]);

  return {
    connected: websocketService.connected,
    send: websocketService.send.bind(websocketService),
    addEventListener: websocketService.addEventListener.bind(websocketService),
    removeEventListener: websocketService.removeEventListener.bind(websocketService)
  };
}

/**
 * Hook for sending WebSocket messages with type safety
 */
export function useWebSocketSender() {
  const { connected } = useWebSocketIntegration({ autoConnect: false });

  return {
    connected,

    // Chat messages
    sendChatMessage: (message: string, personaContext?: any) => {
      websocketService.send('chat_message', {
        message,
        persona_context: personaContext
      });
    },

    requestChatHistory: (personaName?: string) => {
      websocketService.send('request_chat_history', {
        persona_name: personaName
      });
    },

    clearChat: (clearType: 'current' | 'all' | 'persona', personaName?: string) => {
      websocketService.send('clear_chat', {
        clear_type: clearType,
        persona_name: personaName
      });
    },

    // Assistant control
    moveAssistant: (x: number, y: number) => {
      websocketService.send('assistant_move', { x, y });
    },

    // Object manipulation
    moveObject: (objectId: string, x: number, y: number) => {
      websocketService.send('object_move', {
        object_id: objectId,
        x,
        y
      });
    },

    interactWithObject: (objectId: string, action: string) => {
      websocketService.send('object_interact', {
        object_id: objectId,
        action
      });
    },

    pickUpObject: (objectId: string) => {
      websocketService.send('object_pick_up', {
        object_id: objectId
      });
    },

    putDownObject: (x?: number, y?: number) => {
      websocketService.send('object_put_down', { x, y });
    },

    // Model control
    changeModel: (modelId: string) => {
      websocketService.send('model_change', {
        model_id: modelId
      });
    }
  };
}