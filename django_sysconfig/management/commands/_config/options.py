import argparse

from django.core.management.base import CommandParser


def add_dry_run(parser: CommandParser) -> None:
    """Add the shared ``--dry-run`` flag (validate without persisting anything)."""
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the input without saving any changes to the database",
    )


def add_skip_prompt(parser: CommandParser) -> None:
    """Add the confirmation-skip flag to a prompting subcommand.

    ``--no-input``/``--noinput`` is the canonical, Django-idiomatic flag.
    ``-f``/``--force`` is retained as a backward-compatible duplicate; both
    resolve to the same ``force`` option.
    """
    parser.add_argument(
        "--no-input",
        "--noinput",
        action="store_true",
        dest="force",
        help="Skip the confirmation prompt (required for non-interactive use)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        dest="force",
        help="Alias of --no-input",
    )


def add_legacy_force(parser: CommandParser) -> None:
    """Add a deprecated, no-op ``-f``/``--force`` flag for backward compatibility.

    Retained so existing scripts keep parsing; it has no effect and will be
    removed in a future release.
    """
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        dest="force",
        help=argparse.SUPPRESS,
    )
