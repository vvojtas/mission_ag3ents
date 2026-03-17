from typing import Callable, Any, Generic, TypeVar, Awaitable
from abc import ABC, abstractmethod

from pydantic import BaseModel

from common.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

class Tool(ABC, Generic[T]):
    def __init__(self, name: str, description: str, func:  Callable[..., Awaitable[Any]]) -> None:
        self.name = name
        self.description = description
        self.func = func

    @abstractmethod
    def get_model(self) -> type[T]:
        """Return the Pydantic model class that defines this tool's input schema."""
        ...

    async def run(self, model: T) -> Any:
        """Execute the tool with a validated input model.

        Args:
            model: A validated instance of the model returned by `get_model()`.

        Returns:
            The result of the underlying function call.
        """
        logger.log_tool_call(f"Running tool {self.name} with parameters: {model.model_dump()}")
        result = await self.func(**{field: getattr(model, field) for field in model.model_fields})
        logger.log_tool_call(f"Tool {self.name} returned: {result}")
        return result

    def _get_parameters(self) -> dict:
        schema = self.get_model().model_json_schema()
        schema = self._inline_refs(schema, schema.get("$defs", {}))
        schema.pop("$defs", None)
        schema.pop("title", None)
        schema["additionalProperties"] = False
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

    
    def to_dict(self) -> dict:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters(),
            "strict": True,
        }

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.func(*args, **kwds)