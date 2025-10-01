"""
Lens module for running CIAnalyzer and processing results.
"""

import json
import os
import sqlite3
import subprocess
import yaml
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
    cianalyzer_image = Config.CIAnalyzer_IMAGE

    # Get repositories from ci_analyzer.yaml
    repos = _get_repos_from_config()
    logger.log_github_token_usage("data collection", repos)

    # Use stdin method for token passing with ci_analyzer.yaml
    return _run_with_stdin_and_config(github_token, cianalyzer_image)


def _get_repos_from_config() -> list[str]:
    """Get repository list from ci_analyzer.yaml file."""
    config_path = Path("ci_analyzer.yaml")
    if not config_path.exists():
        raise FileNotFoundError("ci_analyzer.yaml file not found")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    repos = []
    for repo_config in config.get('github', {}).get('repos', []):
        repos.append(repo_config['name'])
    
    return repos


def _run_with_stdin_and_config(github_token: str, cianalyzer_image: str) -> dict:
    """Run CIAnalyzer with token passed via stdin and ci_analyzer.yaml config."""
    # Check for debug mode
    debug_mode = os.getenv("CI_ANALYZER_DEBUG", "0")
    use_debug = debug_mode.lower() in ("1", "true", "yes", "on")
    
    # Run CIAnalyzer via Docker with token passed via stdin and config file
    cmd = [
        "docker",
        "run",
        "--rm",
        "-i",
        "-v",
        f"{Path.cwd()}:/app",
        "-w",
        "/app",
        "-e",
        "GITHUB_TOKEN_FILE=/dev/stdin",
    ]
    
    # Add debug environment variable if enabled
    if use_debug:
        cmd.extend(["-e", "CI_ANALYZER_DEBUG=1"])
    
    cmd.extend([cianalyzer_image, "-c", "ci_analyzer.yaml"])
    
    # Add --debug flag if debug mode is enabled
    if use_debug:
        cmd.append("--debug")

    logger.info(f"Executing Docker command: {' '.join(cmd)}")
    result = subprocess.run(
        cmd, 
        input=github_token, 
        capture_output=True, 
        text=True, 
        check=True
    )

    logger.info("CIAnalyzer execution completed successfully (stdin + config method)")
    return json.loads(result.stdout)


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
