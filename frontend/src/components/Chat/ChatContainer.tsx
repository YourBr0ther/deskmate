/**
 * Chat container component for desktop and tablet layouts.
 *
 * Provides a persistent chat interface for larger screens with
 * full messaging functionality and assistant interaction.
 */

import React, { useState, useRef, useEffect } from 'react';
import { useDeviceDetection } from '../../hooks/useDeviceDetection';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  type?: 'text' | 'action' | 'system';
}

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
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hello! I'm your DeskMate assistant. I can help you navigate the room, interact with objects, and answer questions. What would you like to do?",
      sender: 'assistant',
      timestamp: new Date(),
      type: 'text'
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [assistantMood, setAssistantMood] = useState('happy');
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesRef = useRef<HTMLDivElement>(null);

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
      timestamp: new Date(),
      type: 'text'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate assistant response with more variety
    setTimeout(() => {
      const response = generateAssistantResponse(userMessage.content);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.content,
        sender: 'assistant',
        timestamp: new Date(),
        type: response.type
      };

      setMessages(prev => [...prev, assistantMessage]);
      setAssistantMood(response.mood);
      setIsTyping(false);
    }, Math.random() * 1500 + 500); // Variable response time
  };

  // Enhanced response generator
  const generateAssistantResponse = (userMessage: string): {
    content: string;
    type: 'text' | 'action' | 'system';
    mood: string;
  } => {
    const lowerMessage = userMessage.toLowerCase();

    // Movement commands
    if (lowerMessage.includes('move') || lowerMessage.includes('go to')) {
      return {
        content: "I'd be happy to move! Just click on the floor plan where you'd like me to go, and I'll pathfind my way there.",
        type: 'action',
        mood: 'excited'
      };
    }

    // Object interaction
    if (lowerMessage.includes('lamp') || lowerMessage.includes('light')) {
      return {
        content: "I can help with the lamps! Click on any lamp in the room and I'll turn it on or off for you. I can also adjust brightness if it's a smart lamp.",
        type: 'action',
        mood: 'helpful'
      };
    }

    if (lowerMessage.includes('sit') || lowerMessage.includes('chair') || lowerMessage.includes('sofa')) {
      return {
        content: "Sure! I can sit on the sofa, chairs, or bed. Just click on the furniture you'd like me to sit on. It's quite comfortable!",
        type: 'action',
        mood: 'content'
      };
    }

    // Room navigation
    if (lowerMessage.includes('room') || lowerMessage.includes('kitchen') || lowerMessage.includes('bedroom')) {
      return {
        content: "I can move between rooms through the doorways. Click on a doorway or use the room selector at the top to navigate. Each room has different objects to interact with!",
        type: 'action',
        mood: 'enthusiastic'
      };
    }

    // Information requests
    if (lowerMessage.includes('what can you do') || lowerMessage.includes('help')) {
      return {
        content: "I can move around the room, interact with objects like lamps and furniture, sit on chairs, and chat with you! Try clicking on objects or empty spaces to see what I can do. I'm also learning about your preferences over time.",
        type: 'text',
        mood: 'informative'
      };
    }

    if (lowerMessage.includes('weather') || lowerMessage.includes('time')) {
      return {
        content: `It's currently ${new Date().toLocaleTimeString()} and I can see the room lighting is nice right now. I don't have access to outside weather, but the room feels comfortable!`,
        type: 'text',
        mood: 'observant'
      };
    }

    // Friendly responses
    if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
      const greetings = [
        "Hello! Great to see you! How can I help you explore the room today?",
        "Hi there! I'm excited to assist you. What would you like to do?",
        "Hey! Welcome back! Ready for some room exploration?"
      ];
      return {
        content: greetings[Math.floor(Math.random() * greetings.length)],
        type: 'text',
        mood: 'happy'
      };
    }

    if (lowerMessage.includes('thank') || lowerMessage.includes('thanks')) {
      return {
        content: "You're welcome! I'm always happy to help. Is there anything else you'd like to explore or any objects you'd like me to interact with?",
        type: 'text',
        mood: 'pleased'
      };
    }

    // Default responses
    const defaultResponses = [
      "That's interesting! I'm still learning about everything in this room. Would you like me to show you what I can do with the objects here?",
      "I understand! Let me know if you'd like me to move somewhere or interact with any furniture. I'm here to help!",
      "Thanks for letting me know! I'm always learning from our conversations. Want to explore the room together?",
      "I appreciate you sharing that with me! Is there anything specific you'd like me to help you with in the room?"
    ];

    return {
      content: defaultResponses[Math.floor(Math.random() * defaultResponses.length)],
      type: 'text',
      mood: 'curious'
    };
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
    setMessages([{
      id: 'welcome',
      content: "Chat cleared! How can I help you today?",
      sender: 'assistant',
      timestamp: new Date(),
      type: 'system'
    }]);
  };

  // Get assistant emoji based on mood
  const getAssistantEmoji = (mood: string) => {
    const moodEmojis: Record<string, string> = {
      happy: '😊',
      excited: '🤩',
      helpful: '🤗',
      content: '😌',
      enthusiastic: '🎉',
      informative: '🤓',
      observant: '👀',
      pleased: '😄',
      curious: '🤔'
    };
    return moodEmojis[mood] || '😊';
  };

  return (
    <div className={`chat-container flex flex-col h-full bg-white ${className}`} style={style}>
      {/* Assistant Status Bar */}
      <div className="assistant-status flex items-center justify-between p-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            <span className="text-white text-sm">{getAssistantEmoji(assistantMood)}</span>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-800">DeskMate Assistant</p>
            <p className="text-xs text-gray-500 capitalize">Feeling {assistantMood}</p>
          </div>
        </div>

        {/* Chat controls */}
        <div className="flex items-center space-x-1">
          <button
            onClick={handleClearChat}
            className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded"
            title="Clear chat"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414L9.586 12l-3.293 3.293a1 1 0 101.414 1.414L10 13.414l2.293 2.293a1 1 0 001.414-1.414L11.414 12l2.293-2.293z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div
        ref={messagesRef}
        className="messages-area flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2 rounded-lg ${
                message.sender === 'user'
                  ? 'bg-blue-500 text-white rounded-br-sm'
                  : message.type === 'system'
                  ? 'bg-yellow-100 text-yellow-800 rounded-bl-sm'
                  : message.type === 'action'
                  ? 'bg-green-100 text-green-800 rounded-bl-sm'
                  : 'bg-gray-100 text-gray-800 rounded-bl-sm'
              }`}
            >
              <p className="text-sm leading-relaxed">{message.content}</p>
              <p className={`text-xs mt-1 ${
                message.sender === 'user' ? 'text-blue-100' : 'text-gray-500'
              }`}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
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
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything or give me commands..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              disabled={isTyping}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Quick action buttons */}
        <div className="flex items-center space-x-2 mt-3">
          <button
            onClick={() => setInputValue("Move to the kitchen")}
            className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
          >
            Move to kitchen
          </button>
          <button
            onClick={() => setInputValue("Turn on the lamp")}
            className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
          >
            Turn on lamp
          </button>
          <button
            onClick={() => setInputValue("Sit on the sofa")}
            className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
          >
            Sit on sofa
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatContainer;