from django.core.management.base import CommandError
from django.db import transaction

from django_sysconfig.accessor import config
from django_sysconfig.exceptions import ConfigError, ConfigValidationError

from .base import SubCommand
from .options import add_dry_run


class SetCommand(SubCommand):
    name = "set"
    help = "Set a configuration value"

    def add_arguments(self, parser):
        parser.add_argument("path", help="Config path in app.section.field format")
        parser.add_argument("value", help="Value to set")
        add_dry_run(parser)

    def handle(self, command, **options):
        """Parse and persist a single config value."""
        path = options["path"]
        raw = options["value"]
        dry_run = options["dry_run"]

        try:
            app_label, section, field_name = config._parse_path(path)
            field = config._get_field(app_label, section, field_name)
            parsed = field.get_frontend_model_instance().get_value(raw)

            with transaction.atomic():
                config.set(path, parsed)

                if dry_run:
                    command.stdout.write(
                        command.style.SUCCESS(f"✔ Validation passed for '{path}'")
                    )
                    command.stdout.write(
                        command.style.WARNING("Dry run — no values will be saved")
                    )
                    transaction.set_rollback(True)
                    return

                command.stdout.write(
                    command.style.SUCCESS(f"✔ {path} updated successfully")
                )

        except ConfigValidationError as e:
            errors = "\n".join(f"  • {err}" for err in e.errors)
            raise CommandError(f"Validation failed for {path}:\n{errors}") from e

        except ConfigError as e:
            raise CommandError(str(e)) from e
