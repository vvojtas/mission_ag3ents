# Task 07

## Objective

Placeholder — set the hub goal, expected answer shape, and assignment code once the task is defined.

## Approach

1. Load `prompts/agent.md` with placeholders (`date`, `task_code`).
2. Run the **agentic loop** with MCP: `mock_echo` for wiring checks, `hub_answer` for `hub_post_answer` submit/retry.
3. Extend `task_07/tools/` with real FastMCP servers as needed (see `task_04/` for patterns).
4. Emit structured `Task07Answer` (`flag`, `response`).

## LLM usage

**Agentic loop** with MCP tools via `ToolsLoop` + `MCPClient`. Structured output for the final answer. Tune `reasoning`, `parallel_tool_calls`, and `enable_web_search` in `solution.py` as needed.

## Notes

Hub submission uses `hub_post_answer`: the JSON body is passed **as a string** in the tool argument (the tool parses it when valid JSON).

Replace `task_code="TBD"` in `solution.py` and the prompt when the real assignment code is known.

## Featured models cost

*(Fill after runs — output from the cost tracker.)*

| Model | Total Cost | Input Cost | Output Cost | Input Tokens | Cached Tokens | Output Tokens | Reason Tokens | Requests |
|-------|------------|------------|-------------|--------------|---------------|---------------|---------------|----------|
| | | | | | | | | |
