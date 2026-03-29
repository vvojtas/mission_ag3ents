"""FastMCP server for sending action commands to the hub API.

Provides the send_action tool with automatic retry logic for 503/429.
"""

from fastmcp import FastMCP

from common import Settings

from .tools import register_send_action


def create_hub_call_mcp(
    settings: Settings | None = None,
    *,
    max_retries: int = 3,
) -> FastMCP:
    """Build and return a configured FastMCP instance with the send_action tool.

    Args:
        settings: Project settings providing hub credentials.
            Loaded from environment if omitted.
        max_retries: Maximum automatic retries on 503. Defaults to 3.

    Returns:
        Fully configured FastMCP instance ready for Client(mcp) or mcp.run().
    """
    resolved_settings = settings or Settings()

    mcp = FastMCP(
        "Hub Call MCP Server",
        instructions=(
            "Send action commands to the hub API. "
            "Use send_action with a command dict containing an 'action' key. "
            "If unsure of available actions, send {\"action\": \"help\"} first."
        ),
    )

    register_send_action(mcp, resolved_settings, max_retries=max_retries)

    return mcp


mcp = create_hub_call_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8016)
