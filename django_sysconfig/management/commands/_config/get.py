from django.core.management.base import CommandError

from django_sysconfig.accessor import config
from django_sysconfig.exceptions import ConfigError

from .base import SubCommand


class GetCommand(SubCommand):
    name = "get"
    help = "Get a configuration value"

    def add_arguments(self, parser):
        parser.add_argument("path", help="Config path in app.section.field format")

    def handle(self, command, **options):
        """Print the current value of a single config path."""
        path = options["path"]

        try:
            value = config.get(path)
            command.stdout.write(str(value))
        except ConfigError as e:
            raise CommandError(str(e)) from e
