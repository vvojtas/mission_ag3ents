"""MCP tool: hub_post_answer — submit a task answer to the hub API."""

import re
from typing import Annotated, Any

import httpx
from fastmcp import FastMCP
from pydantic import Field

from common import Settings
from common.hub_client import HubClient
from common.logging_config import get_logger

logger = get_logger(__name__)

_FLAG_RE = re.compile(r"\{FLG:[^}]+\}")


def _extract_flag(message: str) -> str | None:
    match = _FLAG_RE.search(message)
    return match.group(0) if match else None


def _build_hint(success: bool, code: int | None, message: str, flag: str | None) -> str:
    if success and flag:
        return f"Task solved! Flag: {flag}"
    if success:
        return "Submission accepted by the hub."
    if code is not None:
        return f"Submission failed (code {code}). Review the answer and try again."
    return "Request to hub failed. Check credentials and connectivity."


def register_post_answer(mcp: FastMCP, settings: Settings) -> None:
    """Attach the hub_post_answer tool to the MCP server.

    Args:
        mcp: FastMCP instance to register the tool on.
        settings: Project settings providing hub credentials.
    """

    @mcp.tool(
        name="hub_post_answer",
        description=(
            "Submit an answer for a task to the hub API. "
            "Returns whether the submission succeeded, the raw hub message, "
            "and the extracted flag on success."
        ),
    )
    async def hub_post_answer(
        task_name: Annotated[
            str,
            Field(
                description=(
                    "Name of the task to submit (e.g. \"mp3\", \"photos\"). "
                    "Ask the user if not specified."
                ),
            ),
        ],
        answer: Annotated[
            str | list[Any] | dict[str, Any],
            Field(
                description=(
                    "The answer payload. Format depends on the task — "
                    "can be a plain string, a list of values, or a dict."
                ),
            ),
        ],
    ) -> dict[str, Any]:
        try:
            async with HubClient(settings) as hub:
                data = await hub.post_answer(task_name, answer)

            code: int | None = data.get("code")
            message: str = str(data.get("message", ""))
            success = code == 0
            flag = _extract_flag(message) if success else None

            return {
                "success": success,
                "code": code,
                "message": message,
                "flag": flag,
                "hint": _build_hint(success, code, message, flag),
            }

        except httpx.HTTPStatusError as exc:
            msg = f"HTTPStatusError: {exc.response.status_code} {exc.response.reason_phrase}"
            logger.error("hub_post_answer HTTP error: %s", msg)
            return {
                "success": False,
                "code": None,
                "message": msg,
                "flag": None,
                "hint": _build_hint(False, None, msg, None),
            }

        except Exception as exc:
            msg = str(exc)
            logger.error("hub_post_answer unexpected error: %s", msg)
            return {
                "success": False,
                "code": None,
                "message": msg,
                "flag": None,
                "hint": _build_hint(False, None, msg, None),
            }
