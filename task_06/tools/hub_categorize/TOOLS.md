# Hub Categorize MCP (`task_06/tools/hub_categorize`)

**MCP root:** `task_06/tools/hub_categorize/`

## Overview

| Item | Value |
|------|--------|
| **Display name** | Task 06 Hub Categorize MCP Server |
| **Purpose** | Send classification prompts to the hub `/verify` endpoint and manage run state (reset). |
| **Secrets** | `Settings` / `.env` — hub URL, API key, `HUB_TASK_NAME`. |
| **Standalone transport** | `streamable-http` on `127.0.0.1:8019` |

## Consumer attachment

- **In-process (recommended):**

  ```python
  from task_06.tools.hub_categorize import mcp
  from common.llm_api.mcp_client import MCPClient

  async with MCPClient(mcp) as client:
      ...
  ```

- **Standalone HTTP:** `uv run python -m task_06.tools.hub_categorize.server`

## Requirements

- POST to `{hub_api_url}/verify` with payload `{"apikey": "...", "task": "<HUB_TASK_NAME>", "answer": {"prompt": "..."}}`.
- `HUB_TASK_NAME` and `hub_api_key` come from `Settings` (`.env`).
- Response contains `code` (negative = error) and `message`; may include token usage and correctness info.
- Reset clears token usage for the current run by sending `{"prompt": "reset"}` as the answer prompt.

## Module map

| MCP tool name | Python module |
|---------------|---------------|
| `categorize_send_prompt` | `tools/send_prompt.py` |
| `categorize_reset` | `tools/reset.py` |

## Tool catalog

### `categorize_send_prompt`

- **Responsibility:** Submit a prompt to the hub and return the response.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | `str` | **yes** | The prompt text to submit. |

- **Wire payload:** `POST /verify` with `{"apikey": "...", "task": "<HUB_TASK_NAME>", "answer": {"prompt": "<prompt>"}}`
- **Returns:** `{ success: bool, code: int | None, message: str, data: dict | None, hint: str }`
- **Errors:** Negative `code` = hub rejection. HTTP/network errors surfaced in `message`.

### `categorize_reset`

- **Responsibility:** Reset the current run.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| *(none)* | — | — | — |

- **Wire payload:** `POST /verify` with `{"apikey": "...", "task": "<HUB_TASK_NAME>", "answer": {"prompt": "reset"}}`
- **Returns:** `{ success: bool, code: int | None, message: str, data: dict | None, hint: str }`

## Open questions

None.
