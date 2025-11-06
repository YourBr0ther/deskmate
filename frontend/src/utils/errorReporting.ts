/**
 * Error reporting and logging utilities for frontend
 */

export interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  sessionId?: string;
  timestamp?: number;
  userAgent?: string;
  url?: string;
  [key: string]: any;
}

export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  correlation_id?: string;
  details?: Record<string, any>;
}

/**
 * Enhanced error logging with context
 */
export const logError = (
  error: Error | string,
  context: ErrorContext = {}
) => {
  const timestamp = Date.now();
  const errorInfo = {
    message: typeof error === 'string' ? error : error.message,
    stack: typeof error === 'string' ? undefined : error.stack,
    timestamp,
    url: window.location.href,
    userAgent: navigator.userAgent,
    ...context,
  };

  // Console logging with structured data
  console.error('Frontend Error:', errorInfo);

  // Send to analytics if available
  if ((window as any).gtag) {
    (window as any).gtag('event', 'exception', {
      description: errorInfo.message,
      fatal: false,
      custom_parameters: {
        component: context.component,
        action: context.action,
        timestamp,
      },
    });
  }

  // Could also send to external error tracking service here
  // e.g., Sentry, LogRocket, etc.
};

/**
 * Log API errors with additional context
 */
export const logApiError = (
  error: ApiError,
  context: ErrorContext = {}
) => {
  logError(
    `API Error: ${error.message}`,
    {
      ...context,
      apiErrorCode: error.code,
      apiStatus: error.status,
      correlationId: error.correlation_id,
      apiDetails: error.details,
    }
  );
};

/**
 * Create a standardized error object from API response
 */
export const createApiError = (response: any): ApiError => {
  if (response?.error) {
    return {
      message: response.error.message || response.error,
      code: response.error.code,
      status: response.status,
      correlation_id: response.correlation_id,
      details: response.error.details,
    };
  }

  if (response?.message) {
    return {
      message: response.message,
      status: response.status,
    };
  }

  return {
    message: 'Unknown API error',
    status: response?.status || 500,
  };
};

/**
 * Check if an error is a network error
 */
export const isNetworkError = (error: any): boolean => {
  return (
    error?.message?.includes('fetch') ||
    error?.message?.includes('network') ||
    error?.name === 'NetworkError' ||
    error?.code === 'NETWORK_ERROR'
  );
};

/**
 * Check if an error is a timeout error
 */
export const isTimeoutError = (error: any): boolean => {
  return (
    error?.message?.includes('timeout') ||
    error?.name === 'TimeoutError' ||
    error?.code === 'TIMEOUT_ERROR'
  );
};

/**
 * Get user-friendly error message
 */
export const getUserFriendlyErrorMessage = (error: any): string => {
  if (isNetworkError(error)) {
    return 'Network connection issue. Please check your internet connection.';
  }

  if (isTimeoutError(error)) {
    return 'Request timed out. Please try again.';
  }

  if (error?.message) {
    return error.message;
  }

  return 'An unexpected error occurred. Please try again.';
};

/**
 * Error retry utility with exponential backoff
 */
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> => {
  let lastError: Error | undefined;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (attempt === maxRetries) {
        break;
      }

      // Exponential backoff with jitter
      const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));

      logError(
        `Retry attempt ${attempt + 1}/${maxRetries} failed: ${lastError.message}`,
        { action: 'retry_attempt', attempt: attempt + 1, maxRetries }
      );
    }
  }

  if (lastError) {
    logError(
      `All retry attempts failed: ${lastError.message}`,
      { action: 'retry_failed', maxRetries }
    );

    throw lastError;
  }

  throw new Error('Retry failed without capturing error');
};