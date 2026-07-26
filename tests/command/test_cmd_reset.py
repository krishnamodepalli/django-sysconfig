"""
Tests for: python manage.py config reset <path>

Covers:
- Resets value to field default
- Prompts for confirmation, proceeds on y
- Prompts for confirmation, aborts on n / empty input
- --no-input skips the confirmation prompt
- --force still skips the prompt but emits a DeprecationWarning
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


def run_reset(path, user_input="y", **kwargs):
    stdout = StringIO()
    stderr = StringIO()
    with patch("builtins.input", return_value=user_input):
        call_command(
            "config",
            "reset",
            path,
            stdout=stdout,
            stderr=stderr,
            **kwargs,
        )
    return stdout.getvalue().strip(), stderr.getvalue().strip()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestCmdReset:

    def test_resets_to_default(self, config, django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True):
            config.set("testapp.general.max_items", 999)
        assert config.get("testapp.general.max_items") == 999

        with django_capture_on_commit_callbacks(execute=True):
            run_reset("testapp.general.max_items")
        assert config.get("testapp.general.max_items") == 10

    def test_resets_string_to_default(self, config):
        config.set("testapp.general.site_name", "Changed")
        run_reset("testapp.general.site_name")
        assert config.get("testapp.general.site_name") == "Test Site"

    def test_resets_boolean_to_default(self, config):
        config.set("testapp.general.enabled", False)
        run_reset("testapp.general.enabled")
        assert config.get("testapp.general.enabled") is True

    def test_success_message_written_to_stdout(self, config):
        stdout, _ = run_reset("testapp.general.max_items")
        assert "✔" in stdout
        assert "testapp.general.max_items" in stdout


# ---------------------------------------------------------------------------
# Confirmation prompt
# ---------------------------------------------------------------------------


class TestCmdResetConfirmation:

    def test_proceeds_on_y(self, config):
        config.set("testapp.general.max_items", 999)
        run_reset("testapp.general.max_items", user_input="y")
        assert config.get("testapp.general.max_items") == 10

    def test_aborts_on_n(self, config):
        config.set("testapp.general.max_items", 999)
        with pytest.raises(CommandError):
            run_reset("testapp.general.max_items", user_input="n")
        assert config.get("testapp.general.max_items") == 999

    def test_aborts_on_empty_input(self, config):
        config.set("testapp.general.max_items", 999)
        with pytest.raises(CommandError):
            run_reset("testapp.general.max_items", user_input="")
        assert config.get("testapp.general.max_items") == 999

    def test_no_input_skips_prompt(self, config):
        config.set("testapp.general.max_items", 999)
        with patch("builtins.input") as mock_input:
            stdout = StringIO()
            call_command(
                "config",
                "reset",
                "testapp.general.max_items",
                no_input=True,
                stdout=stdout,
            )
            mock_input.assert_not_called()
        assert config.get("testapp.general.max_items") == 10


# ---------------------------------------------------------------------------
# Deprecated --force flag (still works, warns)
# ---------------------------------------------------------------------------


class TestCmdResetForceDeprecation:

    def test_force_still_skips_prompt(self, config):
        config.set("testapp.general.max_items", 999)
        with patch("builtins.input") as mock_input:
            stdout = StringIO()
            stderr = StringIO()
            call_command(
                "config",
                "reset",
                "testapp.general.max_items",
                force=True,
                stdout=stdout,
                stderr=stderr,
            )
            mock_input.assert_not_called()
        assert config.get("testapp.general.max_items") == 10

    def test_force_emits_deprecation_warning(self, config):
        with pytest.warns(DeprecationWarning, match="--no-input"):
            _, stderr = run_reset("testapp.general.max_items", force=True)
        assert "deprecated" in stderr.lower()


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestCmdResetErrors:

    def test_raises_for_invalid_path_format(self):
        with pytest.raises(CommandError):
            run_reset("invalid", no_input=True)

    def test_raises_for_unknown_app(self):
        with pytest.raises(CommandError):
            run_reset("unknown_app.general.max_items", no_input=True)

    def test_raises_for_unknown_field(self):
        with pytest.raises(CommandError):
            run_reset("testapp.general.unknown_field", no_input=True)
