from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Interact with django-sysconfig configuration values"

    def add_arguments(self, parser: CommandParser):
        subparsers = parser.add_subparsers(dest="subcommand", metavar="subcommand")
        subparsers.required = True

        get_parser = subparsers.add_parser("get", help="Get a configuration value")
        get_parser.add_argument("path", help="Config path in app.section.field format")

        set_parser = subparsers.add_parser("set", help="Set a configuration value")
        set_parser.add_argument("path", help="Config path in app.section.field format")
        set_parser.add_argument("value", help="Value to set")

        reset_parser = subparsers.add_parser(
            "reset", help="Reset a configuration value to its field default"
        )
        reset_parser.add_argument(
            "path", help="Config path in app.section.field format"
        )
        reset_parser.add_argument(
            "-f", "--force", action="store_true", help="Skip the confirmation prompt"
        )

        export_parser = subparsers.add_parser(
            "export", help="Export configuration values to a JSON or YAML file"
        )
        export_parser.add_argument(
            "app", nargs="?", help="App label to export (exports all apps if omitted)"
        )
        export_parser.add_argument(
            "--output",
            "-o",
            required=True,
            help="Output file path (.json, .yml, .yaml)",
        )
        export_parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Fields to process per batch (default: 50)",
        )

        import_parser = subparsers.add_parser(
            "import", help="Import configuration values from a JSON or YAML file"
        )
        import_parser.add_argument("file", help="Input file path (.json, .yml, .yaml)")
        import_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate the file without saving any values",
        )

    def handle(self, *args, **options):
        handlers = {
            "get": self.handle_get,
            "set": self.handle_set,
            "reset": self.handle_reset,
            "export": self.handle_export,
            "import": self.handle_import,
        }
        handlers[options["subcommand"]](*args, **options)

    def handle_get(self, *args, **options):
        raise NotImplementedError

    def handle_set(self, *args, **options):
        raise NotImplementedError

    def handle_reset(self, *args, **options):
        raise NotImplementedError

    def handle_export(self, *args, **options):
        raise NotImplementedError

    def handle_import(self, *args, **options):
        raise NotImplementedError
