/**
 * Main chat window component for DeskMate
 */

import React, { useEffect, useRef } from 'react';
import { useChatStore } from '../../stores/chatStore';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import ModelSelector from './ModelSelector';

const ChatWindow: React.FC = () => {
  const {
    isConnected,
    isTyping,
    connect,
    disconnect,
    currentModel,
    currentProvider
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [useChatStore.getState().messages]);

  // Connect to WebSocket on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <h2 className="text-lg font-semibold">DeskMate Chat</h2>
          </div>

          <div className="flex items-center space-x-2 text-sm text-gray-400">
            <span>Model:</span>
            <span className="text-white font-medium">{currentModel}</span>
            <span className={`px-2 py-1 rounded text-xs ${
              currentProvider === 'nano_gpt'
                ? 'bg-blue-600 text-white'
                : 'bg-green-600 text-white'
            }`}>
              {currentProvider === 'nano_gpt' ? 'Cloud' : 'Local'}
            </span>
          </div>
        </div>

        {/* Model Selector */}
        <div className="mt-3">
          <ModelSelector />
        </div>

        {/* Connection Status */}
        {!isConnected && (
          <div className="mt-2 p-2 bg-red-600 rounded text-sm">
            Disconnected from server. Attempting to reconnect...
          </div>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <MessageList />

          {/* Typing Indicator */}
          {isTyping && (
            <div className="px-4 py-2">
              <div className="flex items-center space-x-2 text-gray-400">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
                <span className="text-sm">Assistant is typing...</span>
              </div>
            </div>
          )}

          {/* Auto-scroll anchor */}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="flex-shrink-0 border-t border-gray-700">
          <ChatInput />
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;