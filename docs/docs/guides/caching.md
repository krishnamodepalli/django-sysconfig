# Caching

`django-sysconfig` caches every configuration value using Django's standard cache framework. This keeps config reads fast without any configuration on your part — but there are a few things worth knowing, especially in production.

---

## How caching works

Every `config.get(path)` call goes through the cache:

1. **Cache hit** — the value is deserialized from the cache and returned. No database query.
2. **Cache miss** — the value is fetched from the database, written to the cache, then returned.

Every `config.set(path, value)` call:

1. Writes the new value to the database.
2. **Deletes** the cache entry for that path (explicit invalidation).
3. The next `config.get(...)` for that path will be a cache miss, which populates the cache from the fresh database value.

Cache entries have **no expiry time**. They are only ever invalidated explicitly on write. This means config reads are essentially free in steady state — one cache lookup per path per process, then pure in-memory cache hits for all subsequent reads in the same cache entry lifecycle.

---

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

---

## Using a dedicated cache

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

## Cache keys

Cache keys follow the pattern:

```
django_sysconfig:<path>
```

For example, the cache key for `myapp.general.site_name` is `django_sysconfig:myapp.general.site_name`.

You generally don't need to know this, but it's useful if you need to manually inspect or flush individual cache entries:

```python
from django.core.cache import cache

# Manually inspect a cache entry
cache.get("django_sysconfig:myapp.general.site_name")

# Manually invalidate a single entry
cache.delete("django_sysconfig:myapp.general.site_name")
```

---

## Warming the cache

On a fresh deployment, the cache is cold — every `config.get(...)` will be a database miss until the value has been read at least once. For most applications, this doesn't matter: the first request warms the cache and everything is fast from there.

If you want to pre-warm the cache on startup (for example, to ensure the first requests don't hit the database for config), you can do so in a management command or in `AppConfig.ready()`:

```python
from django_sysconfig.accessor import config

# Warm the entire config for an app
config.all("myapp")
```

Calling `config.all(...)` reads all values for an app in a single pass, which populates the cache for each field.

---

## Flushing all config cache entries

If you ever need to flush all `django-sysconfig` cache entries (for example, after a database restore or during debugging):

```python
from django.core.cache import cache

# If using a dedicated cache
cache = caches["sysconfig"]
cache.clear()
```

Or, less bluntly, re-read every registered path to force a fresh DB read for each one:

```python
from django_sysconfig.accessor import config
from django_sysconfig.registry import registry

for app_label in registry.get_apps():
    config.all(app_label)
```
