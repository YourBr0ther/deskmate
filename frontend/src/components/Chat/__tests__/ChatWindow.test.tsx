/**
 * Tests for ChatWindow Component
 *
 * Tests cover:
 * - Initial rendering
 * - Connection status display
 * - Model information display
 * - Clear chat menu
 * - WebSocket connection lifecycle
 * - Typing indicator
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChatWindow from '../ChatWindow';

// Mock child components
jest.mock('../ChatInput', () => () => <div data-testid="chat-input">ChatInput</div>);
jest.mock('../MessageList', () => () => <div data-testid="message-list">MessageList</div>);
jest.mock('../ModelSelector', () => () => <div data-testid="model-selector">ModelSelector</div>);

// Mock stores
const mockConnect = jest.fn();
const mockDisconnect = jest.fn();
const mockClearChat = jest.fn();
let mockChatState = {
  isConnected: true,
  isTyping: false,
  connect: mockConnect,
  disconnect: mockDisconnect,
  currentModel: 'gpt-4o-mini',
  currentProvider: 'nano_gpt',
  clearChat: mockClearChat,
  messages: [],
};

let mockPersonaState: any = {
  selectedPersona: null,
};

jest.mock('../../../stores/chatStore', () => ({
  useChatStore: Object.assign(
    () => mockChatState,
    { getState: () => mockChatState }
  ),
}));

jest.mock('../../../stores/personaStore', () => ({
  usePersonaStore: () => mockPersonaState,
}));

// Mock window.confirm
const mockConfirm = jest.fn();
window.confirm = mockConfirm;

// Mock window.alert
window.alert = jest.fn();

describe('ChatWindow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockConfirm.mockReturnValue(true);
    mockChatState = {
      isConnected: true,
      isTyping: false,
      connect: mockConnect,
      disconnect: mockDisconnect,
      currentModel: 'gpt-4o-mini',
      currentProvider: 'nano_gpt',
      clearChat: mockClearChat,
      messages: [],
    };
    mockPersonaState = {
      selectedPersona: null,
    };
  });

  describe('Initial Rendering', () => {
    it('should render chat window components', () => {
      render(<ChatWindow />);

      expect(screen.getByText('DeskMate Chat')).toBeInTheDocument();
      expect(screen.getByTestId('chat-input')).toBeInTheDocument();
      expect(screen.getByTestId('message-list')).toBeInTheDocument();
      expect(screen.getByTestId('model-selector')).toBeInTheDocument();
    });
  });

  describe('Connection Status', () => {
    it('should show green indicator when connected', () => {
      mockChatState.isConnected = true;
      const { container } = render(<ChatWindow />);

      expect(container.querySelector('.bg-green-500')).toBeInTheDocument();
    });

    it('should show red indicator when disconnected', () => {
      mockChatState.isConnected = false;
      const { container } = render(<ChatWindow />);

      expect(container.querySelector('.bg-red-500')).toBeInTheDocument();
    });

    it('should show disconnect warning when not connected', () => {
      mockChatState.isConnected = false;
      render(<ChatWindow />);

      expect(screen.getByText(/disconnected from server/i)).toBeInTheDocument();
    });
  });

  describe('Model Information', () => {
    it('should display current model name', () => {
      mockChatState.currentModel = 'llama3:latest';
      render(<ChatWindow />);

      expect(screen.getByText('llama3:latest')).toBeInTheDocument();
    });

    it('should show Cloud badge for nano_gpt provider', () => {
      mockChatState.currentProvider = 'nano_gpt';
      render(<ChatWindow />);

      expect(screen.getByText('Cloud')).toBeInTheDocument();
    });

    it('should show Local badge for ollama provider', () => {
      mockChatState.currentProvider = 'ollama';
      render(<ChatWindow />);

      expect(screen.getByText('Local')).toBeInTheDocument();
    });
  });

  describe('WebSocket Connection', () => {
    it('should connect on mount', () => {
      render(<ChatWindow />);

      expect(mockConnect).toHaveBeenCalled();
    });

    it('should disconnect on unmount', () => {
      const { unmount } = render(<ChatWindow />);

      unmount();

      expect(mockDisconnect).toHaveBeenCalled();
    });
  });

  describe('Typing Indicator', () => {
    it('should show typing indicator when assistant is typing', () => {
      mockChatState.isTyping = true;
      render(<ChatWindow />);

      expect(screen.getByText('Assistant is typing...')).toBeInTheDocument();
    });

    it('should not show typing indicator when not typing', () => {
      mockChatState.isTyping = false;
      render(<ChatWindow />);

      expect(screen.queryByText('Assistant is typing...')).not.toBeInTheDocument();
    });
  });

  describe('Clear Chat Menu', () => {
    it('should toggle clear menu on button click', async () => {
      render(<ChatWindow />);

      const clearButton = screen.getByTitle('Clear Chat Options');
      await userEvent.click(clearButton);

      expect(screen.getByText('Clear Current Chat')).toBeInTheDocument();
    });

    it('should show persona clear option when persona is selected', async () => {
      mockPersonaState.selectedPersona = {
        persona: {
          data: {
            name: 'Alice',
          },
        },
      };

      render(<ChatWindow />);

      const clearButton = screen.getByTitle('Clear Chat Options');
      await userEvent.click(clearButton);

      expect(screen.getByText('Clear Alice History')).toBeInTheDocument();
    });

    it('should hide persona clear option when no persona selected', async () => {
      mockPersonaState.selectedPersona = null;

      render(<ChatWindow />);

      const clearButton = screen.getByTitle('Clear Chat Options');
      await userEvent.click(clearButton);

      expect(screen.queryByText(/clear.*history/i)).not.toBeInTheDocument();
    });

    it('should call clearChat with current type', async () => {
      render(<ChatWindow />);

      const clearButton = screen.getByTitle('Clear Chat Options');
      await userEvent.click(clearButton);

      const clearCurrentButton = screen.getByText('Clear Current Chat');
      await userEvent.click(clearCurrentButton);

      expect(mockClearChat).toHaveBeenCalledWith('current', undefined);
    });

    it('should confirm before clearing all', async () => {
      render(<ChatWindow />);

      const clearButton = screen.getByTitle('Clear Chat Options');
      await userEvent.click(clearButton);

      const clearAllButton = screen.getByText(/purge all memory/i);
      await userEvent.click(clearAllButton);

      expect(mockConfirm).toHaveBeenCalled();
    });

    it('should not clear all if user cancels confirmation', async () => {
      mockConfirm.mockReturnValue(false);

      render(<ChatWindow />);

      const clearButton = screen.getByTitle('Clear Chat Options');
      await userEvent.click(clearButton);

      const clearAllButton = screen.getByText(/purge all memory/i);
      await userEvent.click(clearAllButton);

      expect(mockClearChat).not.toHaveBeenCalled();
    });

    it('should close menu when clicking outside', async () => {
      render(<ChatWindow />);

      // Open menu
      const clearButton = screen.getByTitle('Clear Chat Options');
      await userEvent.click(clearButton);

      expect(screen.getByText('Clear Current Chat')).toBeInTheDocument();

      // Click outside
      fireEvent.mouseDown(document.body);

      await waitFor(() => {
        expect(screen.queryByText('Clear Current Chat')).not.toBeInTheDocument();
      });
    });

    it('should call clearChat with persona type', async () => {
      mockPersonaState.selectedPersona = {
        persona: {
          data: {
            name: 'Bob',
          },
        },
      };

      render(<ChatWindow />);

      const clearButton = screen.getByTitle('Clear Chat Options');
      await userEvent.click(clearButton);

      const clearPersonaButton = screen.getByText('Clear Bob History');
      await userEvent.click(clearPersonaButton);

      expect(mockConfirm).toHaveBeenCalled();
      expect(mockClearChat).toHaveBeenCalledWith('persona', 'Bob');
    });
  });
});
