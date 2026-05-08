"""
Tests for: python manage.py config set <path> <value>

Covers:
- Sets value successfully
- Success message written to stdout
- Value is NOT echoed back (secret safety)
- CommandError on validation failure with error details
- CommandError for unknown path
- CommandError for invalid path format
"""

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_set(path, value, **kwargs):
    stdout = StringIO()
    stderr = StringIO()
    call_command(
        "config", "set", path, str(value), stdout=stdout, stderr=stderr, **kwargs
    )
    return stdout.getvalue().strip(), stderr.getvalue().strip()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestCmdSet:

    def test_sets_string_value(self, config):
        run_set("testapp.general.site_name", "New Name")
        assert config.get("testapp.general.site_name") == "New Name"

    def test_sets_integer_value(self, config):
        run_set("testapp.general.max_items", 500)
        assert config.get("testapp.general.max_items") == 500

    def test_sets_boolean_value(self, config):
        run_set("testapp.general.enabled", "False")
        assert config.get("testapp.general.enabled") is False

    def test_sets_select_value(self, config):
        run_set("testapp.advanced.mode", "debug")
        assert config.get("testapp.advanced.mode") == "debug"

    def test_sets_port_value(self, config):
        run_set("testapp.advanced.port", 9000)
        assert config.get("testapp.advanced.port") == 9000

    def test_success_message_written_to_stdout(self):
        stdout, _ = run_set("testapp.general.site_name", "Hello")
        assert "✔" in stdout
        assert "testapp.general.site_name" in stdout

    def test_value_not_echoed_in_output(self):
        # Values must never appear in output — secrets could be exposed
        stdout, _ = run_set("testapp.advanced.api_key", "super-secret-key")
        assert "super-secret-key" not in stdout

    def test_set_overwrites_existing_value(self, config):
        run_set("testapp.general.max_items", 100)
        run_set("testapp.general.max_items", 200)
        assert config.get("testapp.general.max_items") == 200


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class TestCmdSetValidation:

    def test_raises_for_out_of_range_integer(self):
        with pytest.raises(CommandError) as exc:
            run_set("testapp.general.max_items", 9999)
        assert "Validation failed" in str(exc.value)

    def test_raises_for_empty_string_on_not_empty_field(self):
        with pytest.raises(CommandError) as exc:
            run_set("testapp.general.site_name", "")
        assert "Validation failed" in str(exc.value)

    def test_raises_for_invalid_port(self):
        with pytest.raises(CommandError):
            run_set("testapp.advanced.port", 99999)

    def test_db_not_written_on_validation_error(self, config):
        original = config.get("testapp.general.max_items")
        with pytest.raises(CommandError):
            run_set("testapp.general.max_items", 9999)
        assert config.get("testapp.general.max_items") == original

    def test_raises_for_invalid_integer_input_without_writing_null(self):
        from django_sysconfig.models import ConfigValue

        row = ConfigValue.objects.get(
            app_label="testapp",
            path="general.max_items",
        )
        original = row.value

        with pytest.raises(CommandError) as exc:
            run_set("testapp.general.max_items", "3.14")

        row.refresh_from_db()
        assert "Invalid value for testapp.general.max_items" in str(exc.value)
        assert row.value == original

    def test_raises_for_invalid_decimal_input_without_writing_null(self):
        from django_sysconfig.models import ConfigValue

        row = ConfigValue.objects.get(
            app_label="testapp",
            path="general.price",
        )
        original = row.value

        with pytest.raises(CommandError) as exc:
            run_set("testapp.general.price", "not-a-decimal")

        row.refresh_from_db()
        assert "Invalid value for testapp.general.price" in str(exc.value)
        assert row.value == original


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestCmdSetErrors:

    def test_raises_for_invalid_path_format(self):
        with pytest.raises(CommandError):
            run_set("invalid", 10)

    def test_raises_for_unknown_app(self):
        with pytest.raises(CommandError):
            run_set("unknown_app.general.max_items", 10)

    def test_raises_for_unknown_field(self):
        with pytest.raises(CommandError):
            run_set("testapp.general.unknown_field", 10)
