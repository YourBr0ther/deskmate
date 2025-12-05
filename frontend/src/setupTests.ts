/**
 * Jest test setup for DeskMate frontend.
 *
 * This file runs before each test file and sets up:
 * - Jest DOM matchers
 * - Global mocks (WebSocket, fetch, localStorage)
 * - Test utilities
 */

import '@testing-library/jest-dom';

// ============================================================================
// WebSocket Mock
// ============================================================================

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  private messageQueue: string[] = [];

  constructor(url: string) {
    this.url = url;
    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  send(data: string): void {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    this.messageQueue.push(data);
  }

  close(code?: number, reason?: string): void {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: code || 1000, reason }));
    }
  }

  // Test helper: simulate receiving a message
  simulateMessage(data: unknown): void {
    if (this.onmessage) {
      const messageData = typeof data === 'string' ? data : JSON.stringify(data);
      this.onmessage(new MessageEvent('message', { data: messageData }));
    }
  }

  // Test helper: simulate an error
  simulateError(): void {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }

  // Test helper: get sent messages
  getSentMessages(): string[] {
    return this.messageQueue;
  }

  // Test helper: clear message queue
  clearMessages(): void {
    this.messageQueue = [];
  }
}

// Replace global WebSocket
(global as unknown as { WebSocket: typeof MockWebSocket }).WebSocket = MockWebSocket;

// ============================================================================
// Fetch Mock
// ============================================================================

const mockFetch = jest.fn();
global.fetch = mockFetch;

// Helper to set up fetch responses
(global as unknown as { mockFetchResponse: (response: unknown, status?: number) => void }).mockFetchResponse = (
  response: unknown,
  status = 200
) => {
  mockFetch.mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: async () => response,
    text: async () => JSON.stringify(response),
    headers: new Headers(),
  });
};

// ============================================================================
// LocalStorage Mock
// ============================================================================

class MockLocalStorage implements Storage {
  private store: Record<string, string> = {};

  get length(): number {
    return Object.keys(this.store).length;
  }

  key(index: number): string | null {
    const keys = Object.keys(this.store);
    return keys[index] || null;
  }

  getItem(key: string): string | null {
    return this.store[key] || null;
  }

  setItem(key: string, value: string): void {
    this.store[key] = value;
  }

  removeItem(key: string): void {
    delete this.store[key];
  }

  clear(): void {
    this.store = {};
  }
}

Object.defineProperty(window, 'localStorage', {
  value: new MockLocalStorage(),
});

Object.defineProperty(window, 'sessionStorage', {
  value: new MockLocalStorage(),
});

// ============================================================================
// ResizeObserver Mock
// ============================================================================

class MockResizeObserver {
  callback: ResizeObserverCallback;

  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
  }

  observe(): void {
    // No-op for tests
  }

  unobserve(): void {
    // No-op for tests
  }

  disconnect(): void {
    // No-op for tests
  }
}

global.ResizeObserver = MockResizeObserver;

// ============================================================================
// IntersectionObserver Mock
// ============================================================================

class MockIntersectionObserver implements IntersectionObserver {
  callback: IntersectionObserverCallback;
  root: Element | Document | null = null;
  rootMargin: string = '0px';
  thresholds: ReadonlyArray<number> = [0];

  constructor(callback: IntersectionObserverCallback, _options?: IntersectionObserverInit) {
    this.callback = callback;
  }

  observe(): void {
    // No-op for tests
  }

  unobserve(): void {
    // No-op for tests
  }

  disconnect(): void {
    // No-op for tests
  }

  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}

global.IntersectionObserver = MockIntersectionObserver;

// ============================================================================
// matchMedia Mock
// ============================================================================

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// ============================================================================
// requestAnimationFrame Mock
// ============================================================================

global.requestAnimationFrame = (callback: FrameRequestCallback): number => {
  return setTimeout(() => callback(Date.now()), 0) as unknown as number;
};

global.cancelAnimationFrame = (id: number): void => {
  clearTimeout(id);
};

// ============================================================================
// Console Error Suppression (for expected errors)
// ============================================================================

const originalError = console.error;
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    // Suppress React act() warnings in tests
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: An update to')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// ============================================================================
// Cleanup after each test
// ============================================================================

afterEach(() => {
  // Clear all mocks
  jest.clearAllMocks();

  // Clear localStorage/sessionStorage
  window.localStorage.clear();
  window.sessionStorage.clear();

  // Reset fetch mock
  mockFetch.mockReset();
});

// ============================================================================
// Global Test Utilities
// ============================================================================

// Wait for async operations
export const waitForAsync = (ms = 0): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

// Flush all pending promises
export const flushPromises = (): Promise<void> =>
  new Promise((resolve) => setImmediate(resolve));
