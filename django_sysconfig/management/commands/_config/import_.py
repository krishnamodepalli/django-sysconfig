from django.core.management.base import CommandError
from django.db import transaction

from django_sysconfig.accessor import config
from django_sysconfig.exceptions import ConfigError, ConfigValidationError

from .common import confirm, load_json
from .options import resolve_skip_prompt


def handle_import(command, **options):
    """Load a JSON export and persist all contained config values."""
    dry_run = options["dry_run"]
    use_stdin = options["stdin"]
    skip_callbacks = options["skip_on_save_callbacks"]
    skip_prompt = resolve_skip_prompt(command, options)
    file_path = options.get("file")

    # 1. Validate args
    if use_stdin and file_path:
        raise CommandError("--stdin and --file are mutually exclusive")
    if not use_stdin and not file_path:
        raise CommandError("Provide a file path via --file/-i or use --stdin")
    if file_path and not file_path.endswith(".json"):
        raise CommandError("Input file must have a .json extension")

    # 2. Load
    data = load_json(command, file_path, use_stdin)

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

    # 4. Confirm.
    #
    # Skipped for dry-run, for --no-input/--force, and when reading from stdin.
    # load_json() has already drained sys.stdin by this point, so prompting
    # would hit an exhausted stream and raise EOFError; a piped stdin is
    # non-interactive by definition, so there is nobody to ask.
    if not dry_run and not skip_prompt and not use_stdin:
        confirm(
            command,
            f"This will override current configuration values from '{file_path}'. "
            "This cannot be undone.",
        )

    if dry_run:
        command.stdout.write(
            command.style.WARNING("Dry run — no values will be saved\n")
        )

        # Exercise the full import path inside a transaction that is always
        # rolled back — this runs path resolution, frontend-model coercion,
        # serialization, and field validators, so a dry-run failure means the
        # real import would also fail.

        errors = []
        try:
            with transaction.atomic():
                config.set_many(dict(paths), skip_on_save_callbacks=True)
                transaction.set_rollback(True)
        except (ConfigValidationError, ConfigError) as e:
            errors.append(str(e))

        if errors:
            raise CommandError(
                "Dry run failed — import would not succeed:\n"
                + "\n".join(f"  • {err}" for err in errors)
            )

        command.stdout.write(
            command.style.SUCCESS(
                f"✔ Dry run passed — {len(paths)} value(s) look valid"
            )
        )
        return

    # 5. Execute
    try:
        config.set_many(dict(paths), skip_on_save_callbacks=skip_callbacks)
    except (ConfigValidationError, ConfigError) as e:
        raise CommandError(f"Import aborted — all changes rolled back:\n  • {e}") from e

    command.stdout.write(
        command.style.SUCCESS(f"✔ Import complete — {len(paths)} value(s) set")
    )
