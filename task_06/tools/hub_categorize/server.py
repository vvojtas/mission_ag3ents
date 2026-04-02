"""FastMCP server for hub categorization prompt testing.

Provides tools to send classification prompts to the hub /verify endpoint
and to reset the current run (clearing token usage).
"""

from fastmcp import FastMCP

from common import Settings

from .tools import register_reset, register_send_prompt


def create_hub_categorize_mcp(
    settings: Settings | None = None,
) -> FastMCP:
    """Build and return a configured FastMCP instance with categorize tools registered.

    Args:
        settings: Project settings providing hub credentials and task name.
            Loaded from environment if omitted.

    Returns:
        Fully configured FastMCP instance ready for Client(mcp) or mcp.run().
    """
    resolved_settings = settings or Settings()

    mcp = FastMCP(
        "Task 06 Hub Categorize MCP Server",
        instructions=(
            "Submit prompts for evaluation and manage runs."
        ),
    )

    register_send_prompt(mcp, resolved_settings)
    register_reset(mcp, resolved_settings)

    return mcp


mcp = create_hub_categorize_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8019)
