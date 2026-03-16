import json as _json
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar, Union

from openai.types.responses import ResponseInputParam
from pydantic import BaseModel

from common.llm_api.cost_tracker import CostTracker, ModelCost
from common.llm_api.http_client_provider import HttpClientProvider
from common.llm_api.model_repository import ModelRepository
from common.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass
class ParsedResponse(Generic[T]):
    """Holds the raw text and optionally the parsed Pydantic model from a Responses API call."""

    raw_text: str | None
    output_parsed: T | None


class LLMClient:
    def __init__(self, http_client_provider: HttpClientProvider):
        self.http_client_provider = http_client_provider
        self.cost_tracker = CostTracker()
        self.model_repository = ModelRepository(http_client_provider)

    async def responses(
        self,
        model: str,
        input: Union[str, ResponseInputParam],
        text_format: Optional[type[BaseModel]] = None,
        reasoning: Optional[dict] = None,
    ) -> ParsedResponse:
        """Send a request to the Responses API.

        Args:
            model: Model identifier (e.g. 'openai/gpt-4o').
            input: A plain string or a structured ResponseInputParam list.
            text_format: Optional Pydantic model class for structured output.
                         Its JSON schema is sent as ``text.format`` in the request.
            reasoning: Optional reasoning config dict (e.g. ``{"effort": "medium"}``).

        Returns:
            A ParsedResponse with ``raw_text`` always set, and ``output_parsed``
            populated when ``text_format`` is provided and parsing succeeds.
        """
        kwargs: dict = {"model": model, "input": input}

        if text_format is not None:
            kwargs["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": text_format.__name__,
                    "schema": text_format.model_json_schema(),
                    "strict": True,
                }
            }
        if reasoning is not None:
            kwargs["reasoning"] = reasoning

        logger.log_llm_request(str(kwargs))
        http_client = await self.http_client_provider.get_client()
        response = await http_client.post("/responses", json=kwargs)
        if response.status_code != 200:
            error = response.json()
            logger.error(f"LLM API Error: {error['error']['message']}")
            response.raise_for_status()

        data = response.json()
        usage = data.get("usage")
        if usage is not None:
            await self.cost_tracker.update_usage(model, usage["input_tokens"], usage["output_tokens"])

        output_items = data.get("output", [])
        message_output = next(
            (item for item in output_items if item.get("type") == "message"),
            None,
        )
        raw_text: str | None = message_output["content"][0]["text"] if message_output else None
        logger.log_llm_response(str(raw_text))

        output_parsed: BaseModel | None = None
        if text_format and raw_text:
            try:
                output_parsed = text_format.model_validate(_json.loads(raw_text))
            except Exception as exc:
                logger.error(f"Failed to parse structured response: {exc}")

        return ParsedResponse(raw_text=raw_text, output_parsed=output_parsed)


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
