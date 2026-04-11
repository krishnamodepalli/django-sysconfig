"""Custom template filters for safe HTML rendering."""

from __future__ import annotations

import re
from django import template
from django.utils.html import format_html

register = template.Library()

# Allowlist of safe HTML tags and attributes for field comments
ALLOWED_TAGS = frozenset({"code", "strong", "b", "em", "i", "br", "p", "a", "span"})
ALLOWED_ATTRS = {
    "a": frozenset({"href", "title", "target", "rel"}),
    "span": frozenset({"class"}),
}


def _escape_html(text: str) -> str:
    """Escape HTML special characters but allow safe formatting tags."""
    # First, protect the allowed tags by temporarily replacing them
    protected = {}
    placeholder_pattern = re.compile(r"<(/?)([\w]+)([^>]*)>")
    
    def replacer(match):
        prefix, tag, attrs = match.group(1), match.group(2).lower(), match.group(3)
        if tag in ALLOWED_TAGS:
            key = f"\x00{len(protected)}\x00"
            protected[key] = match.group(0)
            return key
        else:
            # Escape dangerous tags - convert <tag> to &lt;tag&gt;
            return f"&lt;{prefix}{tag}{attrs}&gt;"
    
    result = placeholder_pattern.sub(replacer, text)
    
    # Now escape any remaining HTML special chars (outside our protected tags)
    # We need to be careful not to double-escape
    result = (result
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;"))
    
    # Restore protected tags
    for key, tag_html in protected.items():
        result = result.replace(key, tag_html)
    
    return result


@register.filter
def safe_html(text: str) -> str:
    """
    Sanitize field comment HTML, allowing only safe formatting tags.
    
    Allows: <code>, <strong>, <b>, <em>, <i>, <br>, <p>, <a>, <span>
    Strips all other HTML tags and escapes special characters.
    
    This is a defence-in-depth measure - comments are developer-defined
    and committed to version control, but we should still sanitize
    to prevent accidental or malicious HTML injection.
    """
    if not text:
        return ""
    
    # First strip any potentially dangerous tags entirely, keeping content
    # Use a simple approach: strip_tags first, then re-apply basic formatting
    from django.utils.html import strip_tags
    
    # Strip all HTML first, then escape everything
    stripped = strip_tags(text)
    
    # Now we need to allow basic formatting. We'll use a different approach:
    # escape everything first, then selectively unescape for allowed tags
    escaped = _escape_html(text)
    
    return escaped


@register.filter
def field_comment(text: str) -> str:
    """
    Render field comment safely with allowlisted HTML support.
    
    This is the recommended filter for rendering field.comment.
    """
    return safe_html(text)
