"""
CIAnalyzer external service client.
"""

import json
import subprocess
from pathlib import Path

from ..config import config
from ..exceptions.ci_analyzer import CIAnalyzerExecutionError
from ..logger import logger
from ..models.ci_metrics import CIMetrics


class CIAnalyzerClient:
    """Client for CIAnalyzer external service."""

    def __init__(self, image: str | None = None, debug: bool | None = None):
        """Initialize CIAnalyzer client."""
        self.image = image or config.CIANALYZER_IMAGE
        self.debug = debug if debug is not None else config.CI_ANALYZER_DEBUG

    def collect_metrics(self, repositories: list[str], github_token: str) -> CIMetrics:
        """Collect CI metrics from CIAnalyzer."""
        # Check if we should use mock data
        if self.image == "hello-world" or not self.image:
            logger.info("Using mock data for testing")
            from .mock_data import MockDataGenerator

            generator = MockDataGenerator()
            return generator.generate_metrics(repositories)

        # Validate environment
        self._validate_environment(github_token, repositories)

        # Run CIAnalyzer
        result = self._run_cianalyzer(github_token)

        # Parse and return metrics
        return CIMetrics.from_dict(result)

    def _validate_environment(self, github_token: str, repositories: list[str]) -> None:
        """Validate environment for CIAnalyzer execution."""
        if not github_token:
            raise CIAnalyzerExecutionError("GITHUB_TOKEN is required")

        if not repositories:
            raise CIAnalyzerExecutionError("No repositories provided")

    def _run_cianalyzer(self, github_token: str) -> dict:
        """Run CIAnalyzer via Docker."""
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
        if self.debug:
            cmd.extend(["-e", "CI_ANALYZER_DEBUG=1"])

        if self.image is None:
            raise ValueError("CIAnalyzer image is not configured")
        cmd.extend([self.image, "-c", "ci_analyzer.yaml"])

        # Add --debug flag if debug mode is enabled
        if self.debug:
            cmd.append("--debug")

        logger.info(f"Executing CIAnalyzer: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                input=github_token,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,  # 5 minute timeout
            )

            logger.info("CIAnalyzer execution completed successfully")
            return json.loads(result.stdout)

        except subprocess.TimeoutExpired as e:
            raise CIAnalyzerExecutionError(
                f"CIAnalyzer execution timed out after 5 minutes: {e}",
                stderr=e.stderr.decode() if e.stderr else None,
            ) from e
        except subprocess.CalledProcessError as e:
            raise CIAnalyzerExecutionError(
                f"CIAnalyzer execution failed with exit code {e.returncode}: {e}",
                exit_code=e.returncode,
                stderr=e.stderr.decode() if e.stderr else None,
            ) from e
        except json.JSONDecodeError as e:
            raise CIAnalyzerExecutionError(
                f"Failed to parse CIAnalyzer output as JSON: {e}"
            ) from e
        except Exception as e:
            raise CIAnalyzerExecutionError(
                f"Unexpected error during CIAnalyzer execution: {e}"
            ) from e
