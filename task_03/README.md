# Task 03

## Objective
Hub **proxy** task: run a local FastAPI app the platform calls. Register the public base URL via `POST /start`; each chat turn is `POST /msg` with `sessionID` and operator message. The agent assists the logistics operator per the task prompt (tools + natural replies).

## How to run

From the repository root:

```powershell
uv run python -m task_03.solution
```

Optional environment variables (see `.env.example`):

- `HOST` — bind address (default `127.0.0.1`)
- `PORT` — port (default `8000`)

Then open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive OpenAPI UI, or `GET /health` for a simple liveness check.

To expose the local server publicly (e.g. for webhooks), run from another terminal:

```powershell
ngrok http 8000
```

## Approach
1. Start the API (see **How to run**); use ngrok so the hub can reach it.
2. On startup, wire `HubClient`, `ToolsLoop`, in-process MCP, prompts, and dashboard events.
3. `/start` posts to hub `verify` with `task: proxy`, public `url`, and `sessionID`.
4. `/msg` keeps conversation history per `sessionID`, runs the agent loop with tools, returns structured `ConversationResponse`.

## LLM usage
**Agentic loop** with MCP tools via `ToolsLoop`. `ConversationResponse` for each assistant turn. Model and reasoning are set in `solution.py`.

## Notes
Used: openai/gpt-5-mini

<!-- Any additional observations, edge cases, or learnings -->
