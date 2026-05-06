# Image Inspector MCP Server

**MCP root:** `task_07/tools/image_inspector/`

## Overview

Vision tool: loads a workspace image and answers a natural-language `query`.

**Transport:** In-process (`Client(mcp)`); optional HTTP on port 8012.

## How to attach

```python
from task_07.tools.image_inspector import create_image_inspector_mcp
from fastmcp import Client

mcp = create_image_inspector_mcp(settings, workspace_root, prompt_loading_path, cost_tracker)
async with Client(mcp) as client:
    await client.call_tool("check_image", {"resource": "electricity.png", "query": "Describe wires."})
```

## Module Map

| MCP Tool      | Module                 |
| ------------- | ---------------------- |
| `check_image` | `tools/check_image.py` |

## Tool: `check_image`

| Parameter  | Type | Description |
| ---------- | ---- | ----------- |
| `resource` | str  | Image file name in the workspace. |
| `query`    | str  | Question for the vision model. |

**Returns:** `response` text, or `error` / `hint` on failure.

**Prompts:** `task_07/prompts/image_inspector.md`
