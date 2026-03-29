"""FastMCP server with a single stub echo tool."""

from fastmcp import FastMCP

from .tools import register_mock_echo


def create_mock_echo_mcp() -> FastMCP:
    """Build and return a FastMCP instance with mock_echo registered.

    Returns:
        Configured FastMCP instance for in-process Client(mcp) or mcp.run().
    """
    mcp = FastMCP(
        "Mock Echo MCP Server",
        instructions="Provides mock_echo for verifying agent tool wiring before real tools exist.",
    )
    register_mock_echo(mcp)
    return mcp


mcp = create_mock_echo_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8015)
