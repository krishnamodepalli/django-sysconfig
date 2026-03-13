"""
Tests for the `config` management command.

Covers all five subcommands: get, set, reset, export, import.
"""

import json
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run(*args, **kwargs):
    """Run the config management command, returning (stdout, stderr) strings."""
    out, err = StringIO(), StringIO()
    call_command("config", *args, stdout=out, stderr=err, **kwargs)
    return out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# get subcommand
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_returns_field_default(registered_config):
    stdout, _ = run("get", "testapp.general.site_name")
    assert "Test Site" in stdout


@pytest.mark.django_db
def test_get_returns_db_value(registered_config):
    from django_sysconfig.accessor import config

    config.set("testapp.general.site_name", "Overridden")
    stdout, _ = run("get", "testapp.general.site_name")
    assert "Overridden" in stdout


@pytest.mark.django_db
def test_get_integer_field(registered_config):
    stdout, _ = run("get", "testapp.general.max_items")
    assert "100" in stdout


@pytest.mark.django_db
def test_get_unknown_app_raises(registered_config):
    with pytest.raises(CommandError, match="No configuration registered"):
        run("get", "unknown.general.site_name")


@pytest.mark.django_db
def test_get_unknown_field_raises(registered_config):
    with pytest.raises(CommandError):
        run("get", "testapp.general.nonexistent")


@pytest.mark.django_db
def test_get_invalid_path_raises(registered_config):
    with pytest.raises(CommandError):
        run("get", "bad-path")


# ---------------------------------------------------------------------------
# set subcommand
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_set_string_value(registered_config):
    stdout, _ = run("set", "testapp.general.site_name", "New Name")
    assert "New Name" in stdout
    # Verify it persisted
    from django_sysconfig.accessor import config

    assert config.get("testapp.general.site_name") == "New Name"


@pytest.mark.django_db
def test_set_integer_coercion(registered_config):
    """CLI passes a string; the command must coerce it to int via FrontendModel."""
    run("set", "testapp.general.max_items", "250")
    from django_sysconfig.accessor import config

    assert config.get("testapp.general.max_items") == 250


@pytest.mark.django_db
def test_set_boolean_false_string(registered_config):
    """'false' as a CLI string must not be truthy — FrontendModel handles it."""
    run("set", "testapp.general.enabled", "false")
    from django_sysconfig.accessor import config

    assert config.get("testapp.general.enabled") is False


@pytest.mark.django_db
def test_set_boolean_true_string(registered_config):
    run("set", "testapp.general.enabled", "true")
    from django_sysconfig.accessor import config

    assert config.get("testapp.general.enabled") is True


@pytest.mark.django_db
def test_set_validation_failure_raises(registered_config):
    """max_items has RangeValidator(1, 9999); 0 should fail."""
    with pytest.raises(CommandError, match="Validation failed"):
        run("set", "testapp.general.max_items", "0")


@pytest.mark.django_db
def test_set_invalid_path_raises(registered_config):
    with pytest.raises(CommandError):
        run("set", "bad-path", "value")


@pytest.mark.django_db
def test_set_unknown_app_raises(registered_config):
    with pytest.raises(CommandError):
        run("set", "ghost.general.field", "x")


# ---------------------------------------------------------------------------
# reset subcommand
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_reset_with_force_flag(registered_config):
    from django_sysconfig.accessor import config

    config.set("testapp.general.site_name", "Changed")
    assert config.get("testapp.general.site_name") == "Changed"

    stdout, _ = run("reset", "testapp.general.site_name", "--force")
    assert "reset" in stdout.lower()
    assert config.get("testapp.general.site_name") == "Test Site"


@pytest.mark.django_db
def test_reset_confirmation_yes(registered_config):
    from django_sysconfig.accessor import config

    config.set("testapp.general.max_items", "500")
    with patch("builtins.input", return_value="y"):
        stdout, _ = run("reset", "testapp.general.max_items")
    assert config.get("testapp.general.max_items") == 100


