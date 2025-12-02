/**
 * Tests for Persona Store
 *
 * Tests cover:
 * - Initial state
 * - Persona list management
 * - Selected persona management
 * - Expression management
 * - Loading states
 * - Error handling
 * - API calls
 */

import { act } from '@testing-library/react';
import { usePersonaStore } from '../personaStore';

// Mock fetch
global.fetch = jest.fn();

// Mock chatStore import
jest.mock('../chatStore', () => ({
  useChatStore: {
    getState: jest.fn(() => ({
      loadChatHistory: jest.fn(),
    })),
  },
}));

const mockPersonaSummaries = [
  {
    name: 'Alice',
    description: 'A friendly AI assistant',
    tags: ['friendly', 'helpful'],
    creator: 'Test',
  },
  {
    name: 'Bob',
    description: 'A knowledgeable companion',
    tags: ['smart', 'curious'],
    creator: 'Test',
  },
];

const mockLoadedPersona = {
  persona: {
    data: {
      name: 'Alice',
      description: 'A friendly AI assistant',
      personality: 'Friendly and helpful',
      expressions: {
        default: '/path/to/default.png',
        happy: '/path/to/happy.png',
      },
      current_expression: 'default',
    },
  },
  metadata: {
    file_path: '/data/personas/alice.png',
    load_time: '2024-01-01T00:00:00Z',
  },
};

