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
import ErrorBoundary from './components/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';
import './styles/themes.css';

const App: React.FC = () => {
  const { loadPersonas } = usePersonaStore();

  // Initialize persona store on app load
  useEffect(() => {
    loadPersonas();
  }, [loadPersonas]);

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Could send to error tracking service here
        console.error('Application error:', error, errorInfo);
      }}
      resetOnPropsChange={false}
    >
      <ThemeProvider>
        <div className="app-container w-full h-screen overflow-hidden bg-themed-primary text-themed-primary">
          {/* Main responsive layout system */}
          <ResponsiveLayout />

          {/* Global overlays that work across all layouts */}
          <SettingsPanel />
          <PerformanceMonitor />
        </div>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;