"""
Tests for the lens module.
"""

from unittest.mock import MagicMock, patch

import pytest

from cipettelens.lens import run_cianalyzer, save_to_database


class TestCIAnalyzer:
    """Test CIAnalyzer integration."""

    @patch("cipettelens.lens.subprocess.run")
    @patch.dict(
        "os.environ",
        {
            "GITHUB_TOKEN": "ghp_1234567890abcdef1234567890abcdef12345678",
            "TARGET_REPOSITORIES": "owner/repo1,owner/repo2",
        },
    )
    def test_run_cianalyzer_success(self, mock_run):
        """Test successful CIAnalyzer execution."""
        # Mock successful subprocess execution
        mock_result = MagicMock()
        mock_result.stdout = '{"repositories": [], "metrics": {}}'
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = run_cianalyzer()

        assert result == {"repositories": [], "metrics": {}}
        mock_run.assert_called_once()

    @patch.dict("os.environ", {}, clear=True)
    def test_run_cianalyzer_missing_token(self):
        """Test CIAnalyzer execution with missing token."""
        with pytest.raises(
            ValueError, match="GITHUB_TOKEN environment variable is required"
        ):
            run_cianalyzer()

    @patch.dict(
        "os.environ",
        {"GITHUB_TOKEN": "ghp_1234567890abcdef1234567890abcdef12345678"},
        clear=True,
    )
    def test_run_cianalyzer_missing_repos(self):
        """Test CIAnalyzer execution with missing repositories."""
        with pytest.raises(
            ValueError, match="TARGET_REPOSITORIES environment variable is required"
        ):
            run_cianalyzer()


class TestDatabase:
    """Test database operations."""

    @patch("cipettelens.lens.sqlite3.connect")
    @patch("cipettelens.lens.Path")
    def test_save_to_database(self, mock_path, mock_connect):
        """Test saving data to database."""
        # Mock Path behavior
        mock_path_instance = MagicMock()
        mock_path_instance.parent.mkdir = MagicMock()
        mock_path_instance.chmod = MagicMock()
        mock_path.return_value = mock_path_instance

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        test_data = {"test": "data"}
        save_to_database(test_data)

        mock_connect.assert_called_once()
        # Check that cursor.execute was called (for CREATE TABLE)
        assert mock_cursor.execute.call_count >= 1
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        mock_path_instance.chmod.assert_called_with(0o600)
