"""
Tests for the lens module (legacy compatibility).
"""

from unittest.mock import patch


class TestLegacyLens:
    """Test legacy lens module compatibility."""

    def test_main_calls_collect_metrics(self):
        """Test that main function calls collect_metrics."""
        with patch("cipettelens.cli.collect.collect_metrics") as mock_collect:
            mock_collect.return_value = None

            from cipettelens.lens import main

            main()

            mock_collect.assert_called_once()

    def test_collect_metrics_integration(self):
        """Test collect_metrics integration."""
        # Test that the function is properly imported
        from cipettelens.lens import collect_metrics

        # Verify it's callable
        assert callable(collect_metrics)
