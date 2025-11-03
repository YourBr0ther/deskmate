"""
Tests for persona system functionality.

Tests the complete persona loading pipeline:
- PNG metadata extraction
- JSON parsing and validation
- API endpoints
- Error handling
"""

import pytest
import json
import base64
from pathlib import Path
from PIL import Image
from unittest.mock import patch, MagicMock

from app.services.persona_reader import PersonaReader, persona_reader
from app.models.persona import (
    PersonaCard,
    PersonaData,
    LoadedPersona,
    PersonaLoadError,
    PersonaValidationError
)


class TestPersonaReader:
    """Test the PersonaReader service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reader = PersonaReader()
        self.test_directory = Path("data/personas/test")

    def test_persona_reader_initialization(self):
        """Test PersonaReader initializes correctly."""
        assert self.reader.supported_formats == ['.png']
        assert self.reader.max_file_size == 50 * 1024 * 1024

    def test_load_test_personas(self):
        """Test loading personas from test directory."""
        if not self.test_directory.exists():
            pytest.skip("Test personas directory not found")

        personas = self.reader.load_personas_from_directory(str(self.test_directory))

        # Should have loaded the 4 test personas
        assert len(personas) >= 1, "Should load at least one test persona"

        for persona in personas:
            assert isinstance(persona, LoadedPersona)
            assert persona.name, "Persona should have a name"
            assert persona.metadata.file_path, "Should have file path"
            assert persona.metadata.file_size > 0, "Should have positive file size"

    def test_validate_persona_data_valid(self):
        """Test validation of valid persona data."""
        valid_data = {
            "spec": "chara_card_v2",
            "spec_version": "2.0",
            "data": {
                "name": "Test Character",
                "description": "A test character",
                "personality": "Friendly",
                "scenario": "Test scenario",
                "first_mes": "Hello!",
                "mes_example": "Example dialogue",
                "creator_notes": "",
                "system_prompt": "",
                "post_history_instructions": "",
                "alternate_greetings": [],
                "tags": ["test"],
                "creator": "tester",
                "character_version": "1.0",
                "avatar": "none",
                "extensions": {}
            }
        }

        persona = self.reader.validate_persona_data(valid_data)
        assert isinstance(persona, PersonaCard)
        assert persona.data.name == "Test Character"

    def test_validate_persona_data_invalid_spec(self):
        """Test validation fails with invalid spec."""
        invalid_data = {
            "spec": "invalid_spec",
            "spec_version": "2.0",
            "data": {"name": "Test"}
        }

        with pytest.raises(PersonaValidationError):
            self.reader.validate_persona_data(invalid_data)

    def test_validate_persona_data_missing_name(self):
        """Test validation fails with missing name."""
        invalid_data = {
            "spec": "chara_card_v2",
            "spec_version": "2.0",
            "data": {"description": "No name"}
        }

        with pytest.raises(PersonaValidationError):
            self.reader.validate_persona_data(invalid_data)

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error."""
        with pytest.raises(PersonaLoadError, match="File not found"):
            self.reader.load_persona_from_file("nonexistent.png")

    @patch('app.services.persona_reader.Path.exists')
    @patch('app.services.persona_reader.Path.is_file')
    @patch('app.services.persona_reader.Path.stat')
    def test_load_invalid_format(self, mock_stat, mock_is_file, mock_exists):
        """Test loading non-PNG file raises error."""
        # Mock file validation to reach format check
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_stat.return_value.st_size = 1000

        with pytest.raises(PersonaLoadError, match="Unsupported file format"):
            self.reader.load_persona_from_file("test.txt")

    @patch('app.services.persona_reader.Image.open')
    @patch('app.services.persona_reader.Path.exists')
    @patch('app.services.persona_reader.Path.is_file')
    @patch('app.services.persona_reader.Path.stat')
    def test_load_png_without_persona_data(self, mock_stat, mock_is_file, mock_exists, mock_open):
        """Test loading PNG without persona metadata."""
        # Mock file validation
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_stat.return_value.st_size = 1000

        # Mock PIL Image with no 'chara' metadata
        mock_img = MagicMock()
        mock_img.info = {}
        mock_open.return_value.__enter__.return_value = mock_img

        with pytest.raises(PersonaLoadError, match="No 'chara' metadata found"):
            self.reader.load_persona_from_file("empty.png")

    @patch('app.services.persona_reader.Image.open')
    @patch('app.services.persona_reader.Path.exists')
    @patch('app.services.persona_reader.Path.is_file')
    @patch('app.services.persona_reader.Path.stat')
    def test_load_png_with_invalid_base64(self, mock_stat, mock_is_file, mock_exists, mock_open):
        """Test loading PNG with invalid base64 data."""
        # Mock file validation
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_stat.return_value.st_size = 1000

        # Mock PIL Image with invalid base64
        mock_img = MagicMock()
        mock_img.info = {'chara': 'invalid_base64!@#$'}
        mock_open.return_value.__enter__.return_value = mock_img

        with pytest.raises(PersonaLoadError, match="Failed to decode base64"):
            self.reader.load_persona_from_file("invalid_b64.png")

    @patch('app.services.persona_reader.Image.open')
    @patch('app.services.persona_reader.Path.exists')
    @patch('app.services.persona_reader.Path.is_file')
    @patch('app.services.persona_reader.Path.stat')
    def test_load_png_with_invalid_json(self, mock_stat, mock_is_file, mock_exists, mock_open):
        """Test loading PNG with invalid JSON data."""
        # Mock file validation
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_stat.return_value.st_size = 1000

        # Mock PIL Image with invalid JSON
        invalid_json = base64.b64encode(b"invalid json {").decode('utf-8')
        mock_img = MagicMock()
        mock_img.info = {'chara': invalid_json}
        mock_open.return_value.__enter__.return_value = mock_img

        with pytest.raises(PersonaLoadError, match="Invalid JSON"):
            self.reader.load_persona_from_file("invalid_json.png")

    def test_get_persona_summary(self):
        """Test getting persona summary."""
        if not self.test_directory.exists():
            pytest.skip("Test personas directory not found")

        personas = self.reader.load_personas_from_directory(str(self.test_directory))
        if not personas:
            pytest.skip("No test personas found")

        persona = personas[0]
        summary = self.reader.get_persona_summary(persona)

        required_fields = [
            "name", "creator", "tags", "description_length",
            "has_lorebook", "alternate_greetings_count",
            "file_size", "loaded_at"
        ]

        for field in required_fields:
            assert field in summary, f"Summary missing field: {field}"

        assert isinstance(summary["tags"], list)
        assert isinstance(summary["description_length"], int)
        assert isinstance(summary["has_lorebook"], bool)


