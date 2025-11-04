/**
 * Enhanced Status Indicators Component - Visual mood and status representation
 */

import React from 'react';
import { useRoomStore } from '../stores/roomStore';

interface StatusIndicatorsProps {
  compact?: boolean;
  className?: string;
}

const StatusIndicators: React.FC<StatusIndicatorsProps> = ({
  compact = false,
  className = ""
}) => {
  const { assistant } = useRoomStore();

  const getMoodConfig = (mood: string) => {
    switch (mood.toLowerCase()) {
      case 'happy':
        return {
          emoji: '😊',
          color: 'text-green-400',
          bgColor: 'bg-green-500/20',
          borderColor: 'border-green-500/30',
          description: 'Happy and content'
        };
      case 'excited':
        return {
          emoji: '🤩',
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-500/20',
          borderColor: 'border-yellow-500/30',
          description: 'Excited and energetic'
        };
      case 'sad':
        return {
          emoji: '😢',
          color: 'text-blue-400',
          bgColor: 'bg-blue-500/20',
          borderColor: 'border-blue-500/30',
          description: 'Feeling down'
        };
      case 'tired':
        return {
          emoji: '😴',
          color: 'text-purple-400',
          bgColor: 'bg-purple-500/20',
          borderColor: 'border-purple-500/30',
          description: 'Feeling tired'
        };
      case 'neutral':
      default:
        return {
          emoji: '😐',
          color: 'text-gray-400',
          bgColor: 'bg-gray-500/20',
          borderColor: 'border-gray-500/30',
          description: 'Neutral mood'
        };
    }
  };

  const getStatusConfig = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return {
          icon: '🟢',
          color: 'text-green-400',
          bgColor: 'bg-green-500/20',
          description: 'Active and responsive'
        };
      case 'idle':
        return {
          icon: '💭',
          color: 'text-gray-400',
          bgColor: 'bg-gray-500/20',
          description: 'In idle mode'
        };
      case 'busy':
        return {
          icon: '🟡',
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-500/20',
          description: 'Currently busy'
        };
      default:
        return {
          icon: '⚪',
          color: 'text-gray-400',
          bgColor: 'bg-gray-500/20',
          description: 'Unknown status'
        };
    }
  };

  const getActionIcon = (action: string) => {
    switch (action?.toLowerCase()) {
      case 'walking':
        return '🚶‍♂️';
      case 'sitting':
        return '💺';
      case 'talking':
        return '💬';
      case 'thinking':
        return '🤔';
      case 'sleeping':
        return '😴';
      case 'idle':
      default:
        return '⏸️';
    }
  };

  const moodConfig = getMoodConfig(assistant.mood);
  const statusConfig = getStatusConfig(assistant.status);

  if (compact) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        {/* Mood indicator */}
        <div
          className={`flex items-center justify-center w-8 h-8 rounded-full border ${moodConfig.bgColor} ${moodConfig.borderColor}`}
          title={`Mood: ${assistant.mood} - ${moodConfig.description}`}
        >
          <span className="text-lg">{moodConfig.emoji}</span>
        </div>

        {/* Status indicator */}
        <div
          className={`flex items-center justify-center w-8 h-8 rounded-full ${statusConfig.bgColor}`}
          title={`Status: ${assistant.status} - ${statusConfig.description}`}
        >
          <span className="text-sm">{statusConfig.icon}</span>
        </div>

        {/* Action indicator */}
        {assistant.currentAction && (
          <div
            className="flex items-center justify-center w-8 h-8"
            title={`Action: ${assistant.currentAction}`}
          >
            <span className="text-lg">{getActionIcon(assistant.currentAction)}</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Mood */}
      <div className={`p-3 rounded-lg border ${moodConfig.bgColor} ${moodConfig.borderColor}`}>
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{moodConfig.emoji}</span>
          <div>
            <div className={`font-medium ${moodConfig.color}`}>
              {assistant.mood.charAt(0).toUpperCase() + assistant.mood.slice(1)}
            </div>
            <div className="text-sm text-gray-400">{moodConfig.description}</div>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className={`p-3 rounded-lg ${statusConfig.bgColor}`}>
        <div className="flex items-center space-x-3">
          <span className="text-xl">{statusConfig.icon}</span>
          <div>
            <div className={`font-medium ${statusConfig.color}`}>
              {assistant.status.charAt(0).toUpperCase() + assistant.status.slice(1)}
            </div>
            <div className="text-sm text-gray-400">{statusConfig.description}</div>
          </div>
        </div>
      </div>

      {/* Current Action */}
      {assistant.currentAction && (
        <div className="p-3 rounded-lg bg-gray-700/30">
          <div className="flex items-center space-x-3">
            <span className="text-xl">{getActionIcon(assistant.currentAction)}</span>
            <div>
              <div className="font-medium text-white">
                {assistant.currentAction.charAt(0).toUpperCase() + assistant.currentAction.slice(1)}
              </div>
              <div className="text-sm text-gray-400">Current activity</div>
            </div>
          </div>
        </div>
      )}

      {/* Energy Level */}
      <div className="p-3 rounded-lg bg-gray-700/30">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-white">Energy</span>
          <span className="text-sm text-gray-400">{Math.round((assistant.energy_level || 1) * 100)}%</span>
        </div>
        <div className="w-full bg-gray-600 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${(assistant.energy_level || 1) * 100}%` }}
          />
        </div>
      </div>

      {/* Position */}
      <div className="p-3 rounded-lg bg-gray-700/30">
        <div className="flex items-center space-x-3">
          <span className="text-xl">📍</span>
          <div>
            <div className="font-medium text-white">
              Position ({assistant.position.x}, {assistant.position.y})
            </div>
            <div className="text-sm text-gray-400">
              Facing {assistant.facing}
              {assistant.holding_object_id && " • Holding object"}
              {assistant.sitting_on_object_id && " • Sitting"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatusIndicators;