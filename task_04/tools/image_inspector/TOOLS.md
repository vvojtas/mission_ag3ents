# Image Inspector MCP Server

**MCP root:** `task_04/tools/image_inspector/`

## Overview

MCP server providing a single tool to inspect images by sending them to an
OpenRouter-hosted vision LLM together with a user query and returning the
model's answer.

**Transport:** In-process (`Client(mcp)`) — no standalone HTTP needed for normal use.

## Requirements

- Load an image file by name from the workspace.
- Send the image together with a free-form query to a vision-capable LLM via OpenRouter.
- Return the model's textual answer to the caller.
- Authenticate via `Settings` (uses `openrouter_api_key`).

## How to attach

**In-process (primary):**

```python
from task_04.tools.image_inspector import mcp as image_inspector_mcp
from fastmcp import Client

async with Client(image_inspector_mcp) as client:
    await client.call_tool("check_image", {"file_name": "photo.png", "query": "What is in this image?"})
```

**Standalone (development only):**

```powershell
uv run python -m task_04.tools.image_inspector.server
```

## Module Map

| MCP Tool       | Module                  |
| -------------- | ----------------------- |
| `check_image`  | `tools/check_image.py`  |

## Tool Catalog

### `check_image`

**Responsibility:** Inspect an image file using a vision LLM and return the answer.

**Description (model-facing):**
Load an image from the workspace and ask a vision LLM a question about it.
Returns the model's textual answer.

| Parameter   | Type  | Required | Description |
|-------------|-------|----------|-------------|
| `file_name` | `str` | **Yes**  | Name of the image file in the workspace (e.g. `"photo.png"`). Ask the user if not specified. |
| `query`     | `str` | **Yes**  | Free-form question about the image (e.g. `"Describe what you see"`). |

**Returns:** `{ answer: str, hint: str }`
- `answer` — the vision model's textual response.
- `hint` — suggested next step for the model.

**Errors / edge cases:**
- File not found → return error with message.
- Unsupported image format → return error with message.
- LLM API failure → return error with message.

**Maps to:** OpenRouter chat completion with image content (vision model).

## Open Questions

*None — requirements are clear.*
