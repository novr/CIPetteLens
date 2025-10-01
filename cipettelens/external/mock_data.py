"""
Mock data generator for testing.
"""

import secrets
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
        # Generate duration metrics using cryptographically secure random
        duration = DurationMetrics(
            average=secrets.randbelow(2500) / 100 + 5.0,  # 5.0 to 30.0
            median=secrets.randbelow(1700) / 100 + 8.0,  # 8.0 to 25.0
            p95=secrets.randbelow(3000) / 100 + 15.0,  # 15.0 to 45.0
        )

        # Generate throughput metrics
        throughput = ThroughputMetrics(
            daily=secrets.randbelow(4000) / 100 + 10.0,  # 10.0 to 50.0
            weekly=secrets.randbelow(15000) / 100 + 50.0,  # 50.0 to 200.0
        )

        # Generate build metrics
        total_builds = secrets.randbelow(451) + 50  # 50 to 500
        success_rate = secrets.randbelow(2500) / 10000 + 0.7  # 0.7 to 0.95
        successful_builds = int(total_builds * success_rate)
        failed_builds = total_builds - successful_builds

        builds = BuildMetrics(
            total=total_builds,
            successful=successful_builds,
            failed=failed_builds,
        )

        # Generate other metrics
        mttr = secrets.randbelow(1000) / 100 + 2.0  # 2.0 to 12.0 hours
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
