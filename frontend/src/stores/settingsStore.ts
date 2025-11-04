/**
 * Zustand store for application settings and user preferences
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Theme = 'dark' | 'light' | 'auto';
export type GridDisplayMode = 'normal' | 'compact' | 'detailed';
export type PerformanceMode = 'high' | 'balanced' | 'low';

export interface NotificationSettings {
  chatMessages: boolean;
  assistantActions: boolean;
  systemAlerts: boolean;
  soundEnabled: boolean;
}

export interface DisplaySettings {
  theme: Theme;
  gridDisplayMode: GridDisplayMode;
  showFPS: boolean;
  showPerformanceMetrics: boolean;
  animationsEnabled: boolean;
  highQualityRendering: boolean;
  panelTransparency: number; // 0-100
}

export interface LLMSettings {
  defaultProvider: 'nano-gpt' | 'ollama';
  defaultModel: string;
  autoSelectModel: boolean;
  maxTokens: number;
  temperature: number;
}

export interface ChatSettings {
  showTimestamps: boolean;
  enableTypingIndicator: boolean;
  messageRetention: number; // days
  autoScroll: boolean;
  fontSize: 'small' | 'medium' | 'large';
}

export interface SettingsState {
  // Settings categories
  display: DisplaySettings;
  llm: LLMSettings;
  chat: ChatSettings;
  notifications: NotificationSettings;

  // Debug/Developer settings
  debugMode: boolean;
  showDebugPanel: boolean;
  logLevel: 'error' | 'warn' | 'info' | 'debug';

  // UI state
  isSettingsOpen: boolean;
  activeSettingsTab: 'display' | 'llm' | 'chat' | 'notifications' | 'debug';
}

export interface SettingsActions {
  // Settings panel controls
  openSettings: () => void;
  closeSettings: () => void;
  setActiveTab: (tab: SettingsState['activeSettingsTab']) => void;

  // Display settings
  setTheme: (theme: Theme) => void;
  setGridDisplayMode: (mode: GridDisplayMode) => void;
  toggleFPS: () => void;
  togglePerformanceMetrics: () => void;
  toggleAnimations: () => void;
  setHighQualityRendering: (enabled: boolean) => void;
  setPanelTransparency: (transparency: number) => void;

  // LLM settings
  setDefaultProvider: (provider: LLMSettings['defaultProvider']) => void;
  setDefaultModel: (model: string) => void;
  setAutoSelectModel: (enabled: boolean) => void;
  setMaxTokens: (tokens: number) => void;
  setTemperature: (temp: number) => void;

  // Chat settings
  toggleTimestamps: () => void;
  toggleTypingIndicator: () => void;
  setMessageRetention: (days: number) => void;
  toggleAutoScroll: () => void;
  setFontSize: (size: ChatSettings['fontSize']) => void;

  // Notification settings
  setNotificationSetting: (key: keyof NotificationSettings, value: boolean) => void;

  // Debug settings
  toggleDebugMode: () => void;
  toggleDebugPanel: () => void;
  setLogLevel: (level: SettingsState['logLevel']) => void;

  // Reset functions
  resetDisplaySettings: () => void;
  resetLLMSettings: () => void;
  resetChatSettings: () => void;
  resetAllSettings: () => void;
}

// Default settings
const defaultDisplaySettings: DisplaySettings = {
  theme: 'dark',
  gridDisplayMode: 'normal',
  showFPS: false,
  showPerformanceMetrics: false,
  animationsEnabled: true,
  highQualityRendering: true,
  panelTransparency: 90,
};

const defaultLLMSettings: LLMSettings = {
  defaultProvider: 'nano-gpt',
  defaultModel: 'gpt-4o-mini',
  autoSelectModel: true,
  maxTokens: 2000,
  temperature: 0.7,
};

const defaultChatSettings: ChatSettings = {
  showTimestamps: true,
  enableTypingIndicator: true,
  messageRetention: 30,
  autoScroll: true,
  fontSize: 'medium',
};

const defaultNotificationSettings: NotificationSettings = {
  chatMessages: true,
  assistantActions: true,
  systemAlerts: true,
  soundEnabled: false,
};

export const useSettingsStore = create<SettingsState & SettingsActions>()(
  persist(
    (set, get) => ({
      // Initial state
      display: defaultDisplaySettings,
      llm: defaultLLMSettings,
      chat: defaultChatSettings,
      notifications: defaultNotificationSettings,
      debugMode: false,
      showDebugPanel: false,
      logLevel: 'info',
      isSettingsOpen: false,
      activeSettingsTab: 'display',

      // Settings panel controls
      openSettings: () => set({ isSettingsOpen: true }),
      closeSettings: () => set({ isSettingsOpen: false }),
      setActiveTab: (tab) => set({ activeSettingsTab: tab }),

      // Display settings
      setTheme: (theme) => set(state => ({
        display: { ...state.display, theme }
      })),
      setGridDisplayMode: (mode) => set(state => ({
        display: { ...state.display, gridDisplayMode: mode }
      })),
      toggleFPS: () => set(state => ({
        display: { ...state.display, showFPS: !state.display.showFPS }
      })),
      togglePerformanceMetrics: () => set(state => ({
        display: { ...state.display, showPerformanceMetrics: !state.display.showPerformanceMetrics }
      })),
      toggleAnimations: () => set(state => ({
        display: { ...state.display, animationsEnabled: !state.display.animationsEnabled }
      })),
      setHighQualityRendering: (enabled) => set(state => ({
        display: { ...state.display, highQualityRendering: enabled }
      })),
      setPanelTransparency: (transparency) => set(state => ({
        display: { ...state.display, panelTransparency: Math.max(0, Math.min(100, transparency)) }
      })),

      // LLM settings
      setDefaultProvider: (provider) => set(state => ({
        llm: { ...state.llm, defaultProvider: provider }
      })),
      setDefaultModel: (model) => set(state => ({
        llm: { ...state.llm, defaultModel: model }
      })),
      setAutoSelectModel: (enabled) => set(state => ({
        llm: { ...state.llm, autoSelectModel: enabled }
      })),
      setMaxTokens: (tokens) => set(state => ({
        llm: { ...state.llm, maxTokens: Math.max(100, Math.min(8000, tokens)) }
      })),
      setTemperature: (temp) => set(state => ({
        llm: { ...state.llm, temperature: Math.max(0, Math.min(2, temp)) }
      })),

      // Chat settings
      toggleTimestamps: () => set(state => ({
        chat: { ...state.chat, showTimestamps: !state.chat.showTimestamps }
      })),
      toggleTypingIndicator: () => set(state => ({
        chat: { ...state.chat, enableTypingIndicator: !state.chat.enableTypingIndicator }
      })),
      setMessageRetention: (days) => set(state => ({
        chat: { ...state.chat, messageRetention: Math.max(1, Math.min(365, days)) }
      })),
      toggleAutoScroll: () => set(state => ({
        chat: { ...state.chat, autoScroll: !state.chat.autoScroll }
      })),
      setFontSize: (fontSize) => set(state => ({
        chat: { ...state.chat, fontSize }
      })),

      // Notification settings
      setNotificationSetting: (key, value) => set(state => ({
        notifications: { ...state.notifications, [key]: value }
      })),

      // Debug settings
      toggleDebugMode: () => set(state => ({ debugMode: !state.debugMode })),
      toggleDebugPanel: () => set(state => ({ showDebugPanel: !state.showDebugPanel })),
      setLogLevel: (logLevel) => set({ logLevel }),

      // Reset functions
      resetDisplaySettings: () => set({ display: defaultDisplaySettings }),
      resetLLMSettings: () => set({ llm: defaultLLMSettings }),
      resetChatSettings: () => set({ chat: defaultChatSettings }),
      resetAllSettings: () => set({
        display: defaultDisplaySettings,
        llm: defaultLLMSettings,
        chat: defaultChatSettings,
        notifications: defaultNotificationSettings,
        debugMode: false,
        showDebugPanel: false,
        logLevel: 'info',
      }),
    }),
    {
      name: 'deskmate-settings', // localStorage key
      partialize: (state) => ({
        // Only persist actual settings, not UI state
        display: state.display,
        llm: state.llm,
        chat: state.chat,
        notifications: state.notifications,
        debugMode: state.debugMode,
        logLevel: state.logLevel,
      }),
    }
  )
);