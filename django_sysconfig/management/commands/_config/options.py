import argparse
import warnings

from django.core.management.base import CommandParser


def add_dry_run(parser: CommandParser) -> None:
    """Add the shared ``--dry-run`` flag (validate without persisting anything)."""
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the input without saving any changes to the database",
    )


def add_skip_prompt(parser: CommandParser) -> None:
    """Add the confirmation-skip flags to a prompting subcommand.

    ``--no-input``/``--noinput`` is the canonical, Django-idiomatic spelling.
    ``-f``/``--force`` is kept as a working but deprecated alias; it is hidden
    from ``--help`` and will be removed in v2.

    The two spellings deliberately use different ``dest`` values so the handler
    can tell them apart and warn only on the deprecated one. Use
    :func:`resolve_skip_prompt` to collapse them into a single boolean.
    """
    parser.add_argument(
        "--no-input",
        "--noinput",
        action="store_true",
        dest="no_input",
        help="Skip the confirmation prompt (required for non-interactive use)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        dest="force",
        help=argparse.SUPPRESS,
    )


def resolve_skip_prompt(command, options: dict) -> bool:
    """Return whether the confirmation prompt should be skipped.

    Emits a ``DeprecationWarning`` (plus a visible stderr notice, since
    ``DeprecationWarning`` is silenced by default outside ``__main__``) when the
    caller used the legacy ``-f``/``--force`` spelling.
    """
    used_force = bool(options.get("force"))

    if used_force:
        message = (
            "`-f`/`--force` is deprecated; use `--no-input` instead. "
            "It will be removed in v2."
        )
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        command.stderr.write(command.style.WARNING(f"⚠ {message}"))

    return bool(options.get("no_input")) or used_force
