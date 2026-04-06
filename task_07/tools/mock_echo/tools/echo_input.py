"""MCP tool: mock_echo — return input unchanged for wiring tests."""

from fastmcp import FastMCP


def register_mock_echo(mcp: FastMCP) -> None:
    """Register the mock_echo tool on the given server.

    Args:
        mcp: FastMCP instance to attach the tool to.
    """

    @mcp.tool(
        name="mock_echo",
        description="Echo the input back as JSON. For testing MCP and ToolsLoop wiring.",
    )
    def mock_echo(text: str) -> dict[str, str]:
        return {"echo": text}
