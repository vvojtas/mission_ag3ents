import asyncio
from typing import Any
from common.llm_api.http_client_provider import HttpClientProvider
from common.logging_config import get_logger

logger = get_logger(__name__)

class ModelRepository:
    def __init__(self, http_client_provider: HttpClientProvider) -> None:
        self.http_client_provider = http_client_provider
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
                    http_client = await self.http_client_provider.get_client()
                    response = await http_client.get("/models")
                    response.raise_for_status()
                    data = response.json()
                    models_list = data.get("data", [])
                    self.models = {m["id"]: m for m in models_list if "id" in m}
