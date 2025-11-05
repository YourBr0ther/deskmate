/**
 * Notification Service - Browser notifications and sound alerts
 */

import { useSettingsStore } from '../stores/settingsStore';

export type NotificationType = 'chatMessage' | 'assistantAction' | 'systemAlert';

interface NotificationOptions {
  title: string;
  body: string;
  icon?: string;
  tag?: string;
  requireInteraction?: boolean;
}

class NotificationService {
  private permissionRequested = false;
  private audioContext: AudioContext | null = null;

  constructor() {
    // Initialize audio context for sound notifications
    if (typeof window !== 'undefined' && 'AudioContext' in window) {
      this.audioContext = new AudioContext();
    }
  }

  /**
   * Request notification permission from the user
   */
  async requestPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return 'denied';
    }

    if (Notification.permission === 'granted') {
      return 'granted';
    }

    if (Notification.permission === 'denied') {
      return 'denied';
    }

    this.permissionRequested = true;
    const permission = await Notification.requestPermission();
    return permission;
  }

  /**
   * Check if notifications are enabled for a specific type
   */
  private isNotificationEnabled(type: NotificationType): boolean {
    const settings = useSettingsStore.getState().notifications;

    switch (type) {
      case 'chatMessage':
        return settings.chatMessages;
      case 'assistantAction':
        return settings.assistantActions;
      case 'systemAlert':
        return settings.systemAlerts;
      default:
        return false;
    }
  }

  /**
   * Show a browser notification
   */
  async showNotification(
    type: NotificationType,
    options: NotificationOptions
  ): Promise<void> {
    // Check if this notification type is enabled
    if (!this.isNotificationEnabled(type)) {
      return;
    }

    // Request permission if not already requested
    if (!this.permissionRequested) {
      const permission = await this.requestPermission();
      if (permission !== 'granted') {
        return;
      }
    }

    // Check if we have permission
    if (Notification.permission !== 'granted') {
      return;
    }

    // Create notification
    const notification = new Notification(options.title, {
      body: options.body,
      icon: options.icon || '/favicon.ico',
      tag: options.tag || `deskmate-${type}`,
      requireInteraction: options.requireInteraction || false,
      badge: '/favicon.ico'
    });

    // Auto-close after 5 seconds unless it requires interaction
    if (!options.requireInteraction) {
      setTimeout(() => {
        notification.close();
      }, 5000);
    }

    // Play sound if enabled
    await this.playNotificationSound(type);
  }

  /**
   * Play notification sound
   */
  private async playNotificationSound(type: NotificationType): Promise<void> {
    const settings = useSettingsStore.getState().notifications;

    if (!settings.soundEnabled || !this.audioContext) {
      return;
    }

    try {
      // Create different sounds for different notification types
      const frequency = this.getNotificationFrequency(type);
      const duration = 0.2; // 200ms

      const oscillator = this.audioContext.createOscillator();
      const gainNode = this.audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(this.audioContext.destination);

      oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
      gainNode.gain.linearRampToValueAtTime(0.1, this.audioContext.currentTime + 0.01);
      gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + duration);

      oscillator.start(this.audioContext.currentTime);
      oscillator.stop(this.audioContext.currentTime + duration);

    } catch (error) {
      console.warn('Failed to play notification sound:', error);
    }
  }

  /**
   * Get notification sound frequency based on type
   */
  private getNotificationFrequency(type: NotificationType): number {
    switch (type) {
      case 'chatMessage':
        return 800; // High pitch for chat messages
      case 'assistantAction':
        return 600; // Medium pitch for assistant actions
      case 'systemAlert':
        return 400; // Low pitch for system alerts
      default:
        return 500;
    }
  }

  /**
   * Show chat message notification
   */
  async notifyNewMessage(senderName: string, message: string): Promise<void> {
    await this.showNotification('chatMessage', {
      title: `New message from ${senderName}`,
      body: message.length > 100 ? message.substring(0, 100) + '...' : message,
      tag: 'chat-message'
    });
  }

  /**
   * Show assistant action notification
   */
  async notifyAssistantAction(action: string, details?: string): Promise<void> {
    await this.showNotification('assistantAction', {
      title: 'Assistant Action',
      body: details ? `${action}: ${details}` : action,
      tag: 'assistant-action'
    });
  }

  /**
   * Show system alert notification
   */
  async notifySystemAlert(title: string, message: string): Promise<void> {
    await this.showNotification('systemAlert', {
      title,
      body: message,
      tag: 'system-alert',
      requireInteraction: true
    });
  }

  /**
   * Clear all notifications
   */
  clearAllNotifications(): void {
    // Note: There's no standard way to clear all notifications
    // This is a placeholder for future implementation
    console.log('Clearing all notifications');
  }
}

// Export singleton instance
export const notificationService = new NotificationService();
export default notificationService;