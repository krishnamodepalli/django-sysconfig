"""Numeric parsing must not relabel failures that occur after a committed save."""

from io import StringIO

import pytest
from django.core.management import call_command

from django_sysconfig.models import ConfigValue


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("command", ["set", "import"])
def test_save_callback_error_is_not_reported_as_input_failure(
    config, tmp_json_file, command
):
    """A real on-commit callback failure keeps its error and its committed value."""
    field = config._resolve_field_ref("testapp.general.max_items")

    def fail_after_save(path, value, old_value):
        raise ValueError("callback failed after commit")

    field.on_save = fail_after_save
    if command == "set":
        args = ["config", "set", "testapp.general.max_items", "42"]
        options = {}
    else:
        args = ["config", "import"]
        options = {
            "file": tmp_json_file(
                {"version": 1, "config": {"testapp": {"general": {"max_items": 42}}}}
            ),
            "no_input": True,
        }

    with pytest.raises(ValueError, match="callback failed after commit"):
        call_command(*args, **options, stdout=StringIO(), stderr=StringIO())

    assert (
        ConfigValue.objects.get(app_label="testapp", path="general.max_items").value
        == "42"
    )
