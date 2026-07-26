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

    def add_arguments(self, parser: CommandParser) -> None:  # noqa: B027
        """Declare this subcommand's positional arguments and flags.

        Optional — a subcommand may legitimately take no arguments at all.
        Mirrors ``BaseCommand.add_arguments``, which is likewise a no-op.

        The empty body is deliberate, so B027 (missing ``@abstractmethod``)
        is silenced: that rule exists to catch a *forgotten* decorator.
        """

    @abstractmethod
    def handle(self, command: BaseCommand, **options) -> None:
        """Run the subcommand.

        ``command`` is the parent :class:`~django.core.management.base.BaseCommand`
        and supplies ``stdout``, ``stderr`` and ``style``.
        """
