from collections.abc import AsyncIterator

from fastmcp import FastMCP
from fastmcp.server.context import Context
from fastmcp.server.lifespan import lifespan
from fastmcp.dependencies import CurrentContext

from typing import Any, Annotated, cast
from common import Settings
from pydantic import Field


from common.hub_client import HubClient

_HUB_CLIENT_KEY = "hub_client"

@lifespan
async def _hub_lifespan(_server: FastMCP[Any]) -> AsyncIterator[dict[str, HubClient]]:
    """Open the hub HTTP client for the server process and close it on shutdown."""
    async with HubClient(Settings()) as hub_client:
        try:
            yield {_HUB_CLIENT_KEY: hub_client}
        finally:
            print("Shutting down...")


mcp = FastMCP[Any](
    "Package Delivery MCP Server",
    instructions="MCP Server providing access to Package Delivery API",
    lifespan=_hub_lifespan,
)

@mcp.tool(name="check", description="Check for the status and current location of the package.")
async def check(
    package_id: Annotated[str, Field(description="The identification number of the package. Hint: should be provided by operator. Ask if not yet shared.")],
    ctx: Context = CurrentContext(),
    ) -> Any:
    hub_client: HubClient = ctx.lifespan_context[_HUB_CLIENT_KEY]
    response = await hub_client.call_api(
        url="api/packages",
        json={
            "action": "check",
            "packageid": package_id,
        },
    )
    return cast(list[dict[str, Any]], response)

@mcp.tool(name="redirect", description="Redirect the package to a new destination. Returns acknowledgement of the request together with confirmationd code field. Hint: confirmation code should be returned back to operator")
async def redirect(
    package_id: Annotated[str, Field(description="The identification number of the package. Hint: should be provided by operator. Ask if not yet shared.")],
    destination: Annotated[str, Field(description="The new destination of the package. One of power plants identifiers.")],
    code: Annotated[str, Field(description="Security code allowing the redirection. Hint: must be provided by operator. Ask if not yet shared.")],
    ctx: Context = CurrentContext(),
) -> Any:
    hub_client: HubClient = ctx.lifespan_context[_HUB_CLIENT_KEY]
    response = await hub_client.call_api(
        url="api/packages",
        json={
            "action": "redirect",
            "packageid": package_id,
            "destination": destination,
            "code": code,
        },
    )
    return cast(dict[str, Any], response)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8002)