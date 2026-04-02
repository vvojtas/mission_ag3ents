# Task 06 — File Management MCP Server

**MCP root:** `task_06/tools/file_management/`

## Overview

Local MCP server for workspace text files: list root-level files with line counts, read (full or by line range), create, and update by deleting or replacing line ranges.
Designed for **in-process** use via `Client(mcp)` (same pattern as `task_04/tools/file_managment/`, with a non-recursive list tool).

**Transport:**

- Primary: **in-process** — `from task_06.tools.file_management import mcp` then `async with Client(mcp) as client: ...`
- Standalone HTTP: `uv run python -m task_06.tools.file_management.server` — `streamable-http` on `127.0.0.1:8019` (see `server.py` `if __name__ == "__main__"`).

## Requirements summary

- List files — workspace root only, single level (no recursion); each file includes line count (aligned with `ws_read_text_file` line splitting).
- Read text files — full file or a 1-based inclusive line range (`start_line`, `end_line`; `end_line=0` means through EOF).
- Create new files (reject if path already exists; parents created as needed).
- Update existing files — `delete` removes a line range; `replace` substitutes a range with `new_content`.
- Paths must stay under the configured workspace root (via `MCPWorkspaceSettings` / `MCP_WORKSPACE_ROOT`).

## Module map

| MCP tool            | Module                            |
| ------------------- | --------------------------------- |
| `ws_list_files`     | `tools/list_workspace_files.py`     |
| `ws_read_text_file` | `tools/read_workspace_text_file.py` |
| `ws_create_file`    | `tools/create_workspace_file.py`    |
| `ws_update_file`    | `tools/update_workspace_file.py`    |
| *(shared)*          | `tools/path_utils.py`               |

## Tool catalog

### `ws_list_files`

**Responsibility:** List files directly under the workspace root (not in subfolders); include line count per file.

**Parameters:** none.

**Returns:** `{ files: list[{ path: str, lines: int }], total: int, hint: str }` — sorted by path (case-insensitive). If a file cannot be read, that entry may include `lines: null` and `error: "permission denied"`.

**Errors / edge cases:** Permission denied when listing the root → top-level `error` string instead of `files`.

---

### `ws_read_text_file`

Read workspace text; response uses numbered lines `NNNNNN|...` (same width as task 04).

| Parameter    | Type  | Required | Description |
| ------------ | ----- | -------- | ----------- |
| `path`       | `str` | Yes      | Workspace-relative path. |
| `start_line` | `int` | No       | First line (1-based). Default `1`. |
| `end_line`   | `int` | No       | Last line inclusive; `0` = through end of file. Default `0`. |

**Returns:** `path`, `start_line`, `end_line`, `total_lines`, `content`, `hint`.

---

### `ws_create_file`

Create a new file; fails if it already exists.

| Parameter   | Type  | Required | Description |
| ----------- | ----- | -------- | ----------- |
| `file_name` | `str` | Yes      | Workspace-relative path. |
| `content`   | `str` | No       | Initial body; empty if omitted. |

**Returns:** `path`, `total_lines`, `hint`.

---

### `ws_update_file`

Edit an existing file; returns full numbered content after the change.

| Parameter     | Type   | Required        | Description |
| ------------- | ------ | --------------- | ----------- |
| `file_name`   | `str`  | Yes             | Workspace-relative path. |
| `mode`        | `str`  | Yes             | `"delete"` or `"replace"`. |
| `start_line`  | `int`  | Yes for both    | First line of range (1-based). |
| `end_line`    | `int`  | Yes for both    | Last line inclusive (1-based). |
| `new_content` | `str`  | Yes for replace | Replacement text for `replace` mode. |

**Returns:** `path`, `total_lines`, `content`, `hint`.

## Open questions

*None.*
