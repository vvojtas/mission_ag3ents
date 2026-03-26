import asyncio
from dataclasses import dataclass
from typing import Dict

from common.events import Usage
from common.logging_config import get_logger


@dataclass
class ModelUsage:
    """Mutable token-usage accumulator for a single model.

    Used internally by ``CostTracker``; converted to the immutable ``Usage``
    event type when publishing cost reports.
    """

    input_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cost: float = 0.0
    upstream_inference_input_cost: float = 0.0
    upstream_inference_output_cost: float = 0.0
    request_count: int = 0


from common.cost_report import log_cost_report

logger = get_logger(__name__)


def _model_usage_to_event(mu: ModelUsage) -> Usage:
    return Usage(
        input_tokens=mu.input_tokens,
        cached_tokens=mu.cached_tokens,
        output_tokens=mu.output_tokens,
        reasoning_tokens=mu.reasoning_tokens,
        cost=mu.cost,
        upstream_inference_input_cost=mu.upstream_inference_input_cost,
        upstream_inference_output_cost=mu.upstream_inference_output_cost,
        request_count=mu.request_count,
    )


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

    def print_cost(self) -> None:
        """Print the current token usage for all models in a vertical format."""
        usage_events = {model: _model_usage_to_event(mu) for model, mu in self.model_usage.items()}
        log_cost_report(logger, usage_events)

    def snapshot(self) -> dict[str, Usage]:
        """Return an immutable snapshot of current usage for all models."""
        return {model: _model_usage_to_event(mu) for model, mu in self.model_usage.items()}

    async def clear(self) -> None:
        """Reset all per-model counters to zero.

        Acquires each model lock in sorted order to avoid deadlocks with
        concurrent ``update_usage`` calls on the same model.
        """
        async with self._registry_lock:
            models = list(self.model_usage)
        for model in sorted(models):
            lock = self._model_locks.get(model)
            if lock is None:
                continue
            async with lock:
                self.model_usage[model] = ModelUsage()
