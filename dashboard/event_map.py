"""Mapping between ``common.events`` types and ``dashboard.messages`` wire models.

Outbound: ``event_to_wire`` / ``serialize_event`` — convert an ``Event`` to a
  Pydantic wire model and JSON string for WebSocket delivery.

Inbound: ``parse_event`` — validate raw WebSocket JSON and return a
  ``common.events.Event`` so that dashboard formatters never import wire types.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from common import events
from dashboard.messages import (
    ConversationStart,
    DashboardMessage,
    LLMRequest,
    LLMRequestMessage,
    ParsedResponse,
    Reasoning,
    ToolCall,
    ToolResponse,
    TotalCost,
    UsageWire,
    parse_dashboard_message,
)


# ---------------------------------------------------------------------------
# Outbound: Event → wire
# ---------------------------------------------------------------------------


def event_to_wire(event: events.Event) -> DashboardMessage:
    """Convert a runtime ``Event`` to a Pydantic wire ``DashboardMessage``.

    LLM request messages are normalised from raw Responses API dicts
    (``content`` key) to the wire ``LLMRequestMessage`` (``prompt`` field).

    Args:
        event: Any ``common.events.Event`` variant.

    Returns:
        The corresponding Pydantic wire model ready for ``model_dump``.
    """
    match event:
        case events.ConversationStart():
            return ConversationStart()

        case events.LLMRequest():
            wire_messages: list[LLMRequestMessage] = []
            for m in event.messages:
                role = str(m.get("role", ""))
                content = str(m.get("content") or m.get("prompt") or "")
                wire_messages.append(LLMRequestMessage(role=role, prompt=content))
            return LLMRequest(messages=wire_messages)

        case events.ToolCall():
            return ToolCall(
                name=event.name,
                call_id=event.call_id,
                arguments=event.arguments,
                json_output=event.json_output,
            )

        case events.ToolResponse():
            return ToolResponse(
                name=event.name,
                call_id=event.call_id,
                response=event.response,
            )

        case events.Reasoning():
            return Reasoning(
                summary=list(event.summary),
                json_output=event.json_output,
            )

        case events.ParsedResponse():
            return ParsedResponse[BaseModel](
                raw_text=event.raw_text,
                output_parsed=None,
                json_output=event.json_output,
            )

        case events.TotalCost():
            return TotalCost(
                models={
                    k: UsageWire(
                        input_tokens=v.input_tokens,
                        cached_tokens=v.cached_tokens,
                        output_tokens=v.output_tokens,
                        reasoning_tokens=v.reasoning_tokens,
                        cost=v.cost,
                        upstream_inference_input_cost=v.upstream_inference_input_cost,
                        upstream_inference_output_cost=v.upstream_inference_output_cost,
                        request_count=v.request_count,
                    )
                    for k, v in event.models.items()
                }
            )


def serialize_event(event: events.Event) -> str:
    """Serialise an event to a JSON string for WebSocket delivery.

    Args:
        event: Any ``common.events.Event`` variant.

    Returns:
        JSON string representation of the wire model.
    """
    wire = event_to_wire(event)
    return json.dumps(wire.model_dump(mode="json"), ensure_ascii=False)


# ---------------------------------------------------------------------------
# Inbound: wire → Event
# ---------------------------------------------------------------------------


def wire_to_event(msg: DashboardMessage) -> events.Event:
    """Convert a validated Pydantic wire message to a ``common.events.Event``.

    Args:
        msg: A validated ``DashboardMessage`` (from ``parse_dashboard_message``).

    Returns:
        The corresponding ``common.events.Event`` variant.
    """
    match msg:
        case ConversationStart():
            return events.ConversationStart()

        case LLMRequest():
            return events.LLMRequest(
                messages=[{"role": m.role, "prompt": m.prompt} for m in msg.messages]
            )

        case ToolCall():
            return events.ToolCall(
                name=msg.name,
                call_id=msg.call_id,
                arguments=msg.arguments,
                json_output=msg.json_output,
            )

        case ToolResponse():
            return events.ToolResponse(
                name=msg.name,
                call_id=msg.call_id,
                response=msg.response,
            )

        case Reasoning():
            return events.Reasoning(
                summary=list(msg.summary),
                json_output=msg.json_output,
            )

        case ParsedResponse():
            return events.ParsedResponse(
                json_output=msg.json_output,
                raw_text=msg.raw_text,
                output_parsed=None,
            )

        case TotalCost():
            return events.TotalCost(
                models={
                    k: events.Usage(
                        input_tokens=v.input_tokens,
                        cached_tokens=v.cached_tokens,
                        output_tokens=v.output_tokens,
                        reasoning_tokens=v.reasoning_tokens,
                        cost=v.cost,
                        upstream_inference_input_cost=v.upstream_inference_input_cost,
                        upstream_inference_output_cost=v.upstream_inference_output_cost,
                        request_count=v.request_count,
                    )
                    for k, v in msg.models.items()
                }
            )


def parse_event(data: dict[str, Any]) -> events.Event:
    """Validate incoming WebSocket JSON and return a ``common.events.Event``.

    Combines Pydantic wire validation with event conversion in a single call.

    Args:
        data: Parsed JSON dict with a ``kind`` field.

    Returns:
        The validated ``common.events.Event``.

    Raises:
        ValueError: On validation failure (unknown ``kind`` or bad payload).
    """
    return wire_to_event(parse_dashboard_message(data))
