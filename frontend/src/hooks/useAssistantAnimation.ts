/**
 * Hook for smooth assistant movement animations
 */

import { useEffect, useState, useRef } from 'react';
import { Position } from '../types/room';

interface UseAssistantAnimationProps {
  currentPosition: Position;
  targetPosition?: Position;
  isMoving: boolean;
  movementPath?: Position[];
  cellSize: { width: number; height: number };
  speed?: number; // cells per second
}

interface AssistantAnimationState {
  animatedPosition: Position;
  isAnimating: boolean;
  currentPathIndex: number;
}

export const useAssistantAnimation = ({
  currentPosition,
  targetPosition,
  isMoving,
  movementPath,
  cellSize,
  speed = 2 // Default: 2 cells per second
}: UseAssistantAnimationProps): AssistantAnimationState => {
  const [animatedPosition, setAnimatedPosition] = useState<Position>(currentPosition);
  const [isAnimating, setIsAnimating] = useState(false);
  const [currentPathIndex, setCurrentPathIndex] = useState(0);

  const animationRef = useRef<number>();
  const startTimeRef = useRef<number>();

  useEffect(() => {
    // If not moving or no path, just set to current position
    if (!isMoving || !movementPath || movementPath.length === 0) {
      setAnimatedPosition(currentPosition);
      setIsAnimating(false);
      setCurrentPathIndex(0);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      return;
    }

    // Start animation if we have a path
    if (movementPath.length > 1) {
      setIsAnimating(true);
      setCurrentPathIndex(0);
      startTimeRef.current = performance.now();

      const animate = (timestamp: number) => {
        if (!startTimeRef.current) {
          startTimeRef.current = timestamp;
        }

        const elapsed = timestamp - startTimeRef.current;
        const cellDuration = 1000 / speed; // ms per cell

        // Calculate which segment of the path we're on
        const totalElapsed = elapsed;
        const segmentIndex = Math.floor(totalElapsed / cellDuration);

        if (segmentIndex >= movementPath.length - 1) {
          // Animation complete - set to final position
          setAnimatedPosition(movementPath[movementPath.length - 1]);
          setIsAnimating(false);
          setCurrentPathIndex(movementPath.length - 1);
          return;
        }

        // Calculate interpolated position within current segment
        const segmentProgress = (totalElapsed % cellDuration) / cellDuration;
        const fromPos = movementPath[segmentIndex];
        const toPos = movementPath[segmentIndex + 1];

        const interpolatedPosition = {
          x: fromPos.x + (toPos.x - fromPos.x) * segmentProgress,
          y: fromPos.y + (toPos.y - fromPos.y) * segmentProgress
        };

        setAnimatedPosition(interpolatedPosition);
        setCurrentPathIndex(segmentIndex);

        animationRef.current = requestAnimationFrame(animate);
      };

      animationRef.current = requestAnimationFrame(animate);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isMoving, movementPath, speed, currentPosition]);

  return {
    animatedPosition,
    isAnimating,
    currentPathIndex
  };
};