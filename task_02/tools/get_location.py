from common.llm_api.tool import Tool
from pydantic import BaseModel, Field
from common.hub_client import HubClient
from typing import Any

class GetLocationModel(BaseModel):
    name: str = Field(description="The first name of the person")
    surname: str = Field(description="The surname of the person")

class GetLocationTool(Tool[GetLocationModel]):
    
    def __init__(self, hub_client: HubClient):
        self.hub_client = hub_client
        super().__init__(
            name="get_locations",
            description="Get list of known locations (latitude and longitude) of a person",
            func=self.run_tool,
        )

    def get_model(self) -> type[GetLocationModel]:
        return GetLocationModel

    async def run_tool(self, name: str, surname: str) -> dict[str, Any]:
        response = await self.hub_client.call_api(
            url="api/location",
            json={
                "name": name,
                "surname": surname,
            },
        )
        return response