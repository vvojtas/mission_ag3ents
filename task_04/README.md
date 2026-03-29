# Task 04

## Objective
Fetch hub documentation (from `index.md`), build a declaration in `declaration.txt` matching the official template (routing, fees, abbreviations, images where needed), submit it via hub with assignment code `sendit`, and return the task flag plus hub response text.

## Approach
1. Load the dated system prompt (`prompts/declaration.md`).
2. **Agentic loop** with MCP: local file workspace, hub doc download, `hub_answer` for submit/retry, `image_inspector` for image-only docs.
3. Iterate: fill placeholders from docs, verify against regulations, post JSON answer until hub accepts or returns `{FLG:...}`.
4. Emit structured `Task04Answer` (`flag`, `response`).

## LLM usage
**Agentic loop** with MCP tools via `ToolsLoop` + `MCPClient`. Structured output for the final answer. Tune `reasoning`, `parallel_tool_calls`, and `enable_web_search` in `solution.py` as needed.

## Notes
Hub submission uses `hub_post_answer`: the JSON body is passed **as a string** in the tool argument (the tool parses it when valid JSON).

# Featured models cost

## google/gemini-3-flash-preview (agent loop); openai/gpt-5.2 (vision)

| Model                          | Total Cost   | Input Cost   | Output Cost   | Input Tokens | Cached Tokens | Output Tokens | Reason Tokens | Requests |
|--------------------------------|--------------|--------------|---------------|--------------|---------------|---------------|---------------|----------|
| google/gemini-3-flash-preview  | $0.061437    | $0.055359    | $0.006078     | 283442       | 191915        | 2026          | 294           | 15       |
| openai/gpt-5.2                 | $0.001932    | $0.001036    | $0.000896     | 592          | 0             | 64            | 29            | 1        |
