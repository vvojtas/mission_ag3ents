# Hub Doc Download MCP (`task_06/tools/hub_doc_download`)

**MCP root:** `task_06/tools/hub_doc_download/`

## Overview

| Item | Value |
|------|--------|
| **Display name** | Task 06 Hub Doc Download MCP Server |
| **Purpose** | Fetch files from the hub API documentation path (`/dane/doc/`) into the MCP workspace. |
| **Secrets** | `Settings` / `.env` — hub URL, API key (same as other hub tools). |
| **Standalone transport** | `streamable-http` on `127.0.0.1:8018` |

## Consumer attachment

- **In-process (recommended for task solution):** same object the server composes.

  ```python
  from task_06.tools.hub_doc_download import mcp
  from common.llm_api.mcp_client import MCPClient

  async with MCPClient(mcp) as client:
      ...
  ```

  Or with FastMCP’s client:

  ```python
  from fastmcp import Client
  from task_06.tools.hub_doc_download import mcp

  async with Client(mcp) as client:
      await client.list_tools()
      await client.call_tool("hub_download_doc", {"file_names": ["index.md"], "force": False})
  ```

- **Standalone HTTP:** from repo root (PowerShell):

  `uv run python -m task_06.tools.hub_doc_download.server`

## Requirements (summary)

- Host passes hub credentials via environment; no hardcoded keys.
- Downloads are written under **`MCPWorkspaceSettings.workspace_root`** (or the path injected when calling `create_hub_doc_download_mcp(..., workspace_root=...)`).
- Model should name files exactly as served under `/dane/doc/<name>`.

## Module map

| MCP tool name | Python module |
|---------------|---------------|
| `hub_download_doc` | `task_06/tools/hub_doc_download/tools/download_doc.py` |

## Tool catalog

### `hub_download_doc`

- **Responsibility:** Download one or more hub doc files by basename into the workspace root.
- **Backend:** `GET /<hub_base>/dane/doc/<file_name>` via `HubClient.download_file` (Bearer token from `Settings`).
- **Parameters**

  | Name | Type | Required | Notes |
  |------|------|----------|--------|
  | `file_names` | `list[str]` | yes (non-empty to perform downloads) | e.g. `["index.md"]`. Model should ask the user if unknown. |
  | `force` | `bool` | no (default `false`) | If `true`, replace existing local files; if `false`, existing files are reported as skipped. |

- **Returns:** `dict` with:

  - `downloaded`: names saved in this call.
  - `skipped`: existed locally and `force` was `false`.
  - `errors`: `{ "file", "error" }[]` for per-file failures (other files may still succeed).
  - `hint`: short human/model-oriented summary; **surface this to the planner** (counts + next step).

- **Edge cases**

  - Empty `file_names`: no HTTP calls; `hint` explains no work.
  - Partial failure: check `errors` and non-empty `downloaded`/`skipped`.
  - Path traversal: callers should only pass basenames expected by the hub; files are written to `workspace_root / name`.

## Open questions

- None for the current single-tool scope.
