from typing import Self

from common.settings import Settings
import httpx
import asyncio

class HttpClientProvider:
    def __init__(self, settings: Settings, base_url: str = "https://openrouter.ai/api/v1"):
        self.open_router_key = settings.openrouter_api_key
        self.base_url = base_url
        self._init_lock = asyncio.Lock()
        self.client: httpx.AsyncClient | None = None
    
    async def __aenter__(self) -> Self:
        return self

    async def get_client(self) -> httpx.AsyncClient:
        if self.client  is None:
            async with self._init_lock:
                if self.client is None:
                    self.client = httpx.AsyncClient(
                        headers={"Authorization": f"Bearer {self.open_router_key}"},
                        base_url=self.base_url,
                        timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0),
                    )
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async with self._init_lock:
            if self.client:
                await self.client.aclose()
                self.client = None