"""
Collect metrics CLI command.
"""

from ..factories import create_metrics_service
from ..logger import logger
from ..use_cases.collect_metrics import CollectMetricsUseCase


def collect_metrics() -> None:
    """Collect CI/CD metrics and save to database."""
    try:
        logger.info("Starting CIAnalyzer data collection...")

        # Initialize dependencies using factory
        metrics_service = create_metrics_service()
        collect_use_case = CollectMetricsUseCase(metrics_service)

        # Execute use case
        metrics = collect_use_case.execute()

        logger.info(
            f"Data collection completed successfully! Collected metrics for {len(metrics.repositories)} repositories"
        )

    except Exception as e:
        logger.error(f"Error during data collection: {e}")
        raise
