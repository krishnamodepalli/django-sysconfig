# Accessor API Reference

The `config` object is your single interface to all configuration values. Import it once:

```python
from django_sysconfig.accessor import config
```

It's a module-level singleton — import it anywhere, use it everywhere.

---

## Path notation

All methods accept a path in one of two forms:

- **String path** — dot notation with exactly three segments: `"app_label.section.field"`
- **Field reference** — a `Field` instance from your config class (see [reading-writing guide](/guides/reading-writing#typed-field-api))

If a string path doesn't have exactly three dot-separated parts, `InvalidPathError` is raised.

---

## Reading

### `config.get(path, default=<unset>)`

Returns the typed value for the given path.

- If a value has been saved to the database, that value is returned (deserialized to the correct Python type).
- If no value is saved, the field's defined `default` is returned.
- If `default` is passed and no field-level default, that fallback is returned. Invalid paths and unknown apps/fields always raise — `default` does not suppress them.

```python
# Returns the saved value or the field's default
site_name = config.get("myapp.general.site_name")     # str
max_items = config.get("myapp.general.max_items")     # int
live_mode = config.get("billing.general.live_mode")   # bool

# Fallback for a registered field with no saved value and no field default
value = config.get("myapp.general.some_field", default=None)
```

**Returns:** The deserialized value in its correct Python type.
**Raises:** `InvalidPathError`, `AppNotFoundError`, `FieldNotFoundError`.

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
