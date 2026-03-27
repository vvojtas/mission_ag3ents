"""FastMCP server for workspace file management.

Provides read-only tools for listing, reading, and searching text files
within a configurable workspace directory.
"""

from pathlib import Path

from fastmcp import FastMCP

from common.settings import MCPWorkspaceSettings

from .tools import (
    register_list_workspace_files,
    register_read_workspace_text_file,
    register_search_workspace_text,
)


def create_file_management_mcp(workspace_root: Path | None = None) -> FastMCP:
    """Build and return a configured FastMCP instance with all file tools registered.

    Args:
        workspace_root: Absolute path to the workspace root.
            If omitted, uses :class:`MCPWorkspaceSettings` (``MCP_WORKSPACE_ROOT``
            or repository root containing ``common``).

    Returns:
        Fully configured FastMCP instance ready for Client(mcp) or mcp.run().
    """
    root = (
        workspace_root.resolve()
        if workspace_root is not None
        else MCPWorkspaceSettings().workspace_root.resolve()
    )

    mcp = FastMCP(
        "File Management MCP Server",
        instructions=(
            "Read-only workspace file access. Use ws_list_files to discover files, "
            "ws_read_text_file to read contents, and ws_search_text to find patterns."
        ),
    )

    register_list_workspace_files(mcp, root)
    register_read_workspace_text_file(mcp, root)
    register_search_workspace_text(mcp, root)

    return mcp


mcp = create_file_management_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8010)
