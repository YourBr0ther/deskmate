/**
 * WebSocket mock utilities for testing.
 *
 * Provides a controllable mock WebSocket for testing real-time features.
 */

// ============================================================================
// Types
// ============================================================================

export interface MockWebSocketMessage {
  type: string;
  payload?: unknown;
  timestamp?: number;
}

export interface MockWebSocketOptions {
  autoConnect?: boolean;
  connectionDelay?: number;
}

// ============================================================================
// Mock WebSocket Class
// ============================================================================

export class TestableWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = TestableWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  private sentMessages: string[] = [];
  private options: MockWebSocketOptions;

  constructor(url: string, options: MockWebSocketOptions = {}) {
    this.url = url;
    this.options = {
      autoConnect: true,
      connectionDelay: 0,
      ...options,
    };

    if (this.options.autoConnect) {
      this.simulateConnect();
    }
  }

  /**
   * Send a message through the WebSocket.
   */
  send(data: string): void {
    if (this.readyState !== TestableWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    this.sentMessages.push(data);
  }

  /**
   * Close the WebSocket connection.
   */
  close(code = 1000, reason = ''): void {
    this.readyState = TestableWebSocket.CLOSING;
    setTimeout(() => {
      this.readyState = TestableWebSocket.CLOSED;
      if (this.onclose) {
        this.onclose(new CloseEvent('close', { code, reason, wasClean: true }));
      }
    }, 0);
  }

  // ============================================================================
  // Test Helpers
  // ============================================================================

  /**
   * Simulate the WebSocket connecting.
   */
  simulateConnect(): void {
    setTimeout(() => {
      this.readyState = TestableWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, this.options.connectionDelay);
  }

  /**
   * Simulate receiving a message from the server.
   */
  simulateMessage(data: MockWebSocketMessage | string): void {
    if (this.onmessage && this.readyState === TestableWebSocket.OPEN) {
      const messageData = typeof data === 'string' ? data : JSON.stringify(data);
      this.onmessage(new MessageEvent('message', { data: messageData }));
    }
  }

  /**
   * Simulate a WebSocket error.
   */
  simulateError(message = 'WebSocket error'): void {
    if (this.onerror) {
      const error = new Event('error');
      (error as unknown as { message: string }).message = message;
      this.onerror(error);
    }
  }

  /**
   * Simulate the server closing the connection.
   */
  simulateServerClose(code = 1000, reason = ''): void {
    this.readyState = TestableWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code, reason, wasClean: code === 1000 }));
    }
  }

  /**
   * Get all messages sent through this WebSocket.
   */
  getSentMessages(): string[] {
    return [...this.sentMessages];
  }

  /**
   * Get sent messages parsed as JSON.
   */
  getSentMessagesAsJson<T = unknown>(): T[] {
    return this.sentMessages.map((msg) => JSON.parse(msg) as T);
  }

  /**
   * Clear the sent message history.
   */
  clearSentMessages(): void {
    this.sentMessages = [];
  }

  /**
   * Check if a specific message was sent.
   */
  wasSent(predicate: (msg: string) => boolean): boolean {
    return this.sentMessages.some(predicate);
  }

  /**
   * Check if a message with specific type was sent.
   */
  wasTypeSent(type: string): boolean {
    return this.sentMessages.some((msg) => {
      try {
        const parsed = JSON.parse(msg);
        return parsed.type === type;
      } catch {
        return false;
      }
    });
  }
}

// ============================================================================
// Factory Functions
// ============================================================================

let activeWebSockets: TestableWebSocket[] = [];

/**
 * Create a mock WebSocket and track it.
 */
export function createMockWebSocket(
  url: string,
  options?: MockWebSocketOptions
): TestableWebSocket {
  const ws = new TestableWebSocket(url, options);
  activeWebSockets.push(ws);
  return ws;
}

/**
 * Get all active mock WebSockets.
 */
export function getActiveWebSockets(): TestableWebSocket[] {
  return activeWebSockets;
}

/**
 * Get the most recently created WebSocket.
 */
export function getLastWebSocket(): TestableWebSocket | undefined {
  return activeWebSockets[activeWebSockets.length - 1];
}

/**
 * Clear all tracked WebSockets (call in afterEach).
 */
export function clearMockWebSockets(): void {
  activeWebSockets.forEach((ws) => {
    if (ws.readyState !== TestableWebSocket.CLOSED) {
      ws.close();
    }
  });
  activeWebSockets = [];
}

// ============================================================================
// Sample Messages
// ============================================================================

export const sampleMessages = {
  chatResponse: {
    type: 'chat_response',
    payload: {
      content: 'Hello! How can I help you?',
      isComplete: true,
    },
  },
  streamingChunk: {
    type: 'streaming_chunk',
    payload: {
      content: 'Hello',
      isComplete: false,
    },
  },
  assistantMove: {
    type: 'assistant_move',
    payload: {
      position: { x: 10, y: 5 },
      path: [
        { x: 5, y: 5 },
        { x: 7, y: 5 },
        { x: 10, y: 5 },
      ],
    },
  },
  expressionChange: {
    type: 'expression_change',
    payload: {
      expression: 'happy',
      mood: 'cheerful',
    },
  },
  objectUpdate: {
    type: 'object_update',
    payload: {
      objectId: 1,
      state: { power: true },
    },
  },
  connectionAck: {
    type: 'connection_ack',
    payload: {
      sessionId: 'test-session-123',
      timestamp: Date.now(),
    },
  },
  error: {
    type: 'error',
    payload: {
      message: 'Something went wrong',
      code: 'ERR_UNKNOWN',
    },
  },
};

// ============================================================================
// Message Sequence Helpers
// ============================================================================

/**
 * Simulate a streaming response over time.
 */
export async function simulateStreamingResponse(
  ws: TestableWebSocket,
  content: string,
  chunkDelay = 50
): Promise<void> {
  const words = content.split(' ');

  for (let i = 0; i < words.length; i++) {
    const word = words[i] + (i < words.length - 1 ? ' ' : '');
    ws.simulateMessage({
      type: 'streaming_chunk',
      payload: {
        content: word,
        isComplete: false,
      },
    });
    await new Promise((resolve) => setTimeout(resolve, chunkDelay));
  }

  ws.simulateMessage({
    type: 'streaming_complete',
    payload: {
      isComplete: true,
    },
  });
}

/**
 * Simulate assistant movement with path updates.
 */
export async function simulateAssistantMovement(
  ws: TestableWebSocket,
  path: Array<{ x: number; y: number }>,
  stepDelay = 100
): Promise<void> {
  for (const position of path) {
    ws.simulateMessage({
      type: 'assistant_position',
      payload: { position },
    });
    await new Promise((resolve) => setTimeout(resolve, stepDelay));
  }

  ws.simulateMessage({
    type: 'movement_complete',
    payload: { position: path[path.length - 1] },
  });
}
