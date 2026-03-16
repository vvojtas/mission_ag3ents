"""Task 02 solution.

Run with: uv run python -m task_02.solution
"""

import asyncio
import logging

from common import Settings, setup_logging
from common.logging_config import get_logger
from common.llm_api.llm_client import LLMClient
from common.llm_api.http_client_provider import HttpClientProvider
from common.hub_client import HubClient


logger = get_logger(__name__)


async def main() -> None:
    """Entry point for Task 02.

    Loads settings, sets up logging, and executes the task solution.
    """
    setup_logging(level=logging.INFO)
    settings = Settings()
    hub_client = HubClient(settings)

    logger.info("Task 02 started")

    async with HttpClientProvider(settings) as provider:
        llm_client = LLMClient(provider)

        # TODO: Implement solution here

        await llm_client.print_cost()

    logger.info("Task 02 finished")


if __name__ == "__main__":
    asyncio.run(main())
