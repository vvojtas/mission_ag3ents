from pydantic import BaseModel, Field
from common.llm_api.tool import Tool
from typing import Any
from haversine import haversine, Unit
from common.logging_config import get_logger
logger = get_logger(__name__)

class Location(BaseModel):
    latitude: float = Field(description="The latitude of the location")
    longitude: float = Field(description="The longitude of the location")
    label: str = Field(description="The label of the location (use power plant code or person full name)")

class FindShortestDistanceLabelsModel(BaseModel):
    start_locations: list[Location] = Field(description="List of locations")
    target_locations: list[Location] = Field(description="The target locations")

class FindShortestDistanceLabelsTool(Tool[FindShortestDistanceLabelsModel]):
    def __init__(self):
        super().__init__(
            name="find_shortest_distance_labels",
            description="Find the shortest distance (Haversine formula) between one of the start locations and one of the target locations. Returns the smallest distance in kilometers and both locations.",
            func=self.run_tool,
        )

    def get_model(self) -> type[FindShortestDistanceLabelsModel]:
        return FindShortestDistanceLabelsModel

    def _distance(self, location1: Location, location2: Location) -> float:
        return haversine((location1.latitude, location1.longitude), (location2.latitude, location2.longitude), unit=Unit.KILOMETERS)

    async def run_tool(self, start_locations: list[Location], target_locations: list[Location]) -> dict[str, Any]:
        if not start_locations or not target_locations:
            return {"distance": float('inf'), "start_location": None, "target_location": None}
        min_distance = float('inf')
        min_start_location = None
        min_target_location = None
        for start_location in start_locations:
            for target_location in target_locations:
                distance = self._distance(start_location, target_location)
                if distance < min_distance:   
                    min_distance = distance
                    min_start_location = start_location
                    min_target_location = target_location
        return {
            "distance": min_distance, 
            "start_location": min_start_location.model_dump() if min_start_location else None, 
            "target_location": min_target_location.model_dump() if min_target_location else None,
        }
        