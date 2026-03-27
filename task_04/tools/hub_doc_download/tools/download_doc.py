"""MCP tool: hub_download_doc — download docs from the hub API."""

from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from common import Settings
from common.hub_client import HubClient
from common.logging_config import get_logger

logger = get_logger(__name__)


async def _download_single_file(
    hub: HubClient,
    name: str,
    dest: Path,
    force: bool,
) -> str:
    """Download one file and return its disposition: 'downloaded', 'skipped', or 'error'.

    Raises:
        Exception: Propagated from hub client on download failure.
    """
    if dest.exists() and not force:
        logger.info("Skipping %s — already exists", name)
        return "skipped"

    if dest.exists():
        dest.unlink()
        logger.info("Removed existing %s (force=true)", name)

    await hub.download_file(f"dane/doc/{name}", dest)
    return "downloaded"


def _build_hint(downloaded: list[str], skipped: list[str], errors: list[dict[str, str]]) -> str:
    parts: list[str] = []
    if downloaded:
        parts.append(f"Downloaded {len(downloaded)} file(s).")
    if skipped:
        parts.append(f"Skipped {len(skipped)} (already exist, use force=true to overwrite).")
    if errors:
        parts.append(f"{len(errors)} file(s) failed.")
    return " ".join(parts) if parts else "Nothing to do."


def register_download_doc(mcp: FastMCP, settings: Settings, workspace_root: Path) -> None:
    """Attach the hub_download_doc tool to the MCP server.

    Args:
        mcp: FastMCP instance to register the tool on.
        settings: Project settings (provides hub credentials).
        workspace_root: Absolute path where downloaded files are saved.
    """

    @mcp.tool(
        name="hub_download_doc",
        description=(
            "Download one or more files from the hub documentation endpoint "
            "(/dane/doc/) and save them to the workspace. "
            "Existing files are skipped unless `force` is true."
        ),
    )
    async def hub_download_doc(
        file_names: Annotated[
            list[str],
            Field(
                description=(
                    'Names of files to download (e.g. ["index.md", "poziomy.md"]). '
                    "Ask the user which files are needed if not specified."
                ),
            ),
        ],
        force: Annotated[
            bool,
            Field(
                description="When true, overwrite existing local files. Default false.",
            ),
        ] = False,
    ) -> dict[str, Any]:
        if not file_names:
            return {"downloaded": [], "skipped": [], "errors": [], "hint": "No files requested."}

        downloaded: list[str] = []
        skipped: list[str] = []
        errors: list[dict[str, str]] = []

        async with HubClient(settings) as hub:
            for name in file_names:
                try:
                    result = await _download_single_file(hub, name, workspace_root / name, force)
                    (downloaded if result == "downloaded" else skipped).append(name)
                except Exception as exc:
                    logger.error("Failed to download %s: %s", name, exc)
                    errors.append({"file": name, "error": str(exc)})

        return {
            "downloaded": downloaded,
            "skipped": skipped,
            "errors": errors,
            "hint": _build_hint(downloaded, skipped, errors),
        }
