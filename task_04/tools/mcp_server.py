"""FastMCP server for task 04 — add tools here and expose them to the LLM via ToolsLoop."""

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP(
    "Task 04 MCP Server",
    instructions="Boilerplate MCP server for task 04. Replace tools with task-specific implementations.",
)


@mcp.tool(name="echo", description="Return the given text unchanged (example tool for the agent loop).")
async def echo(
    text: Annotated[str, Field(description="Text to echo back.")],
) -> str:
    return text


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8004)
