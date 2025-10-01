"""
Lens module for running CIAnalyzer and processing results.
"""

import json
import os
import sqlite3
import subprocess
from pathlib import Path

from dotenv import load_dotenv

from .logger import logger
from .security import SecurityConfig

# Load environment variables
load_dotenv()


def run_cianalyzer():
    """Run CIAnalyzer via Docker and return the JSON output."""
    # Validate environment variables
    validation_errors = SecurityConfig.validate_environment()
    if validation_errors:
        error_msg = "Environment validation failed: " + "; ".join(
            f"{k}: {v}" for k, v in validation_errors.items()
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    github_token = os.getenv("GITHUB_TOKEN")
    target_repos = os.getenv("TARGET_REPOSITORIES", "")

    # Convert comma-separated repos to list
    repos = [repo.strip() for repo in target_repos.split(",")]

    logger.log_github_token_usage("data collection", repos)

    # Create a secure temporary file for the GitHub token
    token_file_path = SecurityConfig.create_secure_temp_file(github_token, ".token")

    try:
        # Run CIAnalyzer via Docker with token file mount
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{token_file_path}:/tmp/github_token:ro",
            "-e",
            "GITHUB_TOKEN_FILE=/tmp/github_token",
            "kesin11/cianalyzer:latest",
            "--repositories",
            ",".join(repos),
            "--output",
            "json",
        ]

        logger.log_docker_command(cmd, repos)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        logger.info("CIAnalyzer execution completed successfully")
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"CIAnalyzer execution failed: {e.stderr}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse CIAnalyzer output as JSON: {e}")
        raise
    finally:
        # Securely clean up the temporary token file
        SecurityConfig.secure_cleanup(token_file_path)


def save_to_database(data):
    """Save CIAnalyzer results to SQLite database."""
    db_path = Path("db/data.sqlite")
    db_path.parent.mkdir(exist_ok=True)

    # Set secure permissions on database directory
    db_path.parent.chmod(0o700)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repository TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Insert metrics (this is a simplified example)
        # In a real implementation, you would parse the CIAnalyzer JSON output
        # and extract specific metrics like duration, success rate, etc.

        conn.commit()
        logger.info(f"Database schema initialized at: {db_path}")

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if "conn" in locals():
            conn.close()

    # Set secure permissions on database file
    db_path.chmod(0o600)
    logger.info(f"Database file created with secure permissions: {db_path}")


def main():
    """Main entry point for data collection."""
    try:
        logger.info("Starting CIAnalyzer data collection...")
        data = run_cianalyzer()
        save_to_database(data)
        logger.info("Data collection completed successfully!")
    except Exception as e:
        logger.error(f"Error during data collection: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
