"""Unit tests for session timeout helper functions."""

import time

import pytest
from flask import Flask, session

from app import SESSION_TIMEOUT_SECONDS, _has_session_expired, _is_public_endpoint


@pytest.fixture
def flask_app():
    """Create a minimal Flask app for session helper unit tests."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    return app


def test_public_endpoint_is_allowed():
    """Public endpoints should not require login."""
    assert _is_public_endpoint("login") is True
    assert _is_public_endpoint("register") is True
    assert _is_public_endpoint("static") is True


def test_protected_endpoint_is_not_public():
    """Protected endpoints should not be treated as public."""
    assert _is_public_endpoint("profile") is False
    assert _is_public_endpoint("edit_profile") is False


def test_session_before_timeout_is_not_expired(flask_app):
    """Session should remain active before 30 minutes of inactivity."""
    with flask_app.test_request_context("/profile"):
        now = time.time()
        session["last_activity"] = now - (SESSION_TIMEOUT_SECONDS - 60)

        assert _has_session_expired(now) is False


def test_session_after_timeout_is_expired(flask_app):
    """Session should expire after more than 30 minutes of inactivity."""
    with flask_app.test_request_context("/profile"):
        now = time.time()
        session["last_activity"] = now - (SESSION_TIMEOUT_SECONDS + 60)

        assert _has_session_expired(now) is True