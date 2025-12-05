/**
 * Typed WebSocket Service for DeskMate
 *
 * Provides a strongly typed WebSocket connection with automatic reconnection,
 * event handling, and integration with the spatial store.
 */

import { useChatStore } from '../stores/chatStore';
import { useSpatialStore } from '../stores/spatialStore';
import { Position } from '../utils/coordinateSystem';

// ============================================================================
// WebSocket Event Types
// ============================================================================

// Inbound events (from server)
export interface WebSocketInboundEvents {
  // Connection events - matches backend websocket.py
  connection_established: {
    message: string;
    current_model: string;
    provider: string;
    conversation_id: string;
  };

  // Chat events
  chat_message: {
    role: 'assistant' | 'system';
    content: string;
    timestamp: string;
    model?: string;
  };

  chat_stream: {
    content: string;
    full_content: string;
    done: boolean;
  };

  chat_history_loaded: {
    messages: any[];
    count: number;
  };

  chat_cleared: {
    clear_type: 'current' | 'all' | 'persona';
    message: string;
  };

  // Assistant state events - matches backend AssistantState.to_dict() structure
  assistant_state: {
    id: string;
    location: {
      floor_plan_id: string | null;
      room_id: string | null;
      position: { x: number; y: number };
      facing: string;
      facing_angle: number;
    };
    movement: {
      is_moving: boolean;
      target: { x: number; y: number; room_id: string | null } | null;
      path: any[] | null;
      speed: number;
    };
    status: {
      action: string;
      mood: string;
      expression: string;
      energy: number;
      mode: string;
      attention: number;
    };
    interaction: {
      holding: string | null;
      sitting_on: string | null;
      interacting_with: string | null;
    };
    goals?: any[];
    working_memory?: any[];
    timestamps?: Record<string, string | null>;
  };

  assistant_typing: {
    typing: boolean;
  };

  mode_change: {
    old_mode: 'active' | 'idle';
    new_mode: 'active' | 'idle';
    message: string;
  };

  // Object and room events
  object_created: {
    object: any;
    room_id: string;
  };

  object_moved: {
    object_id: string;
    old_position: Position;
    new_position: Position;
  };

  object_state_changed: {
    object_id: string;
    state_key: string;
    old_value: any;
    new_value: any;
  };

  object_deleted: {
    object_id: string;
    room_id: string;
  };

  room_updated: {
    room_id: string;
    changes: any;
  };

  // Storage events
  storage_item_added: {
    item: any;
  };

  storage_item_removed: {
    item_id: string;
  };

  storage_item_placed: {
    item_id: string;
    object_id: string;
    position: Position;
  };

  // Model events
  model_changed: {
    model: string;
    provider: 'nano_gpt' | 'ollama';
  };

  // Error events
  error: {
    message: string;
    error_code?: string;
    category?: string;
  };

  // Keep-alive
  pong: {
    timestamp: number;
  };

  // Idle mode events
  idle_status: {
    mode: string;
    last_user_interaction: string;
    inactivity_duration_minutes: number;
    idle_timeout_minutes: number;
    is_idle_enabled: boolean;
  };

  dreams: {
    dreams: Array<{
      id: string;
      content: string;
      action_type: string;
      created_at: string;
    }>;
    limit: number;
    hours_back: number;
  };

  // Position update (from navigation service)
  position_update: {
    assistant_id: string;
    position: { x: number; y: number };
    timestamp: string;
  };

  // Room transition (when assistant moves between rooms)
  room_transition: {
    assistant_id: string;
    from_room: string;
    to_room: string;
    doorway_id: string;
    timestamp: string;
  };

  // State update (response to get_state request)
  state_update: {
    assistant: WebSocketInboundEvents['assistant_state'];
    model: string;
    provider: string;
  };
}

// Outbound events (to server)
export interface WebSocketOutboundEvents {
  // Chat events
  chat_message: {
    message: string;
    persona_context?: any;
  };

  request_chat_history: {
    persona_name?: string;
  };

  clear_chat: {
    clear_type: 'current' | 'all' | 'persona';
    persona_name?: string;
  };

  // Assistant control
  assistant_move: {
    x: number;
    y: number;
  };

  // Object manipulation
  object_move: {
    object_id: string;
    x: number;
    y: number;
  };

  object_interact: {
    object_id: string;
    action: string;
  };

  object_pick_up: {
    object_id: string;
  };

  object_put_down: {
    x?: number;
    y?: number;
  };

  // Model control
  model_change: {
    model_id: string;
  };

  // Keep-alive
  ping: {
    timestamp: number;
  };

