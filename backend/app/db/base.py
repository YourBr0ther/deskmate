"""
SQLAlchemy Base class for models.

This module provides the declarative base to avoid circular imports.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()