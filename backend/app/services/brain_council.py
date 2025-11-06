"""
Brain Council - Compatibility layer for the refactored Brain Council system.

This file provides backward compatibility by importing from the new
modular brain council implementation.

The new implementation provides:
- Improved separation of concerns with individual reasoners
- Better testability and maintainability
- Parallel execution capabilities
- Centralized prompt building and response parsing

While maintaining 100% API compatibility with existing code.
"""

# Import the refactored implementation
from app.services.brain_council.brain_council import BrainCouncil, brain_council

# Re-export for backward compatibility
__all__ = ['BrainCouncil', 'brain_council']