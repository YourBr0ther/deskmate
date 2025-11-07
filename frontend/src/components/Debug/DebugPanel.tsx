/**
 * Advanced debug panel with tabs for logs, state, performance, and network monitoring
 */

import React, { useState, useEffect, useRef } from 'react';

import { useChatStore } from '../../stores/chatStore';
import { usePersonaStore } from '../../stores/personaStore';
import { useRoomStore } from '../../stores/roomStore';
import { useSettingsStore } from '../../stores/settingsStore';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  source?: string;
}

interface NetworkRequest {
  id: string;
  timestamp: string;
  method: string;
  url: string;
  status?: number;
  duration?: number;
  size?: number;
}

type DebugTab = 'logs' | 'state' | 'performance' | 'network';

export const DebugPanel: React.FC = () => {
  const { showDebugPanel, logLevel } = useSettingsStore();
  const [activeTab, setActiveTab] = useState<DebugTab>('logs');
  const [position, setPosition] = useState({ x: 50, y: 50 });
  const [isDragging, setIsDragging] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [networkRequests, setNetworkRequests] = useState<NetworkRequest[]>([]);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  const panelRef = useRef<HTMLDivElement>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Capture console logs
  useEffect(() => {
    if (!showDebugPanel) return;

    const originalConsole = {
      debug: console.debug,
      info: console.info,
      warn: console.warn,
      error: console.error,
      log: console.log
    };

    const captureLog = (level: LogEntry['level'], args: any[]) => {
      const message = args.map(arg =>
        typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
      ).join(' ');

      const logEntry: LogEntry = {
        id: Math.random().toString(36).substr(2, 9),
        timestamp: new Date().toISOString(),
        level,
        message,
        source: 'console'
      };

      setLogs(prev => [...prev.slice(-99), logEntry]); // Keep last 100 logs
    };

    // Override console methods
    console.debug = (...args) => {
      originalConsole.debug(...args);
      if (logLevel === 'debug') captureLog('debug', args);
    };
    console.info = (...args) => {
      originalConsole.info(...args);
      if (['debug', 'info'].includes(logLevel)) captureLog('info', args);
    };
    console.warn = (...args) => {
      originalConsole.warn(...args);
      if (['debug', 'info', 'warn'].includes(logLevel)) captureLog('warn', args);
    };
    console.error = (...args) => {
      originalConsole.error(...args);
      captureLog('error', args);
    };
    console.log = (...args) => {
      originalConsole.log(...args);
      if (['debug', 'info'].includes(logLevel)) captureLog('info', args);
    };

    return () => {
      // Restore original console methods
      Object.assign(console, originalConsole);
    };
  }, [showDebugPanel, logLevel]);

  // Auto-scroll logs
  useEffect(() => {
    if (logContainerRef.current && activeTab === 'logs') {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, activeTab]);

  // Drag handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (panelRef.current) {
      const rect = panelRef.current.getBoundingClientRect();
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
      setIsDragging(true);
    }
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragOffset.x,
        y: e.clientY - dragOffset.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragOffset]);

  // State inspection
  const chatState = useChatStore();
  const personaState = usePersonaStore();
  const roomState = useRoomStore();
  const settingsState = useSettingsStore();

  const stateData = {
    chat: {
      messageCount: chatState.messages.length,
      isConnected: chatState.isConnected,
      isTyping: chatState.isTyping,
      currentModel: chatState.currentModel,
      currentProvider: chatState.currentProvider
    },
    persona: {
      selectedPersona: personaState.selectedPersona?.persona.data.name || null,
      availablePersonas: personaState.personas.length
    },
    room: {
      assistantPosition: roomState.assistant.position,
      assistantStatus: roomState.assistant.status,
      assistantMood: roomState.assistant.mood,
      objectCount: roomState.objects.length
    },
    settings: {
      theme: settingsState.display.theme,
      debugMode: settingsState.debugMode,
      highQualityRendering: settingsState.display.highQualityRendering
    }
  };

  if (!showDebugPanel) return null;

  const renderTabContent = () => {
    switch (activeTab) {
      case 'logs':
        return (
          <div ref={logContainerRef} className="h-64 overflow-y-auto space-y-1">
            {logs.length === 0 ? (
              <div className="text-gray-400 text-center py-8">No logs captured yet</div>
            ) : (
              logs.map(log => (
                <div
                  key={log.id}
                  className={`text-xs p-2 rounded ${
                    log.level === 'error' ? 'bg-red-900 text-red-100' :
                    log.level === 'warn' ? 'bg-yellow-900 text-yellow-100' :
                    log.level === 'info' ? 'bg-blue-900 text-blue-100' :
                    'bg-gray-800 text-gray-300'
                  }`}
                >
                  <div className="font-mono text-xs opacity-70">
                    {new Date(log.timestamp).toLocaleTimeString()} [{log.level.toUpperCase()}]
                  </div>
                  <div className="mt-1 whitespace-pre-wrap">{log.message}</div>
                </div>
              ))
            )}
          </div>
        );

      case 'state':
        return (
          <div className="h-64 overflow-y-auto">
            <div className="space-y-4">
              {Object.entries(stateData).map(([category, data]) => (
                <div key={category} className="border border-gray-600 rounded p-3">
                  <h4 className="font-semibold text-yellow-400 mb-2">{category.charAt(0).toUpperCase() + category.slice(1)}</h4>
                  <pre className="text-xs text-gray-300 overflow-x-auto">
                    {JSON.stringify(data, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        );

      case 'performance':
        return (
          <div className="h-64 overflow-y-auto space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800 p-3 rounded">
                <h4 className="text-yellow-400 font-semibold mb-2">Memory</h4>
                <div className="text-sm">
                  <div>Heap Used: {((performance as any).memory?.usedJSHeapSize / 1024 / 1024)?.toFixed(1) || 'N/A'} MB</div>
                  <div>Heap Limit: {((performance as any).memory?.jsHeapSizeLimit / 1024 / 1024)?.toFixed(1) || 'N/A'} MB</div>
                </div>
              </div>
              <div className="bg-gray-800 p-3 rounded">
                <h4 className="text-yellow-400 font-semibold mb-2">Timing</h4>
                <div className="text-sm">
                  <div>Navigation: {performance.timing.loadEventEnd - performance.timing.navigationStart}ms</div>
                  <div>DOM Ready: {performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart}ms</div>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-3 rounded">
              <h4 className="text-yellow-400 font-semibold mb-2">DOM Metrics</h4>
              <div className="text-sm grid grid-cols-2 gap-2">
                <div>Elements: {document.querySelectorAll('*').length}</div>
                <div>Event Listeners: {document.querySelectorAll('[onclick], [onchange], [onkeydown], [onmousedown]').length}</div>
              </div>
            </div>
          </div>
        );

      case 'network':
        return (
          <div className="h-64 overflow-y-auto">
            <div className="text-center text-gray-400 py-8">
              <div>Network monitoring coming soon</div>
              <div className="text-xs mt-2">Will track WebSocket connections and API calls</div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div
      ref={panelRef}
      className="fixed bg-gray-900 text-white rounded-lg shadow-xl border border-gray-600 z-50 w-96"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        cursor: isDragging ? 'grabbing' : 'grab'
      }}
      onMouseDown={handleMouseDown}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-600 bg-gray-800 rounded-t-lg">
        <h3 className="font-bold text-green-400">🔧 Debug Panel</h3>
        <button
          onClick={() => useSettingsStore.getState().toggleDebugPanel()}
          className="text-gray-400 hover:text-white"
          title="Close debug panel"
        >
          ✕
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-600">
        {(['logs', 'state', 'performance', 'network'] as DebugTab[]).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium capitalize ${
              activeTab === tab
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-3">
        {renderTabContent()}
      </div>

      {/* Footer */}
      <div className="p-2 bg-gray-800 rounded-b-lg border-t border-gray-600">
        <div className="flex justify-between items-center text-xs text-gray-400">
          <span>Log Level: {logLevel}</span>
          <button
            onClick={() => setLogs([])}
            className="text-red-400 hover:text-red-300"
          >
            Clear Logs
          </button>
        </div>
      </div>
    </div>
  );
};

export default DebugPanel;