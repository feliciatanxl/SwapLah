"""Unit tests for profile/cover image URL validation."""

import pytest

from app.profile_media import MAX_IMAGE_URL_LENGTH, validate_image_url


@pytest.mark.parametrize("blank", [None, "", "   "])
def test_blank_values_become_none_without_error(blank):
    """Blank input is valid and stored as None to use defaults."""
    value, error = validate_image_url(blank)
    assert value is None
    assert error is None


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/a.jpg",
        "https://cdn.example.com/path/to/avatar.png?size=160",
        "  https://example.com/trimmed.jpg  ",
    ],
)
def test_valid_http_urls_are_accepted(url):
    """Absolute http(s) URLs pass and are trimmed."""
    value, error = validate_image_url(url)
    assert error is None
    assert value == url.strip()


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "data:image/png;base64,AAAA",
        "file:///etc/passwd",
        "ftp://example.com/a.jpg",
        "not-a-url",
        "//example.com/a.jpg",
    ],
)
def test_unsafe_or_malformed_schemes_are_rejected(url):
    """Only http and https absolute URLs are permitted."""
    value, error = validate_image_url(url)
    assert value is None
    assert error is not None


@pytest.mark.parametrize(
    "url",
    [
        'https://example.com/"onerror=alert(1).jpg',
        "https://example.com/a'.jpg",
        "https://example.com/<script>.jpg",
        "https://example.com/a b.jpg",
    ],
)
def test_dangerous_characters_are_rejected(url):
    """Characters that could break out of an HTML attribute are rejected."""
    value, error = validate_image_url(url)
    assert value is None
    assert error is not None


def test_overly_long_url_is_rejected():
    """A URL beyond the maximum length is rejected."""
    long_url = "https://example.com/" + ("a" * MAX_IMAGE_URL_LENGTH) + ".jpg"
    value, error = validate_image_url(long_url)
    assert value is None
    assert "characters" in error
