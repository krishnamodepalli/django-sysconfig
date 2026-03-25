"""
Tests for: python manage.py config reset <path>

Covers:
- Resets value to field default with --force
- Prompts confirmation without --force, proceeds on y
- Prompts confirmation without --force, aborts on n
- Success message written to stdout
- CommandError for unknown path
- CommandError for invalid path format
"""

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_reset(path, force=False, user_input="y", **kwargs):
    stdout = StringIO()
    stderr = StringIO()
    with patch("builtins.input", return_value=user_input):
        call_command(
            "config",
            "reset",
            path,
            force=force,
            stdout=stdout,
            stderr=stderr,
            **kwargs,
        )
    return stdout.getvalue().strip(), stderr.getvalue().strip()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestCmdReset:

    def test_resets_to_default_with_force(
        self, config, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.max_items", 999)
        assert config.get("testapp.general.max_items") == 999

        with django_capture_on_commit_callbacks(execute=True):
            run_reset("testapp.general.max_items", force=True)
        assert config.get("testapp.general.max_items") == 10

    def test_resets_string_to_default(self, config):
        config.set("testapp.general.site_name", "Changed")
        run_reset("testapp.general.site_name", force=True)
        assert config.get("testapp.general.site_name") == "Test Site"

    def test_resets_boolean_to_default(self, config):
        config.set("testapp.general.enabled", False)
        run_reset("testapp.general.enabled", force=True)
        assert config.get("testapp.general.enabled") is True

    def test_success_message_written_to_stdout(self):
        stdout, _ = run_reset("testapp.general.max_items", force=True)
        assert "✔" in stdout
        assert "testapp.general.max_items" in stdout


# ---------------------------------------------------------------------------
# Confirmation prompt
# ---------------------------------------------------------------------------


class TestCmdResetConfirmation:

    def test_proceeds_on_y(self, config):
        config.set("testapp.general.max_items", 999)
        run_reset("testapp.general.max_items", force=False, user_input="y")
        assert config.get("testapp.general.max_items") == 10

    def test_aborts_on_n(self, config):
        config.set("testapp.general.max_items", 999)
        with pytest.raises(CommandError):
            run_reset("testapp.general.max_items", force=False, user_input="n")
        assert config.get("testapp.general.max_items") == 999

    def test_aborts_on_empty_input(self, config):
        config.set("testapp.general.max_items", 999)
        with pytest.raises(CommandError):
            run_reset("testapp.general.max_items", force=False, user_input="")
        assert config.get("testapp.general.max_items") == 999

    def test_force_skips_prompt(self):
        # input() should never be called when --force is passed
        with patch("builtins.input") as mock_input:
            stdout = StringIO()
            call_command(
                "config",
                "reset",
                "testapp.general.max_items",
                force=True,
                stdout=stdout,
            )
            mock_input.assert_not_called()


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestCmdResetErrors:

    def test_raises_for_invalid_path_format(self):
        with pytest.raises(CommandError):
            run_reset("invalid", force=True)

    def test_raises_for_unknown_app(self):
        with pytest.raises(CommandError):
            run_reset("unknown_app.general.max_items", force=True)

    def test_raises_for_unknown_field(self):
        with pytest.raises(CommandError):
            run_reset("testapp.general.unknown_field", force=True)
