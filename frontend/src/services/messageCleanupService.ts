/**
 * Message cleanup service for managing chat message retention
 */

import { ChatMessage } from '../stores/chatStore';

export interface CleanupOptions {
  retentionDays: number;
  preserveSystemMessages?: boolean;
  preserveImportantMessages?: boolean;
}

export class MessageCleanupService {
  /**
   * Filter out messages older than the retention period
   */
  static cleanupMessages(
    messages: ChatMessage[],
    options: CleanupOptions
  ): ChatMessage[] {
    const { retentionDays, preserveSystemMessages = true, preserveImportantMessages = true } = options;

    if (retentionDays <= 0) {
      return messages; // No cleanup if retention is 0 or negative
    }

    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

    return messages.filter(message => {
      const messageDate = new Date(message.timestamp);

      // Keep messages newer than cutoff
      if (messageDate >= cutoffDate) {
        return true;
      }

      // Preserve system messages if configured
      if (preserveSystemMessages && message.role === 'system') {
        return true;
      }

      // Preserve important messages (those that contain specific keywords)
      if (preserveImportantMessages && this.isImportantMessage(message)) {
        return true;
      }

      // Remove old messages
      return false;
    });
  }

  /**
   * Check if a message should be considered important and preserved
   */
  private static isImportantMessage(message: ChatMessage): boolean {
    const importantKeywords = [
      'persona',
      'personality',
      'remember',
      'important',
      'config',
      'settings',
      'error',
      'warning'
    ];

    const content = message.content.toLowerCase();
    return importantKeywords.some(keyword => content.includes(keyword));
  }

  /**
   * Get cleanup statistics
   */
  static getCleanupStats(
    originalMessages: ChatMessage[],
    cleanedMessages: ChatMessage[]
  ): {
    originalCount: number;
    cleanedCount: number;
    removedCount: number;
    oldestMessage?: string;
    newestMessage?: string;
  } {
    const originalCount = originalMessages.length;
    const cleanedCount = cleanedMessages.length;
    const removedCount = originalCount - cleanedCount;

    let oldestMessage: string | undefined;
    let newestMessage: string | undefined;

    if (cleanedMessages.length > 0) {
      const sortedMessages = [...cleanedMessages].sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );
      oldestMessage = sortedMessages[0].timestamp;
      newestMessage = sortedMessages[sortedMessages.length - 1].timestamp;
    }

    return {
      originalCount,
      cleanedCount,
      removedCount,
      oldestMessage,
      newestMessage
    };
  }

  /**
   * Schedule automatic cleanup (to be called periodically)
   */
  static scheduleCleanup(
    cleanupFunction: () => void,
    intervalMinutes: number = 60
  ): NodeJS.Timeout {
    return setInterval(cleanupFunction, intervalMinutes * 60 * 1000);
  }

  /**
   * Log cleanup activity for debugging
   */
  static logCleanupActivity(
    stats: ReturnType<typeof MessageCleanupService.getCleanupStats>,
    retentionDays: number
  ): void {
    if (stats.removedCount > 0) {
      console.log(`[MessageCleanup] Removed ${stats.removedCount} messages older than ${retentionDays} days`);
      console.log(`[MessageCleanup] Messages: ${stats.originalCount} → ${stats.cleanedCount}`);
      if (stats.oldestMessage && stats.newestMessage) {
        console.log(`[MessageCleanup] Date range: ${stats.oldestMessage} to ${stats.newestMessage}`);
      }
    } else {
      console.log(`[MessageCleanup] No messages to clean up (retention: ${retentionDays} days)`);
    }
  }
}

export default MessageCleanupService;