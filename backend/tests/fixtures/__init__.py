"""
Test fixtures package for DeskMate backend.

Provides mock implementations for:
- LLM providers (Nano-GPT, Ollama)
- Database (PostgreSQL via SQLite)
- Vector database (Qdrant)
"""

from .mock_llm import *
from .mock_database import *
from .mock_qdrant import *
