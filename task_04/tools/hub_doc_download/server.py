"""FastMCP server for downloading hub documentation files.

Provides a single tool to fetch files from /dane/doc/ and save them
into the workspace directory.
"""

from pathlib import Path

from fastmcp import FastMCP

from common import Settings
from common.settings import MCPWorkspaceSettings

from .tools import register_download_doc


def create_hub_doc_download_mcp(
    settings: Settings | None = None,
    workspace_root: Path | None = None,
) -> FastMCP:
    """Build and return a configured FastMCP instance with the download tool registered.

    Args:
        settings: Project settings providing hub credentials.
            Loaded from environment if omitted.
        workspace_root: Absolute path where files are saved.
            Falls back to MCPWorkspaceSettings if omitted.

    Returns:
        Fully configured FastMCP instance ready for Client(mcp) or mcp.run().
    """
    resolved_settings = settings or Settings()
    root = (
        workspace_root.resolve()
        if workspace_root is not None
        else MCPWorkspaceSettings().workspace_root.resolve()
    )

    mcp = FastMCP(
        "Hub Doc Download MCP Server",
        instructions=(
            "Download documentation files from the hub API. "
            "Use hub_download_doc with a list of file names to fetch them."
        ),
    )

    register_download_doc(mcp, resolved_settings, root)

    return mcp


mcp = create_hub_doc_download_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8011)
