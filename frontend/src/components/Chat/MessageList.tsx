/**
 * Message list component for displaying chat history
 */

import React from 'react';

import { useChatStore, ChatMessage } from '../../stores/chatStore';
import { useSettingsStore } from '../../stores/settingsStore';

const MessageBubble: React.FC<{ message: ChatMessage }> = ({ message }) => {
  const { chat } = useSettingsStore();
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="px-4 py-2">
        <div className="text-center text-sm text-gray-400 bg-gray-800 rounded px-3 py-1 max-w-md mx-auto">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`px-4 py-2 ${isUser ? 'text-right' : 'text-left'}`}>
      <div className={`inline-block max-w-[80%] rounded-lg px-4 py-2 ${
        isUser
          ? 'bg-blue-600 text-white'
          : 'bg-gray-700 text-white'
      }`}>
        <div className={`whitespace-pre-wrap break-words ${
          chat.fontSize === 'small' ? 'text-sm' :
          chat.fontSize === 'large' ? 'text-lg' : 'text-base'
        }`}>
          {message.content || (message.isStreaming ? '...' : '')}
        </div>

        {/* Message metadata */}
        {(chat.showTimestamps || message.model || message.isStreaming) && (
          <div className={`text-xs mt-1 opacity-70 ${
            isUser ? 'text-blue-100' : 'text-gray-400'
          }`}>
            {chat.showTimestamps && new Date(message.timestamp).toLocaleTimeString()}
            {message.model && !isUser && (
              <span className="ml-2">• {message.model}</span>
            )}
            {message.isStreaming && (
              <span className="ml-2 animate-pulse">• streaming</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const MessageList: React.FC = () => {
  const { messages, isTyping } = useChatStore();
  const { chat } = useSettingsStore();

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400">
        <div className="text-center">
          <div className="text-6xl mb-4">🤖</div>
          <h3 className="text-lg font-medium mb-2">Welcome to DeskMate!</h3>
          <p className="text-sm">
            Start a conversation with your AI companion.
            <br />
            I can chat, move around the room, and interact with objects.
          </p>
          <div className="mt-4 text-xs text-gray-500">
            Try asking me to:
            <ul className="mt-2 space-y-1">
              <li>• "Tell me about yourself"</li>
              <li>• "Move to the desk"</li>
              <li>• "What can you see in the room?"</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {/* Typing indicator */}
      {isTyping && chat.enableTypingIndicator && (
        <div className="px-4 py-2 text-left">
          <div className="inline-block max-w-[80%] rounded-lg px-4 py-2 bg-gray-700 text-white">
            <div className="flex items-center space-x-2">
              <span className="text-sm">Assistant is typing</span>
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
  );
};

export default MessageList;