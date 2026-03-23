import asyncio

from common.llm_api.mcp_client import MCPClient
from common.llm_api.llm_client import LLMClient
from common.llm_api.tool import Tool
from typing import Any
from common.llm_api.llm_client import ParsedResponse, ToolCall
import json

class ToolsLoop:
    def __init__(self, llm_client: LLMClient, native_tools: list[Tool] = [], mcp_clients: list[MCPClient] = []):
        self.llm_client = llm_client
        self.native_tools = {tool.name: tool for tool in (native_tools or [])}
        self.mcp_clients: list[MCPClient] = mcp_clients or []
        self.mcp_tools: dict[str, tuple[MCPClient, dict[str, Any]]] = {}

    async def initialize(self) -> None:
        if self.mcp_clients:
            tool_lists = await asyncio.gather(
                *[client.list_mcp_tools() for client in self.mcp_clients]
            )
            self.mcp_tools = {tool["name"]: (client, tool) for client, tools in zip(self.mcp_clients, tool_lists) for tool in tools}

    async def run(self, input: list[Any], max_iterations: int = 10, *args: Any, **kwargs: Any) -> ParsedResponse:

        messages = input.copy()

        all_tools = [
            native_tool.to_dict() for native_tool in self.native_tools.values()
        ] + [mcp_tool[1] for mcp_tool in self.mcp_tools.values()]

        for _ in range(max_iterations):
            responses = await self.llm_client.responses(
                tools = all_tools,
                input = messages,
                *args,
                **kwargs,
            )
            for response in responses:
                if isinstance(response, ParsedResponse):
                    return response

            messages.extend([message.json_output for message in responses if message.json_output is not None])

            tool_calls = [response for response in responses if isinstance(response, ToolCall)]
            tool_responses = await asyncio.gather(
                *[self._run_tool(tc) for tc in tool_calls]
            )
            
            messages.extend(tool_responses)
        
        
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
        return {
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": json.dumps(json_output) if json_output is not None else None
        }
