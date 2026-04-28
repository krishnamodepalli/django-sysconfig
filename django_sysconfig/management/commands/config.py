import json
import os
import sys
from datetime import UTC, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError, CommandParser

from django_sysconfig.accessor import config
from django_sysconfig.exceptions import ConfigError, ConfigValidationError
from django_sysconfig.registry import config_registry

UTC = UTC

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
            help="Validate the input config data without saving any values",
        )
        import_parser.add_argument(
            "-S",
            "--skip-on-save-callbacks",
            action="store_true",
            help="Skip on_save callbacks for all fields in this import batch.",
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

    def handle_get(self, *_args, **options):
        """Print the current value of a single config path."""
        path = options["path"]

        try:
            value = config.get(path)
            self.stdout.write(str(value))
        except ConfigError as e:
            raise CommandError(str(e)) from e

    def handle_set(self, *_args, **options):
        """Parse and persist a single config value."""
        path = options["path"]
        raw = options["value"]

        try:
            app_label, section, field_name = config._parse_path(path)
            field = config._get_field(app_label, section, field_name)
            parsed = field.get_frontend_model_instance().get_value(raw)

            config.set(path, parsed)
            self.stdout.write(self.style.SUCCESS(f"✔ {path} updated successfully"))

        except ConfigValidationError as e:
            errors = "\n".join(f"  • {err}" for err in e.errors)
            raise CommandError(f"Validation failed for {path}:\n{errors}") from e

        except ConfigError as e:
            raise CommandError(str(e)) from e

    def handle_reset(self, *_args, **options):
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

    def handle_export(self, *_args, **options):
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

        self.stdout.write(
            f"Exporting config for {len(apps)} app(s). "
            "This may take a moment for large configs."
        )
        self.stdout.write(f"Output will be written to: {output_path}\n")

        # 3. Fetch & serialise via accessor
        result = {
            "version": 1,
            "exported_at": datetime.now(UTC).isoformat(),
            "config": {},
        }

        for app_label in apps:
            result["config"][app_label] = config.all(app_label)
            self.stdout.write(f"  {app_label} exported...")

        # 4. Write — restricted to owner read/write only (secrets may be present)
        if os.path.exists(output_path):
            os.chmod(output_path, 0o600)
        fd = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(result, f, indent=2, cls=_JSONEncoder)

        self.stdout.write(self.style.SUCCESS(f"\n✔ Export complete → {output_path}"))
        self.stderr.write(
            self.style.WARNING(
                "⚠ This file contains plaintext secrets. Handle it with care."
            )
        )

    def handle_import(self, *_args, **options):
        """Load a JSON export and persist all contained config values."""
        dry_run = options["dry_run"]
        use_stdin = options["stdin"]
        skip_callbacks = options["skip_on_save_callbacks"]
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

        # 3. Validate structure before attempting to iterate
        if not isinstance(config_data, dict):
            raise CommandError("Invalid format: 'config' must be a JSON object")

        for app, sections in config_data.items():
            if not isinstance(sections, dict):
                raise CommandError(
                    f"Invalid format: expected an object for app '{app}', "
                    f"got {type(sections).__name__}"
                )
            for section, fields in sections.items():
                if not isinstance(fields, dict):
                    raise CommandError(
                        f"Invalid format: expected an object for '{app}.{section}', "
                        f"got {type(fields).__name__}"
                    )
                for field in fields:
                    if not isinstance(field, str):
                        raise CommandError(
                            f"Invalid format: field keys must be strings "
                            f"in '{app}.{section}'"
                        )

        paths = [
            (f"{app}.{section}.{field}", value)
            for app, sections in config_data.items()
            for section, fields in sections.items()
            for field, value in fields.items()
        ]

        # 4. Confirm (skipped for dry-run and --force)
        if not dry_run and not force:
            source = "stdin" if use_stdin else file_path
            self._confirm(
                f"This will override current configuration values from '{source}'. "
                "This cannot be undone."
            )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no values will be saved\n"))

            # Exercise the full import path inside a transaction that is always
            # rolled back — this runs path resolution, frontend-model coercion,
            # serialization, and field validators, so a dry-run failure means the
            # real import would also fail.
            from django.db import transaction

            errors = []
            try:
                with transaction.atomic():
                    config.set_many(dict(paths), skip_on_save_callbacks=True)
                    raise transaction.TransactionManagementError("dry-run rollback")
            except transaction.TransactionManagementError:
                pass
            except (ConfigValidationError, ConfigError) as e:
                errors.append(str(e))

            if errors:
                raise CommandError(
                    "Dry run failed — import would not succeed:\n"
                    + "\n".join(f"  • {err}" for err in errors)
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✔ Dry run passed — {len(paths)} value(s) look valid"
                )
            )
            return

        # 5. Execute
        try:
            config.set_many(dict(paths), skip_on_save_callbacks=skip_callbacks)
        except (ConfigValidationError, ConfigError) as e:
            raise CommandError(
                f"Import aborted — all changes rolled back:\n  • {e}"
            ) from e

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
