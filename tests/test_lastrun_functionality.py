"""
Tests for last_run functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from cipettelens.external.ci_analyzer import CIAnalyzerClient


class TestLastRunFunctionality:
    """Test last_run directory and file creation."""

    def test_ensure_lastrun_directories(self):
        """Test that last_run directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                client = CIAnalyzerClient()
                client._ensure_lastrun_directories()

                # Check that directories were created
                assert Path(".ci_analyzer").exists()
                assert Path(".ci_analyzer/last_run").exists()

            finally:
                os.chdir(original_cwd)

    def test_verify_lastrun_file_exists(self):
        """Test verification when last_run file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                # Create the directory structure
                Path(".ci_analyzer/last_run").mkdir(parents=True, exist_ok=True)

                # Create a mock last_run file
                last_run_file = Path(".ci_analyzer/last_run/github.json")
                test_data = {"last_run": "2024-01-01T00:00:00Z", "repos": []}
                last_run_file.write_text(json.dumps(test_data))

                client = CIAnalyzerClient()
                # This should not raise an exception
                client._verify_lastrun_file()

                # Verify file still exists
                assert last_run_file.exists()

            finally:
                os.chdir(original_cwd)

    def test_verify_lastrun_file_missing(self):
        """Test verification when last_run file is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                # Create the directory structure but no file
                Path(".ci_analyzer/last_run").mkdir(parents=True, exist_ok=True)

                client = CIAnalyzerClient()
                # This should log a warning but not raise an exception
                client._verify_lastrun_file()

                # Verify file does not exist
                last_run_file = Path(".ci_analyzer/last_run/github.json")
                assert not last_run_file.exists()

            finally:
                os.chdir(original_cwd)

    @patch("cipettelens.external.ci_analyzer.subprocess.run")
    def test_run_cianalyzer_creates_directories(self, mock_run):
        """Test that running CIAnalyzer creates required directories."""
        # Mock successful subprocess execution
        mock_result = type(
            "MockResult",
            (),
            {"stdout": '{"repositories": {}}', "stderr": "", "returncode": 0},
        )()
        mock_run.return_value = mock_result

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                # Use a real image name to avoid mock data path
                client = CIAnalyzerClient(image="kesin/ci_analyzer:latest")
                client.collect_metrics(["test/repo"], "fake_token")

                # Check that directories were created
                assert Path(".ci_analyzer").exists()
                assert Path(".ci_analyzer/last_run").exists()

            finally:
                os.chdir(original_cwd)

    def test_lastrun_file_structure(self):
        """Test the expected structure of last_run file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                # Create directory structure
                Path(".ci_analyzer/last_run").mkdir(parents=True, exist_ok=True)

                # Create a properly structured last_run file
                last_run_file = Path(".ci_analyzer/last_run/github.json")
                test_data = {
                    "last_run": "2024-01-01T00:00:00Z",
                    "repos": {
                        "test/repo": {
                            "last_analyzed": "2024-01-01T00:00:00Z",
                            "workflow_runs": 10,
                        }
                    },
                }
                last_run_file.write_text(json.dumps(test_data, indent=2))

                # Verify file can be read and parsed
                assert last_run_file.exists()
                with open(last_run_file) as f:
                    data = json.load(f)
                    assert "last_run" in data
                    assert "repos" in data
                    assert data["repos"]["test/repo"]["workflow_runs"] == 10

            finally:
                os.chdir(original_cwd)
