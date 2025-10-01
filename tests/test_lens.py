"""
Tests for the lens module (legacy compatibility).
"""

from unittest.mock import MagicMock, patch

import pytest

from cipettelens.lens import collect_metrics


class TestLegacyLens:
    """Test legacy lens module compatibility."""

    @patch("cipettelens.cli.collect.collect_metrics")
    def test_main_calls_collect_metrics(self, mock_collect):
        """Test that main function calls collect_metrics."""
        from cipettelens.lens import main

        main()

        mock_collect.assert_called_once()

    @patch("cipettelens.cli.collect.collect_metrics")
    def test_collect_metrics_integration(self, mock_collect):
        """Test collect_metrics integration."""
        # This test verifies that the legacy interface still works
        collect_metrics()

        mock_collect.assert_called_once()
