"""MCP tool: ws_update_file — modify an existing workspace text file."""

from pathlib import Path
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from .path_utils import resolve_workspace_path


def register_update_workspace_file(mcp: FastMCP, workspace_root: Path) -> None:
    """Attach the ws_update_file tool to the MCP server."""

    @mcp.tool(
        name="ws_update_file",
        description=(
            "Update an existing text file in the workspace. "
            "Choose a mode: "
            "`delete` removes lines start_line–end_line; "
            "`replace` substitutes that range with new_content; "
            "`append` adds new_content at the end of the file. "
            "Returns the full numbered file content after the edit."
        ),
    )
    async def ws_update_file(
        file_name: Annotated[
            str,
            Field(description="Workspace-relative path to the file."),
        ],
        mode: Annotated[
            Literal["delete", "replace", "append"],
            Field(description='Edit mode: "delete", "replace", or "append".'),
        ],
        start_line: Annotated[
            int | None,
            Field(description="1-based first line of the target range (required for delete/replace)."),
        ] = None,
        end_line: Annotated[
            int | None,
            Field(description="1-based inclusive last line of the target range (required for delete/replace)."),
        ] = None,
        new_content: Annotated[
            str | None,
            Field(description="Content to insert (replace) or add at the end (append)."),
        ] = None,
    ) -> dict[str, Any]:
        try:
            resolved = resolve_workspace_path(workspace_root, file_name)
        except ValueError as exc:
            return {"error": str(exc)}

        if not resolved.exists():
            return {
                "error": f"File not found: {file_name}",
                "hint": "Use ws_create_file to create a new file.",
            }
        if not resolved.is_file():
            return {"error": f"Path is not a file: {file_name}"}

        try:
            text = resolved.read_text(encoding="utf-8")
        except PermissionError:
            return {"error": f"Permission denied: {file_name}"}

        lines = text.splitlines(keepends=True)

        result = _apply_edit(mode, lines, start_line, end_line, new_content)
        if "error" in result:
            return result

        new_text = "".join(result["lines"])
        try:
            resolved.write_text(new_text, encoding="utf-8")
        except PermissionError:
            return {"error": f"Permission denied writing: {file_name}"}

        final_lines = new_text.splitlines(keepends=True)
        total = len(final_lines)
        numbered = "".join(f"{i:>6}|{line}" for i, line in enumerate(final_lines, start=1))

        return {
            "path": file_name,
            "total_lines": total,
            "content": numbered,
            "hint": f'File updated ({mode}). Now has {total} line(s).',
        }


def _apply_edit(
    mode: str,
    lines: list[str],
    start_line: int | None,
    end_line: int | None,
    new_content: str | None,
) -> dict[str, Any]:
    """Compute the updated line list for the requested edit mode.

    Returns a dict with either an ``"error"`` key or an ``"lines"`` key
    containing the resulting list of lines.
    """
    if mode == "append":
        return _apply_append(lines, new_content)
    if mode in ("delete", "replace"):
        return _apply_range_edit(mode, lines, start_line, end_line, new_content)
    return {"error": f'Unknown mode: "{mode}". Use "delete", "replace", or "append".'}


def _apply_append(lines: list[str], new_content: str | None) -> dict[str, Any]:
    if new_content is None:
        return {"error": 'mode "append" requires new_content.'}
    suffix = "\n" if lines and not lines[-1].endswith("\n") else ""
    return {"lines": lines + [suffix + new_content]}


def _apply_range_edit(
    mode: str,
    lines: list[str],
    start_line: int | None,
    end_line: int | None,
    new_content: str | None,
) -> dict[str, Any]:
    if start_line is None or end_line is None:
        return {"error": f'mode "{mode}" requires start_line and end_line.'}
    if mode == "replace" and new_content is None:
        return {"error": 'mode "replace" requires new_content.'}
    if start_line < 1 or end_line < 1:
        return {"error": "start_line and end_line must be >= 1."}
    if start_line > end_line:
        return {"error": f"start_line ({start_line}) must be <= end_line ({end_line})."}

    total_lines = len(lines)
    if start_line > total_lines:
        return {
            "error": f"start_line ({start_line}) exceeds file length ({total_lines} lines).",
        }

    actual_end = min(end_line, total_lines)
    before = lines[: start_line - 1]
    after = lines[actual_end:]

    if mode == "delete":
        return {"lines": before + after}

    replacement = new_content if new_content.endswith("\n") else new_content + "\n"  # type: ignore[union-attr]
    return {"lines": before + [replacement] + after}
