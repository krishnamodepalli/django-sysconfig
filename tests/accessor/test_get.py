"""
Tests for ConfigAccessor.get()

Covers:
- Returning field defaults when no DB row exists
- Returning DB value after config.set()
- Correct type casting per field type
- Cache hit / miss behaviour
- Invalid path format
- Unknown app label
- Unknown field name
- Caller-supplied default for fields with no value and no field default
- Typed Field API (config.get(Field))
"""

from decimal import Decimal

import pytest

from django_sysconfig.exceptions import (
    AppNotFoundError,
    FieldNotFoundError,
    InvalidPathError,
)

# ---------------------------------------------------------------------------
# Defaults (no DB row set yet)
# ---------------------------------------------------------------------------


class TestGetDefaults:

    def test_returns_string_default(self, config):
        value = config.get("testapp.general.site_name")
        assert value == "Test Site"

    def test_returns_integer_default(self, config):
        value = config.get("testapp.general.max_items")
        assert value == 10

    def test_returns_decimal_default(self, config):
        value = config.get("testapp.general.price")
        assert value == Decimal("9.99")

    def test_returns_boolean_default(self, config):
        value = config.get("testapp.general.enabled")
        assert value is True

    def test_returns_textarea_default(self, config):
        value = config.get("testapp.general.description")
        assert value == "A test site."

    def test_returns_select_default(self, config):
        value = config.get("testapp.advanced.mode")
        assert value == "standard"

    def test_returns_integer_default_for_port(self, config):
        value = config.get("testapp.advanced.port")
        assert value == 8080


# ---------------------------------------------------------------------------
# Correct types returned
# ---------------------------------------------------------------------------


