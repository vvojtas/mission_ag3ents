"""FastMCP server for image inspection via a vision LLM."""

from pathlib import Path

from fastmcp import FastMCP

from common import Settings
from common.llm_api.cost_tracker import CostTracker
from common.settings import MCPWorkspaceSettings

from .tools import register_check_image


def create_image_inspector_mcp(
    settings: Settings | None = None,
    workspace_root: Path | None = None,
    prompt_loading_path: Path | None = None,
    cost_tracker: CostTracker | None = None,
) -> FastMCP:
    """Build FastMCP with check_image registered."""
    resolved_settings = settings or Settings()
    root = (
        workspace_root.resolve()
        if workspace_root is not None
        else MCPWorkspaceSettings().workspace_root.resolve()
    )
    resolved_prompt_loading_path = (
        prompt_loading_path.resolve()
        if prompt_loading_path is not None
        else (Path(__file__).resolve().parents[2] / "prompts")
    )
    resolved_cost = cost_tracker or CostTracker()

    mcp = FastMCP(
        "Image Inspector MCP Server",
        instructions=(
            "Inspect workspace images with a vision LLM. "
            "Use check_image with resource (file name) and query."
        ),
    )

    register_check_image(
        mcp,
        resolved_settings,
        root,
        resolved_prompt_loading_path,
        resolved_cost,
    )

    return mcp


mcp = create_image_inspector_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8012)
