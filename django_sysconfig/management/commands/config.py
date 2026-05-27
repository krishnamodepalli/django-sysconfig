from django.core.management.base import BaseCommand, CommandParser

from ._config.export import handle_export
from ._config.get import handle_get
from ._config.import_ import handle_import
from ._config.reset import handle_reset
from ._config.set import handle_set


class Command(BaseCommand):
    help: str = "Interact with django-sysconfig configuration values"

    def add_arguments(self, parser: CommandParser):
        subparsers = parser.add_subparsers(dest="subcommand", metavar="subcommand")
        subparsers.required = True

        # --- get ---
        get_parser = subparsers.add_parser("get", help="Get a configuration value")
        get_parser.add_argument("path", help="Config path in app.section.field format")

        # --- set ---
        set_parser = subparsers.add_parser("set", help="Set a configuration value")
        set_parser.add_argument("path", help="Config path in app.section.field format")
        set_parser.add_argument("value", help="Value to set")
        set_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate the input value without saving into database",
        )

        # --- reset ---
        reset_parser = subparsers.add_parser(
            "reset", help="Reset a configuration value to its field default"
        )
        reset_parser.add_argument(
            "path", help="Config path in app.section.field format"
        )
        reset_parser.add_argument(
            "-f", "--force", action="store_true", help="Skip the confirmation prompt"
        )

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
        import_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate the input config data without saving any values",
        )
        import_parser.add_argument(
            "-S",
            "--skip-on-save-callbacks",
            action="store_true",
            help="Skip on_save callbacks for all fields in this import batch.",
        )
        import_parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Skip the confirmation prompt",
        )

    def handle(self, *args, **options):
        handlers = {
            "get": handle_get,
            "set": handle_set,
            "reset": handle_reset,
            "export": handle_export,
            "import": handle_import,
        }
        handlers[options["subcommand"]](self, **options)
