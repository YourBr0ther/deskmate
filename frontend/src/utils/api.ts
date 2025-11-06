/**
 * Centralized API utilities with standardized error handling
 */

import { createApiError, logApiError } from './errorReporting';

const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? '/api'
  : 'http://localhost:8000';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  correlationId?: string;
}

/**
 * Enhanced fetch wrapper with error handling
 */
export const apiRequest = async <T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> => {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, defaultOptions);
    const responseData = await response.json();

    if (response.ok) {
      return {
        success: true,
        data: responseData,
        correlationId: responseData.correlation_id,
      };
    } else {
      const apiError = createApiError(responseData);

      // Log API error
      logApiError(apiError, {
        component: 'api',
        action: 'api_request',
        endpoint,
        method: options.method || 'GET',
      });

      return {
        success: false,
        error: apiError.message,
        correlationId: responseData.correlation_id,
      };
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Network error';

    // Log network error
    logApiError(
      { message: errorMessage },
      {
        component: 'api',
        action: 'api_request',
        endpoint,
        method: options.method || 'GET',
      }
    );

    return {
      success: false,
      error: errorMessage,
    };
  }
};

/**
 * Specific API methods
 */
export const api = {
  // Room and Object APIs
  async getObjects(): Promise<ApiResponse> {
    return apiRequest('/room/objects');
  },

  async moveObject(objectId: string, position: { x: number; y: number }): Promise<ApiResponse> {
    return apiRequest(`/room/objects/${objectId}/move`, {
      method: 'POST',
      body: JSON.stringify(position),
    });
  },

  async setObjectState(objectId: string, key: string, value: string): Promise<ApiResponse> {
    return apiRequest(`/room/objects/${objectId}/state`, {
      method: 'POST',
      body: JSON.stringify({ [key]: value }),
    });
  },

  async getObjectStates(objectId: string): Promise<ApiResponse> {
    return apiRequest(`/room/objects/${objectId}/state`);
  },

  // Assistant APIs
  async getAssistantState(): Promise<ApiResponse> {
    return apiRequest('/assistant/state');
  },

  async moveAssistant(x: number, y: number): Promise<ApiResponse> {
    return apiRequest('/assistant/move', {
      method: 'POST',
      body: JSON.stringify({ x, y }),
    });
  },

  async sitOnFurniture(furnitureId: string): Promise<ApiResponse> {
    return apiRequest('/assistant/sit', {
      method: 'POST',
      body: JSON.stringify({ furniture_id: furnitureId }),
    });
  },

  // Storage APIs
  async getStorageItems(): Promise<ApiResponse> {
    return apiRequest('/room/storage/items');
  },

  async addToStorage(itemData: any): Promise<ApiResponse> {
    return apiRequest('/room/storage/items', {
      method: 'POST',
      body: JSON.stringify(itemData),
    });
  },

  async placeFromStorage(itemId: string, position: { x: number; y: number }): Promise<ApiResponse> {
    return apiRequest(`/room/storage/items/${itemId}/place`, {
      method: 'POST',
      body: JSON.stringify(position),
    });
  },

  async moveObjectToStorage(objectId: string): Promise<ApiResponse> {
    return apiRequest(`/room/objects/${objectId}/store`, {
      method: 'POST',
    });
  },
};

export default api;