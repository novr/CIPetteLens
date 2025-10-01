"""
Collect metrics use case.
"""

from ..models.ci_metrics import CIMetrics
from ..services.metrics_service import MetricsService


class CollectMetricsUseCase:
    """Use case for collecting CI/CD metrics."""

    def __init__(self, metrics_service: MetricsService):
        """Initialize collect metrics use case."""
        self.metrics_service = metrics_service

    def execute(self) -> CIMetrics:
        """Execute the collect metrics use case."""
        return self.metrics_service.collect_and_save_metrics()
