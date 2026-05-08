"""
Tests for: python manage.py config get <path>

Covers:
- Returns correct value for a valid path
- Output written to stdout
- CommandError for invalid path format
- CommandError for unknown app
- CommandError for unknown field
"""

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_get(path, **kwargs):
    stdout = StringIO()
    stderr = StringIO()
    call_command("config", "get", path, stdout=stdout, stderr=stderr, **kwargs)
    return stdout.getvalue().strip(), stderr.getvalue().strip()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestCmdGet:
    def test_returns_string_default(self):
        stdout, _ = run_get("testapp.general.site_name")
        assert stdout == "Test Site"

    def test_returns_integer_default(self):
        stdout, _ = run_get("testapp.general.max_items")
        assert stdout == "10"

    def test_returns_boolean_default(self):
        stdout, _ = run_get("testapp.general.enabled")
        assert stdout == "True"

    def test_returns_select_default(self):
        stdout, _ = run_get("testapp.advanced.mode")
        assert stdout == "standard"

    def test_returns_updated_value_after_set(self, config):
        config.set("testapp.general.max_items", 42)
        stdout, _ = run_get("testapp.general.max_items")
        assert stdout == "42"

    def test_output_written_to_stdout(self):
        stdout, stderr = run_get("testapp.general.site_name")
        assert stdout != ""
        assert stderr == ""


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestCmdGetErrors:
    def test_raises_for_invalid_path_format(self):
        with pytest.raises(CommandError):
            run_get("invalid")

    def test_raises_for_two_part_path(self):
        with pytest.raises(CommandError):
            run_get("testapp.general")

    def test_raises_for_unknown_app(self):
        with pytest.raises(CommandError):
            run_get("unknown_app.general.site_name")

    def test_raises_for_unknown_field(self):
        with pytest.raises(CommandError):
            run_get("testapp.general.unknown_field")

    def test_raises_for_unknown_section(self):
        with pytest.raises(CommandError):
            run_get("testapp.unknown_section.site_name")
