from collections.abc import AsyncIterator

from fastmcp import FastMCP
from fastmcp.server.context import Context
from fastmcp.server.lifespan import lifespan
from fastmcp.dependencies import CurrentContext

from typing import Any, Annotated, cast
from common import Settings
from pydantic import Field, BaseModel
from haversine import haversine, Unit


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
    "Power Plant Distance MCP Server",
    instructions="MCP Server providing access to Power Plant Employee API and distance calculation tools",
    lifespan=_hub_lifespan,
)

@mcp.tool(name="get_location",  description="Get list of known locations (latitude and longitude) of a person")
async def get_location(
    name: Annotated[str, Field(description="The first name of the person")],
    surname: Annotated[str, Field(description="The surname of the person")],
    ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
    hub_client: HubClient = ctx.lifespan_context[_HUB_CLIENT_KEY]
    response = await hub_client.call_api(
        url="api/location",
        json={
            "name": name,
            "surname": surname,
        },
    )
    return cast(list[dict[str, Any]], response)

@mcp.tool(name="get_access_level", description="Get the access level of a person")
async def get_access_level(
    name: Annotated[str, Field(description="The first name of the person")],
    surname: Annotated[str, Field(description="The surname of the person")],
    birth_year: Annotated[int, Field(description="The birth year of the person")],
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    hub_client: HubClient = ctx.lifespan_context[_HUB_CLIENT_KEY]
    response = await hub_client.call_api(
        url="api/accesslevel",
        json={
            "name": name,
            "surname": surname,
            "birthYear": birth_year,
        },
    )
    return cast(dict[str, Any], response)

class Location(BaseModel):
    latitude: float = Field(description="The latitude of the location")
    longitude: float = Field(description="The longitude of the location")
    label: str = Field(description="The label of the location (use power plant code or person full name)")


def _distance(location1: Location, location2: Location) -> float:
    return haversine((location1.latitude, location1.longitude), (location2.latitude, location2.longitude), unit=Unit.KILOMETERS)

@mcp.tool(name="find_shortest_distance", description="Find the shortest distance (Haversine formula) between one of the start locations and one of the target locations. Returns the smallest distance in kilometers and both locations.")
async def find_shortest_distance(
    start_locations: Annotated[list[Location], Field(description="List of locations")],
    target_locations: Annotated[list[Location], Field(description="The target locations")],
) -> dict[str, Any]:
    if not start_locations or not target_locations:
        return {"distance": float('inf'), "start_location": None, "target_location": None}
    min_distance = float('inf')
    min_start_location = None
    min_target_location = None
    for start_location in start_locations:
        for target_location in target_locations:
            distance = _distance(start_location, target_location)
            if distance < min_distance:   
                min_distance = distance
                min_start_location = start_location
                min_target_location = target_location
    return {
        "distance": min_distance, 
        "start_location": min_start_location.model_dump() if min_start_location else None, 
        "target_location": min_target_location.model_dump() if min_target_location else None,
    }

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8002)