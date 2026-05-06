"""MCP tool: hub_reset — reset electricity task via hub data URL (GET ?reset=1)."""

from typing import Any
from urllib.parse import quote

import httpx
from fastmcp import FastMCP

from common import Settings
from common.logging_config import get_logger

logger = get_logger(__name__)

_HUB_DATA_ORIGIN = "https://hub.ag3nts.org"


def register_hub_reset(mcp: FastMCP, settings: Settings) -> None:
    """Attach the hub_reset tool (no parameters; does not save image bytes)."""

    @mcp.tool(
        name="hub_reset",
        description=(
            "Reset the electricity task on the hub (GET electricity.png with reset=1). "
            "Use when you need a fresh puzzle. Does not write the image to disk."
        ),
    )
    async def hub_reset() -> dict[str, Any]:
        url = (
            f"{_HUB_DATA_ORIGIN}/data/{quote(settings.hub_api_key, safe='')}/electricity.png"
            "?reset=1"
        )
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            status: int | None = None
            if isinstance(exc, httpx.HTTPStatusError):
                status = exc.response.status_code
            logger.error("hub_reset HTTP error: %s", exc)
            return {"ok": False, "error": str(exc), "http_status": status}

        return {
            "ok": True,
            "http_status": response.status_code,
            "message": "Electricity task reset completed (response body not stored).",
        }
