# Task 03

## Objective

Run a local REST API server for this task using **FastAPI**.

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

<!-- Describe the API design and how it fits the competition task when known -->

## Notes

<!-- Edge cases, deployment, or learnings -->
