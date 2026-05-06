"""FastMCP server for downloading the electricity task image from hub data URL."""

from pathlib import Path

from fastmcp import FastMCP

from common import Settings
from common.settings import MCPWorkspaceSettings

from .tools import register_hub_downloader


def create_hub_downloader_mcp(
    settings: Settings | None = None,
    workspace_root: Path | None = None,
) -> FastMCP:
    """Build FastMCP with hub_downloader registered."""
    resolved_settings = settings or Settings()
    root = (
        workspace_root.resolve()
        if workspace_root is not None
        else MCPWorkspaceSettings().workspace_root.resolve()
    )

    mcp = FastMCP(
        "Hub Downloader MCP Server",
        instructions=(
            "Download the electricity challenge image from hub.ag3nts.org into the workspace. "
            "Use hub_downloader with optional filename and override."
        ),
    )
    register_hub_downloader(mcp, resolved_settings, root)
    return mcp


mcp = create_hub_downloader_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8011)