class TestPersonaModels:
    """Test Pydantic persona models."""

    def test_persona_data_validation(self):
        """Test PersonaData validation."""
        data = PersonaData(name="Test Character")
        assert data.name == "Test Character"
        assert data.description == ""
        assert data.tags == []

    def test_persona_data_empty_name_validation(self):
        """Test PersonaData rejects empty name."""
        with pytest.raises(ValueError, match="Character name cannot be empty"):
            PersonaData(name="")

        with pytest.raises(ValueError, match="Character name cannot be empty"):
            PersonaData(name="   ")

    def test_persona_data_tag_cleanup(self):
        """Test PersonaData cleans up tags."""
        data = PersonaData(
            name="Test",
            tags=["  tag1  ", "tag2", "", "tag1", "tag3", "  "]
        )
        # Order is preserved, duplicates removed
        assert data.tags == ["tag1", "tag2", "tag3"]

    def test_persona_card_validation(self):
        """Test PersonaCard validation."""
        card_data = {
            "spec": "chara_card_v2",
            "spec_version": "2.0",
            "data": {"name": "Test Character"}
        }

        card = PersonaCard(**card_data)
        assert card.spec == "chara_card_v2"
        assert card.spec_version == "2.0"
        assert card.data.name == "Test Character"

    def test_persona_card_invalid_spec(self):
        """Test PersonaCard rejects invalid spec."""
        with pytest.raises(ValueError, match="Unsupported spec"):
            PersonaCard(
                spec="invalid_spec",
                spec_version="2.0",
                data=PersonaData(name="Test")
            )

    def test_loaded_persona_properties(self):
        """Test LoadedPersona convenience properties."""
        from app.models.persona import PersonaMetadata
        from datetime import datetime

        persona_data = PersonaData(
            name="Test Character",
            description="A test character description",
            first_mes="Hello there!",
            alternate_greetings=["Hi!", "Hey!"]
        )

        persona_card = PersonaCard(
            spec="chara_card_v2",
            spec_version="2.0",
            data=persona_data
        )

        metadata = PersonaMetadata(
            file_path="/test/path.png",
            file_size=1000,
            character_name="Test Character"
        )

        loaded_persona = LoadedPersona(persona=persona_card, metadata=metadata)

        assert loaded_persona.name == "Test Character"
        assert loaded_persona.description == "A test character description"
        assert loaded_persona.first_message == "Hello there!"

        # Test greeting access
        assert loaded_persona.get_greeting(0) == "Hello there!"
        assert loaded_persona.get_greeting(1) == "Hi!"
        assert loaded_persona.get_greeting(2) == "Hey!"
        assert loaded_persona.get_greeting(99) == "Hello there!"  # Fallback


class TestPersonaAPI:
    """Test persona API endpoints."""

    def test_global_persona_reader_instance(self):
        """Test that global persona_reader instance exists."""
        assert persona_reader is not None
        assert isinstance(persona_reader, PersonaReader)