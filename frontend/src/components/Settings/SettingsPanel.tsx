/**
 * Settings Panel Component - Comprehensive settings management UI
 */

import React from 'react';
import { useSettingsStore } from '../../stores/settingsStore';

const SettingsPanel: React.FC = () => {
  const {
    isSettingsOpen,
    activeSettingsTab,
    display,
    llm,
    chat,
    notifications,
    debugMode,
    showDebugPanel,
    logLevel,
    closeSettings,
    setActiveTab,
    setTheme,
    setGridDisplayMode,
    toggleFPS,
    togglePerformanceMetrics,
    toggleAnimations,
    setHighQualityRendering,
    setPanelTransparency,
    setDefaultProvider,
    setDefaultModel,
    setAutoSelectModel,
    setMaxTokens,
    setTemperature,
    toggleTimestamps,
    toggleTypingIndicator,
    setMessageRetention,
    toggleAutoScroll,
    setFontSize,
    setNotificationSetting,
    toggleDebugMode,
    toggleDebugPanel,
    setLogLevel,
    resetDisplaySettings,
    resetLLMSettings,
    resetChatSettings,
    resetAllSettings,
  } = useSettingsStore();

  if (!isSettingsOpen) return null;

  const tabButtons = [
    { id: 'display' as const, label: 'Display', icon: '🎨' },
    { id: 'llm' as const, label: 'AI Models', icon: '🤖' },
    { id: 'chat' as const, label: 'Chat', icon: '💬' },
    { id: 'notifications' as const, label: 'Notifications', icon: '🔔' },
    { id: 'debug' as const, label: 'Debug', icon: '🐛' },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
      <div className="w-full max-w-4xl h-full max-h-[90vh] bg-gray-800 rounded-lg shadow-2xl border border-gray-700 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-2xl font-bold text-white">Settings</h2>
          <button
            onClick={closeSettings}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-64 bg-gray-900 border-r border-gray-700 p-4">
            <nav className="space-y-2">
              {tabButtons.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-colors flex items-center space-x-3 ${
                    activeSettingsTab === tab.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <span className="text-lg">{tab.icon}</span>
                  <span className="font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>

            {/* Reset Section */}
            <div className="mt-8 pt-4 border-t border-gray-700">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">Reset</h3>
              <div className="space-y-2">
                <button
                  onClick={resetAllSettings}
                  className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-red-900/30 rounded"
                >
                  Reset All Settings
                </button>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {activeSettingsTab === 'display' && <DisplaySettings />}
            {activeSettingsTab === 'llm' && <LLMSettings />}
            {activeSettingsTab === 'chat' && <ChatSettings />}
            {activeSettingsTab === 'notifications' && <NotificationSettings />}
            {activeSettingsTab === 'debug' && <DebugSettings />}
          </div>
        </div>
      </div>
    </div>
  );
};

// Display Settings Panel
const DisplaySettings: React.FC = () => {
  const {
    display,
    setTheme,
    setGridDisplayMode,
    toggleFPS,
    togglePerformanceMetrics,
    toggleAnimations,
    setHighQualityRendering,
    setPanelTransparency,
    resetDisplaySettings,
  } = useSettingsStore();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold text-white">Display Settings</h3>
        <button
          onClick={resetDisplaySettings}
          className="px-3 py-1 text-sm text-gray-400 hover:text-white border border-gray-600 rounded hover:border-gray-500"
        >
          Reset
        </button>
      </div>

      {/* Theme */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">Theme</label>
        <select
          value={display.theme}
          onChange={(e) => setTheme(e.target.value as any)}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
        >
          <option value="dark">Dark</option>
          <option value="light">Light</option>
          <option value="auto">Auto (System)</option>
        </select>
      </div>

      {/* Grid Display Mode */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">Grid Display Mode</label>
        <select
          value={display.gridDisplayMode}
          onChange={(e) => setGridDisplayMode(e.target.value as any)}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
        >
          <option value="normal">Normal</option>
          <option value="compact">Compact</option>
          <option value="detailed">Detailed</option>
        </select>
      </div>

      {/* Panel Transparency */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">
          Panel Transparency: {display.panelTransparency}%
        </label>
        <input
          type="range"
          min="0"
          max="100"
          value={display.panelTransparency}
          onChange={(e) => setPanelTransparency(Number(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
      </div>

      {/* Performance Options */}
      <div className="space-y-3">
        <h4 className="text-lg font-medium text-white">Performance</h4>

        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={display.showFPS}
            onChange={toggleFPS}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">Show FPS Counter</span>
        </label>

        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={display.showPerformanceMetrics}
            onChange={togglePerformanceMetrics}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">Show Performance Metrics</span>
        </label>

        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={display.animationsEnabled}
            onChange={toggleAnimations}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">Enable Animations</span>
        </label>

        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={display.highQualityRendering}
            onChange={(e) => setHighQualityRendering(e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">High Quality Rendering</span>
        </label>
      </div>
    </div>
  );
};

// LLM Settings Panel
const LLMSettings: React.FC = () => {
  const {
    llm,
    setDefaultProvider,
    setDefaultModel,
    setAutoSelectModel,
    setMaxTokens,
    setTemperature,
    resetLLMSettings,
  } = useSettingsStore();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold text-white">AI Model Settings</h3>
        <button
          onClick={resetLLMSettings}
          className="px-3 py-1 text-sm text-gray-400 hover:text-white border border-gray-600 rounded hover:border-gray-500"
        >
          Reset
        </button>
      </div>

      {/* Default Provider */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">Default Provider</label>
        <select
          value={llm.defaultProvider}
          onChange={(e) => setDefaultProvider(e.target.value as any)}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
        >
          <option value="nano-gpt">Nano-GPT (Cloud)</option>
          <option value="ollama">Ollama (Local)</option>
        </select>
      </div>

      {/* Default Model */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">Default Model</label>
        <input
          type="text"
          value={llm.defaultModel}
          onChange={(e) => setDefaultModel(e.target.value)}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
          placeholder="e.g., gpt-4o-mini"
        />
      </div>

      {/* Auto Select Model */}
      <label className="flex items-center space-x-3">
        <input
          type="checkbox"
          checked={llm.autoSelectModel}
          onChange={(e) => setAutoSelectModel(e.target.checked)}
          className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
        />
        <span className="text-gray-300">Auto-select best model for task</span>
      </label>

      {/* Max Tokens */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">
          Max Tokens: {llm.maxTokens}
        </label>
        <input
          type="range"
          min="100"
          max="8000"
          step="100"
          value={llm.maxTokens}
          onChange={(e) => setMaxTokens(Number(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
      </div>

      {/* Temperature */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">
          Temperature: {llm.temperature.toFixed(1)}
        </label>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          value={llm.temperature}
          onChange={(e) => setTemperature(Number(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-400">
          <span>Focused</span>
          <span>Balanced</span>
          <span>Creative</span>
        </div>
      </div>
    </div>
  );
};

// Chat Settings Panel
const ChatSettings: React.FC = () => {
  const {
    chat,
    toggleTimestamps,
    toggleTypingIndicator,
    setMessageRetention,
    toggleAutoScroll,
    setFontSize,
    resetChatSettings,
  } = useSettingsStore();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold text-white">Chat Settings</h3>
        <button
          onClick={resetChatSettings}
          className="px-3 py-1 text-sm text-gray-400 hover:text-white border border-gray-600 rounded hover:border-gray-500"
        >
          Reset
        </button>
      </div>

      {/* Chat Options */}
      <div className="space-y-3">
        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={chat.showTimestamps}
            onChange={toggleTimestamps}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">Show message timestamps</span>
        </label>

        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={chat.enableTypingIndicator}
            onChange={toggleTypingIndicator}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">Show typing indicator</span>
        </label>

        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={chat.autoScroll}
            onChange={toggleAutoScroll}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">Auto-scroll to new messages</span>
        </label>
      </div>

      {/* Font Size */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">Font Size</label>
        <select
          value={chat.fontSize}
          onChange={(e) => setFontSize(e.target.value as any)}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
        >
          <option value="small">Small</option>
          <option value="medium">Medium</option>
          <option value="large">Large</option>
        </select>
      </div>

      {/* Message Retention */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">
          Message Retention: {chat.messageRetention} days
        </label>
        <input
          type="range"
          min="1"
          max="365"
          value={chat.messageRetention}
          onChange={(e) => setMessageRetention(Number(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
      </div>
    </div>
  );
};

// Notification Settings Panel
const NotificationSettings: React.FC = () => {
  const { notifications, setNotificationSetting } = useSettingsStore();

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-white">Notification Settings</h3>

      <div className="space-y-3">
        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={notifications.chatMessages}
            onChange={(e) => setNotificationSetting('chatMessages', e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">Chat message notifications</span>
        </label>

        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={notifications.assistantActions}
            onChange={(e) => setNotificationSetting('assistantActions', e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">Assistant action notifications</span>
        </label>

        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={notifications.systemAlerts}
            onChange={(e) => setNotificationSetting('systemAlerts', e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">System alert notifications</span>
        </label>

        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={notifications.soundEnabled}
            onChange={(e) => setNotificationSetting('soundEnabled', e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">Sound notifications</span>
        </label>
      </div>
    </div>
  );
};

// Debug Settings Panel
const DebugSettings: React.FC = () => {
  const {
    debugMode,
    showDebugPanel,
    logLevel,
    toggleDebugMode,
    toggleDebugPanel,
    setLogLevel,
  } = useSettingsStore();

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-white">Debug Settings</h3>

      <div className="bg-yellow-900/20 border border-yellow-600/50 rounded-lg p-4">
        <p className="text-yellow-200 text-sm">
          ⚠️ Debug settings are for development purposes. Enable only if you know what you're doing.
        </p>
      </div>

      <div className="space-y-3">
        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={debugMode}
            onChange={toggleDebugMode}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">Enable debug mode</span>
        </label>

        <label className="flex items-center space-x-3">
          <input
            type="checkbox"
            checked={showDebugPanel}
            onChange={toggleDebugPanel}
            className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
          />
          <span className="text-gray-300">Show debug panel</span>
        </label>
      </div>

      {/* Log Level */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">Log Level</label>
        <select
          value={logLevel}
          onChange={(e) => setLogLevel(e.target.value as any)}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
        >
          <option value="error">Error</option>
          <option value="warn">Warning</option>
          <option value="info">Info</option>
          <option value="debug">Debug</option>
        </select>
      </div>
    </div>
  );
};

export default SettingsPanel;