class TestGetTypes:

    def test_integer_field_returns_int(
        self, config, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.max_items", 42)

        value = config.get("testapp.general.max_items")
        assert isinstance(value, int)
        assert value == 42

    def test_decimal_field_returns_decimal(
        self, config, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.price", Decimal("19.99"))

        value = config.get("testapp.general.price")
        assert isinstance(value, Decimal)
        assert value == Decimal("19.99")

    def test_boolean_field_returns_bool(
        self, config, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.enabled", False)

        value = config.get("testapp.general.enabled")
        assert isinstance(value, bool)
        assert value is False

    def test_string_field_returns_str(self, config, django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.site_name", "Hello")

        value = config.get("testapp.general.site_name")
        assert isinstance(value, str)
        assert value == "Hello"


# ---------------------------------------------------------------------------
# DB value overrides default
# ---------------------------------------------------------------------------


class TestGetAfterSet:

    def test_returns_updated_value(self, config):
        config.set("testapp.general.max_items", 99)
        assert config.get("testapp.general.max_items") == 99

    def test_returns_latest_value_after_multiple_sets(self, config):
        config.set("testapp.general.max_items", 10)
        config.set("testapp.general.max_items", 20)
        config.set("testapp.general.max_items", 30)
        assert config.get("testapp.general.max_items") == 30

    def test_overriding_boolean_default(
        self, config, django_capture_on_commit_callbacks
    ):
        assert config.get("testapp.general.enabled") is True
        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.enabled", False)
        assert config.get("testapp.general.enabled") is False

    def test_overriding_select_default(self, config):
        config.set("testapp.advanced.mode", "strict")
        assert config.get("testapp.advanced.mode") == "strict"


# ---------------------------------------------------------------------------
# Null DB value (row exists, value is None)
# ---------------------------------------------------------------------------


class TestGetNullDbValue:
    """Tests for ConfigValue rows that exist but carry value=None."""

    def test_returns_none_not_field_default(self, config):
        from django_sysconfig.models import ConfigValue

        # The fixture seeds the row with the serialized default — overwrite to null
        ConfigValue.objects.filter(
            app_label="testapp", path="general.max_items"
        ).update(value=None)
        # field.default is 10 — stored null must win, not fall through to default
        assert config.get("testapp.general.max_items") is None

    def test_null_is_cached(self, config):
        from django_sysconfig.cache import config_cache
        from django_sysconfig.models import ConfigValue

        ConfigValue.objects.filter(
            app_label="testapp", path="general.max_items"
        ).update(value=None)
        config.get("testapp.general.max_items")
        cached = config_cache.get("testapp.general.max_items")
        assert cached is not config_cache.NOT_FOUND
        assert cached is None

    def test_null_served_from_cache_on_second_call(
        self, config, django_assert_num_queries
    ):
        from django_sysconfig.models import ConfigValue

        ConfigValue.objects.filter(
            app_label="testapp", path="general.max_items"
        ).update(value=None)
        config.get("testapp.general.max_items")  # warm cache
        with django_assert_num_queries(0):
            assert config.get("testapp.general.max_items") is None


# ---------------------------------------------------------------------------
# Cache behaviour
# ---------------------------------------------------------------------------


class TestGetCache:

    def test_cache_is_populated_after_get(self, config):
        from django_sysconfig.cache import config_cache

        path = "testapp.general.max_items"

        # Ensure cache is empty first
        config_cache.invalidate(path)
        assert config_cache.get(path) is config_cache.NOT_FOUND

        # Trigger a get — should populate cache
        config.get(path)
        assert config_cache.get(path) is not config_cache.NOT_FOUND

    def test_cache_is_used_on_second_get(self, config, django_assert_num_queries):
        path = "testapp.general.max_items"

        # First call — hits DB and warms cache
        config.get(path)

        # Second call — should hit cache, zero DB queries
        with django_assert_num_queries(0):
            config.get(path)

    def test_cache_invalidated_after_set(
        self, config, django_capture_on_commit_callbacks
    ):
        path = "testapp.general.max_items"
        config.get(path)  # warm cache

        with django_capture_on_commit_callbacks(execute=True):
            config.set(path, 99)
        # Cache should now hold the new value, not the old one
        assert config.get(path) == 99

    def test_stale_cache_does_not_serve_old_value(
        self, config, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.site_name", "Old")
        assert config.get("testapp.general.site_name") == "Old"

        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.site_name", "New")
        assert config.get("testapp.general.site_name") == "New"


# ---------------------------------------------------------------------------
# Caller-supplied default
# ---------------------------------------------------------------------------


class TestGetCallerDefault:

    def test_caller_default_not_used_when_field_has_default(self, config):
        # Field default is "Test Site", caller default should be ignored
        value = config.get("testapp.general.site_name", default="Fallback")
        assert value == "Test Site"

    def test_caller_default_not_used_when_value_is_set(self, config):
        config.set("testapp.general.site_name", "Actual")
        value = config.get("testapp.general.site_name", default="Fallback")
        assert value == "Actual"

    def test_caller_default_used_when_no_field_default(self, config):
        from django_sysconfig.models import ConfigValue

        # The fixture seeds a null row for no_default — delete it to test the no-row path
        ConfigValue.objects.filter(
            app_label="testapp", path="general.no_default"
        ).delete()
        assert (
            config.get("testapp.general.no_default", default="fallback") == "fallback"
        )

    def test_caller_default_not_cached_between_calls(self, config):
        from django_sysconfig.models import ConfigValue

        # Regression: caller's default must not be cached — each call uses its own
        ConfigValue.objects.filter(
            app_label="testapp", path="general.no_default"
        ).delete()
        assert config.get("testapp.general.no_default", default="first") == "first"
        assert config.get("testapp.general.no_default", default="second") == "second"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestGetErrors:

    def test_raises_for_invalid_path_format(self, config):
        with pytest.raises(InvalidPathError):
            config.get("invalid")

    def test_raises_for_two_part_path(self, config):
        with pytest.raises(InvalidPathError):
            config.get("testapp.general")

    def test_raises_for_four_part_path(self, config):
        with pytest.raises(InvalidPathError):
            config.get("testapp.general.max_items.extra")

    def test_raises_for_unknown_app(self, config):
        with pytest.raises(AppNotFoundError):
            config.get("unknown_app.general.max_items")

    def test_raises_for_unknown_section(self, config):
        with pytest.raises(FieldNotFoundError):
            config.get("testapp.unknown_section.max_items")

    def test_raises_for_unknown_field(self, config):
        with pytest.raises(FieldNotFoundError):
            config.get("testapp.general.unknown_field")

    def test_raises_for_empty_path(self, config):
        with pytest.raises(InvalidPathError):
            config.get("")

    def test_raises_type_error_for_invalid_type(self, config):
        with pytest.raises(TypeError):
            config.get(123)


# ---------------------------------------------------------------------------
# Typed Field API
# ---------------------------------------------------------------------------


class TestGetWithField:
    """Tests for config.get(Field) — typed accessor API."""

    def test_returns_field_default(self, config, registry):
        field = registry.get_config("testapp").sections["general"].max_items
        assert config.get(field) == 10

    def test_returns_db_value_after_set(self, config, registry):
        config.set("testapp.general.max_items", 42)
        field = registry.get_config("testapp").sections["general"].max_items
        assert config.get(field) == 42

    def test_returns_correct_type(self, config, registry):
        field = registry.get_config("testapp").sections["general"].max_items
        assert isinstance(config.get(field), int)

    def test_matches_string_path(self, config, registry):
        field = registry.get_config("testapp").sections["general"].max_items
        assert config.get(field) == config.get("testapp.general.max_items")

    def test_populates_cache(self, config, registry):
        from django_sysconfig.cache import config_cache

        field = registry.get_config("testapp").sections["general"].max_items
        config_cache.invalidate(field.full_path)
        config.get(field)
        assert config_cache.get(field.full_path) is not config_cache.NOT_FOUND

    def test_hits_cache_on_second_call(
        self, config, registry, django_assert_num_queries
    ):
        field = registry.get_config("testapp").sections["general"].max_items
        config.get(field)  # warm cache
        with django_assert_num_queries(0):
            config.get(field)

    def test_shares_cache_with_string_api(
        self, config, registry, django_assert_num_queries
    ):
        # Warm cache via string, then get via Field — should not hit DB
        config.get("testapp.general.max_items")
        field = registry.get_config("testapp").sections["general"].max_items
        with django_assert_num_queries(0):
            config.get(field)

    def test_returns_none_for_null_db_value(self, config, registry):
        from django_sysconfig.models import ConfigValue

        field = registry.get_config("testapp").sections["general"].max_items
        ConfigValue.objects.update_or_create(
            app_label="testapp",
            path="general.max_items",
            defaults={"value": None},
        )
        # field.default is 10 — stored null must win
        assert config.get(field) is None

    def test_returns_caller_default_when_no_field_default(self, config, registry):
        from django_sysconfig.models import ConfigValue

        field = registry.get_config("testapp").sections["general"].no_default
        ConfigValue.objects.filter(
            app_label="testapp", path="general.no_default"
        ).delete()
        assert config.get(field, default="fallback") == "fallback"

    def test_caller_default_not_cached_between_calls(self, config, registry):
        from django_sysconfig.models import ConfigValue

        field = registry.get_config("testapp").sections["general"].no_default
        ConfigValue.objects.filter(
            app_label="testapp", path="general.no_default"
        ).delete()
        assert config.get(field, default="first") == "first"
        assert config.get(field, default="second") == "second"
