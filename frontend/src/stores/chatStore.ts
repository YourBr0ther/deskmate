/**
 * Zustand store for chat state management
 */

import { create } from 'zustand';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  model?: string;
  isStreaming?: boolean;
}

export interface LLMModel {
  id: string;
  name: string;
  provider: 'nano_gpt' | 'ollama';
  description: string;
  max_tokens: number;
  context_window: number;
  supports_streaming: boolean;
  cost_per_token: number;
}

interface ChatState {
  // Message history
  messages: ChatMessage[];

  // Current state
  isConnected: boolean;
  isTyping: boolean;
  currentMessage: string;

  // Model selection
  availableModels: LLMModel[];
  currentModel: string;
  currentProvider: 'nano_gpt' | 'ollama';

  // WebSocket connection
  websocket: WebSocket | null;
  reconnectAttempts: number;
  maxReconnectAttempts: number;

  // Actions
  setCurrentMessage: (message: string) => void;
  addMessage: (message: Omit<ChatMessage, 'id'>) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  clearMessages: () => void;

  // WebSocket actions
  connect: () => void;
  disconnect: () => void;
  sendMessage: (content: string) => void;
  sendAssistantMove: (x: number, y: number) => void;

  // Model management
  setAvailableModels: (models: LLMModel[]) => void;
  setCurrentModel: (modelId: string) => void;
  updateCurrentModel: (modelId: string, provider: 'nano_gpt' | 'ollama') => void;

  // Connection management
  setConnected: (connected: boolean) => void;
  setTyping: (typing: boolean) => void;
}

const generateId = () => Math.random().toString(36).substr(2, 9);

// Use hostname-based URL for Docker compatibility
const WEBSOCKET_URL = `ws://${window.location.hostname}:8000/ws`;

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  messages: [],
  isConnected: false,
  isTyping: false,
  currentMessage: '',
  availableModels: [],
  currentModel: 'llama3:latest',
  currentProvider: 'ollama',
  websocket: null,
  reconnectAttempts: 0,
  maxReconnectAttempts: 5,

  // Message actions
  setCurrentMessage: (message) => set({ currentMessage: message }),

  addMessage: (message) => {
    const newMessage: ChatMessage = {
      ...message,
      id: generateId(),
    };
    set((state) => ({
      messages: [...state.messages, newMessage]
    }));
  },

  updateMessage: (id, updates) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      )
    }));
  },

  clearMessages: () => set({ messages: [] }),

  // Model management
  setAvailableModels: (models) => set({ availableModels: models }),

  setCurrentModel: (modelId) => {
    const state = get();
    const { websocket, currentModel } = state;

    // Don't send if already the current model
    if (currentModel === modelId) {
      return;
    }

    const model = state.availableModels.find(m => m.id === modelId);

    if (model) {
      set({
        currentModel: modelId,
        currentProvider: model.provider
      });

      // Notify backend of model change
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
          type: 'model_change',
          data: { model_id: modelId }
        }));
      }
    }
  },

  // Update model without sending WebSocket message (for backend updates)
  updateCurrentModel: (modelId, provider) => {
    set({
      currentModel: modelId,
      currentProvider: provider
    });
  },

  // Connection management
  setConnected: (connected) => set({ isConnected: connected }),
  setTyping: (typing) => set({ isTyping: typing }),

  // WebSocket actions
  connect: () => {
    const state = get();

    if (state.websocket?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const ws = new WebSocket(WEBSOCKET_URL);

      ws.onopen = () => {
        console.log('WebSocket connected');
        set({
          isConnected: true,
          websocket: ws,
          reconnectAttempts: 0
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        set({ isConnected: false, websocket: null });

        // Attempt reconnection
        const { reconnectAttempts, maxReconnectAttempts } = get();
        if (reconnectAttempts < maxReconnectAttempts) {
          setTimeout(() => {
            set((state) => ({
              reconnectAttempts: state.reconnectAttempts + 1
            }));
            get().connect();
          }, Math.pow(2, reconnectAttempts) * 1000); // Exponential backoff
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        set({ isConnected: false });
      };

      set({ websocket: ws });

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  },

  disconnect: () => {
    const { websocket } = get();
    if (websocket) {
      websocket.close();
      set({ websocket: null, isConnected: false });
    }
  },

  sendMessage: (content: string) => {
    const { websocket, isConnected } = get();

    if (!isConnected || !websocket) {
      console.error('Not connected to WebSocket');
      return;
    }

    // Add user message to chat
    get().addMessage({
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    });

    // Send to backend
    websocket.send(JSON.stringify({
      type: 'chat_message',
      data: { message: content }
    }));

    // Clear current message
    set({ currentMessage: '' });
  },

  sendAssistantMove: (x: number, y: number) => {
    const { websocket, isConnected } = get();

    if (!isConnected || !websocket) {
      console.error('Not connected to WebSocket');
      return;
    }

    websocket.send(JSON.stringify({
      type: 'assistant_move',
      data: { x, y }
    }));
  },
}));

// Handle incoming WebSocket messages
function handleWebSocketMessage(message: any) {
  const { type, data } = message;
  const store = useChatStore.getState();

  switch (type) {
    case 'connection_established':
      console.log('Connection established:', data.message);
      store.setCurrentModel(data.current_model);
      break;

    case 'chat_message':
      store.addMessage({
        role: data.role,
        content: data.content,
        timestamp: data.timestamp,
        model: data.model
      });
      break;

    case 'chat_stream':
      // Find the last assistant message and update it
      const messages = store.messages;
      const lastMessage = messages[messages.length - 1];

      if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
        store.updateMessage(lastMessage.id, {
          content: data.full_content
        });
      } else {
        // Create new streaming message
        store.addMessage({
          role: 'assistant',
          content: data.content,
          timestamp: new Date().toISOString(),
          isStreaming: true
        });
      }
      break;

    case 'assistant_typing':
      store.setTyping(data.typing);
      if (data.typing) {
        // Add placeholder message
        store.addMessage({
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          isStreaming: true
        });
      } else {
        // Mark last message as complete
        const lastMsg = store.messages[store.messages.length - 1];
        if (lastMsg && lastMsg.isStreaming) {
          store.updateMessage(lastMsg.id, { isStreaming: false });
        }
      }
      break;

    case 'model_changed':
      store.updateCurrentModel(data.model, data.provider);
      store.addMessage({
        role: 'system',
        content: `Switched to ${data.model} (${data.provider})`,
        timestamp: new Date().toISOString()
      });
      break;

    case 'assistant_state':
      // Handle assistant state updates (could be used for visual updates)
      console.log('Assistant state updated:', data);
      break;

    case 'error':
      console.error('WebSocket error:', data.message);
      store.addMessage({
        role: 'system',
        content: `Error: ${data.message}`,
        timestamp: new Date().toISOString()
      });
      break;

    case 'pong':
      // Handle ping/pong for connection keep-alive
      break;

    default:
      console.log('Unknown message type:', type, data);
  }
}