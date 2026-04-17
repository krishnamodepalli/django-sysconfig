"""
Tests for ConfigAccessor.set_many()

Covers:
- Setting multiple values in one call
- Atomicity — full rollback if any value fails
- Return value (count of values set)
- on_save callbacks fired for each field that defines one
- Cache updated correctly for all paths
"""

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
# Happy path
# ---------------------------------------------------------------------------


class TestSetManyHappyPath:
    def test_sets_multiple_values(self, config):
        config.set_many(
            {
                "testapp.general.site_name": "Bulk Site",
                "testapp.general.max_items": 200,
                "testapp.general.enabled": False,
            }
        )

        assert config.get("testapp.general.site_name") == "Bulk Site"
        assert config.get("testapp.general.max_items") == 200
        assert config.get("testapp.general.enabled") is False

    def test_returns_count_of_values_set(self, config):
        result = config.set_many(
            {
                "testapp.general.site_name": "A",
                "testapp.general.max_items": 5,
            }
        )
        assert result == 2

    def test_sets_values_across_sections(self, config):
        config.set_many(
            {
                "testapp.general.max_items": 100,
                "testapp.advanced.port": 9000,
                "testapp.advanced.mode": "debug",
            }
        )

        assert config.get("testapp.general.max_items") == 100
        assert config.get("testapp.advanced.port") == 9000
        assert config.get("testapp.advanced.mode") == "debug"

    def test_single_item_dict_works(self, config):
        config.set_many({"testapp.general.max_items": 77})
        assert config.get("testapp.general.max_items") == 77

    def test_empty_dict_returns_zero(self, config):
        result = config.set_many({})
        assert result == 0


# ---------------------------------------------------------------------------
# Atomicity
# ---------------------------------------------------------------------------


