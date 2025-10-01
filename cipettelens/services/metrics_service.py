"""
Metrics service for CI/CD metrics management.
"""

from ..config import config
from ..exceptions.validation import ConfigurationError
from ..external.ci_analyzer import CIAnalyzerClient
from ..logger import logger
from ..models.ci_metrics import CIMetrics
from ..repositories.base import MetricsRepository


class MetricsService:
    """Service for managing CI/CD metrics."""

    def __init__(
        self,
        metrics_repository: MetricsRepository,
        ci_analyzer_client: CIAnalyzerClient | None = None,
    ):
        """Initialize metrics service."""
        self.metrics_repository = metrics_repository
        self.ci_analyzer_client = ci_analyzer_client or CIAnalyzerClient()

    def collect_and_save_metrics(self) -> CIMetrics:
        """Collect metrics from CIAnalyzer and save to repository."""
        # Validate configuration
        self._validate_configuration()

        # Get repositories
        repositories = config.get_repositories_from_config()
        logger.info(f"Collecting metrics for {len(repositories)} repositories")

        # Collect metrics
        if config.GITHUB_TOKEN is None:
            raise ConfigurationError("GITHUB_TOKEN is not configured", "GITHUB_TOKEN")
        metrics = self.ci_analyzer_client.collect_metrics(
            repositories, config.GITHUB_TOKEN
        )

        # Save metrics
        self.metrics_repository.save_metrics(metrics)
        logger.info("Metrics saved successfully")

        return metrics

    def get_metrics_by_repository(self, repository: str, limit: int = 100) -> list:
        """Get metrics for a specific repository."""
        return self.metrics_repository.get_metrics_by_repository(repository, limit)

    def get_all_metrics(self, limit: int = 1000) -> list:
        """Get all metrics."""
        return self.metrics_repository.get_all_metrics(limit)

    def get_metrics_by_metric_name(self, metric_name: str, limit: int = 100) -> list:
        """Get metrics by metric name."""
        return self.metrics_repository.get_metrics_by_metric_name(metric_name, limit)

    def _validate_configuration(self) -> None:
        """Validate service configuration."""
        if not config.GITHUB_TOKEN:
            raise ConfigurationError("GITHUB_TOKEN is required", "GITHUB_TOKEN")

        repositories = config.get_repositories_from_config()
        if not repositories:
            raise ConfigurationError(
                "No repositories configured", "TARGET_REPOSITORIES"
            )
