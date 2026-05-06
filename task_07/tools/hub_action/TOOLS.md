# Hub Action MCP Server

**MCP root:** `task_07/tools/hub_action/`

## Overview

- **`hub_action`** — validates grid cells (`axb` with `a,b ∈ {1,2,3}`), then for each cell posts to hub `/verify`:

```json
{
  "apikey": "<from Settings>",
  "task": "electricity",
  "answer": { "rotate": "2x3" }
}
```

  Aggregates hub JSON (or errors) into `results`.

- **`hub_reset`** — no parameters; `GET https://hub.ag3nts.org/data/{apikey}/electricity.png?reset=1` with `Settings.hub_api_key` (URL-encoded like `hub_downloader`). Response body is not saved.

**Transport:** In-process (`Client(mcp)`); standalone HTTP port 8014.

## Module Map

| MCP Tool     | Module                    |
| ------------ | ------------------------- |
| `hub_action` | `tools/rotate_calls.py`   |
| `hub_reset`  | `tools/reset_task.py`     |

## Tool: `hub_action`

| Parameter   | Type        | Description        |
| ----------- | ----------- | ------------------ |
| `rotations` | `list[str]` | Cells, e.g. `["2x3"]`. |

**Returns:** `ok`, `task`, `results` (list of `{cell, hub_response}` or `{cell, error}`); validation failure sets `ok: false` and `invalid_cells`.

## Tool: `hub_reset`

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| *(none)*  | —    | —           |

**Returns:** `ok`, `http_status` on success; on failure `ok: false`, `error`, optional `http_status`. Does not persist the PNG.
