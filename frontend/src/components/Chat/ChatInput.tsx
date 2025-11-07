/**
 * Chat input component for sending messages
 */

import React, { useState, KeyboardEvent } from 'react';

import { useChatStore } from '../../stores/chatStore';

const ChatInput: React.FC = () => {
  const {
    currentMessage,
    setCurrentMessage,
    sendMessage,
    isConnected,
    isTyping
  } = useChatStore();

  const [isComposing, setIsComposing] = useState(false);

  const handleSend = () => {
    if (currentMessage.trim() && isConnected && !isTyping) {
      sendMessage(currentMessage.trim());
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSend();
    }
  };

  const isDisabled = !isConnected || isTyping || !currentMessage.trim();

  return (
    <div className="p-4">
      <div className="flex space-x-3">
        {/* Text Input */}
        <div className="flex-1">
          <textarea
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            onCompositionStart={() => setIsComposing(true)}
            onCompositionEnd={() => setIsComposing(false)}
            placeholder={
              !isConnected
                ? "Connecting..."
                : isTyping
                ? "Assistant is responding..."
                : "Type your message, /create [item], or /idle... (Shift+Enter for new line)"
            }
            disabled={!isConnected}
            className="w-full resize-none bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={1}
            style={{
              minHeight: '44px',
              maxHeight: '120px'
            }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = Math.min(target.scrollHeight, 120) + 'px';
            }}
          />
        </div>

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={isDisabled}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            isDisabled
              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500'
          }`}
        >
          {isTyping ? (
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
              <span>Wait</span>
            </div>
          ) : (
            'Send'
          )}
        </button>
      </div>

      {/* Status indicators */}
      <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
        <div className="flex items-center space-x-4">
          {!isConnected && (
            <span className="text-red-400">• Disconnected</span>
          )}
          {isConnected && !isTyping && (
            <span className="text-green-400">• Connected</span>
          )}
          {isTyping && (
            <span className="text-yellow-400">• Assistant is typing...</span>
          )}
        </div>

        <div className="text-gray-500">
          {currentMessage.length > 0 && (
            <span>{currentMessage.length} characters</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInput;