"""Playground — scratch area for testing common/ components and OpenRouter responses.

Run with: uv run python -m playground.solution
"""

import asyncio
import logging
from pathlib import Path

from pydantic import BaseModel, Field

from common import Settings, setup_logging
from common.logging_config import get_logger
from common.llm_api.llm_client import LLMClient
from common.llm_api.http_client_provider import HttpClientProvider
from common.llm_api.tools_loop import ToolsLoop
from common.prompt_loader import PromptLoader
from playground.tools.echo import EchoTool

logger = get_logger(__name__)


class GreetingResponse(BaseModel):
    greeting: str = Field(description="The most common greeting used in Poznań")
    origin: str = Field(description="Brief explanation of the greeting's origin")


async def main() -> None:
    """Entry point for the playground."""
    setup_logging(level=logging.INFO, task_dir=Path(__file__).parent)
    settings = Settings()

    logger.info("Playground started")

    async with HttpClientProvider(settings) as provider:
        llm_client = LLMClient(provider)
        try:
            prompt_loader = PromptLoader(Path(__file__).parent / "prompts")
            echo_tool = EchoTool()
            tools_loop = ToolsLoop(llm_client, [echo_tool])

            messages = prompt_loader.load_prompt("hello")

            response = await tools_loop.run(
                model="google/gemini-2.5-flash-lite",
                reasoning={"effort": "low", "summary": "auto"},
                input=messages,
                tools=[echo_tool],
                max_iterations=10,
                text_format=GreetingResponse,
                enable_web_search=False,
            )

            logger.info("Final response: %s", response.raw_text)
            if response.output_parsed:
                parsed = response.output_parsed
                logger.info("Greeting: %s", parsed.greeting)
                logger.info("Origin: %s", parsed.origin)
        finally:
            await llm_client.print_cost()

    logger.info("Playground finished")


if __name__ == "__main__":
    asyncio.run(main())
