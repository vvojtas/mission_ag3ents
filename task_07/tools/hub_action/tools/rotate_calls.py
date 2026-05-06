"""MCP tool: hub_action — rotate grid cells via hub /verify."""

import re
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from common import Settings
from common.hub_client import HubClient
from common.logging_config import get_logger

logger = get_logger(__name__)

_CELL_RE = re.compile(r"^[1-3]x[1-3]$")
_ELECTRICITY_TASK = "electricity"


def register_hub_action(mcp: FastMCP, settings: Settings) -> None:
    """Attach the hub_action tool for electricity rotate submissions."""

    @mcp.tool(
        name="hub_action",
        description=(
            "Rotates each cell on list 90 degrees right. Single cell can be listed multiple times for multiple rotations."
            "Returns a list of hub responses."
        ),
    )
    async def hub_action(
        rotations: Annotated[
            list[str],
            Field(
                description=(
                    'Cells to rotate, e.g. ["2x3", "1x1"].'
                    "Each must match axb with a and b between 1 and 3 inclusive."
                ),
            ),
        ],
    ) -> dict[str, Any]:
        if not rotations:
            return {
                "ok": True,
                "results": [],
                "hint": "No rotations were requested.",
            }

        normalized = [c.strip() for c in rotations]
        invalid = [c for c in normalized if not _CELL_RE.fullmatch(c)]
        if invalid:
            return {
                "ok": False,
                "error": (
                    "Invalid cell format. Each cell must be 'axb' where a and b are integers "
                    "from 1 to 3 (e.g. '2x3')."
                ),
                "invalid_cells": invalid,
                "results": [],
            }

        results: list[dict[str, Any]] = []
        async with HubClient(settings) as hub:
            for cell in normalized:
                try:
                    data = await hub.post_answer({"rotate": cell}, task_name=_ELECTRICITY_TASK)
                    results.append({"cell": cell, "hub_response": data})
                except Exception as exc:
                    logger.error("hub_action failed for %s: %s", cell, exc)
                    results.append({"cell": cell, "error": str(exc)})

        return {
            "ok": True,
            "task": _ELECTRICITY_TASK,
            "results": results,
            "hint": "Rotations applied - download new image to verify current state",
        }
