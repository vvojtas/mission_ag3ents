"""FastMCP server for image inspection via a vision LLM.

Provides a single tool to load an image and answer a question about it
using an OpenRouter-hosted vision model.
"""

from fastmcp import FastMCP

from common import Settings
from common.llm_api.cost_tracker import CostTracker
from common.settings import MCPWorkspaceSettings
from .tools import register_check_image
from pathlib import Path

def create_image_inspector_mcp(
    settings: Settings | None = None,
    workspace_root: Path | None = None,
    prompt_loading_path: Path | None = None,
    cost_tracker: CostTracker | None = None,
) -> FastMCP:
    """Build and return a configured FastMCP instance with the check_image tool registered.

    Args:
        settings: Project settings providing hub credentials.
            Loaded from environment if omitted.
        workspace_root: Absolute path where files are saved.
            Falls back to MCPWorkspaceSettings if omitted.
        prompt_loading_path: Absolute path where prompts are stored.
            Falls back to MCPWorkspaceSettings if omitted.
        cost_tracker: Cost tracker to use for tracking costs.
            Falls back to a new CostTracker if omitted.
    Returns:
        Fully configured FastMCP instance ready for Client(mcp) or mcp.run().
    """
    resolved_settings = settings or Settings()
    root = (
        workspace_root.resolve()
        if workspace_root is not None
        else MCPWorkspaceSettings().workspace_root.resolve()
    )
    resolved_prompt_loading_path = (
        prompt_loading_path.resolve() 
        if prompt_loading_path is not None 
        else MCPWorkspaceSettings().workspace_root.parent.resolve() / "prompts"
    )
    cost_tracker = cost_tracker or CostTracker()
    mcp = FastMCP(
        "Image Inspector MCP Server",
        instructions=(
            "Inspect images using a vision LLM. "
            "Use check_image with a file name and a question to get an answer."
        ),
    )

    register_check_image(mcp, resolved_settings, root, resolved_prompt_loading_path, cost_tracker)

    return mcp


mcp = create_image_inspector_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8012)
