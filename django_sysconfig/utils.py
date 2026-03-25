import re


def to_snake_case(name: str) -> str:
    """Convert CamelCase/PascalCase to snake_case. E.g. 'PaymentSettings' -> 'payment_settings'."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def is_snake_case(name: str) -> bool:
    """Return True if name is strictly lowercase snake_case (e.g. 'my_app', 'site_url')."""
    return bool(re.match(r"^[a-z][a-z0-9_]*$", name))
