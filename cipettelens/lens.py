"""
Lens module for running CIAnalyzer and processing results.
"""

import json
import sqlite3
import subprocess
from pathlib import Path

from dotenv import load_dotenv

from .config import Config
from .logger import logger
from .security import SecurityConfig

# Load environment variables
load_dotenv()


def generate_mock_data():
    """Generate mock CI/CD metrics data for testing."""
    import random
    from datetime import datetime, timedelta
    
    target_repos = Config.TARGET_REPOSITORIES
    mock_data = {
        "timestamp": datetime.now().isoformat(),
        "repositories": {}
    }
    
    for repo in target_repos:
        mock_data["repositories"][repo] = {
            "duration": {
                "average": round(random.uniform(5.0, 30.0), 2),
                "median": round(random.uniform(4.0, 25.0), 2),
                "p95": round(random.uniform(15.0, 45.0), 2)
            },
            "success_rate": round(random.uniform(0.85, 0.98), 3),
            "throughput": {
                "daily": random.randint(10, 50),
                "weekly": random.randint(70, 350)
            },
            "mttr": round(random.uniform(2.0, 8.0), 2),
            "builds": {
                "total": random.randint(100, 500),
                "successful": random.randint(85, 490),
                "failed": random.randint(5, 50)
            }
        }
    
    logger.info("Generated mock CI/CD metrics data")
    return mock_data


def run_cianalyzer():
    """Run CIAnalyzer via Docker and return the JSON output."""
    # Check if we should use mock data
    if Config.CIAnalyzer_IMAGE == "hello-world" or not Config.CIAnalyzer_IMAGE:
        logger.info("Using mock data for testing")
        return generate_mock_data()
    
    # Validate environment variables
    validation_errors = SecurityConfig.validate_environment()
    if validation_errors:
        error_msg = "Environment validation failed: " + "; ".join(
            f"{k}: {v}" for k, v in validation_errors.items()
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    github_token = Config.GITHUB_TOKEN
    target_repos = ",".join(Config.TARGET_REPOSITORIES)
    cianalyzer_image = Config.CIAnalyzer_IMAGE

    # Convert comma-separated repos to list
    repos = [repo.strip() for repo in target_repos.split(",")]

    logger.log_github_token_usage("data collection", repos)

    # Select token passing method based on configuration
    security_level = Config.TOKEN_SECURITY_LEVEL.lower()
    
    if security_level == "auto":
        # Try multiple secure token passing methods (ordered by security level)
        token_methods = [
            _run_with_token_file,      # Most secure: file mount with restricted permissions
            _run_with_stdin,           # Secure: passed via stdin
            _run_with_docker_secret,   # Secure: Docker secrets (if available)
            _run_with_env_var,         # Less secure: environment variable
        ]

        last_error = None
        for method in token_methods:
            try:
                logger.info(f"Trying token method: {method.__name__}")
                return method(github_token, repos, cianalyzer_image)
            except Exception as e:
                logger.warning(f"Token method {method.__name__} failed: {e}")
                last_error = e
                continue

        # If all methods fail, raise the last error
        raise RuntimeError(f"All token passing methods failed. Last error: {last_error}")
    
    elif security_level == "file":
        return _run_with_token_file(github_token, repos, cianalyzer_image)
    elif security_level == "stdin":
        return _run_with_stdin(github_token, repos, cianalyzer_image)
    elif security_level == "secret":
        return _run_with_docker_secret(github_token, repos, cianalyzer_image)
    elif security_level == "env":
        return _run_with_env_var(github_token, repos, cianalyzer_image)
    else:
        raise ValueError(f"Invalid TOKEN_SECURITY_LEVEL: {security_level}. Must be one of: auto, file, stdin, secret, env")


def _run_with_token_file(github_token: str, repos: list[str], cianalyzer_image: str) -> dict:
    """Run CIAnalyzer with token file mount (most secure)."""
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
            cianalyzer_image,
            "--repositories",
            ",".join(repos),
            "--output",
            "json",
        ]

        logger.log_docker_command(cmd, repos)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        logger.info("CIAnalyzer execution completed successfully (token file method)")
        return json.loads(result.stdout)
    finally:
        # Securely clean up the temporary token file
        SecurityConfig.secure_cleanup(token_file_path)


