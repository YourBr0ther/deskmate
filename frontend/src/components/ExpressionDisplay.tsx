/**
 * Enhanced Expression Display Component - Smooth expression transitions and mood visualization
 */

import React, { useState, useEffect, useRef } from 'react';

import { usePersonaStore } from '../stores/personaStore';
import { useRoomStore } from '../stores/roomStore';
import { useSettingsStore } from '../stores/settingsStore';

interface ExpressionDisplayProps {
  size?: 'small' | 'medium' | 'large';
  showMoodOverlay?: boolean;
  className?: string;
}

const ExpressionDisplay: React.FC<ExpressionDisplayProps> = ({
  size = 'medium',
  showMoodOverlay = true,
  className = ""
}) => {
  const { selectedPersona, currentExpression } = usePersonaStore();
  const { assistant } = useRoomStore();
  const { display } = useSettingsStore();

  const [isTransitioning, setIsTransitioning] = useState(false);
  const [displayExpression, setDisplayExpression] = useState(currentExpression);
  const [moodOverlayVisible, setMoodOverlayVisible] = useState(false);
  const transitionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const moodTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Handle expression changes with smooth transitions
  useEffect(() => {
    if (currentExpression !== displayExpression && display.animationsEnabled) {
      setIsTransitioning(true);

      // Clear any existing timeout
      if (transitionTimeoutRef.current) {
        clearTimeout(transitionTimeoutRef.current);
      }

      // Transition to new expression after fade out
      transitionTimeoutRef.current = setTimeout(() => {
        setDisplayExpression(currentExpression);
        setIsTransitioning(false);
      }, 200); // 200ms fade out, then change
    } else {
      setDisplayExpression(currentExpression);
    }

    return () => {
      if (transitionTimeoutRef.current) {
        clearTimeout(transitionTimeoutRef.current);
      }
    };
  }, [currentExpression, display.animationsEnabled]);

  // Handle mood changes with overlay flash
  useEffect(() => {
    if (showMoodOverlay && display.animationsEnabled) {
      setMoodOverlayVisible(true);

      // Clear any existing timeout
      if (moodTimeoutRef.current) {
        clearTimeout(moodTimeoutRef.current);
      }

      // Hide overlay after brief display
      moodTimeoutRef.current = setTimeout(() => {
        setMoodOverlayVisible(false);
      }, 800);
    }

    return () => {
      if (moodTimeoutRef.current) {
        clearTimeout(moodTimeoutRef.current);
      }
    };
  }, [assistant.mood, showMoodOverlay, display.animationsEnabled]);

  const getSizeClasses = () => {
    switch (size) {
      case 'small':
        return 'w-12 h-12';
      case 'large':
        return 'w-32 h-32';
      case 'medium':
      default:
        return 'w-16 h-16';
    }
  };

  const getMoodOverlayConfig = (mood: string) => {
    switch (mood.toLowerCase()) {
      case 'happy':
        return {
          color: 'bg-green-400/30',
          emoji: '😊',
          text: 'Happy'
        };
      case 'excited':
        return {
          color: 'bg-yellow-400/30',
          emoji: '🤩',
          text: 'Excited'
        };
      case 'sad':
        return {
          color: 'bg-blue-400/30',
          emoji: '😢',
          text: 'Sad'
        };
      case 'tired':
        return {
          color: 'bg-purple-400/30',
          emoji: '😴',
          text: 'Tired'
        };
      case 'neutral':
      default:
        return {
          color: 'bg-gray-400/30',
          emoji: '😐',
          text: 'Neutral'
        };
    }
  };

  const moodConfig = getMoodOverlayConfig(assistant.mood);

  if (!selectedPersona) {
    return (
      <div className={`${getSizeClasses()} bg-gray-800 rounded-lg flex items-center justify-center ${className}`}>
        <div className="text-gray-400 text-center">
          <div className={size === 'large' ? 'text-4xl' : size === 'medium' ? 'text-2xl' : 'text-lg'}>👤</div>
          {size === 'large' && <div className="text-xs mt-1">No Persona</div>}
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${getSizeClasses()} ${className}`}>
      {/* Main Portrait */}
      <div className="relative w-full h-full rounded-lg overflow-hidden bg-gradient-to-b from-blue-500 to-blue-600">
        <img
          src={`/api/personas/${encodeURIComponent(selectedPersona.persona.data.name)}/image?expression=${displayExpression}`}
          alt={`${selectedPersona.persona.data.name} - ${displayExpression}`}
          className={`w-full h-full object-cover transition-opacity duration-200 ${
            isTransitioning ? 'opacity-50' : 'opacity-100'
          }`}
          onError={(e) => {
            // Fallback to character initial if image fails to load
            e.currentTarget.style.display = 'none';
            const fallback = e.currentTarget.nextElementSibling as HTMLElement;
            if (fallback) {
              fallback.style.display = 'flex';
            }
          }}
        />

        {/* Fallback character initial (hidden by default) */}
        <div
          className={`absolute inset-0 flex items-center justify-center text-white font-bold transition-opacity duration-200 ${
            isTransitioning ? 'opacity-50' : 'opacity-100'
          }`}
          style={{ display: 'none' }}
        >
          <span className={size === 'large' ? 'text-4xl' : size === 'medium' ? 'text-2xl' : 'text-lg'}>
            {selectedPersona.persona.data.name.charAt(0)}
          </span>
        </div>

        {/* Transition overlay */}
        {isTransitioning && display.animationsEnabled && (
          <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
            <div className="animate-spin w-6 h-6 border-2 border-white border-t-transparent rounded-full"></div>
          </div>
        )}
      </div>

      {/* Mood Overlay */}
      {moodOverlayVisible && showMoodOverlay && display.animationsEnabled && (
        <div className={`absolute inset-0 rounded-lg ${moodConfig.color} flex items-center justify-center animate-pulse`}>
          <div className="text-center text-white">
            <div className={size === 'large' ? 'text-3xl' : size === 'medium' ? 'text-xl' : 'text-lg'}>
              {moodConfig.emoji}
            </div>
            {size === 'large' && (
              <div className="text-xs font-medium mt-1">{moodConfig.text}</div>
            )}
          </div>
        </div>
      )}

      {/* Status indicator dots */}
      <div className="absolute top-1 right-1 flex space-x-1">
        {/* Mode indicator */}
        <div
          className={`w-2 h-2 rounded-full ${
            assistant.status === 'active' ? 'bg-green-400' :
            assistant.status === 'idle' ? 'bg-gray-400' :
            'bg-yellow-400'
          }`}
          title={`Mode: ${assistant.status}`}
        />

        {/* Activity indicator */}
        {assistant.currentAction && assistant.currentAction !== 'idle' && (
          <div
            className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"
            title={`Activity: ${assistant.currentAction}`}
          />
        )}
      </div>

      {/* Expression label (for large size) */}
      {size === 'large' && (
        <div className="absolute bottom-0 left-0 right-0 bg-black/75 text-white p-2 text-center">
          <div className="text-xs font-medium">{displayExpression}</div>
        </div>
      )}
    </div>
  );
};

export default ExpressionDisplay;