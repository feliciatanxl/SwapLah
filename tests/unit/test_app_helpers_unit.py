"""Unit tests for admin helper functions."""
import pytest
from flask import Flask, session

# Admin helpers from app.auth
from app.auth import (
    _is_admin_user,
    _require_admin_response,
    admin_required,
)
# _admin_denied_response is defined in app/__init__.py
from app import _admin_denied_response
import app.db as db_module


@pytest.fixture
def helper_app():
    """Create a minimal Flask app for helper tests."""
    flask_app = Flask(__name__)
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    return flask_app


def test_admin_helpers_identify_only_active_admins():
    """Admin helper should require an active admin user."""
    assert _is_admin_user(None) is False
    assert _is_admin_user({"role": "user", "status": "Active"}) is False
    assert _is_admin_user({"role": "admin", "status": "Suspended"}) is False
    assert _is_admin_user({"role": "admin", "status": "Active"}) is True
    assert _admin_denied_response() == ("Forbidden", 403)


def test_require_admin_redirects_logged_out_user(helper_app):
    """Logged-out admin requests should redirect to login."""
    with helper_app.test_request_context("/admin/settings"):
        response = _require_admin_response()
        assert response.status_code == 302
        assert "/login" in response.location


def test_require_admin_blocks_non_admin_user(helper_app, monkeypatch):
    """Logged-in non-admin users should receive a forbidden response."""
    monkeypatch.setattr(
        db_module,
        "get_user_by_id",
        lambda user_id: {"id": user_id, "role": "user", "status": "Active"},
    )
    with helper_app.test_request_context("/admin/settings"):
        session["user_id"] = 7
        assert _require_admin_response() == ("Forbidden", 403)


def test_admin_required_allows_active_admin(helper_app, monkeypatch):
    """Admin decorator should call the wrapped view for active admins."""
    monkeypatch.setattr(
        db_module,
        "get_user_by_id",
        lambda user_id: {"id": user_id, "role": "admin", "status": "Active"},
    )

    def protected_view():
        return "allowed"

    with helper_app.test_request_context("/admin"):
        session["user_id"] = 1
        assert admin_required(protected_view)() == "allowed"