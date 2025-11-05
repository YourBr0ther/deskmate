/**
 * Chat container component for desktop and tablet layouts.
 *
 * Provides a persistent chat interface for larger screens with
 * full messaging functionality and assistant interaction.
 */

import React, { useRef, useEffect } from 'react';
import { useDeviceDetection } from '../../hooks/useDeviceDetection';
import { useChatStore } from '../../stores/chatStore';
import { usePersonaStore } from '../../stores/personaStore';
import ModelSelector from './ModelSelector';

interface ChatContainerProps {
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Desktop/tablet persistent chat container.
 */
export const ChatContainer: React.FC<ChatContainerProps> = ({
  className = '',
  style = {}
}) => {
  const deviceInfo = useDeviceDetection();
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesRef = useRef<HTMLDivElement>(null);

  // Chat store state
  const {
    messages,
    currentMessage,
    isConnected,
    isTyping,
    setCurrentMessage,
    sendMessage,
    clearChat,
    connect,
    disconnect,
    currentModel,
    availableModels,
    requestChatHistory
  } = useChatStore();

  // Persona store state
  const { selectedPersona } = usePersonaStore();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  // Load chat history when persona changes
  useEffect(() => {
    if (selectedPersona && isConnected) {
      // Request chat history for the new persona
      const personaName = selectedPersona.persona.data.name;
      console.log(`Loading chat history for persona: ${personaName}`);
      requestChatHistory(personaName);
    }
  }, [selectedPersona, isConnected, requestChatHistory]);

  // Handle sending a message
  const handleSendMessage = async () => {
    if (!currentMessage.trim() || !isConnected) return;
    await sendMessage(currentMessage);
  };

  // Handle input key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Clear chat history
  const handleClearChat = () => {
    clearChat('current');
  };

  // Get current persona info
  const getPersonaInfo = () => {
    if (selectedPersona) {
      return {
        name: selectedPersona.persona.data.name,
        creator: selectedPersona.persona.data.creator || 'Unknown'
      };
    }
    return {
      name: 'No Assistant Selected',
      creator: 'System'
    };
  };

  const personaInfo = getPersonaInfo();

  return (
    <div className={`chat-container flex flex-col h-full bg-white ${className}`} style={style}>
      {/* Assistant Status Bar */}
      <div className="assistant-status flex items-center justify-between p-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            <span className="text-white text-sm">
              {selectedPersona ? '🤖' : '❌'}
            </span>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-800">{personaInfo.name}</p>
            <p className="text-xs text-gray-500">
              {isConnected ? `Connected • ${personaInfo.creator}` : 'Disconnected'}
            </p>
          </div>
        </div>

        {/* Chat controls and model selector */}
        <div className="flex items-center space-x-2">
          <div className="text-xs text-gray-500">
            {availableModels.find(m => m.id === currentModel)?.name || currentModel}
          </div>
          <button
            onClick={handleClearChat}
            className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded"
            title="Clear chat"
            disabled={!isConnected}
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414L9.586 12l-3.293 3.293a1 1 0 101.414 1.414L10 13.414l2.293 2.293a1 1 0 001.414-1.414L11.414 12l2.293-2.293z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>

      {/* Model Selector */}
      <div className="p-3 bg-gray-800">
        <ModelSelector />
      </div>

      {/* Messages Area */}
      <div
        ref={messagesRef}
        className="messages-area flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.length === 0 && (
          <div className="flex justify-center items-center h-full">
            <div className="text-center text-gray-500">
              <p className="text-sm">
                {selectedPersona
                  ? `Start a conversation with ${personaInfo.name}!`
                  : 'Please select an assistant to begin chatting'
                }
              </p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white rounded-br-sm'
                  : message.role === 'system'
                  ? 'bg-yellow-100 text-yellow-800 rounded-bl-sm'
                  : 'bg-gray-100 text-gray-800 rounded-bl-sm'
              }`}
            >
              <p className="text-sm leading-relaxed">
                {message.content}
              </p>
              <div className="flex items-center justify-between mt-1">
                <p className={`text-xs ${
                  message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                }`}>
                  {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
                {message.model && message.role === 'assistant' && (
                  <p className="text-xs ml-2 text-gray-400">
                    {message.model}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 px-4 py-2 rounded-lg rounded-bl-sm">
              <div className="flex space-x-1 items-center">
                <span className="text-sm text-gray-600">Assistant is typing</span>
                <div className="flex space-x-1">
                  <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="input-area p-4 border-t border-gray-200 bg-white">
        <div className="flex items-end space-x-3">
          <div className="flex-1">
            <input
              ref={inputRef}
              type="text"
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                !isConnected
                  ? "Connecting..."
                  : !selectedPersona
                  ? "Select an assistant first..."
                  : "Ask me anything or give me commands..."
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              disabled={!isConnected || isTyping || !selectedPersona}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!currentMessage.trim() || !isConnected || isTyping || !selectedPersona}
            className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Quick action buttons */}
        {isConnected && selectedPersona && (
          <div className="flex items-center space-x-2 mt-3">
            <button
              onClick={() => setCurrentMessage("Hello! How are you today?")}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
              disabled={isTyping}
            >
              Say hello
            </button>
            <button
              onClick={() => setCurrentMessage("Move to the kitchen")}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
              disabled={isTyping}
            >
              Move to kitchen
            </button>
            <button
              onClick={() => setCurrentMessage("Turn on the lamp")}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
              disabled={isTyping}
            >
              Turn on lamp
            </button>
            <button
              onClick={() => setCurrentMessage("/idle")}
              className="px-3 py-1 text-xs bg-purple-100 text-purple-700 rounded-full hover:bg-purple-200"
              disabled={isTyping}
            >
              /idle mode
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatContainer;