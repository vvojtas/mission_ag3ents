import asyncio
import json
from typing import Any

from common.events import (
    EventPoster,
    LLMRequest,
    NullEventPoster,
    ParsedResponse,
    Reasoning,
    ToolCall,
    ToolResponse,
)
from common.llm_api.llm_client import LLMClient
from common.llm_api.mcp_client import MCPClient
from common.llm_api.tool import Tool


class ToolsLoop:
    """Runs a multi-turn LLM conversation with tool use.

    Args:
        llm_client: Client for LLM API calls.
        event_poster: Receives runtime events (implements ``EventPoster``).
        native_tools: List of local ``Tool`` instances.
        mcp_clients: List of MCP server clients.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        event_poster: EventPoster | None = None,
        native_tools: list[Tool] | None = None,
        mcp_clients: list[MCPClient] | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.event_poster: EventPoster = event_poster or NullEventPoster()
        self.native_tools = {tool.name: tool for tool in (native_tools or [])}
        self.mcp_clients: list[MCPClient] = mcp_clients or []
        self.mcp_tools: dict[str, tuple[MCPClient, dict[str, Any]]] = {}

    async def initialize(self) -> None:
        """Connect to MCP servers and fetch their tool listings."""
        if self.mcp_clients:
            tool_lists = await asyncio.gather(
                *[client.list_mcp_tools() for client in self.mcp_clients]
            )
            self.mcp_tools = {
                tool["name"]: (client, tool)
                for client, tools in zip(self.mcp_clients, tool_lists)
                for tool in tools
            }

    async def run(
        self,
        input: list[Any],
        max_iterations: int = 10,
        *args: Any,
        **kwargs: Any,
    ) -> ParsedResponse:
        """Run the tool loop until a ParsedResponse is returned.

        Args:
            input: Initial message list (Responses API format).
            max_iterations: Maximum number of LLM calls before raising.

        Returns:
            The first ``ParsedResponse`` produced by the LLM.

        Raises:
            ValueError: If no ParsedResponse is returned within ``max_iterations``.
        """
        messages = input.copy()

        all_tools = [
            native_tool.to_dict() for native_tool in self.native_tools.values()
        ] + [mcp_tool[1] for mcp_tool in self.mcp_tools.values()]

        for _ in range(max_iterations):
            self.event_poster.post(LLMRequest(messages=[]))
            responses = await self.llm_client.responses(
                tools=all_tools,
                input=messages,
                *args,
                **kwargs,
            )
            for response in responses:
                match response:
                    case Reasoning():
                        self.event_poster.post(response)
                    case ToolCall():
                        self.event_poster.post(response)
                    case ParsedResponse():
                        self.event_poster.post(response)
                        return response

            messages.extend([
                message.json_output
                for message in responses
                if message.json_output is not None
            ])

            tool_calls = [r for r in responses if isinstance(r, ToolCall)]
            tool_responses = await asyncio.gather(
                *[self._run_tool(tc) for tc in tool_calls]
            )
            messages.extend(tool_responses)

            parsed = next((r for r in responses if isinstance(r, ParsedResponse)), None)
            if parsed:
                return parsed

        raise ValueError("Max iterations reached")

    async def _run_tool(self, tool_call: ToolCall) -> Any:
        json_output = None
        if tool_call.name in self.native_tools:
            native_tool = self.native_tools[tool_call.name]
            arguments = native_tool.get_model().model_validate(tool_call.arguments)
            json_output = await native_tool.run(arguments)
        elif tool_call.name in self.mcp_tools:
            client, _ = self.mcp_tools[tool_call.name]
            json_output = await client.call_mcp_tool(tool_call.name, tool_call.arguments)
        self.event_poster.post(ToolResponse(
            name=tool_call.name,
            call_id=tool_call.call_id,
            response=json_output,
        ))
        return {
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": json.dumps(json_output) if json_output is not None else None,
        }
