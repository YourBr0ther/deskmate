/**
 * Main chat window component for DeskMate
 */

import React, { useEffect, useRef, useState } from 'react';

import ChatInput from './ChatInput';
import MessageList from './MessageList';
import ModelSelector from './ModelSelector';
import { useChatStore } from '../../stores/chatStore';
import { usePersonaStore } from '../../stores/personaStore';

const ChatWindow: React.FC = () => {
  const {
    isConnected,
    isTyping,
    connect,
    disconnect,
    currentModel,
    currentProvider,
    clearChat
  } = useChatStore();

  const { selectedPersona } = usePersonaStore();
  const [showClearMenu, setShowClearMenu] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const clearMenuRef = useRef<HTMLDivElement>(null);

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

  // Close clear menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (clearMenuRef.current && !clearMenuRef.current.contains(event.target as Node)) {
        setShowClearMenu(false);
      }
    };

    if (showClearMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showClearMenu]);

  const handleClearChat = (clearType: 'current' | 'all' | 'persona') => {
    const personaName = selectedPersona?.persona?.data?.name;

    if (clearType === 'persona' && !personaName) {
      alert('No persona selected');
      return;
    }

    // Confirm destructive actions
    if (clearType === 'all') {
      if (!confirm('⚠️ This will permanently delete ALL conversation history from the database. Are you sure?')) {
        return;
      }
    } else if (clearType === 'persona' && personaName) {
      if (!confirm(`⚠️ This will permanently delete all conversation history for ${personaName}. Are you sure?`)) {
        return;
      }
    }

    clearChat(clearType, personaName);
    setShowClearMenu(false);
  };

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

          <div className="flex items-center space-x-4">
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

            {/* Clear Chat Menu */}
            <div className="relative" ref={clearMenuRef}>
              <button
                onClick={() => setShowClearMenu(!showClearMenu)}
                className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
                title="Clear Chat Options"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>

              {showClearMenu && (
                <div className="absolute right-0 mt-2 w-56 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-50">
                  <div className="p-2 space-y-1">
                    <button
                      onClick={() => handleClearChat('current')}
                      className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 rounded transition-colors"
                    >
                      Clear Current Chat
                    </button>

                    {selectedPersona && (
                      <button
                        onClick={() => handleClearChat('persona')}
                        className="w-full text-left px-3 py-2 text-sm text-yellow-400 hover:bg-gray-700 rounded transition-colors"
                      >
                        Clear {selectedPersona.persona.data.name} History
                      </button>
                    )}

                    <hr className="border-gray-600 my-1" />

                    <button
                      onClick={() => handleClearChat('all')}
                      className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-gray-700 rounded transition-colors"
                    >
                      ⚠️ Purge All Memory (Database)
                    </button>
                  </div>
                </div>
              )}
            </div>
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