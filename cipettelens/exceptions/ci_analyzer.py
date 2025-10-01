"""
CIAnalyzer related exceptions.
"""

from .base import CIPetteLensException


class CIAnalyzerException(CIPetteLensException):
    """Base exception for CIAnalyzer operations."""

    pass


class CIAnalyzerExecutionError(CIAnalyzerException):
    """Exception raised when CIAnalyzer execution fails."""

    def __init__(
        self, message: str, exit_code: int | None = None, stderr: str | None = None
    ):
        super().__init__(message, "CIANALYZER_EXECUTION_ERROR")
        self.exit_code = exit_code
        self.stderr = stderr
