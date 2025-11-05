/**
 * Debug overlay component for development and troubleshooting
 */

import React, { useState, useEffect } from 'react';
import { useSettingsStore } from '../../stores/settingsStore';
import { useChatStore } from '../../stores/chatStore';
import { usePersonaStore } from '../../stores/personaStore';
import { useRoomStore } from '../../stores/roomStore';

interface PerformanceStats {
  fps: number;
  memoryUsage?: number;
  renderTime: number;
  componentCount: number;
}

export const DebugOverlay: React.FC = () => {
  const { debugMode } = useSettingsStore();
  const { messages, isConnected, isTyping, currentModel } = useChatStore();
  const { selectedPersona } = usePersonaStore();
  const { assistant } = useRoomStore();

  const [performanceStats, setPerformanceStats] = useState<PerformanceStats>({
    fps: 0,
    renderTime: 0,
    componentCount: 0
  });

  const [isVisible, setIsVisible] = useState(debugMode);

  // Show/hide based on debug mode setting
  useEffect(() => {
    setIsVisible(debugMode);
  }, [debugMode]);

  // Performance monitoring
  useEffect(() => {
    if (!debugMode) return;

    const startTime = performance.now();
    let frameCount = 0;
    let lastTime = startTime;

    const measurePerformance = () => {
      const currentTime = performance.now();
      frameCount++;

      // Calculate FPS every second
      if (currentTime - lastTime >= 1000) {
        const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
        const renderTime = currentTime - startTime;

        setPerformanceStats(prev => ({
          ...prev,
          fps,
          renderTime: Math.round(renderTime),
          componentCount: document.querySelectorAll('[data-react-component]').length || 0,
          memoryUsage: (performance as any).memory?.usedJSHeapSize
            ? Math.round((performance as any).memory.usedJSHeapSize / 1024 / 1024)
            : undefined
        }));

        frameCount = 0;
        lastTime = currentTime;
      }

      if (debugMode) {
        requestAnimationFrame(measurePerformance);
      }
    };

    const animationFrame = requestAnimationFrame(measurePerformance);

    return () => {
      cancelAnimationFrame(animationFrame);
    };
  }, [debugMode]);

  if (!isVisible) return null;

  return (
    <div className="fixed top-4 right-4 bg-black bg-opacity-90 text-white text-xs p-4 rounded-lg shadow-lg z-50 max-w-sm">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-bold text-green-400">🐛 Debug Info</h3>
        <button
          onClick={() => setIsVisible(false)}
          className="text-gray-400 hover:text-white"
          title="Hide debug overlay"
        >
          ✕
        </button>
      </div>

      <div className="space-y-2">
        {/* Performance Stats */}
        <div className="border-b border-gray-700 pb-2">
          <div className="text-yellow-400 font-semibold">Performance</div>
          <div>FPS: <span className="text-green-300">{performanceStats.fps}</span></div>
          <div>Render Time: <span className="text-green-300">{performanceStats.renderTime}ms</span></div>
          <div>Components: <span className="text-green-300">{performanceStats.componentCount}</span></div>
          {performanceStats.memoryUsage && (
            <div>Memory: <span className="text-green-300">{performanceStats.memoryUsage}MB</span></div>
          )}
        </div>

        {/* Chat State */}
        <div className="border-b border-gray-700 pb-2">
          <div className="text-yellow-400 font-semibold">Chat State</div>
          <div>Connected: <span className={isConnected ? "text-green-300" : "text-red-300"}>{isConnected ? "Yes" : "No"}</span></div>
          <div>Typing: <span className={isTyping ? "text-yellow-300" : "text-gray-400"}>{isTyping ? "Yes" : "No"}</span></div>
          <div>Messages: <span className="text-green-300">{messages.length}</span></div>
          <div>Model: <span className="text-blue-300">{currentModel}</span></div>
        </div>

        {/* Persona State */}
        <div className="border-b border-gray-700 pb-2">
          <div className="text-yellow-400 font-semibold">Persona</div>
          <div>Selected: <span className="text-green-300">{selectedPersona?.persona.data.name || "None"}</span></div>
          {selectedPersona && (
            <div>Creator: <span className="text-blue-300">{selectedPersona.persona.data.creator || "Unknown"}</span></div>
          )}
        </div>

        {/* Assistant State */}
        <div className="border-b border-gray-700 pb-2">
          <div className="text-yellow-400 font-semibold">Assistant</div>
          <div>Position: <span className="text-green-300">({Math.round(assistant.position.x)}, {Math.round(assistant.position.y)})</span></div>
          <div>Status: <span className="text-blue-300">{assistant.status}</span></div>
          <div>Mood: <span className="text-purple-300">{assistant.mood}</span></div>
          <div>Action: <span className="text-orange-300">{assistant.currentAction || "idle"}</span></div>
          <div>Moving: <span className={assistant.isMoving ? "text-yellow-300" : "text-gray-300"}>{assistant.isMoving ? "Yes" : "No"}</span></div>
          {assistant.holding_object_id && (
            <div>Holding: <span className="text-yellow-300">{assistant.holding_object_id}</span></div>
          )}
        </div>

        {/* Browser Info */}
        <div>
          <div className="text-yellow-400 font-semibold">Browser</div>
          <div>User Agent: <span className="text-gray-300 truncate block">{navigator.userAgent.split(' ')[0]}</span></div>
          <div>Viewport: <span className="text-green-300">{window.innerWidth}x{window.innerHeight}</span></div>
          <div>Pixel Ratio: <span className="text-green-300">{window.devicePixelRatio}</span></div>
        </div>
      </div>
    </div>
  );
};

export default DebugOverlay;