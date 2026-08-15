from django.core.management.base import CommandError

from django_sysconfig import ConfigError, config


def handle_get(command, **options):
    """Print the current value of a single config path."""
    path = options["path"]

    try:
        value = config.get(path)
        command.stdout.write(str(value))
    except ConfigError as e:
        raise CommandError(str(e)) from e
