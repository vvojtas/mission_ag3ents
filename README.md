# mission_ag3ents

Repository for AI Devs tasks and challenges.

![Taming AI Agents of tomorrow, today!](assets/readme_image.png)

## Tech Stack

| Component | Choice |
|-----------|--------|
| Language | Python 3.12, async-first |
| LLM Access | [OpenAI SDK](https://platform.openai.com/docs/) via [OpenRouter](https://openrouter.ai/) |
| Config | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) + `.env` |
| Package Manager | [uv](https://docs.astral.sh/uv/) |
| Logging | `logging` module with colored output |

## Project Structure

```
mission_ag3ents/
├── .agents/rules/        # AI assistant rules
├── common/               # Shared utilities
│   ├── settings.py       # Configuration (pydantic-settings)
│   └── logging_config.py # Colored logging setup
├── task_01/              # Per-task solution folders
│   ├── README.md         # Task description & notes
│   ├── prompts/          # Prompt templates (.md)
│   └── solution.py       # Task entry point
├── .env.example          # Template for secrets
├── pyproject.toml        # Dependencies
└── README.md
```

## Setup

### 1. Install uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create virtual environment and install dependencies

```bash
uv sync
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### 4. Run a task

```bash
uv run python -m task_01.solution
```

### Running mco inspector

npx @modelcontextprotocol/inspector node build/index.js

## Adding a New Task

1. Create a new folder: `task_XX/`
2. Add `README.md`, `prompts/`, and `solution.py`
3. Follow the pattern from `task_01/`

## Tasks

| Task | Description | Status |
|------|-------------|--------|
| [task_01](task_01/) | *TBD* | ⬜ |
