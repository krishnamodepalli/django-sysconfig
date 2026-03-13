import json
import os
from datetime import UTC, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from django_sysconfig.accessor import config
from django_sysconfig.encryption import safe_decrypt
from django_sysconfig.exceptions import ConfigError, ConfigValidationError
from django_sysconfig.frontend_models import SecretFrontendModel
from django_sysconfig.models import ConfigValue
from django_sysconfig.registry import config_registry


class _JSONEncoder(json.JSONEncoder):
    """Extends the default encoder to handle Decimal values."""

    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)


class Command(BaseCommand):
    # Constants
    MAX_EXPORT_BATCH_SIZE: int = 100

    help: str = "Interact with django-sysconfig configuration values"

    def add_arguments(self, parser: CommandParser):
        subparsers = parser.add_subparsers(dest="subcommand", metavar="subcommand")
        subparsers.required = True

        get_parser = subparsers.add_parser("get", help="Get a configuration value")
        get_parser.add_argument("path", help="Config path in app.section.field format")

        set_parser = subparsers.add_parser("set", help="Set a configuration value")
        set_parser.add_argument("path", help="Config path in app.section.field format")
        set_parser.add_argument("value", help="Value to set")

        reset_parser = subparsers.add_parser(
            "reset", help="Reset a configuration value to its field default"
        )
        reset_parser.add_argument(
            "path", help="Config path in app.section.field format"
        )
        reset_parser.add_argument(
            "-f", "--force", action="store_true", help="Skip the confirmation prompt"
        )

        export_parser = subparsers.add_parser(
            "export", help="Export configuration values to a JSON file"
        )
        export_parser.add_argument(
            "app", nargs="?", help="App label to export (exports all apps if omitted)"
        )
        export_parser.add_argument(
            "--output",
            "-o",
            default="config_export.json",
            help="Output file path (default: config_export.json)",
        )
        export_parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Number of config values to fetch per DB query (default: 50)",
        )

        import_parser = subparsers.add_parser(
            "import", help="Import configuration values from a JSON file"
        )
        import_parser.add_argument("file", help="Input file path (.json)")
        import_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate the file without saving any values",
        )

    def handle(self, *args, **options):
        handlers = {
            "get": self.handle_get,
            "set": self.handle_set,
            "reset": self.handle_reset,
            "export": self.handle_export,
            "import": self.handle_import,
        }
        handlers[options["subcommand"]](*args, **options)

    def handle_get(self, *args, **options):
        path = options["path"]
        try:
            value = config.get(path)
            self.stdout.write(str(value))
        except ConfigError as e:
            raise CommandError(str(e)) from e

    def handle_set(self, *args, **options):
        path = options["path"]
        raw_value = options["value"]
        try:
            app_label, section, field_name = config._parse_path(path)
            field = config._get_field(app_label, section, field_name)
            parsed_value = field.get_frontend_model_instance().get_value(raw_value)
            config.set(path, parsed_value)
            self.stdout.write(self.style.SUCCESS(f"✔ {path} set to {parsed_value!r}"))
        except ConfigValidationError as e:
            errors = "\n".join(f"  • {err}" for err in e.errors)
            raise CommandError(f"Validation failed for {path}:\n{errors}") from e
        except ConfigError as e:
            raise CommandError(str(e)) from e

    def handle_reset(self, *args, **options):
        path = options["path"]

        if not options["force"]:
            confirm = input(
                f"This will reset '{path}' to its field default. "
                "This cannot be undone. Continue? [y/N] "
            )
            if confirm.strip().lower() != "y":
                self.stdout.write("Aborted.")
                return

        try:
            config.reset(path)
            self.stdout.write(self.style.SUCCESS(f"✔ {path} reset to default"))
        except ConfigError as e:
            raise CommandError(str(e)) from e

    def handle_export(self, *args, **options):
        output_path = os.path.abspath(options["output"])
        target_app = options.get("app")
        batch_size = options["batch_size"]

        if not output_path.endswith(".json"):
            raise CommandError("Output file must have a .json extension")

        if not 1 <= batch_size <= self.MAX_EXPORT_BATCH_SIZE:
            raise CommandError("Batch size must be between 1 and 100")

        apps = [target_app] if target_app else config_registry.get_registered_apps()
        if not apps:
            raise CommandError("No registered app configurations found")

        # Enumerate all fields from the registry — metadata only, no DB access
        all_fields = []
        for app_label in apps:
            config_def = config_registry.get_config(app_label)
            if not config_def:
                raise CommandError(f"No config registered for app '{app_label}'")
            for section_name, section_class in config_def.get_sections():
                section_key = section_name.lower()
                for field_name, field in section_class.get_fields().items():
                    all_fields.append((app_label, section_key, field_name, field))

        total = len(all_fields)
        self.stdout.write(
            f"Exporting {total} config value(s) across {len(apps)} app(s). "
            "This may take a moment for large configs."
        )
        self.stdout.write(f"Output will be written to: {output_path}\n")

        result = {
            "version": 1,
            "exported_at": datetime.now(UTC).isoformat(),
            "config": {},
        }

        processed = 0
        for i in range(0, total, batch_size):
            batch = all_fields[i : i + batch_size]

            # Group by app_label for one targeted DB query per app in this batch
            batch_by_app: dict[str, list] = {}
            for app_label, section_key, field_name, field in batch:
                batch_by_app.setdefault(app_label, []).append(
                    (section_key, field_name, field)
                )

            # Fetch raw DB values — one query per app_label
            db_values: dict[tuple, str | None] = {}
            for app_label, fields in batch_by_app.items():
                db_paths = [f"{sk}.{fn}" for sk, fn, _ in fields]
                for row in ConfigValue.objects.filter(
                    app_label=app_label, path__in=db_paths
                ):
                    db_values[(app_label, row.path)] = row.value

            # Deserialize and accumulate
            for app_label, section_key, field_name, field in batch:
                db_path = f"{section_key}.{field_name}"
                raw = db_values.get((app_label, db_path))

                if field.frontend_model is SecretFrontendModel:
                    value = safe_decrypt(raw) if raw else None
                else:
                    value = field.get_frontend_model_instance().get_value(raw)

                result["config"].setdefault(app_label, {}).setdefault(section_key, {})[
                    field_name
                ] = value

                processed += 1

            self.stdout.write(f"  {processed}/{total} apps processed...")

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, cls=_JSONEncoder)

        self.stdout.write(self.style.SUCCESS(f"\n✔ Export complete → {output_path}"))
        self.stderr.write(
            self.style.WARNING(
                "⚠ This file contains plaintext secrets. Handle it with care."
            )
        )

    def handle_import(self, *args, **options):
        file_path = os.path.abspath(options["file"])
        dry_run = options["dry_run"]

        if not file_path.endswith(".json"):
            raise CommandError("Input file must have a .json extension")

        try:
            with open(file_path) as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}") from None
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON: {e}") from e

        config_data = data.get("config", {})
        if not config_data:
            raise CommandError("No config data found in file")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no values will be saved\n"))

        paths = [
            (f"{app}.{section}.{field}", value)
            for app, sections in config_data.items()
            for section, fields in sections.items()
            for field, value in fields.items()
        ]

        if dry_run:
            errors = [
                f"{path}: unknown path" for path, _ in paths if not config.exists(path)
            ]
            if errors:
                raise CommandError(
                    "Validation failed:\n" + "\n".join(f"  • {err}" for err in errors)
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f"✔ Dry run passed — {len(paths)} value(s) look valid"
                )
            )
            return

        errors = []
        paths_written = []
        try:
            with transaction.atomic():
                for path, value in paths:
                    try:
                        config.set(path, value)
                        paths_written.append(path)
                    except ConfigValidationError as e:
                        errors.append(f"{path}: " + ", ".join(e.errors))
                    except ConfigError as e:
                        errors.append(f"{path}: {e}")

                if errors:
                    raise CommandError(
                        "Import aborted — all changes rolled back:\n"
                        + "\n".join(f"  • {err}" for err in errors)
                    )
        except CommandError:
            # DB transaction was rolled back; purge cache keys that were set
            # so the cache doesn't serve stale values.
            from django_sysconfig.cache import config_cache

            for p in paths_written:
                config_cache.invalidate(p)
            raise

        self.stdout.write(
            self.style.SUCCESS(f"✔ Import complete — {len(paths)} value(s) set")
        )
