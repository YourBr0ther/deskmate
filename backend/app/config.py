"""
Configuration management for DeskMate backend.

Centralizes all configuration settings and provides environment-aware defaults.
"""

import os
from typing import List, Optional
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    """Database configuration settings."""
    url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://deskmate:deskmate@localhost:5432/deskmate")
    echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))


class QdrantConfig(BaseModel):
    """Qdrant vector database configuration."""
    url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key: Optional[str] = os.getenv("QDRANT_API_KEY")
    collection_size: int = int(os.getenv("QDRANT_COLLECTION_SIZE", "1536"))


class LLMConfig(BaseModel):
    """LLM service configuration."""
    nano_gpt_api_key: Optional[str] = os.getenv("NANO_GPT_API_KEY")
    nano_gpt_base_url: str = os.getenv("NANO_GPT_BASE_URL", "https://api.nanogpt.ai/v1")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    default_model: str = os.getenv("DEFAULT_LLM_MODEL", "llama3.2:latest")
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    timeout: int = int(os.getenv("LLM_TIMEOUT", "30"))


class SecurityConfig(BaseModel):
    """Security and CORS configuration."""
    environment: str = os.getenv("ENVIRONMENT", "development")
    allowed_origins: List[str] = []
    max_message_length: int = int(os.getenv("MAX_MESSAGE_LENGTH", "10000"))
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.environment == "production":
            # Production CORS - restrict to specific domains
            self.allowed_origins = [
                "https://yourdomain.com",  # Replace with actual production domain
                "https://www.yourdomain.com",
            ]
        else:
            # Development CORS - allow localhost
            self.allowed_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://0.0.0.0:3000",
            ]


class ConversationConfig(BaseModel):
    """Conversation memory configuration."""
    max_recent_messages: int = int(os.getenv("MAX_RECENT_MESSAGES", "20"))
    min_messages_for_vectorization: int = int(os.getenv("MIN_MESSAGES_FOR_VECTORIZATION", "2"))
    vectorization_batch_size: int = int(os.getenv("VECTORIZATION_BATCH_SIZE", "10"))
    memory_cleanup_interval: int = int(os.getenv("MEMORY_CLEANUP_INTERVAL", "3600"))  # seconds


class IdleConfig(BaseModel):
    """Idle mode and autonomous behavior configuration."""
    inactivity_timeout_minutes: int = int(os.getenv("IDLE_TIMEOUT_MINUTES", "10"))  # Minutes before idle mode
    action_interval_seconds: int = int(os.getenv("IDLE_ACTION_INTERVAL_SECONDS", "180"))  # Base interval between actions
    max_action_interval_seconds: int = int(os.getenv("IDLE_MAX_ACTION_INTERVAL", "480"))  # Max interval (8 minutes)
    dream_expiration_hours: int = int(os.getenv("DREAM_EXPIRATION_HOURS", "24"))  # Hours before dreams expire
    idle_model_preference: str = os.getenv("IDLE_MODEL_PREFERENCE", "ollama")  # Prefer Ollama for idle mode
    idle_models: List[str] = [
        "phi3:mini",
        "gemma2:2b",
        "llama3.2:1b",
        "qwen2:0.5b"
    ]  # Lightweight models for idle mode
    max_consecutive_actions: int = int(os.getenv("IDLE_MAX_CONSECUTIVE_ACTIONS", "5"))  # Max actions before pause
    energy_cost_per_action: float = float(os.getenv("IDLE_ENERGY_COST", "0.1"))  # Energy consumed per action


class AppConfig(BaseModel):
    """Main application configuration."""
    title: str = "DeskMate API"
    description: str = "Virtual AI Companion Backend"
    version: str = "0.1.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Sub-configurations
    database: DatabaseConfig = DatabaseConfig()
    qdrant: QdrantConfig = QdrantConfig()
    llm: LLMConfig = LLMConfig()
    security: SecurityConfig = SecurityConfig()
    conversation: ConversationConfig = ConversationConfig()
    idle: IdleConfig = IdleConfig()


# Global configuration instance
config = AppConfig()