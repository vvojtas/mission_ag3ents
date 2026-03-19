"""Colored logging configuration for the project.

Provides distinct colors for different event types so that console
output is easy to scan at a glance:

- **LLM Request** (cyan)   — messages sent to the LLM
- **LLM Response** (green)  — messages received from the LLM
- **Task Hub** (blue)     — task platform API interactions
- **Cost Tracker** (yellow)     — cost tracker events
- **Error** (red)           — errors and exceptions
- **General** (white)       — default informational messages

Supports dual output: colored console and plain-text log file
(per-task `.logs/` directory) for persistence.
"""

import json
import logging
import sys
import typing
from datetime import datetime
from pathlib import Path
from typing import Any

from colorama import Fore, Style, init as colorama_init


# Initialize colorama for Windows compatibility
colorama_init(autoreset=True)


# Custom log level for LLM-specific events
LLM_REQUEST = 25
LLM_RESPONSE = 26
TASK_HUB = 27
COST = 28
TOOL_CALL = 29

logging.addLevelName(LLM_REQUEST, "LLM_REQ")
logging.addLevelName(LLM_RESPONSE, "LLM_RES")
logging.addLevelName(TASK_HUB, "TASK_HUB")
logging.addLevelName(COST, "COST_TRACKER")
logging.addLevelName(TOOL_CALL, "TOOL_CALL")


_COLOR_MAP: dict[int, str] = {
    LLM_REQUEST: Fore.CYAN,
    LLM_RESPONSE: Fore.GREEN,
    TASK_HUB: Fore.BLUE,
    COST: Fore.YELLOW,  
    TOOL_CALL: Fore.MAGENTA,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.RED + Style.BRIGHT,
    logging.WARNING: Fore.MAGENTA,
    logging.INFO: Fore.WHITE,
    logging.DEBUG: Fore.LIGHTBLACK_EX,
}


_LOG_FORMAT = "{timestamp} | {level:<8} | {message}"


class ColoredFormatter(logging.Formatter):
    """Formatter that applies colors based on log level.

    Each log level maps to a distinct color for quick visual
    identification in the console.
    """

    def format(self, record: logging.LogRecord) -> str:
        color = _COLOR_MAP.get(record.levelno, Fore.WHITE)
        message = record.getMessage()

        if record.levelno == COST:
            return f"{color}{message}{Style.RESET_ALL}"

        timestamp = self.formatTime(record, self.datefmt)
        line = _LOG_FORMAT.format(
            timestamp=timestamp, level=record.levelname, message=message,
        )
        return f"{color}{line}{Style.RESET_ALL}"


class PlainFileFormatter(logging.Formatter):
    """Plain text formatter for file output — no ANSI color codes."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()

        if record.levelno == COST:
            return message

        timestamp = self.formatTime(record, self.datefmt)
        return _LOG_FORMAT.format(
            timestamp=timestamp, level=record.levelname, message=message,
        )


def setup_logging(
    level: int = logging.DEBUG,
    task_dir: Path | None = None,
) -> None:
    """Configure the root logger with colored console output and optional file output.

    Sets up a StreamHandler (colored) and, when *task_dir* is given,
    a FileHandler that writes to ``<task_dir>/.logs/run_<timestamp>.log``.

    Args:
        level: Minimum log level to display. Defaults to DEBUG.
        task_dir: Task directory. When provided, a `.logs/` sub-directory
            is created and a plain-text log file is written there.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.handlers:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(level)
        console.setFormatter(ColoredFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
        root_logger.addHandler(console)

    if task_dir is not None:
        logs_dir = Path(task_dir) / ".logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = logs_dir / f"run_{ts}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(
            PlainFileFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        )
        root_logger.addHandler(file_handler)


class CustomLogger(logging.Logger):
    """Custom logger class with dedicated methods for specific event types."""

    def log_llm_request(self, message: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        """Log an outgoing LLM request.

        Args:
            message: Description of the request being sent.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.log(LLM_REQUEST, message, *args, **kwargs)

    def log_llm_response(self, message: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        """Log an incoming LLM response.

        Args:
            message: Description of the response received.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.log(LLM_RESPONSE, message, *args, **kwargs)

    def log_task_hub(self, message: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        """Log a task platform API interaction.

        Args:
            message: Description of the task hub event.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.log(TASK_HUB, message, *args, **kwargs)

    def log_cost(self, message: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        """Log a cost tracker event.

        Args:
            message: Description of the cost tracker event.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.log(COST, message, *args, **kwargs)

    def log_tool_call(self, message: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        """Log a tool call.

        Args:
            message: Description of the tool call.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.log(TOOL_CALL, message, *args, **kwargs)


logging.setLoggerClass(CustomLogger)


def _truncate(obj: Any, max_len: int) -> Any:
    """Recursively truncate string values that exceed *max_len* characters."""
    if isinstance(obj, str):
        return obj[:max_len] + "[…]" if len(obj) > max_len else obj
    if isinstance(obj, dict):
        return {k: _truncate(v, max_len) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_truncate(item, max_len) for item in obj]
    return obj


def format_for_logging(
    data: Any,
    label: str = "",
    max_value_length: int = 1000,
) -> str:
    """Format a dict/object as pretty-printed JSON for log output.

    Args:
        data: The data to format (dict, list, or any JSON-serialisable value).
        label: Optional header label (e.g. ``"LLM Request"``).
        max_value_length: Truncate individual string values longer than this.
            Set to ``0`` to disable truncation.

    Returns:
        A multi-line string with an optional header and indented JSON.
    """
    display_data = _truncate(data, max_value_length) if max_value_length else data
    separator = "=" * 60
    try:
        body = json.dumps(display_data, indent=2, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        body = str(display_data)

    if label:
        return f"\n{separator}\n  {label}\n{separator}\n{body}"
    return f"\n{body}"


def get_logger(name: str) -> CustomLogger:
    """Get a named logger for a module.

    Args:
        name: Logger name, typically `__name__` of the calling module.

    Returns:
        A configured CustomLogger instance.
    """
    return typing.cast(CustomLogger, logging.getLogger(name))