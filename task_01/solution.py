"""Task 01 solution.

Run with: uv run python -m task_01.solution
"""

import asyncio
import logging

from common import Settings, setup_logging
from common.logging_config import get_logger

logger = get_logger(__name__)


async def main() -> None:
    """Entry point for Task 01.

    Loads settings, sets up logging, and executes the task solution.
    """
    setup_logging(level=logging.DEBUG)
    settings = Settings()

    logger.info("Task 01 started")
    logger.info("Using model: %s", settings.default_model)

    # TODO: Implement task solution here

    logger.info("Task 01 finished")


if __name__ == "__main__":
    asyncio.run(main())
