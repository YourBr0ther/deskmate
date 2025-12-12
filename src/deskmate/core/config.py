"""Configuration loader with Pydantic validation."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class DisplayConfig(BaseModel):
    """Display/window configuration."""

    width: int = 1024
    height: int = 768
    fps: int = 60
    title: str = "DeskMate"


class CompanionConfig(BaseModel):
    """Companion behavior configuration."""

    move_speed: float = 150.0
    animation_fps: int = 10
    start_x: int = 512
    start_y: int = 500


class WalkableAreaConfig(BaseModel):
    """Walkable area bounds."""

    min_x: int = 50
    max_x: int = 974
    min_y: int = 400
    max_y: int = 700


class RoomConfig(BaseModel):
    """Room configuration."""

    name: str = "Bedroom"
    walkable_area: WalkableAreaConfig = Field(default_factory=WalkableAreaConfig)


class ChatConfig(BaseModel):
    """Chat UI configuration."""

    panel_width: int = 300
    panel_height: int = 500
    panel_x: int = 700
    panel_y: int = 50
    max_history: int = 50
    font_size: int = 16


class OllamaConfig(BaseModel):
    """Ollama API configuration."""

    host: str = "http://localhost:11434"
    model: str = "llama3.2"
    timeout: int = 30


class PathsConfig(BaseModel):
    """Asset paths configuration."""

    assets: str = "assets/"
    sprites: str = "assets/sprites/"
    config: str = "config/"


class Settings(BaseModel):
    """Root settings configuration."""

    display: DisplayConfig = Field(default_factory=DisplayConfig)
    companion: CompanionConfig = Field(default_factory=CompanionConfig)
    room: RoomConfig = Field(default_factory=RoomConfig)
    chat: ChatConfig = Field(default_factory=ChatConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)


class PersonalityTraits(BaseModel):
    """Personality configuration."""

    name: str = "Pixel"
    traits: list[str] = Field(default_factory=list)
    speech_style: list[str] = Field(default_factory=list)
    background: str = ""
    example_responses: dict[str, str] = Field(default_factory=dict)
    system_prompt_template: str = ""


class PersonalityConfig(BaseModel):
    """Root personality configuration."""

    personality: PersonalityTraits = Field(default_factory=PersonalityTraits)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents."""
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_settings(config_dir: Path | None = None) -> Settings:
    """Load settings from config/settings.yaml."""
    if config_dir is None:
        config_dir = Path(__file__).parent.parent.parent.parent / "config"

    settings_path = config_dir / "settings.yaml"

    if settings_path.exists():
        data = load_yaml(settings_path)
        return Settings.model_validate(data)

    return Settings()


def load_personality(config_dir: Path | None = None) -> PersonalityConfig:
    """Load personality from config/personality.yaml."""
    if config_dir is None:
        config_dir = Path(__file__).parent.parent.parent.parent / "config"

    personality_path = config_dir / "personality.yaml"

    if personality_path.exists():
        data = load_yaml(personality_path)
        return PersonalityConfig.model_validate(data)

    return PersonalityConfig()


# Singleton instances for easy access
_settings: Settings | None = None
_personality: PersonalityConfig | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def get_personality() -> PersonalityConfig:
    """Get the global personality instance."""
    global _personality
    if _personality is None:
        _personality = load_personality()
    return _personality


def reset_config() -> None:
    """Reset config singletons (useful for testing)."""
    global _settings, _personality
    _settings = None
    _personality = None
