"""WebSocket console dashboard: colored logging of LLM-style events.

Run with:
  uv run uvicorn dashboard.console.app:app --reload --host 127.0.0.1 --port 8765

WebSocket URL: ws://127.0.0.1:8765/dashboard/ws
"""

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from common import setup_logging
from common.logging_config import get_logger
from dashboard.console.formatters import get_dashboard_logger, log_dashboard_message
from dashboard.event_map import parse_event


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Configure colored logging once at startup."""
    setup_logging(level=logging.INFO)
    yield


app = FastAPI(
    title="Dashboard console",
    description="WebSocket endpoint that logs structured LLM events to the console.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.websocket("/dashboard/ws")
async def dashboard_websocket(websocket: WebSocket) -> None:
    """Accept JSON event messages with a ``kind`` field; format and log to the console."""
    await websocket.accept()
    log = get_dashboard_logger()
    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                log.error("Invalid JSON: %s", exc)
                continue
            if not isinstance(data, dict):
                log.error("WebSocket message must be a JSON object")
                continue
            try:
                event = parse_event(data)
            except ValueError as exc:
                log.error("Invalid message: %s", exc)
                continue
            log_dashboard_message(log, event)
    except WebSocketDisconnect:
        get_logger(__name__).debug("WebSocket client disconnected")
