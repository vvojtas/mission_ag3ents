"""MCP tool: hub_downloader — fetch the electricity task image from hub data URL."""

from pathlib import Path
from typing import Annotated, Any
from urllib.parse import quote

import httpx
from fastmcp import FastMCP
from pydantic import Field

from common import Settings
from common.logging_config import get_logger

logger = get_logger(__name__)

_HUB_DATA_ORIGIN = "https://hub.ag3nts.org"


def _safe_workspace_file(workspace_root: Path, filename: str) -> Path | None:
    """Resolve a single-segment filename under workspace_root, or None if unsafe."""
    raw = filename.strip()
    if not raw:
        return None
    candidate = Path(raw)
    if len(candidate.parts) != 1:
        return None
    name = candidate.parts[0]
    dest = (workspace_root / name).resolve()
    try:
        dest.relative_to(workspace_root.resolve())
    except ValueError:
        return None
    return dest


def register_hub_downloader(mcp: FastMCP, settings: Settings, workspace_root: Path) -> None:
    """Attach the hub_downloader tool to the MCP server."""

    @mcp.tool(
        name="hub_downloader",
        description=(
            "Download the current electricity task image from the hub "
            "(hub.ag3nts.org/data/{apikey}/electricity.png) into the workspace. "
            "Optional local filename defaults to electricity.png."
        ),
    )
    async def hub_downloader(
        filename: Annotated[
            str | None,
            Field(
                ...,
                description=(
                    'Local workspace filename to save as (e.g. "electricity.png"). '
                    "Pass null to use electricity.png."
                ),
            ),
        ],
        override: Annotated[
            bool | None,
            Field(
                ...,
                description=(
                    "When true, overwrite an existing file. "
                    "When false, fail if the target file already exists. "
                    "Pass null for default (overwrite)."
                ),
            ),
        ],
    ) -> dict[str, Any]:
        local_name = filename or "electricity.png"
        effective_override = True if override is None else override
        dest = _safe_workspace_file(workspace_root, local_name)
        if dest is None:
            msg = f"Invalid or unsafe filename: {filename!r}"
            logger.error("hub_downloader: %s", msg)
            return {
                "ok": False,
                "error": msg,
                "resource": None,
            }

        if dest.exists() and not effective_override:
            msg = f"File already exists: {dest.name} (set override=true to replace)"
            logger.warning("hub_downloader: %s", msg)
            return {
                "ok": False,
                "error": msg,
                "resource": None,
            }

        url = f"{_HUB_DATA_ORIGIN}/data/{quote(settings.hub_api_key, safe='')}/electricity.png"
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                body = response.content
        except httpx.HTTPError as exc:
            logger.error("hub_downloader HTTP error: %s", exc)
            return {
                "ok": False,
                "error": f"Download failed: {exc}",
                "resource": None,
            }

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
        rel = dest.name
        tag = f"<resource>{rel}</resource>"
        logger.info("hub_downloader saved %s (%s bytes)", dest, len(body))
        return {
            "ok": True,
            "message": f"Downloaded electricity image; resource created {tag}",
            "resource": tag,
            "path": rel,
            "bytes_written": len(body),
        }
