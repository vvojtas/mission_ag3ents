# Hub Downloader MCP Server

**MCP root:** `task_07/tools/hub_downloader/`

## Overview

MCP server with one tool that downloads the **electricity** task image from
`https://hub.ag3nts.org/data/{apikey}/electricity.png` (API key from `Settings`)
into the configured workspace.

**Transport:** In-process (`Client(mcp)`) — optional standalone HTTP for development.

## How to attach

**In-process:**

```python
from task_07.tools.hub_downloader import create_hub_downloader_mcp
from fastmcp import Client

mcp = create_hub_downloader_mcp(settings, workspace_root)
async with Client(mcp) as client:
    await client.call_tool("hub_downloader", {})
```

**Standalone:**

```powershell
uv run python -m task_07.tools.hub_downloader.server
```

## Module Map

| MCP Tool         | Module                         |
| ---------------- | ------------------------------ |
| `hub_downloader` | `tools/download_electricity.py` |

## Tool Catalog

### `hub_downloader`

**Parameters:**

| Name        | Type        | Required | Description |
| ----------- | ----------- | -------- | ----------- |
| `filename`  | `str \| null` | No     | Local name; default `electricity.png`. |
| `override`  | `bool`      | No       | Default `true`. If `false` and file exists → error. |

**Returns:** `ok`, `path`, `bytes_written`, `resource` (e.g. `<resource>electricity.png</resource>`), `message` on success; `error` on failure.

## Requirements summary

- Uses `HUB_API_KEY` / `Settings.hub_api_key` in the URL path segment.
- Saves under `MCP_WORKSPACE_ROOT` (or injected `workspace_root`).
