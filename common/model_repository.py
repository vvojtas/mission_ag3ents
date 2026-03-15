import httpx
import asyncio
from typing import Any

from common.logging_config import get_logger

logger = get_logger(__name__)

class ModelRepository:
    def __init__(self, open_router_key: str, base_url: str = "https://openrouter.ai/api/v1") -> None:
        self.open_router_key = open_router_key
        self.base_url = base_url
        self.models: dict[str, dict[str, Any]] | None = None
        self._refresh_lock = asyncio.Lock()

    async def get_model(self, model_name: str) -> dict[str, Any] | None:
        """Retrieve model configuration details from OpenRouter.

        Args:
            model_name: The model ID to fetch (e.g., 'openai/gpt-4o').

        Returns:
            A dictionary of model details matching the requested ID.
        """
        await self._preload_models()
        if self.models is None:
            return None
        return self.models.get(model_name)

    async def get_models(self, model_names: set[str]) -> dict[str, dict[str, Any]]:
        """Retrieve model configuration details from OpenRouter.

        Args:
            model_names: Set of model IDs to fetch (e.g., {'openai/gpt-4o'}).

        Returns:
            A dictionary of model dictionaries matching the requested IDs.
        """
        await self._preload_models()
        if self.models is None:
            return {}
        return {model_id: self.models[model_id] for model_id in model_names if model_id in self.models}

    async def _preload_models(self) -> None:
        if self.models is None:
            async with self._refresh_lock:
                if self.models is None:
                    logger.info("Fetching models from OpenRouter...")
                    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {self.open_router_key}"}) as client:
                        response = await client.get(f"{self.base_url}/models")
                        response.raise_for_status()
                        data = response.json()
                        models_list = data.get("data", [])
                        self.models = {m["id"]: m for m in models_list if "id" in m}
