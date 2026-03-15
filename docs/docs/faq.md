# FAQ & Troubleshooting

Answers to the most common questions and issues.

---

## Installation & setup

### My `sysconfig.py` is being ignored. Fields don't show up in the admin UI.

A few things to check:

**1. Is the app in `INSTALLED_APPS`?**

Autodiscovery only runs for apps listed in `INSTALLED_APPS`. If your app isn't there, its `sysconfig.py` is never imported.

**2. Does the file use `@register_config(...)`?**

Simply having a `sysconfig.py` file isn't enough — you must decorate your config class with `@register_config("your_app_label")`:

```python
# ✅ Correct
@register_config("myapp")
class MyAppConfig:
    ...

# ❌ Wrong — not registered
class MyAppConfig:
    ...
```

**3. Did Django restart after you created the file?**

Autodiscovery runs at startup. If you added `sysconfig.py` while the server was running, restart the dev server.

**4. Is there a syntax error or import error in your `sysconfig.py`?**

If the file raises an exception during import, autodiscovery silently skips it (or you'll see a traceback in the startup logs). Check your terminal output when starting the server.

---

### The admin config UI at `/admin/config/` returns a 404.

Make sure the config URL pattern is in your `urls.py` **and comes before the default admin path**:

```python
urlpatterns = [
    path("admin/config/", include("django_sysconfig.urls")),  # ← first
    path("admin/", admin.site.urls),                          # ← second
]
```

If `path("admin/", ...)` comes first, Django matches it before ever reaching the config pattern.

---

### I get a `django.db.utils.OperationalError: no such table: django_sysconfig_configvalue`.

You haven't run migrations yet:

```bash
python manage.py migrate
```

---

## Reading and writing values

### `config.get(...)` returns `None` but I set a default.

The most common cause is a typo in the path. Double-check:
- The app label matches the string in `@register_config("app_label")`
- The section name matches the class name (lowercased)
- The field name matches the attribute name (lowercased)

You can verify the path is registered:

```python
from django_sysconfig.accessor import config
config.exists("myapp.general.site_name")  # should be True
```

If it returns `False`, the path isn't registered — re-check your `sysconfig.py`.

---

### `AppNotFoundError` raised even though my `sysconfig.py` exists.

The app label you're passing to `config.get(...)` must exactly match the string in `@register_config("app_label")`. They are case-sensitive.

```python
@register_config("MyApp")   # registered as "MyApp"
...

config.get("myapp.general.x")   # ❌ "myapp" ≠ "MyApp" → AppNotFoundError
config.get("MyApp.general.x")   # ✅ matches
```

Convention: use lowercase app labels to avoid this.

---

### `config.set(...)` doesn't seem to take effect in other processes.

You're probably using the default `LocMemCache` (Django's in-memory per-process cache). When one process writes a value, it invalidates its own cache — but other processes have separate in-memory caches and won't see the change until their cache entry expires or is invalidated.

**Fix:** Switch to a shared cache backend like Redis in production:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}
```

See the [Caching guide](guides/caching.md) for details.

---

## Encryption

### After rotating `SECRET_KEY`, reading a secret field raises an error or returns garbage.

Encrypted values are keyed to your `SECRET_KEY`. Rotating the key makes all existing encrypted values unreadable.

**Before rotating your key**, read and store all secret field values:

```python
secrets = {
    "integrations.stripe.secret_key": config.get("integrations.stripe.secret_key"),
    # ... all other SecretFrontendModel fields
}
```

Then rotate `SECRET_KEY`, restart, and re-save the values:

```python
config.set_many(secrets)
```

See the [Encryption guide](guides/encryption.md) for the full procedure.

---

### A secret field I saved shows as blank/empty in the admin UI. Did the save fail?

No — this is expected behaviour. Secret fields are **write-only** in the admin UI. The input is always rendered empty, even when a value is stored. This is intentional to prevent credentials from being exposed in the browser.

To verify a secret value is saved, check `config.is_set(...)`:

```python
config.is_set("integrations.stripe.secret_key")  # True if a value has been saved
```

---

## Admin UI

### Non-staff users see a login page when they visit `/admin/config/`. Is that correct?

Yes. Both config views require `is_staff=True`, identical to the Django admin. Non-staff users are redirected to the admin login page.

If you need to expose configuration to non-staff users, you'll need to build your own views using the `config` accessor.

---

### Saving the config form in the admin doesn't seem to do anything / changes aren't reflected.

Check the following:

1. **Validation errors** — if any field fails validation, the form is re-rendered with error messages. Look for red error text below any field.
2. **Cache backend** — if you're running multiple processes without a shared cache, the process that received the save request has fresh values, but others may be stale. See the caching FAQ above.
3. **`on_save` callback exceptions** — if a field has an `on_save` callback that raises an exception, it will bubble up as a 500 error. Check your server logs.

---

## Schema design

### I renamed a field. Now `config.get(...)` raises `FieldNotFoundError` in production.

Renaming a field effectively creates a new field. The old database row isn't deleted — it becomes orphaned. Any code still referencing the old path will raise `FieldNotFoundError`.

**Migration path:**

1. Add the new field name to your `sysconfig.py` alongside the old one (with the same default).
2. Deploy.
3. Migrate any stored values from the old path to the new one:
   ```python
   old_value = config.get("myapp.general.old_name")
   config.set("myapp.general.new_name", old_value)
   ```
4. Remove the old field from `sysconfig.py` and any code references.
5. Optionally, clean up the orphaned database row manually.

---

### I removed a field from the schema. Is the old database row a problem?

No. Orphaned rows (rows in `ConfigValue` for paths that no longer exist in code) are ignored at runtime. They don't cause errors. You can clean them up manually with a management command or Django shell if you want to keep the table tidy:

```python
from django_sysconfig.models import ConfigValue
ConfigValue.objects.filter(path="myapp.general.old_field").delete()
```

---

### Can I have the same field in two different apps?

Yes. Each field is scoped to its `app_label.section.field` path. `appA.general.site_name` and `appB.general.site_name` are entirely separate values.

---

## Testing

### How do I override config values in tests?

Use `config.set(...)` in your test setup, or patch the accessor directly:

```python
from django_sysconfig.accessor import config

def test_maintenance_mode(client):
    config.set("myapp.general.maintenance_mode", True)
    response = client.get("/")
    assert response.status_code == 503
```

If you're using pytest, consider a fixture that resets values after each test:

```python
import pytest
from django_sysconfig.accessor import config

@pytest.fixture(autouse=True)
def reset_maintenance_mode():
    config.set("myapp.general.maintenance_mode", False)
    yield
    config.set("myapp.general.maintenance_mode", False)
```

For unit tests that shouldn't touch the database at all, you can mock `config.get`:

```python
from unittest.mock import patch

def test_uses_config_value():
    with patch("myapp.views.config.get", return_value="Mocked Name"):
        response = client.get("/")
        assert b"Mocked Name" in response.content
```

---

## Something else isn't working

If your issue isn't covered here:

1. Search the [GitHub Issues](https://github.com/krishnamodepalli/django-sysconfig/issues) — it may have been reported and answered already.
2. Open a new issue with as much context as possible: Python version, Django version, your `sysconfig.py`, and the full traceback if there is one.
