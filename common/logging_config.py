"""Colored logging configuration for the project.

Provides distinct colors for different event types so that console
output is easy to scan at a glance:

- **LLM Request** (cyan)   — messages sent to the LLM
- **LLM Response** (green)  — messages received from the LLM
- **Task Hub** (blue)     — task platform API interactions
- **Cost Tracker** (yellow)     — cost tracker events
- **Error** (red)           — errors and exceptions
- **General** (white)       — default informational messages
"""

import logging
import sys
import typing

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
        level = record.levelname
        message = record.getMessage()
        
        if record.levelno == COST:
            return f"{color}{message}{Style.RESET_ALL}"

        timestamp = self.formatTime(record, self.datefmt)
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


def get_logger(name: str) -> CustomLogger:
    """Get a named logger for a module.

    Args:
        name: Logger name, typically `__name__` of the calling module.

    Returns:
        A configured CustomLogger instance.
    """
    return typing.cast(CustomLogger, logging.getLogger(name))