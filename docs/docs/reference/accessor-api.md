# Accessor API Reference

The `config` object is your single interface to all configuration values. Import it once:

```python
from django_sysconfig.accessor import config
```

It's a module-level singleton — import it anywhere, use it everywhere.

---

## Path notation

All methods that accept a `path` argument use **dot notation** with exactly three segments:

```
app_label.section.field
```

For example: `"billing.pricing.tax_rate"`, `"myapp.general.site_name"`.

If the path doesn't have exactly three dot-separated parts, `InvalidPathError` is raised.

---

## Reading

### `config.get(path, default=<unset>)`

Returns the typed value for the given path.

- If a value has been saved to the database, that value is returned (deserialized to the correct Python type).
- If no value is saved, the field's defined `default` is returned.
- If `default` is passed and the field has no saved value and no field-level default, that fallback is returned. Invalid paths and unknown apps/fields always raise — `default` does not suppress them.

```python
# Returns the saved value or the field's default
site_name = config.get("myapp.general.site_name")     # str
max_items = config.get("myapp.general.max_items")     # int
live_mode = config.get("billing.general.live_mode")   # bool

# Fallback for a registered field with no saved value and no field default
value = config.get("myapp.general.some_field", default=None)
```

**Returns:** The deserialized value in its correct Python type.
**Raises:** `InvalidPathError`, `AppNotFoundError`, `FieldNotFoundError` (unless `default` is provided for unregistered paths).

---

### `config.all(app_label)`

Returns all configuration values for an entire app as a nested dictionary.

```python
config.all("billing")
# {
#   "general": {"live_mode": False},
#   "pricing": {"tax_rate": Decimal("0.20"), "trial_days": 14},
# }
```

**Returns:** `dict[str, dict[str, Any]]` — `{section_name: {field_name: value}}`
**Raises:** `AppNotFoundError` if `app_label` has no registered config.

---

### `config.section(path)`

Returns all configuration values for a single section as a flat dictionary.

The `path` here is two segments: `app_label.section`.

```python
config.section("billing.pricing")
# {"tax_rate": Decimal("0.20"), "trial_days": 14, "free_tier_limit": 10}
```

**Returns:** `dict[str, Any]` — `{field_name: value}`
**Raises:** `InvalidPathError`, `AppNotFoundError`, `FieldNotFoundError`.

---

### `config.exists(path)`

Returns `True` if the given path is registered in the schema (i.e., the app, section, and field all exist in code). Does not query the database.

```python
config.exists("myapp.general.site_name")    # True
config.exists("myapp.general.nonexistent")  # False
config.exists("no_such_app.x.y")            # False
```

**Returns:** `bool`
**Raises:** Nothing — returns `False` for any invalid or unknown path.

---

### `config.is_set(path)`

Returns `True` if the field has a value explicitly saved in the database. Returns `False` if the field is only at its default (no row has ever been written).

```python
config.is_set("myapp.general.site_name")  # False on fresh install
# ... staff member saves the value via admin UI ...
config.is_set("myapp.general.site_name")  # True
```

Useful for onboarding checklists or detecting whether required setup steps have been completed.

**Returns:** `bool`
**Raises:** `InvalidPathError`, `AppNotFoundError`, `FieldNotFoundError`.

---

## Writing

### `config.set(path, value)`

Validates and saves a single value to the database, invalidates the cache, and calls the field's `on_save` callback if defined.

```python
config.set("myapp.general.site_name", "Acme Corp")
config.set("myapp.general.max_items", 500)
config.set("billing.general.live_mode", True)
config.set("billing.pricing.tax_rate", Decimal("0.15"))
```

The value is validated against the field's `validators` before being written. If validation fails, `ConfigValidationError` is raised and nothing is saved.

**Returns:** `None`
**Raises:** `InvalidPathError`, `AppNotFoundError`, `FieldNotFoundError`, `ConfigValidationError`, `ConfigValueError`.

---

### `config.set_many(values)`

Validates and saves multiple values atomically in a single database transaction. Cache invalidation and `on_save` callbacks fire after the transaction commits, one per changed path.

```python
config.set_many({
    "myapp.general.site_name": "Acme Corp",
    "myapp.general.max_items": 500,
    "billing.pricing.tax_rate": Decimal("0.15"),
})
```

If any value fails validation, the entire transaction is rolled back and no values are saved.

**Returns:** `int` Number of values set
**Raises:** `InvalidPathError`, `AppNotFoundError`, `FieldNotFoundError`, `ConfigValidationError`, `ConfigValueError`.

---

## Thread safety

The `config` accessor is thread-safe. The underlying `ConfigRegistry` is read-only after startup. All reads and writes go through Django's cache and ORM, which are designed for concurrent access.
