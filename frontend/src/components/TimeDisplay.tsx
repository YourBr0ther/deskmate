/**
 * Time and Date Display Component - Real-time clock for companion panel
 */

import React, { useState, useEffect } from 'react';

interface TimeDisplayProps {
  showSeconds?: boolean;
  show24Hour?: boolean;
  className?: string;
}

const TimeDisplay: React.FC<TimeDisplayProps> = ({
  showSeconds = true,
  show24Hour = false,
  className = ""
}) => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    const options: Intl.DateTimeFormatOptions = {
      hour: '2-digit',
      minute: '2-digit',
      hour12: !show24Hour,
    };

    if (showSeconds) {
      options.second = '2-digit';
    }

    return date.toLocaleTimeString([], options);
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString([], {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getTimeOfDayGreeting = (date: Date) => {
    const hour = date.getHours();
    if (hour < 6) return '🌙 Late Night';
    if (hour < 12) return '🌅 Morning';
    if (hour < 17) return '☀️ Afternoon';
    if (hour < 21) return '🌆 Evening';
    return '🌙 Night';
  };

  return (
    <div className={`time-display ${className}`}>
      <div className="flex flex-col items-center space-y-1">
        {/* Time */}
        <div className="text-xl font-mono font-bold text-white">
          {formatTime(currentTime)}
        </div>

        {/* Date */}
        <div className="text-sm text-gray-300">
          {formatDate(currentTime)}
        </div>

        {/* Time of day greeting */}
        <div className="text-xs text-gray-400 flex items-center space-x-1">
          <span>{getTimeOfDayGreeting(currentTime)}</span>
        </div>
      </div>
    </div>
  );
};

export default TimeDisplay;