import json
import os
from datetime import datetime, timezone

from django.core.management.base import CommandError

from django_sysconfig.accessor import config
from django_sysconfig.registry import config_registry

from .common import JSONEncoder

UTC = timezone.utc


def handle_export(command, **options):
    """Serialise all registered config values to a JSON file."""
    # 1. Validate
    output_path = os.path.abspath(options["output"])
    target_app = options.get("app")

    if not output_path.endswith(".json"):
        raise CommandError("Output file must have a .json extension")

    # 2. Enumerate apps
    apps = [target_app] if target_app else config_registry.get_registered_apps()
    if not apps:
        raise CommandError("No registered app configurations found")

    for app_label in apps:
        if not config_registry.get_config(app_label):
            raise CommandError(f"No config registered for app '{app_label}'")

    command.stdout.write(
        f"Exporting config for {len(apps)} app(s). "
        "This may take a moment for large configs."
    )
    command.stdout.write(f"Output will be written to: {output_path}\n")

    # 3. Fetch & serialise via accessor
    result = {
        "version": 1,
        "exported_at": datetime.now(UTC).isoformat(),
        "config": {},
    }

    for app_label in apps:
        result["config"][app_label] = config.all(app_label)
        command.stdout.write(f"  {app_label} exported...")

    # 4. Write — restricted to owner read/write only (secrets may be present)
    if os.path.exists(output_path):
        os.chmod(output_path, 0o600)
    fd = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(result, f, indent=2, cls=JSONEncoder)

    command.stdout.write(command.style.SUCCESS(f"\n✔ Export complete → {output_path}"))
    command.stderr.write(
        command.style.WARNING(
            "⚠ This file contains plaintext secrets. Handle it with care."
        )
    )
