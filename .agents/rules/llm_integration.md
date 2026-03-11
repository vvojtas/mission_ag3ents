# LLM Integration Rules

## Provider & Library
- **`litellm`** — use for all LLM calls. Provides a unified API across providers.
- **OpenRouter** — primary provider. Model strings follow the format: `openrouter/<provider>/<model>` (e.g., `openrouter/openai/gpt-4o`, `openrouter/anthropic/claude-3.5-sonnet`).
- Always use **async** calls: `litellm.acompletion()`.

## Model Switching
- Models should be easily switchable per task — pass model as a parameter, don't hardcode.
- A task may use **multiple models** (e.g., a cheap model for classification, a powerful one for generation).


## Cost & Usage Tracking
- Log token usage and cost after each LLM call (OpenRouter returns this in response metadata).
- Use the colored logging system to distinguish LLM requests (cyan) from responses (green).

## Prompts
- Store prompt templates in `/task_XX/prompts/*.md`.
- Use `{placeholder}` syntax for variable substitution (Python's `str.format()` style).
- Keep prompts readable — use markdown formatting within prompt files.

## Error Handling
- Wrap LLM calls in try/except — log errors clearly.
- Retry logic and rate limit handling will be added later (keep code structured to allow this).
