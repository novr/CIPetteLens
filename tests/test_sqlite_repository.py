"""
Tests for SQLiteMetricsRepository.
"""

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from cipettelens.models.ci_metrics import (
    BuildMetrics,
    CIMetrics,
    DurationMetrics,
    RepositoryMetrics,
    ThroughputMetrics,
)
from cipettelens.repositories.sqlite_metrics import SQLiteMetricsRepository


class TestSQLiteMetricsRepository:
    """Test SQLiteMetricsRepository class."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Clean up
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def repository(self, temp_db_path):
        """Create a repository instance with temporary database."""
        return SQLiteMetricsRepository(db_path=temp_db_path)

    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics for testing."""
        repo_metrics = RepositoryMetrics(
            repository="test/repo",
            duration=DurationMetrics(average=120.5, median=110.0, p95=180.0),
            throughput=ThroughputMetrics(daily=5.2, weekly=35.0),
            builds=BuildMetrics(total=100, successful=95, failed=5),
            mttr=45.5,
            success_rate=0.95,
            timestamp=datetime.now(),
        )
        return CIMetrics(repositories=[repo_metrics])

    def test_init_creates_database(self, temp_db_path):
        """Test that initialization creates the database file."""
        repository = SQLiteMetricsRepository(db_path=temp_db_path)
        assert Path(temp_db_path).exists()

    def test_save_metrics(self, repository, sample_metrics):
        """Test saving metrics to database."""
        repository.save_metrics(sample_metrics)

        # Verify data was saved by checking if we can retrieve it
        metrics = repository.get_metrics_by_repository("test/repo")
        assert len(metrics) == 1
        assert metrics[0].repository == "test/repo"
        assert metrics[0].duration is not None
        assert metrics[0].throughput is not None
        assert metrics[0].builds is not None

    def test_get_metrics_by_repository(self, repository, sample_metrics):
        """Test getting metrics by repository."""
        repository.save_metrics(sample_metrics)

        metrics = repository.get_metrics_by_repository("test/repo")
        assert len(metrics) == 1
        assert metrics[0].repository == "test/repo"
        assert metrics[0].duration.average == 120.5
        assert metrics[0].throughput.daily == 5.2
        assert metrics[0].builds.total == 100
        assert metrics[0].mttr == 45.5
        assert metrics[0].success_rate == 0.95

    def test_get_metrics_by_repository_not_found(self, repository):
        """Test getting metrics for non-existent repository."""
        metrics = repository.get_metrics_by_repository("nonexistent/repo")
        assert metrics == []

    def test_get_all_metrics(self, repository, sample_metrics):
        """Test getting all metrics."""
        repository.save_metrics(sample_metrics)

        metrics = repository.get_all_metrics()
        assert len(metrics) == 1
        assert metrics[0].repository == "test/repo"

    def test_get_metrics_by_metric_name(self, repository, sample_metrics):
        """Test getting metrics by metric name."""
        repository.save_metrics(sample_metrics)

        # Test getting duration metrics
        metrics = repository.get_metrics_by_metric_name("duration_average")
        assert len(metrics) == 1
        assert metrics[0].repository == "test/repo"

    def test_get_latest_metrics_by_repository(self, repository, sample_metrics):
        """Test getting latest metrics for a repository."""
        repository.save_metrics(sample_metrics)

        latest = repository.get_latest_metrics_by_repository("test/repo")
        assert latest is not None
        assert latest.repository == "test/repo"
        assert latest.duration is not None

    def test_get_latest_metrics_by_repository_not_found(self, repository):
        """Test getting latest metrics for non-existent repository."""
        latest = repository.get_latest_metrics_by_repository("nonexistent/repo")
        assert latest is None

    def test_get_metric_history(self, repository, sample_metrics):
        """Test getting metric history."""
        repository.save_metrics(sample_metrics)

        history = repository.get_metric_history("test/repo", "duration_average")
        assert len(history) == 1
        assert history[0]["value"] == 120.5
        assert history[0]["repository"] == "test/repo"
        assert history[0]["metric_name"] == "duration_average"

    def test_get_repositories(self, repository, sample_metrics):
        """Test getting list of repositories."""
        repository.save_metrics(sample_metrics)

        repos = repository.get_repositories()
        assert "test/repo" in repos

    def test_get_metric_names(self, repository, sample_metrics):
        """Test getting list of metric names."""
        repository.save_metrics(sample_metrics)

        metric_names = repository.get_metric_names()
        assert "duration_average" in metric_names
        assert "throughput_daily" in metric_names
        assert "builds_total" in metric_names
        assert "mttr" in metric_names
        assert "success_rate" in metric_names

    def test_build_repository_metrics_from_rows_empty(self, repository):
        """Test building metrics from empty rows."""
        result = repository._build_repository_metrics_from_rows([])
        assert result == []

    def test_build_repository_metrics_from_rows_partial_data(self, repository):
        """Test building metrics from partial data."""
        # Create mock rows with only duration data

        # Mock sqlite3.Row objects
        class MockRow:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, key):
                return self._data[key]

        rows = [
            MockRow({
                "repository": "test/repo",
                "metric_name": "duration_average",
                "value": 120.5,
                "timestamp": "2024-01-01T00:00:00"
            }),
            MockRow({
                "repository": "test/repo",
                "metric_name": "duration_median",
                "value": 110.0,
                "timestamp": "2024-01-01T00:00:00"
            }),
        ]

        result = repository._build_repository_metrics_from_rows(rows)
        assert len(result) == 1
        assert result[0].repository == "test/repo"
        assert result[0].duration is not None
        assert result[0].duration.average == 120.5
        assert result[0].duration.median == 110.0
        assert result[0].throughput is None
        assert result[0].builds is None

    def test_multiple_repositories(self, repository):
        """Test handling multiple repositories."""
        # Create metrics for two repositories
        repo1_metrics = RepositoryMetrics(
            repository="repo1/name",
            duration=DurationMetrics(average=100.0, median=90.0, p95=150.0),
            mttr=30.0,
        )

        repo2_metrics = RepositoryMetrics(
            repository="repo2/name",
            duration=DurationMetrics(average=200.0, median=180.0, p95=300.0),
            mttr=60.0,
        )

        metrics = CIMetrics(repositories=[repo1_metrics, repo2_metrics])
        repository.save_metrics(metrics)

        # Test getting all metrics
        all_metrics = repository.get_all_metrics()
        assert len(all_metrics) == 2

        # Test getting repositories
        repos = repository.get_repositories()
        assert "repo1/name" in repos
        assert "repo2/name" in repos

    def test_database_error_handling(self, repository):
        """Test database error handling."""
        # Test with invalid database path
        with pytest.raises(Exception):  # Should raise DatabaseException
            invalid_repo = SQLiteMetricsRepository(db_path="/invalid/path/db.sqlite")
            invalid_repo.get_all_metrics()

    @patch("cipettelens.repositories.sqlite_metrics.sqlite3.connect")
    def test_database_connection_error(self, mock_connect, temp_db_path):
        """Test database connection error handling."""
        mock_connect.side_effect = sqlite3.Error("Connection failed")

        with pytest.raises(Exception):  # Should raise DatabaseConnectionError
            SQLiteMetricsRepository(db_path=temp_db_path)
