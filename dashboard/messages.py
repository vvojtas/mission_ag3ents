"""Pydantic wire models for the dashboard WebSocket protocol.

These models are INTERNAL to the ``dashboard`` package.

The discriminated union ``DashboardMessage`` is used for both outbound
serialisation (``DashboardClient``) and inbound validation (console app).
"""

from __future__ import annotations

from typing import Annotated, Any, Generic, Literal, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

T = TypeVar("T", bound=BaseModel)


class UsageWire(BaseModel):
    """Serialisable snapshot of token usage and cost for a single model."""

    model_config = ConfigDict(extra="ignore")

    input_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cost: float = 0.0
    upstream_inference_input_cost: float = 0.0
    upstream_inference_output_cost: float = 0.0
    request_count: int = 0


class ParsedResponse(BaseModel, Generic[T]):
    """Wire model for ``kind=parsed_response``."""

    model_config = ConfigDict(extra="ignore")

    kind: Literal["parsed_response"] = "parsed_response"
    raw_text: str | None = None
    output_parsed: T | None = None
    json_output: dict[str, Any]


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: Literal["tool_call"] = "tool_call"
    name: str
    call_id: str
    arguments: dict[str, Any]
    json_output: dict[str, Any] = Field(default_factory=dict)


class Reasoning(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: Literal["reasoning"] = "reasoning"
    summary: list[dict[str, str]] = Field(default_factory=list)
    json_output: dict[str, Any] = Field(default_factory=dict)


class ToolResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: Literal["tool_response"] = "tool_response"
    name: str
    call_id: str
    response: Any = None


class LLMRequestMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    role: str
    prompt: str = ""


class LLMRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: Literal["llm_request"] = "llm_request"
    messages: list[LLMRequestMessage]


class TotalCost(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: Literal["total_cost"] = "total_cost"
    models: dict[str, UsageWire]


class ConversationStart(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: Literal["conversation_start"] = "conversation_start"


DashboardMessage = (
    ParsedResponse[BaseModel]
    | ToolCall
    | Reasoning
    | ToolResponse
    | LLMRequest
    | TotalCost
    | ConversationStart
)

_DashboardWire = Annotated[
    Union[
        ParsedResponse[BaseModel],
        ToolCall,
        Reasoning,
        ToolResponse,
        LLMRequest,
        TotalCost,
        ConversationStart,
    ],
    Field(discriminator="kind"),
]

_dashboard_adapter = TypeAdapter(_DashboardWire)


def parse_dashboard_message(data: dict[str, Any]) -> DashboardMessage:
    """Validate a WebSocket JSON object into a dashboard wire message.

    Args:
        data: Parsed JSON object with a ``kind`` field.

    Returns:
        The validated Pydantic model instance.

    Raises:
        ValueError: On validation failure (including unknown ``kind``).
    """
    try:
        return _dashboard_adapter.validate_python(data)
    except ValidationError as exc:
        raise ValueError(exc.errors(include_url=False)) from exc
