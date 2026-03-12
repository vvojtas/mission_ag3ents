---
trigger: always_on
---

# Project Structure Rules

## Directory Layout

```
mission_ag3ents/
├── .agents/rules/        # AI assistant rules (committed)
├── common/               # Shared utilities
│   ├── __init__.py
│   ├── settings.py       # Pydantic-settings configuration
│   ├── logging_config.py # Colored logging setup
│   ├── llm_client.py     # LLM calling wrapper (OpenAI SDK)
│   ├── task_api.py       # Task platform API client
│   └── prompt_loader.py  # Prompt template loader
├── task_01/              # Per-task solution folders
│   ├── README.md
│   ├── prompts/          # Prompt templates (.md)
│   └── solution.py
├── task_02/
│   └── ...
├── .env                  # Secrets (git-ignored)
├── .env.example          # Template for .env
├── pyproject.toml        # Dependencies & project config
└── README.md
```

## Conventions
- **`/common/`** — shared code used across tasks. Import as `from common.settings import Settings`.
- **`/task_XX/`** — each task gets its own folder (e.g., `task_01`, `task_02`).
- **Task README** — every task folder has a `README.md` documenting the objective, approach, and solution.
- **Prompts** — stored as `.md` files in `/task_XX/prompts/` using `{placeholder}` syntax for variable substitution.
- **`pyproject.toml`** — single source of truth for dependencies. Do not create `requirements.txt`.

## Adding a New Task
1. Create `task_XX/` directory with `README.md`, `prompts/`, and `solution.py`.
2. Follow the same structure as existing tasks.
