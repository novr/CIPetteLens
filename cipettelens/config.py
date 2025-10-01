"""
Configuration module for CIPetteLens.
"""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Unified configuration management for CIPetteLens."""

    def __init__(self):
        """Initialize configuration with environment variables."""
        self._load_config()

    def _load_config(self) -> None:
        """Load all configuration values from environment variables."""
        # GitHub configuration
        self.GITHUB_TOKEN = self._get_env("GITHUB_TOKEN")
        self.TARGET_REPOSITORIES = self._get_repositories()

        # Flask configuration
        self.FLASK_DEBUG = self._get_bool("FLASK_DEBUG", False)
        self.FLASK_PORT = self._get_int("FLASK_PORT", 5000)

        # Database configuration
        self.DATABASE_PATH = self._get_env("DATABASE_PATH", "db/data.sqlite")

        # CIAnalyzer configuration
        self.CIANALYZER_IMAGE = self._get_env(
            "CIANALYZER_IMAGE", "kesin/ci_analyzer:latest"
        )
        self.CI_ANALYZER_DEBUG = self._get_bool("CI_ANALYZER_DEBUG", False)

        # Logging configuration
        self.LOG_LEVEL = self._get_env("LOG_LEVEL", "INFO")

        # Security configuration
        self.SECURE_FILE_PERMISSIONS = self._get_bool("SECURE_FILE_PERMISSIONS", True)

    def _get_env(self, key: str, default: str | None = None) -> str | None:
        """Get environment variable with optional default."""
        return os.getenv(key, default)

    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def _get_int(self, key: str, default: int) -> int:
        """Get integer environment variable."""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    def _get_repositories(self) -> list[str]:
        """Get target repositories from environment variable."""
        repos_str = os.getenv("TARGET_REPOSITORIES", "")
        if not repos_str:
            return []

        return [repo.strip() for repo in repos_str.split(",") if repo.strip()]

    def validate(self) -> bool:
        """Validate required configuration."""
        errors = []

        if not self.GITHUB_TOKEN:
            errors.append("GITHUB_TOKEN environment variable is required")

        if not self.TARGET_REPOSITORIES:
            errors.append("TARGET_REPOSITORIES environment variable is required")

        if self.FLASK_PORT < 1 or self.FLASK_PORT > 65535:
            errors.append("FLASK_PORT must be between 1 and 65535")

        if errors:
            raise ValueError("Configuration validation failed: " + "; ".join(errors))

        return True

    def get_database_path(self) -> Path:
        """Get database path as Path object."""
        return Path(self.DATABASE_PATH)

    def get_repositories_from_config(self) -> list[str]:
        """Get repositories from ci_analyzer.yaml file if available."""
        config_path = Path("ci_analyzer.yaml")
        if not config_path.exists():
            return self.TARGET_REPOSITORIES

        try:
            import yaml

            with open(config_path) as f:
                config = yaml.safe_load(f)

            repos = []
            for repo_config in config.get("github", {}).get("repos", []):
                repos.append(repo_config["name"])

            return repos if repos else self.TARGET_REPOSITORIES
        except Exception:
            return self.TARGET_REPOSITORIES

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            "flask_debug": self.FLASK_DEBUG,
            "flask_port": self.FLASK_PORT,
            "database_path": self.DATABASE_PATH,
            "cianalyzer_image": self.CIANALYZER_IMAGE,
            "ci_analyzer_debug": self.CI_ANALYZER_DEBUG,
            "log_level": self.LOG_LEVEL,
            "secure_file_permissions": self.SECURE_FILE_PERMISSIONS,
            "target_repositories_count": len(self.TARGET_REPOSITORIES),
            "has_github_token": bool(self.GITHUB_TOKEN),
        }


# Global configuration instance
config = Config()