describe('PersonaStore', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset store to initial state
    usePersonaStore.setState({
      personas: [],
      selectedPersona: null,
      currentExpression: 'default',
      availableExpressions: ['default'],
      isLoading: false,
      error: null,
    });
  });

  // ========================================================================
  // Initial State Tests
  // ========================================================================

  describe('Initial State', () => {
    it('should have empty personas list', () => {
      const state = usePersonaStore.getState();
      expect(state.personas).toEqual([]);
    });

    it('should have no selected persona', () => {
      const state = usePersonaStore.getState();
      expect(state.selectedPersona).toBeNull();
    });

    it('should have default expression', () => {
      const state = usePersonaStore.getState();
      expect(state.currentExpression).toBe('default');
      expect(state.availableExpressions).toEqual(['default']);
    });

    it('should not be loading', () => {
      const state = usePersonaStore.getState();
      expect(state.isLoading).toBe(false);
    });

    it('should have no error', () => {
      const state = usePersonaStore.getState();
      expect(state.error).toBeNull();
    });
  });

  // ========================================================================
  // Basic Actions Tests
  // ========================================================================

  describe('Basic Actions', () => {
    it('should set personas', () => {
      act(() => {
        usePersonaStore.getState().setPersonas(mockPersonaSummaries);
      });

      expect(usePersonaStore.getState().personas).toEqual(mockPersonaSummaries);
    });

    it('should set selected persona', () => {
      act(() => {
        usePersonaStore.getState().setSelectedPersona(mockLoadedPersona as any);
      });

      expect(usePersonaStore.getState().selectedPersona).toEqual(mockLoadedPersona);
    });

    it('should clear selected persona', () => {
      act(() => {
        usePersonaStore.getState().setSelectedPersona(mockLoadedPersona as any);
        usePersonaStore.getState().setSelectedPersona(null);
      });

      expect(usePersonaStore.getState().selectedPersona).toBeNull();
    });

    it('should set current expression', () => {
      act(() => {
        usePersonaStore.getState().setCurrentExpression('happy');
      });

      expect(usePersonaStore.getState().currentExpression).toBe('happy');
    });

    it('should set available expressions', () => {
      act(() => {
        usePersonaStore.getState().setAvailableExpressions(['default', 'happy', 'sad']);
      });

      expect(usePersonaStore.getState().availableExpressions).toEqual([
        'default',
        'happy',
        'sad',
      ]);
    });

    it('should set loading state', () => {
      act(() => {
        usePersonaStore.getState().setLoading(true);
      });

      expect(usePersonaStore.getState().isLoading).toBe(true);
    });

    it('should set error', () => {
      act(() => {
        usePersonaStore.getState().setError('Something went wrong');
      });

      expect(usePersonaStore.getState().error).toBe('Something went wrong');
    });

    it('should clear error', () => {
      act(() => {
        usePersonaStore.getState().setError('Error');
        usePersonaStore.getState().clearError();
      });

      expect(usePersonaStore.getState().error).toBeNull();
    });
  });

  // ========================================================================
  // Load Personas Tests
  // ========================================================================

  describe('Load Personas', () => {
    it('should load personas successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPersonaSummaries,
      });

      await act(async () => {
        await usePersonaStore.getState().loadPersonas();
      });

      const state = usePersonaStore.getState();
      expect(state.personas).toEqual(mockPersonaSummaries);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should set loading state while fetching', async () => {
      let loadingDuringFetch = false;

      (global.fetch as jest.Mock).mockImplementation(async () => {
        loadingDuringFetch = usePersonaStore.getState().isLoading;
        return {
          ok: true,
          json: async () => mockPersonaSummaries,
        };
      });

      await act(async () => {
        await usePersonaStore.getState().loadPersonas();
      });

      expect(loadingDuringFetch).toBe(true);
    });

    it('should handle fetch error', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await act(async () => {
        await usePersonaStore.getState().loadPersonas();
      });

      const state = usePersonaStore.getState();
      expect(state.error).toContain('Failed to load personas');
      expect(state.isLoading).toBe(false);
    });

    it('should handle network error', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await act(async () => {
        await usePersonaStore.getState().loadPersonas();
      });

      const state = usePersonaStore.getState();
      expect(state.error).toBe('Network error');
      expect(state.isLoading).toBe(false);
    });
  });

  // ========================================================================
  // Load Persona By Name Tests
  // ========================================================================

  describe('Load Persona By Name', () => {
    it('should load persona by name successfully', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockLoadedPersona,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ messages: [], count: 0 }),
        });

      await act(async () => {
        await usePersonaStore.getState().loadPersonaByName('Alice');
      });

      const state = usePersonaStore.getState();
      expect(state.selectedPersona).toBeDefined();
      expect(state.isLoading).toBe(false);
    });

    it('should handle persona not found', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await act(async () => {
        await usePersonaStore.getState().loadPersonaByName('Unknown');
      });

      const state = usePersonaStore.getState();
      expect(state.selectedPersona).toBeNull();
      expect(state.error).toContain('Failed to load persona');
    });

    it('should clear previous persona on new load', async () => {
      // Set initial persona
      act(() => {
        usePersonaStore.getState().setSelectedPersona(mockLoadedPersona as any);
      });

      // Mock failed load
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await act(async () => {
        await usePersonaStore.getState().loadPersonaByName('Unknown');
      });

      expect(usePersonaStore.getState().selectedPersona).toBeNull();
    });

    it('should continue if conversation init fails', async () => {
      // Mock successful persona load, failed conversation init
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockLoadedPersona,
        })
        .mockRejectedValueOnce(new Error('Conversation init failed'));

      await act(async () => {
        await usePersonaStore.getState().loadPersonaByName('Alice');
      });

      // Persona should still be loaded
      const state = usePersonaStore.getState();
      expect(state.selectedPersona).toBeDefined();
      expect(state.error).toBeNull();
    });
  });

  // ========================================================================
  // Load Persona Expressions Tests
  // ========================================================================

  describe('Load Persona Expressions', () => {
    it('should load expressions successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          available_expressions: ['default', 'happy', 'sad', 'curious'],
          current_expression: 'happy',
        }),
      });

      await act(async () => {
        await usePersonaStore.getState().loadPersonaExpressions('Alice');
      });

      const state = usePersonaStore.getState();
      expect(state.availableExpressions).toEqual(['default', 'happy', 'sad', 'curious']);
      expect(state.currentExpression).toBe('happy');
    });

    it('should set defaults on error', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      });

      await act(async () => {
        await usePersonaStore.getState().loadPersonaExpressions('Unknown');
      });

      const state = usePersonaStore.getState();
      expect(state.availableExpressions).toEqual(['default']);
      expect(state.currentExpression).toBe('default');
    });

    it('should handle missing expressions in response', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await act(async () => {
        await usePersonaStore.getState().loadPersonaExpressions('Alice');
      });

      const state = usePersonaStore.getState();
      expect(state.availableExpressions).toEqual(['default']);
      expect(state.currentExpression).toBe('default');
    });
  });

  // ========================================================================
  // Set Persona Expression Tests
  // ========================================================================

  describe('Set Persona Expression', () => {
    it('should set expression successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          expression: 'happy',
        }),
      });

      await act(async () => {
        await usePersonaStore.getState().setPersonaExpression('Alice', 'happy');
      });

      expect(usePersonaStore.getState().currentExpression).toBe('happy');
    });

    it('should handle set expression error', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
      });

      await act(async () => {
        await usePersonaStore.getState().setPersonaExpression('Alice', 'invalid');
      });

      const state = usePersonaStore.getState();
      expect(state.error).toContain('Failed to set expression');
    });

    it('should send correct request body', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ expression: 'sad' }),
      });

      await act(async () => {
        await usePersonaStore.getState().setPersonaExpression('Alice', 'sad');
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/personas/Alice/expression'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ expression: 'sad' }),
        })
      );
    });
  });

  // ========================================================================
  // URL Encoding Tests
  // ========================================================================

  describe('URL Encoding', () => {
    it('should encode persona name in URL', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await act(async () => {
        await usePersonaStore.getState().loadPersonaExpressions('Alice & Bob');
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('Alice%20%26%20Bob')
      );
    });
  });
});
