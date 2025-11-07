/**
 * Hook for automatic message cleanup based on retention settings
 */

import { useEffect, useRef } from 'react';

import { MessageCleanupService } from '../services/messageCleanupService';
import { useChatStore } from '../stores/chatStore';
import { useSettingsStore } from '../stores/settingsStore';

export const useMessageCleanup = () => {
  const { chat } = useSettingsStore();
  const { cleanupOldMessages } = useChatStore();
  const cleanupIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Run initial cleanup when component mounts or retention setting changes
    if (chat.messageRetention > 0) {
      cleanupOldMessages(chat.messageRetention);
    }

    // Set up automatic cleanup every hour
    if (cleanupIntervalRef.current) {
      clearInterval(cleanupIntervalRef.current);
    }

    cleanupIntervalRef.current = MessageCleanupService.scheduleCleanup(
      () => {
        if (chat.messageRetention > 0) {
          cleanupOldMessages(chat.messageRetention);
        }
      },
      60 // Run every 60 minutes
    );

    // Cleanup on unmount
    return () => {
      if (cleanupIntervalRef.current) {
        clearInterval(cleanupIntervalRef.current);
      }
    };
  }, [chat.messageRetention, cleanupOldMessages]);

  // Manual cleanup function
  const manualCleanup = () => {
    if (chat.messageRetention > 0) {
      cleanupOldMessages(chat.messageRetention);
    }
  };

  return {
    manualCleanup,
    currentRetentionDays: chat.messageRetention
  };
};

export default useMessageCleanup;