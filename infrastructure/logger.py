import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler


class Logger:
    """Enhanced logging utility with configurable output and rich formatting."""

    _logger: logging.Logger | None = None
    _console = Console()

    @classmethod
    def setup(
        cls,
        level: str = "INFO",
        log_file: str | None = None,
        console: bool = True,
        format_string: str | None = None,
    ):
        """Setup the logger with specified configuration."""
        if cls._logger is not None:
            return cls._logger

        cls._logger = logging.getLogger("email-sender")
        cls._logger.setLevel(getattr(logging, level.upper()))

        # Clear any existing handlers
        cls._logger.handlers.clear()

        # Console handler with rich formatting
        if console:
            console_handler = RichHandler(
                console=cls._console, show_time=True, show_path=False, markup=True
            )
            console_handler.setLevel(getattr(logging, level.upper()))
            cls._logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(getattr(logging, level.upper()))

            formatter = logging.Formatter(
                format_string or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            cls._logger.addHandler(file_handler)

        return cls._logger

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Get the configured logger instance."""
        if cls._logger is None:
            cls.setup()
        return cls._logger

    @classmethod
    def debug(cls, msg: str):
        """Log debug message."""
        cls.get_logger().debug(msg)

    @classmethod
    def info(cls, msg: str):
        """Log info message."""
        cls.get_logger().info(msg)

    @classmethod
    def warning(cls, msg: str):
        """Log warning message."""
        cls.get_logger().warning(msg)

    @classmethod
    def error(cls, msg: str):
        """Log error message."""
        cls.get_logger().error(msg)

    @classmethod
    def critical(cls, msg: str):
        """Log critical message."""
        cls.get_logger().critical(msg)

    @classmethod
    def success(cls, msg: str):
        """Log success message (info level with green formatting)."""
        cls.get_logger().info(f"[green]✓[/green] {msg}")

    @classmethod
    def exception(cls, msg: str):
        """Log exception with traceback."""
        cls.get_logger().exception(msg)
