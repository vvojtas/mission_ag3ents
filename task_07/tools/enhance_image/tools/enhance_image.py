"""MCP tool: enhance_image — greyscale + morphological dilation / erosion, save to workspace."""

import asyncio
from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP
from PIL import Image, ImageFilter, UnidentifiedImageError
from pydantic import Field

_KERNEL = 3
# Grayscale morphology (3×3): dilate×2 → erode×2 → erode×2 → dilate×2 → erode×3 → dilate×3
_MORPH_PASS = 2
_FINAL_ERODE = 3
_FINAL_DILATE = 3


def _validate_resource_name(raw: str) -> tuple[str, dict[str, str] | None]:
    """Return (stripped name, None) or (unused, error dict)."""
    name = raw.strip()
    if not name:
        return (
            "",
            {
                "error": "Resource name must be non-empty.",
                "hint": "Pass a single workspace file name, e.g. electricity.png.",
            },
        )
    if name in (".", ".."):
        return (
            "",
            {
                "error": f"Invalid resource name: {name!r}",
                "hint": "Use a real file name, not '.' or '..'.",
            },
        )
    candidate = Path(name)
    if candidate.name != name or len(candidate.parts) != 1:
        return (
            "",
            {
                "error": f"Invalid resource name (use a single file name): {raw!r}",
                "hint": "Pass only the base name, e.g. input.png — no directories.",
            },
        )
    return (name, None)


def _process_sync(source_path: Path, target_path: Path) -> None:
    """Load source, greyscale, full morphology pipeline (see module comment), save to target."""
    with Image.open(source_path) as img:
        work = img.convert("L")
        for _ in range(_MORPH_PASS):
            work = work.filter(ImageFilter.MaxFilter(_KERNEL))
        for _ in range(_MORPH_PASS):
            work = work.filter(ImageFilter.MinFilter(_KERNEL))
        for _ in range(_MORPH_PASS):
            work = work.filter(ImageFilter.MinFilter(_KERNEL))
        for _ in range(_MORPH_PASS):
            work = work.filter(ImageFilter.MaxFilter(_KERNEL))
        for _ in range(_FINAL_ERODE):
            work = work.filter(ImageFilter.MinFilter(_KERNEL))
        for _ in range(_FINAL_DILATE):
            work = work.filter(ImageFilter.MaxFilter(_KERNEL))
        work.save(target_path)


def register_enhance_image(mcp: FastMCP, workspace_root: Path) -> None:
    """Attach the enhance_image tool to the MCP server."""

    root = workspace_root.resolve()

    @mcp.tool(
        name="enhance_image",
        description=(
            "Read a workspace image, convert to greyscale, apply morphology (3×3 neighborhood): "
            "dilate×2 → erode×2 → erode×2 → dilate×2 → erode×3 → dilate×3; then save under a new file name. "
            "Fails if the target file already exists."
        ),
    )
    async def enhance_image(
        source_resource: Annotated[
            str,
            Field(
                description=(
                    "Source image file name in the workspace (e.g. electricity.png). "
                    "Ask the user if missing."
                ),
            ),
        ],
        target_resource: Annotated[
            str,
            Field(
                description=(
                    "Output image file name in the workspace; must not exist yet. "
                    "Ask the user if missing."
                ),
            ),
        ],
    ) -> dict[str, Any]:
        src_name, src_err = _validate_resource_name(source_resource)
        if src_err:
            return src_err
        tgt_name, tgt_err = _validate_resource_name(target_resource)
        if tgt_err:
            return tgt_err
        if src_name == tgt_name:
            return {
                "error": "source_resource and target_resource must differ.",
                "hint": "Choose a new name for the output file.",
            }

        source_path = root / src_name
        target_path = root / tgt_name

        if not source_path.is_file():
            return {
                "error": f"Source file not found: {source_path}",
                "hint": "Download or create the image in the workspace first.",
            }
        if target_path.exists():
            return {
                "error": f"Target file already exists: {target_path}",
                "hint": "Choose a different target_resource or remove the existing file.",
            }

        try:
            await asyncio.to_thread(_process_sync, source_path, target_path)
        except UnidentifiedImageError as exc:
            return {
                "error": f"Could not open image: {exc}",
                "hint": "Ensure the source is a supported bitmap (e.g. PNG, JPEG).",
            }
        except OSError as exc:
            return {
                "error": f"Failed to read or write image: {exc}",
                "hint": "Check disk space, permissions, and that the source path is readable.",
            }

        return {
            "status": "ok",
            "target_resource": tgt_name,
            "path": str(target_path),
        }
