"""MCP tool: ws_list_files — list immediate files in the workspace root."""

from pathlib import Path
from typing import Any

from fastmcp import FastMCP


def register_list_workspace_files(mcp: FastMCP, workspace_root: Path) -> None:
    """Attach the ws_list_files tool to the MCP server."""

    @mcp.tool(
        name="ws_list_files",
        description=(
            "List files directly in the workspace root (non-recursive; subdirectories are omitted). "
            "Each entry includes the workspace-relative path and line count "
            "(same line splitting as ws_read_text_file)."
        ),
    )
    async def ws_list_files() -> dict[str, Any]:
        root = workspace_root.resolve()
        items: list[dict[str, Any]] = []
        try:
            entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
        except PermissionError:
            return {"error": "Permission denied listing workspace root."}

        for entry in entries:
            if not entry.is_file():
                continue
            rel = entry.relative_to(root).as_posix()
            try:
                text = entry.read_text(encoding="utf-8", errors="replace")
            except PermissionError:
                items.append({"path": rel, "lines": None, "error": "permission denied"})
                continue
            line_count = len(text.splitlines(keepends=True))
            items.append({"path": rel, "lines": line_count})

        hint = (
            f"Found {len(items)} file(s) at workspace root. "
            "Use ws_read_text_file to read contents."
        )
        return {"files": items, "total": len(items), "hint": hint}