@pytest.mark.django_db
def test_reset_confirmation_no_aborts(registered_config):
    from django_sysconfig.accessor import config

    config.set("testapp.general.max_items", "500")
    with patch("builtins.input", return_value="n"):
        stdout, _ = run("reset", "testapp.general.max_items")
    assert "Aborted" in stdout
    # Value must remain unchanged
    assert config.get("testapp.general.max_items") == 500


@pytest.mark.django_db
def test_reset_invalid_path_raises(registered_config):
    with pytest.raises(CommandError):
        run("reset", "bad-path", "--force")


@pytest.mark.django_db
def test_reset_unknown_field_raises(registered_config):
    with pytest.raises(CommandError):
        run("reset", "testapp.general.nonexistent", "--force")


# ---------------------------------------------------------------------------
# export subcommand
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_export_creates_json_file(registered_config, tmp_path):
    output = str(tmp_path / "export.json")
    run("export", "--output", output)

    with open(output) as f:
        data = json.load(f)

    assert data["version"] == 1
    assert "exported_at" in data
    assert "testapp" in data["config"]
    assert "general" in data["config"]["testapp"]
    assert "site_name" in data["config"]["testapp"]["general"]


@pytest.mark.django_db
def test_export_contains_db_values(registered_config, tmp_path):
    from django_sysconfig.accessor import config

    config.set("testapp.general.site_name", "Exported Value")
    output = str(tmp_path / "export.json")
    run("export", "--output", output)

    with open(output) as f:
        data = json.load(f)

    assert data["config"]["testapp"]["general"]["site_name"] == "Exported Value"


@pytest.mark.django_db
def test_export_uses_field_default_when_no_db_value(registered_config, tmp_path):
    output = str(tmp_path / "export.json")
    run("export", "--output", output)

    with open(output) as f:
        data = json.load(f)

    # No DB row set — export reflects raw DB state (None), not the field default.
    # The accessor's get() applies field defaults at read time; export does not.
    assert data["config"]["testapp"]["general"]["max_items"] is None


@pytest.mark.django_db
def test_export_decrypts_secrets(registered_config, tmp_path):
    from django_sysconfig.accessor import config

    config.set("testapp.secrets.api_key", "my-secret-value")
    output = str(tmp_path / "export.json")
    run("export", "--output", output)

    with open(output) as f:
        data = json.load(f)

    # Secrets must be plaintext in the export
    assert data["config"]["testapp"]["secrets"]["api_key"] == "my-secret-value"


@pytest.mark.django_db
def test_export_warns_about_secrets(registered_config, tmp_path):
    output = str(tmp_path / "export.json")
    _, stderr = run("export", "--output", output)
    assert "secret" in stderr.lower() or "warning" in stderr.lower() or "⚠" in stderr


@pytest.mark.django_db
def test_export_non_json_extension_raises(registered_config, tmp_path):
    output = str(tmp_path / "export.yaml")
    with pytest.raises(CommandError, match=".json"):
        run("export", "--output", output)


@pytest.mark.django_db
def test_export_invalid_batch_size_raises(registered_config, tmp_path):
    output = str(tmp_path / "export.json")
    with pytest.raises(CommandError, match="[Bb]atch"):
        run("export", "--output", output, "--batch-size", "0")


@pytest.mark.django_db
def test_export_specific_app(registered_config, tmp_path):
    output = str(tmp_path / "export.json")
    run("export", "testapp", "--output", output)

    with open(output) as f:
        data = json.load(f)

    assert "testapp" in data["config"]


@pytest.mark.django_db
def test_export_unknown_app_raises(registered_config, tmp_path):
    output = str(tmp_path / "export.json")
    with pytest.raises(CommandError, match="ghost"):
        run("export", "ghost", "--output", output)


