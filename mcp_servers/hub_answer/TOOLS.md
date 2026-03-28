# Hub Answer MCP Server

**MCP root:** `mcp_servers/hub_answer/`

## Overview

MCP server providing a single tool to submit task answers to the hub API (`/verify`)
and return structured success/failure information including the flag on success.

**Transport:** In-process (`Client(mcp)`) — no standalone HTTP needed for normal use.

## Requirements

- Submit an answer for a named task to `{hub_api_url}/verify`.
- Accept answer as `str`, `list`, or `dict` depending on the task.
- Return whether the submission succeeded (`code == 0` means success, negative = failure).
- Extract and surface the flag (e.g. `{FLG:BUSTED}`) from the hub message on success.
- Authenticate via `HubClient` (uses `hub_api_key` from `Settings`).
- Handle HTTP errors and surface them as structured failure responses.

## How to attach

**In-process (primary):**

```python
from mcp_servers.hub_answer import mcp as hub_answer_mcp
from fastmcp import Client

async with Client(hub_answer_mcp) as client:
    await client.call_tool("hub_post_answer", {"task_name": "mp3", "answer": "42"})
```

**Standalone (development only):**

```powershell
uv run python -m mcp_servers.hub_answer.server
```

## Module Map

| MCP Tool          | Module                 |
| ----------------- | ---------------------- |
| `hub_post_answer` | `tools/post_answer.py` |

## Tool Catalog

### `hub_post_answer`

**Responsibility:** Submit a task answer to the hub and return structured result with success/failure and flag.

**Description (model-facing):**
Submit an answer for a task to the hub API. Returns whether the submission succeeded,
the raw hub message, and the extracted flag on success.

| Parameter   | Type                   | Required | Description |
|-------------|------------------------|----------|-------------|
| `task_name` | `str`                  | **Yes**  | Name of the task to submit (e.g. `"mp3"`, `"photos"`). Ask the user if not specified. |
| `answer`    | `str \| list \| dict`  | **Yes**  | The answer payload. Format depends on the task — can be a plain string, a list of values, or a dict. |

**Returns:** `{ success: bool, code: int | None, message: str, flag: str | None, hint: str }`

- `success` — `true` when `code == 0`, `false` otherwise.
- `code` — raw numeric code from the hub (`0` = success, negative = failure, `null` on network error).
- `message` — raw message string from the hub response.
- `flag` — extracted flag string (e.g. `{FLG:BUSTED}`) when present in the message, otherwise `null`.
- `hint` — suggested interpretation for the model (e.g. "Task solved! Flag: {FLG:BUSTED}").

**Hub response examples:**

```json
{"code": 0, "message": "{FLG:BUSTED}"}
{"code": -910, "message": "Incorrect person identification. Check name, surname, access level, and power plant code."}
```

**Errors / edge cases:**

- `code == 0` → success; flag extracted from `message` via regex `{FLG:[^}]+}`.
- Negative `code` → failure; `hint` describes the error with the code.
- HTTP error (4xx/5xx) → `success: false`, `code: null`, error details in `message`.
- Network/unexpected error → `success: false`, `code: null`, exception message in `message`.

**Maps to:** `HubClient.post_answer(task_name, answer)` → `POST /verify`

## Open Questions

*None — requirements are clear.*
