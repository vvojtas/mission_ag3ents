---
name: new-task-setup
description: Scaffolds a new task_NN folder for agentic hub tasks using ToolsLoop, in-process MCP clients, PromptLoader, DashboardClient, hub_answer MCP, and guaranteed cost reporting. Use when adding a new task package, cloning the task_04 stack, or wiring hub_post_answer with a tools loop.
---

# New task setup (mission_ag3ents)

Follow `task_04/` as the reference layout. Prefer **focused diffs**: only add what this task needs.

## 1. Package layout

Create `task_NN/` with:

- `solution.py` — async `main()` + `asyncio.run(main())`; docstring includes `uv run python -m task_NN.solution`
- `README.md` — objective, approach, LLM usage, notes (see §7)
- `prompts/` — at least one stub `.md` prompt (see §6)
- `tools/` — task-local FastMCP servers (see §8); optional nested packages per server

Ensure `pyproject.toml` still discovers `task_*` packages (`[tool.setuptools.packages.find]`).

## 2. `solution.py` wiring (happy path)

Use this structure (order matters for lifetimes):

1. **`setup_logging`** — `setup_logging(level=logging.INFO, task_dir=Path(__file__).parent)` so logs land under the task folder.
2. **`Settings()`** — hub URL, API keys, `dashboard_ws_url`, etc.
3. **`CostTracker()`** — one instance shared by `LLMClient` and any MCP tools that bill LLM calls (e.g. vision helpers).
4. **`async with`** stack (each MCP server gets its own `MCPClient`):
   - `HttpClientProvider(settings) as provider`
   - `MCPClient(...)` for each in-process `FastMCP` instance the task needs
   - **`DashboardClient(settings.dashboard_ws_url) as event_poster`**
5. Inside the stack:
   - `llm_client = LLMClient(provider, cost_tracker)`
   - **`try` / `finally`** around the main work (see §5)
   - `event_poster.post(ConversationStart())` once before the loop / first LLM call
   - `PromptLoader(Path(__file__).parent / "prompts")`
   - `ToolsLoop(llm_client, event_poster=event_poster, mcp_clients=[...])` then **`await tools_loop.initialize()`**
   - Build initial messages with `prompt_loader.load_prompt("stub_name", **kwargs)` (see §6)
   - **`await tools_loop.run(...)`** with `model`, `input`, `max_iterations`, optional `text_format` (Pydantic), `reasoning`, `parallel_tool_calls`, `enable_web_search` as required

Reference implementation: `task_04/solution.py`.

## 3. Hub answer MCP

Submit final answers via the shared hub tool server:

- Import: `from mcp_servers.hub_answer import mcp as hub_answer_mcp`
- Include `MCPClient(hub_answer_mcp)` in the same `async with` stack as other MCP clients.
- Pass that client into `ToolsLoop(..., mcp_clients=[..., hub_answer_client])`.
- In prompts, instruct the model **when and how** to call **`hub_post_answer`** (task code, JSON shape, retries on rejection).

Server implementation (tool schemas, env): `mcp_servers/hub_answer/`.

## 4. Dashboard client

- Construct with `DashboardClient(settings.dashboard_ws_url)`.
- Enter it as an async context manager **alongside** HTTP/MCP clients so the background sender stays alive for the whole run.
- Fire **`event_poster.post(ConversationStart())`** near the start of the task.
- Fire cost summary on shutdown (see §5).

## 5. Cost reporting (normal exit or failure)

Guarantee reporting in a **`finally`** block inside the `async with` where `llm_client` exists:

```python
try:
    ...
finally:
    llm_client.print_cost()
    event_poster.post(TotalCost(models=cost_tracker.snapshot()))
```

Import `TotalCost` from `common.events`. This covers errors after the LLM client is constructed: logs match `CostTracker` / OpenRouter usage and the dashboard receives `TotalCost`.

If a task spins a **FastAPI lifespan** or other long-lived process, mirror `task_03/solution.py`: emit the same `print_cost` + `TotalCost` on shutdown (and give the dashboard queue time to drain if needed).

## 6. Prompts + `PromptLoader`

- Add `prompts/<name>.md` using Markdown section headers **`# System`**, **`# User`**, etc. — each `# Role` becomes one message; role string is the header text lowercased.
- Placeholders use `{name}`; pass values via `load_prompt("name", key=value, ...)`.
- Loader resolves files as `Path(__file__).parent / "prompts"`.

Stub prompt: minimal `# System` block with one or two sentences describing the agent, plus optional `{placeholders}` for dynamic lines (dates, task codes).

## 7. `README.md`

Match `task_04/README.md` sections:

- **Objective** — hub goal, answer/flag expectations
- **Approach** — data sources, which MCP servers, how the loop decides completion
- **LLM usage** — `ToolsLoop`, structured output, knobs (`reasoning`, `parallel_tool_calls`, `enable_web_search`)
- **Notes** — edge cases, model notes, cost gotchas
- **Featured models cost** - section to enter output of cost tracker later on

## 8. Task-local MCP tools (including a mock)

Each logical server lives under `task_NN/tools/<server_name>/`:

- `server.py` — `create_<name>_mcp(...) -> FastMCP`, module-level `mcp = create_<name>_mcp()`, optional `if __name__ == "__main__": mcp.run(...)`
- `__init__.py` — export `mcp` and `create_*` if needed
- `tools/` — one module per `register_*` function attaching `@mcp.tool(...)` handlers (see `task_04/tools/file_managment/`)

**Mock tool:** add a tiny server with one tool (e.g. echo input, return fixed JSON) so `ToolsLoop.initialize()` and hub wiring can be tested before real tools exist. Replace or extend with real tools as the task grows.

For FastMCP patterns and LLM-using tools, see `.cursor/skills/mcp-server-creation/SKILL.md`.

## 9. Imports checklist

Typical stack:

- `common`: `Settings`, `setup_logging`
- `common.events`: `ConversationStart`, `TotalCost`
- `common.llm_api`: `CostTracker`, `HttpClientProvider`, `LLMClient`, `MCPClient`, `ToolsLoop`
- `common.prompt_loader`: `PromptLoader`
- `dashboard.client`: `DashboardClient`
- `mcp_servers.hub_answer`: `mcp as hub_answer_mcp`
- Relative imports for `task_NN.tools...`

## 10. Verification

From repo root (PowerShell):

```powershell
uv run python -m task_NN.solution
```

Confirm logs, `print_cost` output, dashboard events (if the dashboard is running), and that `hub_post_answer` is visible to the model via the loaded prompt plus MCP tool list.
