# File Management MCP Server

**MCP root:** `task_04/tools/file_managment/`

## Overview

Local MCP server providing workspace file access for LLM agents — read and write.
Designed for **in-process** use via `Client(mcp)`.

**Transport:** In-process (`Client(mcp)`) — no standalone HTTP needed for normal use.

## Requirements

- List files in the workspace, with optional glob/name filter.
- Read text files — full content or a line range fragment.
- Search text content across workspace files — returns matching locations with context.
- Create new text files (rejects overwrites; creates parent directories automatically).
- Update existing files — delete lines, replace a line range, or append content.
- All paths are restricted to the workspace root (no directory traversal).

## Module Map

| MCP Tool                   | Module                                     |
| -------------------------- | ------------------------------------------ |
| `ws_list_files`            | `tools/list_workspace_files.py`            |
| `ws_read_text_file`        | `tools/read_workspace_text_file.py`        |
| `ws_search_text`           | `tools/search_workspace_text.py`           |
| `ws_create_file`           | `tools/create_workspace_file.py`           |
| `ws_update_file`           | `tools/update_workspace_file.py`           |
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

---

### `ws_create_file`

**Responsibility:** Create a new text file in the workspace with optional initial content.

**Description (model-facing):**
Create a new text file at the given workspace-relative path. Provide `content` to populate the file, or omit it to create an empty file. Fails if the file already exists — use `ws_update_file` to modify existing files. Parent directories are created automatically.

| Parameter  | Type  | Required | Description |
|------------|-------|----------|-------------|
| `file_name` | `str` | **Yes** | Workspace-relative path for the new file. |
| `content`  | `str` | No       | Initial file content. Defaults to empty string. |

**Returns:** `{ path: str, total_lines: int, hint: str }`

**Errors / edge cases:**
- File already exists → error with hint to use `ws_update_file`.
- Path escapes workspace → rejected with error.
- Permission denied → error.

---

### `ws_update_file`

**Responsibility:** Modify an existing workspace text file — delete lines, replace a line range, or append content.

**Description (model-facing):**
Update an existing text file. Choose a `mode`: `delete` removes lines `start_line`–`end_line`; `replace` substitutes that range with `new_content`; `append` adds `new_content` at the end. Returns the full file content after the edit.

| Parameter    | Type  | Required            | Description |
|--------------|-------|---------------------|-------------|
| `file_name`  | `str` | **Yes**             | Workspace-relative path to the file. |
| `mode`       | `str` | **Yes**             | One of `"delete"`, `"replace"`, `"append"`. |
| `start_line` | `int` | delete / replace    | 1-based first line of the target range. |
| `end_line`   | `int` | delete / replace    | 1-based inclusive last line of the target range. |
| `new_content`| `str` | replace / append    | Content to insert (replace) or add (append). |

**Returns:** `{ path: str, total_lines: int, content: str, hint: str }` — `content` is the full numbered file after the edit (same `{line}|{text}` format as `ws_read_text_file`).

**Errors / edge cases:**
- File not found → error with hint to use `ws_create_file`.
- Path escapes workspace → rejected with error.
- `start_line` / `end_line` missing for delete/replace, or `new_content` missing for replace/append → clear error.
- `start_line > end_line` or range out of bounds → error with file line count.
- Permission denied → error.

## Open Questions

*None — requirements are clear.*
