"""LLM API sub-package: OpenRouter client, cost tracking, and model metadata.

Exports are resolved lazily so submodules can be imported independently
without pulling in heavyweight dependencies during package initialisation.
"""

from typing import Any

__all__ = [
    "LLMClient",
    "HttpClientProvider",
    "CostTracker",
    "ModelUsage",
    "ModelRepository",
]


def __getattr__(name: str) -> Any:
    if name == "LLMClient":
        from common.llm_api.llm_client import LLMClient

        return LLMClient
    if name == "HttpClientProvider":
        from common.llm_api.http_client_provider import HttpClientProvider

        return HttpClientProvider
    if name == "CostTracker":
        from common.llm_api.cost_tracker import CostTracker

        return CostTracker
    if name == "ModelUsage":
        from common.llm_api.cost_tracker import ModelUsage

        return ModelUsage
    if name == "ModelRepository":
        from common.llm_api.model_repository import ModelRepository

        return ModelRepository
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
