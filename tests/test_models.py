"""
Tests for domain models.
"""

from datetime import datetime

from cipettelens.models.ci_metrics import (
    BuildMetrics,
    CIMetrics,
    DurationMetrics,
    RepositoryMetrics,
    ThroughputMetrics,
)


class TestDurationMetrics:
    """Test DurationMetrics model."""

    def test_duration_metrics_creation(self):
        """Test creating DurationMetrics."""
        metrics = DurationMetrics(average=10.5, median=9.0, p95=15.0)

        assert metrics.average == 10.5
        assert metrics.median == 9.0
        assert metrics.p95 == 15.0

    def test_duration_metrics_to_dict(self):
        """Test DurationMetrics to_dict method."""
        metrics = DurationMetrics(average=10.5, median=9.0, p95=15.0)
        result = metrics.to_dict()

        expected = {"average": 10.5, "median": 9.0, "p95": 15.0}
        assert result == expected


class TestThroughputMetrics:
    """Test ThroughputMetrics model."""

    def test_throughput_metrics_creation(self):
        """Test creating ThroughputMetrics."""
        metrics = ThroughputMetrics(daily=20.0, weekly=100.0)

        assert metrics.daily == 20.0
        assert metrics.weekly == 100.0

    def test_throughput_metrics_to_dict(self):
        """Test ThroughputMetrics to_dict method."""
        metrics = ThroughputMetrics(daily=20.0, weekly=100.0)
        result = metrics.to_dict()

        expected = {"daily": 20.0, "weekly": 100.0}
        assert result == expected


class TestBuildMetrics:
    """Test BuildMetrics model."""

    def test_build_metrics_creation(self):
        """Test creating BuildMetrics."""
        metrics = BuildMetrics(total=100, successful=90, failed=10)

        assert metrics.total == 100
        assert metrics.successful == 90
        assert metrics.failed == 10

    def test_build_metrics_success_rate(self):
        """Test BuildMetrics success_rate property."""
        metrics = BuildMetrics(total=100, successful=90, failed=10)

        assert metrics.success_rate == 0.9

    def test_build_metrics_success_rate_zero_total(self):
        """Test BuildMetrics success_rate with zero total."""
        metrics = BuildMetrics(total=0, successful=0, failed=0)

        assert metrics.success_rate == 0.0

    def test_build_metrics_to_dict(self):
        """Test BuildMetrics to_dict method."""
        metrics = BuildMetrics(total=100, successful=90, failed=10)
        result = metrics.to_dict()

        expected = {
            "total": 100,
            "successful": 90,
            "failed": 10,
            "success_rate": 0.9,
        }
        assert result == expected


class TestRepositoryMetrics:
    """Test RepositoryMetrics model."""

    def test_repository_metrics_creation(self):
        """Test creating RepositoryMetrics."""
        duration = DurationMetrics(average=10.0, median=9.0, p95=15.0)
        throughput = ThroughputMetrics(daily=20.0, weekly=100.0)
        builds = BuildMetrics(total=100, successful=90, failed=10)

        metrics = RepositoryMetrics(
            repository="owner/repo",
            duration=duration,
            throughput=throughput,
            builds=builds,
            mttr=5.0,
            success_rate=0.9,
        )

        assert metrics.repository == "owner/repo"
        assert metrics.duration == duration
        assert metrics.throughput == throughput
        assert metrics.builds == builds
        assert metrics.mttr == 5.0
        assert metrics.success_rate == 0.9
        assert metrics.timestamp is not None

    def test_repository_metrics_auto_timestamp(self):
        """Test RepositoryMetrics auto timestamp setting."""
        metrics = RepositoryMetrics(repository="owner/repo")

        assert metrics.timestamp is not None
        assert isinstance(metrics.timestamp, datetime)

    def test_repository_metrics_to_dict(self):
        """Test RepositoryMetrics to_dict method."""
        duration = DurationMetrics(average=10.0, median=9.0, p95=15.0)
        throughput = ThroughputMetrics(daily=20.0, weekly=100.0)
        builds = BuildMetrics(total=100, successful=90, failed=10)

        metrics = RepositoryMetrics(
            repository="owner/repo",
            duration=duration,
            throughput=throughput,
            builds=builds,
            mttr=5.0,
            success_rate=0.9,
        )

        result = metrics.to_dict()

        assert result["repository"] == "owner/repo"
        assert result["duration"] == duration.to_dict()
        assert result["throughput"] == throughput.to_dict()
        assert result["builds"] == builds.to_dict()
        assert result["mttr"] == 5.0
        assert result["success_rate"] == 0.9
        assert "timestamp" in result


class TestCIMetrics:
    """Test CIMetrics model."""

    def test_ci_metrics_creation(self):
        """Test creating CIMetrics."""
        repo_metrics = [
            RepositoryMetrics(repository="owner/repo1"),
            RepositoryMetrics(repository="owner/repo2"),
        ]

        metrics = CIMetrics(repositories=repo_metrics)

        assert len(metrics.repositories) == 2
        assert metrics.repositories[0].repository == "owner/repo1"
        assert metrics.repositories[1].repository == "owner/repo2"
        assert metrics.timestamp is not None

    def test_ci_metrics_auto_timestamp(self):
        """Test CIMetrics auto timestamp setting."""
        metrics = CIMetrics(repositories=[])

        assert metrics.timestamp is not None
        assert isinstance(metrics.timestamp, datetime)

    def test_ci_metrics_to_dict(self):
        """Test CIMetrics to_dict method."""
        repo_metrics = [
            RepositoryMetrics(repository="owner/repo1"),
            RepositoryMetrics(repository="owner/repo2"),
        ]

        metrics = CIMetrics(repositories=repo_metrics)
        result = metrics.to_dict()

        assert "timestamp" in result
        assert "repositories" in result
        assert "owner/repo1" in result["repositories"]
        assert "owner/repo2" in result["repositories"]

    def test_ci_metrics_from_dict(self):
        """Test CIMetrics from_dict method."""
        data = {
            "timestamp": "2023-01-01T00:00:00",
            "repositories": {
                "owner/repo1": {
                    "repository": "owner/repo1",
                    "duration": {"average": 10.0, "median": 9.0, "p95": 15.0},
                    "throughput": {"daily": 20.0, "weekly": 100.0},
                    "builds": {"total": 100, "successful": 90, "failed": 10},
                    "mttr": 5.0,
                    "success_rate": 0.9,
                    "timestamp": "2023-01-01T00:00:00",
                }
            },
        }

        metrics = CIMetrics.from_dict(data)

        assert len(metrics.repositories) == 1
        assert metrics.repositories[0].repository == "owner/repo1"
        assert metrics.repositories[0].duration is not None
        assert metrics.repositories[0].throughput is not None
        assert metrics.repositories[0].builds is not None
        assert metrics.repositories[0].mttr == 5.0
        assert metrics.repositories[0].success_rate == 0.9
