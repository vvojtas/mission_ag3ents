# Task 06

## Objective

Complete the hub **categorize** assignment: design a **single English prompt template** (placeholders `{id}`, `{description}`) that a tiny downstream classifier can use. Each filled instance must stay **within ~100 tokens** (see `prompts/categorize.md` and workspace `token_limits.md`; rough check: length ÷ 3 characters). Labels are **DNG** (dangerous) or **NEU** (neutral) only.

**Reactor rule:** Items that are **reactor-related** must always be classified **NEU**, regardless of wording; other goods follow normal dangerous vs neutral semantics.

The agent must download fresh **`categorize.csv`**, maintain **`prompt.txt`** in the task workspace, send **10** filled prompts to the hub in the order **J–D–I–B–A–C–G–E–H–F** (1-based row indices), handle errors and **reset** when needed, and capture the hub **`{FLG:...}`** when all rows pass.

## Approach

1. Load **`prompts/categorize.md`** (system instructions for the agent).
2. **ToolsLoop** with MCP servers:
   - **`hub_answer`** — submit final hub answers / retries (`hub_post_answer`).
   - **`hub_categorize`** — send classification prompts to `/verify` and **reset** runs (`categorize_send_prompt`, `categorize_reset`). See `tools/hub_categorize/TOOLS.md`.
   - **`hub_doc_download`** — fetch hub docs (e.g. **`categorize.csv`**) into the workspace; use **force** when a fresh CSV is required. See `tools/hub_doc_download/TOOLS.md`.
   - **`file_management`** — read/write **`prompt.txt`** and related workspace files. See `tools/file_management/TOOLS.md`.
3. Run from repo root: `uv run python -m task_06.solution`

## LLM usage

**Agentic loop** via `ToolsLoop` + `MCPClient`. Structured final output: **`Task06Answer`** (`flag`, `response`). Defaults in `solution.py` include `anthropic/claude-sonnet-4-6`, extended reasoning, `max_iterations=25`, `parallel_tool_calls=True`, and ephemeral prompt caching — tune as needed.

## Notes

- **`HUB_TASK_NAME`** and hub API settings come from **`Settings`** / `.env` (same as other hub tasks).
- Workspace artifacts live under the configured MCP workspace root (`.workspace/` locally; git-ignored).

## Featured models cost

| Model | Total Cost | Input Cost | Output Cost | Input Tokens | Output Tokens | Requests |
|-------|------------|------------|-------------|--------------|---------------|----------|
|       |            |            |             |              |               |          |
