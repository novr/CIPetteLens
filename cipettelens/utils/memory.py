"""
Memory optimization utilities.
"""

import gc
import sys
from collections.abc import Generator, Iterator
from typing import Any


def get_memory_usage() -> dict[str, int]:
    """Get current memory usage statistics."""
    return {
        "rss": sys.getsizeof(gc.get_objects()),
        "objects": len(gc.get_objects()),
        "garbage": len(gc.garbage),
    }


def optimize_memory() -> int:
    """Run garbage collection to optimize memory usage."""
    collected = gc.collect()
    return collected


def memory_efficient_batch(
    items: list[Any], batch_size: int = 1000
) -> Generator[list[Any], None, None]:
    """Process items in memory-efficient batches."""
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]
        # Force garbage collection after each batch
        if i % (batch_size * 10) == 0:
            gc.collect()


def chunked_iterator(
    iterator: Iterator[Any], chunk_size: int = 1000
) -> Generator[list[Any], None, None]:
    """Convert an iterator into memory-efficient chunks."""
    chunk = []
    for item in iterator:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
            # Periodic garbage collection
            gc.collect()

    if chunk:
        yield chunk


class MemoryTracker:
    """Track memory usage for debugging."""

    def __init__(self, name: str):
        self.name = name
        self.start_memory = get_memory_usage()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_memory = get_memory_usage()
        memory_diff = end_memory["rss"] - self.start_memory["rss"]

        if memory_diff > 1024 * 1024:  # More than 1MB
            print(f"Memory usage for {self.name}: {memory_diff / 1024 / 1024:.2f} MB")

    def get_delta(self) -> dict[str, int]:
        """Get memory usage delta since start."""
        current_memory = get_memory_usage()
        return {
            "rss": current_memory["rss"] - self.start_memory["rss"],
            "objects": current_memory["objects"] - self.start_memory["objects"],
            "garbage": current_memory["garbage"] - self.start_memory["garbage"],
        }
