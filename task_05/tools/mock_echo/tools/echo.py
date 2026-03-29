"""MCP tool: mock_echo — stub echo for verifying ToolsLoop wiring."""

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from common.logging_config import get_logger

logger = get_logger(__name__)


def register_mock_echo(mcp: FastMCP) -> None:
    """Attach the mock_echo tool to the MCP server.

    Args:
        mcp: FastMCP instance to register the tool on.
    """

    @mcp.tool(
        name="mock_echo",
        description=(
            "Development stub: returns the input message wrapped in JSON. "
            "Use to verify MCP tool calls; replace with real tools for the task."
        ),
    )
    async def mock_echo(
        message: Annotated[
            str,
            Field(description="Text to echo back in the response."),
        ],
    ) -> dict[str, Any]:
        logger.info("mock_echo: %s", message[:200] if len(message) > 200 else message)
        return {"echo": message, "ok": True}
