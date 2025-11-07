/**
 * Error Boundary component to catch and handle React errors gracefully
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';

import { logger } from '../utils/logger';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  resetKeys?: Array<string | number>;
  resetOnPropsChange?: boolean;
  isolate?: boolean; // If true, only shows error for this component, not entire app
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: NodeJS.Timeout | null = null;
  private previousResetKeys: Array<string | number> = [];

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console in development
    logger.error('Error Boundary caught an error:', error, errorInfo);

    // Update state with error details
    this.setState(prevState => ({
      errorInfo,
      errorCount: prevState.errorCount + 1
    }));

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Auto-reset after 10 seconds if error count is low
    if (this.state.errorCount < 3) {
      this.resetTimeoutId = setTimeout(() => {
        this.resetErrorBoundary();
      }, 10000);
    }
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    const { resetKeys, resetOnPropsChange } = this.props;

    // Reset if resetKeys have changed
    if (resetKeys && prevProps.resetKeys) {
      const hasResetKeyChanged = resetKeys.some(
        (key, index) => key !== this.previousResetKeys[index]
      );
      if (hasResetKeyChanged) {
        this.resetErrorBoundary();
        this.previousResetKeys = [...resetKeys];
      }
    }

    // Reset if props have changed and resetOnPropsChange is true
    if (resetOnPropsChange && prevProps.children !== this.props.children) {
      this.resetErrorBoundary();
    }
  }

  componentWillUnmount(): void {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  resetErrorBoundary = (): void => {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
      this.resetTimeoutId = null;
    }

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render(): ReactNode {
    const { hasError, error, errorCount } = this.state;
    const { children, fallback, isolate } = this.props;

    if (hasError && error) {
      // Custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Default error UI
      const errorUI = (
        <div className={`error-boundary-fallback ${isolate ? 'error-isolated' : 'error-fullscreen'}`}>
          <div className="error-content p-8 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center mb-4">
              <svg className="w-8 h-8 text-red-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <h2 className="text-xl font-semibold text-red-800">
                {isolate ? 'Component Error' : 'Application Error'}
              </h2>
            </div>

            <p className="text-gray-700 mb-4">
              {isolate
                ? 'This component encountered an error and cannot be displayed.'
                : 'Something went wrong. The application encountered an unexpected error.'}
            </p>

            {/* Error details in development */}
            {process.env.NODE_ENV === 'development' && (
              <details className="mb-4">
                <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                  Error Details (Development Only)
                </summary>
                <div className="mt-2 p-3 bg-gray-100 rounded text-xs font-mono">
                  <div className="text-red-700 mb-2">{error.toString()}</div>
                  {this.state.errorInfo && (
                    <pre className="text-gray-600 overflow-auto max-h-40">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  )}
                </div>
              </details>
            )}

            <div className="flex items-center justify-between">
              <button
                onClick={this.resetErrorBoundary}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>

              {errorCount > 2 && (
                <p className="text-sm text-gray-600">
                  Multiple errors detected. Consider refreshing the page.
                </p>
              )}
            </div>
          </div>
        </div>
      );

      return isolate ? (
        <div className="relative">
          {errorUI}
        </div>
      ) : errorUI;
    }

    return children;
  }
}

// Higher-order component for wrapping components with error boundary
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
): React.ComponentType<P> {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
}

// Default export
export default ErrorBoundary;