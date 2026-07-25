"""Server-side validation for user-supplied profile and cover image URLs."""

from urllib.parse import urlparse

MAX_IMAGE_URL_LENGTH = 500
_ALLOWED_SCHEMES = ("http", "https")
_FORBIDDEN_CHARS = ('"', "'", "<", ">", "\\", " ", "\t", "\n", "\r")


def _image_url_error(value):
    """Return an error message for an invalid non-blank image URL, or None."""
    if len(value) > MAX_IMAGE_URL_LENGTH:
        return f"Image URL must be {MAX_IMAGE_URL_LENGTH} characters or fewer."

    if any(char in value for char in _FORBIDDEN_CHARS):
        return "Image URL contains invalid characters."

    parsed = urlparse(value)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        return "Image URL must start with http:// or https://."

    if not parsed.netloc:
        return "Image URL is not a valid web address."

    return None


def validate_image_url(raw_value):
    """Return ``(cleaned_url_or_None, error_message_or_None)`` for an image URL.

    Blank input is valid and returns ``None`` so the interface falls back to its
    default image. Only absolute ``http(s)`` URLs are accepted; ``javascript:``,
    ``data:``, ``file:`` and characters that could break out of an HTML
    attribute are rejected.
    """
    if raw_value is None:
        return None, None

    value = raw_value.strip()
    if not value:
        return None, None

    error = _image_url_error(value)
    if error:
        return None, error

    return value, None