  // Idle mode control
  idle_command: {
    command: 'force_idle' | 'force_active' | 'get_status' | 'get_dreams';
    limit?: number;
    hours_back?: number;
  };

  // State request
  get_state: Record<string, never>;  // Empty object
}

// ============================================================================
// WebSocket Event Handlers
// ============================================================================

type EventHandler<T> = (data: T) => void;

export class TypedWebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private isConnected = false;
  private pingInterval: NodeJS.Timeout | null = null;
  private listeners: Map<string, Set<EventHandler<any>>> = new Map();

  // Event handlers
  private eventHandlers: {
    [K in keyof WebSocketInboundEvents]: EventHandler<WebSocketInboundEvents[K]>
  };

  constructor(url?: string) {
    this.url = url || `ws://${window.location.hostname}:8000/ws`;

    // Initialize event handlers
    this.eventHandlers = {
      connection_established: this.handleConnectionEstablished.bind(this),
      chat_message: this.handleChatMessage.bind(this),
      chat_stream: this.handleChatStream.bind(this),
      chat_history_loaded: this.handleChatHistoryLoaded.bind(this),
      chat_cleared: this.handleChatCleared.bind(this),
      assistant_state: this.handleAssistantState.bind(this),
      assistant_typing: this.handleAssistantTyping.bind(this),
      position_update: this.handlePositionUpdate.bind(this),
      room_transition: this.handleRoomTransition.bind(this),
      mode_change: this.handleModeChange.bind(this),
      object_created: this.handleObjectCreated.bind(this),
      object_moved: this.handleObjectMoved.bind(this),
      object_state_changed: this.handleObjectStateChanged.bind(this),
      object_deleted: this.handleObjectDeleted.bind(this),
      room_updated: this.handleRoomUpdated.bind(this),
      storage_item_added: this.handleStorageItemAdded.bind(this),
      storage_item_removed: this.handleStorageItemRemoved.bind(this),
      storage_item_placed: this.handleStorageItemPlaced.bind(this),
      model_changed: this.handleModelChanged.bind(this),
      error: this.handleError.bind(this),
      pong: this.handlePong.bind(this),
      idle_status: this.handleIdleStatus.bind(this),
      dreams: this.handleDreams.bind(this),
      state_update: this.handleStateUpdate.bind(this)
    };
  }

  // ========================================================================
  // Connection Management
  // ========================================================================

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          this.startPingInterval();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.isConnected = false;
          this.stopPingInterval();
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.maxReconnectAttempts = 0; // Prevent reconnection
    this.stopPingInterval();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.isConnected = false;
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

    setTimeout(() => {
      this.connect().catch(() => {
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // Cap at 30 seconds
      });
    }, this.reconnectDelay);
  }

  // ========================================================================
  // Message Handling
  // ========================================================================

  private handleMessage(message: { type: string; data: any }): void {
    const { type, data } = message;

    // Call registered handler
    if (this.eventHandlers[type as keyof WebSocketInboundEvents]) {
      this.eventHandlers[type as keyof WebSocketInboundEvents](data);
    }

    // Call custom listeners
    const listeners = this.listeners.get(type);
    if (listeners) {
      listeners.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in listener for ${type}:`, error);
        }
      });
    }
  }

  // ========================================================================
  // Event Handlers
  // ========================================================================

  private handleConnectionEstablished(data: WebSocketInboundEvents['connection_established']): void {
    const chatStore = useChatStore.getState();
    chatStore.updateCurrentModel(data.current_model, data.provider as 'nano_gpt' | 'ollama');
    console.log(`WebSocket connected: ${data.message} (conversation: ${data.conversation_id})`);
  }

  private handleChatMessage(data: WebSocketInboundEvents['chat_message']): void {
    const chatStore = useChatStore.getState();
    chatStore.addMessage({
      role: data.role,
      content: data.content,
      timestamp: data.timestamp,
      model: data.model
    });
  }

  private handleChatStream(data: WebSocketInboundEvents['chat_stream']): void {
    const chatStore = useChatStore.getState();

    // Hide typing indicator when streaming starts
    chatStore.setTyping(false);

    // Find the last assistant message and update it
    const messages = chatStore.messages;
    const lastMessage = messages[messages.length - 1];

    if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
      chatStore.updateMessage(lastMessage.id, {
        content: data.full_content,
        isStreaming: !data.done  // Mark as complete when done=true
      });
    } else {
      // Create new streaming message
      chatStore.addMessage({
        role: 'assistant',
        content: data.content,
        timestamp: new Date().toISOString(),
        isStreaming: !data.done  // May be complete on first message if short
      });
    }
  }

  private handleChatHistoryLoaded(data: WebSocketInboundEvents['chat_history_loaded']): void {
    const chatStore = useChatStore.getState();
    if (data.messages && data.messages.length > 0) {
      chatStore.loadChatHistory(data.messages);
      console.log(`Loaded ${data.count} previous messages`);
    }
  }

  private handleChatCleared(data: WebSocketInboundEvents['chat_cleared']): void {
    const chatStore = useChatStore.getState();
    chatStore.clearMessages();
    chatStore.addMessage({
      role: 'system',
      content: data.message,
      timestamp: new Date().toISOString()
    });
    console.log(`Chat cleared: ${data.clear_type}`);
  }

  private handleAssistantState(data: WebSocketInboundEvents['assistant_state']): void {
    const spatialStore = useSpatialStore.getState();

    // Extract position from nested location object
    if (data.location?.position) {
      spatialStore.setAssistantPosition(data.location.position);
    }

    // Extract and map status fields
    if (data.status) {
      spatialStore.setAssistantStatus({
        status: data.status.mode === 'active' ? 'active' : 'idle',
        mood: data.status.mood as any,
        current_action: data.status.action,
        energy_level: data.status.energy  // Backend uses "energy", frontend uses "energy_level"
      });
    }

    // Extract interaction fields from nested object
    if (data.interaction) {
      spatialStore.setAssistantStatus({
        holding_object_id: data.interaction.holding,
        sitting_on_object_id: data.interaction.sitting_on
      });
    }

    // Handle movement state
    if (data.movement) {
      spatialStore.setAssistantStatus({
        isMoving: data.movement.is_moving
      });
    }

    // Handle facing direction from location
    if (data.location?.facing) {
      spatialStore.setAssistantStatus({
        facing: data.location.facing as 'up' | 'down' | 'left' | 'right'
      });
    }
  }

  private handleAssistantTyping(data: WebSocketInboundEvents['assistant_typing']): void {
    const chatStore = useChatStore.getState();
    console.log('Assistant typing event:', data.typing);
    chatStore.setTyping(data.typing);

    if (!data.typing) {
      // Mark last message as complete when typing stops
      const messages = chatStore.messages;
      const lastMsg = messages[messages.length - 1];
      if (lastMsg && lastMsg.isStreaming) {
        chatStore.updateMessage(lastMsg.id, { isStreaming: false });
      }
    }
  }

  private handlePositionUpdate(data: WebSocketInboundEvents['position_update']): void {
    const spatialStore = useSpatialStore.getState();
    console.log('Position update:', data);

    // Update assistant position in the store
    spatialStore.setAssistantPosition(data.position);
  }

  private handleRoomTransition(data: WebSocketInboundEvents['room_transition']): void {
    console.log('Room transition:', data);

    // Room transitions are handled automatically by the UI components
    // that listen to WebSocket events. The floor plan components
    // will re-render based on the assistant's position updates.

    // Dispatch a custom event for components that need to react to room changes
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('deskmate:room-transition', {
        detail: data
      }));
    }
  }

  private handleModeChange(data: WebSocketInboundEvents['mode_change']): void {
    const chatStore = useChatStore.getState();
    const spatialStore = useSpatialStore.getState();

    // Add system message
    chatStore.addMessage({
      role: 'system',
      content: data.message || `Assistant is now in ${data.new_mode} mode`,
      timestamp: new Date().toISOString()
    });

    // Update spatial store
    spatialStore.setAssistantStatus({
      status: data.new_mode === 'active' ? 'active' : 'idle'
    });
  }

  private handleObjectCreated(data: WebSocketInboundEvents['object_created']): void {
    const spatialStore = useSpatialStore.getState();
    spatialStore.addObject({
      id: data.object.id,
      type: data.object.type || 'furniture',
      name: data.object.name,
      position: data.object.position,
      size: data.object.size,
      solid: data.object.solid !== false,
      interactive: data.object.interactive !== false,
      movable: data.object.movable === true,
      states: data.object.states || {},
      room_id: data.room_id,
      properties: data.object.properties || {}
    });
  }

  private handleObjectMoved(data: WebSocketInboundEvents['object_moved']): void {
    const spatialStore = useSpatialStore.getState();
    spatialStore.setObjectPosition(data.object_id, data.new_position);
  }

  private handleObjectStateChanged(data: WebSocketInboundEvents['object_state_changed']): void {
    const spatialStore = useSpatialStore.getState();
    spatialStore.setObjectStates(data.object_id, {
      [data.state_key]: data.new_value
    });
  }

  private handleObjectDeleted(data: WebSocketInboundEvents['object_deleted']): void {
    const spatialStore = useSpatialStore.getState();
    spatialStore.removeObject(data.object_id);
  }

  private handleRoomUpdated(data: WebSocketInboundEvents['room_updated']): void {
    // Handle room updates if needed
    console.log('Room updated:', data);
  }

  private handleStorageItemAdded(data: WebSocketInboundEvents['storage_item_added']): void {
    const spatialStore = useSpatialStore.getState();
    spatialStore.addStorageItem({
      id: data.item.id,
      name: data.item.name,
      type: data.item.type,
      size: data.item.size,
      properties: data.item.properties || {},
      created_at: data.item.created_at
    });
  }

  private handleStorageItemRemoved(data: WebSocketInboundEvents['storage_item_removed']): void {
    const spatialStore = useSpatialStore.getState();
    spatialStore.removeStorageItem(data.item_id);
  }

  private handleStorageItemPlaced(data: WebSocketInboundEvents['storage_item_placed']): void {
    const spatialStore = useSpatialStore.getState();
    spatialStore.removeStorageItem(data.item_id);
    // Object should be added via object_created event
  }

  private handleModelChanged(data: WebSocketInboundEvents['model_changed']): void {
    const chatStore = useChatStore.getState();
    chatStore.updateCurrentModel(data.model, data.provider);
    chatStore.addMessage({
      role: 'system',
      content: `Switched to ${data.model} (${data.provider})`,
      timestamp: new Date().toISOString()
    });
  }

  private handleError(data: WebSocketInboundEvents['error']): void {
    console.error('WebSocket error:', data.message);
    const spatialStore = useSpatialStore.getState();
    spatialStore.setError(data.message);

    const chatStore = useChatStore.getState();
    chatStore.addMessage({
      role: 'system',
      content: `Error: ${data.message}`,
      timestamp: new Date().toISOString()
    });
  }

  private handlePong(data: WebSocketInboundEvents['pong']): void {
    // Handle ping/pong for connection keep-alive
    console.debug('Received pong:', data.timestamp);
  }

  private handleIdleStatus(data: WebSocketInboundEvents['idle_status']): void {
    console.log('Idle status received:', data);
    const spatialStore = useSpatialStore.getState();

    // Update assistant mode based on idle status
    spatialStore.setAssistantStatus({
      status: data.mode === 'active' ? 'active' : 'idle'
    });
  }

  private handleDreams(data: WebSocketInboundEvents['dreams']): void {
    console.log(`Dreams received: ${data.dreams.length} dreams from last ${data.hours_back} hours`);

    // Optionally add dream summaries as system messages
    if (data.dreams.length > 0) {
      const chatStore = useChatStore.getState();
      const dreamSummary = data.dreams
        .slice(0, 3)  // Show first 3 dreams
        .map(d => `- ${d.content}`)
        .join('\n');

      chatStore.addMessage({
        role: 'system',
        content: `Recent dreams while idle:\n${dreamSummary}`,
        timestamp: new Date().toISOString()
      });
    }
  }

  private handleStateUpdate(data: WebSocketInboundEvents['state_update']): void {
    // Delegate assistant state handling to existing handler
    this.handleAssistantState(data.assistant);

    // Update model info
    const chatStore = useChatStore.getState();
    chatStore.updateCurrentModel(data.model, data.provider as 'nano_gpt' | 'ollama');
  }

  // ========================================================================
  // Send Methods
  // ========================================================================

  send<K extends keyof WebSocketOutboundEvents>(
    type: K,
    data: WebSocketOutboundEvents[K]
  ): void {
    if (!this.isConnected || !this.ws) {
      console.error('WebSocket not connected');
      return;
    }

    try {
      this.ws.send(JSON.stringify({ type, data }));
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
    }
  }

  // ========================================================================
  // Event Listeners
  // ========================================================================

  addEventListener<K extends keyof WebSocketInboundEvents>(
    type: K,
    handler: EventHandler<WebSocketInboundEvents[K]>
  ): void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)!.add(handler);
  }

  removeEventListener<K extends keyof WebSocketInboundEvents>(
    type: K,
    handler: EventHandler<WebSocketInboundEvents[K]>
  ): void {
    const listeners = this.listeners.get(type);
    if (listeners) {
      listeners.delete(handler);
      if (listeners.size === 0) {
        this.listeners.delete(type);
      }
    }
  }

  // ========================================================================
  // Ping/Pong
  // ========================================================================

  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      this.send('ping', { timestamp: Date.now() });
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  // ========================================================================
  // Getters
  // ========================================================================

  get connected(): boolean {
    return this.isConnected;
  }

  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

// ============================================================================
// Singleton Instance
// ============================================================================

export const websocketService = new TypedWebSocketService();