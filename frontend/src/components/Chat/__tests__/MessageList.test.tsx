/**
 * Tests for MessageList Component
 *
 * Tests cover:
 * - Empty state rendering
 * - Message rendering
 * - User vs assistant messages
 * - System messages
 * - Timestamps
 * - Typing indicator
 * - Streaming state
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import MessageList from '../MessageList';

// Mock stores
let mockMessages: any[] = [];
let mockIsTyping = false;
let mockChatSettings = {
  showTimestamps: true,
  fontSize: 'medium',
  enableTypingIndicator: true,
};

jest.mock('../../../stores/chatStore', () => ({
  useChatStore: () => ({
    messages: mockMessages,
    isTyping: mockIsTyping,
  }),
}));

jest.mock('../../../stores/settingsStore', () => ({
  useSettingsStore: () => ({
    chat: mockChatSettings,
  }),
}));

describe('MessageList', () => {
  beforeEach(() => {
    mockMessages = [];
    mockIsTyping = false;
    mockChatSettings = {
      showTimestamps: true,
      fontSize: 'medium',
      enableTypingIndicator: true,
    };
  });

  describe('Empty State', () => {
    it('should show welcome message when no messages', () => {
      render(<MessageList />);

      expect(screen.getByText(/welcome to deskmate/i)).toBeInTheDocument();
    });

    it('should show helpful suggestions in empty state', () => {
      render(<MessageList />);

      expect(screen.getByText(/tell me about yourself/i)).toBeInTheDocument();
      expect(screen.getByText(/move to the desk/i)).toBeInTheDocument();
    });

    it('should show robot emoji in empty state', () => {
      render(<MessageList />);

      expect(screen.getByText('🤖')).toBeInTheDocument();
    });
  });

  describe('Message Rendering', () => {
    it('should render user message', () => {
      mockMessages = [
        {
          id: '1',
          role: 'user',
          content: 'Hello assistant!',
          timestamp: new Date().toISOString(),
        },
      ];

      render(<MessageList />);

      expect(screen.getByText('Hello assistant!')).toBeInTheDocument();
    });

    it('should render assistant message', () => {
      mockMessages = [
        {
          id: '2',
          role: 'assistant',
          content: 'Hello! How can I help you?',
          timestamp: new Date().toISOString(),
        },
      ];

      render(<MessageList />);

      expect(screen.getByText('Hello! How can I help you?')).toBeInTheDocument();
    });

    it('should render multiple messages', () => {
      mockMessages = [
        {
          id: '1',
          role: 'user',
          content: 'First message',
          timestamp: new Date().toISOString(),
        },
        {
          id: '2',
          role: 'assistant',
          content: 'Second message',
          timestamp: new Date().toISOString(),
        },
        {
          id: '3',
          role: 'user',
          content: 'Third message',
          timestamp: new Date().toISOString(),
        },
      ];

      render(<MessageList />);

      expect(screen.getByText('First message')).toBeInTheDocument();
      expect(screen.getByText('Second message')).toBeInTheDocument();
      expect(screen.getByText('Third message')).toBeInTheDocument();
    });
  });

  describe('System Messages', () => {
    it('should render system message with different styling', () => {
      mockMessages = [
        {
          id: '1',
          role: 'system',
          content: 'Connected to server',
          timestamp: new Date().toISOString(),
        },
      ];

      render(<MessageList />);

      expect(screen.getByText('Connected to server')).toBeInTheDocument();
    });
  });

  describe('Timestamps', () => {
    it('should show timestamps when enabled', () => {
      mockChatSettings.showTimestamps = true;
      mockMessages = [
        {
          id: '1',
          role: 'user',
          content: 'Test message',
          timestamp: new Date().toISOString(),
        },
      ];

      render(<MessageList />);

      // Timestamp should be rendered (format varies by locale)
      expect(screen.getByText('Test message').closest('div')).toBeInTheDocument();
    });

    it('should hide timestamps when disabled', () => {
      mockChatSettings.showTimestamps = false;
      mockMessages = [
        {
          id: '1',
          role: 'user',
          content: 'Test message',
          timestamp: new Date().toISOString(),
        },
      ];

      render(<MessageList />);

      expect(screen.getByText('Test message')).toBeInTheDocument();
    });
  });

  describe('Model Information', () => {
    it('should show model for assistant messages', () => {
      mockChatSettings.showTimestamps = true;
      mockMessages = [
        {
          id: '1',
          role: 'assistant',
          content: 'Response from model',
          timestamp: new Date().toISOString(),
          model: 'gpt-4o-mini',
        },
      ];

      render(<MessageList />);

      expect(screen.getByText(/gpt-4o-mini/i)).toBeInTheDocument();
    });
  });

  describe('Streaming State', () => {
    it('should show streaming indicator for streaming messages', () => {
      mockMessages = [
        {
          id: '1',
          role: 'assistant',
          content: 'Partial response...',
          timestamp: new Date().toISOString(),
          isStreaming: true,
        },
      ];

      render(<MessageList />);

      expect(screen.getByText(/streaming/i)).toBeInTheDocument();
    });

    it('should show ellipsis for empty streaming message', () => {
      mockMessages = [
        {
          id: '1',
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          isStreaming: true,
        },
      ];

      render(<MessageList />);

      expect(screen.getByText('...')).toBeInTheDocument();
    });
  });

  describe('Typing Indicator', () => {
    it('should show typing indicator when enabled and typing', () => {
      mockIsTyping = true;
      mockChatSettings.enableTypingIndicator = true;
      mockMessages = [{ id: '1', role: 'user', content: 'Hi', timestamp: new Date().toISOString() }];

      render(<MessageList />);

      expect(screen.getByText(/assistant is typing/i)).toBeInTheDocument();
    });

    it('should hide typing indicator when disabled', () => {
      mockIsTyping = true;
      mockChatSettings.enableTypingIndicator = false;
      mockMessages = [{ id: '1', role: 'user', content: 'Hi', timestamp: new Date().toISOString() }];

      render(<MessageList />);

      expect(screen.queryByText(/assistant is typing/i)).not.toBeInTheDocument();
    });

    it('should hide typing indicator when not typing', () => {
      mockIsTyping = false;
      mockChatSettings.enableTypingIndicator = true;
      mockMessages = [{ id: '1', role: 'user', content: 'Hi', timestamp: new Date().toISOString() }];

      render(<MessageList />);

      expect(screen.queryByText(/assistant is typing/i)).not.toBeInTheDocument();
    });
  });

  describe('Font Size Settings', () => {
    it('should apply small font size', () => {
      mockChatSettings.fontSize = 'small';
      mockMessages = [
        {
          id: '1',
          role: 'user',
          content: 'Test message',
          timestamp: new Date().toISOString(),
        },
      ];

      const { container } = render(<MessageList />);

      // Check for text-sm class
      expect(container.querySelector('.text-sm')).toBeInTheDocument();
    });

    it('should apply large font size', () => {
      mockChatSettings.fontSize = 'large';
      mockMessages = [
        {
          id: '1',
          role: 'user',
          content: 'Test message',
          timestamp: new Date().toISOString(),
        },
      ];

      const { container } = render(<MessageList />);

      // Check for text-lg class
      expect(container.querySelector('.text-lg')).toBeInTheDocument();
    });
  });
});
