"""Task 05 solution — agentic loop with MCP tools (stub).

Run with: uv run python -m task_05.solution
"""

import asyncio
from datetime import datetime
import logging
from pathlib import Path

from pydantic import BaseModel, Field

from common import Settings, setup_logging
from common.events import ConversationStart, TotalCost
from common.llm_api.cost_tracker import CostTracker
from common.llm_api.http_client_provider import HttpClientProvider
from common.llm_api.llm_client import LLMClient
from common.llm_api.mcp_client import MCPClient
from common.llm_api.tools_loop import ToolsLoop
from common.logging_config import get_logger
from common.prompt_loader import PromptLoader
from dashboard.client import DashboardClient
from mcp_servers.hub_answer import mcp as hub_answer_mcp

from .tools.hub_call import mcp as hub_call_mcp

logger = get_logger(__name__)


class Task05Answer(BaseModel):
    flag: str = Field(description="The flag of the task. Format: {FLG:...} when known.")
    response: str = Field(description="Summary or hub response text.")


async def main() -> None:
    """Entry point for task 05."""
    setup_logging(level=logging.INFO, task_dir=Path(__file__).parent)
    settings = Settings()

    logger.info("Task 05 started")

    prompt_loading_path = Path(__file__).parent / "prompts"
    cost_tracker = CostTracker()
    async with (
        HttpClientProvider(settings) as provider,
        MCPClient(hub_answer_mcp) as hub_answer_client,
        MCPClient(hub_call_mcp) as hub_call_client,
        DashboardClient(settings.dashboard_ws_url) as event_poster,
    ):
        llm_client = LLMClient(provider, cost_tracker)
        try:
            event_poster.post(ConversationStart())
            prompt_loader = PromptLoader(prompt_loading_path)
            tools_loop = ToolsLoop(
                llm_client,
                event_poster=event_poster,
                mcp_clients=[hub_call_client],
            )
            await tools_loop.initialize()

            messages = prompt_loader.load_prompt(
                "railway"
            )

            response = await tools_loop.run(
                #model="google/gemini-3-flash-preview",
                model="gpt-5-nano",
                input=messages,
                max_iterations=25,
                text_format=Task05Answer,
                reasoning={"effort": "medium", "summary": "auto"},
                parallel_tool_calls=True,
                enable_web_search=False,
            )
            if not response or not response.output_parsed:
                logger.error("Failed to parse LLM response")
                return
            logger.info("Parsed response: %s", response.output_parsed)
        finally:
            llm_client.print_cost()
            event_poster.post(TotalCost(models=cost_tracker.snapshot()))
    logger.info("Task 05 finished")


if __name__ == "__main__":
    asyncio.run(main())
