/**
 * Tests for ChatInput Component
 *
 * Tests cover:
 * - Input rendering
 * - Message typing
 * - Send functionality
 * - Disabled states
 * - Keyboard shortcuts
 * - Status indicators
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChatInput from '../ChatInput';

// Mock chat store
const mockSendMessage = jest.fn();
const mockSetCurrentMessage = jest.fn();
let mockStoreState = {
  currentMessage: '',
  isConnected: true,
  isTyping: false,
  sendMessage: mockSendMessage,
  setCurrentMessage: mockSetCurrentMessage,
};

jest.mock('../../../stores/chatStore', () => ({
  useChatStore: () => mockStoreState,
}));

describe('ChatInput', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockStoreState = {
      currentMessage: '',
      isConnected: true,
      isTyping: false,
      sendMessage: mockSendMessage,
      setCurrentMessage: mockSetCurrentMessage,
    };
  });

  describe('Rendering', () => {
    it('should render textarea and send button', () => {
      render(<ChatInput />);

      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });

    it('should show connected status when connected', () => {
      mockStoreState.isConnected = true;
      render(<ChatInput />);

      expect(screen.getByText(/connected/i)).toBeInTheDocument();
    });

    it('should show disconnected status when not connected', () => {
      mockStoreState.isConnected = false;
      render(<ChatInput />);

      expect(screen.getByText(/disconnected/i)).toBeInTheDocument();
    });

    it('should show typing indicator when assistant is typing', () => {
      mockStoreState.isTyping = true;
      render(<ChatInput />);

      expect(screen.getByText(/assistant is typing/i)).toBeInTheDocument();
    });
  });

  describe('Input Behavior', () => {
    it('should call setCurrentMessage when typing', async () => {
      render(<ChatInput />);

      const textarea = screen.getByRole('textbox');
      await userEvent.type(textarea, 'Hello');

      expect(mockSetCurrentMessage).toHaveBeenCalled();
    });

    it('should show character count when message is not empty', () => {
      mockStoreState.currentMessage = 'Hello World';
      render(<ChatInput />);

      expect(screen.getByText('11 characters')).toBeInTheDocument();
    });

    it('should not show character count when message is empty', () => {
      mockStoreState.currentMessage = '';
      render(<ChatInput />);

      expect(screen.queryByText(/characters/i)).not.toBeInTheDocument();
    });
  });

  describe('Send Functionality', () => {
    it('should send message when send button is clicked', async () => {
      mockStoreState.currentMessage = 'Hello';
      render(<ChatInput />);

      const sendButton = screen.getByRole('button', { name: /send/i });
      await userEvent.click(sendButton);

      expect(mockSendMessage).toHaveBeenCalledWith('Hello');
    });

    it('should send message on Enter key press', async () => {
      mockStoreState.currentMessage = 'Hello';
      render(<ChatInput />);

      const textarea = screen.getByRole('textbox');
      fireEvent.keyPress(textarea, { key: 'Enter', shiftKey: false });

      expect(mockSendMessage).toHaveBeenCalledWith('Hello');
    });

    it('should not send on Shift+Enter (allows new line)', async () => {
      mockStoreState.currentMessage = 'Hello';
      render(<ChatInput />);

      const textarea = screen.getByRole('textbox');
      fireEvent.keyPress(textarea, { key: 'Enter', shiftKey: true });

      expect(mockSendMessage).not.toHaveBeenCalled();
    });

    it('should not send empty message', async () => {
      mockStoreState.currentMessage = '   ';
      render(<ChatInput />);

      const sendButton = screen.getByRole('button', { name: /send/i });
      await userEvent.click(sendButton);

      expect(mockSendMessage).not.toHaveBeenCalled();
    });
  });

  describe('Disabled States', () => {
    it('should disable send button when disconnected', () => {
      mockStoreState.isConnected = false;
      mockStoreState.currentMessage = 'Hello';
      render(<ChatInput />);

      const sendButton = screen.getByRole('button', { name: /send/i });
      expect(sendButton).toBeDisabled();
    });

    it('should disable send button when assistant is typing', () => {
      mockStoreState.isTyping = true;
      mockStoreState.currentMessage = 'Hello';
      render(<ChatInput />);

      const sendButton = screen.getByRole('button');
      expect(sendButton).toBeDisabled();
    });

    it('should disable send button when message is empty', () => {
      mockStoreState.currentMessage = '';
      render(<ChatInput />);

      const sendButton = screen.getByRole('button', { name: /send/i });
      expect(sendButton).toBeDisabled();
    });

    it('should disable textarea when disconnected', () => {
      mockStoreState.isConnected = false;
      render(<ChatInput />);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeDisabled();
    });

    it('should show wait button when typing', () => {
      mockStoreState.isTyping = true;
      render(<ChatInput />);

      expect(screen.getByText(/wait/i)).toBeInTheDocument();
    });
  });

  describe('Placeholder Text', () => {
    it('should show connecting placeholder when disconnected', () => {
      mockStoreState.isConnected = false;
      render(<ChatInput />);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('placeholder', 'Connecting...');
    });

    it('should show responding placeholder when typing', () => {
      mockStoreState.isTyping = true;
      render(<ChatInput />);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('placeholder', expect.stringContaining('responding'));
    });

    it('should show default placeholder when connected and idle', () => {
      render(<ChatInput />);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('placeholder', expect.stringContaining('Type your message'));
    });
  });
});
