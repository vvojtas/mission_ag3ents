"""Task 04 solution — agentic loop with MCP tools (boilerplate).

Run with: uv run python -m task_04.solution
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
from .tools.image_inspector.server import create_image_inspector_mcp

from .tools.file_managment import mcp as file_management_mcp
from .tools.hub_doc_download import mcp as hub_doc_mcp
from mcp_servers.hub_answer import mcp as hub_answer_mcp

logger = get_logger(__name__)


class Task04Answer(BaseModel):
    flag: str = Field(description="The flag of the task. Format: {FLG:BUSTED}")
    response: str = Field(description="The response of the task.")


async def main() -> None:
    """Entry point for task 04."""
    setup_logging(level=logging.INFO, task_dir=Path(__file__).parent)
    settings = Settings()

    logger.info("Task 04 started")

    prompt_loading_path = Path(__file__).parent / "prompts"
    cost_tracker = CostTracker()
    async with (
        HttpClientProvider(settings) as provider,
        MCPClient(file_management_mcp) as file_mcp_client,
        MCPClient(hub_doc_mcp) as hub_doc_client,
        MCPClient(hub_answer_mcp) as hub_answer_client,
        MCPClient(create_image_inspector_mcp(cost_tracker=cost_tracker)) as image_inspector_client,
        DashboardClient(settings.dashboard_ws_url) as event_poster,
    ):
        llm_client = LLMClient(provider, cost_tracker)
        try:
            event_poster.post(ConversationStart())
            prompt_loader = PromptLoader(prompt_loading_path)
            tools_loop = ToolsLoop(llm_client, event_poster=event_poster, mcp_clients=[file_mcp_client, hub_doc_client, hub_answer_client, image_inspector_client])
            await tools_loop.initialize()

            messages = prompt_loader.load_prompt(
                "declaration",
                date=datetime.now().strftime("%Y-%m-%d"),
            )

            response = await tools_loop.run(
                #model="openai/gpt-5-mini",
                model="google/gemini-3-flash-preview",
                input=messages,
                max_iterations=30,
                text_format=Task04Answer,
                reasoning={"effort": "medium", "summary": "auto"},
                parallel_tool_calls=True,
                enable_web_search=False,
            )
            if not response or not response.output_parsed:
                logger.error("Failed to parse LLM response")
                return
            logger.info("Parsed response: %s", response.output_parsed)
            # Add HubClient(settings) to this async with and post_answer when the task is defined.
        finally:
            llm_client.print_cost()
            event_poster.post(TotalCost(models=cost_tracker.snapshot()))
    logger.info("Task 04 finished")


if __name__ == "__main__":
    asyncio.run(main())
