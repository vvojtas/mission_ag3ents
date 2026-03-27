"""FastMCP server for image inspection via a vision LLM.

Provides a single tool to load an image and answer a question about it
using an OpenRouter-hosted vision model.
"""

from fastmcp import FastMCP

from .tools import register_check_image


def create_image_inspector_mcp() -> FastMCP:
    """Build and return a configured FastMCP instance with the check_image tool registered.

    Returns:
        Fully configured FastMCP instance ready for Client(mcp) or mcp.run().
    """
    #TODO: change instructions
    mcp = FastMCP(
        "Image Inspector MCP Server",
        instructions=(
            "Inspect images using a vision LLM. "
            "Use check_image with a file name and a question to get an answer."
        ),
    )

    register_check_image(mcp)

    return mcp


mcp = create_image_inspector_mcp()

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8012)
