"""
Pydantic models for SillyTavern V2 persona cards.

Supports the SillyTavern character card specification v2.0:
https://github.com/SillyTavern/SillyTavern/blob/release/docs/character-card-spec-v2.md
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class CharacterBook(BaseModel):
    """Character book/lorebook for world information."""
    entries: List[Dict[str, Any]] = Field(default_factory=list)
    name: str = ""
    description: str = ""
    scan_depth: Optional[int] = None
    token_budget: Optional[int] = None
    recursive_scanning: Optional[bool] = None


class PersonaData(BaseModel):
    """Main character data from SillyTavern V2 format."""

    # Core required fields
    name: str = Field(..., description="Character name")
    description: str = Field(default="", description="Detailed character description")
    personality: str = Field(default="", description="Personality summary")
    scenario: str = Field(default="", description="Setting/context")
    first_mes: str = Field(default="", description="Initial greeting message")
    mes_example: str = Field(default="", description="Example dialogue")

    # Optional core fields
    creator_notes: str = Field(default="", description="Notes from creator")
    system_prompt: str = Field(default="", description="System instructions")
    post_history_instructions: str = Field(default="", description="Additional instructions")

    # Arrays
    alternate_greetings: List[str] = Field(default_factory=list, description="Alternative greeting messages")
    tags: List[str] = Field(default_factory=list, description="Character tags")

    # Metadata
    creator: str = Field(default="", description="Creator username")
    character_version: str = Field(default="", description="Version identifier")
    avatar: str = Field(default="none", description="Avatar reference")

    # Extensions and advanced features
    extensions: Dict[str, Any] = Field(default_factory=dict, description="Extensions/plugins data")
    character_book: Optional[CharacterBook] = Field(None, description="Lorebook/world info")

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Character name cannot be empty')
        return v.strip()

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        # Remove empty tags and duplicates, maintain order
        seen = set()
        result = []
        for tag in v:
            clean_tag = tag.strip()
            if clean_tag and clean_tag not in seen:
                result.append(clean_tag)
                seen.add(clean_tag)
        return result


class PersonaCard(BaseModel):
    """Complete SillyTavern V2 persona card."""

    spec: str = Field(..., description="Card specification identifier")
    spec_version: str = Field(..., description="Specification version")
    data: PersonaData = Field(..., description="Character data")

    @field_validator('spec')
    @classmethod
    def validate_spec(cls, v):
        if v != "chara_card_v2":
            raise ValueError(f'Unsupported spec: {v}. Expected "chara_card_v2"')
        return v

    @field_validator('spec_version')
    @classmethod
    def validate_spec_version(cls, v):
        if v != "2.0":
            raise ValueError(f'Unsupported spec version: {v}. Expected "2.0"')
        return v


class PersonaMetadata(BaseModel):
    """Metadata about a loaded persona."""

    file_path: str = Field(..., description="Path to the persona PNG file")
    file_size: int = Field(..., description="File size in bytes")
    loaded_at: datetime = Field(default_factory=datetime.utcnow, description="When the persona was loaded")
    character_name: str = Field(..., description="Character name for quick reference")
    creator: str = Field(default="", description="Creator name")
    tags: List[str] = Field(default_factory=list, description="Character tags")
    has_lorebook: bool = Field(False, description="Whether character has lorebook data")


class LoadedPersona(BaseModel):
    """A fully loaded and validated persona with metadata."""

    persona: PersonaCard = Field(..., description="The persona card data")
    metadata: PersonaMetadata = Field(..., description="Metadata about the loaded persona")

    @property
    def name(self) -> str:
        """Quick access to character name."""
        return self.persona.data.name

    @property
    def description(self) -> str:
        """Quick access to character description."""
        return self.persona.data.description

    @property
    def first_message(self) -> str:
        """Quick access to first message."""
        return self.persona.data.first_mes

    def get_greeting(self, index: int = 0) -> str:
        """Get a greeting message by index (0 = default, 1+ = alternates)."""
        if index == 0:
            return self.persona.data.first_mes

        alt_greetings = self.persona.data.alternate_greetings
        if 0 < index <= len(alt_greetings):
            return alt_greetings[index - 1]

        return self.persona.data.first_mes  # Fallback to default


class PersonaValidationError(Exception):
    """Raised when persona validation fails."""
    pass


class PersonaLoadError(Exception):
    """Raised when persona loading fails."""
    pass