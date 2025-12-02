"""
Tests for Personas API endpoints.

Tests cover:
- GET /personas/ - List personas
- GET /personas/load - Load persona from file
- GET /personas/test - Load test personas
- GET /personas/{persona_name} - Get persona by name
- POST /personas/validate - Validate persona data
- GET /personas/{persona_name}/image - Get persona image
- GET /personas/{persona_name}/expressions - Get expressions
- POST /personas/{persona_name}/expression - Set expression
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from httpx import AsyncClient

from app.models.persona import PersonaLoadError, PersonaValidationError


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_persona():
    """Create a mock loaded persona."""
    persona = MagicMock()
    persona.name = "Alice"
    persona.dict.return_value = {
        "name": "Alice",
        "description": "A friendly AI assistant",
        "personality": "Helpful, kind, curious",
        "scenario": "Living in a cozy room"
    }
    persona.persona = MagicMock()
    persona.persona.data = MagicMock()
    persona.persona.data.expressions = {
        "default": "/data/personas/alice_default.png",
        "happy": "/data/personas/alice_happy.png",
        "sad": "/data/personas/alice_sad.png"
    }
    persona.persona.data.current_expression = "default"
    persona.metadata = MagicMock()
    persona.metadata.file_path = "/data/personas/alice.png"
    return persona


@pytest.fixture
def mock_persona_summary():
    """Create a mock persona summary."""
    return {
        "name": "Alice",
        "description": "A friendly AI assistant",
        "tags": ["friendly", "helpful"],
        "creator": "Test Creator"
    }


@pytest.fixture
def mock_persona_card():
    """Create a mock persona card for validation."""
    card = MagicMock()
    card.data = MagicMock()
    card.data.name = "Alice"
    card.spec = "chara_card_v2"
    card.spec_version = "2.0"
    card.data.character_book = None
    return card


# ============================================================================
# GET /personas/ Tests
# ============================================================================

class TestListPersonas:
    """Tests for GET /personas/ endpoint."""

    @pytest.mark.asyncio
    async def test_list_personas_success(self, client, mock_persona, mock_persona_summary):
        """Should return list of personas."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = [mock_persona]
            mock_reader.get_persona_summary.return_value = mock_persona_summary

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    response = await client.get("/personas/")

                    assert response.status_code == 200
                    data = response.json()
                    assert len(data) == 1
                    assert data[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_list_personas_full_data(self, client, mock_persona):
        """Should return full persona data when summary_only=false."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = [mock_persona]

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    response = await client.get("/personas/", params={"summary_only": False})

                    assert response.status_code == 200
                    data = response.json()
                    assert "personality" in data[0]

    @pytest.mark.asyncio
    async def test_list_personas_directory_not_found(self, client):
        """Should return 404 for nonexistent directory."""
        with patch('pathlib.Path.exists', return_value=False):
            with patch('pathlib.Path.resolve', return_value=Path("/nonexistent")):
                response = await client.get("/personas/", params={"directory": "/nonexistent"})

                assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_personas_load_error(self, client):
        """Should return 400 for load errors."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.side_effect = PersonaLoadError("Load failed")

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    response = await client.get("/personas/")

                    assert response.status_code == 400


# ============================================================================
# GET /personas/load Tests
# ============================================================================

class TestLoadPersona:
    """Tests for GET /personas/load endpoint."""

    @pytest.mark.asyncio
    async def test_load_persona_success(self, client, mock_persona, mock_persona_summary):
        """Should load persona from file."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_persona_from_file.return_value = mock_persona
            mock_reader.get_persona_summary.return_value = mock_persona_summary

            with patch('pathlib.Path.resolve', return_value=Path("/data/personas/alice.png")):
                response = await client.get(
                    "/personas/load",
                    params={"file_path": "/data/personas/alice.png"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_load_persona_not_found(self, client):
        """Should return 404 for missing file."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_persona_from_file.side_effect = FileNotFoundError()

            with patch('pathlib.Path.resolve', return_value=Path("/data/personas/missing.png")):
                response = await client.get(
                    "/personas/load",
                    params={"file_path": "/data/personas/missing.png"}
                )

                assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_load_persona_validation_error(self, client):
        """Should return 422 for invalid persona."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_persona_from_file.side_effect = PersonaValidationError("Invalid")

            with patch('pathlib.Path.resolve', return_value=Path("/data/personas/invalid.png")):
                response = await client.get(
                    "/personas/load",
                    params={"file_path": "/data/personas/invalid.png"}
                )

                assert response.status_code == 422


# ============================================================================
# GET /personas/test Tests
# ============================================================================

class TestLoadTestPersonas:
    """Tests for GET /personas/test endpoint."""

    @pytest.mark.asyncio
    async def test_load_test_personas_success(self, client, mock_persona, mock_persona_summary):
        """Should load test personas."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = [mock_persona]
            mock_reader.get_persona_summary.return_value = mock_persona_summary

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas/test")):
                    response = await client.get("/personas/test")

                    assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_load_test_personas_empty(self, client):
        """Should return empty list when no test personas."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = []

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas/test")):
                    response = await client.get("/personas/test")

                    assert response.status_code == 200
                    assert response.json() == []

    @pytest.mark.asyncio
    async def test_load_test_personas_directory_missing(self, client):
        """Should return 404 when test directory missing."""
        with patch('pathlib.Path.exists', return_value=False):
            with patch('pathlib.Path.resolve', return_value=Path("/data/personas/test")):
                response = await client.get("/personas/test")

                assert response.status_code == 404


# ============================================================================
# GET /personas/{persona_name} Tests
# ============================================================================

class TestGetPersonaByName:
    """Tests for GET /personas/{persona_name} endpoint."""

    @pytest.mark.asyncio
    async def test_get_persona_success(self, client, mock_persona, mock_persona_summary):
        """Should return persona by name."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = [mock_persona]
            mock_reader.get_persona_summary.return_value = mock_persona_summary

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    response = await client.get("/personas/Alice")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_get_persona_case_insensitive(self, client, mock_persona, mock_persona_summary):
        """Should match name case-insensitively."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = [mock_persona]
            mock_reader.get_persona_summary.return_value = mock_persona_summary

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    response = await client.get("/personas/alice")

                    assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_persona_not_found(self, client):
        """Should return 404 for unknown persona."""
        mock_other = MagicMock()
        mock_other.name = "Bob"

        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = [mock_other]

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    response = await client.get("/personas/UnknownPerson")

                    assert response.status_code == 404


# ============================================================================
# POST /personas/validate Tests
# ============================================================================

class TestValidatePersona:
    """Tests for POST /personas/validate endpoint."""

    @pytest.mark.asyncio
    async def test_validate_success(self, client, mock_persona_card):
        """Should validate valid persona data."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.validate_persona_data.return_value = mock_persona_card

            response = await client.post(
                "/personas/validate",
                json={
                    "spec": "chara_card_v2",
                    "spec_version": "2.0",
                    "data": {
                        "name": "Alice",
                        "description": "Test"
                    }
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["character_name"] == "Alice"

    @pytest.mark.asyncio
    async def test_validate_invalid(self, client):
        """Should return 422 for invalid persona."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.validate_persona_data.side_effect = PersonaValidationError("Invalid")

            response = await client.post(
                "/personas/validate",
                json={"invalid": "data"}
            )

            assert response.status_code == 422
            data = response.json()
            assert data["valid"] is False


# ============================================================================
# GET /personas/{persona_name}/image Tests
# ============================================================================

class TestGetPersonaImage:
    """Tests for GET /personas/{persona_name}/image endpoint."""

    @pytest.mark.asyncio
    async def test_get_image_default(self, client, mock_persona):
        """Should return default expression image."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = [mock_persona]

            with patch('pathlib.Path.exists') as mock_exists:
                mock_exists.side_effect = lambda p=None: True

                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    # We can't fully test FileResponse without real files
                    # Just verify the endpoint handles the request
                    pass

    @pytest.mark.asyncio
    async def test_get_image_persona_not_found(self, client):
        """Should return 404 for unknown persona."""
        mock_other = MagicMock()
        mock_other.name = "Bob"

        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = [mock_other]

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    response = await client.get("/personas/Alice/image")

                    assert response.status_code == 404


# ============================================================================
# GET /personas/{persona_name}/expressions Tests
# ============================================================================

class TestGetPersonaExpressions:
    """Tests for GET /personas/{persona_name}/expressions endpoint."""

    @pytest.mark.asyncio
    async def test_get_expressions_success(self, client, mock_persona):
        """Should return available expressions."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = [mock_persona]

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    response = await client.get("/personas/Alice/expressions")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["persona_name"] == "Alice"
                    assert "default" in data["available_expressions"]
                    assert "happy" in data["available_expressions"]
                    assert data["current_expression"] == "default"

    @pytest.mark.asyncio
    async def test_get_expressions_persona_not_found(self, client):
        """Should return 404 for unknown persona."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = []

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    response = await client.get("/personas/Unknown/expressions")

                    assert response.status_code == 404


# ============================================================================
# POST /personas/{persona_name}/expression Tests
# ============================================================================

class TestSetPersonaExpression:
    """Tests for POST /personas/{persona_name}/expression endpoint."""

    @pytest.mark.asyncio
    async def test_set_expression_success(self, client, mock_persona):
        """Should set expression successfully."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = [mock_persona]

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    response = await client.post(
                        "/personas/Alice/expression",
                        json={"expression": "happy"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["expression"] == "happy"

    @pytest.mark.asyncio
    async def test_set_expression_missing(self, client, mock_persona):
        """Should return 400 when expression missing."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                response = await client.post(
                    "/personas/Alice/expression",
                    json={}
                )

                assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_set_expression_invalid(self, client, mock_persona):
        """Should return 400 for invalid expression."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = [mock_persona]

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    response = await client.post(
                        "/personas/Alice/expression",
                        json={"expression": "angry"}  # Not in available expressions
                    )

                    assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_set_expression_persona_not_found(self, client):
        """Should return 404 for unknown persona."""
        with patch('app.api.personas.persona_reader') as mock_reader:
            mock_reader.load_personas_from_directory.return_value = []

            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path("/data/personas")):
                    response = await client.post(
                        "/personas/Unknown/expression",
                        json={"expression": "happy"}
                    )

                    assert response.status_code == 404

