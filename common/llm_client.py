from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from typing import Optional, Union
from openai.types.responses import ResponseInputParam
from common.cost_tracker import CostTracker, ModelCost
from openai.lib._parsing._responses import TextFormatT
from common.model_repository import ModelRepository
from common import Settings
from common.logging_config import get_logger

logger = get_logger(__name__)

class LLMClient:
    def __init__(self, settings: Settings, base_url: str = "https://openrouter.ai/api/v1"):
        self.client = AsyncOpenAI(api_key=settings.openrouter_api_key, base_url=base_url)
        self.cost_tracker = CostTracker()
        self.model_repository = ModelRepository(settings.openrouter_api_key, base_url)

    async def responses(
        self, 
        model: str,
        input: Union[str, ResponseInputParam],
        text_format: Optional[TextFormatT] = None,
        reasoning: Optional[dict] = None,
    ):
        kwargs = {
            "model": model,
            "input": input,
        }
            
        if text_format is not None:
            kwargs["text_format"] = text_format
        if reasoning is not None:
            kwargs["reasoning"] = reasoning

        logger.log_llm_request(str(input))
        response = await self.client.responses.parse(**kwargs)
        if response.usage is not None:
            await self.cost_tracker.update_usage(model, response.usage.input_tokens, response.usage.output_tokens)
        
        logger.log_llm_response(str(response.output_text))
        return response
    

    async def print_cost(self):
        """Print the current token usage for all models in a grid format."""
        
        async def fetch_prices(model_names: set[str]) -> dict[str, ModelCost]:
            models = await self.model_repository.get_models(model_names)
            return {
                model_id: ModelCost(
                    model_name=model_id,
                    input_tokens_cost=float(model.get("pricing", {}).get("prompt", 0)),
                    output_tokens_cost=float(model.get("pricing", {}).get("completion", 0))
                )
                for model_id, model in models.items() if model_id in model_names
            }

        await self.cost_tracker.print_cost(fetch_prices)