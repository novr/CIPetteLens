"""
Tests for CLI module.
"""

from unittest.mock import MagicMock, patch

import pytest

from cipettelens.cli.collect import collect_metrics


class TestCollectCLI:
    """Test collect CLI functionality."""

    @patch("cipettelens.cli.collect.SQLiteMetricsRepository")
    @patch("cipettelens.cli.collect.MetricsService")
    @patch("cipettelens.cli.collect.CollectMetricsUseCase")
    @patch("cipettelens.cli.collect.logger")
    def test_collect_metrics_success(
        self, mock_logger, mock_use_case_class, mock_service_class, mock_repo_class
    ):
        """Test successful metrics collection."""
        # Setup mocks
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        mock_use_case = MagicMock()
        mock_metrics = MagicMock()
        mock_metrics.repositories = [MagicMock(), MagicMock()]
        mock_use_case.execute.return_value = mock_metrics
        mock_use_case_class.return_value = mock_use_case

        # Execute
        collect_metrics()

        # Verify
        mock_repo_class.assert_called_once()
        mock_service_class.assert_called_once_with(mock_repo)
        mock_use_case_class.assert_called_once_with(mock_service)
        mock_use_case.execute.assert_called_once()
        mock_logger.info.assert_called()
        mock_logger.info.assert_any_call("Starting CIAnalyzer data collection...")
        mock_logger.info.assert_any_call(
            "Data collection completed successfully! Collected metrics for 2 repositories"
        )

    @patch("cipettelens.cli.collect.SQLiteMetricsRepository")
    @patch("cipettelens.cli.collect.MetricsService")
    @patch("cipettelens.cli.collect.CollectMetricsUseCase")
    @patch("cipettelens.cli.collect.logger")
    def test_collect_metrics_error(
        self, mock_logger, mock_use_case_class, mock_service_class, mock_repo_class
    ):
        """Test metrics collection with error."""
        # Setup mocks
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        mock_use_case = MagicMock()
        mock_use_case.execute.side_effect = Exception("Test error")
        mock_use_case_class.return_value = mock_use_case

        # Execute and verify exception is raised
        with pytest.raises(Exception, match="Test error"):
            collect_metrics()

        # Verify error logging
        mock_logger.error.assert_called_with("Error during data collection: Test error")
