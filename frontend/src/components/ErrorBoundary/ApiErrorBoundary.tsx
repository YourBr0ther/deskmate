import React from 'react';
import { ErrorBoundary } from './ErrorBoundary';

interface ApiErrorBoundaryProps {
  children: React.ReactNode;
  onRetry?: () => void;
}

/**
 * Error boundary specifically for API-related errors
 * Provides retry functionality and API-specific error messaging
 */
export const ApiErrorBoundary: React.FC<ApiErrorBoundaryProps> = ({
  children,
  onRetry
}) => {
  const handleError = (error: Error) => {
    console.error('API Error caught:', error);

    // Log to external error tracking service if available
    if ((window as any).gtag) {
      (window as any).gtag('event', 'exception', {
        description: error.toString(),
        fatal: false,
      });
    }
  };

  const fallbackUI = (
    <div className="api-error-boundary bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
      <div className="text-yellow-800 mb-3">
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
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
        <h3 className="font-medium">Network Connection Issue</h3>
      </div>

      <p className="text-yellow-700 text-sm mb-4">
        We're having trouble connecting to our servers. Please check your internet connection and try again.
      </p>

      <div className="flex gap-2 justify-center">
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-yellow-600 text-white text-sm rounded-md hover:bg-yellow-700 transition-colors"
          >
            Retry Connection
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

export default ApiErrorBoundary;