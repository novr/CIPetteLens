"""
Mock data generator for testing.
"""

import random
from datetime import datetime

from ..models.ci_metrics import (
    BuildMetrics,
    CIMetrics,
    DurationMetrics,
    RepositoryMetrics,
    ThroughputMetrics,
)


class MockDataGenerator:
    """Generator for mock CI/CD metrics data."""

    def generate_metrics(self, repositories: list[str]) -> CIMetrics:
        """Generate mock CI metrics for given repositories."""
        repo_metrics = []

        for repo in repositories:
            metrics = self._generate_repository_metrics(repo)
            repo_metrics.append(metrics)

        return CIMetrics(repositories=repo_metrics)

    def _generate_repository_metrics(self, repository: str) -> RepositoryMetrics:
        """Generate mock metrics for a single repository."""
        # Generate duration metrics
        duration = DurationMetrics(
            average=random.uniform(5.0, 30.0),
            median=random.uniform(8.0, 25.0),
            p95=random.uniform(15.0, 45.0),
        )

        # Generate throughput metrics
        throughput = ThroughputMetrics(
            daily=random.uniform(10.0, 50.0),
            weekly=random.uniform(50.0, 200.0),
        )

        # Generate build metrics
        total_builds = random.randint(50, 500)
        successful_builds = int(total_builds * random.uniform(0.7, 0.95))
        failed_builds = total_builds - successful_builds

        builds = BuildMetrics(
            total=total_builds,
            successful=successful_builds,
            failed=failed_builds,
        )

        # Generate other metrics
        mttr = random.uniform(2.0, 12.0)  # hours
        success_rate = builds.success_rate

        return RepositoryMetrics(
            repository=repository,
            duration=duration,
            throughput=throughput,
            builds=builds,
            mttr=mttr,
            success_rate=success_rate,
            timestamp=datetime.now(),
        )
