"""Task 02 solution.

Run with: uv run python -m task_02.solution
"""

import asyncio
import logging

from common import Settings, setup_logging
from common.llm_api.mcp_client import MCPClient
from common.logging_config import get_logger
from common.llm_api.llm_client import LLMClient
from common.llm_api.http_client_provider import HttpClientProvider
from common.hub_client import HubClient
from pathlib import Path
import aiofiles
import json
from pydantic import BaseModel, Field
from common.prompt_loader import PromptLoader
from common.llm_api.tools_loop import ToolsLoop
from .tools.mcp_server import mcp as mcp_server_app

logger = get_logger(__name__)

class FindHimAnswer(BaseModel):
    name: str = Field(description="The name of the person")
    surname: str = Field(description="The surname of the person")
    accessLevel: int = Field(description="The access level of the person")
    powerPlant: str = Field(description="The code of closest power plant to person's location")

async def main() -> None:
    """
    Entry point for Task 02.
    """
    setup_logging(level=logging.INFO, task_dir=Path(__file__).parent)
    settings = Settings()

    logger.info("Task 02 started")

    
    async with HttpClientProvider(settings) as provider, HubClient(settings) as hub_client, MCPClient(mcp_server_app) as mcp_client:
        llm_client = LLMClient(provider)
        try:
            prompt_loader = PromptLoader(Path(__file__).parent / "prompts")

            tools_loop = ToolsLoop(llm_client, mcp_clients=[mcp_client])
            await tools_loop.initialize()

            file_path = Path(__file__).parent / ".data" / "findhim_locations.json"
            await hub_client.download_file(f"data/{settings.hub_api_key}/findhim_locations.json", str(file_path))

            async with aiofiles.open(file_path, mode="rt", encoding="utf-8") as f:
                content = await f.read()
            locations_data = json.loads(content)

            file_path = Path(__file__).parent / ".data" / "people_transport.json"
            async with aiofiles.open(file_path, mode="rt", encoding="utf-8") as f:
                content = await f.read()
            people_data = json.loads(content)

            minimal_people_data = []
            for person in people_data:
                minimal_people_data.append({
                    "name": person["name"],
                    "surname": person["surname"],
                    "born": person["born"]
                })


            messages = prompt_loader.load_prompt(
                "find_him",
                people_json=json.dumps(minimal_people_data, ensure_ascii=False, indent=2),
                locations_json=json.dumps(locations_data, ensure_ascii=False, indent=2),
            )

            response = await tools_loop.run(
                #model="google/gemini-2.5-flash-lite",
                #model="openai/gpt-5.4-nano",
                model="openai/gpt-5-mini",
                input=messages,
                max_iterations=20,
                text_format=FindHimAnswer,
                reasoning={"effort": "low", "summary": "auto" },
                parallel_tool_calls=True,
                enable_web_search=True,
            )
            if not response or not response.output_parsed:
                logger.error("Failed to parse LLM response")
                return
            logger.info(f"Got LLM response: {response.output_parsed}")
            hub_response = await hub_client.post_answer(task_name="findhim", answer=response.output_parsed.model_dump())
            logger.info(f"Task 'findhim' submitted successfully: {hub_response}")
        finally:
            await llm_client.print_cost()
    logger.info("Task 02 finished")

if __name__ == "__main__":
    asyncio.run(main())
