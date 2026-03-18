"""Echo tool — returns whatever message it receives.

Useful for verifying that the tools loop correctly dispatches calls and
feeds results back into the conversation.
"""

from typing import Any

from pydantic import BaseModel, Field

from common.llm_api.tool import Tool
from common.logging_config import get_logger

logger = get_logger(__name__)


class EchoModel(BaseModel):
    message: str = Field(description="The message to echo back.")


class EchoTool(Tool[EchoModel]):
    def __init__(self) -> None:
        super().__init__(
            name="echo",
            description="Echo the provided message back to the caller. Use this whenever you want to repeat something verbatim.",
            func=self.run_tool,
        )

    def get_model(self) -> type[EchoModel]:
        return EchoModel

    async def run_tool(self, message: str) -> dict[str, Any]:
        """Echo the message back.

        Args:
            message: The string to echo.

        Returns:
            A dict with a single ``echo`` key containing the original message.
        """
        return {"echo": message}
