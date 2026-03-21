import json
import os
import sys
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _JSONEncoder(json.JSONEncoder):
    """Extends the default encoder to handle Decimal values."""

    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


class Command(BaseCommand):

    # Constants
    MAX_EXPORT_BATCH_SIZE: int = 100

    help: str = "Interact with django-sysconfig configuration values"

    # -----------------------------------------------------------------------
    # Argument definitions
    # -----------------------------------------------------------------------

    def add_arguments(self, parser: CommandParser):
        subparsers = parser.add_subparsers(dest="subcommand", metavar="subcommand")
        subparsers.required = True

        # --- get ---
        get_parser = subparsers.add_parser("get", help="Get a configuration value")
        get_parser.add_argument("path", help="Config path in app.section.field format")

        # --- set ---
        set_parser = subparsers.add_parser("set", help="Set a configuration value")
        set_parser.add_argument("path", help="Config path in app.section.field format")
        set_parser.add_argument("value", help="Value to set")

        # --- reset ---
        reset_parser = subparsers.add_parser(
            "reset", help="Reset a configuration value to its field default"
        )
        reset_parser.add_argument(
            "path", help="Config path in app.section.field format"
        )
        reset_parser.add_argument(
            "-f", "--force", action="store_true", help="Skip the confirmation prompt"
        )

        # --- export ---
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

        # --- import ---
        import_parser = subparsers.add_parser(
            "import", help="Import configuration values from a JSON file"
        )
        import_parser.add_argument(
            "--file",
            "-i",
            help="Input file path (.json)",
        )
        import_parser.add_argument(
            "--stdin",
            action="store_true",
            help="Read JSON from stdin instead of a file",
        )
        import_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate the file without saving any values",
        )
        import_parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Skip the confirmation prompt",
        )

    # -----------------------------------------------------------------------
    # Dispatch
    # -----------------------------------------------------------------------

    def handle(self, *args, **options):
        handlers = {
            "get": self.handle_get,
            "set": self.handle_set,
            "reset": self.handle_reset,
            "export": self.handle_export,
            "import": self.handle_import,
        }
        handlers[options["subcommand"]](*args, **options)

    # -----------------------------------------------------------------------
    # Subcommand handlers
    # -----------------------------------------------------------------------

    def handle_get(self, *args, **options):
        """Print the current value of a single config path."""
        path = options["path"]

        try:
            value = config.get(path)
            self.stdout.write(str(value))
        except ConfigError as e:
            raise CommandError(str(e)) from e

    def handle_set(self, *args, **options):
        """Parse and persist a single config value."""
        path = options["path"]
        raw = options["value"]

        try:
            app_label, section, field_name = config._parse_path(path)
            field = config._get_field(app_label, section, field_name)
            parsed = field.get_frontend_model_instance().get_value(raw)

            config.set(path, parsed)
            self.stdout.write(self.style.SUCCESS(f"✔ {path} set to {parsed!r}"))

        except ConfigValidationError as e:
            errors = "\n".join(f"  • {err}" for err in e.errors)
            raise CommandError(f"Validation failed for {path}:\n{errors}") from e

        except ConfigError as e:
            raise CommandError(str(e)) from e

    def handle_reset(self, *args, **options):
        """Reset a config path to its field default, with optional confirmation."""
        path = options["path"]

        if not options["force"]:
            self._confirm(
                f"This will reset '{path}' to its field default. "
                "This cannot be undone."
            )

        try:
            config.reset(path)
            self.stdout.write(self.style.SUCCESS(f"✔ {path} reset to default"))
        except ConfigError as e:
            raise CommandError(str(e)) from e

    def handle_export(self, *args, **options):
        """Serialise all registered config values to a JSON file."""
        # 1. Validate
        output_path = os.path.abspath(options["output"])
        target_app = options.get("app")
        batch_size = options["batch_size"]

        if not output_path.endswith(".json"):
            raise CommandError("Output file must have a .json extension")

        if not 1 <= batch_size <= self.MAX_EXPORT_BATCH_SIZE:
            raise CommandError("Batch size must be between 1 and 100")

        # 2. Enumerate fields from the registry (metadata only, no DB access yet)
        apps = [target_app] if target_app else config_registry.get_registered_apps()
        if not apps:
            raise CommandError("No registered app configurations found")

        all_fields = self._collect_all_fields(apps)
        total = len(all_fields)

        self.stdout.write(
            f"Exporting {total} config value(s) across {len(apps)} app(s). "
            "This may take a moment for large configs."
        )
        self.stdout.write(f"Output will be written to: {output_path}\n")

        # 3. Fetch & serialise in batches
        result = {
            "version": 1,
            "exported_at": datetime.now(UTC).isoformat(),
            "config": {},
        }

        processed = 0

        for i in range(0, total, batch_size):
            batch = all_fields[i : i + batch_size]

            # Group fields by app so we can do one DB query per app per batch
            apps_in_batch: dict[str, list] = {}
            for app_label, section_key, field_name, field in batch:
                apps_in_batch.setdefault(app_label, []).append(
                    (section_key, field_name, field)
                )

            # One targeted SELECT per app_label in this batch
            stored_values: dict[tuple, str | None] = {}
            for app_label, fields in apps_in_batch.items():
                db_paths = [f"{sk}.{fn}" for sk, fn, _ in fields]
                for row in ConfigValue.objects.filter(
                    app_label=app_label, path__in=db_paths
                ):
                    stored_values[(app_label, row.path)] = row.value

            for app_label, section_key, field_name, field in batch:
                db_path = f"{section_key}.{field_name}"
                raw = stored_values.get((app_label, db_path))

                if field.frontend_model is SecretFrontendModel:
                    value = safe_decrypt(raw) if raw else None
                else:
                    value = field.get_frontend_model_instance().get_value(raw)

                result["config"].setdefault(app_label, {}).setdefault(section_key, {})[
                    field_name
                ] = value

                processed += 1

            self.stdout.write(f"  {processed}/{total} values processed...")

        # 4. Write
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, cls=_JSONEncoder)

        self.stdout.write(self.style.SUCCESS(f"\n✔ Export complete → {output_path}"))
        self.stderr.write(
            self.style.WARNING(
                "⚠ This file contains plaintext secrets. Handle it with care."
            )
        )

    def handle_import(self, *args, **options):
        """Load a JSON export and persist all contained config values."""
        dry_run = options["dry_run"]
        use_stdin = options["stdin"]
        force = options["force"]
        file_path = options.get("file")

        # 1. Validate args
        if use_stdin and file_path:
            raise CommandError("--stdin and --file are mutually exclusive")
        if not use_stdin and not file_path:
            raise CommandError("Provide a file path via --file/-i or use --stdin")
        if file_path and not file_path.endswith(".json"):
            raise CommandError("Input file must have a .json extension")

        # 2. Load
        data = self._load_json(file_path, use_stdin)

        config_data = data.get("config", {})
        if not config_data:
            raise CommandError("No config data found in file")

        paths = [
            (f"{app}.{section}.{field}", value)
            for app, sections in config_data.items()
            for section, fields in sections.items()
            for field, value in fields.items()
        ]

        # 3. Confirm (skipped for dry-run and --force)
        if not dry_run and not force:
            source = "stdin" if use_stdin else file_path
            self._confirm(
                f"This will override current configuration values from '{source}'. "
                "This cannot be undone."
            )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no values will be saved\n"))

            unknown = [path for path, _ in paths if not config.exists(path)]
            if unknown:
                raise CommandError(
                    "Validation failed:\n"
                    + "\n".join(f"  • {p}: unknown path" for p in unknown)
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✔ Dry run passed — {len(paths)} value(s) look valid"
                )
            )
            return

        # 4. Execute
        errors = []
        committed_paths = []

        try:
            with transaction.atomic():
                for path, value in paths:
                    try:
                        config.set(path, value)
                        committed_paths.append(path)
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
            # Purge any cache keys written before the rollback so the cache
            # doesn't serve stale values.
            from django_sysconfig.cache import config_cache

            for path in committed_paths:
                config_cache.invalidate(path)

            raise

        self.stdout.write(
            self.style.SUCCESS(f"✔ Import complete — {len(paths)} value(s) set")
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _confirm(self, message: str) -> None:
        """Prompt the user for y/N confirmation; abort with CommandError on refusal."""
        answer = input(f"{message} Continue? [y/N] ")
        if answer.strip().lower() != "y":
            self.stdout.write("Aborted.")
            raise CommandError("Aborted by user.")

    def _load_json(self, file_path: str | None, use_stdin: bool) -> dict:
        """Load and parse JSON from stdin or a file path."""
        try:
            if use_stdin:
                self.stdout.write("Reading from stdin...")
                return json.load(sys.stdin)

            abs_path = os.path.abspath(file_path)
            with open(abs_path) as f:
                return json.load(f)

        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}") from None
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON: {e}") from e

    def _collect_all_fields(self, apps: list[str]) -> list[tuple]:
        """Return a flat list of (app_label, section_key, field_name, field) tuples
        for every registered field across the given app labels."""
        all_fields = []

        for app_label in apps:
            config_def = config_registry.get_config(app_label)
            if not config_def:
                raise CommandError(f"No config registered for app '{app_label}'")

            for section_name, section_class in config_def.get_sections():
                section_key = section_name.lower()
                for field_name, field in section_class.get_fields().items():
                    all_fields.append((app_label, section_key, field_name, field))

        return all_fields
