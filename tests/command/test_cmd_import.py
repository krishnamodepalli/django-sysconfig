"""
Tests for: python manage.py config import [--file] [--stdin] [--dry-run]
                                              [--force] [-S]

Covers:
- Imports from file successfully
- Imports from --stdin successfully
- --dry-run passes for valid file, no DB writes
- --dry-run fails for unknown paths
- --dry-run catches validation errors before any write
- --dry-run does not write on validation failure
- --force skips confirmation prompt
- Confirmation prompt proceeds on y
- Confirmation prompt aborts on n
- --skip-on-save-callbacks suppresses callbacks
- Without --skip-on-save-callbacks callbacks fire
- Raises CommandError when both --stdin and --file provided
- Raises CommandError when neither --stdin nor --file provided
- Raises CommandError for non-.json file extension
- Raises CommandError for file not found
- Raises CommandError for invalid JSON
- Raises CommandError for empty config data
- Raises CommandError on validation failure, rolls back all
- Raises CommandError for unknown path in import file
- Raises CommandError for malformed JSON structure
"""

import json
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_IMPORT_DATA = {
    "version": 1,
    "config": {
        "testapp": {
            "general": {
                "site_name": "Imported Site",
                "max_items": 50,
            }
        }
    },
}


def run_import(
    file=None,
    stdin=False,
    dry_run=False,
    force=False,
    skip_callbacks=False,
    user_input="y",
    stdin_data=None,
):
    stdout = StringIO()
    stderr = StringIO()
    kwargs = {
        "stdout": stdout,
        "stderr": stderr,
        "dry_run": dry_run,
        "force": force,
        "skip_on_save_callbacks": skip_callbacks,
        "stdin": stdin,
    }
    if file:
        kwargs["file"] = file

    with patch("builtins.input", return_value=user_input):
        if stdin and stdin_data:
            with patch.object(sys, "stdin", StringIO(json.dumps(stdin_data))):
                call_command("config", "import", **kwargs)
        else:
            call_command("config", "import", **kwargs)

    return stdout.getvalue().strip(), stderr.getvalue().strip()


# ---------------------------------------------------------------------------
# Happy path — file
# ---------------------------------------------------------------------------


class TestCmdImportFile:

    def test_imports_from_file_successfully(self, config, tmp_json_file):
        path = tmp_json_file(VALID_IMPORT_DATA)
        run_import(file=path, force=True)
        assert config.get("testapp.general.site_name") == "Imported Site"
        assert config.get("testapp.general.max_items") == 50

    def test_success_message_written_to_stdout(self, tmp_json_file):
        path = tmp_json_file(VALID_IMPORT_DATA)
        stdout, _ = run_import(file=path, force=True)
        assert "✔" in stdout
        assert "Import complete" in stdout

    def test_imports_multiple_sections(self, config, tmp_json_file):
        data = {
            "version": 1,
            "config": {
                "testapp": {
                    "general": {"site_name": "Multi Section"},
                    "advanced": {"port": 9090, "mode": "debug"},
                }
            },
        }
        path = tmp_json_file(data)
        run_import(file=path, force=True)
        assert config.get("testapp.general.site_name") == "Multi Section"
        assert config.get("testapp.advanced.port") == 9090
        assert config.get("testapp.advanced.mode") == "debug"


# ---------------------------------------------------------------------------
# Happy path — stdin
# ---------------------------------------------------------------------------


class TestCmdImportStdin:

    def test_imports_from_stdin_successfully(self, config):
        run_import(stdin=True, force=True, stdin_data=VALID_IMPORT_DATA)
        assert config.get("testapp.general.site_name") == "Imported Site"
        assert config.get("testapp.general.max_items") == 50

    def test_stdin_success_message_written_to_stdout(self):
        stdout, _ = run_import(stdin=True, force=True, stdin_data=VALID_IMPORT_DATA)
        assert "✔" in stdout


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


