"""
Simple in-memory cache for performance optimization.
"""

import time
from threading import RLock
from typing import Any


class TTLCache:
    """Thread-safe TTL (Time To Live) cache."""

    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        """Initialize cache with default TTL."""
        self.default_ttl = default_ttl
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = RLock()

    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if time.time() < expiry:
                    return value
                else:
                    # Remove expired entry
                    del self._cache[key]
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with TTL."""
        with self._lock:
            expiry = time.time() + (ttl or self.default_ttl)
            self._cache[key] = (value, expiry)

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed entries."""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key
                for key, (_, expiry) in self._cache.items()
                if current_time >= expiry
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)


# Global cache instance
_global_cache: TTLCache | None = None


def get_cache() -> TTLCache:
    """Get the global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = TTLCache()
    return _global_cache


def clear_cache() -> None:
    """Clear the global cache."""
    global _global_cache
    if _global_cache:
        _global_cache.clear()
