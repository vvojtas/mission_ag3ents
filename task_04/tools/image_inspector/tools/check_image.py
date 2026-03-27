"""MCP tool: check_image — inspect an image via a vision LLM."""

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from common.logging_config import get_logger

logger = get_logger(__name__)


def register_check_image(mcp: FastMCP) -> None:
    """Attach the check_image tool to the MCP server.

    Args:
        mcp: FastMCP instance to register the tool on.
    """

    @mcp.tool(
        name="check_image",
        description=(
            "Load an image from the workspace and ask a vision LLM a question "
            "about it. Returns the model's textual answer."
        ),
    )
    async def check_image(
        file_name: Annotated[
            str,
            Field(
                description=(
                    'Name of the image file in the workspace (e.g. "photo.png"). '
                    "Ask the user if not specified."
                ),
            ),
        ],
        query: Annotated[
            str,
            Field(
                description=(
                    'Free-form question about the image (e.g. "Describe what you see").'
                ),
            ),
        ],
    ) -> dict[str, Any]:
        # TODO: Load image from workspace (resolve path, validate existence/format)
        # TODO: Send image + query to OpenRouter vision LLM
        # TODO: Return model answer
        return {
            "answer": "Not implemented yet.",
            "hint": "check_image is a stub — vision LLM integration pending.",
        }
