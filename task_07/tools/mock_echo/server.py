"""FastMCP server with a single echo tool for local wiring tests."""

from fastmcp import FastMCP

from .tools import register_mock_echo


def create_mock_echo_mcp() -> FastMCP:
    """Build and return a FastMCP instance with the mock_echo tool.

    Returns:
        Configured FastMCP instance for in-process `MCPClient(mcp)`.
    """
    mcp = FastMCP(
        "Mock Echo MCP Server",
        instructions=(
            "Testing helper — mock_echo returns the same text back. "
            "Useful to verify tool calls before real task tools exist."
        ),
    )
    register_mock_echo(mcp)
    return mcp


mcp = create_mock_echo_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8017)
