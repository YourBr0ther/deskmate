/**
 * Main App component - Responsive web layout (Simplified)
 */

import React, { useEffect, useState } from 'react';
import { usePersonaStore } from './stores/personaStore';
import { useRoomStore } from './stores/roomStore';
import Grid from './components/Grid';
import CompanionPanel from './components/CompanionPanel';

const App: React.FC = () => {
  const [isMobile, setIsMobile] = useState(false);
  const { personas, selectedPersona, isLoading, error, loadPersonas, loadPersonaByName, clearError } = usePersonaStore();
  const { setViewMode } = useRoomStore();

  // Check if mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      setViewMode(mobile ? 'mobile' : 'desktop');
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);

    // Load personas on app start
    loadPersonas();

    return () => window.removeEventListener('resize', checkMobile);
  }, [loadPersonas, setViewMode]);

  const handlePersonaSelect = (personaName: string) => {
    loadPersonaByName(personaName);
  };

  if (isMobile) {
    // Mobile layout - stacked vertically
    return (
      <div className="w-full h-full flex flex-col bg-gray-900 text-white">
        {/* Mobile Header */}
        <div className="flex-shrink-0 p-4 bg-gray-800 border-b border-gray-700">
          <h1 className="text-xl font-bold">DeskMate</h1>
          <p className="text-sm text-gray-400">Virtual AI Companion</p>
        </div>

        {/* Mobile Portrait Section */}
        {selectedPersona && (
          <div className="flex-shrink-0 p-4 bg-gray-800 border-b border-gray-700">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-gradient-to-b from-gray-700 to-gray-800 rounded-lg flex items-center justify-center text-2xl">
                {selectedPersona.persona.data.name.charAt(0)}
              </div>
              <div className="flex-1">
                <h2 className="font-bold">{selectedPersona.persona.data.name}</h2>
                <p className="text-sm text-gray-400">by {selectedPersona.persona.data.creator}</p>
                <div className="flex items-center mt-1">
                  <span className="status-dot bg-yellow-500"></span>
                  <span className="text-xs">Idle</span>
                  <span className="ml-2">😐</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Mobile Grid Area */}
        <div className="flex-1 p-4 overflow-auto">
          <div className="mobile-grid-container">
            <Grid />
          </div>
        </div>

        {/* Mobile Persona Selection */}
        <div className="flex-shrink-0 max-h-48 overflow-y-auto bg-gray-800 border-t border-gray-700">
          <div className="p-4">
            <h3 className="font-semibold mb-2">Select Persona</h3>
            {error && (
              <div className="bg-red-900/50 border border-red-700 text-red-200 p-2 rounded mb-2 text-sm">
                {error}
                <button onClick={clearError} className="ml-2 underline text-xs">Dismiss</button>
              </div>
            )}
            {isLoading ? (
              <div className="text-center py-2">
                <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
              </div>
            ) : (
              <div className="space-y-2">
                {personas.map((persona) => (
                  <button
                    key={persona.name}
                    onClick={() => handlePersonaSelect(persona.name)}
                    className={`w-full text-left p-2 rounded border text-sm transition-colors ${
                      selectedPersona?.persona.data.name === persona.name
                        ? 'bg-blue-900/50 border-blue-700'
                        : 'bg-gray-700 border-gray-600 hover:bg-gray-600'
                    }`}
                  >
                    <div className="font-medium">{persona.name}</div>
                    <div className="text-xs text-gray-400">by {persona.creator}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Desktop layout - side by side
  return (
    <div className="w-full h-full flex bg-gray-900 text-white">
      {/* Left: Grid Area */}
      <div className="flex-1 p-4 overflow-auto">
        <div className="desktop-grid-container max-w-6xl mx-auto">
          <Grid />
        </div>
      </div>

      {/* Right: Companion Panel */}
      <div className="w-80 bg-gray-800 border-l border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-lg font-bold">DeskMate Companion</h2>
        </div>

        {/* Portrait Section */}
        <div className="p-4 flex-shrink-0">
          <CompanionPanel />
        </div>

        {/* Character Info */}
        <div className="p-4 flex-shrink-0">
          {selectedPersona && (
            <div className="space-y-2">
              <div className="flex items-center">
                <span className="status-dot bg-yellow-500"></span>
                <span className="text-sm">Status: Idle</span>
              </div>
              <div className="flex items-center">
                <span className="mr-2">😐</span>
                <span className="text-sm">Mood: Neutral</span>
              </div>
              <div className="text-sm">
                <span className="text-gray-400">Tags: </span>
                {selectedPersona.persona.data.tags.slice(0, 3).join(', ')}
                {selectedPersona.persona.data.tags.length > 3 && '...'}
              </div>
            </div>
          )}
        </div>

        {/* Persona Selection */}
        <div className="flex-1 p-4 overflow-y-auto">
          <h3 className="text-md font-semibold mb-3">Available Personas</h3>

          {error && (
            <div className="bg-red-900/50 border border-red-700 text-red-200 p-3 rounded mb-3">
              <div className="font-medium">Error</div>
              <div className="text-sm">{error}</div>
              <button onClick={clearError} className="text-xs underline mt-1">Dismiss</button>
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
                      : 'bg-gray-700 border-gray-600 hover:bg-gray-600'
                  }`}
                >
                  <div className="font-medium">{persona.name}</div>
                  <div className="text-sm text-gray-400">by {persona.creator}</div>
                  <div className="text-xs mt-1 flex flex-wrap gap-1">
                    {persona.tags.slice(0, 3).map((tag) => (
                      <span key={tag} className="bg-gray-600 px-1 py-0.5 rounded text-xs">
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
        <div className="p-4 border-t border-gray-700 flex-shrink-0">
          <div className="text-xs text-gray-400 text-center">
            DeskMate v0.1.0 | {personas.length} personas loaded
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;