from pathlib import Path
from typing import Self

import httpx

from common import Settings
from common.logging_config import get_logger

logger = get_logger(__name__)


class HubClient:
    def __init__(self, settings: Settings):
        self.hub_api_key = settings.hub_api_key
        self._default_task_name = settings.hub_task_name

        self.base_url = settings.hub_api_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Self:
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.hub_api_key}"},
            base_url=self.base_url,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("HubClient must be used as an async context manager")
        return self._client

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

        response = await self._get_client().get(f"/{url_path.lstrip('/')}")
        response.raise_for_status()
        out_file.write_bytes(response.content)
        logger.info(f"File {out_file} downloaded successfully")

    async def post_answer(
        self,
        answer: list | dict | str,
        task_name: str | None = None,
    ) -> dict:
        """Post an answer to the hub API for a specific task.

        Args:
            answer: The answer payload.
            task_name: Hub task code. When omitted, uses ``Settings.hub_task_name``.

        Returns:
            The parsed JSON response.

        Raises:
            ValueError: If ``task_name`` is omitted and ``hub_task_name`` is empty.
            httpx.HTTPStatusError: If the API request fails.
        """
        resolved_task = task_name if task_name is not None else self._default_task_name
        if not resolved_task:
            raise ValueError(
                "task_name was not provided and hub_task_name is empty in Settings; "
                "set HUB_TASK_NAME or pass task_name explicitly.",
            )
        payload = {
            "task": resolved_task,
            "apikey": self.hub_api_key,
            "answer": answer,
        }
        response = await self._get_client().post("/verify", json=payload)
        logger.log_task_hub(f"Response from hub:\n{response.text}")
        return response.json()

    async def call_api(self, url: str, json: dict, add_api_key: bool = True) -> dict | list[dict]:
        """Send a POST request to an arbitrary hub API endpoint.

        Args:
            url: The relative path on the hub API.
            json: Optional JSON payload.
            add_api_key: Whether to add the API key to the request.
        Returns:
            The parsed JSON response.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        if add_api_key:
            json["apikey"] = self.hub_api_key
        if "{api_key}" in url:
            url = url.replace("{api_key}", self.hub_api_key)
        response = await self._get_client().post(f"/{url.lstrip('/')}", json=json)
        
        if not response.is_success:
            logger.log_task_hub(f"[ERROR] Response from hub:\n{response.text}")
            response.raise_for_status()
        return response.json()
