"""MCP tool: send_action — send an action command to the hub API with retry logic."""

import asyncio
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from common import Settings
from common.hub_client import HubClient, HubResponse
from common.logging_config import get_logger

logger = get_logger(__name__)

_DEFAULT_MAX_RETRIES = 3


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
            '`{"command":{"action":"help"}}` first to get the full documentation.'
        ),
    )
    async def send_action(
        command: Annotated[
            dict[str, Any],
            Field(
                description=(
                    "Action command dict. Must contain key 'action' (str). "
                    'Example: {"command":{"action":"help"}} to list available actions. '
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
                    'Try {"command":{"action":"help"}} to discover available actions.'
                ),
            }

        retries_left = max_retries

        while True:
            async with HubClient(settings) as hub:
                result: HubResponse = await hub.post_answer_with_headers(answer=command)

            if 200 <= result.http_code < 300:
                    return {
                        "success": True,
                        "response": result.response,
                        "headers": result.headers,
                        "hint": _success_hint(result.response),
                    }
            elif result.http_code == 429:
                retry_after = _parse_retry_after(result.headers)
                logger.warning(
                    "send_action: 429 Too Many Requests — waiting %.1fs (Retry-After)",
                    retry_after,
                )
                await asyncio.sleep(retry_after+1)

            elif result.http_code == 503 and retries_left > 0:
                retries_left -= 1
                wait = 2 ** (max_retries - retries_left)
                logger.warning(
                    "send_action: 503 — retry %d/%d in %ds",
                    max_retries - retries_left,
                    max_retries,
                    wait,
                )
                await asyncio.sleep(wait)
            else:
                logger.error(f"send_action HTTP - not retrieble code: {result.http_code}, retries left {retries_left}")
                return {
                    "success": False,
                    "response": result.response,
                    "headers": result.headers,
                    "hint": _failure_hint(result.http_code),
                }



def _parse_retry_after(headers: dict[str, Any]) -> float:
    """Extract Retry-After as seconds, defaulting to 30s if missing or unparseable."""
    raw = headers.get("retry-after", "30")
    try:
        return float(raw)
    except (ValueError, TypeError):
        return 30.0


def _success_hint(body: dict[str, Any]) -> str:
    message = str(body.get("message", ""))
    if message:
        return message
    return "Action executed. Review the response for details."


def _failure_hint(code: int | None) -> str:
    base = f"Request failed (HTTP {code}). " if code else f"Request failed."
    return base + 'Try sending {"command":{"action":"help"}} to see available actions and parameters.'
