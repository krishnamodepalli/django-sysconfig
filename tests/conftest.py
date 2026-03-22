"""
Shared fixtures and test configuration for django-sysconfig tests.

Provides:
- A registered test app config covering all field types (``testapp``).
- Per-test isolation: registry, cache, and DB records are cleaned up
  after every test so tests cannot bleed state into each other.
- Convenience fixtures: ``config`` (the accessor) and ``registry``.
"""

from decimal import Decimal

import pytest
from django.core.cache import cache

from django_sysconfig.registry import AppConfigDefinition

# ---------------------------------------------------------------------------
# Test app label
# ---------------------------------------------------------------------------

TEST_APP = "testapp"

# ---------------------------------------------------------------------------
# Test config definition
#
# Registered once per session (Django's autodiscovery won't pick it up in
# tests, so we do it manually here).  The ``isolate_registry`` fixture
# (function-scoped) clears and re-registers it before every test so each
# test starts with a clean slate.
# ---------------------------------------------------------------------------


def make_test_config():
    """Build and return the test config class without registering it."""
    from django_sysconfig.frontend_models import (
        BooleanFrontendModel,
        DecimalFrontendModel,
        IntegerFrontendModel,
        SecretFrontendModel,
        SelectFrontendModel,
        StringFrontendModel,
        TextareaFrontendModel,
    )
    from django_sysconfig.registry import Field, Section
    from django_sysconfig.validators import (
        MaxLengthValidator,
        NotEmptyValidator,
        PortValidator,
        RangeValidator,
    )

    class TestAppConfig:
        class General(Section):
            label = "General"
            sort_order = 10

            site_name = Field(
                StringFrontendModel,
                label="Site Name",
                default="Test Site",
                validators=[NotEmptyValidator(), MaxLengthValidator(100)],
            )
            description = Field(
                TextareaFrontendModel,
                label="Description",
                default="A test site.",
            )
            max_items = Field(
                IntegerFrontendModel,
                label="Max Items",
                default=10,
                validators=[RangeValidator(min_value=1, max_value=1000)],
            )
            price = Field(
                DecimalFrontendModel,
                label="Price",
                default=Decimal("9.99"),
            )
            enabled = Field(
                BooleanFrontendModel,
                label="Enabled",
                default=True,
            )

        class Advanced(Section):
            label = "Advanced"
            sort_order = 20

            mode = Field(
                SelectFrontendModel,
                label="Mode",
                default="standard",
                choices=[
                    ("standard", "Standard"),
                    ("strict", "Strict"),
                    ("debug", "Debug"),
                ],
            )
            api_key = Field(
                SecretFrontendModel,
                label="API Key",
                default="",
            )
            port = Field(
                IntegerFrontendModel,
                label="Port",
                default=8080,
                validators=[PortValidator()],
            )

    return TestAppConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolate_registry(request, db):
    """
    Reset the config registry and cache before every test, then re-register
    the test app config so each test starts from a known state.

    ``db`` is pytest-django's built-in fixture; requesting it here ensures
    Django's test DB is set up and migrations have run before we attempt to
    write ConfigValue rows.
    """
    if "no_db" in request.keywords:
        yield
        return

    from django_sysconfig.registry import config_registry

    # Clear any registrations left by previous tests or autodiscovery
    config_registry.clear()

    # Clear the cache so no stale values bleed between tests
    cache.clear()

    # Register the canonical test config; this also seeds ConfigValue rows
    # for fields that carry defaults
    test_app_config = make_test_config()
    config_registry.register(TEST_APP, test_app_config)

    config_registry._ensure_db_records(
        TEST_APP,
        AppConfigDefinition(TEST_APP, test_app_config),
    )

    yield

    # Teardown: wipe registry and cache again so the next test's setup is clean
    config_registry.clear()
    cache.clear()


@pytest.fixture(autouse=True)
def auto_capture_on_commit(django_capture_on_commit_callbacks):
    """
    Automatically execute on_commit callbacks after every test.
    Ensures cache refresh and on_save hooks fire consistently
    without needing to wrap individual calls in tests.
    """
    with django_capture_on_commit_callbacks(execute=True):
        yield


@pytest.fixture()
def tmp_json_file(tmp_path):
    """Return a factory that writes a dict as JSON to a temp file and returns its path."""

    def _make(data: dict, filename: str = "config.json") -> str:
        path = tmp_path / filename
        import json

        path.write_text(json.dumps(data))
        return str(path)

    return _make


@pytest.fixture()
def registry():
    """Return the global ConfigRegistry instance."""
    from django_sysconfig.registry import config_registry

    return config_registry


@pytest.fixture()
def config(isolate_registry):
    """Return the global ConfigAccessor instance (with testapp registered)."""
    from django_sysconfig.accessor import config as _config

    return _config
