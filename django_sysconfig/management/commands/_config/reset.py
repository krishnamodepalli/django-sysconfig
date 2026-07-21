from django.core.management.base import CommandError

from django_sysconfig.accessor import config
from django_sysconfig.exceptions import ConfigError


def handle_reset(command, **options):
    """Reset a config path to its field default.

    ``reset`` targets a single path, so it no longer prompts for confirmation
    (confirmation is reserved for bulk operations like ``import``).
    """
    path = options["path"]

    if options["force"]:
        command.stderr.write(
            command.style.WARNING(
                "⚠ --force/-f is deprecated for 'reset' and will be removed in a "
                "future release; 'reset' no longer prompts for confirmation."
            )
        )

    try:
        config.reset(path)
        command.stdout.write(command.style.SUCCESS(f"✔ {path} reset to default"))
    except ConfigError as e:
        raise CommandError(str(e)) from e
