/**
 * API mock utilities for testing.
 *
 * Provides helpers for mocking fetch requests and API responses.
 */

// ============================================================================
// Types
// ============================================================================

export interface MockApiResponse<T = unknown> {
  data: T;
  status?: number;
  headers?: Record<string, string>;
  delay?: number;
}

export interface MockApiError {
  message: string;
  status: number;
  code?: string;
}

// ============================================================================
// Mock Fetch Helper
// ============================================================================

type FetchMock = jest.Mock<Promise<Response>>;

/**
 * Get the global fetch mock.
 */
export function getFetchMock(): FetchMock {
  return global.fetch as FetchMock;
}

/**
 * Set up a successful API response.
 */
export function mockApiSuccess<T>(
  data: T,
  options: Partial<MockApiResponse<T>> = {}
): void {
  const { status = 200, headers = {}, delay = 0 } = options;

  const response = {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: new Headers({
      'Content-Type': 'application/json',
      ...headers,
    }),
    json: async () => data,
    text: async () => JSON.stringify(data),
    clone: function () {
      return this;
    },
  };

  if (delay > 0) {
    getFetchMock().mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve(response as Response), delay)
        )
    );
  } else {
    getFetchMock().mockResolvedValueOnce(response as Response);
  }
}

/**
 * Set up an API error response.
 */
export function mockApiError(error: MockApiError): void {
  const { message, status, code } = error;

  getFetchMock().mockResolvedValueOnce({
    ok: false,
    status,
    statusText: message,
    headers: new Headers({ 'Content-Type': 'application/json' }),
    json: async () => ({ error: message, code }),
    text: async () => JSON.stringify({ error: message, code }),
  } as Response);
}

/**
 * Set up a network error (fetch throws).
 */
export function mockNetworkError(message = 'Network error'): void {
  getFetchMock().mockRejectedValueOnce(new Error(message));
}

/**
 * Clear all fetch mock implementations.
 */
export function clearApiMocks(): void {
  getFetchMock().mockReset();
}

// ============================================================================
// API Response Factories
// ============================================================================

export const apiResponses = {
  health: {
    status: 'ok',
    version: '1.0.0',
    services: {
      database: 'connected',
      qdrant: 'connected',
      llm: 'available',
    },
  },

  models: {
    models: [
      { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'nano_gpt' },
      { id: 'llama3:latest', name: 'Llama 3', provider: 'ollama' },
    ],
    current: 'llama3:latest',
  },

  assistantState: {
    id: 1,
    position: { x: 5, y: 5 },
    room: 'living_room',
    mood: 'neutral',
    expression: 'default',
    energy: 1.0,
    isIdle: false,
    holding: null,
  },

  roomObjects: [
    {
      id: 1,
      name: 'desk',
      type: 'furniture',
      position: { x: 10, y: 8 },
      size: { width: 2, height: 1 },
      interactive: true,
      movable: false,
    },
    {
      id: 2,
      name: 'chair',
      type: 'furniture',
      position: { x: 12, y: 8 },
      size: { width: 1, height: 1 },
      interactive: true,
      movable: false,
      sittable: true,
    },
    {
      id: 3,
      name: 'lamp',
      type: 'decoration',
      position: { x: 10, y: 7 },
      size: { width: 1, height: 1 },
      interactive: true,
      movable: false,
      state: { power: false },
    },
  ],

  personas: [
    {
      name: 'Alice',
      description: 'A friendly AI companion',
      personality: 'Cheerful and helpful',
      expressions: ['default', 'happy', 'sad', 'thinking'],
    },
    {
      name: 'Bob',
      description: 'A knowledgeable assistant',
      personality: 'Calm and informative',
      expressions: ['default', 'happy', 'confused'],
    },
  ],

  chatHistory: [
    { id: '1', role: 'user', content: 'Hello!', timestamp: Date.now() - 60000 },
    {
      id: '2',
      role: 'assistant',
      content: 'Hi there! How can I help you today?',
      timestamp: Date.now() - 55000,
    },
  ],

  memoryStats: {
    totalMemories: 42,
    recentMemories: 10,
    oldestMemory: '2024-01-01T00:00:00Z',
    newestMemory: new Date().toISOString(),
  },

  brainCouncilResponse: {
    council_response: {
      personality: 'Character maintains cheerful demeanor',
      memory: 'User previously asked about the weather',
      spatial: 'Assistant is at position (5, 5), near the desk',
      action: 'Suggest moving to the window',
      validation: 'Action is valid and possible',
    },
    final_response: "I'd be happy to help with that!",
    suggested_actions: [
      { type: 'move', target: { x: 10, y: 8 } },
      { type: 'expression', value: 'happy' },
    ],
  },
};

// ============================================================================
// Endpoint Matchers
// ============================================================================

/**
 * Check if fetch was called with a specific endpoint.
 */
export function wasEndpointCalled(endpoint: string): boolean {
  const calls = getFetchMock().mock.calls;
  return calls.some((call) => {
    const url = call[0] as string;
    return url.includes(endpoint);
  });
}

/**
 * Get all calls to a specific endpoint.
 */
export function getEndpointCalls(endpoint: string): unknown[] {
  const calls = getFetchMock().mock.calls;
  return calls.filter((call) => {
    const url = call[0] as string;
    return url.includes(endpoint);
  });
}

/**
 * Get the request body from the last fetch call.
 */
export function getLastRequestBody<T = unknown>(): T | null {
  const calls = getFetchMock().mock.calls;
  if (calls.length === 0) return null;

  const lastCall = calls[calls.length - 1];
  const options = lastCall[1] as RequestInit | undefined;

  if (options?.body) {
    return JSON.parse(options.body as string) as T;
  }

  return null;
}

// ============================================================================
// Batch Mock Setup
// ============================================================================

/**
 * Set up multiple API responses at once.
 */
export function setupApiMocks(
  mocks: Array<{ endpoint: string; response: unknown; status?: number }>
): void {
  mocks.forEach(({ response, status = 200 }) => {
    mockApiSuccess(response, { status });
  });
}

/**
 * Set up common API responses for a full app test.
 */
export function setupFullAppMocks(): void {
  mockApiSuccess(apiResponses.health);
  mockApiSuccess(apiResponses.models);
  mockApiSuccess(apiResponses.assistantState);
  mockApiSuccess(apiResponses.roomObjects);
  mockApiSuccess(apiResponses.personas);
  mockApiSuccess(apiResponses.chatHistory);
}