def _run_with_stdin(github_token: str, repos: list[str], cianalyzer_image: str) -> dict:
    """Run CIAnalyzer with token passed via stdin (secure)."""
    # Run CIAnalyzer via Docker with token passed via stdin
    cmd = [
        "docker",
        "run",
        "--rm",
        "-i",
        "-e",
        "GITHUB_TOKEN_FILE=/dev/stdin",
        cianalyzer_image,
        "--repositories",
        ",".join(repos),
        "--output",
        "json",
    ]

    logger.log_docker_command(cmd, repos)
    result = subprocess.run(
        cmd, 
        input=github_token, 
        capture_output=True, 
        text=True, 
        check=True
    )

    logger.info("CIAnalyzer execution completed successfully (stdin method)")
    return json.loads(result.stdout)


def _run_with_docker_secret(github_token: str, repos: list[str], cianalyzer_image: str) -> dict:
    """Run CIAnalyzer with token passed via Docker secrets (secure, requires Docker Swarm)."""
    # Create a secure temporary file for the GitHub token
    token_file_path = SecurityConfig.create_secure_temp_file(github_token, ".token")

    try:
        # Create Docker secret (requires Docker Swarm mode)
        secret_name = "github_token_secret"
        
        # Try to create secret
        create_secret_cmd = [
            "docker",
            "secret",
            "create",
            secret_name,
            token_file_path,
        ]
        
        # Check if Docker Swarm is available
        result = subprocess.run(create_secret_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Docker Swarm not available or secret creation failed: {result.stderr}")

        # Run CIAnalyzer with Docker secret
        cmd = [
            "docker",
            "run",
            "--rm",
            "--secret",
            f"source={secret_name},target=/run/secrets/github_token",
            "-e",
            "GITHUB_TOKEN_FILE=/run/secrets/github_token",
            cianalyzer_image,
            "--repositories",
            ",".join(repos),
            "--output",
            "json",
        ]

        logger.log_docker_command(cmd, repos)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        logger.info("CIAnalyzer execution completed successfully (Docker secret method)")
        return json.loads(result.stdout)
    finally:
        # Clean up secret and temporary file
        try:
            subprocess.run(["docker", "secret", "rm", secret_name], capture_output=True)
        except Exception:
            pass
        SecurityConfig.secure_cleanup(token_file_path)


def _run_with_env_var(github_token: str, repos: list[str], cianalyzer_image: str) -> dict:
    """Run CIAnalyzer with token passed via environment variable (less secure)."""
    # Run CIAnalyzer via Docker with token in environment variable
    cmd = [
        "docker",
        "run",
        "--rm",
        "-e",
        f"GITHUB_TOKEN={github_token}",
        cianalyzer_image,
        "--repositories",
        ",".join(repos),
        "--output",
        "json",
    ]

    logger.log_docker_command(cmd, repos)
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    logger.info("CIAnalyzer execution completed successfully (env var method)")
    return json.loads(result.stdout)


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

        # Insert metrics from the data
        if "repositories" in data:
            for repo, metrics in data["repositories"].items():
                # Insert duration metrics
                if "duration" in metrics:
                    cursor.execute(
                        "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                        (repo, "duration_average", metrics["duration"]["average"])
                    )
                    cursor.execute(
                        "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                        (repo, "duration_median", metrics["duration"]["median"])
                    )
                    cursor.execute(
                        "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                        (repo, "duration_p95", metrics["duration"]["p95"])
                    )
                
                # Insert success rate
                if "success_rate" in metrics:
                    cursor.execute(
                        "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                        (repo, "success_rate", metrics["success_rate"])
                    )
                
                # Insert throughput metrics
                if "throughput" in metrics:
                    cursor.execute(
                        "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                        (repo, "throughput_daily", metrics["throughput"]["daily"])
                    )
                    cursor.execute(
                        "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                        (repo, "throughput_weekly", metrics["throughput"]["weekly"])
                    )
                
                # Insert MTTR
                if "mttr" in metrics:
                    cursor.execute(
                        "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                        (repo, "mttr", metrics["mttr"])
                    )
                
                # Insert build metrics
                if "builds" in metrics:
                    cursor.execute(
                        "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                        (repo, "builds_total", metrics["builds"]["total"])
                    )
                    cursor.execute(
                        "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                        (repo, "builds_successful", metrics["builds"]["successful"])
                    )
                    cursor.execute(
                        "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                        (repo, "builds_failed", metrics["builds"]["failed"])
                    )

        conn.commit()
        logger.info(f"Database schema initialized and data saved at: {db_path}")

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
