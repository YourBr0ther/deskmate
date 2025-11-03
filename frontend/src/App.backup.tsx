/**
 * Main App component - Responsive web layout (Simplified)
 */

import React, { useEffect, useState } from 'react';
import { usePersonaStore } from './stores/personaStore';
import { useRoomStore } from './stores/roomStore';
import Grid from './components/Grid';
import CompanionPanel from './components/CompanionPanel';
import ChatWindow from './components/Chat/ChatWindow';

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

        {/* Mobile Chat Area */}
        <div className="flex-shrink-0 h-48 border-t border-gray-700">
          <ChatWindow />
        </div>

        {/* Mobile Persona Selection */}
        <div className="flex-shrink-0 max-h-32 overflow-y-auto bg-gray-800 border-t border-gray-700">
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

  // Desktop layout - side by side with chat
  return (
    <div className="w-full h-full flex bg-gray-900 text-white">
      {/* Left: Grid Area (1280px width target) */}
      <div className="flex-1 max-w-[1280px] p-4 overflow-auto">
        <div className="desktop-grid-container">
          <Grid />
        </div>
      </div>

      {/* Right: Companion Panel (640px width target) */}
      <div className="w-[640px] min-w-[640px] bg-gray-800 border-l border-gray-700 flex flex-col">
        {/* Top: Companion Info (400px height for portrait + status) */}
        <div className="h-[400px] flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-700 flex-shrink-0">
            <h2 className="text-lg font-bold">DeskMate Companion</h2>
          </div>

          {/* Portrait Section */}
          <div className="p-4 flex-shrink-0">
            <CompanionPanel />
          </div>

          {/* Character Info & Quick Persona Selection */}
          <div className="flex-1 p-4 overflow-y-auto">
            {/* Character Status */}
            {selectedPersona && (
              <div className="space-y-2 mb-4">
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

            {/* Compact Persona Selection */}
            <div>
              <h3 className="text-sm font-semibold mb-2">Available Personas</h3>

              {error && (
                <div className="bg-red-900/50 border border-red-700 text-red-200 p-2 rounded mb-2 text-xs">
                  {error}
                  <button onClick={clearError} className="ml-2 underline">Dismiss</button>
                </div>
              )}

              {isLoading ? (
                <div className="text-center py-2">
                  <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
                  <div className="text-xs mt-1">Loading...</div>
                </div>
              ) : (
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {personas.slice(0, 5).map((persona) => (
                    <button
                      key={persona.name}
                      onClick={() => handlePersonaSelect(persona.name)}
                      className={`w-full text-left p-2 rounded border text-xs transition-colors ${
                        selectedPersona?.persona.data.name === persona.name
                          ? 'bg-blue-900/50 border-blue-700'
                          : 'bg-gray-700 border-gray-600 hover:bg-gray-600'
                      }`}
                    >
                      <div className="font-medium">{persona.name}</div>
                      <div className="text-gray-400">by {persona.creator}</div>
                    </button>
                  ))}
                  {personas.length > 5 && (
                    <div className="text-xs text-gray-400 text-center py-1">
                      +{personas.length - 5} more available
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Bottom: Chat Window (80px height minimum, flexible) */}
        <div className="flex-1 min-h-[80px] border-t border-gray-700">
          <ChatWindow />
        </div>

        {/* Footer */}
        <div className="p-2 border-t border-gray-700 flex-shrink-0">
          <div className="text-xs text-gray-400 text-center">
            DeskMate v0.1.0 | {personas.length} personas
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;