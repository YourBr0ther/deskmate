"""
Service for reading and parsing SillyTavern V2 persona cards from PNG files.

This service handles:
- PNG metadata extraction
- Base64 decoding
- JSON parsing and validation
- Error handling for malformed cards
"""

import base64
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image
import logging

from ..models.persona import (
    PersonaCard,
    PersonaData,
    PersonaMetadata,
    LoadedPersona,
    PersonaValidationError,
    PersonaLoadError
)

logger = logging.getLogger(__name__)


class PersonaReader:
    """Service for reading SillyTavern V2 persona cards from PNG files."""

    def __init__(self):
        self.supported_formats = ['.png']
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit

    def load_persona_from_file(self, file_path: str) -> LoadedPersona:
        """
        Load and validate a persona card from a PNG file.

        Args:
            file_path: Path to the PNG file containing the persona card

        Returns:
            LoadedPersona: Validated persona with metadata

        Raises:
            PersonaLoadError: If file cannot be loaded or parsed
            PersonaValidationError: If persona data is invalid
        """
        try:
            # Validate file path and size
            path = Path(file_path)
            self._validate_file(path)

            # Extract persona data from PNG
            persona_data = self._extract_persona_from_png(file_path)

            # Parse and validate the persona
            persona_card = self._parse_persona_data(persona_data)

            # Create metadata
            metadata = self._create_metadata(file_path, persona_card.data)

            return LoadedPersona(persona=persona_card, metadata=metadata)

        except (PersonaLoadError, PersonaValidationError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading persona from {file_path}: {e}")
            raise PersonaLoadError(f"Failed to load persona: {str(e)}")

    def load_personas_from_directory(self, directory_path: str) -> List[LoadedPersona]:
        """
        Load all valid persona cards from a directory.

        Args:
            directory_path: Path to directory containing PNG persona cards

        Returns:
            List[LoadedPersona]: List of successfully loaded personas

        Note:
            Invalid files are logged as warnings but don't stop the process
        """
        personas = []
        directory = Path(directory_path)

        if not directory.exists() or not directory.is_dir():
            raise PersonaLoadError(f"Directory not found: {directory_path}")

        for file_path in directory.rglob("*.png"):
            try:
                persona = self.load_persona_from_file(str(file_path))
                personas.append(persona)
                logger.info(f"Loaded persona '{persona.name}' from {file_path.name}")
            except (PersonaLoadError, PersonaValidationError) as e:
                logger.warning(f"Skipping invalid persona file {file_path.name}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error with {file_path.name}: {e}")
                continue

        return personas

    def validate_persona_data(self, persona_data: Dict[str, Any]) -> PersonaCard:
        """
        Validate raw persona data against SillyTavern V2 schema.

        Args:
            persona_data: Raw persona data dictionary

        Returns:
            PersonaCard: Validated persona card

        Raises:
            PersonaValidationError: If validation fails
        """
        try:
            return PersonaCard(**persona_data)
        except Exception as e:
            raise PersonaValidationError(f"Persona validation failed: {str(e)}")

    def _validate_file(self, file_path: Path) -> None:
        """Validate file exists, is readable, and meets size requirements."""
        if not file_path.exists():
            raise PersonaLoadError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise PersonaLoadError(f"Path is not a file: {file_path}")

        if file_path.suffix.lower() not in self.supported_formats:
            raise PersonaLoadError(f"Unsupported file format: {file_path.suffix}")

        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise PersonaLoadError(f"File too large: {file_size} bytes (max: {self.max_file_size})")

        if file_size == 0:
            raise PersonaLoadError("File is empty")

    def _extract_persona_from_png(self, file_path: str) -> Dict[str, Any]:
        """
        Extract persona data from PNG metadata.

        Args:
            file_path: Path to PNG file

        Returns:
            Dict containing persona data

        Raises:
            PersonaLoadError: If extraction fails
        """
        try:
            with Image.open(file_path) as img:
                # Look for SillyTavern persona data in PNG text chunks
                chara_data = img.info.get('chara')

                if not chara_data:
                    raise PersonaLoadError("No 'chara' metadata found in PNG file")

                # Decode base64 data
                try:
                    decoded_bytes = base64.b64decode(chara_data)
                    decoded_str = decoded_bytes.decode('utf-8')
                except Exception as e:
                    raise PersonaLoadError(f"Failed to decode base64 persona data: {e}")

                # Parse JSON
                try:
                    persona_data = json.loads(decoded_str)
                except json.JSONDecodeError as e:
                    raise PersonaLoadError(f"Invalid JSON in persona data: {e}")

                return persona_data

        except PersonaLoadError:
            raise
        except Exception as e:
            raise PersonaLoadError(f"Failed to read PNG file: {e}")

    def _parse_persona_data(self, persona_data: Dict[str, Any]) -> PersonaCard:
        """
        Parse and validate persona data.

        Args:
            persona_data: Raw persona data from PNG

        Returns:
            PersonaCard: Validated persona card

        Raises:
            PersonaValidationError: If validation fails
        """
        # Validate required top-level structure
        if not isinstance(persona_data, dict):
            raise PersonaValidationError("Persona data must be a dictionary")

        required_fields = ['spec', 'spec_version', 'data']
        missing_fields = [field for field in required_fields if field not in persona_data]
        if missing_fields:
            raise PersonaValidationError(f"Missing required fields: {missing_fields}")

        # Validate using Pydantic model
        try:
            return PersonaCard(**persona_data)
        except Exception as e:
            raise PersonaValidationError(f"Persona validation failed: {str(e)}")

    def _create_metadata(self, file_path: str, persona_data: PersonaData) -> PersonaMetadata:
        """Create metadata object for a loaded persona."""
        path = Path(file_path)
        file_size = path.stat().st_size

        return PersonaMetadata(
            file_path=file_path,
            file_size=file_size,
            character_name=persona_data.name,
            creator=persona_data.creator,
            tags=persona_data.tags,
            has_lorebook=persona_data.character_book is not None
        )

    def get_persona_summary(self, persona: LoadedPersona) -> Dict[str, Any]:
        """
        Get a summary of persona information for API responses.

        Args:
            persona: Loaded persona

        Returns:
            Dict with summary information
        """
        return {
            "name": persona.name,
            "creator": persona.persona.data.creator,
            "tags": persona.persona.data.tags,
            "description_length": len(persona.persona.data.description),
            "has_lorebook": persona.metadata.has_lorebook,
            "alternate_greetings_count": len(persona.persona.data.alternate_greetings),
            "file_size": persona.metadata.file_size,
            "loaded_at": persona.metadata.loaded_at.isoformat()
        }


# Global instance for dependency injection
persona_reader = PersonaReader()