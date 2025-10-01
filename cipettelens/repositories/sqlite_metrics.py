"""
SQLite implementation of metrics repository.
"""

import sqlite3
from pathlib import Path

from ..config import config
from ..exceptions.database import DatabaseConnectionError, DatabaseException
from ..models.ci_metrics import CIMetrics, RepositoryMetrics
from .base import MetricsRepository


class SQLiteMetricsRepository(MetricsRepository):
    """SQLite implementation of metrics repository."""

    def __init__(self, db_path: str | None = None):
        """Initialize SQLite metrics repository."""
        self.db_path = Path(db_path or config.DATABASE_PATH)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create metrics table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        repository TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        value REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create indexes for better performance
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_repository_metric
                    ON metrics(repository, metric_name)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_timestamp
                    ON metrics(timestamp)
                """
                )

                conn.commit()

        except sqlite3.Error as e:
            raise DatabaseConnectionError(
                f"Failed to initialize database: {e}", str(self.db_path)
            ) from e

    def save_metrics(self, metrics: CIMetrics) -> None:
        """Save CI metrics to the repository."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for repo_metrics in metrics.repositories:
                    self._save_repository_metrics(cursor, repo_metrics)

                conn.commit()

        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to save metrics: {e}") from e

    def _save_repository_metrics(
        self, cursor: sqlite3.Cursor, repo_metrics: RepositoryMetrics
    ) -> None:
        """Save metrics for a single repository."""
        # Save duration metrics
        if repo_metrics.duration:
            cursor.execute(
                "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                (
                    repo_metrics.repository,
                    "duration_average",
                    repo_metrics.duration.average,
                ),
            )
            cursor.execute(
                "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                (
                    repo_metrics.repository,
                    "duration_median",
                    repo_metrics.duration.median,
                ),
            )
            cursor.execute(
                "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                (repo_metrics.repository, "duration_p95", repo_metrics.duration.p95),
            )

        # Save throughput metrics
        if repo_metrics.throughput:
            cursor.execute(
                "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                (
                    repo_metrics.repository,
                    "throughput_daily",
                    repo_metrics.throughput.daily,
                ),
            )
            cursor.execute(
                "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                (
                    repo_metrics.repository,
                    "throughput_weekly",
                    repo_metrics.throughput.weekly,
                ),
            )

        # Save build metrics
        if repo_metrics.builds:
            cursor.execute(
                "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                (repo_metrics.repository, "builds_total", repo_metrics.builds.total),
            )
            cursor.execute(
                "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                (
                    repo_metrics.repository,
                    "builds_successful",
                    repo_metrics.builds.successful,
                ),
            )
            cursor.execute(
                "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                (repo_metrics.repository, "builds_failed", repo_metrics.builds.failed),
            )

        # Save MTTR
        if repo_metrics.mttr is not None:
            cursor.execute(
                "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                (repo_metrics.repository, "mttr", repo_metrics.mttr),
            )

        # Save success rate
        if repo_metrics.success_rate is not None:
            cursor.execute(
                "INSERT INTO metrics (repository, metric_name, value) VALUES (?, ?, ?)",
                (repo_metrics.repository, "success_rate", repo_metrics.success_rate),
            )

    def get_metrics_by_repository(
        self, repository: str, limit: int = 100
    ) -> list[RepositoryMetrics]:
        """Get metrics for a specific repository."""
        # This is a simplified implementation
        # In a real application, you would reconstruct RepositoryMetrics from the database
        return []

    def get_all_metrics(self, limit: int = 1000) -> list[RepositoryMetrics]:
        """Get all metrics."""
        # This is a simplified implementation
        # In a real application, you would reconstruct RepositoryMetrics from the database
        return []

    def get_metrics_by_metric_name(
        self, metric_name: str, limit: int = 100
    ) -> list[RepositoryMetrics]:
        """Get metrics by metric name."""
        # This is a simplified implementation
        # In a real application, you would reconstruct RepositoryMetrics from the database
        return []
