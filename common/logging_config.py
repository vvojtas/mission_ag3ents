"""Colored logging configuration for the project.

Provides distinct colors for different event types so that console
output is easy to scan at a glance:

- **LLM Request** (cyan)   — messages sent to the LLM
- **LLM Response** (green)  — messages received from the LLM
- **Task Hub** (yellow)     — task platform API interactions
- **Error** (red)           — errors and exceptions
- **General** (white)       — default informational messages
"""

import logging
import sys

from colorama import Fore, Style, init as colorama_init


# Initialize colorama for Windows compatibility
colorama_init(autoreset=True)


# Custom log level for LLM-specific events
LLM_REQUEST = 25
LLM_RESPONSE = 26
TASK_HUB = 27

logging.addLevelName(LLM_REQUEST, "LLM_REQ")
logging.addLevelName(LLM_RESPONSE, "LLM_RES")
logging.addLevelName(TASK_HUB, "TASK_HUB")


_COLOR_MAP: dict[int, str] = {
    LLM_REQUEST: Fore.CYAN,
    LLM_RESPONSE: Fore.GREEN,
    TASK_HUB: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.RED + Style.BRIGHT,
    logging.WARNING: Fore.MAGENTA,
    logging.INFO: Fore.WHITE,
    logging.DEBUG: Fore.LIGHTBLACK_EX,
}


class ColoredFormatter(logging.Formatter):
    """Formatter that applies colors based on log level.

    Each log level maps to a distinct color for quick visual
    identification in the console.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with the appropriate color.

        Args:
            record: The log record to format.

        Returns:
            The formatted, colored log string.
        """
        color = _COLOR_MAP.get(record.levelno, Fore.WHITE)
        timestamp = self.formatTime(record, self.datefmt)
        level = record.levelname
        message = record.getMessage()
        return f"{color}{timestamp} | {level:<8} | {message}{Style.RESET_ALL}"


def setup_logging(level: int = logging.DEBUG) -> None:
    """Configure the root logger with colored console output.

    Sets up a single StreamHandler with the ColoredFormatter.
    Call this once at application startup.

    Args:
        level: Minimum log level to display. Defaults to DEBUG.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers on repeated calls
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(
            ColoredFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        )
        root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger for a module.

    Args:
        name: Logger name, typically `__name__` of the calling module.

    Returns:
        A configured Logger instance.
    """
    return logging.getLogger(name)


# --- Convenience functions for typed logging ---


def log_llm_request(logger: logging.Logger, message: str) -> None:
    """Log an outgoing LLM request.

    Args:
        logger: The logger instance to use.
        message: Description of the request being sent.
    """
    logger.log(LLM_REQUEST, message)


def log_llm_response(logger: logging.Logger, message: str) -> None:
    """Log an incoming LLM response.

    Args:
        logger: The logger instance to use.
        message: Description of the response received.
    """
    logger.log(LLM_RESPONSE, message)


def log_task_hub(logger: logging.Logger, message: str) -> None:
    """Log a task platform API interaction.

    Args:
        logger: The logger instance to use.
        message: Description of the task hub event.
    """
    logger.log(TASK_HUB, message)
