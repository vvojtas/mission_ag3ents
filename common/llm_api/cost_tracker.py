import asyncio
from dataclasses import dataclass
from typing import Dict, Callable, Awaitable

from common.logging_config import get_logger


@dataclass
class ModelUsage:
    """Tracks token usage and request counts for a specific model."""
    input_tokens: int = 0
    output_tokens: int = 0
    request_count: int = 0


@dataclass
class ModelCost:
    model_name: str
    input_tokens_cost: float
    output_tokens_cost: float


logger = get_logger(__name__)


type PriceFetcher = Callable[[set[str]], Awaitable[dict[str, ModelCost]]]


class CostTracker:
    """Tracks token usage per LLM model, safe for concurrent async access.

    Uses per-model locks so concurrent updates to different models
    never block each other.
    """

    def __init__(self) -> None:
        self.model_usage: Dict[str, ModelUsage] = {}
        self._model_locks: Dict[str, asyncio.Lock] = {}
        self._registry_lock = asyncio.Lock()

    async def update_usage(self, model: str, input_tokens: int, output_tokens: int) -> None:
        """Update token usage and request count for a given model.

        Args:
            model: The model identifier string (e.g. 'openai/gpt-4o').
            input_tokens: Number of input tokens consumed.
            output_tokens: Number of output tokens produced.
        """
        if model not in self._model_locks:
            async with self._registry_lock:
                if model not in self._model_locks:
                    self._model_locks[model] = asyncio.Lock()
                    self.model_usage[model] = ModelUsage()

        async with self._model_locks[model]:
            self.model_usage[model].input_tokens += input_tokens
            self.model_usage[model].output_tokens += output_tokens
            self.model_usage[model].request_count += 1

    async def print_cost(self, fetch_prices_func: PriceFetcher):
        """Print the current token usage for all models in a grid format."""
        if not self.model_usage:
            logger.log_cost("No token usage recorded yet.")
            return

        model_costs = await fetch_prices_func(set(self.model_usage.keys()))

        logger.log_cost("-" * 122)
        logger.log_cost(f"| {'Model':<30} | {'Total Cost':<12} | {'Input Cost':<12} | {'Output Cost':<13} | {'Input Tokens':<12} | {'Output Tokens':<13} | {'Requests':<8} |")
        logger.log_cost("-" * 122)

        for model, usage in self.model_usage.items():
            cost_info = model_costs.get(model)
            if cost_info:
                in_cost = usage.input_tokens * cost_info.input_tokens_cost
                out_cost = usage.output_tokens * cost_info.output_tokens_cost
            else:
                in_cost = 0.0
                out_cost = 0.0
            
            total_cost = in_cost + out_cost
                
            logger.log_cost(
                f"| {model:<30} | ${total_cost:<11.6f} | ${in_cost:<11.6f} | ${out_cost:<12.6f} | "
                f"{usage.input_tokens:<12} | {usage.output_tokens:<13} | {usage.request_count:<8} |"
            )

        logger.log_cost("-" * 122)
