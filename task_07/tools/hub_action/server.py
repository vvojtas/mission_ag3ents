"""FastMCP server for electricity task hub actions (per-cell rotate)."""

from fastmcp import FastMCP

from common import Settings

from .tools import register_hub_action, register_hub_reset


def create_hub_action_mcp(settings: Settings | None = None) -> FastMCP:
    """Build FastMCP with hub_action registered."""
    resolved_settings = settings or Settings()
    mcp = FastMCP(
        "Hub Action MCP Server",
        instructions=(
            "Call hub_action with a list of cells (strings like '2x3') to rotate each "
            "90° right."
        ),
    )
    register_hub_action(mcp, resolved_settings)
    register_hub_reset(mcp, resolved_settings)
    return mcp


mcp = create_hub_action_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8014)
