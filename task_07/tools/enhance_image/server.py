"""FastMCP server — workspace image enhance (greyscale, dilate, erode, save)."""

from pathlib import Path

from fastmcp import FastMCP

from common.settings import MCPWorkspaceSettings

from .tools import register_enhance_image


def create_enhance_image_mcp(workspace_root: Path | None = None) -> FastMCP:
    """Build FastMCP with enhance_image registered.

    Args:
        workspace_root: Root directory for source/target image paths. Defaults to
            ``MCPWorkspaceSettings().workspace_root``.

    Returns:
        Configured ``FastMCP`` instance with tools attached.
    """
    root = (
        workspace_root.resolve()
        if workspace_root is not None
        else MCPWorkspaceSettings().workspace_root.resolve()
    )

    mcp = FastMCP(
        "Enhance Image MCP Server",
        instructions=(
            "Modifies image resources in the workspace. Details are in the tool description."
        ),
    )
    register_enhance_image(mcp, root)
    return mcp


mcp = create_enhance_image_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8015)
