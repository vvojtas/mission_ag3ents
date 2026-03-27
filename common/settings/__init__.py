"""Shared configuration (app credentials, MCP workspace root, etc.)."""

from common.settings.project_settings import Settings
from common.settings.mcp_workspace_settings import MCPWorkspaceSettings

__all__ = ["MCPWorkspaceSettings", "Settings"]
