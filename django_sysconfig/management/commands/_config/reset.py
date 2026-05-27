from django.core.management.base import CommandError

from django_sysconfig.accessor import config
from django_sysconfig.exceptions import ConfigError

from .common import confirm


def handle_reset(command, **options):
    """Reset a config path to its field default, with optional confirmation."""
    path = options["path"]

    if not options["force"]:
        confirm(
            command,
            f"This will reset '{path}' to its field default. " "This cannot be undone.",
        )

    try:
        config.reset(path)
        command.stdout.write(command.style.SUCCESS(f"✔ {path} reset to default"))
    except ConfigError as e:
        raise CommandError(str(e)) from e
