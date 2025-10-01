"""
CI Metrics domain models.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class DurationMetrics:
    """Duration metrics for CI/CD pipelines."""

    average: float
    median: float
    p95: float

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "average": self.average,
            "median": self.median,
            "p95": self.p95,
        }


@dataclass
class ThroughputMetrics:
    """Throughput metrics for CI/CD pipelines."""

    daily: float
    weekly: float

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "daily": self.daily,
            "weekly": self.weekly,
        }


@dataclass
class BuildMetrics:
    """Build metrics for CI/CD pipelines."""

    total: int
    successful: int
    failed: int

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total == 0:
            return 0.0
        return self.successful / self.total

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": self.success_rate,
        }


@dataclass
class RepositoryMetrics:
    """Repository-specific CI metrics."""

    repository: str
    duration: DurationMetrics | None = None
    throughput: ThroughputMetrics | None = None
    builds: BuildMetrics | None = None
    mttr: float | None = None  # Mean Time To Recovery
    success_rate: float | None = None
    timestamp: datetime | None = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "repository": self.repository,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

        if self.duration:
            result["duration"] = self.duration.to_dict()

        if self.throughput:
            result["throughput"] = self.throughput.to_dict()

        if self.builds:
            result["builds"] = self.builds.to_dict()

        if self.mttr is not None:
            result["mttr"] = self.mttr

        if self.success_rate is not None:
            result["success_rate"] = self.success_rate

        return result


@dataclass
class CIMetrics:
    """Complete CI metrics collection."""

    repositories: list[RepositoryMetrics]
    timestamp: datetime | None = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "repositories": {
                repo.repository: repo.to_dict() for repo in self.repositories
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CIMetrics":
        """Create CIMetrics from dictionary."""
        repositories = []

        for repo_name, repo_data in data.get("repositories", {}).items():
            # Parse duration metrics
            duration = None
            if "duration" in repo_data:
                duration = DurationMetrics(**repo_data["duration"])

            # Parse throughput metrics
            throughput = None
            if "throughput" in repo_data:
                throughput = ThroughputMetrics(**repo_data["throughput"])

            # Parse build metrics
            builds = None
            if "builds" in repo_data:
                builds = BuildMetrics(**repo_data["builds"])

            # Parse timestamp
            timestamp = None
            if "timestamp" in repo_data:
                timestamp = datetime.fromisoformat(repo_data["timestamp"])

            repo_metrics = RepositoryMetrics(
                repository=repo_name,
                duration=duration,
                throughput=throughput,
                builds=builds,
                mttr=repo_data.get("mttr"),
                success_rate=repo_data.get("success_rate"),
                timestamp=timestamp,
            )
            repositories.append(repo_metrics)

        return cls(repositories=repositories)
