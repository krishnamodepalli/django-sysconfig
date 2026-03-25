"""
Tests for ConfigAccessor.set()

Covers:
- Persisting values to DB for all field types
- Overwriting an existing value
- Cache invalidation and re-population after set
- on_save callback invoked with correct arguments
- Validation errors raised before any DB write
- Invalid path / unknown app / unknown field
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from django_sysconfig.exceptions import (
    AppNotFoundError,
    ConfigValidationError,
    FieldNotFoundError,
    InvalidPathError,
)
from django_sysconfig.models import ConfigValue

# ---------------------------------------------------------------------------
# Happy path — all field types
# ---------------------------------------------------------------------------


class TestSetHappyPath:

    def test_set_string(self, config):
        config.set("testapp.general.site_name", "New Name")
        assert config.get("testapp.general.site_name") == "New Name"

    def test_set_integer(self, config):
        config.set("testapp.general.max_items", 500)
        assert config.get("testapp.general.max_items") == 500

    def test_set_decimal(self, config):
        config.set("testapp.general.price", Decimal("49.99"))
        assert config.get("testapp.general.price") == Decimal("49.99")

    def test_set_boolean_false(self, config):
        config.set("testapp.general.enabled", False)
        assert config.get("testapp.general.enabled") is False

    def test_set_boolean_true(self, config):
        config.set("testapp.general.enabled", True)
        assert config.get("testapp.general.enabled") is True

    def test_set_select(self, config):
        config.set("testapp.advanced.mode", "debug")
        assert config.get("testapp.advanced.mode") == "debug"

    def test_set_port(self, config):
        config.set("testapp.advanced.port", 3000)
        assert config.get("testapp.advanced.port") == 3000


# ---------------------------------------------------------------------------
# DB persistence
# ---------------------------------------------------------------------------


class TestSetPersistence:

    def test_value_written_to_db(self, config):
        config.set("testapp.general.max_items", 77)
        row = ConfigValue.objects.get(
            app_label="testapp",
            path="general.max_items",
        )
        assert row.value == "77"

    def test_overwrite_updates_existing_row(self, config):
        config.set("testapp.general.max_items", 10)
        config.set("testapp.general.max_items", 20)

        rows = ConfigValue.objects.filter(
            app_label="testapp",
            path="general.max_items",
        )
        # Should be exactly one row, not two
        assert rows.count() == 1
        assert config.get("testapp.general.max_items") == 20


# ---------------------------------------------------------------------------
# Cache behaviour
# ---------------------------------------------------------------------------


class TestSetCache:

    def test_cache_holds_new_value_after_set(
        self, config, django_capture_on_commit_callbacks
    ):
        from django_sysconfig.cache import config_cache

        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.max_items", 55)
        cached = config_cache.get("testapp.general.max_items")
        assert cached is not config_cache.NOT_FOUND

    def test_get_after_set_does_not_hit_db(
        self, config, django_assert_num_queries, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.max_items", 55)

        with django_assert_num_queries(0):
            value = config.get("testapp.general.max_items")

        assert value == 55


# ---------------------------------------------------------------------------
# on_save callback
# ---------------------------------------------------------------------------


class TestSetOnSave:

    def test_on_save_called_after_set(
        self, config, registry, django_capture_on_commit_callbacks
    ):
        callback = MagicMock()

        from django_sysconfig.frontend_models import IntegerFrontendModel
        from django_sysconfig.registry import Field
        from tests.conftest import TEST_APP

        section = registry.get_config(TEST_APP).sections["general"]
        new_field = Field(
            IntegerFrontendModel, label="Max Items", default=10, on_save=callback
        )
        new_field.name = "max_items"
        section._fields["max_items"] = new_field

        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.max_items", 42)

        callback.assert_called_once()

    def test_on_save_receives_correct_arguments(
        self, config, registry, django_capture_on_commit_callbacks
    ):
        received = {}

        def capture(path, new_value, old_value):
            received["path"] = path
            received["new_value"] = new_value
            received["old_value"] = old_value

        from django_sysconfig.frontend_models import IntegerFrontendModel
        from django_sysconfig.registry import Field
        from tests.conftest import TEST_APP

        section = registry.get_config(TEST_APP).sections["general"]
        new_field = Field(
            IntegerFrontendModel, label="Max Items", default=10, on_save=capture
        )
        new_field.name = "max_items"
        section._fields["max_items"] = new_field

        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.max_items", 99)

        assert received["path"] == "testapp.general.max_items"
        assert received["new_value"] == 99

    def test_on_save_receives_old_value(
        self, config, registry, django_capture_on_commit_callbacks
    ):
        received = {}

        def capture(path, new_value, old_value):
            received["old_value"] = old_value

        from django_sysconfig.frontend_models import IntegerFrontendModel
        from django_sysconfig.registry import Field
        from tests.conftest import TEST_APP

        section = registry.get_config(TEST_APP).sections["general"]
        new_field = Field(
            IntegerFrontendModel, label="Max Items", default=10, on_save=capture
        )
        new_field.name = "max_items"
        section._fields["max_items"] = new_field

        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.max_items", 50)  # differs from default of 10
        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.max_items", 20)  # update

        assert received["old_value"] == 50

    def test_on_save_receives_field_default_as_old_value_on_first_set(
        self, config, registry, django_capture_on_commit_callbacks
    ):
        # When no prior DB row exists, old_value should fall back to field.default
        received = {}

        def capture(path, new_value, old_value):
            received["old_value"] = old_value

        from django_sysconfig.frontend_models import IntegerFrontendModel
        from django_sysconfig.models import ConfigValue
        from django_sysconfig.registry import Field
        from tests.conftest import TEST_APP

        section = registry.get_config(TEST_APP).sections["general"]
        new_field = Field(
            IntegerFrontendModel, label="Max Items", default=10, on_save=capture
        )
        new_field.name = "max_items"
        section._fields["max_items"] = new_field

        # Delete the seeded row so there is no prior DB value
        ConfigValue.objects.filter(
            app_label="testapp", path="general.max_items"
        ).delete()

        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.max_items", 99)

        assert received["old_value"] == 10


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class TestSetValidation:

    def test_raises_for_out_of_range_integer(self, config):
        with pytest.raises(ConfigValidationError):
            config.set("testapp.general.max_items", 9999)  # max is 1000

    def test_raises_for_below_range_integer(self, config):
        with pytest.raises(ConfigValidationError):
            config.set("testapp.general.max_items", 0)  # min is 1

    def test_raises_for_empty_string_on_not_empty_field(self, config):
        with pytest.raises(ConfigValidationError):
            config.set("testapp.general.site_name", "")

    def test_raises_for_invalid_port(self, config):
        with pytest.raises(ConfigValidationError):
            config.set("testapp.advanced.port", 99999)

    def test_db_not_written_on_validation_error(self, config):
        original = config.get("testapp.general.max_items")

        with pytest.raises(ConfigValidationError):
            config.set("testapp.general.max_items", 9999)

        assert config.get("testapp.general.max_items") == original


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestSetErrors:

    def test_raises_for_invalid_path_format(self, config):
        with pytest.raises(InvalidPathError):
            config.set("invalid", 10)

    def test_raises_for_unknown_app(self, config):
        with pytest.raises(AppNotFoundError):
            config.set("unknown_app.general.max_items", 10)

    def test_raises_for_unknown_field(self, config):
        with pytest.raises(FieldNotFoundError):
            config.set("testapp.general.unknown_field", 10)
