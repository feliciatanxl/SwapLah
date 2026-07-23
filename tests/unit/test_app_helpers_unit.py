"""Unit tests for Flask app helper functions."""
import pytest
from flask import Flask, session
from werkzeug.security import generate_password_hash

# Import the functions from the actual modules where they are defined
from app.auth import (
    _is_admin_user,
    _admin_denied_response,
    _require_admin_response,
    admin_required,
)
from app.db import get_user_by_id  # only used for patching, not directly
import app.db as db_module  # for monkeypatching


@pytest.fixture
def helper_app():
    """Create a minimal Flask app for helper tests."""
    flask_app = Flask(__name__)
    flask_app.config["SECRET_KEY"] = "test-secret-key"

    @flask_app.route("/login")
    def login():
        return "Login"

    @flask_app.route("/profile")
    def profile():
        return "Profile"

    return flask_app


def test_load_secret_key_requires_environment_value(monkeypatch):
    """Secret key helper should fail fast when SECRET_KEY is missing."""
    # This function is in app/__init__.py, so import it from there
    from app import _load_secret_key
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError):
        _load_secret_key()


def test_load_secret_key_returns_environment_value(monkeypatch):
    """Secret key helper should return the configured value."""
    from app import _load_secret_key
    monkeypatch.setenv("SECRET_KEY", "unit-secret")

    assert _load_secret_key() == "unit-secret"


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
    # Patch the db.get_user_by_id to return a non-admin user
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


def test_handle_login_requires_credentials(helper_app, monkeypatch):
    """Login helper should reject missing credentials."""
    from app import _handle_login
    monkeypatch.setattr("app.render_template", lambda template: template)

    with helper_app.test_request_context("/login", method="POST", data={}):
        assert _handle_login() == "login.html"


def test_handle_login_rejects_unknown_user(helper_app, monkeypatch):
    """Login helper should reject users that cannot be found."""
    from app import _handle_login
    monkeypatch.setattr("app.render_template", lambda template: template)
    monkeypatch.setattr(db_module, "get_user_by_email", lambda email: None)

    with helper_app.test_request_context(
        "/login",
        method="POST",
        data={"email": "missing@mymail.nyp.edu.sg", "password": "Password123"},
    ):
        assert _handle_login() == "login.html"


def test_handle_login_rejects_suspended_user(helper_app, monkeypatch):
    """Login helper should reject suspended accounts."""
    from app import _handle_login
    user = {
        "id": 3,
        "email": "suspended@mymail.nyp.edu.sg",
        "display_name": "Suspended",
        "role": "user",
        "status": "Suspended",
        "password_hash": generate_password_hash("Password123"),
    }

    monkeypatch.setattr("app.render_template", lambda template: template)
    monkeypatch.setattr(db_module, "get_user_by_email", lambda email: user)

    with helper_app.test_request_context(
        "/login",
        method="POST",
        data={"email": user["email"], "password": "Password123"},
    ):
        assert _handle_login() == "login.html"


def test_handle_login_sets_session_for_valid_user(helper_app, monkeypatch):
    """Login helper should create a session for active users."""
    from app import _handle_login
    user = {
        "id": 4,
        "email": "active@mymail.nyp.edu.sg",
        "display_name": "Active",
        "role": "user",
        "status": "Active",
        "password_hash": generate_password_hash("Password123"),
    }

    monkeypatch.setattr(db_module, "get_user_by_email", lambda email: user)

    with helper_app.test_request_context(
        "/login",
        method="POST",
        data={"email": user["email"], "password": "Password123"},
    ):
        response = _handle_login()

        assert response.status_code == 302
        assert "/profile" in response.location
        assert session["user_id"] == user["id"]
        assert session["email"] == user["email"]