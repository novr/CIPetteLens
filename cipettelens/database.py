"""
Database operations for CIPetteLens.
"""

import sqlite3
from pathlib import Path
from typing import Any

from .config import config


class Database:
    """SQLite database operations."""

    def __init__(self, db_path: str | None = None):
        if db_path is None and config.DATABASE_PATH is None:
            raise ValueError("DATABASE_PATH is not configured")
        # At this point, we know at least one of them is not None
        actual_path = db_path or config.DATABASE_PATH
        assert actual_path is not None  # Type assertion for mypy
        self.db_path = Path(actual_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables."""
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

    def insert_metric(self, repository: str, metric_name: str, value: float):
        """Insert a single metric into the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO metrics (repository, metric_name, value)
                VALUES (?, ?, ?)
            """,
                (repository, metric_name, value),
            )
            conn.commit()

    def insert_metrics(self, metrics: list[dict[str, Any]]):
        """Insert multiple metrics into the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO metrics (repository, metric_name, value)
                VALUES (?, ?, ?)
            """,
                [(m["repository"], m["metric_name"], m["value"]) for m in metrics],
            )
            conn.commit()

    def get_latest_metrics(self, repository: str | None = None) -> list[dict[str, Any]]:
        """Get the latest metrics for a repository or all repositories."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if repository:
                cursor.execute(
                    """
                    SELECT repository, metric_name, value, timestamp
                    FROM metrics
                    WHERE repository = ?
                    ORDER BY timestamp DESC
                """,
                    (repository,),
                )
            else:
                cursor.execute(
                    """
                    SELECT repository, metric_name, value, timestamp
                    FROM metrics
                    ORDER BY timestamp DESC
                """
                )

            return [dict(row) for row in cursor.fetchall()]

    def get_metric_history(
        self, repository: str, metric_name: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get historical data for a specific metric."""
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

    def save_cianalyzer_data(self, data: dict[str, Any]) -> None:
        """Save CIAnalyzer results to the database."""
        if "repositories" not in data:
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for repo, metrics in data["repositories"].items():
                # Insert duration metrics
                if "duration" in metrics:
                    self._insert_metric_batch(
                        cursor,
                        repo,
                        [
                            ("duration_average", metrics["duration"]["average"]),
                            ("duration_median", metrics["duration"]["median"]),
                            ("duration_p95", metrics["duration"]["p95"]),
                        ],
                    )

                # Insert success rate
                if "success_rate" in metrics:
                    self._insert_metric_batch(
                        cursor, repo, [("success_rate", metrics["success_rate"])]
                    )

                # Insert throughput metrics
                if "throughput" in metrics:
                    self._insert_metric_batch(
                        cursor,
                        repo,
                        [
                            ("throughput_daily", metrics["throughput"]["daily"]),
                            ("throughput_weekly", metrics["throughput"]["weekly"]),
                        ],
                    )

                # Insert MTTR
                if "mttr" in metrics:
                    self._insert_metric_batch(cursor, repo, [("mttr", metrics["mttr"])])

                # Insert build metrics
                if "builds" in metrics:
                    self._insert_metric_batch(
                        cursor,
                        repo,
                        [
                            ("builds_total", metrics["builds"]["total"]),
                            ("builds_successful", metrics["builds"]["successful"]),
                            ("builds_failed", metrics["builds"]["failed"]),
                        ],
                    )

            conn.commit()

    def _insert_metric_batch(
        self, cursor: sqlite3.Cursor, repository: str, metrics: list[tuple[str, float]]
    ) -> None:
        """Insert a batch of metrics for a repository."""
        for metric_name, value in metrics:
            cursor.execute(
                """
                INSERT INTO metrics (repository, metric_name, value)
                VALUES (?, ?, ?)
            """,
                (repository, metric_name, value),
            )
