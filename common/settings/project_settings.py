"""Application settings loaded from environment variables.

Uses pydantic-settings to provide type-safe, validated configuration.
All secrets are loaded from a `.env` file at the project root.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the project.

    Loads values from environment variables and `.env` file.
    All fields can be overridden via environment variables
    (case-insensitive).

    Attributes:
        openrouter_api_key: API key for OpenRouter LLM access.
        hub_api_key: API key for the AI Devs competition platform.
        hub_api_url: Base URL for the AI Devs task API.
        dashboard_ws_url: WebSocket URL for the optional dashboard.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: str = Field(default=...)
    hub_api_key: str = Field(default=...)
    hub_api_url: str = "https://api.example.com"

    dashboard_ws_url: str = "ws://127.0.0.1:8765/dashboard/console/ws"