class TestCmdImportDryRun:

    def test_dry_run_passes_for_valid_file(self, tmp_json_file):
        path = tmp_json_file(VALID_IMPORT_DATA)
        stdout, _ = run_import(file=path, dry_run=True, force=True)
        assert "Dry run passed" in stdout

    def test_dry_run_does_not_write_to_db(self, config, tmp_json_file):
        original = config.get("testapp.general.site_name")
        path = tmp_json_file(VALID_IMPORT_DATA)
        run_import(file=path, dry_run=True, force=True)
        assert config.get("testapp.general.site_name") == original

    def test_dry_run_fails_for_unknown_path(self, tmp_json_file):
        data = {
            "version": 1,
            "config": {"testapp": {"general": {"nonexistent_field": "value"}}},
        }
        path = tmp_json_file(data)
        with pytest.raises(CommandError) as exc:
            run_import(file=path, dry_run=True, force=True)
        assert "Dry run failed" in str(exc.value)

    def test_dry_run_fails_for_invalid_field(self, tmp_json_file):
        # set_many raises on the first failure so only one error is reported
        data = {
            "version": 1,
            "config": {
                "testapp": {
                    "general": {
                        "bad_field_one": "x",
                        "bad_field_two": "y",
                    }
                }
            },
        }
        path = tmp_json_file(data)
        with pytest.raises(CommandError) as exc:
            run_import(file=path, dry_run=True, force=True)
        assert "Dry run failed" in str(exc.value)

    def test_dry_run_catches_validation_errors(self, tmp_json_file):
        # Exercises the full validator path — not just path existence
        data = {
            "version": 1,
            "config": {
                "testapp": {"general": {"max_items": 99999}}  # fails RangeValidator
            },
        }
        path = tmp_json_file(data)
        with pytest.raises(CommandError) as exc:
            run_import(file=path, dry_run=True, force=True)
        assert "Dry run failed" in str(exc.value)

    def test_dry_run_does_not_write_on_validation_failure(self, config, tmp_json_file):
        original = config.get("testapp.general.max_items")
        data = {
            "version": 1,
            "config": {
                "testapp": {"general": {"max_items": 99999}}  # fails RangeValidator
            },
        }
        path = tmp_json_file(data)
        with pytest.raises(CommandError):
            run_import(file=path, dry_run=True, force=True)
        assert config.get("testapp.general.max_items") == original

    def test_dry_run_skips_confirmation_prompt(self, tmp_json_file):
        path = tmp_json_file(VALID_IMPORT_DATA)
        with patch("builtins.input") as mock_input:
            stdout = StringIO()
            call_command(
                "config",
                "import",
                file=path,
                dry_run=True,
                stdout=stdout,
            )
            mock_input.assert_not_called()


# ---------------------------------------------------------------------------
# Confirmation prompt
# ---------------------------------------------------------------------------


class TestCmdImportConfirmation:

    def test_force_skips_prompt(self, tmp_json_file):
        path = tmp_json_file(VALID_IMPORT_DATA)
        with patch("builtins.input") as mock_input:
            stdout = StringIO()
            call_command(
                "config",
                "import",
                file=path,
                force=True,
                stdout=stdout,
            )
            mock_input.assert_not_called()

    def test_proceeds_on_y(self, config, tmp_json_file):
        path = tmp_json_file(VALID_IMPORT_DATA)
        run_import(file=path, force=False, user_input="y")
        assert config.get("testapp.general.site_name") == "Imported Site"

    def test_aborts_on_n(self, config, tmp_json_file):
        original = config.get("testapp.general.site_name")
        path = tmp_json_file(VALID_IMPORT_DATA)
        with pytest.raises(CommandError):
            run_import(file=path, force=False, user_input="n")
        assert config.get("testapp.general.site_name") == original

    def test_aborts_on_empty_input(self, config, tmp_json_file):
        original = config.get("testapp.general.site_name")
        path = tmp_json_file(VALID_IMPORT_DATA)
        with pytest.raises(CommandError):
            run_import(file=path, force=False, user_input="")
        assert config.get("testapp.general.site_name") == original


