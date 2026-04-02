"""MCP tool: ws_read_text_file — read a text file from the workspace."""

from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from .path_utils import resolve_workspace_path


def register_read_workspace_text_file(mcp: FastMCP, workspace_root: Path) -> None:
    """Attach the ws_read_text_file tool to the MCP server."""

    @mcp.tool(
        name="ws_read_text_file",
        description=(
            "Read a text file from the workspace. Returns numbered lines. "
            "Provide `start_line` and/or `end_line` to read a fragment "
            "(1-based, inclusive). Omit end_line (or use 0) to read through end of file; "
            "defaults read the entire file from line 1."
        ),
    )
    async def ws_read_text_file(
        path: Annotated[
            str,
            Field(description="Workspace-relative path to the file."),
        ],
        start_line: Annotated[
            int,
            Field(description="First line to return (1-based). Defaults to 1."),
        ] = 1,
        end_line: Annotated[
            int,
            Field(
                description=(
                    "Last line to return (1-based, inclusive). Use 0 for end of file "
                    "(default when reading the whole file)."
                ),
            ),
        ] = 0,
    ) -> dict[str, Any]:
        try:
            resolved = resolve_workspace_path(workspace_root, path)
        except ValueError as exc:
            return {"error": str(exc)}

        if not resolved.exists():
            return {
                "error": f"File not found: {path}",
                "hint": "Verify the path or use ws_list_files for files at workspace root.",
            }

        if not resolved.is_file():
            return {"error": f"Path is not a file: {path}"}

        try:
            text = resolved.read_text(encoding="utf-8", errors="replace")
        except PermissionError:
            return {"error": f"Permission denied: {path}"}

        lines = text.splitlines(keepends=True)
        total_lines = len(lines)

        actual_start = max(1, start_line)
        actual_end = total_lines if end_line <= 0 else min(end_line, total_lines)

        hints: list[str] = []
        if start_line > total_lines:
            return {
                "error": f"start_line ({start_line}) exceeds file length ({total_lines} lines).",
                "hint": f"File has {total_lines} line(s). Adjust your range.",
            }

        if end_line > 0 and end_line != actual_end:
            hints.append(
                f"end_line clamped from {end_line} to {actual_end} (file has {total_lines} lines)."
            )

        selected = lines[actual_start - 1 : actual_end]
        numbered = "".join(
            f"{i:>6}|{line}" for i, line in enumerate(selected, start=actual_start)
        )

        if actual_end < total_lines:
            hints.append(
                f"Showing lines {actual_start}-{actual_end} of {total_lines}. "
                "Request a further range to see more."
            )

        return {
            "path": path,
            "start_line": actual_start,
            "end_line": actual_end,
            "total_lines": total_lines,
            "content": numbered,
            "hint": " ".join(hints) if hints else "Full file returned.",
        }
