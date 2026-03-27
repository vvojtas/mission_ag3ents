# File Management MCP Server

**MCP root:** `task_04/tools/file_managment/`

## Overview

Local MCP server providing read-only workspace file access for LLM agents.
Designed for **in-process** use via `Client(mcp)`.

**Transport:** In-process (`Client(mcp)`) — no standalone HTTP needed for normal use.

## Requirements

- List files in the workspace, with optional glob/name filter.
- Read text files — full content or a line range fragment.
- Search text content across workspace files — returns matching locations with context.
- All paths are restricted to the workspace root (no directory traversal).
- Read-only — no file creation, modification, or deletion.

## Module Map

| MCP Tool                   | Module                                     |
| -------------------------- | ------------------------------------------ |
| `ws_list_files`            | `tools/list_workspace_files.py`            |
| `ws_read_text_file`        | `tools/read_workspace_text_file.py`        |
| `ws_search_text`           | `tools/search_workspace_text.py`           |
| *(shared helpers)*         | `tools/path_utils.py`                      |

## Tool Catalog

### `ws_list_files`

**Responsibility:** List files in the workspace, optionally filtered by a glob pattern.

**Description (model-facing):**
List files in the workspace directory. Returns relative paths. Use the `pattern` parameter to filter by glob (e.g. `*.py`, `docs/**/*.md`). Without a pattern all files are returned.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pattern` | `str` | No | Glob pattern to filter files (e.g. `*.py`, `**/*.md`). Defaults to `**/*` (all files). |

**Returns:** `{ files: list[str], total: int, hint: str }` — list of workspace-relative paths sorted alphabetically, count, and a next-step hint.

**Errors / edge cases:**
- Pattern matches nothing → empty list with hint "No files matched the pattern."
- Invalid glob syntax → error message with allowed pattern examples.

---

### `ws_read_text_file`

**Responsibility:** Read the content of a text file — fully or a line range fragment.

**Description (model-facing):**
Read a text file from the workspace. Returns numbered lines. Provide `start_line` and/or `end_line` to read a fragment (1-based, inclusive). Omit both to read the entire file.

| Parameter    | Type  | Required | Description |
|--------------|-------|----------|-------------|
| `path`       | `str` | **Yes**  | Workspace-relative path to the file. |
| `start_line` | `int` | No       | First line to return (1-based). Defaults to 1. |
| `end_line`   | `int` | No       | Last line to return (1-based, inclusive). Defaults to end of file. |

**Returns:** `{ path: str, start_line: int, end_line: int, total_lines: int, content: str, hint: str }` — the text with line numbers, metadata, and hints when the range was clamped.

**Errors / edge cases:**
- File not found → error with hint to list files first.
- Path outside workspace → rejected with error.
- Binary file detected → error suggesting the file is not a text file.
- Range clamped to file length → hint stating actual bounds.

---

### `ws_search_text`

**Responsibility:** Search content of text files for a string/pattern. Returns matching locations.

**Description (model-facing):**
Search text files in the workspace for a string or regex pattern. Returns a list of matches with file path, line number, and text fragment. Optionally restrict to specific files.

| Parameter          | Type        | Required | Description |
|--------------------|-------------|----------|-------------|
| `query`            | `str`       | **Yes**  | Search string or regex pattern. |
| `files`            | `list[str]` | No       | List of workspace-relative file paths to search. Searches all text files if omitted. |
| `max_results_per_file` | `int`  | No       | Maximum matches to return per file. Default 10. |
| `max_total_results`    | `int`  | No       | Maximum total matches to return. Default 50. |

**Returns:** `{ matches: list[{file, line, text}], total_matches: int, truncated: bool, hint: str }` — match list, count, whether results were truncated, and a next-step hint.

**Errors / edge cases:**
- No matches → empty list with hint.
- Invalid regex → falls back to literal string search, hint notes fallback.
- Binary files silently skipped.
- Results truncated → `truncated: true` with hint to narrow scope.

## Open Questions

*None — requirements are clear.*
