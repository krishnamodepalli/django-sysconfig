from typing import Any

from django.core.cache import cache


class ConfigCache:
    CACHE_KEY_PREFIX = "django_sysconfig:"
    # Sentinel value to distinguish between "key doesn't exist" and "value is None"
    # Made a class attribute for public access
    NOT_FOUND = object()

    _instance: "ConfigCache | None" = None

    def __new__(cls) -> "ConfigCache":
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

    def clear(self) -> None:
        """
        Clear all cache keys matching the prefix.

        On backends supporting delete_pattern (like redis), it deletes matching keys.
        On LocMemCache (often used in tests), it iterates and removes matching keys.
        Otherwise, it falls back to cache.clear() which flushes the ENTIRE cache.
        """
        try:
            cache.delete_pattern(f"{self.CACHE_KEY_PREFIX}*")
        except AttributeError:
            if hasattr(cache, "_cache"):
                # Safe individual invalidation for LocMemCache
                # In testing, the default cache has keys stored via versions.
                # Find all keys including the sysconfig prefix and invalidate the core key without version
                keys_to_delete = []
                for internal_key in list(cache._cache.keys()):
                    if self.CACHE_KEY_PREFIX in internal_key:
                        # Extract the key relative to our prefix
                        # Using partition on our prefix gives us the exact trailing key string
                        key_subset = internal_key.split(self.CACHE_KEY_PREFIX, 1)[1]
                        keys_to_delete.append(key_subset)
                for k in keys_to_delete:
                    self.invalidate(k)
            else:
                # Warning: Nuclear operation on other unknown backends
                cache.clear()


# Singleton instance
config_cache = ConfigCache()
