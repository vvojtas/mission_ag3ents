"""FastMCP server for submitting task answers to the hub API.

Provides a single tool to post an answer for a named task and return
structured success/failure information including the flag on success.
"""

from fastmcp import FastMCP

from common import Settings

from .tools import register_post_answer


def create_hub_answer_mcp(settings: Settings | None = None) -> FastMCP:
    """Build and return a configured FastMCP instance with the hub_post_answer tool registered.

    Args:
        settings: Project settings providing hub credentials.
            Loaded from environment if omitted.

    Returns:
        Fully configured FastMCP instance ready for Client(mcp) or mcp.run().
    """
    resolved_settings = settings or Settings()

    mcp = FastMCP(
        "Hub Answer MCP Server",
        instructions=(
            "Submit task answers to the hub API. "
            "Use hub_post_answer with a task name and answer to submit and get the result."
        ),
    )

    register_post_answer(mcp, resolved_settings)

    return mcp


mcp = create_hub_answer_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8013)