# ---------------------------------------------------------------------------
# skip_on_save_callbacks
# ---------------------------------------------------------------------------


class TestCmdImportSkipCallbacks:

    def test_skip_callbacks_suppresses_on_save(
        self, config, registry, tmp_json_file, django_capture_on_commit_callbacks
    ):
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

        path = tmp_json_file(VALID_IMPORT_DATA)
        with django_capture_on_commit_callbacks(execute=True):
            run_import(file=path, force=True, skip_callbacks=True)

        callback.assert_not_called()

    def test_callbacks_fire_without_skip(
        self, registry, tmp_json_file, django_capture_on_commit_callbacks
    ):
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

        path = tmp_json_file(VALID_IMPORT_DATA)
        with django_capture_on_commit_callbacks(execute=True):
            run_import(file=path, force=True, skip_callbacks=False)

        callback.assert_called()


# ---------------------------------------------------------------------------
# Atomicity
# ---------------------------------------------------------------------------


class TestCmdImportAtomicity:

    def test_all_rolled_back_on_validation_failure(self, config, tmp_json_file):
        original_name = config.get("testapp.general.site_name")
        data = {
            "version": 1,
            "config": {
                "testapp": {
                    "general": {
                        "site_name": "Should Not Stick",
                        "max_items": 99999,  # fails RangeValidator
                    }
                }
            },
        }
        path = tmp_json_file(data)
        with pytest.raises(CommandError) as exc:
            run_import(file=path, force=True)
        assert "rolled back" in str(exc.value)
        assert config.get("testapp.general.site_name") == original_name


# ---------------------------------------------------------------------------
# Structure validation
# ---------------------------------------------------------------------------


class TestCmdImportStructureValidation:

    def test_raises_for_non_dict_app_value(self, tmp_json_file):
        path = tmp_json_file({"version": 1, "config": {"testapp": "not a dict"}})
        with pytest.raises(CommandError) as exc:
            run_import(file=path, force=True)
        assert "testapp" in str(exc.value)

    def test_raises_for_non_dict_section_value(self, tmp_json_file):
        path = tmp_json_file(
            {
                "version": 1,
                "config": {"testapp": {"general": ["not", "a", "dict"]}},
            }
        )
        with pytest.raises(CommandError) as exc:
            run_import(file=path, force=True)
        assert "testapp.general" in str(exc.value)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestCmdImportErrors:

    def test_raises_when_both_stdin_and_file_provided(self, tmp_json_file):
        path = tmp_json_file(VALID_IMPORT_DATA)
        with pytest.raises(CommandError) as exc:
            run_import(file=path, stdin=True, force=True)
        assert "mutually exclusive" in str(exc.value)

    def test_raises_when_neither_stdin_nor_file_provided(self):
        with pytest.raises(CommandError) as exc:
            run_import(force=True)
        assert "--file" in str(exc.value) or "--stdin" in str(exc.value)

    def test_raises_for_non_json_extension(self, tmp_path):
        with pytest.raises(CommandError) as exc:
            run_import(file=str(tmp_path / "config.txt"), force=True)
        assert ".json" in str(exc.value)

    def test_raises_for_file_not_found(self):
        with pytest.raises(CommandError) as exc:
            run_import(file="/nonexistent/path/config.json", force=True)
        assert "not found" in str(exc.value).lower()

    def test_raises_for_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("this is not json {{{")
        with pytest.raises(CommandError) as exc:
            run_import(file=str(bad_file), force=True)
        assert "Invalid JSON" in str(exc.value)

    def test_raises_for_empty_config_data(self, tmp_json_file):
        path = tmp_json_file({"version": 1, "config": {}})
        with pytest.raises(CommandError) as exc:
            run_import(file=path, force=True)
        assert "No config data" in str(exc.value)

    def test_raises_for_unknown_path_in_file(self, tmp_json_file):
        data = {
            "version": 1,
            "config": {"testapp": {"general": {"nonexistent_field": "value"}}},
        }
        path = tmp_json_file(data)
        with pytest.raises(CommandError):
            run_import(file=path, force=True)
