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

@override_sysconfig(ENABLE_BETA_FEATURES=True, MAX_RETRIES=5)
def test_beta_logic():
    # Inside this test, these values are locked in
    assert my_function_using_config() is True




####Use this when you need to test multiple configuration states within a single test.
from django_sysconfig import override_sysconfig

def test_dynamic_threshold():
    with override_sysconfig(THRESHOLD=10):
        assert calculate_logic() == "Low"
        
    with override_sysconfig(THRESHOLD=100):
        assert calculate_logic() == "High"




####Global Registry Isolation (pytest)
import pytest
from django_sysconfig import registry

@pytest.fixture(autouse=True)
def isolate_sysconfig():
    """Reset the config registry before and after every test."""
    registry.reset_to_defaults()
    yield
    registry.reset_to_defaults()


###For Handling on_commit Side Effects
## You can use 2 options and they are 
#Opt-A   Use transactional_db
import pytest

@pytest.mark.django_db(transaction=True)
def test_cache_refresh_on_config_change():
    config.set("MAINTENANCE_MODE", True)
    # The transaction commits, and the refresh callback fires
    assert cache.get("is_maint_mode") is True


#Opt-b   Capture Callbacks
from django.test import TestCase

def test_callback_execution(self):
    with self.captureOnCommitCallbacks(execute=True):
        config.set("THEME", "dark")
    
    # Side effects from 'on_save' or 'on_commit' are now applied
    assert check_theme_applied("dark")