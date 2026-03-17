import asyncio

from common.llm_api.llm_client import LLMClient
from common.llm_api.tool import Tool
from typing import Any
from common.llm_api.llm_client import ParsedResponse, ToolCall, Reasoning
import json

class ToolsLoop:
    def __init__(self, llm_client: LLMClient, tools: list[Tool]):
        self.llm_client = llm_client
        self.tools = {tool.name: tool for tool in tools}

    async def run(self, tools: list[Tool], input: list[Any], max_iterations: int = 10, *args: Any, **kwargs: Any) -> ParsedResponse:

        messages = input.copy()

        for _ in range(max_iterations):
            responses = await self.llm_client.responses(
                tools = [tool.to_dict() for tool in tools],
                input = messages,
                *args,
                **kwargs,
            )
            for response in responses:
                if isinstance(response, ParsedResponse):
                    return response

            tool_calls = [response for response in responses if isinstance(response, ToolCall)]
            messages.extend([tc.json_output for tc in tool_calls])
            if not tool_calls:
                raise ValueError("No actionable responses found")
            tool_responses = await asyncio.gather(
                *[self._run_tool(tc) for tc in tool_calls]
            )
            messages.extend(tool_responses)
        
        
        raise ValueError("Max iterations reached")


    async def _run_tool(self, tool_call: ToolCall) -> Any:
        tool = self.tools[tool_call.name]
        arguments = tool.get_model().model_validate(tool_call.arguments)
        json_output = await tool.run(arguments)
        return {
             "type": "function_call_output",
             "call_id": tool_call.call_id,
             "output": json.dumps(json_output)
        }