class TestSetManyAtomicity:
    def test_all_rolled_back_if_one_fails_validation(self, config):
        original_name = config.get("testapp.general.site_name")
        original_items = config.get("testapp.general.max_items")

        with pytest.raises(ConfigValidationError):
            config.set_many(
                {
                    "testapp.general.site_name": "Should Not Stick",
                    "testapp.general.max_items": 9999,  # exceeds RangeValidator max
                }
            )

        # Both values should be unchanged
        assert config.get("testapp.general.site_name") == original_name
        assert config.get("testapp.general.max_items") == original_items

    def test_all_rolled_back_if_one_path_is_unknown(self, config):
        original = config.get("testapp.general.site_name")

        with pytest.raises((FieldNotFoundError, AppNotFoundError, InvalidPathError)):
            config.set_many(
                {
                    "testapp.general.site_name": "Should Not Stick",
                    "testapp.general.nonexistent_field": "value",
                }
            )

        assert config.get("testapp.general.site_name") == original

    def test_no_partial_db_writes_on_failure(self, config):
        initial_count = ConfigValue.objects.filter(app_label="testapp").count()

        with pytest.raises(ConfigValidationError):
            config.set_many(
                {
                    "testapp.general.site_name": "X",
                    "testapp.general.max_items": 99999,  # invalid
                }
            )

        # Row count should be the same as before — nothing extra committed
        assert ConfigValue.objects.filter(app_label="testapp").count() == initial_count


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class TestSetManyCache:
    def test_all_paths_cached_after_set_many(
        self, config, django_capture_on_commit_callbacks
    ):
        from django_sysconfig.cache import config_cache

        paths = [
            "testapp.general.site_name",
            "testapp.general.max_items",
        ]

        with django_capture_on_commit_callbacks(execute=True):
            config.set_many(
                {
                    "testapp.general.site_name": "Cached",
                    "testapp.general.max_items": 10,
                }
            )

        for path in paths:
            assert config_cache.get(path) is not config_cache.NOT_FOUND

    def test_get_after_set_many_does_not_hit_db(
        self, config, django_assert_num_queries, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            config.set_many(
                {
                    "testapp.general.site_name": "Cached",
                    "testapp.general.max_items": 10,
                }
            )

        with django_assert_num_queries(0):
            config.get("testapp.general.site_name")
            config.get("testapp.general.max_items")


# ---------------------------------------------------------------------------
# on_save callbacks
# ---------------------------------------------------------------------------


class TestSetManyOnSave:
    def test_on_save_fired_for_each_field_with_callback(
        self, config, registry, django_capture_on_commit_callbacks
    ):
        callback_a = MagicMock()
        callback_b = MagicMock()

        from django_sysconfig.frontend_models import (
            IntegerFrontendModel,
            StringFrontendModel,
        )
        from django_sysconfig.registry import Field
        from tests.conftest import TEST_APP

        section = registry.get_config(TEST_APP).sections["general"]

        field_a = Field(
            StringFrontendModel,
            label="Site Name",
            default="Test Site",
            on_save=callback_a,
        )
        field_a.name = "site_name"
        section._fields["site_name"] = field_a

        field_b = Field(
            IntegerFrontendModel, label="Max Items", default=10, on_save=callback_b
        )
        field_b.name = "max_items"
        section._fields["max_items"] = field_b

        with django_capture_on_commit_callbacks(execute=True):
            config.set_many(
                {
                    "testapp.general.site_name": "Hello",
                    "testapp.general.max_items": 50,
                }
            )

        callback_a.assert_called_once()
        callback_b.assert_called_once()

    def test_on_save_not_fired_on_rollback(
        self, config, registry, django_capture_on_commit_callbacks
    ):
        # django_capture_on_commit_callbacks is required here — without it,
        # callbacks never fire anyway under the db fixture, so the test would
        # pass for the wrong reason regardless of rollback behaviour.
        callback = MagicMock()

        from django_sysconfig.frontend_models import StringFrontendModel
        from django_sysconfig.registry import Field
        from tests.conftest import TEST_APP

        section = registry.get_config(TEST_APP).sections["general"]
        new_field = Field(
            StringFrontendModel,
            label="Site Name",
            default="Test Site",
            on_save=callback,
        )
        new_field.name = "site_name"
        section._fields["site_name"] = new_field

        with pytest.raises(ConfigValidationError):
            with django_capture_on_commit_callbacks(execute=True):
                config.set_many(
                    {
                        "testapp.general.site_name": "Hello",
                        "testapp.general.max_items": 99999,  # causes rollback
                    }
                )

        callback.assert_not_called()

    def test_skip_on_save_callbacks_suppresses_all_callbacks(
        self, config, registry, django_capture_on_commit_callbacks
    ):
        callback_a = MagicMock()
        callback_b = MagicMock()

        from django_sysconfig.frontend_models import (
            IntegerFrontendModel,
            StringFrontendModel,
        )
        from django_sysconfig.registry import Field
        from tests.conftest import TEST_APP

        section = registry.get_config(TEST_APP).sections["general"]

        field_a = Field(
            StringFrontendModel,
            label="Site Name",
            default="Test Site",
            on_save=callback_a,
        )
        field_a.name = "site_name"
        section._fields["site_name"] = field_a

        field_b = Field(
            IntegerFrontendModel, label="Max Items", default=1098, on_save=callback_b
        )
        field_b.name = "max_items"
        section._fields["max_items"] = field_b

        with django_capture_on_commit_callbacks(execute=True):
            config.set_many(
                {
                    "testapp.general.site_name": "Hello",
                    "testapp.general.max_items": 50,
                },
                skip_on_save_callbacks=True,
            )

        # Values should be written to DB and cache as normal
        assert config.get("testapp.general.site_name") == "Hello"
        assert config.get("testapp.general.max_items") == 50

        # But neither callback should have fired
        callback_a.assert_not_called()
        callback_b.assert_not_called()

    def test_skip_on_save_callbacks_does_not_affect_cache(
        self, config, django_capture_on_commit_callbacks
    ):
        # Suppressing callbacks must not suppress cache refresh —
        # cache is always updated regardless of skip_on_save_callbacks
        from django_sysconfig.cache import config_cache

        with django_capture_on_commit_callbacks(execute=True):
            config.set_many(
                {
                    "testapp.general.site_name": "Hello World",
                    "testapp.general.max_items": 50,
                },
                skip_on_save_callbacks=True,
            )

        assert (
            config_cache.get("testapp.general.site_name") is not config_cache.NOT_FOUND
        )
        assert (
            config_cache.get("testapp.general.max_items") is not config_cache.NOT_FOUND
        )
        assert config.get("testapp.general.site_name") == "Hello World"
        assert config.get("testapp.general.max_items") == 50
