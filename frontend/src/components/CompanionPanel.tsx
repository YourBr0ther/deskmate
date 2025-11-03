/**
 * Companion Panel - 640x480 right panel with portrait and character info
 */

import React, { useEffect } from 'react';
import { usePersonaStore } from '../stores/personaStore';
import { useRoomStore } from '../stores/roomStore';

const CompanionPanel: React.FC = () => {
  const {
    personas,
    selectedPersona,
    currentExpression,
    availableExpressions,
    isLoading,
    error,
    loadPersonas,
    loadPersonaByName,
    loadPersonaExpressions,
    setPersonaExpression,
    clearError
  } = usePersonaStore();

  const { assistant } = useRoomStore();

  // Load personas on component mount
  useEffect(() => {
    loadPersonas();
  }, [loadPersonas]);

  const handlePersonaSelect = async (personaName: string) => {
    await loadPersonaByName(personaName);
    // Load expressions for the selected persona
    await loadPersonaExpressions(personaName);
  };

  const handleExpressionChange = async (expression: string) => {
    if (selectedPersona) {
      await setPersonaExpression(selectedPersona.persona.data.name, expression);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'status-active';
      case 'idle': return 'status-idle';
      case 'busy': return 'status-busy';
      default: return 'status-idle';
    }
  };

  const getMoodEmoji = (mood: string) => {
    switch (mood) {
      case 'happy': return '😊';
      case 'sad': return '😢';
      case 'excited': return '🤩';
      case 'tired': return '😴';
      default: return '😐';
    }
  };

  return (
    <div className="panel-area companion-panel flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-panel-border">
        <h2 className="text-lg font-bold text-panel-text">DeskMate Companion</h2>
      </div>

      {/* Portrait Section */}
      <div className="p-4 flex-shrink-0">
        <div className="portrait-frame mx-auto w-64 h-64 max-w-full">
          {selectedPersona ? (
            <div className="w-full h-full bg-gradient-to-b from-gray-800 to-gray-900 flex items-center justify-center relative overflow-hidden rounded-lg">
              {/* Use actual persona PNG with current expression */}
              <img
                src={`/api/personas/${encodeURIComponent(selectedPersona.persona.data.name)}/image?expression=${currentExpression}`}
                alt={`${selectedPersona.persona.data.name} - ${currentExpression}`}
                className="w-full h-full object-cover"
                onError={(e) => {
                  // Fallback to character initial if image fails to load
                  e.currentTarget.style.display = 'none';
                  const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                  if (fallback) {
                    fallback.style.display = 'flex';
                  }
                }}
              />

              {/* Fallback character initial (hidden by default) */}
              <div className="absolute inset-0 flex items-center justify-center text-6xl text-white" style={{display: 'none'}}>
                {selectedPersona.persona.data.name.charAt(0)}
              </div>

              {/* Character name overlay */}
              <div className="absolute bottom-0 left-0 right-0 bg-black/75 text-white p-2 text-center">
                <div className="font-bold">{selectedPersona.persona.data.name}</div>
                <div className="text-sm opacity-75">by {selectedPersona.persona.data.creator}</div>
              </div>
            </div>
          ) : (
            <div className="w-full h-full bg-gray-800 flex items-center justify-center rounded-lg">
              <div className="text-gray-400 text-center">
                <div className="text-4xl mb-2">👤</div>
                <div>No persona selected</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Character Info */}
      <div className="p-4 flex-shrink-0">
        {selectedPersona && (
          <div className="space-y-2">
            <div className="flex items-center">
              <span className={`status-indicator ${getStatusColor(assistant.status)}`}></span>
              <span className="text-sm">Status: {assistant.status}</span>
            </div>
            <div className="flex items-center">
              <span className="mr-2">{getMoodEmoji(assistant.mood)}</span>
              <span className="text-sm">Mood: {assistant.mood}</span>
            </div>
            {assistant.currentAction && (
              <div className="text-sm">
                <span className="opacity-75">Action: </span>
                <span>{assistant.currentAction}</span>
              </div>
            )}
            <div className="text-sm">
              <span className="opacity-75">Position: </span>
              <span>({assistant.position.x}, {assistant.position.y})</span>
            </div>
          </div>
        )}
      </div>

      {/* Expression Controls */}
      {selectedPersona && availableExpressions.length > 1 && (
        <div className="p-4 flex-shrink-0 border-t border-panel-border">
          <h3 className="text-sm font-semibold mb-2">Expression</h3>
          <div className="flex flex-wrap gap-2">
            {availableExpressions.map((expression) => (
              <button
                key={expression}
                onClick={() => handleExpressionChange(expression)}
                className={`px-3 py-1 text-xs rounded border transition-colors ${
                  currentExpression === expression
                    ? 'bg-blue-900/50 border-blue-700 text-blue-200'
                    : 'bg-gray-800/50 border-gray-700 hover:bg-gray-700/50 text-gray-300'
                }`}
                title={`Switch to ${expression} expression`}
              >
                {expression}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Persona Selection */}
      <div className="flex-1 p-4 overflow-y-auto">
        <h3 className="text-md font-semibold mb-3">Available Personas</h3>

        {error && (
          <div className="bg-red-900/50 border border-red-700 text-red-200 p-3 rounded mb-3">
            <div className="font-medium">Error</div>
            <div className="text-sm">{error}</div>
            <button
              onClick={clearError}
              className="text-xs underline mt-1"
            >
              Dismiss
            </button>
          </div>
        )}

        {isLoading ? (
          <div className="text-center py-4">
            <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
            <div className="text-sm mt-2">Loading personas...</div>
          </div>
        ) : (
          <div className="space-y-2">
            {personas.map((persona) => (
              <button
                key={persona.name}
                onClick={() => handlePersonaSelect(persona.name)}
                className={`w-full text-left p-3 rounded border transition-colors ${
                  selectedPersona?.persona.data.name === persona.name
                    ? 'bg-blue-900/50 border-blue-700'
                    : 'bg-gray-800/50 border-gray-700 hover:bg-gray-700/50'
                }`}
              >
                <div className="font-medium">{persona.name}</div>
                <div className="text-sm opacity-75">by {persona.creator}</div>
                <div className="text-xs mt-1 flex flex-wrap gap-1">
                  {persona.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="bg-gray-700 px-1 py-0.5 rounded text-xs"
                    >
                      {tag}
                    </span>
                  ))}
                  {persona.tags.length > 3 && (
                    <span className="text-gray-400">+{persona.tags.length - 3}</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-panel-border flex-shrink-0">
        <div className="text-xs text-gray-400 text-center">
          DeskMate v0.1.0 | {personas.length} personas loaded
        </div>
      </div>
    </div>
  );
};

export default CompanionPanel;