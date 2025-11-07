/**
 * Model selector component for switching between LLM models
 */

import React, { useEffect, useState } from 'react';

import { useChatStore, LLMModel } from '../../stores/chatStore';

const ModelSelector: React.FC = () => {
  const {
    availableModels,
    currentModel,
    setAvailableModels,
    setCurrentModel,
    isConnected
  } = useChatStore();

  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load available models on mount
  useEffect(() => {
    const loadModels = async () => {
      if (!isConnected) return;

      setLoading(true);
      try {
        const response = await fetch('/api/chat/models');
        if (response.ok) {
          const data = await response.json();
          setAvailableModels(data.models);
        }
      } catch (error) {
        console.error('Failed to load models:', error);
      } finally {
        setLoading(false);
      }
    };

    loadModels();
  }, [isConnected, setAvailableModels]);

  const handleModelChange = (modelId: string) => {
    setCurrentModel(modelId);
    setIsOpen(false);
  };

  const currentModelData = availableModels.find(m => m.id === currentModel);

  if (!isConnected) {
    return (
      <div className="text-sm text-gray-400">
        Connect to view models
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center space-x-2 text-sm text-gray-400">
        <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
        <span>Loading models...</span>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Current Model Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full p-2 bg-gray-800 border border-gray-600 rounded-lg hover:bg-gray-700 transition-colors"
      >
        <div className="flex items-center space-x-3">
          <div className={`w-2 h-2 rounded-full ${
            currentModelData?.provider === 'nano_gpt' ? 'bg-blue-500' : 'bg-green-500'
          }`} />
          <div className="text-left">
            <div className="text-sm font-medium text-white">
              {currentModelData?.name || currentModel}
            </div>
            <div className="text-xs text-gray-400">
              {currentModelData?.description || 'Model description'}
            </div>
          </div>
        </div>
        <svg
          className={`w-4 h-4 text-gray-400 transform transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
          {availableModels.length === 0 ? (
            <div className="p-3 text-sm text-gray-400 text-center">
              No models available
            </div>
          ) : (
            availableModels.map((model) => (
              <button
                key={model.id}
                onClick={() => handleModelChange(model.id)}
                className={`w-full text-left p-3 hover:bg-gray-700 transition-colors border-b border-gray-700 last:border-b-0 ${
                  model.id === currentModel ? 'bg-gray-700' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      model.provider === 'nano_gpt' ? 'bg-blue-500' : 'bg-green-500'
                    }`} />
                    <div>
                      <div className="text-sm font-medium text-white">
                        {model.name}
                      </div>
                      <div className="text-xs text-gray-400">
                        {model.description}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {model.max_tokens.toLocaleString()} tokens • {model.context_window.toLocaleString()} context
                        {model.cost_per_token > 0 && (
                          <span> • ${model.cost_per_token.toFixed(6)}/token</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs ${
                    model.provider === 'nano_gpt'
                      ? 'bg-blue-600 text-white'
                      : 'bg-green-600 text-white'
                  }`}>
                    {model.provider === 'nano_gpt' ? 'Cloud' : 'Local'}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {/* Backdrop to close dropdown */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default ModelSelector;