"""MCP tool: send_action — send an action command to the hub API with retry logic."""

import asyncio
from typing import Annotated, Any

import httpx
from fastmcp import FastMCP
from pydantic import Field

from common import Settings
from common.hub_client import HubClient, HubResponse
from common.logging_config import get_logger

logger = get_logger(__name__)

_DEFAULT_MAX_RETRIES = 3


async def _execute_hub_call(settings: Settings, command: dict[str, Any]) -> dict[str, Any]:
    """Make a single hub call and return the structured success result."""
    async with HubClient(settings) as hub:
        result: HubResponse = await hub.post_answer_with_headers(answer=command)
    return {
        "success": True,
        "response": result.response,
        "headers": result.headers,
        "hint": _success_hint(result.response),
    }


async def _handle_retryable_errors(
    exc: httpx.HTTPStatusError,
    retries_left: int,
    max_retries: int,
) -> int | None:
    """Handle 429 and 503 by sleeping; return updated retries_left or None to stop."""
    code = exc.response.status_code

    if code == 429:
        retry_after = _parse_retry_after(exc.response.headers)
        logger.warning(
            "send_action: 429 Too Many Requests — waiting %.1fs (Retry-After)",
            retry_after,
        )
        await asyncio.sleep(retry_after)
        return retries_left  # unchanged — 429 does not count as a retry

    if code == 503 and retries_left > 0:
        retries_left -= 1
        wait = 2 ** (max_retries - retries_left)
        logger.warning(
            "send_action: 503 — retry %d/%d in %ds",
            max_retries - retries_left,
            max_retries,
            wait,
        )
        await asyncio.sleep(wait)
        return retries_left

    return None  # not retryable


def register_send_action(
    mcp: FastMCP,
    settings: Settings,
    *,
    max_retries: int = _DEFAULT_MAX_RETRIES,
) -> None:
    """Attach the send_action tool to the MCP server.

    Args:
        mcp: FastMCP instance to register the tool on.
        settings: Project settings providing hub credentials.
        max_retries: Maximum retries on 503. Defaults to 3.
    """

    @mcp.tool(
        name="send_action",
        description=(
            "Send an action command to the hub API. "
            "The `command` dict MUST contain an `action` key (string) identifying "
            "the action to execute. Additional keys are action-specific parameters. "
            "Available actions include: start, status, move, help, and others. "
            "If you don't know the available actions or their parameters, send "
            '`{"action": "help"}` first to get the full documentation.'
        ),
    )
    async def send_action(
        command: Annotated[
            dict[str, Any],
            Field(
                description=(
                    "Action command dict. Must contain key 'action' (str). "
                    'Example: {"action": "help"} to list available actions. '
                    "Additional keys depend on the action."
                ),
            ),
        ],
    ) -> dict[str, Any]:
        if "action" not in command:
            return {
                "success": False,
                "response": None,
                "headers": {},
                "hint": (
                    "The command dict must include an 'action' key. "
                    'Try {"action": "help"} to discover available actions.'
                ),
            }

        retries_left = max_retries

        while True:
            try:
                return await _execute_hub_call(settings, command)
            except httpx.HTTPStatusError as exc:
                updated = await _handle_retryable_errors(exc, retries_left, max_retries)
                if updated is not None:
                    retries_left = updated
                    continue
                msg = f"HTTP {exc.response.status_code}: {exc.response.text[:500]}"
                logger.error("send_action HTTP error: %s", msg)
                return {
                    "success": False,
                    "response": _try_json(exc.response),
                    "headers": dict(exc.response.headers),
                    "hint": _failure_hint(exc.response.status_code, msg),
                }
            except Exception as exc:
                msg = str(exc)
                logger.error("send_action unexpected error: %s", msg)
                return {
                    "success": False,
                    "response": None,
                    "headers": {},
                    "hint": _failure_hint(None, msg),
                }


def _parse_retry_after(headers: httpx.Headers) -> float:
    """Extract Retry-After as seconds, defaulting to 5s if missing or unparseable."""
    raw = headers.get("retry-after", "5")
    try:
        return float(raw)
    except (ValueError, TypeError):
        return 5.0


def _try_json(response: httpx.Response) -> dict | str | None:
    try:
        return response.json()
    except Exception:
        return response.text or None


def _success_hint(body: dict[str, Any]) -> str:
    message = str(body.get("message", ""))
    if message:
        return message
    return "Action executed. Review the response for details."


def _failure_hint(code: int | None, message: str) -> str:
    base = f"Request failed (HTTP {code}). " if code else f"Request failed: {message}. "
    return base + 'Try sending {"action": "help"} to see available actions and parameters.'
