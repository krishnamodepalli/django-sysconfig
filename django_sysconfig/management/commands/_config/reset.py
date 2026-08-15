from django.core.management.base import CommandError

from django_sysconfig.accessor import config
from django_sysconfig.exceptions import ConfigError

from .common import confirm
from .options import resolve_skip_prompt


def handle_reset(command, **options):
    """Reset a config path to its field default, with optional confirmation."""
    path = options["path"]

    if not resolve_skip_prompt(command, options):
        confirm(
            command,
            f"This will reset '{path}' to its field default. This cannot be undone.",
        )

    try:
        config.reset(path)
        command.stdout.write(command.style.SUCCESS(f"✔ {path} reset to default"))
    except ConfigError as e:
        raise CommandError(str(e)) from e