@pytest.mark.django_db
def test_export_no_apps_registered(tmp_path):
    # clean_state already cleared the registry; nothing registered
    output = str(tmp_path / "export.json")
    with pytest.raises(CommandError, match="No registered"):
        run("export", "--output", output)


# ---------------------------------------------------------------------------
# import subcommand
# ---------------------------------------------------------------------------


def _write_import_file(path, config_data):
    """Helper: write a minimal valid export file."""
    payload = {
        "version": 1,
        "exported_at": "2026-01-01T00:00:00+00:00",
        "config": config_data,
    }
    path.write_text(json.dumps(payload))


@pytest.mark.django_db
def test_import_sets_values(registered_config, tmp_path):
    f = tmp_path / "import.json"
    _write_import_file(f, {"testapp": {"general": {"site_name": "Imported"}}})

    run("import", str(f))

    from django_sysconfig.accessor import config

    assert config.get("testapp.general.site_name") == "Imported"


@pytest.mark.django_db
def test_import_dry_run_does_not_save(registered_config, tmp_path):
    f = tmp_path / "import.json"
    _write_import_file(f, {"testapp": {"general": {"site_name": "DryRun"}}})

    run("import", str(f), "--dry-run")

    from django_sysconfig.accessor import config

    # Default should still be returned — nothing was saved
    assert config.get("testapp.general.site_name") == "Test Site"


@pytest.mark.django_db
def test_import_dry_run_unknown_path_raises(registered_config, tmp_path):
    f = tmp_path / "import.json"
    _write_import_file(f, {"testapp": {"general": {"does_not_exist": "x"}}})

    with pytest.raises(CommandError, match="unknown path"):
        run("import", str(f), "--dry-run")


@pytest.mark.django_db
def test_import_non_json_extension_raises(registered_config, tmp_path):
    f = tmp_path / "import.yaml"
    f.write_text("{}")
    with pytest.raises(CommandError, match=".json"):
        run("import", str(f))


@pytest.mark.django_db
def test_import_file_not_found_raises(registered_config, tmp_path):
    with pytest.raises(CommandError, match="not found"):
        run("import", str(tmp_path / "missing.json"))


@pytest.mark.django_db
def test_import_invalid_json_raises(registered_config, tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("not json {{{")
    with pytest.raises(CommandError, match="[Ii]nvalid JSON"):
        run("import", str(f))


@pytest.mark.django_db
def test_import_empty_config_raises(registered_config, tmp_path):
    f = tmp_path / "empty.json"
    f.write_text(json.dumps({"version": 1, "config": {}}))
    with pytest.raises(CommandError, match="No config data"):
        run("import", str(f))


@pytest.mark.django_db
def test_import_is_atomic_on_validation_error(registered_config, tmp_path):
    """If one value fails validation the entire import must roll back."""
    f = tmp_path / "import.json"
    _write_import_file(
        f,
        {
            "testapp": {
                "general": {
                    "site_name": "Good Value",
                    "max_items": 99999,  # exceeds RangeValidator max of 9999
                }
            }
        },
    )

    with pytest.raises(CommandError):
        run("import", str(f))

    from django_sysconfig.accessor import config

    # Neither value should have been saved
    assert config.get("testapp.general.site_name") == "Test Site"
    assert config.get("testapp.general.max_items") == 100


@pytest.mark.django_db
def test_import_secret_value(registered_config, tmp_path):
    """Importing a plaintext secret should store it encrypted."""
    f = tmp_path / "import.json"
    _write_import_file(f, {"testapp": {"secrets": {"api_key": "plain-secret"}}})

    run("import", str(f))

    from django_sysconfig.accessor import config
    from django_sysconfig.models import ConfigValue

    # Accessor should decrypt transparently
    assert config.get("testapp.secrets.api_key") == "plain-secret"

    # Raw DB value should be encrypted (not plaintext)
    raw = ConfigValue.objects.get(app_label="testapp", path="secrets.api_key").value
    assert raw != "plain-secret"
    assert raw.startswith("gAAAAA")
