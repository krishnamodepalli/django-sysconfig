import json
import os
import sys
from decimal import Decimal

from django.core.management.base import CommandError


class JSONEncoder(json.JSONEncoder):
    """Extends the default encoder to handle Decimal values."""

    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)


def confirm(command, message: str) -> None:
    """Prompt the user for y/N confirmation; abort with CommandError on refusal."""
    answer = input(f"{message} Continue? [y/N] ")
    if answer.strip().lower() != "y":
        command.stdout.write("Aborted.")
        raise CommandError("Aborted by user.")


def load_json(command, file_path: str | None, use_stdin: bool) -> dict:
    """Load and parse JSON from stdin or a file path."""
    try:
        if use_stdin:
            command.stdout.write("Reading from stdin...")
            data = json.load(sys.stdin)
        else:
            abs_path = os.path.abspath(file_path)
            with open(abs_path) as f:
                data = json.load(f)

    except FileNotFoundError:
        raise CommandError(f"File not found: {file_path}") from None
    except json.JSONDecodeError as e:
        raise CommandError(f"Invalid JSON: {e}") from e

    if not isinstance(data, dict):
        raise CommandError(
            f"Invalid JSON: expected a top-level object, got {type(data).__name__}"
        )
    return data
