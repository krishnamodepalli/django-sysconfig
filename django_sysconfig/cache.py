from typing import Any, Self

from django.core.cache import cache


class ConfigCache:
    CACHE_KEY_PREFIX = "config:"
    # Sentinel value to distinguish between "key doesn't exist" and "value is None"
    # Made a class attribute for public access
    NOT_FOUND = object()

    _instance: Self | None = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get(self, key: str) -> Any:
        """
        Get value from cache.

        Returns:
            Cached value if exists, NOT_FOUND sentinel if key doesn't exist
        """
        full_key = self.CACHE_KEY_PREFIX + key
        # Use a sentinel to distinguish between "key doesn't exist" and "value is None"
        value = cache.get(full_key, self.NOT_FOUND)
        return value

    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        return self.get(key) is not self.NOT_FOUND

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with no expiration (invalidate only on change)."""
        cache.set(self.CACHE_KEY_PREFIX + key, value, timeout=None)

    def invalidate(self, key: str) -> None:
        """Invalidate (delete) a cache key."""
        cache.delete(self.CACHE_KEY_PREFIX + key)


# Singleton instance
config_cache = ConfigCache()
