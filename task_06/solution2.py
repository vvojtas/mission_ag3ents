"""Task 06 solution 2 — programmatic (no LLM) execution.

Calls MCP tools directly in a fixed sequence instead of using an LLM tools loop.

Run with: uv run python -m task_06.solution2
"""

import asyncio
import csv
import logging
import string
from pathlib import Path

from common import Settings, setup_logging
from common.llm_api.mcp_client import MCPClient
from common.logging_config import get_logger
from common.settings import MCPWorkspaceSettings

from .tools.hub_categorize import mcp as hub_categorize_mcp
from .tools.hub_doc_download import mcp as hub_doc_download_mcp

logger = get_logger(__name__)

SEND_ORDER = "JDIBACGEHF"


async def main() -> None:
    """Entry point for task 06 solution 2."""
    setup_logging(level=logging.INFO, task_dir=Path(__file__).parent)
    logger.info("Task 06 solution 2 started")

    workspace_dir = MCPWorkspaceSettings().workspace_root.resolve()

    async with (
        MCPClient(hub_categorize_mcp) as categorize_client,
        MCPClient(hub_doc_download_mcp) as download_client,
    ):
        # 1) Download categorize.csv with force
        logger.info("Step 1: Downloading categorize.csv (force=true)")
        dl_result = await download_client.call_mcp_tool(
            "hub_download_doc",
            {"file_names": ["categorize.csv"], "force": True},
        )
        logger.info("Download result: %s", dl_result)

        # 2) Reset hub
        logger.info("Step 2: Resetting hub")
        reset_result = await categorize_client.call_mcp_tool("categorize_reset", {})
        logger.info("Reset result: %s", reset_result)

        # 3) Read categorize.csv
        csv_path = workspace_dir / "categorize.csv"
        logger.info("Step 3: Reading %s", csv_path)
        with csv_path.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        logger.info("Loaded %d rows", len(rows))

        # 4) Assign each row a letter A–J in order of appearance
        letters = string.ascii_uppercase[:len(rows)]
        lettered: dict[str, dict[str, str]] = {}
        for letter, row in zip(letters, rows):
            lettered[letter] = row
            logger.info("  %s → %s: %s", letter, row["code"], row["description"][:60])

        # 5) Read prompt template from .workspace/prompt.txt
        prompt_path = workspace_dir / "prompt.txt"
        prompt_template = prompt_path.read_text(encoding="utf-8")
        logger.info("Prompt template:\n%s", prompt_template.strip())

        # 6–7) Build & send prompts in order J-D-I-B-A-C-G-E-H-F
        for letter in SEND_ORDER:
            row = lettered[letter]
            prompt = prompt_template.format(
                id=row["code"],
                description=row["description"],
            )
            logger.info("Sending [%s] %s — prompt: %s", letter, row["code"], prompt.strip())
            result = await categorize_client.call_mcp_tool(
                "categorize_send_prompt",
                {"prompt": prompt},
            )
            success = result.get("success", False) if isinstance(result, dict) else False
            message = result.get("message", "") if isinstance(result, dict) else result
            logger.info("  → success=%s  message=%s", success, message)

            if not success:
                logger.error("Hub rejected prompt for %s (%s). Aborting.", letter, row["code"])
                return

    logger.info("Task 06 solution 2 finished")


if __name__ == "__main__":
    asyncio.run(main())
