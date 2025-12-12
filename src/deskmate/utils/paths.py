"""Path utilities for asset resolution."""

from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent.parent


def get_assets_dir() -> Path:
    """Get the assets directory."""
    return get_project_root() / "assets"


def get_config_dir() -> Path:
    """Get the config directory."""
    return get_project_root() / "config"


def get_sprite_path(sprite_name: str) -> Path:
    """Get the path to a sprite file."""
    return get_assets_dir() / "sprites" / sprite_name


def get_background_path(background_name: str) -> Path:
    """Get the path to a background file."""
    return get_assets_dir() / "backgrounds" / background_name


def get_object_sprite_path(object_name: str) -> Path:
    """Get the path to an object sprite file."""
    return get_assets_dir() / "objects" / object_name


def get_font_path(font_name: str) -> Path:
    """Get the path to a font file."""
    return get_assets_dir() / "fonts" / font_name
