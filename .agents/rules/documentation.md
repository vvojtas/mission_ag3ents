---
trigger: always_on
---

# Documentation Rules

## Docstrings
- **Key functions and classes** must have Google-style docstrings — not every trivial helper needs one, focus on public APIs, complex logic, and non-obvious behavior.
- Include: one-line summary, `Args:`, `Returns:`, `Raises:` (when applicable).
- Keep docstrings concise — describe *what* and *why*, not obvious implementation details.

### Example
```python
async def ask(prompt: str, model: str | None = None) -> str:
    """Send a prompt to the LLM and return the text response.

    Args:
        prompt: The user message to send.
        model: Model identifier (e.g., 'openai/gpt-4o').
            Uses default from settings if not provided.

    Returns:
        The assistant's text response.

    Raises:
        LLMError: If the API call fails after retries.
    """
```

## Updating Documentation
- **When code changes, update docstrings immediately** — never leave outdated docs.
- **Do NOT rephrase documentation for the sake of it** — only change docs when the underlying behavior changes.
- If a function's signature, behavior, or error handling changes, the docstring must reflect that.

## Comments
- Use comments sparingly — explain *why*, not *what*.
- Remove comments that repeat what the code already says.
- Mark future work with `# TODO:` comments (include context on what needs to be done).
