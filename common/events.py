"""Runtime event types shared across the application.

These are the single source of truth for all payloads produced and consumed
within the application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, TypeAlias, TypeVar

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Event dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConversationStart:
    """Signals the start of a new conversation."""


@dataclass(frozen=True)
class LLMRequest:
    """LLM request with its raw message history.

    ``messages`` carries the Responses API message list (dicts with ``role`` and
    ``content`` keys). Downstream consumers normalise them for display.
    """

    messages: list[dict[str, Any]]


@dataclass(frozen=True)
class ToolCall:
    """A tool call returned by the LLM."""

    name: str
    call_id: str
    arguments: dict[str, Any]
    json_output: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResponse:
    """A tool execution result."""

    name: str
    call_id: str
    response: Any = None


@dataclass(frozen=True)
class Reasoning:
    """LLM reasoning step with the API summary and the raw output.

    Each summary item is ``{"type": "summary_text", "text": "..."}``.
    """

    summary: list[dict[str, str]] = field(default_factory=list)
    json_output: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedResponse(Generic[T]):
    """Parsed LLM response, optionally validated against a structured model.

    ``json_output`` carries the raw API output item — needed both for display
    and for rebuilding the Responses API conversation history in multi-turn loops.
    ``output_parsed`` holds the validated model instance when ``text_format``
    was provided to ``LLMClient.responses``.
    """

    json_output: dict[str, Any]
    raw_text: str | None = None
    output_parsed: T | None = None


@dataclass(frozen=True)
class Usage:
    """Token usage and cost snapshot for a single model (immutable)."""

    input_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cost: float = 0.0
    upstream_inference_input_cost: float = 0.0
    upstream_inference_output_cost: float = 0.0
    request_count: int = 0


@dataclass(frozen=True)
class TotalCost:
    """Aggregated cost report across all models."""

    models: dict[str, Usage]


# ---------------------------------------------------------------------------
# Union type alias and protocol
# ---------------------------------------------------------------------------

Event: TypeAlias = (
    ConversationStart
    | LLMRequest
    | ToolCall
    | ToolResponse
    | Reasoning
    | ParsedResponse
    | TotalCost
)


class EventPoster(Protocol):
    """Protocol for objects that can receive and queue runtime events.

    Consumers in ``common/`` should depend only on this protocol, keeping
    the import direction clean (``common`` must not import from ``dashboard``).
    """

    def post(self, event: Event) -> None:
        """Enqueue an event for async delivery. Returns immediately."""
        ...


class NullEventPoster:
    """No-op ``EventPoster`` for use when no event consumer is connected."""

    def post(self, event: Event) -> None:  # noqa: ARG002
        pass
