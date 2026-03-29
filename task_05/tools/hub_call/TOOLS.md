# Hub Call MCP Server

**MCP root:** `task_05/tools/hub_call/`

## Overview

| Item | Value |
|---|---|
| Server name | Hub Call MCP Server |
| Purpose | Send action commands to the hub API and return structured results with headers |
| Transport | In-process `Client(mcp)` (primary); `streamable-http` on port 8016 (standalone) |
| Host attachment | `from task_05.tools.hub_call import mcp` then `Client(mcp)` |

## Requirements

- Wraps `HubClient.post_answer_with_headers` so the LLM agent can send arbitrary action commands to the hub.
- Automatic retry on **503 Service Unavailable** (configurable, default **3** retries).
- On **429 Too Many Requests**, wait the `Retry-After` header value and retry (does **not** count towards the retry budget).
- Settings and hub credentials loaded from the shared `common.Settings`.

## Module Map

| MCP Tool | Module |
|---|---|
| `send_action` | `task_05/tools/hub_call/tools/send_action.py` |

## Tool Catalog

### `send_action`

| Field | Detail |
|---|---|
| **Responsibility** | Send an action command to the hub and return the response with headers |
| **Description** | Send an action command to the hub API. The command dict must contain an `action` key. If you don't know available actions or parameters, send `{"action": "help"}` to get documentation. |
| **Parameters** | |
| `command` | `dict[str, Any]` — **required**. Must include key `action` (str). May include additional action-specific parameters. |
| **Returns** | `dict` with keys: `success` (bool), `response` (hub JSON body), `headers` (HTTP headers dict), `hint` (guidance for next step) |
| **Errors** | 503 → auto-retry up to 3 times; 429 → wait `Retry-After` then retry (unlimited, not counted); other HTTP errors → returned as structured failure |
| **Hints** | On failure the hint suggests sending `{"action": "help"}` to discover available actions and parameters |

## Open Questions

- None at this time.
