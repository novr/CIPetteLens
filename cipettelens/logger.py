"""
Logging configuration for CIPetteLens.
"""

import logging
import sys
from pathlib import Path

from .config import config


class SecureLogger:
    """Secure logging wrapper that masks sensitive information."""

    def __init__(self, name: str, log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Set up logging handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "cipettelens.log")
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def _mask_sensitive_data(self, message: str) -> str:
        """Mask sensitive data in log messages."""
        # Common patterns to mask
        patterns_to_mask = [
            r"GITHUB_TOKEN=[^\s]+",
            r'token["\']?\s*[:=]\s*["\']?[^\s"\']+["\']?',
            r'password["\']?\s*[:=]\s*["\']?[^\s"\']+["\']?',
            r'secret["\']?\s*[:=]\s*["\']?[^\s"\']+["\']?',
        ]

        import re

        for pattern in patterns_to_mask:
            message = re.sub(
                pattern, lambda m: m.group(0).split("=")[0] + "=***MASKED***", message
            )

        return message

    def debug(self, message: str, *args, **kwargs):
        """Log debug message with sensitive data masked."""
        masked_message = self._mask_sensitive_data(message)
        self.logger.debug(masked_message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log info message with sensitive data masked."""
        masked_message = self._mask_sensitive_data(message)
        self.logger.info(masked_message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message with sensitive data masked."""
        masked_message = self._mask_sensitive_data(message)
        self.logger.warning(masked_message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message with sensitive data masked."""
        masked_message = self._mask_sensitive_data(message)
        self.logger.error(masked_message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message with sensitive data masked."""
        masked_message = self._mask_sensitive_data(message)
        self.logger.critical(masked_message, *args, **kwargs)

    def log_github_token_usage(self, action: str, repositories: list[str]):
        """Log GitHub token usage without exposing the token."""
        self.info(
            f"GitHub token used for {action} on repositories: {', '.join(repositories)}"
        )

    def log_docker_command(self, command: list[str], repositories: list[str]):
        """Log Docker command execution without exposing sensitive data."""
        # Create a safe version of the command for logging
        safe_command = []
        for arg in command:
            if arg.startswith("GITHUB_TOKEN="):
                safe_command.append("GITHUB_TOKEN=***MASKED***")
            else:
                safe_command.append(arg)

        self.info(f"Executing Docker command: {' '.join(safe_command)}")
        self.info(f"Target repositories: {', '.join(repositories)}")


# Global logger instance
logger = SecureLogger("cipettelens", config.LOG_LEVEL or "INFO")
