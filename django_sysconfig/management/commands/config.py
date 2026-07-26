from django.core.management.base import BaseCommand, CommandParser

from ._config.export import ExportCommand
from ._config.get import GetCommand
from ._config.import_ import ImportCommand
from ._config.reset import ResetCommand
from ._config.set import SetCommand

# Every subcommand owns both its flags and its handler. Adding one means
# writing a SubCommand subclass and listing it here — this module does not
# otherwise grow.
SUBCOMMANDS = (
    GetCommand(),
    SetCommand(),
    ResetCommand(),
    ExportCommand(),
    ImportCommand(),
)
_BY_NAME = {sub.name: sub for sub in SUBCOMMANDS}


class Command(BaseCommand):
    help: str = "Interact with django-sysconfig configuration values"

    def add_arguments(self, parser: CommandParser):
        subparsers = parser.add_subparsers(dest="subcommand", metavar="subcommand")
        subparsers.required = True

        for sub in SUBCOMMANDS:
            sub.add_arguments(subparsers.add_parser(sub.name, help=sub.help))

    def handle(self, *args, **options):
        _BY_NAME[options["subcommand"]].handle(self, **options)
