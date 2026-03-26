"""Shared cost report logging (same layout as ``CostTracker.print_cost``)."""

from common.events import Usage
from common.logging_config import CustomLogger


def log_cost_report(log: CustomLogger, model_usage: dict[str, Usage]) -> None:
    """Emit the vertical cost report for all models using ``log_cost`` lines.

    Args:
        log: Logger with ``log_cost`` method.
        model_usage: Mapping from model identifier to its ``Usage`` snapshot.
    """
    if not model_usage:
        log.log_cost("No token usage recorded yet.")
        return

    for model, u in model_usage.items():
        log.log_cost("=" * 40)
        log.log_cost(f"  Model:        {model}")
        log.log_cost("-" * 40)
        log.log_cost(f"  Cost:         ${u.cost:.6f}")
        log.log_cost(f"  Input Cost:   ${u.upstream_inference_input_cost:.6f}")
        log.log_cost(f"  Output Cost:  ${u.upstream_inference_output_cost:.6f}")
        log.log_cost("-" * 40)
        log.log_cost(f"  Input Tokens:   {u.input_tokens}")
        log.log_cost(f"  Cached Tokens:  {u.cached_tokens}")
        log.log_cost(f"  Output Tokens:  {u.output_tokens}")
        log.log_cost(f"  Reason Tokens:  {u.reasoning_tokens}")
        log.log_cost("-" * 40)
        log.log_cost(f"  Requests:       {u.request_count}")
        log.log_cost("=" * 40)
