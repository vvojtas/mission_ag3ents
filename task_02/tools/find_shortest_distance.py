from pydantic import BaseModel, Field
from common.llm_api.tool import Tool
from typing import Any
from haversine import haversine, Unit
from common.logging_config import get_logger
logger = get_logger(__name__)

class Location(BaseModel):
    latitude: float = Field(description="The latitude of the location")
    longitude: float = Field(description="The longitude of the location")

class FindShortestDistanceModel(BaseModel):
    locations: list[Location] = Field(description="List of locations")
    target_location: Location = Field(description="The target location")

class FindShortestDistanceTool(Tool[FindShortestDistanceModel]):
    def __init__(self):
        super().__init__(
            name="find_shortest_distance",
            description="Find the shortest distance (Haversine formula) between the target and any location from the list. Returns the smallest distance in kilometers.",
            func=self.run_tool,
        )

    def get_model(self) -> type[FindShortestDistanceModel]:
        return FindShortestDistanceModel

    def _distance(self, location1: Location, location2: Location) -> float:
        return haversine((location1.latitude, location1.longitude), (location2.latitude, location2.longitude), unit=Unit.KILOMETERS)

    async def run_tool(self, locations: list[Location], target_location: Location) -> dict[str, Any]:
        if not locations:
            return {"distance": None}
        min_distance = self._distance(target_location, locations[0])
        for location in locations[1:]:
            distance = self._distance(target_location, location)
            if distance < min_distance:
                min_distance = distance
        return {"distance": min_distance}
        