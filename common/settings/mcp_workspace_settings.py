"""Configuration for MCP servers that operate on a bounded filesystem workspace."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_workspace_root() -> Path:
    """Return the repository root (directory that contains ``common``)."""
    return Path(__file__).resolve().parent.parent.parent


class MCPWorkspaceSettings(BaseSettings):
    """Root directory for MCP file and search tools.

    Loads from environment variables and optional ``.env``. Does not require
    LLM or hub credentials — use this in MCP server factories and hosts that
    should not instantiate full :class:`common.settings.project_settings.Settings`.

    Environment:
        ``MCP_WORKSPACE_ROOT``: Overrides ``workspace_root``. Paths may be
        relative; they are resolved from the current working directory when
        pydantic parses them (set an absolute path if CWD is unstable).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="MCP_",
    )

    workspace_root: Path = Field(
        default_factory=_default_workspace_root,
        description=(
            "Filesystem root under which MCP file tools are allowed to operate. "
            "Environment variable: MCP_WORKSPACE_ROOT."
        ),
    )
