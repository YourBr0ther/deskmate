/**
 * Assistant Selection Component
 *
 * Provides a dropdown interface for selecting between different AI assistants.
 * Integrates with the persona system and backend assistant management.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { usePersonaStore } from '../../stores/personaStore';
import { useRoomStore } from '../../stores/roomStore';

interface Assistant {
  id: string;
  name: string;
  description?: string;
  persona_id?: string;
  status: 'active' | 'idle' | 'offline';
  avatar?: string;
  imageUrl?: string;
}

interface AssistantSelectorProps {
  onAssistantChange?: (assistantId: string) => void;
  className?: string;
  compact?: boolean;
}

export const AssistantSelector: React.FC<AssistantSelectorProps> = ({
  onAssistantChange,
  className = '',
  compact = false
}) => {
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [selectedAssistantId, setSelectedAssistantId] = useState<string>('default');
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { personas, selectedPersona, setSelectedPersona, currentExpression, availableExpressions, setPersonaExpression } = usePersonaStore();
  const { assistant } = useRoomStore();

  // Handle expression changes
  const handleExpressionChange = useCallback(async (expression: string) => {
    if (selectedPersona && setPersonaExpression) {
      try {
        await setPersonaExpression(selectedPersona.persona.data.name, expression);
        console.log(`Changed expression to: ${expression}`);
      } catch (error) {
        console.error('Failed to change expression:', error);
        setError('Failed to change expression');
      }
    }
  }, [selectedPersona, setPersonaExpression]);

  // Status indicator helpers
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-400';
      case 'idle': return 'bg-yellow-400';
      case 'busy': return 'bg-red-400';
      default: return 'bg-gray-400';
    }
  };

  const getMoodEmoji = (mood: string) => {
    switch (mood) {
      case 'happy': return '😊';
      case 'sad': return '😢';
      case 'excited': return '🤩';
      case 'tired': return '😴';
      case 'neutral': return '😐';
      default: return '🙂';
    }
  };

  // Avatar component with fallback
  const AssistantAvatar: React.FC<{ assistant: Assistant; size?: 'sm' | 'md' | 'lg' }> = ({
    assistant,
    size = 'md'
  }) => {
    const [imageError, setImageError] = useState(false);

    const sizeClasses = {
      sm: 'w-6 h-6',
      md: 'w-8 h-8',
      lg: 'w-10 h-10'
    };

    const statusDotSizes = {
      sm: 'w-2 h-2',
      md: 'w-3 h-3',
      lg: 'w-3 h-3'
    };

    if (assistant.imageUrl && !imageError) {
      return (
        <div className="relative">
          <img
            src={assistant.imageUrl}
            alt={assistant.name}
            className={`${sizeClasses[size]} rounded-full object-cover border-2 border-gray-300`}
            onError={() => setImageError(true)}
          />
          <div className={`absolute -bottom-0.5 -right-0.5 ${statusDotSizes[size]} rounded-full border-2 border-white ${
            assistant.status === 'active' ? 'bg-green-400' :
            assistant.status === 'idle' ? 'bg-yellow-400' : 'bg-gray-400'
          }`} />
        </div>
      );
    }

    // Fallback to status dot only
    return (
      <div className={`${statusDotSizes[size]} rounded-full ${
        assistant.status === 'active' ? 'bg-green-400' :
        assistant.status === 'idle' ? 'bg-yellow-400' : 'bg-gray-400'
      }`} />
    );
  };

  // Load available assistants from API
  const loadAssistants = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch available assistants from backend
      const response = await fetch('/api/assistant/list');
      if (!response.ok) {
        throw new Error(`Failed to fetch assistants: ${response.statusText}`);
      }

      const data = await response.json();
      const apiAssistants: Assistant[] = data.assistants.map((assistant: any) => ({
        id: assistant.id,
        name: assistant.name,
        description: assistant.description,
        status: assistant.status as 'active' | 'idle' | 'offline'
      }));

      // Add persona-based assistants from test folder only
      if (personas.length > 0) {
        const personaAssistants = personas.map(persona => ({
          id: `persona-${persona.name}`,
          name: persona.name || 'Unnamed Persona',
          description: `Persona-based assistant`,
          persona_id: persona.name,
          status: 'idle' as const,
          imageUrl: `/api/personas/${encodeURIComponent(persona.name)}/image?expression=default`
        }));

        setAssistants([...apiAssistants, ...personaAssistants]);
      } else {
        setAssistants(apiAssistants);
      }

      // Set the current assistant from API response
      if (data.current_assistant) {
        setSelectedAssistantId(data.current_assistant);
      } else if (personas.length > 0) {
        // If no current assistant and we have personas, select the first one
        const firstPersonaId = `persona-${personas[0].name}`;
        setSelectedAssistantId(firstPersonaId);

        // Also load the first persona
        try {
          await usePersonaStore.getState().loadPersonaByName(personas[0].name);
        } catch (err) {
          console.warn('Failed to auto-load first persona:', err);
        }
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load assistants');
      console.error('Error loading assistants:', err);
    } finally {
      setIsLoading(false);
    }
  }, [personas]);

  // Load assistants on mount and when personas change
  useEffect(() => {
    loadAssistants();
  }, [loadAssistants]);

  // Handle assistant selection
  const handleAssistantSelect = useCallback(async (assistantId: string) => {
    const assistant = assistants.find(a => a.id === assistantId);
    if (!assistant) return;

    setSelectedAssistantId(assistantId);
    setIsOpen(false);

    // If this is a persona-based assistant, select the persona
    if (assistant.persona_id) {
      const persona = personas.find(p => p.name === assistant.persona_id);
      if (persona && persona.name !== selectedPersona?.persona.data.name) {
        // Load the persona by name (which sets it as selected)
        await usePersonaStore.getState().loadPersonaByName(persona.name);
      }
    } else if (selectedPersona) {
      // Clear persona selection if switching to non-persona assistant
      setSelectedPersona(null);
    }

    // Notify parent component
    onAssistantChange?.(assistantId);

    // Send assistant change to backend API
    try {
      console.log(`Switching to assistant: ${assistant.name}`);

      // Update assistant status to active immediately for UI feedback
      setAssistants(prevAssistants =>
        prevAssistants.map(a => ({
          ...a,
          status: a.id === assistantId ? 'active' :
                  a.status === 'active' ? 'idle' : a.status
        }))
      );

      const response = await fetch('/api/assistant/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assistant_id: assistantId,
          preserve_context: true
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to switch assistant');
      }

      const result = await response.json();
      console.log('Assistant switch successful:', result.message);

    } catch (err) {
      console.error('Error switching assistant:', err);
      setError(err instanceof Error ? err.message : 'Failed to switch assistant');

      // Revert status changes on error
      setAssistants(prevAssistants =>
        prevAssistants.map(a => ({
          ...a,
          status: 'idle'
        }))
      );
    }
  }, [assistants, personas, selectedPersona, setSelectedPersona, onAssistantChange]);

  const selectedAssistant = assistants.find(a => a.id === selectedAssistantId);

  if (compact) {
    return (
      <div className={`assistant-selector-compact relative ${className}`}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center space-x-2 px-3 py-1 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        >
          {selectedAssistant ? (
            <AssistantAvatar assistant={selectedAssistant} size="sm" />
          ) : (
            <div className="w-2 h-2 rounded-full bg-gray-400" />
          )}
          <span className="text-sm font-medium text-gray-700">
            {isLoading ? 'Loading...' : selectedAssistant?.name || 'Select Assistant'}
          </span>
          <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-300 rounded-md shadow-lg z-50">
            <div className="py-1">
              {assistants.map((assistant) => (
                <button
                  key={assistant.id}
                  onClick={() => handleAssistantSelect(assistant.id)}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${
                    selectedAssistantId === assistant.id ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <AssistantAvatar assistant={assistant} size="sm" />
                    <div className="flex-1">
                      <div className="font-medium">{assistant.name}</div>
                      {assistant.description && (
                        <div className="text-xs text-gray-500 mt-1 line-clamp-2">
                          {assistant.description}
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`assistant-selector ${className}`}>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        AI Assistant
      </label>

      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between px-4 py-3 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        >
          <div className="flex items-center space-x-3">
            {selectedAssistant ? (
              <>
                <AssistantAvatar assistant={selectedAssistant} size="md" />
                <div className="text-left">
                  <div className="font-medium text-gray-900">{selectedAssistant.name}</div>
                  {selectedAssistant.description && (
                    <div className="text-sm text-gray-500 line-clamp-1">
                      {selectedAssistant.description}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <span className="text-gray-500">
                {isLoading ? 'Loading assistants...' : 'Select an assistant'}
              </span>
            )}
          </div>

          <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg z-50">
            <div className="py-1 max-h-64 overflow-y-auto">
              {assistants.map((assistant) => (
                <button
                  key={assistant.id}
                  onClick={() => handleAssistantSelect(assistant.id)}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-100 ${
                    selectedAssistantId === assistant.id ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <AssistantAvatar assistant={assistant} size="md" />
                    <div className="flex-1">
                      <div className="font-medium">{assistant.name}</div>
                      {assistant.description && (
                        <div className="text-sm text-gray-500 mt-1">
                          {assistant.description}
                        </div>
                      )}
                      {assistant.persona_id && (
                        <div className="text-xs text-blue-600 mt-1">
                          Persona-based assistant
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {error && (
              <div className="px-4 py-2 border-t border-gray-200 bg-red-50">
                <div className="text-sm text-red-600">{error}</div>
                <button
                  onClick={loadAssistants}
                  className="text-xs text-red-700 hover:text-red-800 mt-1"
                >
                  Retry
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Click outside to close */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Enhanced Status Panel */}
      {!compact && selectedPersona && assistant && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg border">
          <h3 className="text-sm font-semibold mb-2 text-gray-700">Assistant Status</h3>

          {/* Status indicators */}
          <div className="space-y-2 mb-3">
            <div className="flex items-center text-sm">
              <div className={`w-3 h-3 rounded-full ${getStatusColor(assistant.status)} mr-2`}></div>
              <span className="text-gray-600">Status:</span>
              <span className="ml-1 font-medium capitalize">{assistant.status}</span>
            </div>

            <div className="flex items-center text-sm">
              <span className="mr-2 text-lg">{getMoodEmoji(assistant.mood)}</span>
              <span className="text-gray-600">Mood:</span>
              <span className="ml-1 font-medium capitalize">{assistant.mood}</span>
            </div>

            {assistant.currentAction && (
              <div className="flex items-center text-sm">
                <span className="text-gray-600">Action:</span>
                <span className="ml-1 font-medium">{assistant.currentAction}</span>
              </div>
            )}

            <div className="flex items-center text-sm">
              <span className="text-gray-600">Position:</span>
              <span className="ml-1 font-mono text-xs">({Math.round(assistant.position.x)}, {Math.round(assistant.position.y)})</span>
            </div>
          </div>

          {/* Expression Controls */}
          {availableExpressions && availableExpressions.length > 1 && (
            <div className="border-t pt-3">
              <h4 className="text-sm font-medium mb-2 text-gray-700">Expression</h4>
              <div className="flex flex-wrap gap-1">
                {availableExpressions.map((expression) => (
                  <button
                    key={expression}
                    onClick={() => handleExpressionChange(expression)}
                    className={`px-2 py-1 text-xs rounded border transition-colors ${
                      currentExpression === expression
                        ? 'bg-blue-100 border-blue-300 text-blue-700'
                        : 'bg-white border-gray-300 hover:bg-gray-50 text-gray-600'
                    }`}
                    title={`Switch to ${expression} expression`}
                  >
                    {expression}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AssistantSelector;