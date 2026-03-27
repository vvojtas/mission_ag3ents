"""MCP tool: ws_search_text — search text content across workspace files."""

import re
from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from .path_utils import (
    is_likely_binary,
    iter_text_files,
    resolve_workspace_path,
)


def register_search_workspace_text(mcp: FastMCP, workspace_root: Path) -> None:
    """Attach the ws_search_text tool to the MCP server."""

    @mcp.tool(
        name="ws_search_text",
        description=(
            "Search text files in the workspace for a string or regex pattern. "
            "Returns matching locations with file path, line number, and text fragment. "
            "Optionally restrict the search to specific files."
        ),
    )
    async def ws_search_text(
        query: Annotated[
            str,
            Field(description="Search string or regex pattern."),
        ],
        files: Annotated[
            list[str],
            Field(
                description=(
                    "List of workspace-relative file paths to search. "
                    "Searches all text files if not provided."
                ),
            ),
        ] = [],  # noqa: B006 — mutable default is fine here; FastMCP copies per call
        max_results_per_file: Annotated[
            int,
            Field(description="Maximum matches to return per file. Default 10."),
        ] = 10,
        max_total_results: Annotated[
            int,
            Field(description="Maximum total matches to return. Default 50."),
        ] = 50,
    ) -> dict[str, Any]:
        regex, used_literal = _compile_pattern(query)

        if files:
            target_paths = _resolve_file_list(workspace_root, files)
        else:
            root = workspace_root.resolve()
            target_paths = [(root / rel) for rel in iter_text_files(workspace_root)]

        matches: list[dict[str, Any]] = []
        total_found = 0
        truncated = False

        for abs_path in target_paths:
            if len(matches) >= max_total_results:
                truncated = True
                break

            file_matches = _search_file(
                abs_path,
                regex,
                workspace_root,
                max_per_file=max_results_per_file,
                budget=max_total_results - len(matches),
            )
            total_found += len(file_matches)
            matches.extend(file_matches)

        if not matches:
            hint = f"No matches found for '{query}'."
            if used_literal:
                hint += " (Pattern was treated as a literal string.)"
            hint += " Try a broader query or check ws_list_files for available files."
        elif truncated:
            hint = (
                f"Results truncated to {max_total_results} matches. "
                "Narrow the search by specifying files or a more specific query."
            )
        else:
            hint = (
                f"Found {len(matches)} match(es). "
                "Use ws_read_text_file to see more context around a match."
            )

        if used_literal:
            hint += " Note: regex was invalid, fell back to literal string search."

        return {
            "matches": matches,
            "total_matches": len(matches),
            "truncated": truncated,
            "hint": hint,
        }


def _compile_pattern(query: str) -> tuple[re.Pattern[str], bool]:
    """Try to compile as regex; fall back to escaped literal."""
    try:
        return re.compile(query, re.IGNORECASE), False
    except re.error:
        return re.compile(re.escape(query), re.IGNORECASE), True


def _resolve_file_list(workspace_root: Path, files: list[str]) -> list[Path]:
    """Resolve and filter user-provided file paths."""
    resolved: list[Path] = []
    root = workspace_root.resolve()
    for f in files:
        try:
            p = resolve_workspace_path(workspace_root, f)
        except ValueError:
            continue
        if p.is_file() and not is_likely_binary(p) and p.is_relative_to(root):
            resolved.append(p)
    return resolved


def _search_file(
    abs_path: Path,
    regex: re.Pattern[str],
    workspace_root: Path,
    *,
    max_per_file: int,
    budget: int,
) -> list[dict[str, str | int]]:
    """Search a single file for regex matches, returning up to the budget."""
    try:
        text = abs_path.read_text(encoding="utf-8", errors="replace")
    except (PermissionError, OSError):
        return []

    lines = text.splitlines()
    results: list[dict[str, str | int]] = []
    limit = min(max_per_file, budget)

    rel_path = abs_path.relative_to(workspace_root.resolve()).as_posix()

    for line_num, line in enumerate(lines, start=1):
        if regex.search(line):
            results.append({
                "file": rel_path,
                "line": line_num,
                "text": line.strip()[:200],
            })
            if len(results) >= limit:
                break

    return results
