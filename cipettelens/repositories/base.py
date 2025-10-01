"""
Base repository interfaces.
"""

from abc import ABC, abstractmethod

from ..models.ci_metrics import CIMetrics, RepositoryMetrics


class MetricsRepository(ABC):
    """Abstract base class for metrics repository."""

    @abstractmethod
    def save_metrics(self, metrics: CIMetrics) -> None:
        """Save CI metrics to the repository."""
        pass

    @abstractmethod
    def get_metrics_by_repository(
        self, repository: str, limit: int = 100
    ) -> list[RepositoryMetrics]:
        """Get metrics for a specific repository."""
        pass

    @abstractmethod
    def get_all_metrics(self, limit: int = 1000) -> list[RepositoryMetrics]:
        """Get all metrics."""
        pass

    @abstractmethod
    def get_metrics_by_metric_name(
        self, metric_name: str, limit: int = 100
    ) -> list[RepositoryMetrics]:
        """Get metrics by metric name."""
        pass
