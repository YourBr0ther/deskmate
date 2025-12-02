/**
 * Tests for Settings Store
 *
 * Tests cover:
 * - Initial state
 * - Display settings
 * - LLM settings
 * - Chat settings
 * - Notification settings
 * - Debug settings
 * - Reset functions
 * - Settings panel controls
 */

import { act } from '@testing-library/react';
import { useSettingsStore } from '../settingsStore';

// Mock localStorage for persistence
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('SettingsStore', () => {
  beforeEach(() => {
    localStorageMock.clear();
    // Reset store to defaults
    act(() => {
      useSettingsStore.getState().resetAllSettings();
      useSettingsStore.setState({ isSettingsOpen: false, activeSettingsTab: 'display' });
    });
  });

  // ========================================================================
  // Initial State Tests
  // ========================================================================

  describe('Initial State', () => {
    it('should have correct default display settings', () => {
      const state = useSettingsStore.getState();

      expect(state.display.theme).toBe('dark');
      expect(state.display.gridDisplayMode).toBe('normal');
      expect(state.display.showFPS).toBe(false);
      expect(state.display.animationsEnabled).toBe(true);
      expect(state.display.panelTransparency).toBe(90);
    });

    it('should have correct default LLM settings', () => {
      const state = useSettingsStore.getState();

      expect(state.llm.defaultProvider).toBe('nano-gpt');
      expect(state.llm.defaultModel).toBe('gpt-4o-mini');
      expect(state.llm.autoSelectModel).toBe(true);
      expect(state.llm.maxTokens).toBe(2000);
      expect(state.llm.temperature).toBe(0.7);
    });

    it('should have correct default chat settings', () => {
      const state = useSettingsStore.getState();

      expect(state.chat.showTimestamps).toBe(true);
      expect(state.chat.enableTypingIndicator).toBe(true);
      expect(state.chat.messageRetention).toBe(30);
      expect(state.chat.autoScroll).toBe(true);
      expect(state.chat.fontSize).toBe('medium');
    });

    it('should have correct default notification settings', () => {
      const state = useSettingsStore.getState();

      expect(state.notifications.chatMessages).toBe(true);
      expect(state.notifications.assistantActions).toBe(true);
      expect(state.notifications.systemAlerts).toBe(true);
      expect(state.notifications.soundEnabled).toBe(false);
    });

    it('should have settings panel closed by default', () => {
      const state = useSettingsStore.getState();

      expect(state.isSettingsOpen).toBe(false);
      expect(state.activeSettingsTab).toBe('display');
    });
  });

  // ========================================================================
  // Settings Panel Control Tests
  // ========================================================================

  describe('Settings Panel Controls', () => {
    it('should open settings panel', () => {
      act(() => {
        useSettingsStore.getState().openSettings();
      });

      expect(useSettingsStore.getState().isSettingsOpen).toBe(true);
    });

    it('should close settings panel', () => {
      act(() => {
        useSettingsStore.getState().openSettings();
        useSettingsStore.getState().closeSettings();
      });

      expect(useSettingsStore.getState().isSettingsOpen).toBe(false);
    });

    it('should set active tab', () => {
      act(() => {
        useSettingsStore.getState().setActiveTab('llm');
      });

      expect(useSettingsStore.getState().activeSettingsTab).toBe('llm');
    });
  });

  // ========================================================================
  // Display Settings Tests
  // ========================================================================

  describe('Display Settings', () => {
    it('should set theme', () => {
      act(() => {
        useSettingsStore.getState().setTheme('light');
      });

      expect(useSettingsStore.getState().display.theme).toBe('light');
    });

    it('should set grid display mode', () => {
      act(() => {
        useSettingsStore.getState().setGridDisplayMode('compact');
      });

      expect(useSettingsStore.getState().display.gridDisplayMode).toBe('compact');
    });

    it('should toggle FPS display', () => {
      const initial = useSettingsStore.getState().display.showFPS;

      act(() => {
        useSettingsStore.getState().toggleFPS();
      });

      expect(useSettingsStore.getState().display.showFPS).toBe(!initial);
    });

    it('should toggle performance metrics', () => {
      const initial = useSettingsStore.getState().display.showPerformanceMetrics;

      act(() => {
        useSettingsStore.getState().togglePerformanceMetrics();
      });

      expect(useSettingsStore.getState().display.showPerformanceMetrics).toBe(!initial);
    });

    it('should toggle animations', () => {
      const initial = useSettingsStore.getState().display.animationsEnabled;

      act(() => {
        useSettingsStore.getState().toggleAnimations();
      });

      expect(useSettingsStore.getState().display.animationsEnabled).toBe(!initial);
    });

    it('should set high quality rendering', () => {
      act(() => {
        useSettingsStore.getState().setHighQualityRendering(false);
      });

      expect(useSettingsStore.getState().display.highQualityRendering).toBe(false);
    });

    it('should set panel transparency within bounds', () => {
      act(() => {
        useSettingsStore.getState().setPanelTransparency(75);
      });

      expect(useSettingsStore.getState().display.panelTransparency).toBe(75);
    });

    it('should clamp panel transparency to 0-100', () => {
      act(() => {
        useSettingsStore.getState().setPanelTransparency(150);
      });

      expect(useSettingsStore.getState().display.panelTransparency).toBe(100);

      act(() => {
        useSettingsStore.getState().setPanelTransparency(-10);
      });

      expect(useSettingsStore.getState().display.panelTransparency).toBe(0);
    });
  });

  // ========================================================================
  // LLM Settings Tests
  // ========================================================================

  describe('LLM Settings', () => {
    it('should set default provider', () => {
      act(() => {
        useSettingsStore.getState().setDefaultProvider('ollama');
      });

      expect(useSettingsStore.getState().llm.defaultProvider).toBe('ollama');
    });

    it('should set default model', () => {
      act(() => {
        useSettingsStore.getState().setDefaultModel('llama3:latest');
      });

      expect(useSettingsStore.getState().llm.defaultModel).toBe('llama3:latest');
    });

    it('should set auto select model', () => {
      act(() => {
        useSettingsStore.getState().setAutoSelectModel(false);
      });

      expect(useSettingsStore.getState().llm.autoSelectModel).toBe(false);
    });

    it('should set max tokens within bounds', () => {
      act(() => {
        useSettingsStore.getState().setMaxTokens(4000);
      });

      expect(useSettingsStore.getState().llm.maxTokens).toBe(4000);
    });

    it('should clamp max tokens to 100-8000', () => {
      act(() => {
        useSettingsStore.getState().setMaxTokens(50);
      });

      expect(useSettingsStore.getState().llm.maxTokens).toBe(100);

      act(() => {
        useSettingsStore.getState().setMaxTokens(10000);
      });

      expect(useSettingsStore.getState().llm.maxTokens).toBe(8000);
    });

    it('should set temperature within bounds', () => {
      act(() => {
        useSettingsStore.getState().setTemperature(1.5);
      });

      expect(useSettingsStore.getState().llm.temperature).toBe(1.5);
    });

    it('should clamp temperature to 0-2', () => {
      act(() => {
        useSettingsStore.getState().setTemperature(-0.5);
      });

      expect(useSettingsStore.getState().llm.temperature).toBe(0);

      act(() => {
        useSettingsStore.getState().setTemperature(3);
      });

      expect(useSettingsStore.getState().llm.temperature).toBe(2);
    });
  });

  // ========================================================================
  // Chat Settings Tests
  // ========================================================================

  describe('Chat Settings', () => {
    it('should toggle timestamps', () => {
      const initial = useSettingsStore.getState().chat.showTimestamps;

      act(() => {
        useSettingsStore.getState().toggleTimestamps();
      });

      expect(useSettingsStore.getState().chat.showTimestamps).toBe(!initial);
    });

    it('should toggle typing indicator', () => {
      const initial = useSettingsStore.getState().chat.enableTypingIndicator;

      act(() => {
        useSettingsStore.getState().toggleTypingIndicator();
      });

      expect(useSettingsStore.getState().chat.enableTypingIndicator).toBe(!initial);
    });

    it('should set message retention', () => {
      act(() => {
        useSettingsStore.getState().setMessageRetention(60);
      });

      expect(useSettingsStore.getState().chat.messageRetention).toBe(60);
    });

    it('should clamp message retention to 1-365 days', () => {
      act(() => {
        useSettingsStore.getState().setMessageRetention(0);
      });

      expect(useSettingsStore.getState().chat.messageRetention).toBe(1);

      act(() => {
        useSettingsStore.getState().setMessageRetention(500);
      });

      expect(useSettingsStore.getState().chat.messageRetention).toBe(365);
    });

    it('should toggle auto scroll', () => {
      const initial = useSettingsStore.getState().chat.autoScroll;

      act(() => {
        useSettingsStore.getState().toggleAutoScroll();
      });

      expect(useSettingsStore.getState().chat.autoScroll).toBe(!initial);
    });

    it('should set font size', () => {
      act(() => {
        useSettingsStore.getState().setFontSize('large');
      });

      expect(useSettingsStore.getState().chat.fontSize).toBe('large');
    });
  });

  // ========================================================================
  // Notification Settings Tests
  // ========================================================================

  describe('Notification Settings', () => {
    it('should set notification settings', () => {
      act(() => {
        useSettingsStore.getState().setNotificationSetting('chatMessages', false);
      });

      expect(useSettingsStore.getState().notifications.chatMessages).toBe(false);
    });

    it('should enable sound', () => {
      act(() => {
        useSettingsStore.getState().setNotificationSetting('soundEnabled', true);
      });

      expect(useSettingsStore.getState().notifications.soundEnabled).toBe(true);
    });

    it('should disable assistant actions notifications', () => {
      act(() => {
        useSettingsStore.getState().setNotificationSetting('assistantActions', false);
      });

      expect(useSettingsStore.getState().notifications.assistantActions).toBe(false);
    });
  });

  // ========================================================================
  // Debug Settings Tests
  // ========================================================================

  describe('Debug Settings', () => {
    it('should toggle debug mode', () => {
      const initial = useSettingsStore.getState().debugMode;

      act(() => {
        useSettingsStore.getState().toggleDebugMode();
      });

      expect(useSettingsStore.getState().debugMode).toBe(!initial);
    });

    it('should toggle debug panel', () => {
      const initial = useSettingsStore.getState().showDebugPanel;

      act(() => {
        useSettingsStore.getState().toggleDebugPanel();
      });

      expect(useSettingsStore.getState().showDebugPanel).toBe(!initial);
    });

    it('should set log level', () => {
      act(() => {
        useSettingsStore.getState().setLogLevel('debug');
      });

      expect(useSettingsStore.getState().logLevel).toBe('debug');
    });
  });

  // ========================================================================
  // Reset Functions Tests
  // ========================================================================

  describe('Reset Functions', () => {
    it('should reset display settings', () => {
      // Modify settings
      act(() => {
        useSettingsStore.getState().setTheme('light');
        useSettingsStore.getState().toggleFPS();
        useSettingsStore.getState().setPanelTransparency(50);
      });

      // Reset
      act(() => {
        useSettingsStore.getState().resetDisplaySettings();
      });

      const state = useSettingsStore.getState();
      expect(state.display.theme).toBe('dark');
      expect(state.display.showFPS).toBe(false);
      expect(state.display.panelTransparency).toBe(90);
    });

    it('should reset LLM settings', () => {
      // Modify settings
      act(() => {
        useSettingsStore.getState().setDefaultProvider('ollama');
        useSettingsStore.getState().setTemperature(1.5);
      });

      // Reset
      act(() => {
        useSettingsStore.getState().resetLLMSettings();
      });

      const state = useSettingsStore.getState();
      expect(state.llm.defaultProvider).toBe('nano-gpt');
      expect(state.llm.temperature).toBe(0.7);
    });

    it('should reset chat settings', () => {
      // Modify settings
      act(() => {
        useSettingsStore.getState().toggleTimestamps();
        useSettingsStore.getState().setFontSize('large');
      });

      // Reset
      act(() => {
        useSettingsStore.getState().resetChatSettings();
      });

      const state = useSettingsStore.getState();
      expect(state.chat.showTimestamps).toBe(true);
      expect(state.chat.fontSize).toBe('medium');
    });

    it('should reset all settings', () => {
      // Modify various settings
      act(() => {
        useSettingsStore.getState().setTheme('light');
        useSettingsStore.getState().setDefaultProvider('ollama');
        useSettingsStore.getState().toggleTimestamps();
        useSettingsStore.getState().toggleDebugMode();
      });

      // Reset all
      act(() => {
        useSettingsStore.getState().resetAllSettings();
      });

      const state = useSettingsStore.getState();
      expect(state.display.theme).toBe('dark');
      expect(state.llm.defaultProvider).toBe('nano-gpt');
      expect(state.chat.showTimestamps).toBe(true);
      expect(state.debugMode).toBe(false);
    });
  });

  // ========================================================================
  // Multiple Settings Changes Tests
  // ========================================================================

  describe('Multiple Settings Changes', () => {
    it('should handle rapid setting changes', () => {
      act(() => {
        useSettingsStore.getState().setTheme('light');
        useSettingsStore.getState().setTheme('dark');
        useSettingsStore.getState().setTheme('auto');
      });

      expect(useSettingsStore.getState().display.theme).toBe('auto');
    });

    it('should preserve other settings when changing one', () => {
      act(() => {
        useSettingsStore.getState().setTheme('light');
        useSettingsStore.getState().toggleFPS();
      });

      const state = useSettingsStore.getState();
      expect(state.display.theme).toBe('light');
      expect(state.display.showFPS).toBe(true);
      // Other settings should remain default
      expect(state.display.gridDisplayMode).toBe('normal');
    });
  });
});
