# Hub Doc Download MCP Server

**MCP root:** `task_04/tools/hub_doc_download/`

## Overview

MCP server providing a single tool to download documentation files from the
hub API (`/dane/doc/`) and save them into the local workspace.

**Transport:** In-process (`Client(mcp)`) — no standalone HTTP needed for normal use.

## Requirements

- Download one or more named files from `{hub_api_url}/dane/doc/{file_name}`.
- Save each file to the workspace root using its original filename.
- Skip files that already exist locally unless `force=True`.
- Authenticate via `HubClient` (uses `hub_api_key` from `Settings`).

## How to attach

**In-process (primary):**

```python
from task_04.tools.hub_doc_download import mcp as hub_doc_mcp
from fastmcp import Client

async with Client(hub_doc_mcp) as client:
    await client.call_tool("hub_download_doc", {"file_names": ["index.md"]})
```

**Standalone (development only):**

```powershell
uv run python -m task_04.tools.hub_doc_download.server
```

## Module Map

| MCP Tool            | Module                    |
| ------------------- | ------------------------- |
| `hub_download_doc`  | `tools/download_doc.py`   |

## Tool Catalog

### `hub_download_doc`

**Responsibility:** Download documentation files from the hub and save them to the workspace.

**Description (model-facing):**
Download one or more files from the hub documentation endpoint and save them
to the workspace. Existing files are skipped unless `force` is true.

| Parameter    | Type        | Required | Description |
|--------------|-------------|----------|-------------|
| `file_names` | `list[str]` | **Yes**  | Names of files to download (e.g. `["index.md", "poziomy.md"]`). |
| `force`      | `bool`      | No       | When true, overwrite existing local files. Default `false`. |

**Returns:** `{ downloaded: list[str], skipped: list[str], errors: list[{file, error}], hint: str }`
- `downloaded` — files that were fetched and saved.
- `skipped` — files that already existed locally (only when `force=false`).
- `errors` — files that failed with an error message per file.
- `hint` — suggested next step for the model.

**Errors / edge cases:**
- File already exists and `force=false` → added to `skipped`, not an error.
- HTTP error from hub → added to `errors` with status/message.
- Empty `file_names` list → immediate return with hint "No files requested."

**Maps to:** `HubClient.download_file(url_path, file_path)` for each file.

## Open Questions

*None — requirements are clear.*
