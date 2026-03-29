from typing import Any, Self
from fastmcp import Client, FastMCP

from common.llm_api.schema_utils import make_strict_schema, make_strictless_schema
from common.logging_config import get_logger
logger = get_logger(__name__)

strickless_tools = ["send_action"]

class MCPClient:
    def __init__(self, client_initialization_charge: str| FastMCP) -> None:
        self.client_initialization_charge = client_initialization_charge
        self._client: Client[Any] | None = None

    async def __aenter__(self) -> Self:
        self._client = Client[Any](self.client_initialization_charge)
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client is not None:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
            self._client = None


    async def list_mcp_tools(self) -> list[dict[str, Any]]:
        client = self._client
        if client is None:
            raise RuntimeError("MCPClient must be used as an async context manager")
        tools = await client.list_tools()
        return [MCPClient._mcp_tool_to_openai(tool) for tool in tools]

    async def call_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        logger.log_tool_call(f"Running tool {tool_name} with parameters: {arguments}")
        
        client = self._client
        if client is None:
            raise RuntimeError("MCPClient must be used as an async context manager")
        try:
            result = await client.call_tool(tool_name, arguments)
            logger.log_tool_call(f"Tool {tool_name} returned: {result}")
            return result.structured_content
        except Exception as ex:
            return {
                "sucess": False,
                "error_message": str(ex)
            }

    @staticmethod
    def _mcp_tool_to_openai(mcp_tool: Any) -> dict[str, Any]:
        if mcp_tool.name in strickless_tools:
            return {
                "type": "function",
                "name": mcp_tool.name,
                "description": mcp_tool.description,
                "parameters": make_strictless_schema(mcp_tool.inputSchema),
                "strict": False,
            }
        else:
            return {
                "type": "function",
                "name": mcp_tool.name,
                "description": mcp_tool.description,
                "parameters": make_strict_schema(mcp_tool.inputSchema),
                "strict": True,
            }

