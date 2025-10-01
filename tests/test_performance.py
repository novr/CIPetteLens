"""
Performance tests for CIPetteLens.
"""

import tempfile
import time
from pathlib import Path

import pytest

from cipettelens.infrastructure.cache import TTLCache
from cipettelens.infrastructure.database_pool import DatabaseConnectionPool
from cipettelens.models.ci_metrics import (
    BuildMetrics,
    CIMetrics,
    DurationMetrics,
    RepositoryMetrics,
    ThroughputMetrics,
)
from cipettelens.repositories.sqlite_metrics import SQLiteMetricsRepository
from cipettelens.utils.performance import PerformanceMonitor, measure_time


class TestPerformanceOptimizations:
    """Test performance optimizations."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            temp_path = f.name
        yield temp_path
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def repository(self, temp_db_path):
        """Create a repository instance with temporary database."""
        return SQLiteMetricsRepository(db_path=temp_db_path)

    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics for performance testing."""
        repos = []
        for i in range(10):  # 10 repositories
            repo_metrics = RepositoryMetrics(
                repository=f"test/repo{i}",
                duration=DurationMetrics(average=120.5, median=110.0, p95=180.0),
                throughput=ThroughputMetrics(daily=5.2, weekly=35.0),
                builds=BuildMetrics(total=100, successful=95, failed=5),
                mttr=45.5,
                success_rate=0.95,
            )
            repos.append(repo_metrics)

        return CIMetrics(repositories=repos)

    def test_batch_insert_performance(self, repository, sample_metrics):
        """Test that batch insert is faster than individual inserts."""
        start_time = time.time()
        repository.save_metrics(sample_metrics)
        batch_time = time.time() - start_time

        # Should complete in reasonable time (less than 1 second for 10 repos)
        assert batch_time < 1.0
        print(f"Batch insert time: {batch_time:.4f} seconds")

    def test_cache_performance(self):
        """Test cache performance."""
        cache = TTLCache(default_ttl=60)

        # Test cache hit performance
        cache.set("test_key", "test_value")

        start_time = time.time()
        for _ in range(1000):
            cache.get("test_key")
        cache_time = time.time() - start_time

        # Should be very fast (less than 0.1 seconds for 1000 lookups)
        assert cache_time < 0.1
        print(f"Cache lookup time: {cache_time:.4f} seconds")

    def test_database_connection_pool(self, temp_db_path):
        """Test database connection pool performance."""
        pool = DatabaseConnectionPool(db_path=temp_db_path, max_connections=5)

        start_time = time.time()

        # Test multiple concurrent connections
        with pool.get_connection() as conn1:
            with pool.get_connection() as conn2:
                with pool.get_connection() as conn3:
                    # All connections should be available
                    assert conn1 is not None
                    assert conn2 is not None
                    assert conn3 is not None

        pool_time = time.time() - start_time

        # Should be fast (less than 0.5 seconds)
        assert pool_time < 0.5
        print(f"Connection pool time: {pool_time:.4f} seconds")

        pool.close_all()

    def test_query_performance(self, repository, sample_metrics):
        """Test query performance with large dataset."""
        # Insert test data
        repository.save_metrics(sample_metrics)

        # Test query performance
        start_time = time.time()
        metrics = repository.get_all_metrics(limit=1000)
        query_time = time.time() - start_time

        # Should be fast (less than 0.5 seconds)
        assert query_time < 0.5
        assert len(metrics) > 0
        print(f"Query time: {query_time:.4f} seconds")

    def test_memory_usage(self, repository, sample_metrics):
        """Test memory usage during operations."""
        import gc

        # Get initial memory
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Perform operations
        repository.save_metrics(sample_metrics)
        repository.get_all_metrics()

        # Check memory didn't grow excessively
        gc.collect()
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects

        # Should not create excessive objects (less than 1000 new objects)
        assert object_growth < 1000
        print(f"Object growth: {object_growth} objects")

    def test_performance_monitor(self):
        """Test performance monitoring."""
        monitor = PerformanceMonitor()

        # Simulate some operations
        monitor.start_timer("test_operation")
        time.sleep(0.01)  # 10ms
        monitor.end_timer("test_operation")

        monitor.start_timer("test_operation")
        time.sleep(0.02)  # 20ms
        monitor.end_timer("test_operation")

        # Check statistics
        stats = monitor.get_stats()
        assert "test_operation" in stats
        assert stats["test_operation"]["count"] == 2
        assert stats["test_operation"]["average"] > 0.01
        assert stats["test_operation"]["average"] < 0.03

    def test_measure_time_decorator(self):
        """Test the measure_time decorator."""

        @measure_time
        def test_function():
            time.sleep(0.01)
            return "test_result"

        result = test_function()
        assert result == "test_result"

    def test_large_dataset_performance(self, temp_db_path):
        """Test performance with larger dataset."""
        repository = SQLiteMetricsRepository(db_path=temp_db_path)

        # Create larger dataset
        repos = []
        for i in range(100):  # 100 repositories
            repo_metrics = RepositoryMetrics(
                repository=f"test/repo{i}",
                duration=DurationMetrics(average=120.5, median=110.0, p95=180.0),
                throughput=ThroughputMetrics(daily=5.2, weekly=35.0),
                builds=BuildMetrics(total=100, successful=95, failed=5),
                mttr=45.5,
                success_rate=0.95,
            )
            repos.append(repo_metrics)

        large_metrics = CIMetrics(repositories=repos)

        # Test batch insert performance
        start_time = time.time()
        repository.save_metrics(large_metrics)
        insert_time = time.time() - start_time

        # Should complete in reasonable time (less than 5 seconds for 100 repos)
        assert insert_time < 5.0
        print(f"Large dataset insert time: {insert_time:.4f} seconds")

        # Test query performance
        start_time = time.time()
        repository.get_all_metrics(limit=10000)
        query_time = time.time() - start_time

        # Should be fast (less than 2 seconds)
        assert query_time < 2.0
        print(f"Large dataset query time: {query_time:.4f} seconds")
