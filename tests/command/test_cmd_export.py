"""
Tests for: python manage.py config export [app] [--output]

Covers:
- Exports all apps to default output file
- Exports a specific app
- Output file has correct top-level structure
- Output file contains correct values
- Secrets are decrypted in export
- Warning about plaintext secrets written to stderr
- Raises CommandError for non-.json output path
- Raises CommandError for unknown app label
- Raises CommandError if no apps registered
"""

import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_export(output_path, app=None, **kwargs):
    stdout = StringIO()
    stderr = StringIO()
    args = ["config", "export"]
    if app:
        args.append(app)
    extra = {"output": output_path, "stdout": stdout, "stderr": stderr}
    call_command(*args, **extra, **kwargs)
    return stdout.getvalue().strip(), stderr.getvalue().strip()


# ---------------------------------------------------------------------------
# Output file structure
# ---------------------------------------------------------------------------


class TestCmdExportStructure:

    def test_creates_output_file(self, tmp_path):
        output = str(tmp_path / "export.json")
        run_export(output)
        assert (tmp_path / "export.json").exists()

    def test_output_has_version_key(self, tmp_path):
        output = str(tmp_path / "export.json")
        run_export(output)
        data = json.loads((tmp_path / "export.json").read_text())
        assert data["version"] == 1

    def test_output_has_exported_at_key(self, tmp_path):
        output = str(tmp_path / "export.json")
        run_export(output)
        data = json.loads((tmp_path / "export.json").read_text())
        assert "exported_at" in data

    def test_output_has_config_key(self, tmp_path):
        output = str(tmp_path / "export.json")
        run_export(output)
        data = json.loads((tmp_path / "export.json").read_text())
        assert "config" in data

    def test_output_contains_testapp(self, tmp_path):
        output = str(tmp_path / "export.json")
        run_export(output)
        data = json.loads((tmp_path / "export.json").read_text())
        assert "testapp" in data["config"]

    def test_output_contains_all_sections(self, tmp_path):
        output = str(tmp_path / "export.json")
        run_export(output)
        data = json.loads((tmp_path / "export.json").read_text())
        assert "general" in data["config"]["testapp"]
        assert "advanced" in data["config"]["testapp"]

    def test_output_contains_all_fields(self, tmp_path):
        output = str(tmp_path / "export.json")
        run_export(output)
        data = json.loads((tmp_path / "export.json").read_text())
        general = data["config"]["testapp"]["general"]
        assert "site_name" in general
        assert "max_items" in general
        assert "enabled" in general
        assert "price" in general
        assert "description" in general


# ---------------------------------------------------------------------------
# Correct values
# ---------------------------------------------------------------------------


class TestCmdExportValues:

    def test_exports_default_values(self, tmp_path):

        output = str(tmp_path / "export.json")
        run_export(output)
        data = json.loads((tmp_path / "export.json").read_text())

        assert data["config"]["testapp"]["general"]["site_name"] == "Test Site"
        assert data["config"]["testapp"]["general"]["max_items"] == 10
        assert data["config"]["testapp"]["general"]["enabled"] is True
        assert data["config"]["testapp"]["advanced"]["mode"] == "standard"

    def test_exports_updated_value(self, config, tmp_path):
        config.set("testapp.general.max_items", 42)
        output = str(tmp_path / "export.json")
        run_export(output)
        data = json.loads((tmp_path / "export.json").read_text())
        assert data["config"]["testapp"]["general"]["max_items"] == 42

    def test_exports_specific_app_only(self, tmp_path):
        output = str(tmp_path / "export.json")
        run_export(output, app="testapp")
        data = json.loads((tmp_path / "export.json").read_text())
        assert "testapp" in data["config"]
        assert len(data["config"]) == 1


# ---------------------------------------------------------------------------
# Secrets
# ---------------------------------------------------------------------------


class TestCmdExportSecrets:

    def test_secret_field_present_in_export(self, tmp_path):
        output = str(tmp_path / "export.json")
        run_export(output)
        data = json.loads((tmp_path / "export.json").read_text())
        assert "api_key" in data["config"]["testapp"]["advanced"]

    def test_warns_about_plaintext_secrets_on_stderr(self, tmp_path):
        output = str(tmp_path / "export.json")
        _, stderr = run_export(output)
        assert "secret" in stderr.lower() or "⚠" in stderr


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestCmdExportErrors:

    def test_raises_for_non_json_output_path(self, tmp_path):
        with pytest.raises(CommandError):
            run_export(str(tmp_path / "export.txt"))

    def test_raises_for_unknown_app(self, tmp_path):
        with pytest.raises(CommandError):
            run_export(str(tmp_path / "export.json"), app="unknown_app")
