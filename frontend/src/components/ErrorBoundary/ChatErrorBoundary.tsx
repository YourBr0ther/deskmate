import React from 'react';

import { ErrorBoundary } from './ErrorBoundary';

interface ChatErrorBoundaryProps {
  children: React.ReactNode;
  onClearChat?: () => void;
}

/**
 * Error boundary specifically for chat-related errors
 * Provides chat-specific error recovery options
 */
export const ChatErrorBoundary: React.FC<ChatErrorBoundaryProps> = ({
  children,
  onClearChat
}) => {
  const handleError = (error: Error) => {
    console.error('Chat Error caught:', error);

    // Log chat-specific error context
    if ((window as any).gtag) {
      (window as any).gtag('event', 'exception', {
        description: `Chat error: ${error.toString()}`,
        fatal: false,
      });
    }
  };

  const fallbackUI = (
    <div className="chat-error-boundary bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
      <div className="text-blue-800 mb-3">
        <svg
          className="w-8 h-8 mx-auto mb-2"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        <h3 className="font-medium">Chat System Error</h3>
      </div>

      <p className="text-blue-700 text-sm mb-4">
        There was an issue with the chat system. You can try clearing the chat history or refreshing the page.
      </p>

      <div className="flex gap-2 justify-center">
        {onClearChat && (
          <button
            onClick={onClearChat}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
          >
            Clear Chat
          </button>
        )}
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700 transition-colors"
        >
          Refresh Page
        </button>
      </div>
    </div>
  );

  return (
    <ErrorBoundary fallback={fallbackUI} onError={handleError}>
      {children}
    </ErrorBoundary>
  );
};

export default ChatErrorBoundary;