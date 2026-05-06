"""Task 07 solution — agentic loop with MCP tools.

Run with: uv run python -m task_07.solution
"""

import asyncio
import logging
from datetime import datetime
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
from common.settings import MCPWorkspaceSettings
from dashboard.client import DashboardClient

from .tools.enhance_image.server import create_enhance_image_mcp
from .tools.hub_action.server import create_hub_action_mcp
from .tools.hub_downloader.server import create_hub_downloader_mcp
from .tools.image_inspector.server import create_image_inspector_mcp

logger = get_logger(__name__)


class Task07Answer(BaseModel):
    flag: str = Field(description="The task flag if returned by the hub, else empty or unknown.")
    response: str = Field(description="Summary of what was done and the hub response if any.")


async def main() -> None:
    """Entry point for task 07."""
    setup_logging(level=logging.INFO, task_dir=Path(__file__).parent)
    settings = Settings()

    logger.info("Task 07 started")

    prompt_loading_path = Path(__file__).parent / "prompts"
    workspace_root = MCPWorkspaceSettings().workspace_root.resolve()
    cost_tracker = CostTracker()

    hub_downloader_mcp = create_hub_downloader_mcp(settings, workspace_root)
    enhance_image_mcp = create_enhance_image_mcp(workspace_root)
    image_inspector_mcp = create_image_inspector_mcp(
        settings,
        workspace_root,
        prompt_loading_path=prompt_loading_path,
        cost_tracker=cost_tracker,
    )
    hub_action_mcp = create_hub_action_mcp(settings)

    async with (
        HttpClientProvider(settings) as provider,
        MCPClient(hub_downloader_mcp) as hub_downloader_client,
        MCPClient(enhance_image_mcp) as enhance_image_client,
        MCPClient(image_inspector_mcp) as image_inspector_client,
        MCPClient(hub_action_mcp) as hub_action_client,
        DashboardClient(settings.dashboard_ws_url) as event_poster,
    ):
        llm_client = LLMClient(provider, cost_tracker)
        try:
            event_poster.post(ConversationStart())
            prompt_loader = PromptLoader(prompt_loading_path)
            tools_loop = ToolsLoop(
                llm_client,
                event_poster=event_poster,
                mcp_clients=[
                    hub_downloader_client,
                    enhance_image_client,
                    image_inspector_client,
                    hub_action_client,
                ],
            )
            await tools_loop.initialize()

            messages = prompt_loader.load_prompt(
                "electricity",
                date=datetime.now().strftime("%Y-%m-%d"),
                task_code="TBD",
            )

            response = await tools_loop.run(
                #model="anthropic/claude-sonnet-4.5",
                #model="google/gemini-3-flash-preview",
                #model="anthropic/claude-haiku-4.5",
                model="openai/gpt-5.4-mini",
                input=messages,
                max_iterations=30,
                text_format=Task07Answer,
                reasoning={"effort": "medium", "summary": "auto", "enabled": True},
                parallel_tool_calls=False,
                enable_web_search=False,
            )
            if not response or not response.output_parsed:
                logger.error("Failed to parse LLM response")
                return
            logger.info("Parsed response: %s", response.output_parsed)
        finally:
            llm_client.print_cost()
            event_poster.post(TotalCost(models=cost_tracker.snapshot()))
    logger.info("Task 07 finished")


if __name__ == "__main__":
    asyncio.run(main())
