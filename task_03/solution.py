"""Task 03: REST API server (FastAPI).

Run with: uv run python -m task_03.solution
"""

import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from common import setup_logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Task 03 API",
    description="REST API for task 03.",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service liveness for probes and quick checks."""
    return {"status": "ok"}


def main() -> None:
    """Start the HTTP server with Uvicorn."""
    setup_logging(level=logging.INFO, task_dir=Path(__file__).parent)
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    logger.info("Starting %s — listening on http://%s:%s", app.title, host, port)
    # FastAPI serves Swagger UI at /docs and OpenAPI JSON at /openapi.json by default.
    browse_host = "127.0.0.1" if host in ("0.0.0.0", "::", "[::]") else host
    logger.info("Swagger UI: http://%s:%s/docs  |  ReDoc: http://%s:%s/redoc", browse_host, port, browse_host, port)
    uvicorn.run(
        "task_03.solution:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
