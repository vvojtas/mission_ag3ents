"""MCP tool: ws_list_files — list files in the workspace."""

from fnmatch import fnmatch
from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from .path_utils import is_likely_binary, should_skip_dir


def register_list_workspace_files(mcp: FastMCP, workspace_root: Path) -> None:
    """Attach the ws_list_files tool to the MCP server."""

    @mcp.tool(
        name="ws_list_files",
        description=(
            "List files in the workspace directory. Returns relative paths. "
            "Use the `pattern` parameter to filter by glob (e.g. `*.py`, `**/*.md`). "
            "Without a pattern all files are returned. "
            "Directories like .git, __pycache__, .venv, and node_modules are excluded."
        ),
    )
    async def ws_list_files(
        pattern: Annotated[
            str,
            Field(
                description=(
                    "Glob pattern to filter files (e.g. `*.py`, `**/*.md`). "
                    "Defaults to all files if not provided."
                ),
            ),
        ] = "",
    ) -> dict[str, Any]:
        root = workspace_root.resolve()
        matched: list[str] = []

        if pattern:
            normalized = pattern.replace("\\", "/")
            for path in _walk_files(root):
                rel = path.relative_to(root).as_posix()
                if fnmatch(rel, normalized):
                    matched.append(rel)
        else:
            for path in _walk_files(root):
                matched.append(path.relative_to(root).as_posix())

        matched.sort()

        if not matched:
            hint = (
                f"No files matched the pattern '{pattern}'."
                if pattern
                else "The workspace appears to be empty."
            )
        else:
            hint = (
                f"Found {len(matched)} file(s). "
                "Use ws_read_text_file to read contents or ws_search_text to search."
            )

        return {"files": matched, "total": len(matched), "hint": hint}


def _walk_files(root: Path) -> list[Path]:
    """Walk workspace and yield non-binary file paths."""
    results: list[Path] = []

    def _recurse(directory: Path) -> None:
        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            return
        for entry in entries:
            if entry.is_dir():
                if not should_skip_dir(entry.name):
                    _recurse(entry)
            elif entry.is_file() and not is_likely_binary(entry):
                results.append(entry)

    _recurse(root)
    return results
