/**
 * Standardized error handling utilities for Zustand stores
 */

import { logError, logApiError, createApiError, isNetworkError, isTimeoutError } from './errorReporting';

export interface StoreErrorState {
  isLoading: boolean;
  error: string | null;
  lastErrorTimestamp: number | null;
}

export const createInitialErrorState = (): StoreErrorState => ({
  isLoading: false,
  error: null,
  lastErrorTimestamp: null,
});

/**
 * Generic error handler for store operations
 */
export const handleStoreError = (
  error: any,
  context: {
    storeName: string;
    operation: string;
    setState: (update: Partial<StoreErrorState>) => void;
  }
): string => {
  const timestamp = Date.now();
  const errorMessage = error?.message || 'An unexpected error occurred';

  // Log the error with context
  logError(error, {
    component: 'store',
    store: context.storeName,
    action: context.operation,
  });

  // Update store error state
  context.setState({
    isLoading: false,
    error: errorMessage,
    lastErrorTimestamp: timestamp,
  });

  return errorMessage;
};

/**
 * API error handler for store operations
 */
export const handleApiError = async (
  response: Response,
  context: {
    storeName: string;
    operation: string;
    setState: (update: Partial<StoreErrorState>) => void;
  }
): Promise<string> => {
  let apiError;

  try {
    const responseData = await response.json();
    apiError = createApiError(responseData);
  } catch {
    apiError = createApiError({
      message: `HTTP ${response.status}: ${response.statusText}`,
      status: response.status,
    });
  }

  const timestamp = Date.now();

  // Log the API error
  logApiError(apiError, {
    component: 'store',
    store: context.storeName,
    action: context.operation,
    url: response.url,
  });

  // Update store error state
  context.setState({
    isLoading: false,
    error: apiError.message,
    lastErrorTimestamp: timestamp,
  });

  return apiError.message;
};

/**
 * Wrapper for async store operations with standardized error handling
 */
export const withErrorHandling = <T>(
  operation: () => Promise<T>,
  context: {
    storeName: string;
    operation: string;
    setState: (update: Partial<StoreErrorState>) => void;
    onSuccess?: (result: T) => void;
    onError?: (error: string) => void;
  }
): Promise<T | null> => {
  // Set loading state
  context.setState({
    isLoading: true,
    error: null,
  });

  return operation()
    .then((result) => {
      // Clear loading and error state on success
      context.setState({
        isLoading: false,
        error: null,
      });

      if (context.onSuccess) {
        context.onSuccess(result);
      }

      return result;
    })
    .catch((error) => {
      const errorMessage = handleStoreError(error, context);

      if (context.onError) {
        context.onError(errorMessage);
      }

      return null;
    });
};

/**
 * Create a standardized API call handler
 */
export const createApiHandler = (
  storeName: string,
  setState: (update: Partial<StoreErrorState>) => void
) => {
  return async <T>(
    operation: string,
    apiCall: () => Promise<Response>,
    onSuccess: (response: Response) => Promise<T>
  ): Promise<T | null> => {
    return withErrorHandling(
      async () => {
        const response = await apiCall();

        if (!response.ok) {
          const errorMessage = await handleApiError(response, {
            storeName,
            operation,
            setState,
          });
          throw new Error(errorMessage);
        }

        return await onSuccess(response);
      },
      {
        storeName,
        operation,
        setState,
      }
    );
  };
};

/**
 * Get user-friendly error message for store errors
 */
export const getStoreErrorMessage = (error: any): string => {
  if (isNetworkError(error)) {
    return 'Network connection issue. Please check your internet and try again.';
  }

  if (isTimeoutError(error)) {
    return 'Request timed out. Please try again.';
  }

  if (typeof error === 'string') {
    return error;
  }

  if (error?.message) {
    return error.message;
  }

  return 'An unexpected error occurred. Please try again.';
};

/**
 * Clear error state in store
 */
export const clearStoreError = (setState: (update: Partial<StoreErrorState>) => void) => {
  setState({
    error: null,
    lastErrorTimestamp: null,
  });
};

/**
 * Check if an error should be retried
 */
export const shouldRetryError = (error: any): boolean => {
  return isNetworkError(error) || isTimeoutError(error);
};