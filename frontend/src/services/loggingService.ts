/**
 * Logging Service - Configurable frontend logging system
 */

import { useSettingsStore } from '../stores/settingsStore';

export type LogLevel = 'error' | 'warn' | 'info' | 'debug';

interface LogEntry {
  timestamp: Date;
  level: LogLevel;
  message: string;
  data?: any;
  component?: string;
}

class LoggingService {
  private logs: LogEntry[] = [];
  private maxLogs = 1000; // Keep last 1000 log entries

  constructor() {
    // Override console methods to capture logs
    this.interceptConsole();
  }

  /**
   * Check if a log level should be output based on settings
   */
  private shouldLog(level: LogLevel): boolean {
    const currentLevel = useSettingsStore.getState().logLevel;
    const levels: LogLevel[] = ['error', 'warn', 'info', 'debug'];

    const currentIndex = levels.indexOf(currentLevel);
    const messageIndex = levels.indexOf(level);

    return messageIndex <= currentIndex;
  }

  /**
   * Add a log entry
   */
  private addLog(level: LogLevel, message: string, data?: any, component?: string): void {
    const logEntry: LogEntry = {
      timestamp: new Date(),
      level,
      message,
      data,
      component
    };

    this.logs.push(logEntry);

    // Keep only the last maxLogs entries
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // Output to console if enabled
    if (this.shouldLog(level)) {
      this.outputToConsole(logEntry);
    }
  }

  /**
   * Output log entry to browser console
   */
  private outputToConsole(entry: LogEntry): void {
    const prefix = `[${entry.timestamp.toISOString()}] [${entry.level.toUpperCase()}]`;
    const message = entry.component ? `${prefix} [${entry.component}] ${entry.message}` : `${prefix} ${entry.message}`;

    switch (entry.level) {
      case 'error':
        console.error(message, entry.data);
        break;
      case 'warn':
        console.warn(message, entry.data);
        break;
      case 'info':
        console.info(message, entry.data);
        break;
      case 'debug':
        console.debug(message, entry.data);
        break;
    }
  }

  /**
   * Intercept console methods to capture all logging
   */
  private interceptConsole(): void {
    const originalError = console.error;
    const originalWarn = console.warn;
    const originalInfo = console.info;
    const originalLog = console.log;

    console.error = (...args) => {
      this.addLog('error', args.join(' '));
      originalError.apply(console, args);
    };

    console.warn = (...args) => {
      this.addLog('warn', args.join(' '));
      originalWarn.apply(console, args);
    };

    console.info = (...args) => {
      this.addLog('info', args.join(' '));
      originalInfo.apply(console, args);
    };

    console.log = (...args) => {
      this.addLog('info', args.join(' '));
      originalLog.apply(console, args);
    };
  }

  /**
   * Log an error message
   */
  error(message: string, data?: any, component?: string): void {
    this.addLog('error', message, data, component);
  }

  /**
   * Log a warning message
   */
  warn(message: string, data?: any, component?: string): void {
    this.addLog('warn', message, data, component);
  }

  /**
   * Log an info message
   */
  info(message: string, data?: any, component?: string): void {
    this.addLog('info', message, data, component);
  }

  /**
   * Log a debug message
   */
  debug(message: string, data?: any, component?: string): void {
    this.addLog('debug', message, data, component);
  }

  /**
   * Get all log entries
   */
  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  /**
   * Get logs filtered by level
   */
  getLogsByLevel(level: LogLevel): LogEntry[] {
    return this.logs.filter(log => log.level === level);
  }

  /**
   * Get logs filtered by component
   */
  getLogsByComponent(component: string): LogEntry[] {
    return this.logs.filter(log => log.component === component);
  }

  /**
   * Clear all logs
   */
  clearLogs(): void {
    this.logs = [];
  }

  /**
   * Export logs as JSON
   */
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  /**
   * Get log statistics
   */
  getStats(): { [key in LogLevel]: number } {
    const stats = { error: 0, warn: 0, info: 0, debug: 0 };

    this.logs.forEach(log => {
      stats[log.level]++;
    });

    return stats;
  }
}

// Export singleton instance
export const loggingService = new LoggingService();
export default loggingService;