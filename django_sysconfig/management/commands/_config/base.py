from abc import ABC, abstractmethod

from django.core.management.base import BaseCommand, CommandParser


class SubCommand(ABC):
    """One ``config`` subcommand: its CLI flags and the code that reads them.

    Keeping ``add_arguments`` and ``handle`` on the same class is the point of
    this base: a flag is declared next to the code that consumes it, so the two
    cannot drift apart across modules.

    Instances are built once at import time and shared by every invocation, so
    subclasses must stay stateless — anything per-run arrives as an argument.
    """

    name: str
    help: str = ""

    @abstractmethod
    def add_arguments(self, parser: CommandParser) -> None:
        """Declare this subcommand's positional arguments and flags."""

    @abstractmethod
    def handle(self, command: BaseCommand, **options) -> None:
        """Run the subcommand.

        ``command`` is the parent :class:`~django.core.management.base.BaseCommand`
        and supplies ``stdout``, ``stderr`` and ``style``.
        """
