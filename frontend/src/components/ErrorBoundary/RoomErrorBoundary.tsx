import React from 'react';
import { ErrorBoundary } from './ErrorBoundary';

interface RoomErrorBoundaryProps {
  children: React.ReactNode;
  onResetRoom?: () => void;
}

/**
 * Error boundary specifically for room/grid-related errors
 * Provides room-specific error recovery options
 */
export const RoomErrorBoundary: React.FC<RoomErrorBoundaryProps> = ({
  children,
  onResetRoom
}) => {
  const handleError = (error: Error) => {
    console.error('Room Error caught:', error);

    // Log room-specific error context
    if ((window as any).gtag) {
      (window as any).gtag('event', 'exception', {
        description: `Room error: ${error.toString()}`,
        fatal: false,
      });
    }
  };

  const fallbackUI = (
    <div className="room-error-boundary bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
      <div className="text-purple-800 mb-3">
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
            d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2 2v0zM3 7l9-4 9 4v0"
          />
        </svg>
        <h3 className="font-medium">Room Display Error</h3>
      </div>

      <p className="text-purple-700 text-sm mb-4">
        There was an issue rendering the room environment. This might be due to corrupted room data or a display error.
      </p>

      <div className="flex gap-2 justify-center">
        {onResetRoom && (
          <button
            onClick={onResetRoom}
            className="px-4 py-2 bg-purple-600 text-white text-sm rounded-md hover:bg-purple-700 transition-colors"
          >
            Reset Room
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

export default RoomErrorBoundary;