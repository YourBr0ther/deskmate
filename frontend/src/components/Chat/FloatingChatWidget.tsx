/**
 * Floating chat widget for mobile devices.
 *
 * Provides a minimizable chat interface that can switch between three states:
 * - Minimized: Small floating icon in corner
 * - Partial: Quick chat with assistant avatar and simple input
 * - Expanded: Full-screen chat overlay with complete functionality
 */

import React, { useState, useRef, useEffect } from 'react';
import { useDeviceDetection } from '../../hooks/useDeviceDetection';

export type ChatWidgetState = 'minimized' | 'partial' | 'expanded';

interface FloatingChatWidgetProps {
  state: ChatWidgetState;
  onStateChange: (newState: ChatWidgetState) => void;
  className?: string;
}

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

/**
 * Mobile floating chat widget component.
 */
export const FloatingChatWidget: React.FC<FloatingChatWidgetProps> = ({
  state,
  onStateChange,
  className = ''
}) => {
  const deviceInfo = useDeviceDetection();
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hi! I'm your DeskMate assistant. Tap objects in the room to interact with them, or ask me anything!",
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesRef = useRef<HTMLDivElement>(null);

  // Auto-focus input when expanding
  useEffect(() => {
    if (state === 'expanded' && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [state]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages]);

  // Handle sending a message
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate assistant response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: getAssistantResponse(userMessage.content),
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 1000);
  };

  // Simple response generator (in real app, this would call the AI API)
  const getAssistantResponse = (userMessage: string): string => {
    const lowerMessage = userMessage.toLowerCase();

    if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
      return "Hello! How can I help you today? You can ask me to move around the room or interact with objects.";
    }
    if (lowerMessage.includes('move') || lowerMessage.includes('go')) {
      return "I'd be happy to move around! Just tap where you'd like me to go on the floor plan.";
    }
    if (lowerMessage.includes('what') && lowerMessage.includes('do')) {
      return "I can move around the room, interact with objects like lamps and furniture, and chat with you about anything! Try tapping on objects to see what I can do with them.";
    }
    return "Thanks for your message! I'm here to help you explore and interact with your virtual space. What would you like to do?";
  };

  // Handle input key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Get assistant mood emoji
  const getAssistantEmoji = () => {
    const emojis = ['😊', '🤔', '😄', '🙂', '😌'];
    return emojis[Math.floor(Math.random() * emojis.length)];
  };

  // Render minimized state (floating icon)
  const renderMinimized = () => (
    <div
      className={`fixed bottom-4 right-4 z-50 ${className}`}
      onClick={() => onStateChange('partial')}
    >
      <div className="w-16 h-16 bg-blue-500 rounded-full shadow-lg flex items-center justify-center cursor-pointer transform transition-all duration-200 hover:scale-105 active:scale-95">
        <div className="relative">
          {/* Chat icon */}
          <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
          </svg>

          {/* Assistant mood indicator */}
          <div className="absolute -top-1 -right-1 w-6 h-6 bg-white rounded-full flex items-center justify-center text-sm">
            {getAssistantEmoji()}
          </div>

          {/* Notification dot */}
          {messages.length > 1 && (
            <div className="absolute -top-2 -left-2 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-bold">!</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Render partial state (quick chat)
  const renderPartial = () => (
    <div className={`fixed bottom-4 right-4 z-50 ${className}`}>
      <div className="bg-white rounded-2xl shadow-xl border border-gray-200 w-80 max-w-[90vw]">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white text-lg">{getAssistantEmoji()}</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">Assistant</h3>
              <p className="text-xs text-gray-500">Online</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => onStateChange('expanded')}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
              </svg>
            </button>
            <button
              onClick={() => onStateChange('minimized')}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>

        {/* Quick message preview */}
        <div className="p-4 max-h-32 overflow-y-auto">
          <div className="text-sm text-gray-600">
            {messages[messages.length - 1]?.content || 'Start a conversation...'}
          </div>
        </div>

        {/* Quick input */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-full text-sm focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              className="p-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Render expanded state (full overlay)
  const renderExpanded = () => (
    <div className={`fixed inset-0 z-50 ${className}`}>
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-30"
        onClick={() => onStateChange('minimized')}
      />

      {/* Chat overlay */}
      <div className="absolute inset-0 flex flex-col bg-white">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white text-lg">{getAssistantEmoji()}</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">DeskMate Assistant</h3>
              <p className="text-sm text-gray-500">Always here to help</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => onStateChange('partial')}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" />
              </svg>
            </button>
            <button
              onClick={() => onStateChange('minimized')}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>

        {/* Messages */}
        <div
          ref={messagesRef}
          className="flex-1 overflow-y-auto p-4 space-y-4"
          style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
        >
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs px-4 py-2 rounded-2xl ${
                  message.sender === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                <p className="text-sm">{message.content}</p>
                <p className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-gray-100 px-4 py-2 rounded-2xl">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="flex items-end space-x-3">
            <div className="flex-1">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything or give me commands..."
                className="w-full px-4 py-3 border border-gray-300 rounded-2xl text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              className="p-3 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Render appropriate state
  switch (state) {
    case 'minimized':
      return renderMinimized();
    case 'partial':
      return renderPartial();
    case 'expanded':
      return renderExpanded();
    default:
      return null;
  }
};

export default FloatingChatWidget;