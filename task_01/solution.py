"""Task 01 solution.

Run with: uv run python -m task_01.solution
"""

import asyncio
import csv
import io
import logging

from common import Settings, setup_logging
from common.logging_config import get_logger
from common.llm_api.llm_client import LLMClient, ParsedResponse
from common.llm_api.http_client_provider import HttpClientProvider
from common.hub_client import HubClient
from common.prompt_loader import PromptLoader
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal
import json
import aiofiles

logger = get_logger(__name__)

IndustryType = Literal["IT", "transport", "edukacja", "medycyna", "praca z ludźmi", "praca z pojazdami", "praca fizyczna", "inne"]

class PersonClasified(BaseModel):
    name: str = Field(description="The full name of the person")
    #reasoning: str = Field(description="One sentence reasoning for each selected industry. Qoute 2-3 words from the job description as evidence per tag.")
    industries: list[IndustryType] = Field(description="List of polish named industries the person is clasified to work in. Use inne if the person does not fit into any of the other categories.")
class PersonClasifiedList(BaseModel):
    persons: list[PersonClasified] = Field(description="List of person clasifications")


async def main() -> None:
    """
    Entry point for Task 01.
    """
    setup_logging(level=logging.DEBUG, task_dir=Path(__file__).parent)
    settings = Settings()
    prompt_loader = PromptLoader(Path(__file__).parent / "prompts")

    logger.info("Task 01 started")

    async with HubClient(settings) as hub_client, HttpClientProvider(settings) as provider:
        llm_client = LLMClient(provider)

        file_path = Path(__file__).parent / ".data" / "people.csv"
        await hub_client.download_file(f"data/{settings.hub_api_key}/people.csv", str(file_path))

        async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
            content = await f.read()
        people_data = list(csv.DictReader(io.StringIO(content)))

        logger.info(f"Loaded {len(people_data)} records from CSV. First record: {people_data[0] if people_data else None}")

        filtered_people = [
            person for person in people_data
            if person["gender"] == "M"
            and person["birthPlace"] == "Grudziądz"
            and 20 <= (2026 - int(person["birthDate"][:4])) <= 40
        ]
        logger.info(f"Filtered {len(filtered_people)} records. First record: {filtered_people[0] if filtered_people else None}")

        transformed_people = [
            {
                "full_name": f"{person['name']} {person['surname']}",
                "job_description": person["job"],
            }
            for person in filtered_people
        ]

        people_json = json.dumps(transformed_people, ensure_ascii=False, indent=2)

        messages = prompt_loader.load_prompt(
            "clasify_industries",
            industries=IndustryType.__args__,
            people_json=people_json
        )

        responses = await llm_client.responses(
            #model="mistralai/mistral-nemo",
            model="google/gemini-2.5-flash-lite",
            input=messages,
            text_format=PersonClasifiedList,
            reasoning={"effort": "medium"},
        )
        parsed = next((r for r in responses if isinstance(r, ParsedResponse)), None)

        if not parsed or not parsed.output_parsed:
            logger.error("Failed to parse LLM response")
            return

        final_answer = []
        for person, classified in zip(filtered_people, parsed.output_parsed.persons):
            if classified.name != f"{person['name']} {person['surname']}":
                logger.error(f"Full name mismatch: {classified.name} != {person['name']} {person['surname']}")
                continue
            if "transport" in classified.industries:
                final_answer.append({
                    "name": person["name"],
                    "surname": person["surname"],
                    "gender": person["gender"],
                    "born": int(person["birthDate"][:4]),
                    "city": person["birthPlace"],
                    "tags": classified.industries
                })

        logger.info(f"Found {len(final_answer)} people in transport. Submitting answer...")

        hub_response = await hub_client.post_answer(task_name="people", answer=final_answer)
        logger.info(f"Task 'people' submitted successfully: {hub_response}")

        dump_path = Path(__file__).parent.parent / "task_02" / ".data" / "people_transport.json"
        if dump_path.exists():
            logger.info(f"Answer already saved to {dump_path}")
        else:
            dump_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(dump_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(final_answer, ensure_ascii=False, indent=2))
            logger.info(f"Answer saved to {dump_path}")

        await llm_client.print_cost()

    logger.info("Task 01 finished")

if __name__ == "__main__":
    asyncio.run(main())
