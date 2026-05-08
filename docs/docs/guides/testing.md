# Testing Guide

This guide covers best practices for testing application code that interacts with `django-sysconfig`. Because the configuration registry is a global singleton and interacts with the database, proper isolation is critical to prevent state leakage and "flaky" tests.

---

## Why Isolation Matters

When testing, you want each test to start with a "clean slate." Without proper isolation, you may encounter:

* **State Leakage:** A `config.set()` call in `test_a` persists in memory and causes `test_b` to fail unexpectedly.
* **Database Pollution:** `config.get()` might attempt to hit the real database if the Django test environment isn't correctly initialized.
* **The on_commit Gotcha:** Features like **cache refreshing** or **on_save callbacks** often rely on `transaction.on_commit()`. In standard tests, transactions are rolled back, meaning these callbacks never fire.

---

## 1. Using the `override_sysconfig` Utility

The most reliable way to test different configuration states is the `override_sysconfig` utility. It takes a "snapshot" of the registry before the test and restores it afterward.

### As a Decorator
Use this when a specific configuration applies to the entire test function.

```python
from django_sysconfig import override_sysconfig

@override_sysconfig(myapp__general__beta_features=True, myapp__advanced__max_retries=5)
def test_beta_logic():
    # Inside this test, these values are locked in
    assert my_function_using_config() is True
```

### As a Context Manager

Use this when you need to test multiple configuration states within a single test.

```python
from django_sysconfig import override_sysconfig

def test_dynamic_threshold():
    with override_sysconfig(myapp__general__threshold=10):
        assert calculate_logic() == "Low"

    with override_sysconfig(myapp__general__threshold=100):
        assert calculate_logic() == "High"
```

## 2. Global Registry Isolation (pytest)

If your project uses `pytest-django`, you should ensure the registry is reset automatically between every test run. Add an "autouse" fixture to your `conftest.py`:

```python
import pytest
from django_sysconfig.registry import config_registry

@pytest.fixture(autouse=True)
def isolate_sysconfig():
    """Reset the config registry before and after every test."""
    config_registry.reset_to_defaults()
    yield
    config_registry.reset_to_defaults()
```

## 3. Handling on_commit Side Effects

If your configuration logic triggers background tasks or cache updates via `on_commit`, a standard `db` fixture will not trigger them because the transaction is never committed.

There are two primary options to handle this constraint:

### Option A: Use transactional_db

This allows the transaction to actually commit, triggering all associated callbacks.

```python
import pytest
from django_sysconfig.accessor import config
from django.core.cache import cache

@pytest.mark.django_db(transaction=True)
def test_cache_refresh_on_config_change():
    config.set("myapp.general.maintenance_mode", True)
    # The transaction commits, and the refresh callback fires
    assert cache.get("is_maint_mode") is True
```

### Option B: Capture Callbacks

If you want to avoid the performance hit of a transactional database, use Django's capture utility to force execution.

```python
from django.test import TestCase
from django_sysconfig.accessor import config

class CallbackTests(TestCase):
    def test_callback_execution(self):
        with self.captureOnCommitCallbacks(execute=True):
            config.set("myapp.display.theme", "dark")

        # Side effects from 'on_save' or 'on_commit' are now applied
        assert check_theme_applied("dark")
```
