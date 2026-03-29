# Task 05

## Objective
Define the hub assignment goal, expected answer shape, and flag handling once the task brief is available.

## Approach
1. Load the dated system prompt (`prompts/agent.md`).
2. **Agentic loop** with MCP: stub `mock_echo` for tool wiring checks, `hub_answer` for submit/retry when the assignment code and JSON payload are known.
3. Replace placeholders, add task-specific tools under `task_05/tools/`, and tune the loop until the hub accepts the answer.

## LLM usage
**Agentic loop** with MCP tools via `ToolsLoop` + `MCPClient`. Structured output for the final answer (`Task05Answer`). Adjust `model`, `max_iterations`, `reasoning`, `parallel_tool_calls`, and `enable_web_search` in `solution.py` as the task requires.

## Notes
Stub `mock_echo` is for verifying `ToolsLoop` and MCP wiring; remove or replace when real tools are added. Set the real hub assignment code in the prompt and in `hub_post_answer` instructions.

## Featured models cost

| Model | Total Cost | Input Cost | Output Cost | Input Tokens | Output Tokens | Requests |
|-------|------------|------------|-------------|--------------|---------------|----------|
|       |            |            |             |              |               |          |
