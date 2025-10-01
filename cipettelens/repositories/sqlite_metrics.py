"""
SQLite implementation of metrics repository.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import config
from ..exceptions.database import DatabaseConnectionError, DatabaseException
from ..models.ci_metrics import (
    BuildMetrics,
    CIMetrics,
    DurationMetrics,
    RepositoryMetrics,
    ThroughputMetrics,
)
from .base import MetricsRepository


class SQLiteMetricsRepository(MetricsRepository):
    """SQLite implementation of metrics repository."""

    def __init__(self, db_path: str | None = None):
        """Initialize SQLite metrics repository."""
        if db_path is None and config.DATABASE_PATH is None:
            raise ValueError("DATABASE_PATH is not configured")
        # At this point, we know at least one of them is not None
        actual_path = db_path or config.DATABASE_PATH
        if actual_path is None:
            raise ValueError("DATABASE_PATH is not configured")
        self.db_path = Path(actual_path)
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
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get latest metrics for the repository
                cursor.execute(
                    """
                    SELECT repository, metric_name, value, timestamp
                    FROM metrics
                    WHERE repository = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (repository, limit),
                )

                rows = cursor.fetchall()
                return self._build_repository_metrics_from_rows(rows)

        except sqlite3.Error as e:
            raise DatabaseException(
                f"Failed to get metrics for repository {repository}: {e}"
            ) from e

    def get_all_metrics(self, limit: int = 1000) -> list[RepositoryMetrics]:
        """Get all metrics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get latest metrics for all repositories
                cursor.execute(
                    """
                    SELECT repository, metric_name, value, timestamp
                    FROM metrics
                    ORDER BY repository, timestamp DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

                rows = cursor.fetchall()
                return self._build_repository_metrics_from_rows(rows)

        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to get all metrics: {e}") from e

    def get_metrics_by_metric_name(
        self, metric_name: str, limit: int = 100
    ) -> list[RepositoryMetrics]:
        """Get metrics by metric name."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get metrics by metric name
                cursor.execute(
                    """
                    SELECT repository, metric_name, value, timestamp
                    FROM metrics
                    WHERE metric_name = ?
                    ORDER BY repository, timestamp DESC
                    LIMIT ?
                    """,
                    (metric_name, limit),
                )

                rows = cursor.fetchall()
                return self._build_repository_metrics_from_rows(rows)

        except sqlite3.Error as e:
            raise DatabaseException(
                f"Failed to get metrics by name {metric_name}: {e}"
            ) from e

    def _build_repository_metrics_from_rows(
        self, rows: list[sqlite3.Row]
    ) -> list[RepositoryMetrics]:
        """Build RepositoryMetrics objects from database rows."""
        if not rows:
            return []

        # Group metrics by repository and timestamp
        repo_metrics_map: dict[tuple[str, str], dict[str, Any]] = {}

        for row in rows:
            repo = row["repository"]
            metric_name = row["metric_name"]
            value = row["value"]
            timestamp = row["timestamp"]

            # Use repository and timestamp as key to group metrics
            key = (repo, timestamp)
            if key not in repo_metrics_map:
                repo_metrics_map[key] = {
                    "repository": repo,
                    "timestamp": (
                        datetime.fromisoformat(timestamp) if timestamp else None
                    ),
                    "metrics": {},
                }

            repo_metrics_map[key]["metrics"][metric_name] = value

        # Convert grouped data to RepositoryMetrics objects
        result = []
        for (repo, _), data in repo_metrics_map.items():
            metrics = data["metrics"]
            timestamp = data["timestamp"]

            # Build DurationMetrics
            duration = None
            if any(k.startswith("duration_") for k in metrics.keys()):
                duration = DurationMetrics(
                    average=metrics.get("duration_average", 0.0),
                    median=metrics.get("duration_median", 0.0),
                    p95=metrics.get("duration_p95", 0.0),
                )

            # Build ThroughputMetrics
            throughput = None
            if any(k.startswith("throughput_") for k in metrics.keys()):
                throughput = ThroughputMetrics(
                    daily=metrics.get("throughput_daily", 0.0),
                    weekly=metrics.get("throughput_weekly", 0.0),
                )

            # Build BuildMetrics
            builds = None
            if any(k.startswith("builds_") for k in metrics.keys()):
                builds = BuildMetrics(
                    total=int(metrics.get("builds_total", 0)),
                    successful=int(metrics.get("builds_successful", 0)),
                    failed=int(metrics.get("builds_failed", 0)),
                )

            # Create RepositoryMetrics
            repo_metrics = RepositoryMetrics(
                repository=repo,
                duration=duration,
                throughput=throughput,
                builds=builds,
                mttr=metrics.get("mttr"),
                success_rate=metrics.get("success_rate"),
                timestamp=timestamp,
            )

            result.append(repo_metrics)

        return result

    def get_latest_metrics_by_repository(
        self, repository: str
    ) -> RepositoryMetrics | None:
        """Get the latest metrics for a specific repository."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get the latest timestamp for the repository
                cursor.execute(
                    """
                    SELECT MAX(timestamp) as latest_timestamp
                    FROM metrics
                    WHERE repository = ?
                    """,
                    (repository,),
                )

                latest_row = cursor.fetchone()
                if not latest_row or not latest_row["latest_timestamp"]:
                    return None

                latest_timestamp = latest_row["latest_timestamp"]

                # Get all metrics for that timestamp
                cursor.execute(
                    """
                    SELECT repository, metric_name, value, timestamp
                    FROM metrics
                    WHERE repository = ? AND timestamp = ?
                    """,
                    (repository, latest_timestamp),
                )

                rows = cursor.fetchall()
                metrics_list = self._build_repository_metrics_from_rows(rows)
                return metrics_list[0] if metrics_list else None

        except sqlite3.Error as e:
            raise DatabaseException(
                f"Failed to get latest metrics for repository {repository}: {e}"
            ) from e

    def get_metric_history(
        self, repository: str, metric_name: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get historical data for a specific metric."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT repository, metric_name, value, timestamp
                    FROM metrics
                    WHERE repository = ? AND metric_name = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (repository, metric_name, limit),
                )

                return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            raise DatabaseException(
                f"Failed to get metric history for {repository}/{metric_name}: {e}"
            ) from e

    def get_repositories(self) -> list[str]:
        """Get list of all repositories in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT DISTINCT repository
                    FROM metrics
                    ORDER BY repository
                    """
                )

                return [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to get repositories: {e}") from e

    def get_metric_names(self) -> list[str]:
        """Get list of all metric names in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT DISTINCT metric_name
                    FROM metrics
                    ORDER BY metric_name
                    """
                )

                return [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to get metric names: {e}") from e
