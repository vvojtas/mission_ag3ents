# Task 07

## Objective

Placeholder — set the hub goal, expected answer shape, and assignment code once the task is defined.

## Approach

1. Load `prompts/electricity.md` with placeholders (`date`, `task_code`).
2. Run the **agentic loop** with MCP: `hub_downloader`, `image_inspector` (`check_image`), and `hub_action` (no `hub_answer` / `hub_post_answer`).
3. Add or adjust `task_07/tools/` FastMCP servers as needed (see `task_04/` for patterns).
4. Emit structured `Task07Answer` (`flag`, `response`).

## LLM usage

**Agentic loop** with MCP tools via `ToolsLoop` + `MCPClient`. Structured output for the final answer. Tune `reasoning`, `parallel_tool_calls`, and `enable_web_search` in `solution.py` as needed.

## Notes

Grid moves use **`hub_action`** (`rotations` list); image fetch uses **`hub_downloader`**.

Replace `task_code="TBD"` in `solution.py` and the prompt when the real assignment code is known.

## Featured models cost

*(Fill after runs — output from the cost tracker.)*

| Model | Total Cost | Input Cost | Output Cost | Input Tokens | Cached Tokens | Output Tokens | Reason Tokens | Requests |
|-------|------------|------------|-------------|--------------|---------------|---------------|---------------|----------|
| | | | | | | | | |
