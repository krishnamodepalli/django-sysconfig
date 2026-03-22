import re


def to_snake_case(text: str) -> str:
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
    text = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", text)
    text = re.sub(r"[-\s]+", "_", text)
    return text.lower().strip("_")


def to_camel_case(text: str) -> str:
    words = re.split(r"[-_\s]+", to_snake_case(text))
    return words[0] + "".join(word.capitalize() for word in words[1:])


def to_pascal_case(text: str) -> str:
    words = re.split(r"[-_\s]+", to_snake_case(text))
    return "".join(word.capitalize() for word in words)


def convert_case(text: str, target: str) -> str:
    """
    Convert a string to the specified case format.

    Args:
        text: Input string in any common case format.
        target: One of "snake", "camel", or "pascal".

    Returns:
        The converted string.

    Raises:
        ValueError: If target is not a recognised case format.
    """
    converters = {
        "snake": to_snake_case,
        "camel": to_camel_case,
        "pascal": to_pascal_case,
    }
    if target not in converters:
        raise ValueError(
            f"Unknown case format '{target}'. "
            f"Expected one of: {', '.join(converters)}"
        )
    return converters[target](text)
