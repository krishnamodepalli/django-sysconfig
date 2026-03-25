# Caching

`django-sysconfig` caches every configuration value using Django's standard cache framework. This keeps config reads fast without any configuration on your part — but there are a few things worth knowing, especially in production.

## How caching works

Every `config.get(path)` call goes through the cache:

1. **Cache hit** — the value is deserialized from the cache and returned. No database query.
2. **Cache miss** — the value is fetched from the database, written to the cache, then returned.

Every `config.set(path, value)` call:

1. Writes the new value to the database.
2. **Updates** the cache entry for that path with the new value. No Invalidation, the next get will be fetched from cache.

Cache entries have **no expiry time**. They are only updated on write. This means config reads are essentially free in steady state — one cache lookup per path per process, then pure in-memory cache hits for all subsequent reads in the same cache entry lifecycle.

## Cache backend requirements

`django-sysconfig` uses whatever cache backend you've configured in `CACHES`. The default Django cache backend is `LocMemCache`:

```python
# Django's default — in-memory, per-process
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
```

**`LocMemCache` works fine in development**, but has a critical limitation in production: it's per-process. If you run multiple web workers (e.g., several Gunicorn or uWSGI processes), each process has its own independent cache. A value written by one process invalidates the cache only in *that* process's memory. Other processes will continue serving stale values until they take a cache miss themselves.

**For production, use a shared cache backend:**

```python
# Redis (recommended)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}

# Memcached
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "127.0.0.1:11211",
    }
}
```

With a shared cache, all processes invalidate and read from the same cache layer, so writes propagate immediately across all workers.

<!-- ## Using a dedicated cache

TODO: Uncomment this when the issue #51 is closed

If you want `django-sysconfig` to use a named cache other than `"default"`, you can configure this in your settings:

```python
# settings.py
DJANGO_SYSCONFIG = {
    "CACHE_NAME": "sysconfig",
}
```

Then define that cache in `CACHES`:

```python
CACHES = {
    "default": { ... },
    "sysconfig": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
    }
}
```

This is useful if you want to keep config cache entries isolated from your application cache — for example, to avoid config values being evicted under memory pressure, or to set different eviction policies.

---

-->
