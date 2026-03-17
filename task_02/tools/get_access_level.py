from common.llm_api.tool import Tool
from pydantic import BaseModel, Field
from common.hub_client import HubClient
from typing import Any
from common.logging_config import get_logger
logger = get_logger(__name__)


class GetAccessLevelModel(BaseModel):
    name: str = Field(description="The name of the person")
    surname: str = Field(description="The surname of the person")
    birth_year: int = Field(description="The birth year of the person")

class GetAccessLevelTool(Tool[GetAccessLevelModel]):
    def __init__(self, hub_client: HubClient):
        self.hub_client = hub_client
        super().__init__(
            name="get_access_level",
            description="Get the access level of a person",
            func=self.run_tool,
        )

    def get_model(self) -> type[GetAccessLevelModel]:
        return GetAccessLevelModel

    async def run_tool(self, name: str, surname: str, birth_year: int) -> dict[str, Any]:
        response = await self.hub_client.call_api(
            url="api/accesslevel",
            json={
                "name": name,
                "surname": surname,
                "birthYear": birth_year,
            },
        )
        return response