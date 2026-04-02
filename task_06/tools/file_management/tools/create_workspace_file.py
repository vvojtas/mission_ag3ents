"""MCP tool: ws_create_file — create a new text file in the workspace."""

from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from .path_utils import resolve_workspace_path


def register_create_workspace_file(mcp: FastMCP, workspace_root: Path) -> None:
    """Attach the ws_create_file tool to the MCP server."""

    @mcp.tool(
        name="ws_create_file",
        description=(
            "Create a new text file at the given workspace-relative path. "
            "Provide `content` to populate the file, or omit it to create an empty file. "
            "Fails if the file already exists — use `ws_update_file` to modify existing files."
        ),
    )
    async def ws_create_file(
        file_name: Annotated[
            str,
            Field(description="Workspace-relative path for the new file."),
        ],
        content: Annotated[
            str,
            Field(description="Initial file content. Defaults to empty string."),
        ] = "",
    ) -> dict[str, Any]:
        try:
            resolved = resolve_workspace_path(workspace_root, file_name)
        except ValueError as exc:
            return {"error": str(exc)}

        if resolved.exists():
            return {
                "error": f"File already exists: {file_name}",
                "hint": "Use ws_update_file to modify an existing file.",
            }

        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
        except PermissionError:
            return {"error": f"Permission denied: {file_name}"}

        total_lines = len(content.splitlines()) if content else 0

        return {
            "path": file_name,
            "total_lines": total_lines,
            "hint": (
                f"File created with {total_lines} line(s). "
                "Use ws_update_file to modify it or ws_read_text_file to read it."
            ),
        }
