from typing import Callable, Any, Generic, TypeVar, Awaitable
from abc import ABC, abstractmethod

from pydantic import BaseModel

from common.llm_api.schema_utils import clean_schema
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
        return clean_schema(self.get_model().model_json_schema())

    
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