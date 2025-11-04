/**
 * Zustand store for chat state management
 */

import { create } from 'zustand';
import { usePersonaStore } from './personaStore';

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
  loadChatHistory: (messages: ChatMessage[]) => void;

  // WebSocket actions
  connect: () => void;
  disconnect: () => void;
  sendMessage: (content: string) => void;
  sendAssistantMove: (x: number, y: number) => void;
  clearChat: (clearType: 'current' | 'all' | 'persona', personaName?: string) => void;
  handleCommand: (command: string) => Promise<void>;

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

  loadChatHistory: (messages) => {
    // Convert loaded messages to proper ChatMessage format with unique IDs
    const formattedMessages: ChatMessage[] = messages.map((msg) => ({
      ...msg,
      id: msg.id || generateId(), // Use existing ID or generate new one
    }));
    set({ messages: formattedMessages });
  },

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
        // WebSocket connected successfully
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
        // WebSocket disconnected
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

  sendMessage: async (content: string) => {
    // Check if message is a command
    if (content.startsWith('/')) {
      // Handle specific commands via WebSocket for better real-time response
      if (content.toLowerCase().trim() === '/idle') {
        // Send idle command directly via WebSocket
        const { websocket, isConnected } = get();

        if (!isConnected || !websocket) {
          console.error('Not connected to WebSocket');
          return;
        }

        // Add user command to chat
        get().addMessage({
          role: 'user',
          content: content,
          timestamp: new Date().toISOString()
        });

        // Send to backend via WebSocket
        websocket.send(JSON.stringify({
          type: 'chat_message',
          data: {
            message: content,
            persona_context: null
          }
        }));

        // Clear current message
        set({ currentMessage: '' });
        return;
      } else {
        // Use API for other commands
        await get().handleCommand(content);
        return;
      }
    }

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

    // Get current persona context for Brain Council
    const getPersonaContext = () => {
      try {
        const personaState = usePersonaStore.getState();
        if (personaState.selectedPersona) {
          const persona = personaState.selectedPersona.persona.data;
          return {
            name: persona.name,
            personality: persona.personality || persona.description,
            creator: persona.creator,
            tags: persona.tags || []
          };
        }
      } catch (e) {
        // Fallback for any errors
      }
      return null;
    };

    // Send to backend with persona context
    websocket.send(JSON.stringify({
      type: 'chat_message',
      data: {
        message: content,
        persona_context: getPersonaContext()
      }
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

  clearChat: (clearType: 'current' | 'all' | 'persona', personaName?: string) => {
    const { websocket, isConnected } = get();

    if (!isConnected || !websocket) {
      console.error('Not connected to WebSocket');
      return;
    }

    websocket.send(JSON.stringify({
      type: 'clear_chat',
      data: {
        clear_type: clearType,
        persona_name: personaName
      }
    }));
  },

  handleCommand: async (command: string) => {
    // Add user command to chat
    get().addMessage({
      role: 'user',
      content: command,
      timestamp: new Date().toISOString()
    });

    try {
      // Get persona context
      const getPersonaContext = () => {
        try {
          const personaState = usePersonaStore.getState();
          if (personaState.selectedPersona) {
            return personaState.selectedPersona.persona.data.name;
          }
        } catch (e) {
          // Fallback for any errors
        }
        return null;
      };

      // Send command to backend
      const response = await fetch('/api/chat/command', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: command,
          persona_name: getPersonaContext()
        }),
      });

      if (response.ok) {
        const result = await response.json();

        // Add success response to chat
        get().addMessage({
          role: 'assistant',
          content: result.message,
          timestamp: new Date().toISOString()
        });

        // If it's a create command, refresh storage
        if (result.command === 'create' && result.created_object) {
          // Import the room store and refresh storage items
          const { useRoomStore } = await import('./roomStore');
          const roomStore = useRoomStore.getState();
          await roomStore.loadStorageItems();

          console.log(`Created object: ${result.created_object.name}`);
        }

      } else {
        const error = await response.json();
        get().addMessage({
          role: 'system',
          content: `Command failed: ${error.detail}`,
          timestamp: new Date().toISOString()
        });
      }

    } catch (error) {
      console.error('Error processing command:', error);
      get().addMessage({
        role: 'system',
        content: `Error processing command: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString()
      });
    }

    // Clear current message
    set({ currentMessage: '' });
  },
}));

// Handle incoming WebSocket messages
function handleWebSocketMessage(message: any) {
  const { type, data } = message;
  const store = useChatStore.getState();

  switch (type) {
    case 'connection_established':
      // Connection established successfully
      store.setCurrentModel(data.current_model);
      break;

    case 'chat_history_loaded':
      // Load previous chat history for the persona
      if (data.messages && data.messages.length > 0) {
        store.loadChatHistory(data.messages);
        console.log(`Loaded ${data.count} previous messages`);
      }
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
      // Handle assistant state updates - update both stores
      try {
        // Update legacy roomStore for backward compatibility
        import('./roomStore').then(({ useRoomStore }) => {
          const roomStore = useRoomStore.getState();

          if (data.status) {
            roomStore.setAssistantStatus(data.status.mode === 'active' ? 'active' : 'idle');
          }
          if (data.status?.action) {
            roomStore.setAssistantAction(data.status.action);
          }
          if (data.status?.mood) {
            roomStore.setAssistantMood(data.status.mood);
          }
          if (data.position) {
            roomStore.setAssistantPosition({ x: data.position.x, y: data.position.y });
          }
        }).catch(error => {
          console.error('Error updating room store:', error);
        });

        // Update new FloorPlanStore with coordinate conversion
        import('./floorPlanStore').then(({ useFloorPlanStore }) => {
          const floorPlanStore = useFloorPlanStore.getState();
          floorPlanStore.syncAssistantFromBackend(data);
        }).catch(error => {
          console.error('Error updating floor plan store:', error);
        });
      } catch (error) {
        console.error('Error importing stores:', error);
      }
      break;

    case 'mode_change':
      // Handle mode change notifications
      store.addMessage({
        role: 'system',
        content: data.message || `Assistant is now in ${data.new_mode} mode`,
        timestamp: new Date().toISOString()
      });

      // Update room store assistant status
      try {
        import('./roomStore').then(({ useRoomStore }) => {
          const roomStore = useRoomStore.getState();
          roomStore.setAssistantStatus(data.new_mode === 'active' ? 'active' : 'idle');
        }).catch(error => {
          console.error('Error updating mode in room store:', error);
        });
      } catch (error) {
        console.error('Error importing room store for mode change:', error);
      }
      break;

    case 'error':
      console.error('WebSocket error:', data.message);
      store.addMessage({
        role: 'system',
        content: `Error: ${data.message}`,
        timestamp: new Date().toISOString()
      });
      break;

    case 'chat_cleared':
      // Chat was cleared - update UI
      store.clearMessages();
      store.addMessage({
        role: 'system',
        content: data.message,
        timestamp: new Date().toISOString()
      });
      console.log(`Chat cleared: ${data.clear_type}`);
      break;

    case 'pong':
      // Handle ping/pong for connection keep-alive
      break;

    default:
      // Unknown message type received
  }
}