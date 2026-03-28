import json as _json
from typing import Optional, Union, Any

from openai.types.responses import ResponseInputParam
from pydantic import BaseModel

from common.events import ParsedResponse, Reasoning, ToolCall
from common.llm_api.cost_tracker import CostTracker
from common.llm_api.http_client_provider import HttpClientProvider
from common.llm_api.model_repository import ModelRepository
from common.logging_config import format_for_logging, get_logger
from common.llm_api.mcp_client import MCPClient

logger = get_logger(__name__)


class LLMClient:
    def __init__(self, http_client_provider: HttpClientProvider, cost_tracker: CostTracker | None = None):
        self.http_client_provider = http_client_provider
        self.cost_tracker = cost_tracker or CostTracker()
        self.model_repository = ModelRepository(http_client_provider)

    def fix_schema(self, schema):
        schema = self._inline_refs(schema, schema.get("$defs", {}))
        schema.pop("$defs", None)
        schema.pop("title", None)
        return schema

    def _inline_refs(self, node: Any, defs: dict) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                ref_name = node["$ref"].split("/")[-1]
                return self._inline_refs(defs[ref_name], defs)
            return {k: self._inline_refs(v, defs) for k, v in node.items()}
        if isinstance(node, list):
            return [self._inline_refs(item, defs) for item in node]
        return node

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
            enable_web_search: Optional flag to enable web search.

        Returns:
            A list of ``ParsedResponse``, ``ToolCall``, and ``Reasoning`` events.
            ``ParsedResponse.raw_text`` is always set; ``output_parsed`` is populated
            when ``text_format`` is provided and parsing succeeds.
        """
        kwargs["model"] = model
        kwargs["input"] = input

        if text_format is not None:
            kwargs["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": text_format.__name__,
                    "schema": MCPClient._make_strict_schema(self.fix_schema(text_format.model_json_schema())),
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

        response_messages: list[ParsedResponse | ToolCall | Reasoning] = []
        for item in output_items:
            if item.get("type") == "message":
                raw_text: str | None = item["content"][0]["text"] if item else None

                output_parsed: BaseModel | None = None
                if text_format and raw_text:
                    try:
                        output_parsed = text_format.model_validate(_json.loads(raw_text))
                    except Exception as exc:
                        logger.error(f"Failed to parse structured response: {exc}")

                response_messages.append(ParsedResponse(
                    json_output=item,
                    raw_text=raw_text,
                    output_parsed=output_parsed,
                ))

            elif item.get("type") == "function_call":
                response_messages.append(ToolCall(
                    name=item["name"],
                    call_id=item["call_id"],
                    arguments=_json.loads(item["arguments"]) if isinstance(item["arguments"], str) else item["arguments"],
                    json_output=item,
                ))
            elif item.get("type") == "reasoning":
                response_messages.append(Reasoning(
                    summary=item.get("summary") or [],
                    json_output=item,
                ))
            else:
                logger.error(f"Unknown item type: {item.get('type')}")

        return response_messages

    def print_cost(self) -> None:
        """Print the current token usage for all models in a grid format."""
        self.cost_tracker.print_cost()
