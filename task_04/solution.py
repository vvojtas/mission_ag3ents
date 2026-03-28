"""Task 04 solution — agentic loop with MCP tools (boilerplate).

Run with: uv run python -m task_04.solution
"""

import asyncio
import logging
from pathlib import Path

from pydantic import BaseModel, Field

from common import Settings, setup_logging
from common.llm_api.http_client_provider import HttpClientProvider
from common.llm_api.llm_client import LLMClient
from common.llm_api.mcp_client import MCPClient
from common.llm_api.tools_loop import ToolsLoop
from common.logging_config import get_logger
from common.prompt_loader import PromptLoader

from .tools.file_managment import mcp as file_management_mcp
from .tools.hub_doc_download import mcp as hub_doc_mcp
from .tools.mcp_server import mcp as mcp_server_app

logger = get_logger(__name__)


class Task04Answer(BaseModel):
    """Structured final answer — replace fields for the real task."""

    summary: str = Field(description="Brief summary of what was done and the tool result.")


async def main() -> None:
    """Entry point for task 04."""
    setup_logging(level=logging.INFO, task_dir=Path(__file__).parent)
    settings = Settings()

    logger.info("Task 04 started")

    async with (
        HttpClientProvider(settings) as provider,
        MCPClient(mcp_server_app) as mcp_client,
        MCPClient(file_management_mcp) as file_mcp_client,
        MCPClient(hub_doc_mcp) as hub_doc_client,
        MCPClient(hub_client) as hub_client,
    ):
        llm_client = LLMClient(provider)
        try:
            prompt_loader = PromptLoader(Path(__file__).parent / "prompts")
            tools_loop = ToolsLoop(llm_client, mcp_clients=[mcp_client, file_mcp_client, hub_doc_client])
            await tools_loop.initialize()

            messages = prompt_loader.load_prompt(
                "agent",
                task_context="Boilerplate run: verify the MCP tool loop end-to-end.",
            )

            response = await tools_loop.run(
                model="openai/gpt-5-mini",
                input=messages,
                max_iterations=20,
                text_format=Task04Answer,
                reasoning={"effort": "low", "summary": "auto"},
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

    logger.info("Task 04 finished")


if __name__ == "__main__":
    asyncio.run(main())
