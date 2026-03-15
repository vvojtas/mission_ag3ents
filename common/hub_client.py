import httpx
from pathlib import Path

from common import Settings
from common.logging_config import get_logger

logger = get_logger(__name__)

class HubClient:
    def __init__(self, settings: Settings):
        self.hub_api_key = settings.hub_api_key
        self.hub_api_url = settings.hub_api_url

    async def download_file(self, url_path: str, file_path: Path | str) -> None:
        """Download a file from the hub API and save it to the local filesystem.

        Args:
            url_path: The relative path on the hub API to download from.
            file_path: The local destination path to save the downloaded file.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        out_file = Path(file_path)
        if out_file.exists():
            logger.info(f"File {out_file} already exists, skipping download")
            return
        out_file.parent.mkdir(parents=True, exist_ok=True)

        headers = {
            "Authorization": f"Bearer {self.hub_api_key}",
        }

        url = f"{self.hub_api_url.rstrip('/')}/{url_path.lstrip('/')}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            out_file.write_bytes(response.content)
            logger.info(f"File {out_file} downloaded successfully")

    async def post_answer(self, task_name: str, answer: list | dict | str) -> dict:
        """Post an answer to the hub API for a specific task.

        Args:
            task_name: The name of the task to submit.
            answer: The answer payload.

        Returns:
            The parsed JSON response.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        url = f"{self.hub_api_url.rstrip('/')}/verify"
        payload = {
            "task": task_name,
            "apikey": self.hub_api_key,
            "answer": answer
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            logger.log_task_hub(f"Response from hub:\n{response.text}")
            response.raise_for_status()
            result = response.json()
            return result