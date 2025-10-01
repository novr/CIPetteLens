"""
Performance monitoring and optimization utilities.
"""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from ..logger import logger

F = TypeVar("F", bound=Callable[..., Any])


def measure_time(func: F) -> F:
    """Decorator to measure function execution time."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {execution_time:.4f} seconds: {e}"
            )
            raise

    return wrapper  # type: ignore[return-value]


def log_slow_queries(threshold: float = 1.0):
    """Decorator to log slow database queries."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                if execution_time > threshold:
                    logger.warning(
                        f"Slow query detected: {func.__name__} took {execution_time:.4f} seconds "
                        f"(threshold: {threshold}s)"
                    )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Query {func.__name__} failed after {execution_time:.4f} seconds: {e}"
                )
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


class PerformanceMonitor:
    """Simple performance monitoring class."""

    def __init__(self):
        self.metrics: dict[str, list[float]] = {}

    def start_timer(self, operation: str) -> None:
        """Start timing an operation."""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(time.time())

    def end_timer(self, operation: str) -> float:
        """End timing an operation and return duration."""
        if operation not in self.metrics or not self.metrics[operation]:
            return 0.0

        start_time = self.metrics[operation].pop()
        duration = time.time() - start_time
        self.metrics[operation].append(duration)
        return duration

    def get_average_time(self, operation: str) -> float:
        """Get average execution time for an operation."""
        if operation not in self.metrics or not self.metrics[operation]:
            return 0.0

        times = [t for t in self.metrics[operation] if isinstance(t, float)]
        return sum(times) / len(times) if times else 0.0

    def get_stats(self) -> dict[str, dict[str, float]]:
        """Get performance statistics."""
        stats = {}
        for operation, times in self.metrics.items():
            float_times = [t for t in times if isinstance(t, float)]
            if float_times:
                stats[operation] = {
                    "count": len(float_times),
                    "total": sum(float_times),
                    "average": sum(float_times) / len(float_times),
                    "min": min(float_times),
                    "max": max(float_times),
                }
        return stats


# Global performance monitor
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor."""
    return _performance_monitor
