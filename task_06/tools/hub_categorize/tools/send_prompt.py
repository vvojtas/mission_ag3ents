"""MCP tool: categorize_send_prompt — send a classification prompt to the hub."""

from typing import Annotated, Any

import httpx
from fastmcp import FastMCP
from pydantic import Field

from common import Settings
from common.logging_config import get_logger

logger = get_logger(__name__)


def _build_hint(success: bool, code: int | None, message: str) -> str:
    if success:
        return "Prompt accepted."
    if code is not None:
        return f"Failed (code {code})."
    return "Request failed."


def register_send_prompt(mcp: FastMCP, settings: Settings) -> None:
    """Attach the categorize_send_prompt tool to the MCP server.

    Args:
        mcp: FastMCP instance to register the tool on.
        settings: Project settings providing hub credentials and task name.
    """

    @mcp.tool(
        name="categorize_send_prompt",
        description="Send a prompt to the hub for evaluation.",
    )
    async def categorize_send_prompt(
        prompt: Annotated[
            str,
            Field(description="The prompt text to submit."),
        ],
    ) -> dict[str, Any]:
        payload = {
            "apikey": settings.hub_api_key,
            "task": settings.hub_task_name,
            "answer": {"prompt": prompt},
        }

        try:
            async with httpx.AsyncClient(base_url=settings.hub_api_url.rstrip("/")) as client:
                response = await client.post("/verify", json=payload)
                #response.raise_for_status()

            data = response.json()
            logger.info("categorize_send_prompt response: %s", data)

            code: int | None = data.get("code")
            message: str = str(data.get("message", ""))
            success = code is not None and code >= 0

            return {
                "success": success,
                "code": code,
                "message": message,
                "data": data,
                "hint": _build_hint(success, code, message),
            }

        except httpx.HTTPStatusError as exc:
            msg = f"HTTPStatusError: {exc.response.status_code} {exc.response.reason_phrase}"
            logger.error("categorize_send_prompt HTTP error: %s", msg)
            return {
                "success": False,
                "code": None,
                "message": msg,
                "data": None,
                "hint": _build_hint(False, None, msg),
            }

        except Exception as exc:
            msg = str(exc)
            logger.error("categorize_send_prompt unexpected error: %s", msg)
            return {
                "success": False,
                "code": None,
                "message": msg,
                "data": None,
                "hint": _build_hint(False, None, msg),
            }
