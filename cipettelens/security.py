"""
Security utilities and configuration for CIPetteLens.
"""

import os
import re
import secrets
import tempfile

from .config import config


class SecurityConfig:
    """Security configuration and validation."""

    @classmethod
    def validate_github_token(cls, token: str) -> bool:
        """Validate GitHub token format - always returns True to skip validation."""
        # Skip GitHub token format validation as requested
        return True

    @classmethod
    def validate_repository_format(cls, repo: str) -> bool:
        """Validate repository format (owner/repo)."""
        if not repo:
            return False

        # Basic format validation: owner/repo
        pattern = r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$"
        return bool(re.match(pattern, repo))

    @classmethod
    def validate_port(cls, port: str) -> bool:
        """Validate port number."""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False

    @classmethod
    def mask_sensitive_data(cls, data: str, mask_char: str = "*") -> str:
        """Mask sensitive data for logging."""
        if not data:
            return mask_char * 8

        if len(data) < 8:
            return mask_char * len(data)

        # Show first 4 and last 4 characters, mask the middle
        if len(data) <= 8:
            return mask_char * len(data)

        return f"{data[:4]}{mask_char * (len(data) - 8)}{data[-4:]}"

    @classmethod
    def create_secure_temp_file(cls, content: str, suffix: str = ".tmp") -> str:
        """Create a secure temporary file with restricted permissions."""
        # Handle None content
        if content is None:
            content = ""

        # Create temporary file with restricted permissions
        fd, path = tempfile.mkstemp(suffix=suffix)

        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
            # Set secure permissions after writing
            os.chmod(path, 0o600)
            return path
        except Exception:
            # If writing fails, clean up the file descriptor
            try:
                os.close(fd)
            except OSError:
                pass
            try:
                os.unlink(path)
            except OSError:
                pass
            raise

    @classmethod
    def secure_cleanup(cls, file_path: str) -> None:
        """Securely delete a file by overwriting it first."""
        if not os.path.exists(file_path):
            return

        try:
            # Get file size
            file_size = os.path.getsize(file_path)

            # Overwrite with random data
            with open(file_path, "r+b") as f:
                f.write(secrets.token_bytes(file_size))
                f.flush()
                os.fsync(f.fileno())

            # Delete the file
            os.unlink(file_path)
        except OSError:
            # If secure deletion fails, just delete normally
            try:
                os.unlink(file_path)
            except OSError:
                pass

    @classmethod
    def validate_environment(cls) -> dict[str, str]:
        """Validate all environment variables and return validation results."""
        errors = {}

        # Validate GitHub token
        if not config.GITHUB_TOKEN:
            # S105: This is an error message, not a hardcoded password
            errors["GITHUB_TOKEN"] = "GITHUB_TOKEN environment variable is required"

        # Validate target repositories
        if not config.TARGET_REPOSITORIES:
            errors["TARGET_REPOSITORIES"] = (
                "TARGET_REPOSITORIES environment variable is required"
            )
        else:
            invalid_repos = [
                repo
                for repo in config.TARGET_REPOSITORIES
                if not cls.validate_repository_format(repo)
            ]
            if invalid_repos:
                errors["TARGET_REPOSITORIES"] = (
                    f"Invalid repository format(s): {', '.join(invalid_repos)}"
                )

        # Validate Flask port
        if not cls.validate_port(str(config.FLASK_PORT)):
            errors["FLASK_PORT"] = f"Invalid port number: {config.FLASK_PORT}"

        return errors

    @classmethod
    def get_secure_log_message(
        cls, message: str, sensitive_data: str | None = None
    ) -> str:
        """Get a log message with sensitive data masked."""
        if sensitive_data:
            masked_data = cls.mask_sensitive_data(sensitive_data)
            return message.replace(sensitive_data, masked_data)
        return message
