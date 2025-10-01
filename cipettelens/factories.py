"""
Factory functions for creating service instances.
"""

from .config import config
from .external.ci_analyzer import CIAnalyzerClient
from .repositories.sqlite_metrics import SQLiteMetricsRepository
from .services.metrics_service import MetricsService


def create_metrics_service() -> MetricsService:
    """Create MetricsService with dependencies injected."""
    # Validate configuration before creating service
    config.validate_and_raise()

    return MetricsService(
        metrics_repository=SQLiteMetricsRepository(),
        github_token=config.GITHUB_TOKEN or "",
        target_repositories=config.get_repositories_from_config(),
        ci_analyzer_client=CIAnalyzerClient(),
    )


def create_metrics_repository():
    """Create MetricsRepository instance."""
    return SQLiteMetricsRepository()


def create_ci_analyzer_client() -> CIAnalyzerClient:
    """Create CIAnalyzerClient instance."""
    return CIAnalyzerClient()
