/**
 * Tests for Chat Store
 *
 * Tests cover:
 * - Message management
 * - WebSocket connection
 * - Model selection
 * - Command handling
 * - Message cleanup
 */

import { act } from '@testing-library/react';
import { useChatStore, ChatMessage, LLMModel } from '../chatStore';

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1;
  static CONNECTING = 0;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: ((error: any) => void) | null = null;

  send = jest.fn();
  close = jest.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) this.onclose();
  });
}

// Mock MessageCleanupService
jest.mock('../../services/messageCleanupService', () => ({
  MessageCleanupService: {
    cleanupMessages: jest.fn((messages: any[]) => messages),
    getCleanupStats: jest.fn(() => ({ removed: 0 })),
    logCleanupActivity: jest.fn(),
  },
}));

// Mock personaStore
jest.mock('../personaStore', () => ({
  usePersonaStore: {
    getState: jest.fn(() => ({
      selectedPersona: {
        persona: {
          data: {
            name: 'TestPersona',
            personality: 'Test personality',
            creator: 'Test',
            tags: [],
          },
        },
      },
    })),
  },
}));

// Mock global WebSocket
(global as any).WebSocket = MockWebSocket;

describe('ChatStore', () => {
  beforeEach(() => {
    // Reset store to initial state
    useChatStore.setState({
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
    });
  });

  // ========================================================================
  // Message Management Tests
  // ========================================================================

  describe('Message Management', () => {
    it('should set current message', () => {
      act(() => {
        useChatStore.getState().setCurrentMessage('Hello there');
      });

      expect(useChatStore.getState().currentMessage).toBe('Hello there');
    });

    it('should add message with generated ID', () => {
      act(() => {
        useChatStore.getState().addMessage({
          role: 'user',
          content: 'Test message',
          timestamp: new Date().toISOString(),
        });
      });

      const state = useChatStore.getState();
      expect(state.messages.length).toBe(1);
      expect(state.messages[0].content).toBe('Test message');
      expect(state.messages[0].id).toBeDefined();
    });

    it('should update existing message', () => {
      act(() => {
        useChatStore.getState().addMessage({
          role: 'assistant',
          content: 'Initial content',
          timestamp: new Date().toISOString(),
          isStreaming: true,
        });
      });

      const messageId = useChatStore.getState().messages[0].id;

      act(() => {
        useChatStore.getState().updateMessage(messageId, {
          content: 'Updated content',
          isStreaming: false,
        });
      });

      const state = useChatStore.getState();
      expect(state.messages[0].content).toBe('Updated content');
      expect(state.messages[0].isStreaming).toBe(false);
    });

    it('should clear all messages', () => {
      act(() => {
        useChatStore.getState().addMessage({
          role: 'user',
          content: 'Message 1',
          timestamp: new Date().toISOString(),
        });
        useChatStore.getState().addMessage({
          role: 'assistant',
          content: 'Message 2',
          timestamp: new Date().toISOString(),
        });
        useChatStore.getState().clearMessages();
      });

      expect(useChatStore.getState().messages).toHaveLength(0);
    });

    it('should load chat history', () => {
      const history: ChatMessage[] = [
        { id: 'msg-1', role: 'user', content: 'Hi', timestamp: '2024-01-01' },
        { id: 'msg-2', role: 'assistant', content: 'Hello', timestamp: '2024-01-01' },
      ];

      act(() => {
        useChatStore.getState().loadChatHistory(history);
      });

      const state = useChatStore.getState();
      expect(state.messages.length).toBe(2);
      expect(state.messages[0].content).toBe('Hi');
    });

    it('should generate ID for messages without one during history load', () => {
      const history = [
        { role: 'user', content: 'Test', timestamp: '2024-01-01' },
      ] as ChatMessage[];

      act(() => {
        useChatStore.getState().loadChatHistory(history);
      });

      const state = useChatStore.getState();
      expect(state.messages[0].id).toBeDefined();
    });
  });

  // ========================================================================
  // Model Management Tests
  // ========================================================================

  describe('Model Management', () => {
    const testModels: LLMModel[] = [
      {
        id: 'gpt-4o-mini',
        name: 'GPT-4o Mini',
        provider: 'nano_gpt',
        description: 'Test model',
        max_tokens: 4096,
        context_window: 128000,
        supports_streaming: true,
        cost_per_token: 0.00015,
      },
      {
        id: 'llama3:latest',
        name: 'Llama 3',
        provider: 'ollama',
        description: 'Local model',
        max_tokens: 4096,
        context_window: 8192,
        supports_streaming: true,
        cost_per_token: 0,
      },
    ];

    it('should set available models', () => {
      act(() => {
        useChatStore.getState().setAvailableModels(testModels);
      });

      expect(useChatStore.getState().availableModels).toHaveLength(2);
    });

    it('should set current model and provider', () => {
      act(() => {
        useChatStore.getState().setAvailableModels(testModels);
        useChatStore.getState().setCurrentModel('gpt-4o-mini');
      });

      const state = useChatStore.getState();
      expect(state.currentModel).toBe('gpt-4o-mini');
      expect(state.currentProvider).toBe('nano_gpt');
    });

    it('should not change model if already current', () => {
      const mockWs = new MockWebSocket();

      act(() => {
        useChatStore.setState({
          websocket: mockWs as any,
          currentModel: 'gpt-4o-mini',
          availableModels: testModels,
        });
      });

      act(() => {
        useChatStore.getState().setCurrentModel('gpt-4o-mini');
      });

      expect(mockWs.send).not.toHaveBeenCalled();
    });

    it('should update current model without WebSocket message', () => {
      act(() => {
        useChatStore.getState().updateCurrentModel('custom-model', 'ollama');
      });

      const state = useChatStore.getState();
      expect(state.currentModel).toBe('custom-model');
      expect(state.currentProvider).toBe('ollama');
    });
  });

  // ========================================================================
  // Connection Management Tests
  // ========================================================================

  describe('Connection Management', () => {
    it('should set connected state', () => {
      act(() => {
        useChatStore.getState().setConnected(true);
      });

      expect(useChatStore.getState().isConnected).toBe(true);
    });

    it('should set typing state', () => {
      act(() => {
        useChatStore.getState().setTyping(true);
      });

      expect(useChatStore.getState().isTyping).toBe(true);
    });

    it('should disconnect and cleanup', () => {
      const mockWs = new MockWebSocket();

      act(() => {
        useChatStore.setState({
          websocket: mockWs as any,
          isConnected: true,
        });
      });

      act(() => {
        useChatStore.getState().disconnect();
      });

      expect(mockWs.close).toHaveBeenCalled();
      const state = useChatStore.getState();
      expect(state.websocket).toBeNull();
      expect(state.isConnected).toBe(false);
    });
  });

  // ========================================================================
  // Send Message Tests
  // ========================================================================

  describe('Send Message', () => {
    it('should not send if not connected', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await act(async () => {
        await useChatStore.getState().sendMessage('Test');
      });

      expect(consoleSpy).toHaveBeenCalledWith('Not connected to WebSocket');
      consoleSpy.mockRestore();
    });

    it('should send chat message and add to history', async () => {
      const mockWs = new MockWebSocket();

      act(() => {
        useChatStore.setState({
          websocket: mockWs as any,
          isConnected: true,
        });
      });

      await act(async () => {
        await useChatStore.getState().sendMessage('Hello');
      });

      // Should add user message
      expect(useChatStore.getState().messages.length).toBe(1);
      expect(useChatStore.getState().messages[0].role).toBe('user');
      expect(useChatStore.getState().messages[0].content).toBe('Hello');

      // Should send via WebSocket
      expect(mockWs.send).toHaveBeenCalled();

      // Should clear current message
      expect(useChatStore.getState().currentMessage).toBe('');
    });

    it('should set typing indicator when sending message', async () => {
      const mockWs = new MockWebSocket();

      act(() => {
        useChatStore.setState({
          websocket: mockWs as any,
          isConnected: true,
        });
      });

      await act(async () => {
        await useChatStore.getState().sendMessage('Hello');
      });

      expect(useChatStore.getState().isTyping).toBe(true);
    });
  });

  // ========================================================================
  // Assistant Move Tests
  // ========================================================================

  describe('Assistant Move', () => {
    it('should send assistant move command', () => {
      const mockWs = new MockWebSocket();

      act(() => {
        useChatStore.setState({
          websocket: mockWs as any,
          isConnected: true,
        });
      });

      act(() => {
        useChatStore.getState().sendAssistantMove(100, 200);
      });

      expect(mockWs.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"assistant_move"')
      );
    });

    it('should not send move if not connected', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      act(() => {
        useChatStore.getState().sendAssistantMove(100, 200);
      });

      expect(consoleSpy).toHaveBeenCalledWith('Not connected to WebSocket');
      consoleSpy.mockRestore();
    });
  });

  // ========================================================================
  // Clear Chat Tests
  // ========================================================================

  describe('Clear Chat', () => {
    it('should send clear chat command', () => {
      const mockWs = new MockWebSocket();

      act(() => {
        useChatStore.setState({
          websocket: mockWs as any,
          isConnected: true,
        });
      });

      act(() => {
        useChatStore.getState().clearChat('current');
      });

      expect(mockWs.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"clear_chat"')
      );
    });

    it('should send clear with persona name', () => {
      const mockWs = new MockWebSocket();

      act(() => {
        useChatStore.setState({
          websocket: mockWs as any,
          isConnected: true,
        });
      });

      act(() => {
        useChatStore.getState().clearChat('persona', 'Alice');
      });

      const sendArg = mockWs.send.mock.calls[0][0];
      expect(sendArg).toContain('"persona_name":"Alice"');
    });
  });

  // ========================================================================
  // Request Chat History Tests
  // ========================================================================

  describe('Request Chat History', () => {
    it('should request history and clear messages', () => {
      const mockWs = new MockWebSocket();

      act(() => {
        useChatStore.setState({
          websocket: mockWs as any,
          isConnected: true,
          messages: [
            { id: '1', role: 'user', content: 'Old', timestamp: '' },
          ],
        });
      });

      act(() => {
        useChatStore.getState().requestChatHistory('Alice');
      });

      expect(useChatStore.getState().messages).toHaveLength(0);
      expect(mockWs.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"request_chat_history"')
      );
    });

    it('should warn if not connected', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      act(() => {
        useChatStore.getState().requestChatHistory('Alice');
      });

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  // ========================================================================
  // Message Cleanup Tests
  // ========================================================================

  describe('Message Cleanup', () => {
    it('should cleanup old messages', () => {
      const { MessageCleanupService } = require('../../services/messageCleanupService');

      act(() => {
        useChatStore.setState({
          messages: [
            { id: '1', role: 'user', content: 'Old', timestamp: '2020-01-01' },
            { id: '2', role: 'user', content: 'New', timestamp: new Date().toISOString() },
          ],
        });
      });

      // Mock to return filtered messages
      MessageCleanupService.cleanupMessages.mockReturnValue([
        { id: '2', role: 'user', content: 'New', timestamp: new Date().toISOString() },
      ]);

      act(() => {
        useChatStore.getState().cleanupOldMessages(7);
      });

      expect(MessageCleanupService.cleanupMessages).toHaveBeenCalled();
    });
  });
});
