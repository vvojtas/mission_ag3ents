"""MCP tool: categorize_reset — reset the current categorization run."""

from typing import Any

import httpx
from fastmcp import FastMCP

from common import Settings
from common.logging_config import get_logger

logger = get_logger(__name__)


def _build_hint(success: bool, code: int | None, message: str) -> str:
    if success:
        return f"Reset done. Hub: {message}"
    if code is not None:
        return f"Reset failed (code {code}): {message}"
    return f"Reset request failed: {message}"


def register_reset(mcp: FastMCP, settings: Settings) -> None:
    """Attach the categorize_reset tool to the MCP server.

    Args:
        mcp: FastMCP instance to register the tool on.
        settings: Project settings providing hub credentials and task name.
    """

    @mcp.tool(
        name="categorize_reset",
        description=(
            "Reset the current run. "
            "Clears accumulated token usage on the hub so you can start fresh."
        ),
    )
    async def categorize_reset() -> dict[str, Any]:
        payload = {
            "apikey": settings.hub_api_key,
            "task": settings.hub_task_name,
            "answer": {"prompt": "reset"},
        }

        try:
            async with httpx.AsyncClient(base_url=settings.hub_api_url.rstrip("/")) as client:
                response = await client.post("/verify", json=payload)
                response.raise_for_status()

            data = response.json()
            logger.info("categorize_reset response: %s", data)

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
            logger.error("categorize_reset HTTP error: %s", msg)
            return {
                "success": False,
                "code": None,
                "message": msg,
                "data": None,
                "hint": _build_hint(False, None, msg),
            }

        except Exception as exc:
            msg = str(exc)
            logger.error("categorize_reset unexpected error: %s", msg)
            return {
                "success": False,
                "code": None,
                "message": msg,
                "data": None,
                "hint": _build_hint(False, None, msg),
            }
