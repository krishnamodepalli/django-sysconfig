from django.core.management.base import CommandError

from django_sysconfig.accessor import config
from django_sysconfig.exceptions import ConfigError

from .base import SubCommand
from .common import confirm
from .options import add_skip_prompt, resolve_skip_prompt


class ResetCommand(SubCommand):
    name = "reset"
    help = "Reset a configuration value to its field default"

    def add_arguments(self, parser):
        parser.add_argument("path", help="Config path in app.section.field format")
        add_skip_prompt(parser)

    def handle(self, command, **options):
        """Reset a config path to its field default, with optional confirmation."""
        path = options["path"]

        if not resolve_skip_prompt(command, options):
            confirm(
                command,
                f"This will reset '{path}' to its field default. "
                "This cannot be undone.",
            )

        try:
            config.reset(path)
            command.stdout.write(command.style.SUCCESS(f"✔ {path} reset to default"))
        except ConfigError as e:
            raise CommandError(str(e)) from e
