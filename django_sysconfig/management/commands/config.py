from django.core.management.base import BaseCommand, CommandParser

from ._config.export import handle_export
from ._config.get import GetCommand
from ._config.import_ import handle_import
from ._config.options import add_dry_run, add_skip_prompt
from ._config.reset import handle_reset
from ._config.set import SetCommand

# Subcommands migrated to the SubCommand class form. Each owns both its flags
# and its handler. The remaining subcommands below are still declared inline
# and dispatched through LEGACY_HANDLERS; they are being converted one at a
# time, after which both this comment and LEGACY_HANDLERS disappear.
SUBCOMMANDS = (GetCommand(), SetCommand())
_BY_NAME = {sub.name: sub for sub in SUBCOMMANDS}


class Command(BaseCommand):
    help: str = "Interact with django-sysconfig configuration values"

    def add_arguments(self, parser: CommandParser):
        subparsers = parser.add_subparsers(dest="subcommand", metavar="subcommand")
        subparsers.required = True

        for sub in SUBCOMMANDS:
            sub.add_arguments(subparsers.add_parser(sub.name, help=sub.help))

        # --- reset ---
        reset_parser = subparsers.add_parser(
            "reset", help="Reset a configuration value to its field default"
        )
        reset_parser.add_argument(
            "path", help="Config path in app.section.field format"
        )
        add_skip_prompt(reset_parser)

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
        add_dry_run(import_parser)
        import_parser.add_argument(
            "-S",
            "--skip-on-save-callbacks",
            action="store_true",
            help="Skip on_save callbacks for all fields in this import batch.",
        )
        add_skip_prompt(import_parser)

    def handle(self, *args, **options):
        name = options["subcommand"]

        sub = _BY_NAME.get(name)
        if sub is not None:
            sub.handle(self, **options)
            return

        LEGACY_HANDLERS[name](self, **options)


# Not-yet-migrated subcommands. Shrinks to empty as each one moves to a class.
LEGACY_HANDLERS = {
    "reset": handle_reset,
    "export": handle_export,
    "import": handle_import,
}
