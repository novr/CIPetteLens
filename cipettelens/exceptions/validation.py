"""
Validation related exceptions.
"""

from .base import CIPetteLensException


class ValidationException(CIPetteLensException):
    """Base exception for validation errors."""

    pass


class ConfigurationError(ValidationException):
    """Exception raised when configuration validation fails."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, "CONFIGURATION_ERROR")
        self.field = field
