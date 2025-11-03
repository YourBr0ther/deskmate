/**
 * Zustand store for persona management (Web version)
 */

import { create } from 'zustand';
import { PersonaSummary, LoadedPersona } from '../types/persona';

interface PersonaStore {
  // State
  personas: PersonaSummary[];
  selectedPersona: LoadedPersona | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setPersonas: (personas: PersonaSummary[]) => void;
  setSelectedPersona: (persona: LoadedPersona | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // API calls
  loadPersonas: () => Promise<void>;
  loadPersonaByName: (name: string) => Promise<void>;
  clearError: () => void;
}

// Get API base URL - works in both development and production
const getApiBaseUrl = () => {
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:8000';
  }
  // In production, use the API proxy route or direct backend URL
  if (window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  // For deployed version, use /api proxy
  return '/api';
};

export const usePersonaStore = create<PersonaStore>((set, get) => ({
  // Initial state
  personas: [],
  selectedPersona: null,
  isLoading: false,
  error: null,

  // Actions
  setPersonas: (personas) => set({ personas }),
  setSelectedPersona: (persona) => set({ selectedPersona: persona }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),

  // Load all personas from test directory
  loadPersonas: async () => {
    const { setLoading, setError, setPersonas } = get();

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiBaseUrl()}/personas/test`);

      if (!response.ok) {
        throw new Error(`Failed to load personas: ${response.status}`);
      }

      const personas: PersonaSummary[] = await response.json();
      setPersonas(personas);
    } catch (error) {
      console.error('Error loading personas:', error);
      setError(error instanceof Error ? error.message : 'Failed to load personas');
    } finally {
      setLoading(false);
    }
  },

  // Load detailed persona data by name
  loadPersonaByName: async (name: string) => {
    const { setLoading, setError, setSelectedPersona } = get();

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${getApiBaseUrl()}/personas/${encodeURIComponent(name)}?summary_only=false&directory=/data/personas`
      );

      if (!response.ok) {
        throw new Error(`Failed to load persona: ${response.status}`);
      }

      const personaData = await response.json();

      // Convert API response to LoadedPersona format
      const loadedPersona: LoadedPersona = {
        persona: personaData.persona,
        metadata: personaData.metadata
      };

      setSelectedPersona(loadedPersona);

      // Initialize conversation memory for this persona
      try {
        const convResponse = await fetch(`${getApiBaseUrl()}/conversation/initialize`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            persona_name: personaData.persona.data.name,
            load_history: true
          }),
        });

        if (convResponse.ok) {
          const convData = await convResponse.json();
          console.log(`Initialized conversation for persona: ${personaData.persona.data.name}`);

          // Load chat history if available
          if (convData.messages && convData.messages.length > 0) {
            // Import the chat store to load history
            const { useChatStore } = await import('./chatStore');
            const chatStore = useChatStore.getState();
            chatStore.loadChatHistory(convData.messages);
            console.log(`Loaded ${convData.count} previous messages for ${personaData.persona.data.name}`);
          }
        }
      } catch (convError) {
        console.warn('Failed to initialize conversation memory:', convError);
        // Don't fail the persona loading if conversation init fails
      }
    } catch (error) {
      console.error('Error loading persona by name:', error);
      setError(error instanceof Error ? error.message : 'Failed to load persona');
      setSelectedPersona(null);
    } finally {
      setLoading(false);
    }
  },
}));