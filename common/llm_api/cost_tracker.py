import asyncio
from dataclasses import dataclass
from typing import Dict

from common.logging_config import get_logger


@dataclass
class ModelUsage:
    """Tracks token usage, cost, and request counts for a specific model."""
    input_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cost: float = 0.0
    upstream_inference_input_cost: float = 0.0
    upstream_inference_output_cost: float = 0.0
    request_count: int = 0


logger = get_logger(__name__)


class CostTracker:
    """Tracks token usage per LLM model, safe for concurrent async access.

    Uses per-model locks so concurrent updates to different models
    never block each other.
    """

    def __init__(self) -> None:
        self.model_usage: Dict[str, ModelUsage] = {}
        self._model_locks: Dict[str, asyncio.Lock] = {}
        self._registry_lock = asyncio.Lock()

    async def update_usage(self, model: str, usage: dict) -> None:
        """Update token usage, cost, and request count for a given model.

        Args:
            model: The model identifier string (e.g. 'openai/gpt-4o').
            usage: The raw usage dict from the API response.
        """
        if model not in self._model_locks:
            async with self._registry_lock:
                if model not in self._model_locks:
                    self._model_locks[model] = asyncio.Lock()
                    self.model_usage[model] = ModelUsage()

        input_details = usage.get("input_tokens_details", {})
        output_details = usage.get("output_tokens_details", {})
        cost_details = usage.get("cost_details", {})
        cost = usage.get("cost")
        if cost is None:
            logger.warning("Cost not found in usage: %s", usage)
            

        async with self._model_locks[model]:
            mu = self.model_usage[model]
            mu.input_tokens += usage.get("input_tokens", 0)
            mu.cached_tokens += input_details.get("cached_tokens", 0)
            mu.output_tokens += usage.get("output_tokens", 0)
            mu.reasoning_tokens += output_details.get("reasoning_tokens", 0)
            mu.cost += cost or 0.0
            mu.upstream_inference_input_cost += cost_details.get("upstream_inference_input_cost", 0.0)
            mu.upstream_inference_output_cost += cost_details.get("upstream_inference_output_cost", 0.0)
            mu.request_count += 1

    async def print_cost(self):
        """Print the current token usage for all models in a vertical format."""
        if not self.model_usage:
            logger.log_cost("No token usage recorded yet.")
            return

        for model, u in self.model_usage.items():
            logger.log_cost("=" * 40)
            logger.log_cost(f"  Model:        {model}")
            logger.log_cost("-" * 40)
            logger.log_cost(f"  Cost:         ${u.cost:.6f}")
            logger.log_cost(f"  Input Cost:   ${u.upstream_inference_input_cost:.6f}")
            logger.log_cost(f"  Output Cost:  ${u.upstream_inference_output_cost:.6f}")
            logger.log_cost("-" * 40)
            logger.log_cost(f"  Input Tokens:   {u.input_tokens}")
            logger.log_cost(f"  Cached Tokens:  {u.cached_tokens}")
            logger.log_cost(f"  Output Tokens:  {u.output_tokens}")
            logger.log_cost(f"  Reason Tokens:  {u.reasoning_tokens}")
            logger.log_cost("-" * 40)
            logger.log_cost(f"  Requests:       {u.request_count}")
            logger.log_cost("=" * 40)
