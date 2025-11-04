/**
 * Main App component for DeskMate - Phase 12B Multi-Device System
 *
 * Features:
 * - Responsive layouts for desktop/tablet/mobile
 * - Multi-room floor plan system with top-down rendering
 * - Touch gesture support and accessibility features
 * - Real-time room navigation and pathfinding
 */

import React, { useEffect } from 'react';
import { usePersonaStore } from './stores/personaStore';
import ResponsiveLayout from './components/Layout/ResponsiveLayout';
import SettingsPanel from './components/Settings/SettingsPanel';
import PerformanceMonitor from './components/PerformanceMonitor';

const App: React.FC = () => {
  const { loadPersonas } = usePersonaStore();

  // Initialize persona store on app load
  useEffect(() => {
    loadPersonas();
  }, [loadPersonas]);

  return (
    <div className="app-container w-full h-screen overflow-hidden">
      {/* Main responsive layout system */}
      <ResponsiveLayout />

      {/* Global overlays that work across all layouts */}
      <SettingsPanel />
      <PerformanceMonitor />
    </div>
  );
};

export default App;