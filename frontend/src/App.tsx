/**
 * Improved App component with better UI/UX and less crowding
 */

import React, { useEffect, useState } from 'react';
import { usePersonaStore } from './stores/personaStore';
import { useRoomStore } from './stores/roomStore';
import Grid from './components/Grid';
import ChatWindow from './components/Chat/ChatWindow';

const App: React.FC = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [showPersonaSelector, setShowPersonaSelector] = useState(false);
  const [activeTab, setActiveTab] = useState<'room' | 'chat'>('room');
  const { personas, selectedPersona, isLoading, error, loadPersonas, loadPersonaByName, clearError } = usePersonaStore();
  const { setViewMode } = useRoomStore();

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      setViewMode(mobile ? 'mobile' : 'desktop');
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    loadPersonas();

    return () => window.removeEventListener('resize', checkMobile);
  }, [loadPersonas, setViewMode]);

  const handlePersonaSelect = (personaName: string) => {
    loadPersonaByName(personaName);
    setShowPersonaSelector(false); // Auto-close after selection
  };

  if (isMobile) {
    // Mobile layout - Tab-based interface to reduce crowding

    return (
      <div className="w-full h-full flex flex-col bg-gray-900 text-white">
        {/* Mobile Header - Simplified */}
        <div className="flex-shrink-0 px-4 py-3 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
          <h1 className="text-lg font-bold">DeskMate</h1>
          {selectedPersona && (
            <button
              onClick={() => setShowPersonaSelector(!showPersonaSelector)}
              className="flex items-center space-x-2 px-3 py-1 bg-gray-700 rounded-lg"
            >
              <span className="text-sm">{selectedPersona.persona.data.name}</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          )}
        </div>

        {/* Persona Selector Overlay - Only when needed */}
        {showPersonaSelector && (
          <div className="absolute inset-0 bg-black/50 z-50 flex items-end">
            <div className="w-full bg-gray-800 rounded-t-xl p-4 max-h-[50vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Select Persona</h2>
                <button
                  onClick={() => setShowPersonaSelector(false)}
                  className="p-2 hover:bg-gray-700 rounded"
                >
                  ✕
                </button>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {personas.map((persona) => (
                  <button
                    key={persona.name}
                    onClick={() => handlePersonaSelect(persona.name)}
                    className={`p-3 rounded-lg border text-left ${
                      selectedPersona?.persona.data.name === persona.name
                        ? 'bg-blue-900/50 border-blue-500'
                        : 'bg-gray-700 border-gray-600'
                    }`}
                  >
                    <div className="font-medium text-sm">{persona.name}</div>
                    <div className="text-xs text-gray-400">{persona.creator}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex-shrink-0 flex bg-gray-800 border-b border-gray-700">
          <button
            onClick={() => setActiveTab('room')}
            className={`flex-1 py-3 text-sm font-medium ${
              activeTab === 'room'
                ? 'bg-gray-700 border-b-2 border-blue-500'
                : 'text-gray-400'
            }`}
          >
            Room View
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex-1 py-3 text-sm font-medium ${
              activeTab === 'chat'
                ? 'bg-gray-700 border-b-2 border-blue-500'
                : 'text-gray-400'
            }`}
          >
            Chat
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'room' ? (
            <div className="h-full p-4">
              <div className="mobile-grid-container">
                <Grid />
              </div>
            </div>
          ) : (
            <ChatWindow />
          )}
        </div>
      </div>
    );
  }

  // Desktop layout - Better space distribution
  return (
    <div className="w-full h-full flex bg-gray-900 text-white">
      {/* Left: Room View - More reasonable width */}
      <div className="flex-1 flex flex-col">
        {/* Room Header */}
        <div className="flex-shrink-0 px-6 py-4 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
          <h1 className="text-xl font-bold">DeskMate Room</h1>

          {/* Persona Selector Button */}
          <button
            onClick={() => setShowPersonaSelector(!showPersonaSelector)}
            className="flex items-center space-x-3 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          >
            {selectedPersona ? (
              <>
                <div className="w-8 h-8 bg-gradient-to-b from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-sm font-bold">
                  {selectedPersona.persona.data.name.charAt(0)}
                </div>
                <div className="text-left">
                  <div className="text-sm font-medium">{selectedPersona.persona.data.name}</div>
                  <div className="text-xs text-gray-400">Click to change</div>
                </div>
              </>
            ) : (
              <span className="text-sm">Select Persona</span>
            )}
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        {/* Persona Selector Dropdown - Desktop */}
        {showPersonaSelector && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center" onClick={() => setShowPersonaSelector(false)}>
            <div className="w-96 bg-gray-800 rounded-lg shadow-2xl border border-gray-700 p-4 max-h-96 overflow-y-auto" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold">Select Persona</h3>
                <button
                  onClick={() => setShowPersonaSelector(false)}
                  className="p-1 hover:bg-gray-700 rounded"
                >
                  ✕
                </button>
              </div>
              {isLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
                </div>
              ) : (
                <div className="space-y-2">
                  {personas.map((persona) => (
                    <button
                      key={persona.name}
                      onClick={() => handlePersonaSelect(persona.name)}
                      className={`w-full p-3 rounded-lg border text-left transition-colors ${
                        selectedPersona?.persona.data.name === persona.name
                          ? 'bg-blue-900/50 border-blue-500'
                          : 'bg-gray-700 border-gray-600 hover:bg-gray-600'
                      }`}
                    >
                      <div className="font-medium">{persona.name}</div>
                      <div className="text-sm text-gray-400">by {persona.creator}</div>
                      {persona.tags && (
                        <div className="mt-1">
                          {persona.tags.slice(0, 3).map((tag, i) => (
                            <span key={i} className="inline-block text-xs bg-gray-600 px-2 py-1 rounded mr-1">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Room Grid - Properly sized */}
        <div className="flex-1 p-4 overflow-auto">
          <div className="desktop-grid-container">
            <div className="relative">
              <Grid />

              {/* Room Status Bar */}
              <div className="absolute bottom-0 left-0 right-0 bg-gray-800/90 backdrop-blur px-4 py-2 flex items-center justify-between">
                <div className="flex items-center space-x-4 text-sm">
                  <span className="text-gray-400">Room:</span>
                  <span>Living Room</span>
                  {selectedPersona && (
                    <>
                      <span className="text-gray-400">•</span>
                      <span className="flex items-center">
                        <span className="status-dot bg-green-500"></span>
                        Active
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right: Chat Panel - Optimized width */}
      <div className="w-96 bg-gray-800 border-l border-gray-700 flex flex-col">
        {/* Header */}
        <div className="flex-shrink-0 p-4 border-b border-gray-700">
          <h2 className="text-lg font-bold">DeskMate Chat</h2>
        </div>

        {/* Companion Portrait - Compact */}
        {selectedPersona && (
          <div className="flex-shrink-0 p-4 border-b border-gray-700">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-gradient-to-b from-blue-500 to-blue-600 rounded-lg flex items-center justify-center overflow-hidden relative">
                <img
                  src={`/api/personas/${encodeURIComponent(selectedPersona.persona.data.name)}/image`}
                  alt={selectedPersona.persona.data.name}
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
                <div className="absolute inset-0 flex items-center justify-center text-2xl text-white font-bold" style={{display: 'none'}}>
                  {selectedPersona.persona.data.name.charAt(0)}
                </div>
              </div>
              <div className="flex-1">
                <h3 className="font-semibold">{selectedPersona.persona.data.name}</h3>
                <div className="text-sm text-gray-400">{selectedPersona.persona.data.creator}</div>
                <div className="flex items-center mt-1 text-sm">
                  <span className="mr-2">😊</span>
                  <span>Happy</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Chat Window - Takes remaining space */}
        <div className="flex-1 min-h-0">
          <ChatWindow />
        </div>
      </div>
    </div>
  );
};

export default App;