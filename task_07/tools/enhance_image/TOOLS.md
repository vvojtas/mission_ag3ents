# Enhance Image MCP Server

**MCP root:** `task_07/tools/enhance_image/`

## Overview

Transforms a workspace image with Pillow: greyscale (`L`), then **dilate×2 → erode×2 → erode×2 → dilate×2 → erode×3 → dilate×3** (3×3 **MaxFilter** / **MinFilter**), and saves to a new file. **Refuses to overwrite:** if `target_resource` already exists, the tool returns an error.

**Transport:** In-process (`Client(mcp)`); optional HTTP on port **8015**.

## Requirements summary

- **Workspace paths:** `source_resource` and `target_resource` are single file names resolved under `MCP_WORKSPACE_ROOT` / configured workspace root (no subpaths).
- **Target must be absent:** existing target → error.
- **Processing:** greyscale → dilate×2 → erode×2 → erode×2 → dilate×2 → erode×3 → dilate×3 (Pillow only).

## How to attach

```python
from pathlib import Path
from fastmcp import Client

from task_07.tools.enhance_image import create_enhance_image_mcp

mcp = create_enhance_image_mcp(workspace_root=Path("..."))
async with Client(mcp) as client:
    await client.call_tool(
        "enhance_image",
        {"source_resource": "in.png", "target_resource": "out.png"},
    )
```

Standalone from repo root (HTTP on 127.0.0.1:8015):

```powershell
uv run python -m task_07.tools.enhance_image.server
```

## Module map

| MCP tool        | Module                   |
| --------------- | ------------------------ |
| `enhance_image` | `tools/enhance_image.py` |

## Tool: `enhance_image`

**Responsibility:** Read source image from workspace, apply pipeline, write to target path only if target does not exist.

| Parameter          | Type | Required | Description                                                |
| ------------------ | ---- | -------- | ---------------------------------------------------------- |
| `source_resource`  | str  | yes      | Source image file name in the workspace.                   |
| `target_resource`  | str  | yes      | Output file name; must not already exist.                  |

**Returns (success):** `status`, `target_resource`, `path` (absolute saved path).

**Returns (failure):** `error`, `hint` — e.g. missing source, existing target, invalid name, I/O or decode errors.

**Edge cases**

- Empty names, `.`, `..`, or paths with separators → validation error.
- `source_resource` == `target_resource` → error.

## Configuration

- **Workspace:** `MCP_WORKSPACE_ROOT` (see `MCPWorkspaceSettings`).
- **Dependency:** `pillow` (project dependency).
