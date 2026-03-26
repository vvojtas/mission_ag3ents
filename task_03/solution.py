"""Task 03: REST API server (FastAPI).

Run with: uv run python -m task_03.solution
"""

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from common import Settings, setup_logging
from common.events import ConversationStart, EventPoster, LLMRequest, TotalCost
from common.hub_client import HubClient
from common.llm_api.cost_tracker import CostTracker
from common.llm_api.http_client_provider import HttpClientProvider
from common.llm_api.llm_client import LLMClient
from common.llm_api.mcp_client import MCPClient
from common.llm_api.tools_loop import ToolsLoop
from common.prompt_loader import PromptLoader
from dashboard.client import DashboardClient
from .tools.mcp_server import mcp as mcp_server_app


logger = logging.getLogger(__name__)


class StartRequest(BaseModel):
    """Body for POST /start — forwarded to the hub verify endpoint."""

    url: str = Field(description="Public URL of this task API.")
    sessionID: str = Field(description="Session identifier for the task run.")


class ConversationMessage(BaseModel):
    """Message in the conversation."""

    sessionID: str = Field(description="Session identifier for the conversation.")
    msg: str = Field(description="Message content.")


class ConversationResponse(BaseModel):
    """Response from the conversation."""

    msg: str = Field(description="Message content.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Open one hub HTTP client for the app process and close it on shutdown."""
    cost_tracker = CostTracker()

    async with (
        HttpClientProvider(Settings()) as provider,
        HubClient(Settings()) as hub_client,
        MCPClient(mcp_server_app) as mcp_client,
        DashboardClient(Settings().dashboard_ws_url) as event_poster,
    ):
        event_poster.post(ConversationStart())
        llm_client = LLMClient(provider, cost_tracker)
        tools_loop = ToolsLoop(llm_client, event_poster=event_poster, mcp_clients=[mcp_client])
        await tools_loop.initialize()

        app.state.hub_client = hub_client
        app.state.conversations_data = {}
        app.state.prompt_loader = PromptLoader(Path(__file__).parent / "prompts")
        app.state.tools_loop = tools_loop
        app.state.event_poster = event_poster
        yield
        cost_tracker.print_cost()
        event_poster.post(TotalCost(models=cost_tracker.snapshot()))
        while not event_poster._queue.empty():
            await asyncio.sleep(0.05)


app = FastAPI(
    title="Task 03 API",
    description="REST API for task 03.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.post("/start")
async def start(request: Request, body: StartRequest) -> dict[str, Any]:
    """Sends start request to hub API."""
    hub_client: HubClient = request.app.state.hub_client
    response = await hub_client.call_api(
        url="verify",
        json={
            "task": "proxy",
            "answer": {
                "url": body.url,
                "sessionID": body.sessionID,
            },
        },
    )
    logger.warning(f"Initialized new converstation. Start response: {response}")
    return {"status": "ok", "response": response}


@app.post("/msg")
async def msg(request: Request, body: ConversationMessage) -> ConversationResponse:
    logger.info(f"Received message: {body}")
    session_id = body.sessionID
    user_msg = body.msg
    conversations_data = request.app.state.conversations_data
    event_poster: EventPoster = request.app.state.event_poster

    if session_id not in conversations_data:
        prompt_loader = request.app.state.prompt_loader
        messages = prompt_loader.load_prompt("packages")
        conversations_data[session_id] = messages
        event_poster.post(ConversationStart())
        event_poster.post(LLMRequest(messages=messages))

    new_message = {"role": "user", "content": user_msg}
    history = conversations_data[session_id]
    history.append(new_message)
    event_poster.post(LLMRequest(messages=[new_message]))

    tools_loop: ToolsLoop = request.app.state.tools_loop
    llm_response = await tools_loop.run(
        #model="openai/gpt-5-mini",
        #model="mistralai/mistral-nemo",
        model="anthropic/claude-haiku-4.5",
        reasoning={"effort": "low", "summary": "auto" },
        input=history,
        max_iterations=5,
        text_format=ConversationResponse,
    )

    history.append({"role": "assistant", "content": llm_response.raw_text})
    conversations_data[session_id] = history

    logger.info(f"Responding with: {llm_response.raw_text}")
    return ConversationResponse(msg=llm_response.raw_text or "")


def main() -> None:
    """Start the HTTP server with Uvicorn."""
    setup_logging(level=logging.INFO, task_dir=Path(__file__).parent)
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    logger.info("Starting %s — listening on http://%s:%s", app.title, host, port)
    browse_host = "127.0.0.1" if host in ("0.0.0.0", "::", "[::]") else host
    logger.info("Swagger UI: http://%s:%s/docs  |  ReDoc: http://%s:%s/redoc", browse_host, port, browse_host, port)
    uvicorn.run(
        "task_03.solution:app",
        host=host,
        port=port,
        reload=True,
        ws="websockets-sansio",
    )


if __name__ == "__main__":
    main()
