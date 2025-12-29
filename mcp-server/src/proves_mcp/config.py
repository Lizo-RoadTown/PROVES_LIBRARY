"""Configuration management for PROVES MCP Server."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database
    neon_database_url: str = Field(
        default="",
        description="PostgreSQL connection string for Neon database"
    )

    # For agent-backed deep tools
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for deep search tools"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    # Paths
    source_registry_path: Path = Field(
        default=Path(__file__).parent.parent.parent / "source_registry.yaml",
        description="Path to source registry YAML file"
    )


def get_settings() -> Settings:
    """Get application settings, checking multiple .env locations."""
    # Try current directory first, then parent directories
    env_paths = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path(__file__).parent.parent.parent.parent / ".env",  # PROVES_LIBRARY/.env
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            return Settings(_env_file=env_path)
    
    return Settings()


settings = get_settings()
