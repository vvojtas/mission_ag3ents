"""Prompt loader utility for reading markdown prompt templates.
"""

from pathlib import Path
from typing import Any


class PromptLoader:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def _load_prompt(self, prompt_name: str) -> str:
        """Load a prompt from the filesystem."""
        prompt_path = self.base_path / f"{prompt_name}.md"
        if not prompt_path.is_file():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()


    def load_prompt(self, prompt_name: str, **kwargs: Any) -> list[Any]:
        """Load a markdown prompt file and parse it into a list of message dictionaries.

        The file should use markdown headers (e.g., `# System`, `# User`) to denote
        the role for each message block. The content under each header is treated as
        the message content. Placeholders in the markdown file will be substituted
        with the provided kwargs using Python's string.format().

        Args:
            prompt_name: Name of the markdown prompt file.
            **kwargs: Variables to substitute into the prompt placeholders.

        Returns:
            A list of dictionaries containing 'role' and 'content' keys.

        Raises:
            FileNotFoundError: If the prompt file does not exist.
            KeyError: If a placeholder in the template is missing from kwargs.
        """

        content = self._load_prompt(prompt_name)
        if kwargs:
            content = content.format(**kwargs)

        messages = []
        current_role = None
        current_content = []

        for line in content.splitlines():
            if line.startswith("# "):
                if current_role is not None:
                    messages.append({
                        "role": current_role,
                        "content": "\n".join(current_content).strip()
                    })
                current_role = line[2:].strip().lower()
                current_content = []
            else:
                if current_role is not None:
                    current_content.append(line)

        if current_role is not None:
            messages.append({
                "role": current_role,
                "content": "\n".join(current_content).strip()
            })

        return messages
