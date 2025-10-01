"""
Configuration module for CIPetteLens.
"""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration class."""

    # GitHub configuration
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    TARGET_REPOSITORIES = [
        repo.strip()
        for repo in os.getenv("TARGET_REPOSITORIES", "").split(",")
        if repo.strip()
    ]

    # Flask configuration
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

    # Database configuration
    DATABASE_PATH = os.getenv("DATABASE_PATH", "db/data.sqlite")

    # CIAnalyzer configuration
    CIAnalyzer_IMAGE = os.getenv("CIANALYZER_IMAGE", "kesin11/cianalyzer:latest")

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN environment variable is required")

        if not cls.TARGET_REPOSITORIES or not any(cls.TARGET_REPOSITORIES):
            raise ValueError("TARGET_REPOSITORIES environment variable is required")

        return True
