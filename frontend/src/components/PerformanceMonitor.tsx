/**
 * Performance Monitor Component - Real-time performance metrics and FPS counter
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSettingsStore } from '../stores/settingsStore';

interface PerformanceMetrics {
  fps: number;
  memoryUsage: number;
  renderTime: number;
  frameTimes: number[];
  timestamp: number;
}

interface PerformanceMonitorProps {
  className?: string;
}

const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({ className = "" }) => {
  const { display } = useSettingsStore();
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 0,
    memoryUsage: 0,
    renderTime: 0,
    frameTimes: [],
    timestamp: Date.now()
  });

  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(performance.now());
  const frameTimesRef = useRef<number[]>([]);
  const animationFrameRef = useRef<number>();

  // Performance tracking
  const trackFrame = useCallback(() => {
    const now = performance.now();
    const deltaTime = now - lastTimeRef.current;

    frameCountRef.current++;
    frameTimesRef.current.push(deltaTime);

    // Keep only last 60 frames for rolling average
    if (frameTimesRef.current.length > 60) {
      frameTimesRef.current.shift();
    }

    // Update metrics every 30 frames (roughly 0.5 seconds at 60fps)
    if (frameCountRef.current % 30 === 0) {
      const avgFrameTime = frameTimesRef.current.reduce((a, b) => a + b, 0) / frameTimesRef.current.length;
      const fps = 1000 / avgFrameTime;

      // Memory usage (if available)
      let memoryUsage = 0;
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        memoryUsage = memory.usedJSHeapSize / (1024 * 1024); // Convert to MB
      }

      setMetrics({
        fps: Math.round(fps * 10) / 10,
        memoryUsage: Math.round(memoryUsage * 10) / 10,
        renderTime: Math.round(avgFrameTime * 100) / 100,
        frameTimes: [...frameTimesRef.current],
        timestamp: Date.now()
      });
    }

    lastTimeRef.current = now;
    animationFrameRef.current = requestAnimationFrame(trackFrame);
  }, []);

  useEffect(() => {
    if (display.showFPS || display.showPerformanceMetrics) {
      animationFrameRef.current = requestAnimationFrame(trackFrame);
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [display.showFPS, display.showPerformanceMetrics, trackFrame]);

  const getPerformanceStatus = (fps: number) => {
    if (fps >= 55) return { color: 'text-green-400', status: 'Excellent' };
    if (fps >= 45) return { color: 'text-yellow-400', status: 'Good' };
    if (fps >= 30) return { color: 'text-orange-400', status: 'Fair' };
    return { color: 'text-red-400', status: 'Poor' };
  };

  const getMemoryStatus = (memory: number) => {
    if (memory < 50) return { color: 'text-green-400', status: 'Low' };
    if (memory < 100) return { color: 'text-yellow-400', status: 'Medium' };
    if (memory < 200) return { color: 'text-orange-400', status: 'High' };
    return { color: 'text-red-400', status: 'Critical' };
  };

  const renderMiniGraph = (values: number[], color: string) => {
    const maxValue = Math.max(...values, 1);
    const minValue = Math.min(...values, 0);
    const range = maxValue - minValue || 1;

    return (
      <div className="flex items-end h-8 space-x-0.5">
        {values.slice(-20).map((value, index) => {
          const height = ((value - minValue) / range) * 100;
          return (
            <div
              key={index}
              className={`w-1 ${color} opacity-60`}
              style={{ height: `${Math.max(height, 2)}%` }}
            />
          );
        })}
      </div>
    );
  };

  if (!display.showFPS && !display.showPerformanceMetrics) {
    return null;
  }

  const performanceStatus = getPerformanceStatus(metrics.fps);
  const memoryStatus = getMemoryStatus(metrics.memoryUsage);

  return (
    <div className={`performance-monitor ${className}`}>
      {/* FPS Counter */}
      {display.showFPS && (
        <div className="fixed top-4 left-4 z-40 bg-black/75 backdrop-blur text-white p-2 rounded text-sm font-mono">
          <div className="flex items-center space-x-2">
            <span className={performanceStatus.color}>●</span>
            <span>{metrics.fps} FPS</span>
          </div>
        </div>
      )}

      {/* Detailed Performance Metrics */}
      {display.showPerformanceMetrics && (
        <div className="fixed top-4 right-4 z-40 bg-black/90 backdrop-blur text-white p-4 rounded-lg text-sm font-mono min-w-64">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-white">Performance Monitor</h3>
            <div className={`w-2 h-2 rounded-full ${performanceStatus.color}`} />
          </div>

          <div className="space-y-3">
            {/* FPS */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-gray-300">FPS</span>
                <span className={performanceStatus.color}>
                  {metrics.fps} ({performanceStatus.status})
                </span>
              </div>
              {renderMiniGraph(
                metrics.frameTimes.map(t => 1000 / t),
                'bg-green-400'
              )}
            </div>

            {/* Frame Time */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-gray-300">Frame Time</span>
                <span className="text-white">{metrics.renderTime}ms</span>
              </div>
              {renderMiniGraph(metrics.frameTimes, 'bg-blue-400')}
            </div>

            {/* Memory Usage */}
            {metrics.memoryUsage > 0 && (
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-gray-300">Memory</span>
                  <span className={memoryStatus.color}>
                    {metrics.memoryUsage}MB ({memoryStatus.status})
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      memoryStatus.status === 'Critical' ? 'bg-red-400' :
                      memoryStatus.status === 'High' ? 'bg-orange-400' :
                      memoryStatus.status === 'Medium' ? 'bg-yellow-400' :
                      'bg-green-400'
                    }`}
                    style={{ width: `${Math.min((metrics.memoryUsage / 200) * 100, 100)}%` }}
                  />
                </div>
              </div>
            )}

            {/* System Info */}
            <div className="pt-2 border-t border-gray-700 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-400">Browser:</span>
                <span className="text-gray-300">{navigator.userAgent.split(' ')[0]}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Platform:</span>
                <span className="text-gray-300">{navigator.platform}</span>
              </div>
              {navigator.hardwareConcurrency && (
                <div className="flex justify-between">
                  <span className="text-gray-400">CPU Cores:</span>
                  <span className="text-gray-300">{navigator.hardwareConcurrency}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceMonitor;