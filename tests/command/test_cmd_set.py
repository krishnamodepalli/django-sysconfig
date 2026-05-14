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


class TestCmdSetDryRun:

    def test_dry_run_doesnt_save(self, config):
        original = config.get("testapp.general.max_items")
        run_set("testapp.general.max_items", original + 1, dry_run=True)
        assert config.get("testapp.general.max_items") == original

    def test_dry_run_raises_invalid_path(self):
        with pytest.raises(CommandError):
            run_set("invalid.path", 200, dry_run=True)

    def test_dry_run_raises_on_validation_fail(self):
        with pytest.raises(CommandError):
            run_set("testapp.general.site_name", "", dry_run=True)
        with pytest.raises(CommandError):
            run_set("testapp.general.max_items", 1002, dry_run=True)


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
