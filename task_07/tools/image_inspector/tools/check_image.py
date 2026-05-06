"""MCP tool: check_image — inspect an image via a vision LLM."""

import base64
from pathlib import Path
from typing import Annotated, Any

import aiofiles
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from common import Settings
from common.events import ParsedResponse
from common.llm_api.cost_tracker import CostTracker
from common.llm_api.http_client_provider import HttpClientProvider
from common.llm_api.llm_client import LLMClient
from common.logging_config import get_logger
from common.prompt_loader import PromptLoader

logger = get_logger(__name__)

_MIME_TYPES: dict[str, str] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


class ImageInspectorAnswer(BaseModel):
    response: str = Field(description="The response from the image inspector")


def register_check_image(
    mcp: FastMCP,
    settings: Settings,
    workspace_root: Path,
    prompt_loading_path: Path,
    cost_tracker: CostTracker,
) -> None:
    """Attach the check_image tool to the MCP server."""

    @mcp.tool(
        name="check_image",
        description=(
            "Load an image from the workspace by file name and ask a vision LLM "
            "a question about it. Returns the model's textual answer."
        ),
    )
    async def check_image(
        resource: Annotated[
            str,
            Field(
                description=(
                    'Workspace image file name (e.g. "electricity.png"). '
                    "Ask the user if not specified."
                ),
            ),
        ],
        query: Annotated[
            str,
            Field(
                description='Question about the image (e.g. "What colors dominate?").',
            ),
        ],
    ) -> dict[str, Any]:
        async with HttpClientProvider(settings) as provider:
            llm_client = LLMClient(provider, cost_tracker)
            raw_name = resource.strip()
            if not raw_name:
                return {
                    "error": "resource must be a non-empty file name",
                    "hint": "Pass the image base name, e.g. electricity.png.",
                }
            candidate = Path(raw_name)
            if candidate.name != raw_name or len(candidate.parts) != 1:
                return {
                    "error": f"Invalid resource name (use a single filename): {resource!r}",
                    "hint": "Pass only the image base name, e.g. electricity.png.",
                }
            image_path = workspace_root / candidate.name
            if not image_path.is_file():
                return {
                    "error": f"File not found: {image_path}",
                    "hint": "Use hub_downloader first or list workspace files.",
                }
            ext = image_path.suffix[1:].lower()
            if ext not in _MIME_TYPES:
                return {
                    "error": f"Unsupported image format: {ext!r}",
                    "hint": f"Supported: {', '.join(sorted(_MIME_TYPES))}.",
                }

            async with aiofiles.open(image_path, "rb") as image_file:
                image_data = await image_file.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            mime_type = _MIME_TYPES[ext]

            prompt_loader = PromptLoader(prompt_loading_path)
            image_message = {
                "type": "input_image",
                "image_url": f"data:{mime_type};base64,{image_base64}",
            }
            text_message = {
                "type": "input_text",
                "text": query,
            }
            messages = prompt_loader.load_prompt("image_inspector")
            messages.append(
                {
                    "role": "user",
                    "content": [image_message, text_message],
                },
            )

            responses = await llm_client.responses(
                #model="openai/gpt-5.2",
                model="google/gemini-3.1-pro-preview",
                input=messages,
                text_format=ImageInspectorAnswer,
            )
            parsed = next((r for r in responses if isinstance(r, ParsedResponse)), None)
            if not parsed or not parsed.output_parsed:
                logger.error("Failed to parse LLM response")
                return {
                    "error": "Failed to parse LLM response",
                    "hint": "Try again with a different image or query.",
                }

            return {
                "response": parsed.output_parsed.response,
            }
