/**
 * Theme Context Provider - Manages application theme state and switching
 */

import React, { createContext, useContext, useEffect } from 'react';
import { useSettingsStore } from '../stores/settingsStore';

interface ThemeContextType {
  theme: 'dark' | 'light' | 'auto';
  resolvedTheme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light' | 'auto') => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const { display, setTheme: setSettingsTheme } = useSettingsStore();
  const { theme } = display;

  // Resolve 'auto' theme to actual theme based on system preference
  const getResolvedTheme = (): 'dark' | 'light' => {
    if (theme === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return theme;
  };

  const resolvedTheme = getResolvedTheme();

  // Apply theme to document root
  useEffect(() => {
    const root = document.documentElement;

    // Remove existing theme classes
    root.classList.remove('theme-dark', 'theme-light');

    // Add current theme class
    root.classList.add(`theme-${resolvedTheme}`);

    // Update CSS custom properties
    if (resolvedTheme === 'dark') {
      root.style.setProperty('--bg-primary', '#111827');
      root.style.setProperty('--bg-secondary', '#1f2937');
      root.style.setProperty('--bg-tertiary', '#374151');
      root.style.setProperty('--text-primary', '#f9fafb');
      root.style.setProperty('--text-secondary', '#d1d5db');
      root.style.setProperty('--text-tertiary', '#9ca3af');
      root.style.setProperty('--border-primary', '#4b5563');
      root.style.setProperty('--border-secondary', '#6b7280');
      root.style.setProperty('--accent-primary', '#3b82f6');
      root.style.setProperty('--accent-secondary', '#1d4ed8');
    } else {
      root.style.setProperty('--bg-primary', '#ffffff');
      root.style.setProperty('--bg-secondary', '#f9fafb');
      root.style.setProperty('--bg-tertiary', '#f3f4f6');
      root.style.setProperty('--text-primary', '#111827');
      root.style.setProperty('--text-secondary', '#374151');
      root.style.setProperty('--text-tertiary', '#6b7280');
      root.style.setProperty('--border-primary', '#d1d5db');
      root.style.setProperty('--border-secondary', '#9ca3af');
      root.style.setProperty('--accent-primary', '#3b82f6');
      root.style.setProperty('--accent-secondary', '#1d4ed8');
    }
  }, [resolvedTheme]);

  // Listen for system theme changes when in auto mode
  useEffect(() => {
    if (theme === 'auto') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

      const handleChange = () => {
        // Force re-render to update resolved theme
        setSettingsTheme('auto');
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [theme, setSettingsTheme]);

  const contextValue: ThemeContextType = {
    theme,
    resolvedTheme,
    setTheme: setSettingsTheme,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

export default ThemeProvider;