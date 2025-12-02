/**
 * Custom render function with providers for testing React components.
 *
 * Wraps components with necessary providers (Theme, etc.) and
 * provides utilities for testing with Zustand stores.
 */

import React, { ReactElement, ReactNode } from 'react';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { ThemeProvider } from '../contexts/ThemeContext';

// ============================================================================
// Provider Wrapper
// ============================================================================

interface WrapperProps {
  children: ReactNode;
}

/**
 * Default wrapper with all providers.
 */
const AllProviders: React.FC<WrapperProps> = ({ children }) => {
  return (
    <ThemeProvider>
      {children}
    </ThemeProvider>
  );
};

// ============================================================================
// Custom Render Function
// ============================================================================

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  /**
   * Initial state for stores (if needed)
   */
  initialState?: {
    chat?: Partial<ChatStoreState>;
    spatial?: Partial<SpatialStoreState>;
    persona?: Partial<PersonaStoreState>;
    settings?: Partial<SettingsStoreState>;
  };
}

// Store state types (simplified for testing)
interface ChatStoreState {
  messages: Array<{ id: string; role: string; content: string }>;
  isConnected: boolean;
  isTyping: boolean;
}

interface SpatialStoreState {
  objects: Array<{ id: number; name: string; x: number; y: number }>;
  assistantPosition: { x: number; y: number };
  currentRoom: string;
}

interface PersonaStoreState {
  currentPersona: string | null;
  personas: Array<{ name: string; description: string }>;
}

interface SettingsStoreState {
  theme: 'light' | 'dark';
  debugMode: boolean;
}

/**
 * Render with all providers and optional initial state.
 *
 * @example
 * const { getByText } = renderWithProviders(<MyComponent />);
 *
 * @example
 * const { getByText } = renderWithProviders(<MyComponent />, {
 *   initialState: {
 *     chat: { messages: [{ id: '1', role: 'user', content: 'Hello' }] }
 *   }
 * });
 */
export function renderWithProviders(
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult & { rerender: (ui: ReactElement) => void } {
  const { initialState, ...renderOptions } = options;

  // If initial state provided, set up stores before render
  if (initialState) {
    setupStores(initialState);
  }

  const result = render(ui, {
    wrapper: AllProviders,
    ...renderOptions,
  });

  return {
    ...result,
    rerender: (newUi: ReactElement) =>
      result.rerender(<AllProviders>{newUi}</AllProviders>),
  };
}

// ============================================================================
// Store Setup Utilities
// ============================================================================

/**
 * Set up Zustand stores with initial state for testing.
 */
function setupStores(initialState: CustomRenderOptions['initialState']): void {
  // This will be implemented when we create store tests
  // For now, it's a placeholder that can be extended
  if (initialState?.chat) {
    // Set chat store state
  }
  if (initialState?.spatial) {
    // Set spatial store state
  }
  if (initialState?.persona) {
    // Set persona store state
  }
  if (initialState?.settings) {
    // Set settings store state
  }
}

/**
 * Reset all stores to their default state.
 * Call this in afterEach() to ensure clean state between tests.
 */
export function resetAllStores(): void {
  // This will reset all Zustand stores
  // Implementation depends on store structure
}

// ============================================================================
// Re-export testing-library utilities
// ============================================================================

export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
