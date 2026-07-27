from abc import ABC, abstractmethod

from django.core.management.base import BaseCommand, CommandParser


class SubCommand(ABC):
    """One ``config`` subcommand: its CLI flags and the code that reads them.

    Declaring a flag next to the code that reads it keeps the two from drifting
    apart. Instances are created once at import time and shared across every
    invocation, so subclasses must stay stateless.
    """

    name: str
    help: str = ""

    def register(self, subparsers) -> None:
        """Build this subcommand's parser and populate it."""
        parser = subparsers.add_parser(self.name, help=self.help, description=self.help)
        self.add_arguments(parser)

    def add_arguments(self, parser: CommandParser) -> None:  # noqa: B027
        """Declare this subcommand's positional arguments and flags."""

    @abstractmethod
    def handle(self, command: BaseCommand, **options) -> None:
        """Run the subcommand.

        ``command`` is the parent :class:`~django.core.management.base.BaseCommand`
        and supplies ``stdout``, ``stderr`` and ``style``.
        """
