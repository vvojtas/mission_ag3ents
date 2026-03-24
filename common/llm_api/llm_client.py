import json as _json
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar, Union, Any

from openai.types.responses import ResponseInputParam
from pydantic import BaseModel

from common.llm_api.cost_tracker import CostTracker
from common.llm_api.http_client_provider import HttpClientProvider
from common.llm_api.model_repository import ModelRepository
from common.logging_config import format_for_logging, get_logger


logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass
class ParsedResponse(Generic[T]):
    raw_text: str | None
    output_parsed: T | None
    json_output: dict[str, Any]

@dataclass
class ToolCall:
    name: str
    call_id: str
    arguments: dict[str, Any]
    json_output: dict

@dataclass
class Reasoning:
    summary: list[str]
    json_output: dict[str, Any]

class LLMClient:
    def __init__(self, http_client_provider: HttpClientProvider, cost_tracker: CostTracker | None = None):
        self.http_client_provider = http_client_provider
        self.cost_tracker = cost_tracker or CostTracker()
        self.model_repository = ModelRepository(http_client_provider)

    async def responses(
        self,
        model: str,
        input: Union[str, ResponseInputParam],
        text_format: Optional[type[BaseModel]] = None,
        enable_web_search: Optional[bool] = False,
        **kwargs: Any,
    ) -> list[ParsedResponse | ToolCall | Reasoning]:
        """Send a request to the Responses API.

        Args:
            model: Model identifier (e.g. 'openai/gpt-4o').
            input: A plain string or a structured ResponseInputParam list.
            text_format: Optional Pydantic model class for structured output.
                         Its JSON schema is sent as ``text.format`` in the request.
            reasoning: Optional reasoning config dict (e.g. ``{"effort": "medium"}``).
            tools: Optional list of tools to use.
            enable_web_search: Optional flag to enable web search.
        Returns:
            A ParsedResponse with ``raw_text`` always set, and ``output_parsed``
            populated when ``text_format`` is provided and parsing succeeds.
        """
        kwargs["model"] = model
        kwargs["input"] = input

        if text_format is not None:
            kwargs["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": text_format.__name__,
                    "schema": text_format.model_json_schema(),
                    "strict": True,
                }
            }
        
        if enable_web_search:
            kwargs["plugins"] = [{"id": "web"}]

        logger.log_llm_request(format_for_logging(kwargs, "LLM Request"))
        http_client = await self.http_client_provider.get_client()
        response = await http_client.post("/responses", json=kwargs)
        if response.status_code != 200:
            error = response.json()
            logger.error(f"LLM API Error: {error}")
            response.raise_for_status()

        data = response.json()
        usage = data.get("usage")
        if usage is not None:
            logger.log_cost(format_for_logging(usage, "Token Usage"))
            await self.cost_tracker.update_usage(model, usage)

        output_items = data.get("output", [])
        logger.log_llm_response(format_for_logging(data, "LLM Response"))

        response_messages = []
        for item in output_items:
            if item.get("type") == "message":
                raw_text: str | None = item["content"][0]["text"] if item else None

                output_parsed: BaseModel | None = None
                if text_format and raw_text:
                    try:
                        output_parsed = text_format.model_validate(_json.loads(raw_text))
                    except Exception as exc:
                        logger.error(f"Failed to parse structured response: {exc}")

                parsed_response = ParsedResponse[BaseModel](
                    raw_text=raw_text, 
                    output_parsed=output_parsed, 
                    json_output=item,
                )

                response_messages.append(parsed_response)

            elif item.get("type") == "function_call":
                tool_call = ToolCall(
                    name=item["name"],
                    call_id=item["call_id"],
                    arguments= _json.loads(item["arguments"]) if isinstance(item["arguments"], str) else item["arguments"],
                    json_output=item,
                )
                response_messages.append(tool_call)
            elif item.get("type") == "reasoning":
                reasoning_response = Reasoning(
                    summary=item["summary"],
                    json_output=item,
                )
                response_messages.append(reasoning_response)
            else:
                logger.error(f"Unknown item type: {item.get('type')}")


        return response_messages


    async def print_cost(self):
        """Print the current token usage for all models in a grid format."""
        await self.cost_tracker.print_cost()
