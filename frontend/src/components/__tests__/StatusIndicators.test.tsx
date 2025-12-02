/**
 * Tests for StatusIndicators Component
 *
 * Tests cover:
 * - Compact mode rendering
 * - Full mode rendering
 * - Mood indicators
 * - Status indicators
 * - Action indicators
 * - Energy level display
 * - Position display
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import StatusIndicators from '../StatusIndicators';

// Mock spatial store
let mockAssistant = {
  mood: 'neutral',
  status: 'active',
  current_action: null as string | null,
  energy_level: 1,
  position: { x: 10, y: 5 },
  facing: 'right',
  holding_object_id: null as string | null,
  sitting_on_object_id: null as string | null,
};

jest.mock('../../stores/spatialStore', () => ({
  useSpatialStore: (selector: (state: any) => any) =>
    selector({ assistant: mockAssistant }),
}));

describe('StatusIndicators', () => {
  beforeEach(() => {
    mockAssistant = {
      mood: 'neutral',
      status: 'active',
      current_action: null,
      energy_level: 1,
      position: { x: 10, y: 5 },
      facing: 'right',
      holding_object_id: null,
      sitting_on_object_id: null,
    };
  });

  describe('Mood Indicators', () => {
    it('should show happy mood with emoji', () => {
      mockAssistant.mood = 'happy';
      render(<StatusIndicators />);

      expect(screen.getByText('😊')).toBeInTheDocument();
      expect(screen.getByText('Happy')).toBeInTheDocument();
    });

    it('should show excited mood with emoji', () => {
      mockAssistant.mood = 'excited';
      render(<StatusIndicators />);

      expect(screen.getByText('🤩')).toBeInTheDocument();
      expect(screen.getByText('Excited')).toBeInTheDocument();
    });

    it('should show sad mood with emoji', () => {
      mockAssistant.mood = 'sad';
      render(<StatusIndicators />);

      expect(screen.getByText('😢')).toBeInTheDocument();
      expect(screen.getByText('Sad')).toBeInTheDocument();
    });

    it('should show tired mood with emoji', () => {
      mockAssistant.mood = 'tired';
      render(<StatusIndicators />);

      expect(screen.getByText('😴')).toBeInTheDocument();
      expect(screen.getByText('Tired')).toBeInTheDocument();
    });

    it('should show neutral mood by default', () => {
      mockAssistant.mood = 'neutral';
      render(<StatusIndicators />);

      expect(screen.getByText('😐')).toBeInTheDocument();
      expect(screen.getByText('Neutral')).toBeInTheDocument();
    });

    it('should show mood description', () => {
      mockAssistant.mood = 'happy';
      render(<StatusIndicators />);

      expect(screen.getByText('Happy and content')).toBeInTheDocument();
    });
  });

  describe('Status Indicators', () => {
    it('should show active status', () => {
      mockAssistant.status = 'active';
      render(<StatusIndicators />);

      expect(screen.getByText('🟢')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('should show idle status', () => {
      mockAssistant.status = 'idle';
      render(<StatusIndicators />);

      expect(screen.getByText('💭')).toBeInTheDocument();
      expect(screen.getByText('Idle')).toBeInTheDocument();
    });

    it('should show busy status', () => {
      mockAssistant.status = 'busy';
      render(<StatusIndicators />);

      expect(screen.getByText('🟡')).toBeInTheDocument();
      expect(screen.getByText('Busy')).toBeInTheDocument();
    });

    it('should show status description', () => {
      mockAssistant.status = 'active';
      render(<StatusIndicators />);

      expect(screen.getByText('Active and responsive')).toBeInTheDocument();
    });
  });

  describe('Action Indicators', () => {
    it('should show walking action', () => {
      mockAssistant.current_action = 'walking';
      render(<StatusIndicators />);

      expect(screen.getByText('🚶‍♂️')).toBeInTheDocument();
      expect(screen.getByText('Walking')).toBeInTheDocument();
    });

    it('should show sitting action', () => {
      mockAssistant.current_action = 'sitting';
      render(<StatusIndicators />);

      expect(screen.getByText('💺')).toBeInTheDocument();
      expect(screen.getByText('Sitting')).toBeInTheDocument();
    });

    it('should show talking action', () => {
      mockAssistant.current_action = 'talking';
      render(<StatusIndicators />);

      expect(screen.getByText('💬')).toBeInTheDocument();
      expect(screen.getByText('Talking')).toBeInTheDocument();
    });

    it('should show thinking action', () => {
      mockAssistant.current_action = 'thinking';
      render(<StatusIndicators />);

      expect(screen.getByText('🤔')).toBeInTheDocument();
      expect(screen.getByText('Thinking')).toBeInTheDocument();
    });

    it('should not show action section when no action', () => {
      mockAssistant.current_action = null;
      render(<StatusIndicators />);

      expect(screen.queryByText('Current activity')).not.toBeInTheDocument();
    });
  });

  describe('Energy Level', () => {
    it('should show 100% energy', () => {
      mockAssistant.energy_level = 1;
      render(<StatusIndicators />);

      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('should show 50% energy', () => {
      mockAssistant.energy_level = 0.5;
      render(<StatusIndicators />);

      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('should show 25% energy', () => {
      mockAssistant.energy_level = 0.25;
      render(<StatusIndicators />);

      expect(screen.getByText('25%')).toBeInTheDocument();
    });

    it('should have energy progress bar', () => {
      mockAssistant.energy_level = 0.75;
      const { container } = render(<StatusIndicators />);

      const progressBar = container.querySelector('.bg-gradient-to-r');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveStyle({ width: '75%' });
    });
  });

  describe('Position Display', () => {
    it('should show position coordinates', () => {
      mockAssistant.position = { x: 15, y: 8 };
      render(<StatusIndicators />);

      expect(screen.getByText('Position (15, 8)')).toBeInTheDocument();
    });

    it('should show facing direction', () => {
      mockAssistant.facing = 'left';
      render(<StatusIndicators />);

      expect(screen.getByText(/facing left/i)).toBeInTheDocument();
    });

    it('should show holding object indicator', () => {
      mockAssistant.holding_object_id = 'obj-123';
      render(<StatusIndicators />);

      expect(screen.getByText(/holding object/i)).toBeInTheDocument();
    });

    it('should show sitting indicator', () => {
      mockAssistant.sitting_on_object_id = 'chair-1';
      render(<StatusIndicators />);

      expect(screen.getByText(/sitting/i)).toBeInTheDocument();
    });
  });

  describe('Compact Mode', () => {
    it('should render compact version', () => {
      mockAssistant.mood = 'happy';
      mockAssistant.status = 'active';

      const { container } = render(<StatusIndicators compact />);

      // Compact mode should have smaller elements
      expect(container.querySelector('.w-8.h-8')).toBeInTheDocument();
    });

    it('should show mood emoji in compact mode', () => {
      mockAssistant.mood = 'happy';
      render(<StatusIndicators compact />);

      expect(screen.getByText('😊')).toBeInTheDocument();
    });

    it('should show status icon in compact mode', () => {
      mockAssistant.status = 'active';
      render(<StatusIndicators compact />);

      expect(screen.getByText('🟢')).toBeInTheDocument();
    });

    it('should show action icon when action exists in compact mode', () => {
      mockAssistant.current_action = 'walking';
      render(<StatusIndicators compact />);

      expect(screen.getByText('🚶‍♂️')).toBeInTheDocument();
    });

    it('should not show action icon when no action in compact mode', () => {
      mockAssistant.current_action = null;
      render(<StatusIndicators compact />);

      expect(screen.queryByText('🚶‍♂️')).not.toBeInTheDocument();
    });
  });

  describe('Custom className', () => {
    it('should apply custom className', () => {
      const { container } = render(<StatusIndicators className="custom-class" />);

      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });
  });

  describe('Tooltips', () => {
    it('should have tooltip on mood indicator in compact mode', () => {
      mockAssistant.mood = 'happy';
      render(<StatusIndicators compact />);

      const moodIndicator = screen.getByTitle(/mood: happy/i);
      expect(moodIndicator).toBeInTheDocument();
    });

    it('should have tooltip on status indicator in compact mode', () => {
      mockAssistant.status = 'active';
      render(<StatusIndicators compact />);

      const statusIndicator = screen.getByTitle(/status: active/i);
      expect(statusIndicator).toBeInTheDocument();
    });
  });
});
