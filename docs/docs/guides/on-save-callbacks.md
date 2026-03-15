# on_save Callbacks

Every field can have an `on_save` callback — a Python callable that fires after a value has been successfully written to the database and the cache has been invalidated. Use callbacks to react to configuration changes: flush application-level caches, notify your team, trigger webhooks, or update downstream systems.

---

## Defining a callback

Pass a callable to the `on_save` parameter of `Field`. The callable receives three arguments:

| Argument    | Type  | Description                          |
| ----------- | ----- | ------------------------------------ |
| `path`      | `str` | The full dot-notation path           |
| `new_value` | `Any` | The new value (already deserialized) |
| `old_value` | `Any` | The previous value (deserialized), or `None` if this is the first save |

```python
def on_maintenance_mode_change(path: str, new_value: bool, old_value: bool) -> None:
    if new_value and not old_value:
        notify_ops_team("Maintenance mode enabled")

maintenance_mode = Field(
    BooleanFrontendModel,
    label="Maintenance Mode",
    default=False,
    on_save=on_maintenance_mode_change,
)
```

---

## When the callback fires

The callback fires **after** the database write and cache invalidation. The sequence is:

1. Value is validated
2. Value is written to the database
3. Cache entry is invalidated
4. `on_save` callback is called

If the callback raises an exception, the exception propagates to the caller (e.g., the admin UI will show an error), but the database write has **already committed**. Design your callbacks to be idempotent and tolerant of failure, or wrap them in try/except if you want to suppress errors.

---

## Common patterns

### Clearing an application-level cache

```python
from django.core.cache import cache

def clear_homepage_cache(path, new_value, old_value):
    cache.delete("homepage_rendered")
    cache.delete("featured_products")

homepage_product_count = Field(
    IntegerFrontendModel,
    label="Featured Products Count",
    default=6,
    on_save=clear_homepage_cache,
)
```

---

### Sending a Slack notification

```python
import requests
from django.conf import settings

def notify_slack(path, new_value, old_value):
    if not hasattr(settings, "SLACK_WEBHOOK_URL"):
        return
    requests.post(settings.SLACK_WEBHOOK_URL, json={
        "text": f"Config changed: `{path}` → `{new_value}` (was `{old_value}`)"
    }, timeout=5)

live_mode = Field(
    BooleanFrontendModel,
    label="Live Mode",
    default=False,
    on_save=notify_slack,
)
```

---

### Logging changes to an audit trail

```python
import logging

audit_log = logging.getLogger("config.audit")

def log_change(path, new_value, old_value):
    audit_log.info(
        "Config value changed",
        extra={"path": path, "new_value": new_value, "old_value": old_value},
    )
```

You can reuse this callback across multiple fields:

```python
@register_config("billing")
class BillingConfig:
    class General(Section):
        live_mode = Field(
            BooleanFrontendModel,
            label="Live Mode",
            default=False,
            on_save=log_change,
        )

    class Pricing(Section):
        tax_rate = Field(
            DecimalFrontendModel,
            label="Tax Rate",
            default=Decimal("0.20"),
            on_save=log_change,
        )
```

---

### Refreshing a third-party SDK client

Some SDKs are initialized with credentials at startup and need to be re-initialized when those credentials change:

```python
import stripe as stripe_sdk

def reinitialize_stripe(path, new_value, old_value):
    stripe_sdk.api_key = new_value

stripe_secret_key = Field(
    SecretFrontendModel,
    label="Stripe Secret Key",
    on_save=reinitialize_stripe,
)
```

---

## Callbacks and `set_many`

When you call `config.set_many({...})`, each field's `on_save` callback fires individually after the transaction commits, once per changed path. The callbacks fire in the order the keys appear in the dictionary.

---

## Asynchronous callbacks

`on_save` callbacks are called synchronously, in the same request/response cycle as the save. For expensive operations (sending emails, making HTTP requests, running background jobs), dispatch to a task queue instead:

```python
from myapp.tasks import notify_team_async  # Celery task, for example

def on_live_mode_change(path, new_value, old_value):
    if new_value:
        notify_team_async.delay("Billing is now in live mode!")

live_mode = Field(
    BooleanFrontendModel,
    label="Live Mode",
    default=False,
    on_save=on_live_mode_change,
)
```
