"""Format dashboard events and write them with the colored logger."""

import json
import sys
from typing import assert_never

from common.cost_report import log_cost_report
from common.events import (
    ConversationStart,
    Event,
    LLMRequest,
    ParsedResponse,
    Reasoning,
    ToolCall,
    ToolResponse,
    TotalCost,
)
from common.logging_config import CustomLogger, format_for_logging, get_logger

# Trimming for reasoning fallback, tool response, and similar.
_DASHBOARD_TRIM = 1000


def clear_console(log: CustomLogger) -> None:
    """Clear the terminal screen and scrollback buffer via ANSI codes."""
    sys.stdout.write("\033[2J\033[3J\033[H")
    log.info("Console cleared" + "\n".join(["" for _ in range(25)]))

    sys.stdout.flush()


def log_dashboard_message(log: CustomLogger, event: Event) -> None:
    """Apply formatting rules and emit log lines for a dashboard event.

    Args:
        log: Logger with colored methods (``log_llm_request``, etc.).
        event: Any ``common.events.Event`` variant.
    """
    if isinstance(event, ConversationStart):
        clear_console(log)
        return

    if isinstance(event, TotalCost):
        log_cost_report(log, event.models)
        return

    if isinstance(event, ParsedResponse):
        if event.output_parsed is not None:
            body = json.dumps(
                event.output_parsed.model_dump(),
                indent=2,
                ensure_ascii=False,
                default=str,
            )
            log.log_llm_response(body)
        else:
            log.log_llm_response(event.raw_text or "")
        return

    if isinstance(event, Reasoning):
        if event.summary:
            summary_text = "\n".join(s.get("text", str(s)) for s in event.summary)
            log.log_llm_response(f"summary:\n{summary_text}")
        else:
            data = event.json_output.get("content") or event.json_output
            trimmed = format_for_logging(data, max_value_length=_DASHBOARD_TRIM)
            log.log_llm_response(trimmed)
        return

    if isinstance(event, ToolCall):
        wrapped = format_for_logging(
            {"arguments": event.arguments},
            max_value_length=_DASHBOARD_TRIM,
        )
        text = f"name: {event.name}\n call_id: {event.call_id}\n{wrapped}"
        log.log_tool_call(text)
        return

    if isinstance(event, ToolResponse):
        wrapped = format_for_logging(
            {"response": event.response},
            max_value_length=_DASHBOARD_TRIM,
        )
        text = f"name: {event.name}\ncall_id: {event.call_id}\n{wrapped}"
        log.log_tool_call(text)
        return

    if isinstance(event, LLMRequest):
        blocks: list[str] = []
        for m in event.messages:
            role = m.get("role", "")
            content = m.get("content") or m.get("prompt") or ""
            blocks.append(f"role: {role}\nprompt:\n{content}")
        log.log_llm_request("\n\n".join(blocks))
        return

    assert_never(event)


def get_dashboard_logger() -> CustomLogger:
    """Logger used for WebSocket console output."""
    return get_logger("dashboard.console")
