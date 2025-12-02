/**
 * Tests for SettingsPanel Component
 *
 * Tests cover:
 * - Panel open/close behavior
 * - Tab navigation
 * - Display settings
 * - LLM settings
 * - Chat settings
 * - Notification settings
 * - Debug settings
 * - Reset functionality
 * - Keyboard navigation
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SettingsPanel from '../SettingsPanel';

// Mock settings store
const mockCloseSettings = jest.fn();
const mockSetActiveTab = jest.fn();
const mockSetTheme = jest.fn();
const mockSetGridDisplayMode = jest.fn();
const mockToggleFPS = jest.fn();
const mockTogglePerformanceMetrics = jest.fn();
const mockToggleAnimations = jest.fn();
const mockSetHighQualityRendering = jest.fn();
const mockSetPanelTransparency = jest.fn();
const mockSetDefaultProvider = jest.fn();
const mockSetDefaultModel = jest.fn();
const mockSetAutoSelectModel = jest.fn();
const mockSetMaxTokens = jest.fn();
const mockSetTemperature = jest.fn();
const mockToggleTimestamps = jest.fn();
const mockToggleTypingIndicator = jest.fn();
const mockSetMessageRetention = jest.fn();
const mockToggleAutoScroll = jest.fn();
const mockSetFontSize = jest.fn();
const mockSetNotificationSetting = jest.fn();
const mockToggleDebugMode = jest.fn();
const mockToggleDebugPanel = jest.fn();
const mockSetLogLevel = jest.fn();
const mockResetDisplaySettings = jest.fn();
const mockResetLLMSettings = jest.fn();
const mockResetChatSettings = jest.fn();
const mockResetAllSettings = jest.fn();

let mockSettingsState = {
  isSettingsOpen: true,
  activeSettingsTab: 'display' as const,
  display: {
    theme: 'dark',
    gridDisplayMode: 'normal',
    showFPS: false,
    showPerformanceMetrics: false,
    animationsEnabled: true,
    highQualityRendering: true,
    panelTransparency: 90,
  },
  llm: {
    defaultProvider: 'nano-gpt',
    defaultModel: 'gpt-4o-mini',
    autoSelectModel: true,
    maxTokens: 2000,
    temperature: 0.7,
  },
  chat: {
    showTimestamps: true,
    enableTypingIndicator: true,
    messageRetention: 30,
    autoScroll: true,
    fontSize: 'medium',
  },
  notifications: {
    chatMessages: true,
    assistantActions: true,
    systemAlerts: true,
    soundEnabled: false,
  },
  debugMode: false,
  showDebugPanel: false,
  logLevel: 'info',
  closeSettings: mockCloseSettings,
  setActiveTab: mockSetActiveTab,
  setTheme: mockSetTheme,
  setGridDisplayMode: mockSetGridDisplayMode,
  toggleFPS: mockToggleFPS,
  togglePerformanceMetrics: mockTogglePerformanceMetrics,
  toggleAnimations: mockToggleAnimations,
  setHighQualityRendering: mockSetHighQualityRendering,
  setPanelTransparency: mockSetPanelTransparency,
  setDefaultProvider: mockSetDefaultProvider,
  setDefaultModel: mockSetDefaultModel,
  setAutoSelectModel: mockSetAutoSelectModel,
  setMaxTokens: mockSetMaxTokens,
  setTemperature: mockSetTemperature,
  toggleTimestamps: mockToggleTimestamps,
  toggleTypingIndicator: mockToggleTypingIndicator,
  setMessageRetention: mockSetMessageRetention,
  toggleAutoScroll: mockToggleAutoScroll,
  setFontSize: mockSetFontSize,
  setNotificationSetting: mockSetNotificationSetting,
  toggleDebugMode: mockToggleDebugMode,
  toggleDebugPanel: mockToggleDebugPanel,
  setLogLevel: mockSetLogLevel,
  resetDisplaySettings: mockResetDisplaySettings,
  resetLLMSettings: mockResetLLMSettings,
  resetChatSettings: mockResetChatSettings,
  resetAllSettings: mockResetAllSettings,
};

jest.mock('../../../stores/settingsStore', () => ({
  useSettingsStore: () => mockSettingsState,
}));

describe('SettingsPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSettingsState.isSettingsOpen = true;
    mockSettingsState.activeSettingsTab = 'display';
  });

  describe('Panel Visibility', () => {
    it('should render when isSettingsOpen is true', () => {
      mockSettingsState.isSettingsOpen = true;
      render(<SettingsPanel />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    it('should not render when isSettingsOpen is false', () => {
      mockSettingsState.isSettingsOpen = false;
      render(<SettingsPanel />);

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  describe('Close Button', () => {
    it('should close settings when close button is clicked', async () => {
      render(<SettingsPanel />);

      const closeButton = screen.getByLabelText('Close settings panel');
      await userEvent.click(closeButton);

      expect(mockCloseSettings).toHaveBeenCalled();
    });

    it('should close settings on Escape key', () => {
      render(<SettingsPanel />);

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(mockCloseSettings).toHaveBeenCalled();
    });
  });

  describe('Tab Navigation', () => {
    it('should show all tab buttons', () => {
      render(<SettingsPanel />);

      expect(screen.getByText('Display')).toBeInTheDocument();
      expect(screen.getByText('AI Models')).toBeInTheDocument();
      expect(screen.getByText('Chat')).toBeInTheDocument();
      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText('Debug')).toBeInTheDocument();
    });

    it('should switch tabs when clicked', async () => {
      render(<SettingsPanel />);

      const llmTab = screen.getByRole('tab', { name: /ai models/i });
      await userEvent.click(llmTab);

      expect(mockSetActiveTab).toHaveBeenCalledWith('llm');
    });

    it('should highlight active tab', () => {
      mockSettingsState.activeSettingsTab = 'chat';
      render(<SettingsPanel />);

      const chatTab = screen.getByRole('tab', { name: /chat/i });
      expect(chatTab).toHaveClass('bg-blue-600');
    });
  });

  describe('Display Settings', () => {
    beforeEach(() => {
      mockSettingsState.activeSettingsTab = 'display';
    });

    it('should show display settings section', () => {
      render(<SettingsPanel />);

      expect(screen.getByText('Display Settings')).toBeInTheDocument();
    });

    it('should show theme selector', () => {
      render(<SettingsPanel />);

      expect(screen.getByLabelText('Theme')).toBeInTheDocument();
    });

    it('should change theme', async () => {
      render(<SettingsPanel />);

      const themeSelect = screen.getByLabelText('Theme');
      await userEvent.selectOptions(themeSelect, 'light');

      expect(mockSetTheme).toHaveBeenCalledWith('light');
    });

    it('should show FPS checkbox', () => {
      render(<SettingsPanel />);

      expect(screen.getByLabelText('Show FPS Counter')).toBeInTheDocument();
    });

    it('should toggle FPS display', async () => {
      render(<SettingsPanel />);

      const fpsCheckbox = screen.getByLabelText('Show FPS Counter');
      await userEvent.click(fpsCheckbox);

      expect(mockToggleFPS).toHaveBeenCalled();
    });

    it('should show transparency slider', () => {
      render(<SettingsPanel />);

      expect(screen.getByText(/panel transparency/i)).toBeInTheDocument();
    });

    it('should reset display settings', async () => {
      render(<SettingsPanel />);

      const resetButtons = screen.getAllByText('Reset');
      await userEvent.click(resetButtons[0]); // First reset is for display

      expect(mockResetDisplaySettings).toHaveBeenCalled();
    });
  });

  describe('LLM Settings', () => {
    beforeEach(() => {
      mockSettingsState.activeSettingsTab = 'llm';
    });

    it('should show LLM settings section', () => {
      render(<SettingsPanel />);

      expect(screen.getByText('AI Model Settings')).toBeInTheDocument();
    });

    it('should show provider selector', () => {
      render(<SettingsPanel />);

      expect(screen.getByLabelText('Default Provider')).toBeInTheDocument();
    });

    it('should change provider', async () => {
      render(<SettingsPanel />);

      const providerSelect = screen.getByLabelText('Default Provider');
      await userEvent.selectOptions(providerSelect, 'ollama');

      expect(mockSetDefaultProvider).toHaveBeenCalledWith('ollama');
    });

    it('should show model input', () => {
      render(<SettingsPanel />);

      expect(screen.getByLabelText('Default Model')).toBeInTheDocument();
    });

    it('should show temperature slider', () => {
      render(<SettingsPanel />);

      expect(screen.getByText(/temperature/i)).toBeInTheDocument();
    });

    it('should show max tokens slider', () => {
      render(<SettingsPanel />);

      expect(screen.getByText(/max tokens/i)).toBeInTheDocument();
    });
  });

  describe('Chat Settings', () => {
    beforeEach(() => {
      mockSettingsState.activeSettingsTab = 'chat';
    });

    it('should show chat settings section', () => {
      render(<SettingsPanel />);

      expect(screen.getByText('Chat Settings')).toBeInTheDocument();
    });

    it('should show timestamps checkbox', () => {
      render(<SettingsPanel />);

      expect(screen.getByLabelText('Show message timestamps')).toBeInTheDocument();
    });

    it('should toggle timestamps', async () => {
      render(<SettingsPanel />);

      const timestampsCheckbox = screen.getByLabelText('Show message timestamps');
      await userEvent.click(timestampsCheckbox);

      expect(mockToggleTimestamps).toHaveBeenCalled();
    });

    it('should show typing indicator checkbox', () => {
      render(<SettingsPanel />);

      expect(screen.getByLabelText('Show typing indicator')).toBeInTheDocument();
    });

    it('should show font size selector', () => {
      render(<SettingsPanel />);

      expect(screen.getByLabelText('Font Size')).toBeInTheDocument();
    });

    it('should change font size', async () => {
      render(<SettingsPanel />);

      const fontSizeSelect = screen.getByLabelText('Font Size');
      await userEvent.selectOptions(fontSizeSelect, 'large');

      expect(mockSetFontSize).toHaveBeenCalledWith('large');
    });

    it('should show message retention slider', () => {
      render(<SettingsPanel />);

      expect(screen.getByText(/message retention/i)).toBeInTheDocument();
    });
  });

  describe('Notification Settings', () => {
    beforeEach(() => {
      mockSettingsState.activeSettingsTab = 'notifications';
    });

    it('should show notification settings section', () => {
      render(<SettingsPanel />);

      expect(screen.getByText('Notification Settings')).toBeInTheDocument();
    });

    it('should show chat message notifications checkbox', () => {
      render(<SettingsPanel />);

      expect(screen.getByLabelText('Chat message notifications')).toBeInTheDocument();
    });

    it('should toggle chat notifications', async () => {
      render(<SettingsPanel />);

      const chatNotificationsCheckbox = screen.getByLabelText('Chat message notifications');
      await userEvent.click(chatNotificationsCheckbox);

      expect(mockSetNotificationSetting).toHaveBeenCalledWith('chatMessages', expect.any(Boolean));
    });

    it('should show sound notifications checkbox', () => {
      render(<SettingsPanel />);

      expect(screen.getByLabelText('Sound notifications')).toBeInTheDocument();
    });
  });

  describe('Debug Settings', () => {
    beforeEach(() => {
      mockSettingsState.activeSettingsTab = 'debug';
    });

    it('should show debug settings section', () => {
      render(<SettingsPanel />);

      expect(screen.getByText('Debug Settings')).toBeInTheDocument();
    });

    it('should show warning message', () => {
      render(<SettingsPanel />);

      expect(screen.getByText(/debug settings are for development/i)).toBeInTheDocument();
    });

    it('should show debug mode checkbox', () => {
      render(<SettingsPanel />);

      expect(screen.getByLabelText('Enable debug mode')).toBeInTheDocument();
    });

    it('should toggle debug mode', async () => {
      render(<SettingsPanel />);

      const debugModeCheckbox = screen.getByLabelText('Enable debug mode');
      await userEvent.click(debugModeCheckbox);

      expect(mockToggleDebugMode).toHaveBeenCalled();
    });

    it('should show log level selector', () => {
      render(<SettingsPanel />);

      expect(screen.getByLabelText('Log Level')).toBeInTheDocument();
    });

    it('should change log level', async () => {
      render(<SettingsPanel />);

      const logLevelSelect = screen.getByLabelText('Log Level');
      await userEvent.selectOptions(logLevelSelect, 'debug');

      expect(mockSetLogLevel).toHaveBeenCalledWith('debug');
    });
  });

  describe('Reset All Settings', () => {
    it('should show reset all button', () => {
      render(<SettingsPanel />);

      expect(screen.getByText('Reset All Settings')).toBeInTheDocument();
    });

    it('should call resetAllSettings when clicked', async () => {
      render(<SettingsPanel />);

      const resetAllButton = screen.getByText('Reset All Settings');
      await userEvent.click(resetAllButton);

      expect(mockResetAllSettings).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have dialog role', () => {
      render(<SettingsPanel />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should have aria-modal attribute', () => {
      render(<SettingsPanel />);

      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    });

    it('should have settings title with aria-labelledby', () => {
      render(<SettingsPanel />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-labelledby', 'settings-title');
    });

    it('should have tablist for navigation', () => {
      render(<SettingsPanel />);

      expect(screen.getByRole('tablist')).toBeInTheDocument();
    });

    it('should mark active tab with aria-selected', () => {
      mockSettingsState.activeSettingsTab = 'display';
      render(<SettingsPanel />);

      const displayTab = screen.getByRole('tab', { name: /display/i });
      expect(displayTab).toHaveAttribute('aria-selected', 'true');
    });
  });
});
